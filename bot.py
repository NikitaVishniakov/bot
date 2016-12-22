import config
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import telebot
bot = telebot.TeleBot(config.token)
def get_week():
    date = datetime.now().isocalendar() 
    weekNum = date[1] #get the num of the current week from the turple (Y, WEEK, WEEK_DAY)
    day = date[2]
    if weekNum % 2 == 1:
        if day == 7:
            even = 1
        else:
            even = 2
    else:
        if day == 7:
            even = 2
        else:
            even = 1
    return day, even
def get_page(group, week=''):
    if week:
        week = str(week)
    else:
        _, week = get_week()
        week = str(week)
    url = "{domain}/{group}/{week}/raspisanie_zanyatiy_{group}.htm".format(
        domain = config.domain, 
        week = week, 
        group = group
    )
    response = requests.get(url)
    web_page = response.text
    return web_page
def get_schedule(day, group, week = ''):
    web_page = get_page(group, week)
    if len(str(day)) == 1:
        day_num = day
        day_name = config.week[day]
    if day in config.week:
        for i in range(len(config.week)):
            if day == config.week[i]:
                day_num = i
                if day_num == 0:
                    day_num = 1
                day_name = config.week[day_num]
    soup = BeautifulSoup(web_page, "html5lib")
    day = str(day_num) + "day"
    # Получаем таблицу с расписанием на понедельник
    schedule_table = soup.find("table", attrs={"id": day})

    # Время проведения занятий
    times_list = schedule_table.find_all("td", attrs={"class": "time"})
    times_list = [time.span.text for time in times_list]

    # Место проведения занятий
    locations_list = schedule_table.find_all("td", attrs={"class": "room"})
    locations_list = [room.dd.text + ", " + room.span.text for room in locations_list]
        
    # Название дисциплин и имена преподавателей
    lessons_list = schedule_table.find_all("td", attrs={"class": "lesson"})
    lessons_list = [lesson.text.split('\n\n') for lesson in lessons_list]
    lessons_list = [', '.join([info for info in lesson_info if info]) for lesson_info in lessons_list]
    return times_list, locations_list, lessons_list, day_name
@bot.message_handler(commands=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'])
def get_exact_day(message):
    comand = message.text.split()
    week = ''
    if len(comand) == 1:
        day = comand[0]
        group = "M3110"
    elif len(comand) == 3:
        day = comand[0]
        week = comand[1]
        group = comand[2].upper()
    else:
        day = comand[0]
        if len(comand[1]) > 1:
            group = comand[1].upper()
        else:
            group = "M3110"
            week = comand[1]
    day = day[1:]
    web_page = get_page(group)
    times_lst, locations_lst, lessons_lst, day = get_schedule(day, group, week)
    resp = ''
    resp += "<b>{}</b>\n{}\n".format(day.upper(), group)
    for time, location, lession in zip(times_lst, locations_lst, lessons_lst):
        resp += '<b>{}</b>, {}, {}\n'.format(time, location, lession)
    bot.send_message(message.chat.id, resp, parse_mode='HTML')
@bot.message_handler(commands=['tommorow'])
def get_next_day(message):
    comand = message.text.split()
    day, week = get_week()
    if day == 7 or day == 6:
        day = 1
    else:
        day = int(day) + 1
    if len(comand) == 1:
        group = "M3110"
    else:
        group = comand[1].upper()
#    for i in range(len(config.week)):
#        if day == i:
#            day = config.week[i]
    web_page = get_page(group)
    times_lst, locations_lst, lessons_lst, day = get_schedule(day, group, week)
    resp = ''
    resp += "<b>{}</b>\n{}\n".format(day.upper(), group)
    for time, location, lession in zip(times_lst, locations_lst, lessons_lst):
        resp += '<b>{}</b>, {}, {}\n'.format(time, location, lession)
    bot.send_message(message.chat.id, resp, parse_mode='HTML')
@bot.message_handler(commands=['all'])
def get_all_week(message):
    week = ''
    comand = message.text.split()
    if len(comand) == 1:
        group = "M3110"
    elif len(comand) == 3:
        week = comand[1]
        group = comand[2].upper()
    else:
        if len(comand[1]) > 1:
            group = comand[1].upper()
        else:
            group = "M3110"
            week = comand[1]
    web_page = get_page(group)
    for i in range(1,6):
        times_lst, locations_lst, lessons_lst, day = get_schedule(i, group, week)
        resp = ''
        resp += "<b>{}</b>\n{}\n".format(day.upper(), group)
        for time, location, lession in zip(times_lst, locations_lst, lessons_lst):
            resp += '<b>{}</b>, {}, {}\n'.format(time, location, lession)
        bot.send_message(message.chat.id, resp, parse_mode='HTML')
@bot.message_handler(commands=['near_lesson'])
def get_near_lesson(message):
    comand = message.text.split()
    if len(comand) == 1:
        group = "M3110"
    else:
        group = comand[1].upper()
    day, week = get_week()
    current = datetime.strftime(datetime.now(), "%H:%M")
    web_page = get_page(group)
    times_lst, locations_lst, lessons_lst, day = get_schedule(day, group, week)
    resp = ''
    resp += "<b>Сейчас: {}</b>\n Ближайшая пара: \n".format(current)
    for time, location, lession in zip(times_lst, locations_lst, lessons_lst):
        class_time = datetime.strftime(datetime.strptime(time[:4],"%H:%M"),"%H:%M")
        if class_time > current:
            resp += '<b>{}</b>, {}, {}\n'.format(time, location, lession)
            break
    bot.send_message(message.chat.id, resp, parse_mode='HTML')
if __name__ == '__main__':
   bot.polling(none_stop=True)
#def echo_table():
#    times_lst, locations_lst, lessons_lst = get_schedule()
#    resp = ''
#    for time, location, lession in zip(times_lst, locations_lst, lessons_lst):
#        resp += '<b>{}</b>, {}, {}\n'.format(time, location, lession)
#    return resp
