import telebot
from telebot import types
import psycopg2
from email_validator import validate_email, EmailNotValidError
from pytz import timezone
import datetime
from configuration import config
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

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
rus_list = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З', 'И', 'Й', 'К', 'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т', 'У',
            'Ф', 'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Э', 'Ю', 'Я']
con = psycopg2.connect(config['database_url'], sslmode="require")
cur = con.cursor()


class ClassFormatError(Exception):
    pass


def kb():
    keybord = types.ReplyKeyboardMarkup(resize_keyboard=True)
    now_lesson = types.KeyboardButton(text="Текущий и следующий урок")
    day_timetable = types.KeyboardButton(text="Расписание на день")
    take_marks = types.KeyboardButton(text="Оценки")
    keybord.add(now_lesson, day_timetable, take_marks)
    return keybord


@our_bot.message_handler(commands=['start'], chat_types=['private'])
def start_message(message):
    global dct_of_dt
    dct_of_dt = {}
    our_bot.send_message(message.chat.id, "Hi, my name is OLEG and I'm soo well-bread bot")
    cur.execute("""SELECT userID FROM info""")
    result = cur.fetchall()
    reg_passed = False
    global us_id
    us_id = message.from_user.id
    for i in result:
        if i[0] == us_id:
            reg_passed = True
    if not reg_passed:
        our_bot.send_message(message.chat.id,
                             "Пока вы не зарегистрируетесь, возможности бота будут Вам недоступны, извините. Ваша регистрация обязательна.")
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
        cur.execute(f"""SELECT number_of_class FROM info WHERE userID = {message.from_user.id}""")
        cls_nbr = cur.fetchone()[0]
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
                        cur.execute(
                            f"""SELECT {i} FROM all_class WHERE number_of_class = '{cls_nbr}' AND Day = '{date}'""")
                        now_lesson = cur.fetchone()[0]
                        our_bot.send_message(message.chat.id, f'Сейчас урок: {now_lesson}')
                        cur.execute(
                            f"""SELECT {i.split('_')[0] + '_' + str(int(i.split('_')[1]) + 1)} FROM all_class WHERE number_of_class = '{cls_nbr}' AND Day = '{date}'""")
                        next_lesson = cur.fetchone()[0]
                        our_bot.send_message(message.chat.id, f"Следующий урок: {next_lesson}")
                    else:
                        cur.execute(
                            f"""SELECT {i} FROM all_class WHERE number_of_class = '{cls_nbr}' AND Day = '{date}'""")
                        now_lesson = cur.fetchone()[0]
                        our_bot.send_message(message.chat.id, f'Сейчас урок: {now_lesson}')
                elif time2 > k and time2 < j[0]:
                    cur.execute(
                        f"""SELECT {i} FROM all_class WHERE number_of_class = '{cls_nbr}' AND Day = '{date}'""")
                    next_lesson = cur.fetchone()[0]
                    our_bot.send_message(message.chat.id, "Перемена!")
                    our_bot.send_message(message.chat.id, f'Ваш класс: {cls_nbr}')
                    our_bot.send_message(message.chat.id, f"Следующий урок - {next_lesson}")
                k = j[1]
        else:
            for i, j in timetable.items():
                if time2 > j[0] and time2 < j[1]:
                    our_bot.send_message(message.chat.id, f'Ваш класс: {cls_nbr}')
                    if i != 'lesson_8':
                        cur.execute(
                            f"""SELECT {i} FROM all_class WHERE number_of_class = '{cls_nbr}' AND Day = '{date}'""")
                        now_lesson = cur.fetchone()[0]
                        our_bot.send_message(message.chat.id, f'Сейчас урок: {now_lesson}')
                        cur.execute(
                            f"""SELECT {i.split('_')[0] + '_' + str(int(i.split('_')[1]) + 1)} FROM all_class WHERE number_of_class = '{cls_nbr}' AND Day = '{date}'""")
                        next_lesson = cur.fetchone()[0]
                        our_bot.send_message(message.chat.id, f"Следующий урок: {next_lesson}")
                    else:
                        cur.execute(
                            f"""SELECT {i} FROM all_class WHERE number_of_class = '{cls_nbr}' AND Day = '{date}'""")
                        now_lesson = cur.fetchone()[0]
                        our_bot.send_message(message.chat.id, f'Сейчас урок: {now_lesson}')
                elif time2 > k and time2 < j[0]:
                    cur.execute(
                        f"""SELECT {i} FROM all_class WHERE number_of_class = '{cls_nbr}' AND Day = '{date}'""")
                    next_lesson = cur.fetchone()[0]
                    our_bot.send_message(message.chat.id, "Перемена!")
                    our_bot.send_message(message.chat.id, f'Ваш класс: {cls_nbr}')
                    our_bot.send_message(message.chat.id, f"Следующий урок - {next_lesson}")
                k = j[1]
    elif message.text == "Расписание на день":
        cur.execute(f"""SELECT number_of_class FROM info WHERE userID = {message.from_user.id}""")
        cls_nbr = cur.fetchone()[0]
        daily_tt = []
        dt = datetime.datetime.now(timezone("Europe/Moscow"))
        date = week_days[dt.weekday()]
        for i in range(1, 9):
            cur.execute(f"""SELECT lesson_{i} FROM all_class WHERE number_of_class = '{cls_nbr}' AND Day = '{date}'""")
            lsn = cur.fetchone()[0]
            daily_tt.append(lsn)
        our_bot.send_message(message.chat.id, '\n'.join(daily_tt))
    elif message.text == "Оценки":
        cur.execute(f"""SELECT username FROM info WHERE userid = '{message.from_user.id}'""")
        stdnt_nm = cur.fetchone()[0]
        cur.execute(f"""SELECT user_mail FROM info WHERE userid = {us_id}""")
        us_mail = cur.fetchone()[0]
        cur.execute(f"""SELECT user_password FROM info WHERE userid = {us_id}""")
        us_pswd = cur.fetchone()[0]
        keybord_time_zone = types.InlineKeyboardMarkup()
        url = "https://dnevnik2.petersburgedu.ru/login"
        options = webdriver.ChromeOptions()
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
        #   options.add_argument("--headless")
        driver = webdriver.Chrome(
            executable_path="chromedriver.exe",
            options=options
        )
        try:
            our_bot.send_message(message.chat.id,
                                 'Загрузка... Подключаюсь к серверу...')
            driver.get(url=url)
            mail, password = driver.find_elements(By.CLASS_NAME, "input__control")
            mail.clear()
            mail.send_keys(us_mail)
            password.clear()
            password.send_keys(us_pswd)
            scroll_by = f'window.scrollBy(0, {400});'
            driver.execute_script(scroll_by)
            time.sleep(0.5)
            driver.find_element(By.CLASS_NAME, "button_theme_action").click()
            driver.get("https://dnevnik2.petersburgedu.ru/students/my")
            time.sleep(0.5)
            scroll_by = f'window.scrollBy(0, {400});'
            driver.execute_script(scroll_by)
            time.sleep(0.5)
            students_blocks = driver.find_elements(By.XPATH, "//int-student-snippet[@class='ng-star-inserted']")
            for i in students_blocks:
                name_student = i.find_element(By.TAG_NAME, 'h4')
                if stdnt_nm in name_student.text:
                    list_of_std_btns = i.find_elements(By.TAG_NAME, 'button')
                    list_of_std_btns[1].click()
            time.sleep(3)
            elem1 = driver.find_element(By.XPATH,
                                        "//widget-estimate-filter-container[@tableparent='ESTIMATE']//button[contains(@class, 'select') and contains(@class, 'select_theme_filter')]")
            elem1.click()
            elem = driver.find_element(By.XPATH, "//ul[@class='options-list__items']")
            lst = elem.find_elements(By.TAG_NAME, 'li')
            for i in lst:
                element_button = types.InlineKeyboardButton(text=i.get_attribute("title"), callback_data=i.get_attribute("title"))
                keybord_time_zone.add(element_button)
            our_bot.send_message(message.chat.id, 'Выберите вариант, пожалуйста', reply_markup=keybord_time_zone)
        except Exception as ex:
            print(ex)
            our_bot.send_message(message.chat.id,
                                 'Возникла непредвиденная ошибка!\nСкорее всего неверный логин или пароль!')
        finally:
            driver.close()
            driver.quit()


