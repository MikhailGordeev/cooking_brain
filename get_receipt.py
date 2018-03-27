import uuid
from qrscanner import get_qr_data
from furl import furl
import requests

#
# Place .netrc in home directory with format "machine proverkacheka.nalog.ru login {you phone number} password {pin from sms}"
#
# Place your receipt photo with QR code in project root directory
# Receipt QR code
qr_file = 'qr.png'

# Random device ID
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

f = furl('/?{}'.format(get_qr_data(qr_file)[0].decode("utf-8")))

# Fiscal storage (Номер фискального накопителя - ФН)
fn = f.args['fn']
# Fiscal document number (Номер фискального документа - ФД)
fd = f.args['i']
# Fiscal sign (Подпись фискального документа - ФП)
fp = f.args['fp']

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

response = requests.get(request_receipt, headers=headers, params=data_request)

print(response.json())