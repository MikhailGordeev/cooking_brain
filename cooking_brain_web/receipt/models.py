from django.db import models
from django.contrib.postgres.fields import JSONField


class QRRequest(models.Model):
    user_id = models.CharField(max_length=1000)
    date = models.DateField()
    qr_code = models.CharField(max_length=1000)


class ReceiptRequest(models.Model):
    chat_id = models.IntegerField()
    user_name = models.CharField(max_length=64)
    fn = models.BigIntegerField()
    fd = models.BigIntegerField()
    fp = models.BigIntegerField()


class ReceiptBotUsers(models.Model):
    chat_id = models.IntegerField()
    user_name = models.CharField(max_length=64)
    connection_date = models.DateTimeField(auto_now_add=True)


class ReceiptCash(models.Model):
    users = models.ManyToManyField(ReceiptBotUsers)
    fn = models.BigIntegerField()
    fd = models.BigIntegerField()
    fp = models.BigIntegerField()
    receipt_raw = JSONField()