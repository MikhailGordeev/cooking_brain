from django.db import models
from django.contrib.postgres.fields import JSONField

class QRRequest(models.Model):
    user_id = models.CharField(max_length=1000)
    date = models.DateField()
    qr_code = models.CharField(max_length=1000)

class ReceiptCash(models.Model):
    fn = models.BigIntegerField()
    fd = models.BigIntegerField()
    fp = models.BigIntegerField()
    receipt_raw = JSONField()

class ReceiptRequest(models.Model):
    chat_id = models.IntegerField()
    user_name = models.CharField()
    fn = models.BigIntegerField()
    fd = models.BigIntegerField()
    fp = models.BigIntegerField()

class ReceiptBotUsers(models.Model):
    chat_id = models.IntegerField()
    user_name = models.CharField()
    connection_date = models.DateTimeField(auto_now_add=True)