@our_bot.callback_query_handler(func=lambda x: x.data)
def check_suggestion_keyboard(callback):
    our_bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text="Спасибо за ваш ответ!",
                              reply_markup=None)
    if callback.data == "Not":
        our_bot.send_message(callback.message.chat.id,
                             "В таком случае мы не можем ничем Вам помочь, простите. С уважением, команда разработчиков")
    elif callback.data == "Yes":
        our_bot.send_message(callback.message.chat.id, "Отлично, я рад знакомству!")
        msg = our_bot.send_message(callback.message.chat.id,
                                   "Введи свою электронную почту, я буду очень рад с тобой работать!")
        our_bot.register_next_step_handler(msg, email_answer)
    else:
        our_bot.send_message(callback.message.chat.id,
                             'Загрузка... Тащу оценки с сайта...')
        cur.execute(f"""SELECT username FROM info WHERE userid = {us_id}""")
        stdnt_nm = cur.fetchone()[0]
        cur.execute(f"""SELECT user_mail FROM info WHERE userid = {us_id}""")
        us_mail = cur.fetchone()[0]
        cur.execute(f"""SELECT user_password FROM info WHERE userid = {us_id}""")
        us_pswd = cur.fetchone()[0]
        data_dict = {}
        answer = callback.data
        url = "https://dnevnik2.petersburgedu.ru/login"
        options = webdriver.ChromeOptions()
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
        #   options.add_argument("--headless")
        driver = webdriver.Chrome(
            executable_path="chromedriver.exe",
            options=options
        )
        try:
            driver.get(url=url)
            mail, password = driver.find_elements(By.CLASS_NAME, "input__control")
            mail.clear()
            mail.send_keys(us_mail)
            password.clear()
            password.send_keys(us_pswd)
            scroll_by = f'window.scrollBy(0, {400});'
            driver.execute_script(scroll_by)
            time.sleep(0.5)
            driver.find_element(By.CLASS_NAME, "button_theme_action").click()
            driver.get("https://dnevnik2.petersburgedu.ru/students/my")
            time.sleep(0.5)
            scroll_by = f'window.scrollBy(0, {400});'
            driver.execute_script(scroll_by)
            time.sleep(0.5)
            students_blocks = driver.find_elements(By.XPATH, "//int-student-snippet[@class='ng-star-inserted']")
            for i in students_blocks:
                name_student = i.find_element(By.TAG_NAME, 'h4')
                if stdnt_nm in name_student.text:
                    list_of_std_btns = i.find_elements(By.TAG_NAME, 'button')
                    list_of_std_btns[1].click()
            time.sleep(3)
            elem1 = driver.find_element(By.XPATH,
                                        "//widget-estimate-filter-container[@tableparent='ESTIMATE']//button[contains(@class, 'select') and contains(@class, 'select_theme_filter')]")
            elem1.click()
            elem = driver.find_element(By.XPATH, "//ul[@class='options-list__items']")
            elem.find_element(By.XPATH, f"//li[@title='{answer}']").click()
            time.sleep(3)
            subject_block = driver.find_elements(By.XPATH,
                                                 "//div[contains(@class,'date-grid__container') and contains(@class,'date-grid__container_type_fixed') and contains(@class,'date-grid__container_position_left')]//tr[contains(@class,'date-grid__row') and contains(@class,' ng-star-inserted')]")[
                            :-1]
            marks_block = driver.find_elements(By.XPATH,
                                               "//div[contains(@class,'date-grid__container') and contains(@class,'date-grid__container_type_scrollable') and contains(@class,'date-grid__container_position_middle')]//tr[contains(@class,'date-grid__row') and contains(@class,' ng-star-inserted')]")
            all_marks = ''
            for i in range(len(subject_block)):
                subject = subject_block[i].text
                marks = marks_block[i].text
                marks = marks.replace('\n', ' ')
                marks = marks.replace('•', ' ')
                marks = marks.replace('!', ' ')
                marks = marks.replace('Н', ' ')
                marks = ', '.join(marks.split())
                data_dict[subject] = marks
            for i, j in data_dict.items():
                all_marks += f'{i}: {j}\n'
            our_bot.send_message(callback.message.chat.id, f"Ваши оценки за период {answer}:\n{all_marks}",
                                 reply_markup=kb())
        except Exception as ex:
            our_bot.send_message(callback.message.chat.id,
                                 'Возникла непредвиденная ошибка!\nСкорее всего неверный логин или пароль!')
            print(ex)
        finally:
            driver.close()
            driver.quit()



