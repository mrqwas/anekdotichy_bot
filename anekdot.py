# by mrqwas

import logging
import os
import time
import threading

import requests
from dotenv import load_dotenv
from telebot import TeleBot, types


load_dotenv()

# Tokens
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ENDPOINT = os.getenv('ENDPOINT')
ENV_VARS = ('TELEGRAM_TOKEN', 'ENDPOINT')

# Numerical Constants
CUT_JOKE_LEFT = 12
CUT_JOKE_RIGHT = -2
MINUTE = 60
DEFAULT_PERIOD = 5

# Button Texts
JOKE_BUTTON = '🤡 - Анекдот'
START_NONSTOP_BUTTON = '🗣️ - Включить нонстоп'
STOP_NONSTOP_BUTTON = '✋ - Выключить нонстоп'
DOCUMENTATION_BUTTON = '📃 - Открыть документацию'

# Normal command text
DOCUMENTATION = (
    'Андекдоты4и - это бесплатный бот анекдотов.\n'
    'Анекдоты берутся с сайта http://rzhunemogu.ru/. Спасибо за апи :3\n'
    'Автор - @mrqwas - сын генерала-майора прокуратуры, '
    'так что копирование и распространение бота без его ведома запрещены.\n'
    'Если что-то в боте сломалось - смело пишите ему.\n'
    'Список команд:\n'
    '/start - Запустить бота\n'
    '/anekdot (кнопка "🤡 - Анекдот") - Получить рандомный анекдот\n'
    '/nonstop (кнопка "🗣️ - Включить нонстоп") - Включить автоматическую'
    'отправку анекдотов. Можно настраивать периодичность'
    ' (/period) и лимит (/limit).\n'
    '/stop (кнопка "✋ - Выключить нонстоп") - '
    'Отключить автоматическую отправку сообщений\n'
    '/docs (кнопка "📃 - Открыть документацию") - '
    'Документация к боту (этот текст)\n'
    '/period - Установить период отправки сообщений. '
    'Значение по умолчанию - 2 часа.'
    'Чтобы изменить этот параметр, небходимо вызвать команду и '
    'ввести период отправки сообщений В МИНУТАХ!!!\n'
    'Вроде ничего не забыл, если что - пишите @mrqwas.\n'
    '©mrqwas. Все права защищены')

GREETING_TEXT = (
    'Привет, {name}. Бот запущен, нажми /docs '
    'чтобы ознакомиться с документацией и командами')
NONSTOP_TEXT = (
    'Автоматическая отправка анекдотов включена.'
    'Нажмите /stop для остановки')
STOP_BOT_TEXT = (
    'Автоматическая отправка анекдотов остановлена.'
    'Нажмите /nonstop чтобы запустить его снова')
ASK_FOR_PERIOD_TEXT = (
    'Установите период отправки сообщения в минутах. '
    'На данный момент: {period} минут.\n'
    'Нажмите /exit для выхода.')
SET_PERIOD_DONE = 'Установлен период: {mins} минут.'
SUCCESS = 'Успешно'

# Error text
CHECK_VARS_CRITICAL = 'Отсутсвуют обязательные переменные {vars}'
GET_JOKE_ERROR = 'Ошибка при запросе к API {error}'
SEND_MESSAGE_ERROR = 'Ошибка при отправке сообщения {msg}: {error}'
STOP_BOT_ERROR = 'Ошибка при остановке бота {error}'
SET_PERIOD_ERROR = 'Ошибка {e}. Установите период отправки сообщений в минутах'

# Some vars are needed
bot = TeleBot(token=TELEGRAM_TOKEN)
current_period = DEFAULT_PERIOD
stop_sending = threading.Event()


@bot.message_handler(func=lambda msg: msg.text == STOP_NONSTOP_BUTTON)
def handle_stop_nonstop(message):
    """Handler for stop nonstop button."""
    stop_bot(message)


@bot.message_handler(func=lambda msg: msg.text == START_NONSTOP_BUTTON)
def handle_nonstop(message):
    """Handler for nonstop button."""
    nonstop(message)


