import datetime
import logging.config
import re
from typing import List, Any

import telebot
from decouple import config
from telegram_bot_calendar import WMonthTelegramCalendar

from botrequests.bestdeal import get_list_hotels_bestdeal
from botrequests.history import SQLighter
from botrequests.lowprice_and_highprice import get_list_hotels
from botrequests.users import User
from logging_config import dict_config
from src.config import DATABASE_NAME

TOKEN = config('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

logging.config.dictConfig(dict_config)
logger = logging.getLogger('main')


@bot.message_handler(commands=['start'])
def command_start(message: Any) -> None:
    """ Функция для обработки команды /start и вывода клавиатуры с командами бота"""
    logger.info(f'Пользователь {message.from_user.id} ввёл команду {message.text}')
    start_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    start_markup.row('/start', '/help', '/lowprice')
    start_markup.row('/highprice', '/bestdeal', '/history')
    bot.send_message(message.from_user.id,
                     '🤖 Привет, я бот для поиска отелей на Hotels.com.\n'
                     '\n'
                     'Мои функции:\n\n'
                     '/lowprice - вывод самых дешёвых отелей в городе.\n'
                     '/highprice - вывод самых дорогих отелей в городе.\n'
                     '/bestdeal - вывод отелей, наиболее подходящих по цене и расположению от центра.\n'
                     '/history - вывод истории поиска отелей.\n'
                     '/help - помощь по командам бота',
                     reply_markup=start_markup)


@bot.message_handler(commands=['help'])
def command_help(message: Any) -> None:
    """ Функция для обработки команды /help"""
    logger.info(f'Пользователь {message.from_user.id} ввёл команду {message.text}')
    bot.send_message(message.from_user.id,
                     'Мои функции:\n\n'
                     '/lowprice - вывод самых дешёвых отелей в городе.\n'
                     '/highprice - вывод самых дорогих отелей в городе.\n'
                     '/bestdeal - вывод отелей, наиболее подходящих по цене и расположению от центра.\n'
                     '/history - вывод истории поиска отелей.\n'
                     '/help - помощь по командам бота')


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def command_lowprice_or_highprice_or_bestdeal(message: Any) -> None:
    """Функция для обработки комманд бота и сортировки поиска отелей"""
    current_user = User.get_user(user_id=message.from_user.id)
    logger.info(f'Пользователь {message.from_user.id} ввёл команду "{message.text}"')
    if message.text == '/lowprice':
        current_user.command = message.text
        current_user.sortorder = 'PRICE'
        bot.send_message(message.from_user.id, 'Введите город для поиска')
        bot.register_next_step_handler(message, quantity_hotels)
    elif message.text == '/highprice':
        current_user.command = message.text
        current_user.sortorder = 'PRICE_HIGHEST_FIRST'
        bot.send_message(message.from_user.id, 'Введите город для поиска')
        bot.register_next_step_handler(message, quantity_hotels)
    elif message.text == '/bestdeal':
        current_user.command = message.text
        bot.send_message(message.from_user.id, 'Введите город для поиска')
        bot.register_next_step_handler(message, range_of_prices)


def range_of_prices(message: Any) -> None:
    """Функция для обработки искомого города, при использовании команды /bestdeal"""
    logger.info(f'Пользователь {message.from_user.id} ищет город "{message.text}"')
    current_user = User.get_user(user_id=message.from_user.id)
    current_user.city = message.text
    bot.send_message(message.from_user.id, 'Выберите диапазон цен в формате(1000/3000)')
    bot.register_next_step_handler(message, distances_from_center)


def distances_from_center(message: Any) -> None:
    """ Функция для обработки диапазона цен"""
    current_user = User.get_user(user_id=message.from_user.id)
    try:
        if re.search(r'\d+/\d+', message.text) is None:
            raise ValueError
        if int(message.text.split('/')[0]) > int(message.text.split('/')[1]):
            raise TypeError
        logger.info(f'Пользователь {message.from_user.id} ввёл диапазон цен "{message.text}"')
        current_user.price_range = message.text
        bot.send_message(message.from_user.id,
                         'Выберите расстояние, на котором находится отель от центра(в километрах)')
        bot.register_next_step_handler(message, check_distance)
    except ValueError as e:
        logger.exception(f'Пользователь {message.from_user.id} ввёл неверный диапазон цен', e)
        bot.send_message(message.from_user.id, 'Выбранный диапазон цен не соответствует формату(1000/3000)')
        bot.register_next_step_handler(message, distances_from_center)
    except TypeError as e:
        logger.exception(f'Пользователь {message.from_user.id} ввёл начальную цену больше конечной', e)
        bot.send_message(message.from_user.id, 'Начальная цена должна быть меньше конечной')
        bot.register_next_step_handler(message, distances_from_center)


def check_distance(message: Any) -> None:
    """ Функция для обработки расстояния"""
    current_user = User.get_user(user_id=message.from_user.id)
    try:
        int(message.text)
        logger.info(f'Пользователь {message.from_user.id} ввёл расстояние от центра "{message.text}" км')
        current_user.distance = message.text
        bot.send_message(message.from_user.id, 'Сколько отелей найти?')
        bot.register_next_step_handler(message, show_photo)
    except ValueError as e:
        logger.exception(f'Пользователь {message.from_user.id} ввёл не число', e)
        bot.send_message(message.from_user.id, 'Расстояние необходимо указать числом в километрах')
        bot.register_next_step_handler(message, check_distance)


def quantity_hotels(message: Any) -> None:
    """ Функция для обработки искомого города"""
    logger.info(f'Пользователь {message.from_user.id} ищет город "{message.text}"')
    current_user = User.get_user(user_id=message.from_user.id)
    current_user.city = message.text
    bot.send_message(message.from_user.id, 'Сколько отелей найти?')
    bot.register_next_step_handler(message, show_photo)


def show_photo(message: Any) -> None:
    """ Функция для обработки количества отелей"""
    current_user = User.get_user(user_id=message.from_user.id)
    try:
        int(message.text)
        logger.info(f'Пользователь {message.from_user.id} ввёл кол-во отелей "{message.text}"')
        current_user.quantity_hotels = message.text
        bot.send_message(message.from_user.id, 'Показать фотографии отелей?')
        bot.register_next_step_handler(message, quantity_photo)
    except ValueError as e:
        logger.exception(f'Пользователь {message.from_user.id} ввёл не число', e)
        bot.send_message(message.chat.id, 'Кол-во отелей укажите числом')
        bot.register_next_step_handler(message, show_photo)


def quantity_photo(message: Any) -> None:
    """Функция для обработки условия показывать фотографии отелей пользователю или нет"""
    current_user = User.get_user(user_id=message.from_user.id)
    if message.text.lower() in ['да', 'нет']:
        current_user.show_photo = message.text
        if message.text.lower() == 'да':
            logger.info(f'Пользователь {message.from_user.id} хочет видеть фото отелей')
            bot.send_message(message.from_user.id, 'Сколько штук(не больше 10)?')
            bot.register_next_step_handler(message, checking_for_quantity_of_photo)
        else:
            logger.info(f'Пользователь {message.from_user.id} не хочет видеть фото отелей')
            check_in(message=message)
    else:
        bot.send_message(message.chat.id, 'Необходимо указать <b>да</b> или <b>нет</b>', parse_mode='HTML')
        bot.register_next_step_handler(message, quantity_photo)


def checking_for_quantity_of_photo(message: Any) -> None:
    """ Функция для обработки количества фотографий"""
    current_user = User.get_user(user_id=message.from_user.id)
    try:
        if int(message.text) > 10:
            raise OverflowError
        logger.info(f'Пользователь {message.from_user.id} ввёл кол-во фото фото "{message.text}"')
        current_user.quantity_photo = message.text
        check_in(message=message)
    except ValueError as e:
        logger.exception(f'Пользователь {message.from_user.id} ввёл не число', e)
        bot.send_message(message.from_user.id, 'Количество фотографий укажите числом')
        bot.register_next_step_handler(message, checking_for_quantity_of_photo)
    except OverflowError as e:
        logger.exception(f'Пользователь {message.from_user.id} ввёл число больше 10', e)
        bot.send_message(message.from_user.id, 'Количество фотографий не может превышать 10')
        bot.register_next_step_handler(message, checking_for_quantity_of_photo)


@bot.callback_query_handler(func=WMonthTelegramCalendar.func(calendar_id=1))
def cal(c: Any) -> None:
    """ Календарь 1 для ввода даты заселения """
    day89: datetime = datetime.date.today() + datetime.timedelta(days=89)
    result, key, step = WMonthTelegramCalendar(calendar_id=1,
                                               min_date=datetime.date.today(),
                                               max_date=day89).process(c.data)
    if not result and key:
        bot.edit_message_text(f"Введите дату заселения в отель",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        logger.info(f'Пользователь {c.from_user.id} выбрал дату "{result}"')
        current_user = User.get_user(user_id=c.from_user.id)
        current_user.check_in_date = datetime.datetime.strftime(result, '%Y-%m-%d')
        bot.edit_message_text(f"Вы ввели дату заселения в отель {result}", c.message.chat.id, c.message.message_id)
        check_out(message=c.message, user_id=c.from_user.id)


def check_in(message: Any) -> None:
    """ Функция обработки ввода даты заселения """
    day89: datetime = datetime.date.today() + datetime.timedelta(days=89)
    calendar, step = WMonthTelegramCalendar(calendar_id=1,
                                            min_date=datetime.date.today(),
                                            max_date=day89).build()
    bot.send_message(message.chat.id, f"Введите дату заселения в отель", reply_markup=calendar)


@bot.callback_query_handler(func=WMonthTelegramCalendar.func(calendar_id=2))
def cal(c: Any) -> None:
    """ Календарь 2 для ввода даты выезда """
    current_user = User.get_user(user_id=c.from_user.id)
    check_in_date: datetime = datetime.datetime.strptime(current_user.check_in_date, '%Y-%m-%d')

    start_range: datetime = check_in_date + datetime.timedelta(days=1)
    day90: datetime = datetime.date.today() + datetime.timedelta(days=90)

    result, key, step = WMonthTelegramCalendar(calendar_id=2,
                                               min_date=start_range,
                                               max_date=day90).process(c.data)
    if not result and key:
        bot.edit_message_text(f"Введите дату выезда из отеля",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        current_user.check_out_date = datetime.datetime.strftime(result, '%Y-%m-%d')
        bot.edit_message_text(f"Вы ввели дату выезда из отеля {result}", c.message.chat.id, c.message.message_id)
        print_info_for_user(message=c.message, user_id=c.from_user.id)


def check_out(message: Any, user_id: int) -> None:
    """ Функция обработки ввода даты выезда """
    current_user = User.get_user(user_id=user_id)
    check_in_date: datetime = datetime.datetime.strptime(current_user.check_in_date, '%Y-%m-%d').date()

    start_range: datetime = check_in_date + datetime.timedelta(days=1)
    day90: datetime = datetime.date.today() + datetime.timedelta(days=90)
    calendar, step = WMonthTelegramCalendar(calendar_id=2,
                                            min_date=start_range,
                                            max_date=day90).build()
    bot.send_message(message.chat.id, f"Введите дату выезда из отеля", reply_markup=calendar)


def print_info_for_user(message: Any, user_id: int) -> None:
    """ Функция предоставляющая информацию пользователю по критериям его запроса"""
    current_user = User.get_user(user_id=user_id)
    hotels_name: List[str] = []
    result = ''
    logger.info(f'Выполняется запрос к API для пользователя {user_id}')
    bot.send_message(message.chat.id, 'Ищу...')
    if current_user.command in ['/lowprice', '/highprice']:
        result = get_list_hotels(user=current_user)
    elif current_user.command == '/bestdeal':
        result = get_list_hotels_bestdeal(user=current_user)
    if result is False or result == {}:
        logger.info(f'По запросу пользователя {user_id} не было ничего найдено')
        bot.send_message(
            message.chat.id,
            f'К сожалению на ближайшую неделю по вашему запросу в городе'
            f' {current_user.city.capitalize()} нет свободных отелей.'
        )
    elif result is None:
        logger.info(f'По запросу пользователя {user_id} не удалось подключиться к API')
        bot.send_message(message.chat.id,
                         'Повторите поиск или попробуйте позже, проблема с подключением к сайту')
    else:
        bot.send_message(message.chat.id,
                         f'На ближайшую неделю в городе {current_user.city.capitalize()} найдено:')
        db = SQLighter(DATABASE_NAME)
        if current_user.show_photo == 'да':
            for k, v in result.items():
                info = f"<b>{k} вариант:</b>\n" \
                       f"Название: <a href='https://ru.hotels.com/ho{v['id']}'>{v['name']}</a>\n" \
                       f"Адрес: {v['address']}\n" \
                       f"Расстояние от центра: {v['distance']}\n" \
                       f"Цена: {v['price']}\n" \
                       f"Фотографии: "
                hotels_name.append(v['name'])
                bot.send_message(user_id, info, parse_mode='HTML', disable_web_page_preview=True)
                bot.send_media_group(user_id, v['photo'])
                db.safe_user_info(
                    user_id,
                    current_user.command,
                    f"<a href='https://ru.hotels.com/ho{v['id']}'>{v['name']}</a>",
                    v['address'],
                    v['distance'],
                    v['price'],
                )
        else:
            for k, v in result.items():
                info = f"<b>{k} вариант:</b>\n" \
                       f"Название: <a href='https://ru.hotels.com/ho{v['id']}'>{v['name']}</a>\n" \
                       f"Адрес: {v['address']}\n" \
                       f"Расстояние от центра: {v['distance']}\n" \
                       f"Цена: {v['price']}\n"
                bot.send_message(user_id, info, parse_mode='HTML', disable_web_page_preview=True)
                db.safe_user_info(
                    user_id,
                    current_user.command,
                    f"<a href='https://ru.hotels.com/ho{v['id']}'>{v['name']}</a>",
                    v['address'],
                    v['distance'],
                    v['price'],
                )
        db.close()
        logger.info(f'Запросу пользователя {user_id} успешно выполнен')
    current_user.clear_user_info()


@bot.message_handler(commands=['history'])
def command_history(message: Any) -> None:
    """ Функция для обработки команды /history, выводит историю поиска отелей конкретным пользователем"""
    logger.info(f'Пользователь {message.from_user.id} ввёл команду {message.text}')
    user_id = message.from_user.id
    db = SQLighter(DATABASE_NAME)
    result = db.get_user_info(user_id=user_id)
    bot.send_message(message.from_user.id, '<b>Ваша история поиска:</b>', parse_mode='HTML')
    if result:
        for i_info in result:
            info = f'Команда: {i_info[0]}\n' \
                   f'Дата и время: {i_info[1]}\n' \
                   f'Название отеля: {i_info[2]}\n' \
                   f'Адрес: {i_info[3]}\n' \
                   f'Расстояние от центра: {i_info[4]}\n' \
                   f'Цена: {i_info[5]}\n'
            bot.send_message(message.from_user.id, info, parse_mode='HTML', disable_web_page_preview=True)
    else:
        bot.send_message(message.from_user.id, 'У вас нет истории поиска')
    db.close()


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
