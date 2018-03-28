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
import telegram


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
    new_file = bot.get_file(file_id)
    file_name = '{}.jpg'.format(file_id['file_id'])
    new_file.download(file_name)
    try:
        decode_result = get_qr_data(file_name)[0].data.decode("utf-8")
        f = furl('/?{}'.format(decode_result))
        bot.send_chat_action(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    except TypeError:
       update.message.reply_text('Извините, я не могу найти QR-код, попробуйте отправить фото ещё раз')
       return os.remove(file_name)
    except IndexError:
       update.message.reply_text('Извините, я не могу найти QR-код, попробуйте отправить фото ещё раз')
       return os.remove(file_name)
    except AttributeError:
       update.message.reply_text('Извините, я не могу найти QR-код, попробуйте отправить фото ещё раз')
       return os.remove(file_name)

    try:
        # Fiscal storage (Номер фискального накопителя - ФН)
        fn = f.args['fn']
        fd = f.args['i']
        # Fiscal sign (Подпись фискального документа - ФП)
        fp = f.args['fp']
    except KeyError:
        update.message.reply_text('Извините, не нешел нужной информации для получения чека, распознанный текст: {}'.format(decode_result))
        return os.remove(file_name)
    # Fiscal document number (Номер фискального документа - ФД)

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
        response = response.json()
    else:
        response = requests.get(request_receipt, headers=headers, params=data_request, auth=(phone, pin))
        if response.status_code == 200:
            response = response.json()
        else:
            return update.message.reply_text('База данных не отвечает, повторите попытку чуть позже.')

    n = 0
    receipt_txt = ''


    total_sum = response['document']['receipt']['totalSum'] * 0.01

    try:
        user = response['document']['receipt']['user']
        receipt_txt += '{}\n'.format(user)
    except KeyError:
        # Key is not present
        pass
    try:
        retail_place_address = response['document']['receipt']['retailPlaceAddress']
        receipt_txt += '{}\n'.format(retail_place_address)
    except KeyError:
        # Key is not present
        pass
    try:
        user_inn = response['document']['receipt']['userInn']
        receipt_txt += 'ИНН {}\n'.format(user_inn)

    except KeyError:
        # Key is not present
        pass
    receipt_txt += '{}\n'.format(datetime(*map(int, re.split('[^\d]', response['document']['receipt']['dateTime']))).strftime('%d.%m.%Y %H:%M'))
    receipt_txt += 'Чек № {}\n'.format(response['document']['receipt']['requestNumber'])
    try:
        shift_number = response['document']['receipt']['shiftNumber']
        receipt_txt += 'Смена № {}\n'.format(shift_number)
    except KeyError:
        # Key is not present
        pass
    receipt_txt += 'Кассир {}\n'.format(response['document']['receipt']['operator'])
    receipt_txt += 'Приход\n'
    receipt_txt += '----------------------------\n'
    receipt_txt += '№  Название                              Цена    Кол.    Сумма\n'
    for i in response['document']['receipt']['items']:
        n += 1
        price = i['price'] * 0.01
        sum = i['sum'] * 0.01
        receipt_txt += '{}  {}   {:,.2f}       {}      {:,.2f}\n'.format(n, i['name'], price, i['quantity'], sum)
    receipt_txt += '----------------------------\n'
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
