import telebot
from telebot import types
import sqlite3
import time
from email_validator import validate_email, EmailNotValidError
from pytz import timezone
import datetime
from configuration import config


token = config['token']
our_bot = telebot.TeleBot(token)
week_days = {
    0: '1_Monday',
    1: '2_Tuesday',
    2: '3_Wednesday',
    3: '4_Thursday',
    4: '5_Friday',
    5: '6_Saturday',
    6: 'now_sunday'
}
lessons = {
    9: 'lesson_1',
    10: 'lesson_2',
    11: 'lesson_3',
    12: 'lesson_4',
    13: 'lesson_5',
    14: 'lesson_6',
    15: 'lesson_7',
    16: 'lesson_8'
}
timetable = {
    "lesson_1": [datetime.time(9, 0), datetime.time(9, 45)],
    "lesson_2": [datetime.time(10, 0), datetime.time(10, 45)],
    "lesson_3": [datetime.time(11, 5), datetime.time(11, 50)],
    "lesson_4": [datetime.time(12, 5), datetime.time(12, 50)],
    "lesson_5": [datetime.time(13, 10), datetime.time(13, 55)],
    "lesson_6": [datetime.time(14, 10), datetime.time(14, 55)],
    "lesson_7": [datetime.time(15, 5), datetime.time(15, 50)],
    "lesson_8": [datetime.time(16, 00), datetime.time(16, 45)],
}
alt_timetable = {
    "lesson_1": [datetime.time(9, 0), datetime.time(9, 40)],
    "lesson_2": [datetime.time(9, 55), datetime.time(10, 35)],
    "lesson_3": [datetime.time(10, 55), datetime.time(11, 35)],
    "lesson_4": [datetime.time(11, 50), datetime.time(12, 30)],
    "lesson_5": [datetime.time(12, 50), datetime.time(13, 30)],
    "lesson_6": [datetime.time(13, 40), datetime.time(14, 20)],
    "lesson_7": [datetime.time(14, 30), datetime.time(15, 10)],
    "lesson_8": [datetime.time(15, 20), datetime.time(16, 0)],
}
rus_list = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З', 'И', 'Й', 'К', 'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф', 'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Э', 'Ю', 'Я']
con = sqlite3.connect('timetable.db', check_same_thread=False)
cur = con.cursor()
a = []


class ClassFormatError(Exception):
    pass


def kb():
    keybord = types.ReplyKeyboardMarkup(resize_keyboard=True)
    now_lesson = types.KeyboardButton(text="Текущий и следующий урок")
    day_timetable = types.KeyboardButton(text="Расписание на день")
    keybord.add(now_lesson, day_timetable)
    return keybord


@our_bot.message_handler(commands=['start'], chat_types=['private'])
def start_message(message):
    a = []
    our_bot.send_message(message.chat.id, "Hi, my name is OLEG and I'm soo well-bread bot")
    result = cur.execute("""SELECT userID FROM info""").fetchall()
    reg_passed = False
    us_id = message.from_user.id
    for i in result:
        if i[0] == us_id:
            reg_passed = True
    if not reg_passed:
        our_bot.send_message(message.chat.id, "Пока вы не зарегистрируетесь, возможности бота будут Вам недоступны, извините. Ваша регистрация обязательна.")
        markup = types.InlineKeyboardMarkup()
        click_decline = types.InlineKeyboardButton(text='Отказ от регистрации', callback_data="Not")
        click_suggestion = types.InlineKeyboardButton(text='Согласие на дальнейшую работу с ботом', callback_data="Yes")
        markup.add(click_decline, click_suggestion)
        our_bot.send_message(message.chat.id, "Выберите подходящий Вам вариант:", reply_markup=markup)
    elif reg_passed:
        our_bot.send_message(message.chat.id, "Вы уже зарегистрированы, выберите желаемое действие:", reply_markup=kb())


