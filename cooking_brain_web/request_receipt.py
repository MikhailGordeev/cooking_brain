import uuid
import requests
from auth import phone, pin
import time
import telegram

def request_to_nalog(fp, fd, fn, update, bot):
    dev_id = str(uuid.uuid4()).replace('-', '')
    # DeviceID
    dev_os = 'Adnroid 6.4.4'
    # Protocol version
    proto = '2'
    # Client version
    client = '1.5.1.3'
    # User agent
    uagent = 'okhttp/5.2.1'
    # Base URL
    base = 'https://proverkacheka.nalog.ru:9999'
    headers = {
        'Device-Id': dev_id,
        'Device-OS': dev_os,
        'Version': proto,
        'ClientVersion': client,
        'User-Agent': uagent
    }

    data_request = [
        ('fiscalSign', fp),
        ('sendToEmail', 'no'),
    ]
    request_receipt = "%s/v1/inns/*/kkts/*/fss/%s/tickets/%s" % (base, fn, fd)
    bot.send_chat_action(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    response = requests.get(request_receipt, headers=headers, params=data_request, auth=(phone, pin))
    # TODO
    # Переписать в цикл, добавить слип
    if response.status_code == 200:
        return response.json()
    else:
        bot.send_chat_action(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
        time.sleep(5)
        bot.send_chat_action(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
        response = requests.get(request_receipt, headers=headers, params=data_request, auth=(phone, pin))
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 406:
            update.message.reply_text('Чек ещё не поступил в базу данных ФНС, повторите попытку чуть позже.')
        elif response.status_code == 500:
            update.message.reply_text('Сервера ФНС упали. Попробуйте ещё раз чуть позже')
        elif response.status_code == 404:
            update.message.reply_text('Упс, возможно ваш чек утерян в недрах ФНС. Попробуйте ещё раз чуть позже')
        else:
            update.message.reply_text('База данных ФНС не отвечает, повторите попытку чуть позже.')