import time
import sys
import os
import django
sys.path.append('cooking_brain_web')
os.environ['DJANGO_SETTINGS_MODULE'] = 'cooking_brain_web.settings'
django.setup()
from receipt.models import ReceiptBotUsers

def log_new_user(update):
    if update.message.chat.username is None:
        user_name = 'empty'
    else:
        user_name = update.message.chat.username
    check_user = ReceiptBotUsers.objects.filter(user_name=user_name, chat_id=update.message.chat.id)
    if check_user.count() > 0:
        pass
    else:
        ts = int(time.time())
        save_user = ReceiptBotUsers(user_name=user_name, chat_id=update.message.chat.id, connection_date=ts)
        return save_user.save()