@our_bot.message_handler(content_types=["text"])
def daily_answer(message):
    if message.text == "Текущий и следующий урок":
        cls_nbr = cur.execute(f"""SELECT number_of_class FROM info WHERE userID = {message.from_user.id}""").fetchone()[0]
        dt = datetime.datetime.now(timezone("Europe/Moscow"))
        date = week_days[dt.weekday()]
        time2 = datetime.datetime.now(timezone("Europe/Moscow")).time()
        k = datetime.time(0, 0)
        our_bot.send_message(message.chat.id, f"Текущее время и дата:\n{dt.time()}\n{dt.date()}")
        if date == "now_sunday":
            our_bot.send_message(message.chat.id, "Сегодня можно отдохнуть")
        if time2 < timetable["lesson_1"][0]:
            our_bot.send_message(message.chat.id, "Уроки ещё не начались")
        elif time2 > timetable["lesson_7"][1] and date != "1_Monday":
            our_bot.send_message(message.chat.id, "На сегодня больше уроков нету")
        elif time2 > alt_timetable["lesson_8"][1] and date == "1_Monday":
            our_bot.send_message(message.chat.id, "На сегодня больше уроков нету")
        elif date == "1_Monday":
            for i, j in alt_timetable.items():
                if time2 > j[0] and time2 < j[1]:
                    our_bot.send_message(message.chat.id, f'Ваш класс: {cls_nbr}')
                    if i != 'lesson_8':
                        now_lesson = cur.execute(
                            f'''SELECT {i} FROM all_class WHERE number_of_class = "{cls_nbr}" AND Day = "{date}"''').fetchone()[0]
                        our_bot.send_message(message.chat.id, f'Сейчас урок: {now_lesson}')
                        next_lesson = cur.execute(
                            f'''SELECT {i.split('_')[0] + '_' + str(int(i.split('_')[1]) + 1)} FROM all_class WHERE number_of_class = "{cls_nbr}" AND Day = "{date}"''').fetchone()[0]
                        our_bot.send_message(message.chat.id, f"Следующий урок: {next_lesson}")
                    else:
                        now_lesson = cur.execute(
                            f'''SELECT {i} FROM all_class WHERE number_of_class = "{cls_nbr}" AND Day = "{date}"''').fetchone()[0]
                        our_bot.send_message(message.chat.id, f'Сейчас урок: {now_lesson}')
                elif time2 > k and time2 < j[0]:
                    next_lesson = cur.execute(
                        f'''SELECT {i} FROM all_class WHERE number_of_class = "{cls_nbr}" AND Day = "{date}"''').fetchone()[0]
                    our_bot.send_message(message.chat.id, "Перемена!")
                    our_bot.send_message(message.chat.id, f'Ваш класс: {cls_nbr}')
                    our_bot.send_message(message.chat.id, f"Следующий урок - {next_lesson}")
                k = j[1]
        else:
            for i, j in timetable.items():
                if time2 > j[0] and time2 < j[1]:
                    our_bot.send_message(message.chat.id, f'Ваш класс: {cls_nbr}')
                    if i != 'lesson_8':
                        now_lesson = cur.execute(
                            f'''SELECT {i} FROM all_class WHERE number_of_class = "{cls_nbr}" AND Day = "{date}"''').fetchone()[0]
                        our_bot.send_message(message.chat.id, f'Сейчас урок: {now_lesson}')
                        next_lesson = cur.execute(
                            f'''SELECT {i.split('_')[0] + '_' + str(int(i.split('_')[1]) + 1)} FROM all_class WHERE number_of_class = "{cls_nbr}" AND Day = "{date}"''').fetchone()[0]
                        our_bot.send_message(message.chat.id, f"Следующий урок: {next_lesson}")
                    else:
                        now_lesson = cur.execute(
                            f'''SELECT {i} FROM all_class WHERE number_of_class = "{cls_nbr}" AND Day = "{date}"''').fetchone()[0]
                        our_bot.send_message(message.chat.id, f'Сейчас урок: {now_lesson}')
                elif time2 > k and time2 < j[0]:
                    next_lesson = cur.execute(
                        f'''SELECT {i} FROM all_class WHERE number_of_class = "{cls_nbr}" AND Day = "{date}"''').fetchone()[0]
                    our_bot.send_message(message.chat.id, "Перемена!")
                    our_bot.send_message(message.chat.id, f'Ваш класс: {cls_nbr}')
                    our_bot.send_message(message.chat.id, f"Следующий урок - {next_lesson}")
                k = j[1]
    elif message.text == "Расписание на день":
        cls_nbr = cur.execute(f"""SELECT number_of_class FROM info WHERE userID = {message.from_user.id}""").fetchone()[0]
        dt = datetime.datetime.now(timezone("Europe/Moscow"))
        date = week_days[dt.weekday()]
        lsn1 = cur.execute(
            f"""SELECT lesson_1 FROM all_class WHERE number_of_class = '{cls_nbr}' AND Day = '{date}'""").fetchone()[0]
        lsn2 = cur.execute(
            f"""SELECT lesson_2 FROM all_class WHERE number_of_class = '{cls_nbr}' AND Day = '{date}'""").fetchone()[0]
        lsn3 = cur.execute(
            f"""SELECT lesson_3 FROM all_class WHERE number_of_class = '{cls_nbr}' AND Day = '{date}'""").fetchone()[0]
        lsn4 = cur.execute(
            f"""SELECT lesson_4 FROM all_class WHERE number_of_class = '{cls_nbr}' AND Day = '{date}'""").fetchone()[0]
        lsn5 = cur.execute(
            f"""SELECT lesson_5 FROM all_class WHERE number_of_class = '{cls_nbr}' AND Day = '{date}'""").fetchone()[0]
        lsn6 = cur.execute(
            f"""SELECT lesson_6 FROM all_class WHERE number_of_class = '{cls_nbr}' AND Day = '{date}'""").fetchone()[0]
        lsn7 = cur.execute(
            f"""SELECT lesson_7 FROM all_class WHERE number_of_class = '{cls_nbr}' AND Day = '{date}'""").fetchone()[0]
        lsn8 = cur.execute(
            f"""SELECT lesson_8 FROM all_class WHERE number_of_class = '{cls_nbr}' AND Day = '{date}'""").fetchone()[0]
        daily_tt = [lsn1, lsn2, lsn3, lsn4, lsn5, lsn6, lsn7, lsn8]
        for i in range(len(daily_tt)):
            our_bot.send_message(message.chat.id, daily_tt[i])


