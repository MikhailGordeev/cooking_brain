from django.db import models
from django.contrib.postgres.fields import JSONField

# Create your models here.
class QRRequest(models.Model):
    user_id = models.CharField(max_length=1000)
    date = models.DateField()
    qr_code = models.CharField(max_length=1000)

class ReceiptCash(models.Model):
    fn = models.BigIntegerField()
    fd = models.BigIntegerField()
    fp = models.BigIntegerField()
    receipt_raw = JSONField()