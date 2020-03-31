from Crypto.Cipher import AES
# from Crypto.Cipher import AES
from django.db import models
from binascii import b2a_hex, a2b_hex

class Owner(models.Model):
    username = models.CharField(max_length = 32)
    password = models.CharField(max_length = 32)
    nickname = models.CharField(max_length = 32)
    phone = models.CharField(max_length = 32)
    address = models.CharField(max_length = 64)
    email = models.EmailField()

class EmailValid(models.Model):
    value = models.CharField(max_length = 32)
    email_address = models.EmailField()
    times = models.DateTimeField()

class Product(models.Model):
    product_bcId = models.CharField(max_length = 32)
    product_name = models.CharField(max_length = 32)
    product_version = models.CharField(max_length= 32)
    product_category = models.CharField(max_length= 32)
    product_hashLink = models.CharField(max_length= 64)
    product_descLink = models.CharField(max_length= 64)
    product_status = models.BooleanField()
    product_state = models.CharField(max_length=512)
    product_price = models.CharField(max_length=128)
    product_show_time = models.DateField()
    product_blocknum = models.BigIntegerField()
    product_timestamp =models.BigIntegerField()
    product_transactionHash =models.CharField(max_length= 128)
    product_suffix = models.CharField(max_length= 64)
    product_index = models.IntegerField()
    product_address = models.CharField(max_length= 128)
    product_key = models.CharField(max_length= 64)
    product_offset = models.CharField(max_length=64)
    product_verify = models.IntegerField()
    owner = models.ForeignKey(Owner, on_delete=True)

class Image(models.Model):
    img_adress = models.ImageField(upload_to = "image")
    img_label = models.CharField(max_length = 32)
    img_description= models.TextField()
    product = models.ForeignKey(Product, on_delete=True)

class Password1(models.Model):
    product_bcId = models.CharField(max_length = 32)
    product_permit = models.IntegerField()
    product_address = models.CharField(max_length= 128)
    password = models.CharField(max_length= 16)


class Password2(models.Model):
    product_bcId = models.CharField(max_length = 32)
    product_permit = models.IntegerField()
    product_address = models.CharField(max_length= 128)
    password = models.CharField(max_length= 16)

class PrpCrypt(object):

    def __init__(self, key,offset):
        self.key = key.encode()
        self.offset = offset.encode()
        self.mode = AES.MODE_CBC

    def encrypt(self, text):
        cryptor = AES.new(self.key, self.mode, self.offset)
        length = 16
        count = len(text)
        if count < length:
            add = (length - count)
            text = text + ('\0'.encode() * add)
        elif count > length:
            add = (length - (count % length))
            text = text + ('\0'.encode() * add)
        self.ciphertext = cryptor.encrypt(text)
        return b2a_hex(self.ciphertext)

    def decrypt(self, text):
        cryptor = AES.new(self.key, self.mode, self.offset)
        plain_text = cryptor.decrypt(a2b_hex(text))
        return plain_text.rstrip('\0'.encode())