@our_bot.callback_query_handler(func=lambda x: x.data)
def check_suggestion_keyboard(callback):
    our_bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text="Спасибо за ваш ответ!",
                          reply_markup=None)
    if callback.data == "Not":
        our_bot.send_message(callback.message.chat.id, "В таком случае мы не можем ничем Вам помочь, простите. С уважением, команда разработчиков")
    elif callback.data == "Yes":
        our_bot.send_message(callback.message.chat.id, "Отлично, я рад знакомству!")
        msg = our_bot.send_message(callback.message.chat.id, "Введи свою электронную почту, я буду очень рад с тобой работать!")
        our_bot.register_next_step_handler(msg, email_answer, a)


def email_answer(message, lst):
    mail = message.text
    lst = []
    try:
        is_new_account = True
        validation = validate_email(mail, check_deliverability=is_new_account)
        mail = validation.email
        us_id = message.from_user.id
        lst.append(us_id)
        lst.append(mail)
        our_bot.send_message(message.chat.id, "Отлично! Осталось совсем чуть-чуть и я смогу тебе помогать)")
        msg = our_bot.send_message(message.chat.id, "Теперь мне необходим пароль от твоего аккаунта")
        our_bot.register_next_step_handler(msg, check_pswd, lst)
    except EmailNotValidError:
        wts = our_bot.send_message(message.chat.id, "Неверный формат! Неправильно! Попробуй еще разок)")
        our_bot.register_next_step_handler(wts, email_answer, lst)


def check_pswd(message, lst):
    password = message.text
    lst.append(password)
    our_bot.send_message(message.chat.id, "Наша команда не знает твоего пароля, так что пусть пока что он будет таким, если он не подойдет к электронному дневнику потом - мы сообщим")
    msg = our_bot.send_message(message.chat.id, "Теперь введи номер и букву своего класса в формате как в примере:10 А")
    our_bot.register_next_step_handler(msg, check_cls, lst)


def check_cls(message, lst):
    clas_check_passed = False
    cls = message.text
    if cls.split()[0].isdigit():
        if int(cls.split()[0]) > 0 and int(cls.split()[0]) < 12:
            if cls.split()[1] in rus_list:
                clas_check_passed = True
                lst.append(cls)
                cur.execute(f"""INSERT INTO info VALUES ({lst[0]}, '{lst[1]}', '{lst[2]}', '{lst[3]}')""")
                con.commit()
                lst = []
                start_message(message)
    if not clas_check_passed:
        ask_class = our_bot.send_message(message.chat.id, "Неверный формат ввода класса, попробуй-ка ещё разок")
        our_bot.register_next_step_handler(ask_class, check_cls, lst)


our_bot.infinity_polling()