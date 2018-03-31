from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import signal
from datetime import datetime
from qrscanner import get_qr_data
from request_reciept import request_to_nalog
from furl import furl
import re
from bot_vars import BOT_API_TOKEN, BOT_NAME
import telegram
import sys
import os
import django
sys.path.append('cooking_brain_web')
os.environ['DJANGO_SETTINGS_MODULE'] = 'cooking_brain_web.settings'
django.setup()

from reciept.models import ReceiptCash



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
        # Fiscal document number (Номер фискального документа - ФД)
        fd = f.args['i']
        # Fiscal sign (Подпись фискального документа - ФП)
        fp = f.args['fp']
    except KeyError:
        update.message.reply_text('Извините, не нешел нужной информации для получения чека, распознанный текст: {}'.format(decode_result))
        return os.remove(file_name)

    check_reciept_in_db = ReceiptCash.objects.filter(fn=fn, fd=fd, fp=fp)
    if check_reciept_in_db.count() > 0:
        response = check_reciept_in_db[0].receipt_raw
    else:
        response = request_to_nalog(fp, fd, fn, update)
        rc = ReceiptCash(fn=fn, fd=fd, fp=fp, receipt_raw=response)
        rc.save()

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
    print("Bot {} is running".format(BOT_NAME))
    updater = Updater(BOT_API_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", greet_user))
    dp.add_handler(MessageHandler(Filters.photo, check_photo_from))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    logging.info('Bot started')
    main()

logging.info('Bot has stopped')
