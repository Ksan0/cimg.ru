# coding: utf-8
from django.contrib.auth import *
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpRequest
from django.core.files import *
from django.core.files.uploadedfile import *
from django.shortcuts import render
# from django.contrib.auth.models import User, UserManager
# from time import gmtime, strftime
from forms import *
import sys, os, zlib, string, random, time
from Cimage_iodata import *
import StringIO
# import hashlib
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import SHA256, SHA
from django.utils.encoding import smart_str


# version: 2 bytes
# init_vec: AES.block_size bytes
# password: 32 bytes
# ibits_count: 1 byte

# titles_count: 4 bytes
# [
# * title_size: 4 bytes
# * title: title_size bytes
# * content_adress: 4 bytes
# * content_size: 4 bytes
# ]

# [
# * content
# ]



def str_to_hex(s):
    return ''.join([hex(ord(c))[2:].zfill(2) for c in s])

def hex_to_str(hs):
    s = ''
    for i in range(len(hs)/2):
        c = chr(int(hs[i*2:(i+1)*2], 16))
        s += c
    return s

def save_file(path, file, name=''):
    if name == '':
        name = file.name
    f = open(buffer(path + '/' + name), 'wb')
    for chunk in file.chunks():
        f.write(chunk)
    f.close()


def random_str(size=32):
    #hash_builder = SHA.new()
    #hash_builder.update(buffer(str(Random.new().read(20))))
    #return hash_builder.hexdigest()
    #return hashlib.sha1().update(Random.new().read(16)).hexdigest()
    # return str_to_hex(Random.new().read(size/2))
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for x in range(size))


class CimageConst:
    version = 2
    version_size = 2
    init_vector_size = AES.block_size
    password_size = 32
    init_ibits_count = 2
    ibits_count_size = 1
    sys_info_size = version_size + init_vector_size + password_size + ibits_count_size
    int_size = 4
    #session_path = '/home/users/k/kgfq/domains/kgfq.myjino.ru/sessions/'
    #session_path = '/home/users/k/kgfq/domains/cimg.ru/sessions/'
    #session_path = '/home/ksan/MyProjects/Cimage/sessions/'
    session_path = '/var/www/ksan/data/www/cimg.ru/sessions/'


def gen_session_id():
    session_id = random_str()
    session_path = CimageConst.session_path + session_id
    while os.path.exists(session_path):
        session_id = random_str()
        session_path = CimageConst.session_path + session_id
    return session_id


def encrypt_function(request):
    try:
        form = EncryptForm(request.POST)
        try:
            ibits_count = int(form.data['imgDifferenceSelect'])
        except:
            ibits_count = 2
        if not form.is_valid():
            return {"error": "password and confirm don't match"}
    except:
        return {"error": "form convert error"}

    try:
        session_id = gen_session_id()
        session_path = CimageConst.session_path + session_id
        os.mkdir(session_path)
    except:
        return {"error": "session generate error"}

    try:
        img_file = request.FILES.getlist('imgChooseInput')[0]
    except:
        return {"error": "No image"}
    
    try:
        save_file(session_path, img_file, 'image')
    except:
        return {"error": "save file error"}

    try:
        hash_builder = SHA256.new()
        hash_builder.update(smart_str(form.data['enterPasswordInput']))
        password = hash_builder.digest()
    except:
        return {"error": "hash error"}

    try:
        img = Image.open(session_path + '/image')
    except:
        return {"error": "Bad image"}

    try:
        cim = CIM(img, CimageConst.init_ibits_count)
    except:
        return {"error": "CIM init error"}

    try:
        init_vector = buffer(Random.new().read(AES.block_size))
        cipher = AES.new(password, AES.MODE_CFB, init_vector)
    except:
        return {"error": "cipher init error"}

    try:
        cim.write(cipher.encrypt(CIM.i2bs(CimageConst.version, CimageConst.version_size)), upto_ibits=ibits_count)
        cim.write(init_vector, upto_ibits=ibits_count)
        cim.write(cipher.encrypt(password), upto_ibits=ibits_count)
        cim.write(cipher.encrypt(CIM.i2bs(ibits_count, CimageConst.ibits_count_size)), upto_ibits=ibits_count)

        cim.ibits = ibits_count
        
        titles_count = len(request.FILES.getlist('filesChooseInput')) + 1  # +1 : text
        cim.write(cipher.encrypt(CIM.i2bs(titles_count, CimageConst.int_size)))
        cursor_title = cim.cursor
        
        titles_size = CimageConst.int_size * 3
        for file in request.FILES.getlist('filesChooseInput'):
            titles_size += CimageConst.int_size * 3 + len(smart_str(file.name))
        cim.miss(titles_size)
        cursor_content = cim.cursor
        text = smart_str(form.data['textField'])   

        cim.cursor = cursor_title
        cim.write(cipher.encrypt(CIM.i2bs(0, CimageConst.int_size)))
        cim.write(cipher.encrypt(CIM.i2bs(cursor_content, CimageConst.int_size)))
        cim.write(cipher.encrypt(CIM.i2bs(len(text), CimageConst.int_size)))
        cursor_title = cim.cursor
        cim.cursor = cursor_content
        cipher_content = AES.new(password, AES.MODE_CFB, init_vector)
        cim.write(cipher_content.encrypt(text))
        cursor_content = cim.cursor

        index = 1
        for file in request.FILES.getlist('filesChooseInput'):
            cim.cursor = cursor_title
            file_name = smart_str(file.name)
            cim.write(cipher.encrypt(CIM.i2bs(len(file_name), CimageConst.int_size)))
            cim.write(cipher.encrypt(file_name))
            file_data = zlib.compress(file.read(), 9)
            cim.write(cipher.encrypt(CIM.i2bs(cursor_content, CimageConst.int_size)))
            cim.write(cipher.encrypt(CIM.i2bs(len(file_data), CimageConst.int_size)))
            cursor_title = cim.cursor
            cim.cursor = cursor_content
            cipher_content = AES.new(password, AES.MODE_CFB, init_vector)
            cim.write(cipher_content.encrypt(file_data))
            cursor_content = cim.cursor
            index += 1
            
    except IndexError:
        if img.size[0]*img.size[1] < 1024:
            return {"error": "Too small image"}
        return {"error": "Too small image. It can contain " + "{0:.2f}".format((img.size[0]*img.size[1]*3*ibits_count/8 - 256)/1024.0) + " Kbytes at this difference level"}
    except TypeError:
        return {"error": "Unsupported image format"}

    try:
        img_file_name = smart_str(img_file.name)
    except:
        img_file_name = 'image'
    
    try:
        img.save(session_path + '/[CIM]' + img_file_name + '.png', 'PNG')
    except:
        return {"error": "Unsupported image format"}

    try:
        os.remove(session_path + '/image')
    except:
        return {"error": "image remove error [2]"}    

    return {
        'session_id': session_id,
        'filename': '[CIM]' + img_file_name + '.png',
    }