def email_answer(message):
    mail = message.text
    try:
        is_new_account = True
        validation = validate_email(mail, check_deliverability=is_new_account)
        mail = validation.email
        us_id = message.from_user.id
        dct_of_dt[str(message.from_user.id) + 'id'] = us_id
        dct_of_dt[str(message.from_user.id) + 'mail'] = mail
        print(dct_of_dt)
        our_bot.send_message(message.chat.id, "Отлично! Осталось совсем чуть-чуть и я смогу тебе помогать)")
        msg = our_bot.send_message(message.chat.id, "Теперь мне необходим пароль от твоего аккаунта")
        our_bot.register_next_step_handler(msg, check_pswd)
    except EmailNotValidError:
        wts = our_bot.send_message(message.chat.id, "Неверный формат! Неправильно! Попробуй еще разок)")
        our_bot.register_next_step_handler(wts, email_answer)


def check_pswd(message):
    password = message.text
    dct_of_dt[str(message.from_user.id) + 'pswd'] = password
    our_bot.send_message(message.chat.id,
                         "Наша команда не знает твоего пароля, так что пусть пока что он будет таким, если он не подойдет к электронному дневнику потом - мы сообщим")
    msg = our_bot.send_message(message.chat.id, "Теперь введи, пожалуйста, как тебя зовут")
    our_bot.register_next_step_handler(msg, name_answer)


