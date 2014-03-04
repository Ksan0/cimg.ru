from PIL import Image, ImageDraw
import random


class CIM:
    def __init__(self, img, ibits_count):
        self.__img = img
        self.__img_width  = img.size[0]
        self.__img_draw   = ImageDraw.Draw(img)

        self.cursor = 0
        self.ibits  = ibits_count


    # convert n bytes of int to binary string
    @staticmethod
    def i2bs(val, n = 4):
        bstr = str()
        for i in range(n):
            bstr += chr(val & 0xFF)
            val >>= 8
        return bstr


    # convert binary string to int
    @staticmethod
    def bs2i(bstr):
        val = 0
        i = 0
        for ch in bstr:
            val |= ord(ch) << 8*i
            i += 1
        return val


    # data = data_to_save, type = str
    def write(self, data, upto_ibits=0):
        pixel_cursor = self.cursor / 24
        byte_cursor = (self.cursor % 24) / 8
        bit_cursor = (self.cursor % 24) % 8

        first_good_bit = 8 - self.ibits

        pixel = self.__img.getpixel((pixel_cursor%self.__img_width, pixel_cursor/self.__img_width))

        for data_char in data:
            if bit_cursor < first_good_bit:
                bit_cursor = first_good_bit
            data_byte = ord(data_char)
            data_byte_bits_count = 8
            while data_byte_bits_count > 0:
                tmp = (data_byte << (8 - data_byte_bits_count)) & 0xFF
                tmp >>= bit_cursor
                tmp2 = pixel[byte_cursor] >> (8 - bit_cursor) << (8 - bit_cursor)  # tmp2 = pixel[byte_cursor]
                tmp2 |= tmp

                if upto_ibits > self.ibits:
                    rand_byte = ((random.randint(0, 255) >> self.ibits << (self.ibits + 8 - upto_ibits)) & 0xFF) >> (8 - upto_ibits) 
                    clr_byte  = ((0xFF >> self.ibits << (self.ibits + 8 - upto_ibits)) & 0xFF) >> (8 - upto_ibits) 
                    clr_byte = (~clr_byte) & 0xFF
                    tmp2 = (tmp2 & clr_byte) | rand_byte

                if byte_cursor == 0:
                    pixel = (tmp2, pixel[1], pixel[2])
                elif byte_cursor == 1:
                    pixel = (pixel[0], tmp2, pixel[2])
                else:
                    pixel = (pixel[0], pixel[1], tmp2)

                used_bits = 8 - bit_cursor
                if data_byte_bits_count < used_bits:
                    used_bits = data_byte_bits_count

                data_byte_bits_count -= used_bits
                bit_cursor += used_bits
                if bit_cursor >= 8:
                    if byte_cursor == 2:
                        self.__img_draw.point((pixel_cursor%self.__img_width, pixel_cursor/self.__img_width), pixel)
                        pixel_cursor += 1
                        byte_cursor = 0
                        bit_cursor = 0
                        pixel = self.__img.getpixel((pixel_cursor%self.__img_width, pixel_cursor/self.__img_width))
                    else:
                        byte_cursor += 1
                        bit_cursor = 0

                if data_byte_bits_count > 0:
                    bit_cursor = first_good_bit
                else:
                    self.__img_draw.point((pixel_cursor%self.__img_width, pixel_cursor/self.__img_width), pixel) 

        self.cursor = pixel_cursor * 24 + byte_cursor * 8 + bit_cursor


    def miss(self, bytes_count):
        pixel_cursor = self.cursor / 24
        byte_cursor = (self.cursor % 24) / 8
        bit_cursor = (self.cursor % 24) % 8

        first_good_bit = 8 - self.ibits

        for data_char in range(bytes_count):
            if bit_cursor < first_good_bit:
                bit_cursor = first_good_bit
            data_byte_bits_count = 8
            while data_byte_bits_count > 0:
                used_bits = 8 - bit_cursor
                if data_byte_bits_count < used_bits:
                    used_bits = data_byte_bits_count

                data_byte_bits_count -= used_bits
                bit_cursor += used_bits
                if bit_cursor >= 8:
                    if byte_cursor == 2:
                        pixel_cursor += 1
                        byte_cursor = 0
                        bit_cursor = 0
                    else:
                        byte_cursor += 1
                        bit_cursor = 0

                if data_byte_bits_count > 0:
                    bit_cursor = first_good_bit

        self.cursor = pixel_cursor * 24 + byte_cursor * 8 + bit_cursor


    # bytes_count, type = int
    def read(self, bytes_count):
        pixel_cursor = self.cursor / 24
        byte_cursor = (self.cursor % 24) / 8
        bit_cursor = (self.cursor % 24) % 8

        first_good_bit = 8 - self.ibits

        pixel = self.__img.getpixel((pixel_cursor%self.__img_width, pixel_cursor/self.__img_width))
        readed_string = str()

        for i in range(bytes_count):
            if bit_cursor < first_good_bit:
                bit_cursor = first_good_bit
            data_byte = 0  # byte reading now
            data_byte_bits_count = 8  # bits to read
            while data_byte_bits_count > 0:
                tmp = (pixel[byte_cursor] << bit_cursor) & 0xFF
                tmp >>= (8 - data_byte_bits_count)
                data_byte |= tmp

                used_bits = 8 - bit_cursor
                if data_byte_bits_count < used_bits:
                    used_bits = data_byte_bits_count

                data_byte_bits_count -= used_bits
                bit_cursor += used_bits

                if bit_cursor >= 8:
                    if byte_cursor == 2:
                        pixel_cursor += 1
                        byte_cursor = 0
                        bit_cursor = 0
                        pixel = self.__img.getpixel((pixel_cursor%self.__img_width, pixel_cursor/self.__img_width))
                    else:
                        byte_cursor += 1
                        bit_cursor = 0

                if data_byte_bits_count > 0:
                    bit_cursor = first_good_bit

            readed_string += chr(data_byte)

        self.cursor = pixel_cursor * 24 + byte_cursor * 8 + bit_cursor
        return readed_string
