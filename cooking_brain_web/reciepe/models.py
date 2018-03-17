from django.db import models

# Create your models here.
class QR_request(models.Model):
    user_id = models.CharField(primary_key=True)
    date = models.DateField
    qr_code = models.CharField(max_length=1000)