def name_answer(message):
    usname = message.text
    dct_of_dt[str(message.from_user.id) + 'name'] = usname
    our_bot.send_message(message.chat.id, f"Твоё имя - {usname}... Звучит классно)")
    msg = our_bot.send_message(message.chat.id, "Теперь введи номер и букву своего класса в формате как в примере:10 А")
    our_bot.register_next_step_handler(msg, check_cls, dct_of_dt)


def check_cls(message, dct):
    clas_check_passed = False
    cls = message.text
    if cls.split()[0].isdigit():
        if int(cls.split()[0]) > 0 and int(cls.split()[0]) < 12:
            if cls.split()[1] in rus_list:
                clas_check_passed = True
                cur.execute(
                    f"""INSERT INTO info VALUES ({dct[str(message.from_user.id) + 'id']}, '{dct[str(message.from_user.id) + 'mail']}', '{dct[str(message.from_user.id) + 'pswd']}', '{cls}', '{dct[str(message.from_user.id) + 'name']}')""")
                con.commit()
                dct_of_dt = {}
                start_message(message)
    if not clas_check_passed:
        ask_class = our_bot.send_message(message.chat.id, "Неверный формат ввода класса, попробуй-ка ещё разок")
        our_bot.register_next_step_handler(ask_class, check_cls)


our_bot.infinity_polling()
