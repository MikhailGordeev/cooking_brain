from django.db import models

# Create your models here.
class QRRequest(models.Model):
    user_id = models.CharField(max_length=1000)
    date = models.DateField()
    qr_code = models.CharField(max_length=1000)