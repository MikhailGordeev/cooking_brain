# Generated by Django 2.0.3 on 2018-04-01 11:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('receipt', '0003_auto_20180401_1130'),
    ]

    operations = [
        migrations.RenameField(
            model_name='receiptbotusers',
            old_name='telegr_chat_id',
            new_name='chat_id',
        ),
        migrations.RenameField(
            model_name='receiptbotusers',
            old_name='telegr_connection_date',
            new_name='connection_date',
        ),
        migrations.RenameField(
            model_name='receiptbotusers',
            old_name='telegr_user_name',
            new_name='user_name',
        ),
        migrations.RenameField(
            model_name='receiptrequest',
            old_name='telegr_chat_id',
            new_name='chat_id',
        ),
        migrations.RenameField(
            model_name='receiptrequest',
            old_name='telegr_user_name',
            new_name='user_name',
        ),
    ]