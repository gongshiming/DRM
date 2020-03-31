from django.db import models

from Owner.models import Product, Owner


class Buyer(models.Model):
    username = models.CharField(max_length = 32)
    password = models.CharField(max_length = 32)
    nickname = models.CharField(max_length = 32)
    phone = models.CharField(max_length = 32)
    address = models.CharField(max_length = 64)
    email = models.EmailField()

class Msg(models.Model):
    msg = models.CharField(max_length= 512)
    time = models.CharField(max_length=128)
    type = models.IntegerField()
    product = models.ForeignKey(Product,on_delete=True)
    buyer = models.ForeignKey(Buyer,on_delete=True)
    owner = models.ForeignKey(Owner,on_delete=True)

class PurchaseMessage(models.Model):
    permission = models.CharField(max_length=32)
    blocknum = models.BigIntegerField()
    purchaseId = models.BigIntegerField()
    timestamp = models.BigIntegerField()
    time = models.CharField(max_length=32)
    transactionHash =models.CharField(max_length= 128)
    product = models.ForeignKey(Product,on_delete=True)
    buyer = models.ForeignKey(Buyer,on_delete=True)

class Purchase():
    pass


