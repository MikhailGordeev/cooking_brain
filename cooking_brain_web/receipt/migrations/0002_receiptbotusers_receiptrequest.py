# Generated by Django 2.0.3 on 2018-04-01 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('receipt', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReceiptBotUsers',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat_id', models.IntegerField()),
                ('user_name', models.CharField(max_length=64)),
                ('connection_date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ReceiptRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat_id', models.IntegerField()),
                ('user_name', models.CharField(max_length=64)),
                ('fn', models.BigIntegerField()),
                ('fd', models.BigIntegerField()),
                ('fp', models.BigIntegerField()),
            ],
        ),
    ]
