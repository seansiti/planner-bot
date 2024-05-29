import telebot
from telebot import types
import sqlite3
import requests
import json


bot = telebot.TeleBot('6898542856:AAHJ3WIjzRcsd6UveT656454GkTQq-ndzM8')
API = 'e40074b756f67d08714d500dce9f344b'

@bot.message_handler(commands=['start', 'menu'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Добавить заметку ✏', callback_data='add')
    btn2 = types.InlineKeyboardButton('Мои заметки 🗒', callback_data='show')
    btn3 = types.InlineKeyboardButton('Удалить заметку ❌', callback_data='delete')
    btn4 = types.InlineKeyboardButton('Узнать погоду ☀', callback_data='weather')
    markup.row(btn1, btn3)
    markup.row(btn2, btn4)
    
    bot.send_message(message.chat.id, f'<b>Привет, {message.from_user.first_name}!</b>👋\n Я бот-напоминалка!\n Я помогу тебе с задачами!\n\nЧтобы вернуться в главное меню - введите команду /start или /menu', parse_mode='html', reply_markup=markup)
    
    conn = sqlite3.connect('reminder_db.sql')
    cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS users(username varchar(200), note varchar(200))''')
    conn.commit()
    cur.close()
    conn.close()

@bot.callback_query_handler(func = lambda callback: True)
def callback_message(callback):
    if callback.data == 'add':
        mesg = bot.send_message(callback.message.chat.id,'Введите название заметки')
        bot.register_next_step_handler(mesg, write_note)

    elif callback.data == 'show':
        notes(callback.message)

    elif callback.data == 'delete':
        delete_note(callback.message)

    elif callback.data == 'weather':
        mesg = bot.send_message(callback.message.chat.id,'Введите название города')
        bot.register_next_step_handler(mesg, get_weather)
    

def write_note (message):
    user_note = message.text.strip()

    conn = sqlite3.connect('reminder_db.sql')
    cur = conn.cursor()

    cur.execute('INSERT INTO users(username, note) VALUES(?, ?)', (str(message.from_user.username), str(user_note),))
    conn.commit()
    cur.close()
    conn.close()

    bot.send_message(message.chat.id,'Заметка добавлена') 


def notes(message):
    conn = sqlite3.connect('reminder_db.sql')
    cur = conn.cursor()

    cur.execute('SELECT * FROM users WHERE username = ?', (str(message.chat.username),))
    users = cur.fetchall()
    info = ''
    if users:
        for index, user in enumerate(users, start=1):
            info += f'{index}. {user[1]}\n'
    else:
        info += 'пуст.'
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, f'Список заметок:\n{info}', parse_mode='html')

@bot.callback_query_handler(func=lambda callback: callback.data == 'delete')
def delete_note(message):
    conn = sqlite3.connect('reminder_db.sql')
    cur = conn.cursor()

    cur.execute('SELECT * FROM users WHERE username = ?', (str(message.chat.username),))
    users = cur.fetchall()
    info = ''
    if users:
        for index, user in enumerate(users, start=1):
            info += f'{index}. {user[1]}\n'
    else:
        info += 'пуст.'
    conn.commit()
    cur.close()
    conn.close()

    msg = bot.send_message(message.chat.id, f"Введите номер заметки, которую хотите удалить:\n{info}", parse_mode='html')
    bot.register_next_step_handler(msg, confirm_delete)

def confirm_delete(message):
    conn = sqlite3.connect('reminder_db.sql')
    cur = conn.cursor()
    note_id = int(message.text)
    username = message.from_user.username

    cur.execute('SELECT * FROM users WHERE username = ?', (username,))
    users = cur.fetchall()
    
    if note_id <= len(users):
        note_to_delete = users[note_id-1][1]
        cur.execute('DELETE FROM users WHERE username = ? AND note = ?', (username, note_to_delete))
        conn.commit()
        bot.send_message(message.chat.id, f"Заметка '{note_to_delete}' удалена.")
    else:
        bot.send_message(message.chat.id, "Заметка не найдена или принадлежит другому пользователю.")
    
    cur.close()
    conn.close()

def get_weather(message):
    city = message.text.strip().lower()
    res = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid={API}')
    if res.status_code == 200:
        data = json.loads(res.text)
        if 'weather' in data and 'main' in data['weather'][0] and 'temp' in data['main'] and 'feels_like' in data['main'] and 'temp_min' in data['main'] and 'temp_max' in data['main'] and 'humidity' in data['main']:
            bot.reply_to(message, f'Погода в городе: {data["weather"][0]["description"]}\nТемпература: {data["main"]["temp"]} °C\nОщущается как: {data["main"]["feels_like"]} °C\nСамая низкая температура сегодня: {data["main"]["temp_min"]} °C\nСамая высокая температура сегодня: {data["main"]["temp_max"]} °C\nВлажность воздуха: {data["main"]["humidity"]}%')
        else:
            bot.reply_to(message, 'Ошибка при получении погоды.')
    else:
        bot.reply_to(message, 'Ошибка при запросе погоды.')


# Обработка текста сообщения:
@bot.message_handler(func=lambda message: True)
def info(message):
    if message.text.lower() == '/start' or message.text.lower() == '/menu':
        bot.send_message(message.chat.id, f'<b>Привет, {message.from_user.first_name}! Я бот-напоминалка!<b><br> Я помогу тебе с задачами!', parse_mode='html')


bot.polling(none_stop=True)