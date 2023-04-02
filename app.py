import datetime
import os
import telebot
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get('BOT_TOKEN')
# задаем токен бота
print(BOT_TOKEN)

bot = telebot.TeleBot(BOT_TOKEN)


# функция для парсинга расписания
def parse_schedule(group):
    # отправляем запрос на страницу расписания
    url = f"https://petrsu.ru/schedule/term?group={group}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    f_schedule = ""  # инициализируем строку для расписания
    cur_date = datetime.datetime.now().strftime("%-d.%m")
    print(cur_date)
    for day_schedule in soup.find_all('div', class_='panel-body'):
        schedule = ""
        prev_div = day_schedule.find_previous_sibling('div')
        day_text = prev_div.text.strip()
        if cur_date in day_text:
            schedule += f"🟢  {day_text}.\n"
        else:
            schedule += f"🔴  {day_text}.\n"
        table_rows = day_schedule.find_all('div', class_='rTableRow')
        if len(table_rows) == 0:
            schedule += f"  *Занятий в этот день нет!*\n\n"
        else:
            for lesson in table_rows:
                table_cells = lesson.find_all('div', {'class': 'rTableCell'})
                instructor = "УВОЛЕН"
                number = table_cells[0].text.strip()
                time = ' '.join(table_cells[1].stripped_strings)
                time = time.replace(" ", "-")
                course = table_cells[2].b.text.strip()
                try:
                    instructor = table_cells[2].span.a.text.strip()
                except:
                    instructor = table_cells[2].span.text.strip()
                dates = table_cells[2].find_all('br')[1].next_sibling.strip()
                type = ' '.join(table_cells[3].stripped_strings)
                room = table_cells[4].text.strip()

                schedule += f"— Время: *{time}*\n" \
                            f"— Номер пары: *{number}*\n" \
                            f"— Название предмета:\n _{course}_\n" \
                            f"— Преподаватель: _{instructor}_\n" \
                            f"— Тип занятия: {type}\n" \
                            f"— Кабинет: {room}\n" \
                            f"— Даты проведения курса: {dates}\n\n"
        f_schedule += schedule
    return f"📅 Расписание:\n\n{f_schedule}"  # возвращаем расписание в нужном формате

# обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Введи номер группы, чтобы получить расписание. 📚")


# обработчик команды /help
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Чтобы получить расписание, введи номер группы. 📅")

# обработчик команды /today
@bot.message_handler(commands=['today'])
def send_today_schedule(message):
    try:
        group = message.text.split()[1].strip()  # преобразуем номер группы в число
        schedule = parse_schedule(group)  # парсим расписание для данной группы
        today_schedule = ""
        cur_date = datetime.datetime.now().strftime("%-d.%m")
        # Ищем расписание только на текущий день
        for day_schedule in schedule.split('🟢')[1:]:
            if cur_date in day_schedule:
                today_schedule = f'📅 Расписание на сегодня:\n\n 🟢 {day_schedule}'
                break
        if today_schedule:
            bot.reply_to(message, today_schedule, parse_mode="Markdown")
        else:
            bot.reply_to(message, "На сегодня занятий нет. 🔥", parse_mode="Markdown")
    except:
        bot.reply_to(message, "Некорректный номер группы. Попробуй еще раз. ❌")

# обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def send_schedule(message):
    try:
        print(message.text)
        group = int(message.text.strip())  # преобразуем номер группы в число
        schedule = parse_schedule(group)  # парсим расписание для данной группы
        if len(schedule) > 4000:
            # Разбиваем расписание на блоки по 4000 символов
            schedule_blocks = schedule.split("\n\n")
            current_block = ""
            for block in schedule_blocks:
                if len(current_block + block) > 4000:
                    # Отправляем блок расписания пользователю
                    bot.reply_to(message, current_block, parse_mode="Markdown")
                    current_block = block
                else:
                    current_block += block + "\n\n"
            if current_block:
                # Отправляем последний блок расписания пользователю
                bot.reply_to(message, current_block, parse_mode="Markdown")
        else:
            # Отправляем расписание пользователю
            bot.reply_to(message, schedule, parse_mode="Markdown")
    except:
        bot.reply_to(message, "Некорректный номер группы. Попробуй еще раз. ❌")


bot.polling(none_stop=True)
