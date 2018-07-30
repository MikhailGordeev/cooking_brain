from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import signal
from datetime import datetime
from qrscanner import get_qr_data
from request_receipt import request_to_nalog
from furl import furl
import re
from bot_vars import BOT_API_TOKEN, BOT_NAME, BOT_PROXY, BOT_PROXY_USER, BOT_PROXY_PASS
from bot_answers import ANSWERS
from user_logger import log_new_user
import telegram
import sys
import os
import django

sys.path.append('cooking_brain_web')
os.environ['DJANGO_SETTINGS_MODULE'] = 'cooking_brain_web.settings'
django.setup()

from receipt.models import ReceiptCash, ReceiptRequest, ReceiptBotUsers



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
    # Log new user info
    log_new_user(update)
    text = "Привет, {}! Я умею читать QR-коды с чеков и присылать в ответ чек в текстовом виде. Пришли мне фото QR-кода и получи ответ".format(update.message.from_user.first_name)
    logging.info('Пользователь {} нажал /start'.format(update.message.chat.username))
    update.message.reply_text(text)


def check_photo_from(bot, update):
    logging.info(update)
    # Log new user info
    log_new_user(update)
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
    os.remove(file_name)
    check_requested_text(fn, fd, fp, update, bot)


def check_requested_text(fn, fd, fp, update, bot):

    # Log unique request
    if update.message.chat.username is None:
        user_name = 'empty'
    else:
        user_name = update.message.chat.username
    check_receipt_request = ReceiptRequest.objects.filter(fn=fn, fd=fd, fp=fp, user_name=user_name, chat_id=update.message.chat.id)
    if check_receipt_request.count() > 0:
        pass
    else:
        save_request = ReceiptRequest(fn=fn, fd=fd, fp=fp, user_name=user_name, chat_id=update.message.chat.id)
        save_request.save()

    # If receipt exist in local db, send response from it
    check_receipt_in_db = ReceiptCash.objects.filter(fn=fn, fd=fd, fp=fp)
    if check_receipt_in_db.count() > 0:
        rc = check_receipt_in_db[0]
        response = rc.receipt_raw
    else:
        response = request_to_nalog(fp, fd, fn, update, bot)
        if response is not None:
            rc = ReceiptCash(fn=fn, fd=fd, fp=fp, receipt_raw=response)
            print(response)
            rc.save()
        else:
            return
    #future cash model
    #user = ReceiptBotUsers.objects.get(chat_id=update.message.chat.id)
    #rc.users.add(user)
    #print(user.receiptcash_set.all())


    # print receipt
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


def check_message_from(bot, update):
    logging.info(update)
    check_text = update.message.text.lower()
    logging.info(check_text)

    # Если обращаются в ЛС
    if update.message.chat_id > 0:
        logging.info("Сообщение в ЛС " + check_text)
        talk_to_me(check_text, update, bot)

    elif update.message.chat_id < 0:

        # отвечать в группе только если к тебе обращаются
        if BOT_NAME in check_text:
            check_text = check_text.split(BOT_NAME, 1)[1].lstrip()
            logging.info("Сообщение в Группе " + check_text)
            talk_to_me(check_text, update, bot)

    if BOT_NAME in check_text:
        check_text = check_text.split(BOT_NAME, 1)[1].lstrip()
        logging.info("Сообщение в Группе " + check_text)
        talk_to_me(check_text, update, bot)


def talk_to_me(user_text, replay, bot):
    # Реакция на ключевую фразу сообщением
    #if user_text in bot_vars.GROUP_MESSAGES:
    #    logging.info('Пользователь {} получил сообщение {}'.format(replay.message.chat.username, bot_vars.GROUP_MESSAGES[user_text]))
    #    replay.message.reply_text(bot_vars.GROUP_MESSAGES[user_text])
    # Если знает ответ, скажет - answer[user_text]
    f = furl('/?{}'.format(user_text))
    if user_text in ANSWERS:
        logging.info('Пользователь {} получил ответ {}'.format(replay.message.chat.username, ANSWERS[user_text]))
        replay.message.reply_text(ANSWERS[user_text])
    else:
        try:
            # Fiscal storage (Номер фискального накопителя - ФН)
            fn = f.args['fn']
            # Fiscal document number (Номер фискального документа - ФД)
            fd = f.args['i']
            # Fiscal sign (Подпись фискального документа - ФП)
            fp = f.args['fp']
        except KeyError:
            replay.message.reply_text(
                'Извините, не нешел нужной информации для получения чека, распознанный текст: {}'.format(user_text))
        return check_requested_text(fn, fd, fp, replay, bot)


def main():
    print("Bot {} is running".format(BOT_NAME))
    REQUEST_KWARGS = {
        'proxy_url': BOT_PROXY,
        # Optional, if you need authentication:
        'urllib3_proxy_kwargs': {
            'username': BOT_PROXY_USER,
            'password': BOT_PROXY_PASS,
        }
    }
    updater = Updater(BOT_API_TOKEN, request_kwargs=REQUEST_KWARGS)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", greet_user))
    dp.add_handler(MessageHandler(Filters.photo, check_photo_from))
    dp.add_handler(MessageHandler(Filters.text, check_message_from))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    logging.info('Bot started')
    main()

logging.info('Bot has stopped')