@bot.message_handler(func=lambda msg: msg.text == JOKE_BUTTON)
def handle_joke(message):
    """Handler for send joke button."""
    send_joke(message)


@bot.message_handler(func=lambda msg: msg.text == DOCUMENTATION_BUTTON)
def handle_documentation(message):
    """Handler for documentation button."""
    documentation(message)


def check_vars():
    """Checking env variables for availability."""
    missing_vars = [name for name in ENV_VARS if not globals()[name]]
    if missing_vars:
        error_msg = CHECK_VARS_CRITICAL.format(vars=missing_vars)
        logging.critical(error_msg)
        raise RuntimeError(error_msg)


def get_joke():
    """Get joke from API."""
    try:
        response = requests.get(ENDPOINT)
        response.raise_for_status()
        return rf'{response.text}'[CUT_JOKE_LEFT:CUT_JOKE_RIGHT]
    except requests.RequestException as e:
        raise ConnectionError(GET_JOKE_ERROR.format(error=e))


@bot.message_handler(commands=['anekdot'])
def send_joke(message):
    """Send a joke in telegram chat."""
    try:
        joke = get_joke()
        bot.send_message(
            chat_id=message.chat.id,
            text=joke)
    except Exception as e:
        logging.exception(SEND_MESSAGE_ERROR.format(msg=joke, error=e))
        raise e


@bot.message_handler(commands=['start'])
def start_bot(message):
    """Keyboard configs and greeting."""
    chat = message.chat
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton(JOKE_BUTTON))
    keyboard.add(types.KeyboardButton(START_NONSTOP_BUTTON))
    keyboard.add(types.KeyboardButton(STOP_NONSTOP_BUTTON))
    keyboard.add(types.KeyboardButton(DOCUMENTATION_BUTTON))
    bot.send_message(
        chat_id=chat.id,
        text=GREETING_TEXT.format(
            name=chat.first_name),
        reply_markup=keyboard)


@bot.message_handler(commands=['nonstop'])
def nonstop(message):
    """Auto-sending jokes."""
    stop_sending.clear()

    def send_periodic():
        while not stop_sending.is_set():
            send_joke(message)
            time.sleep(current_period)

    threading.Thread(target=send_periodic, daemon=True).start()


@bot.message_handler(commands=['docs'])
def documentation(message):
    """Shows a documentation."""
    bot.send_message(
        chat_id=message.chat.id,
        text=DOCUMENTATION)


@bot.message_handler(commands=['stop'])
def stop_bot(message):
    """Stops sending jokes."""
    try:
        stop_sending.set()
        bot.send_message(
            chat_id=message.chat.id,
            text=STOP_BOT_TEXT,
        )
        logging.debug(STOP_BOT_TEXT)
        return True
    except Exception as e:
        logging.exception(STOP_BOT_ERROR.format(error=e))
        raise e


@bot.message_handler(commands=['period'])
def ask_for_period(message):
    """Asking user for auto-sending jokes period."""
    bot.send_message(message.chat.id, ASK_FOR_PERIOD_TEXT.format(
        period=current_period / MINUTE
    ))
    bot.register_next_step_handler(message, set_period)


def set_period(message):
    """Set a period for auto-sending jokes."""
    global current_period
    try:
        text = message.text
        chat_id = message.chat.id
        if text != '/exit':
            input_mins = float(text)
            bot.send_message(chat_id, SET_PERIOD_DONE.format(mins=input_mins))
            current_period = input_mins * MINUTE
        else:
            bot.send_message(chat_id, SUCCESS)
            current_period = DEFAULT_PERIOD
    except ValueError as e:
        bot.send_message(message.chat.id, SET_PERIOD_ERROR.format(e=e))
        bot.register_next_step_handler(message, set_period)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename=f'{__file__}.log',
        encoding='utf-8',
        format='%(asctime)s %(funcName)s %(levelname)s %(message)s'
    )
    check_vars()
    bot.polling(non_stop=True)