def decrypt_get_file_titles(request):
    try:
        form = DecryptForm(request.POST)
    except:
        return {"error": "form convert error"}

    try:   
        session_id = gen_session_id()
        session_path = CimageConst.session_path + session_id
        os.mkdir(session_path)
    except:
        return {"error": "session generate error"}

    try:
        img_file = request.FILES.getlist('imgChooseInput')[0]
    except:
        return {"error": "No image"}
    
    try:
        save_file(session_path, img_file, 'Cimage')
    except:
        return {"error": "save file error"}

    try:
        hash_builder = SHA256.new()
        hash_builder.update(smart_str(form.data['enterPasswordInput']))
        password = hash_builder.digest()
    except:
        return {"error": "hash error"}

    try:
        img = Image.open(session_path + '/Cimage')
    except:
        return {"error": "Bad image"}

    try:
        cim = CIM(img, CimageConst.init_ibits_count)
    except:
        return {"error": "CIM init error"}

    try:
        cipher = AES.new(password, AES.MODE_CFB, '0'*AES.block_size)
    except:
        return {"error": "cipher init error"}

    try:
        crypt_version = cim.read(CimageConst.version_size)
        init_vector = cim.read(CimageConst.init_vector_size)
        cipher.decrypt(init_vector)
	version = CIM.bs2i(cipher.decrypt(crypt_version))
        decrypt_password = smart_str( cipher.decrypt(cim.read(CimageConst.password_size)) )
        ibits_count = CIM.bs2i(cipher.decrypt(cim.read(CimageConst.ibits_count_size)))
    except:
        return {"error": "No data or image is corrupted"}

    if password != decrypt_password or ibits_count < 1 or ibits_count > 8:
        return {"error": "No data, wrong password or image is corrupted"}

    cim.ibits = ibits_count
    
    try:
        titles_count = CIM.bs2i(cipher.decrypt(cim.read(CimageConst.int_size)))
        titles = []
        CIM.bs2i(cipher.decrypt(cim.read(CimageConst.int_size)))
        text_adress = CIM.bs2i(cipher.decrypt(cim.read(CimageConst.int_size)))
        text_size = CIM.bs2i(cipher.decrypt(cim.read(CimageConst.int_size)))
        text = ''

        if text_size != 0:
            cursor_tmp = cim.cursor
            cim.cursor = text_adress
            cipher_content = AES.new(password, AES.MODE_CFB, '0'*AES.block_size)
            cipher_content.decrypt(init_vector)
            text = smart_str( cipher_content.decrypt(cim.read(text_size)) )
            cim.cursor = cursor_tmp

        for index in range(titles_count - 1):
            title_size = CIM.bs2i(cipher.decrypt(cim.read(CimageConst.int_size)))
            if title_size != 0:
                title = smart_str( cipher.decrypt(cim.read(title_size)) )
                titles.append( (index+1, title) )
                
            cipher.decrypt(cim.read(CimageConst.int_size))
            cipher.decrypt(cim.read(CimageConst.int_size))
    
    except:
        return {"error": "image is corrupted"}

    return {
        'session_id': session_id,
        'password': password,
        'titles': titles,
        'text': text,
    }


