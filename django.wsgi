import os, sys

reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')

sys.path.append('/var/www/ksan/data/www/cimg.ru')

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()