# Generated by Django 2.0.3 on 2018-03-17 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='QRRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.CharField(max_length=1000)),
                ('date', models.DateField()),
                ('qr_code', models.CharField(max_length=1000)),
            ],
        ),
    ]