def decrypt_get_file(request):
    try:
        file_number = int(request.GET.get('fnum'))
        session_id = request.GET.get('sid')
        password = hex_to_str(request.get_signed_cookie(key='key', salt=str(os.path.getctime(CimageConst.session_path + session_id))))

        session_path = CimageConst.session_path + session_id
        if not os.path.exists(session_path):
            return {"error": "invalid session or url"}

        img = Image.open(session_path + '/Cimage')
        cim = CIM(img, CimageConst.init_ibits_count)

        cipher = AES.new(password, AES.MODE_CFB, '0'*AES.block_size)

        crypt_version = cim.read(CimageConst.version_size)
        init_vector = cim.read(CimageConst.init_vector_size)
        cipher.decrypt(init_vector)
        version = CIM.bs2i(cipher.decrypt(crypt_version))
        decrypt_password = cipher.decrypt(cim.read(CimageConst.password_size))
        ibits_count = CIM.bs2i(cipher.decrypt(cim.read(CimageConst.ibits_count_size)))

        if password != decrypt_password:
            return {"error": "invalid session or url"}

        cim.ibits = ibits_count

        titles_count = CIM.bs2i(cipher.decrypt(cim.read(CimageConst.int_size)))
        if file_number < 1 or file_number >= titles_count:
            return {"error": "invalid session or url"}

        title_size = 0
        title = ''
        content_adress = 0
        content_size = 0
        for index in range(file_number + 1):
            title_size = CIM.bs2i(cipher.decrypt(cim.read(CimageConst.int_size)))
            if title_size != 0:
                title = smart_str( cipher.decrypt(cim.read(title_size)) )
            content_adress = CIM.bs2i(cipher.decrypt(cim.read(CimageConst.int_size)))
            content_size = CIM.bs2i(cipher.decrypt(cim.read(CimageConst.int_size)))
        cim.cursor = content_adress

        cipher_content = AES.new(password, AES.MODE_CFB, '0'*AES.block_size)
        cipher_content.decrypt(init_vector)
        data = zlib.decompress(cipher_content.decrypt(cim.read(content_size)))
    except BaseException:
        return {"error": "invalid session or image was corrupted"}
    except Exception:
        return {"error": "invalid session or image was corrupted"}

    return {
            'data': data, 
            'filename': title
        }


def index(request):
    if request.is_secure() == False:
        return HttpResponseRedirect('https://cimg.ru/' + request.META['QUERY_STRING'])
    filename = request.GET.get('type') == 'decrypt' and 'decrypt.html' or 'encrypt.html'

    return render(request, "index.html", {
        "input_form": EncryptForm(),
        "include_files": [filename],
        })


def encrypt(request):
    data = encrypt_function(request)
    
    if type(data) is BaseException:
        raise data
        
    if "error" in data:
        return render(request, "index.html", {
            "input_form": EncryptForm(request.POST),
            "include_files": ['encrypt.html'],
            "error": data['error'],
        })

    file = open(CimageConst.session_path + data['session_id'] + '/' + data['filename'], 'rb')
    response = HttpResponse(file.read(), content_type='application/octet-stream')
    file.close()
    os.remove(CimageConst.session_path + data['session_id'] + '/' + data['filename'])
    os.rmdir(CimageConst.session_path + data['session_id'])
    response['Content-Disposition'] = 'attachment; filename=' + data['filename']
    return response


def decrypt(request):
    if request.method == 'POST':
        data = decrypt_get_file_titles(request)   
        if type(data) is BaseException:
            raise data
        
        if "error" in data:
            return render(request, "index.html", {
                "input_form": DecryptForm(request.POST),
                "include_files": ['decrypt.html'],
                "error": data['error'],
            })
	
        response = render(request, "index.html", {
            "include_files": ["decrypt_file_titles_list.html"],
            "session_id": data['session_id'],
            "text": data['text'].decode('utf-8', 'ignore'),
            "titles": data['titles'],
            })
        response.set_signed_cookie(key='key', value=str_to_hex(data['password']), salt=str(os.path.getctime(CimageConst.session_path + data['session_id'])), max_age=1800)
        return response


    data = decrypt_get_file(request)
    if "error" in data:
        return render(request, "index.html", {
            "input_form": DecryptForm(request.POST),
            "include_files": ['decrypt.html'],
            "error": data['error'],
        })

    response = HttpResponse(data['data'], content_type='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename=' + data['filename']
    return response


def recursive_clear_dir(dir_path):
    for (dirPath, dirNames, fileNames) in os.walk(dir_path):
        for fileName in fileNames:
            path = os.path.join(dirPath, fileName)
            os.remove(path)
        for dirName in dirNames:
            path = os.path.join(dirPath, dirName)
            recursive_clear_dir(path)
            os.rmdir(path)


def sessions_clear(request):
    for (dirPath, dirNames, fileNames) in os.walk(CimageConst.session_path):
        for dirName in dirNames:
            path = os.path.join(dirPath, dirName)
            if time.time() - os.path.getctime(path) > 1800:
                recursive_clear_dir(path)
                os.rmdir(path)
                
    return HttpResponse('OK')

