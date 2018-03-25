from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import bot_vars
import logging
import signal
from datetime import datetime
from qrscanner import get_qr_data
import uuid
from furl import furl
import requests
import re
from auth import phone, pin
import os


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self):
        self.kill_now = True


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='bot.log'
                    )


def greet_user(bot, update):
    logging.info(update)
    text = "Привет, {}! Я умею читать QR-коды с чеков и присылать в ответ чек в текстовом виде. Пришли мне фото QR-кода и получи ответ".format(update.message.from_user.first_name)
    logging.info('Пользователь {} нажал /start'.format(update.message.chat.username))
    update.message.reply_text(text)


def check_photo_from(bot, update):
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
    logging.info(update)
    file_id = update.message.photo[-1]
    newFile = bot.get_file(file_id)
    file_name = '{}.jpg'.format(file_id['file_id'])
    newFile.download(file_name)
    try:
        f = furl('/?{}'.format(get_qr_data(file_name)[0].decode("utf-8")))
    except TypeError:
       update.message.reply_text('Извините, я не могу найти QR-код, попробуйте отправить фото ещё раз')
       return os.remove(file_name)

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

    response = requests.get(request_receipt, headers=headers, params=data_request, auth=(phone, pin)).json()
    n = 0
    receipt_txt = ''


    total_sum = response['document']['receipt']['totalSum'] * 0.01

    try:
        user = response['document']['receipt']['user']
        #update.message.reply_text(user)
        receipt_txt += '{}\n'.format(user)
    except KeyError:
        # Key is not present
        pass
    try:
        retail_place_address = response['document']['receipt']['retailPlaceAddress']
        #update.message.reply_text(retail_place_address)
        receipt_txt += '{}\n'.format(retail_place_address)
    except KeyError:
        # Key is not present
        pass
    try:
        user_inn = response['document']['receipt']['userInn']
        #update.message.reply_text('ИНН {}\n'.format(user_inn))
        receipt_txt += 'ИНН {}\n'.format(user_inn)

    except KeyError:
        # Key is not present
        pass
    #update.message.reply_text(datetime(*map(int, re.split('[^\d]', response['document']['receipt']['dateTime']))).strftime('%d.%m.%Y %H:%M'))
    receipt_txt += '{}\n'.format(datetime(*map(int, re.split('[^\d]', response['document']['receipt']['dateTime']))).strftime('%d.%m.%Y %H:%M'))
    #update.message.reply_text('Чек № {}'.format(response['document']['receipt']['requestNumber']))
    receipt_txt += 'Чек № {}\n'.format(response['document']['receipt']['requestNumber'])
    try:
        shift_number = response['document']['receipt']['shiftNumber']
        #update.message.reply_text('Смена № {}'.format(shift_number))
        receipt_txt += 'Смена № {}\n'.format(shift_number)
    except KeyError:
        # Key is not present
        pass
    #update.message.reply_text('Кассир {}'.format(response['document']['receipt']['operator']))
    receipt_txt += 'Кассир {}\n'.format(response['document']['receipt']['operator'])
    #update.message.reply_text('Приход')
    receipt_txt += 'Приход\n'
    #update.message.reply_text('-------------------------------------------------------------------')
    receipt_txt += '----------------------------\n'
    #update.message.reply_text('№  Название                              Цена    Кол.    Сумма')
    receipt_txt += '№  Название                              Цена    Кол.    Сумма\n'
    for i in response['document']['receipt']['items']:
        n += 1
        price = i['price'] * 0.01
        sum = i['sum'] * 0.01
        #update.message.reply_text('{}  {}   {:,.2f}       {}      {:,.2f}'.format(n, i['name'], price, i['quantity'], sum))
        receipt_txt += '{}  {}   {:,.2f}       {}      {:,.2f}\n'.format(n, i['name'], price, i['quantity'], sum)
    #update.message.reply_text('-------------------------------------------------------------------')
    receipt_txt += '----------------------------\n'
    #update.message.reply_text('Итого: {:,.2f}'.format(total_sum))
    receipt_txt += 'Итого: {:,.2f}'.format(total_sum)
    update.message.reply_text(receipt_txt)
    os.remove(file_name)


def main():
    print("Bot receipt_helper_bot is running")
    updater = Updater(bot_vars.BOT_API_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", greet_user))
    dp.add_handler(MessageHandler(Filters.photo, check_photo_from))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    logging.info('Bot started')
    main()

logging.info('Bot has stopped')
