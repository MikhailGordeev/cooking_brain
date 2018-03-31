import uuid
import requests
from auth import phone, pin

def request_to_nalog(fp, fd, fn, update):
    dev_id = str(uuid.uuid4()).replace('-', '')
    # DeviceID
    dev_os = 'Adnroid 4.4.4'
    # Protocol version
    proto = '2'
    # Client version
    client = '1.4.1.3'
    # User agent
    uagent = 'okhttp/3.0.1'
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

    response = requests.get(request_receipt, headers=headers, params=data_request, auth=(phone, pin))

    if response.status_code == 200:
        return response.json()
    else:
        response = requests.get(request_receipt, headers=headers, params=data_request, auth=(phone, pin))
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 406:
            return update.message.reply_text('Чек ещё не поступил в базу данных, повторите попытку чуть позже.')
        else:
            return update.message.reply_text('База данных не отвечает, повторите попытку чуть позже.')