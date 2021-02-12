import telebot
import config
import os
from private_info import telegram_token as tel_token
from flask import Flask, request
from random import randint

telegram_token = os.environ.get('telegram_token', tel_token)

PROJECT_NAME = os.environ.get('PROJECT_NAME')

bot = telebot.TeleBot(telegram_token)
app = Flask(__name__)

WEBHOOK_URL = f"{PROJECT_NAME}{telegram_token}/"

commands_list = [
    telebot.types.BotCommand('/hmmm', 'Стикер от бота.'),
    telebot.types.BotCommand('/pic', 'Картинка животного.'),
    telebot.types.BotCommand('/problems', 'Описание возможных проблем.'),
    telebot.types.BotCommand('/w', 'Погода. \"/wthr@запрос\"'),
    telebot.types.BotCommand('/m', 'Музыка. \"/m@запрос\"'),
    # Hidden commands
    # telebot.types.BotCommand('/update', 'Обновление команд.'),
    # telebot.types.BotCommand('/get_chat_id', 'Получение идентификатора чата.'),
    # telebot.types.BotCommand('/user_info', 'Информация о пользователе.'),
    # telebot.types.BotCommand('/bot_info', 'Информация о боте.'),
]

@bot.message_handler(commands=['hmmm'])
def sticker_command(message: telebot.types.Message):
    stickers = ['CAACAgIAAxkBAAICpF9CRtdmBhe4Fpq7cEQOWWKw5K1JAAJYAANVLHgLLstV0QW9DSAbBA',
                'CAACAgIAAxkBAAICqF9CR2678a2lvd_5y6ibbyLbuEKEAAJGAANVLHgLn47i6FdyuM4bBA',
                'CAACAgIAAxkBAAICql9CR5i3mnkHfkb34Oz76DlZrg-WAAJaAANVLHgLASOiMaawoZsbBA',
                'CAACAgIAAxkBAAICrF9CR7M_HwABa9qf_N5bchLUJ-yPTQACRAADVSx4CzmHlwP9k0jSGwQ',
                'CAACAgIAAxkBAAICrl9CR8fY2Q7xzUvzhjiDJY-UZRRtAAI8AANVLHgL5fNA1aSlAbYbBA',
                'CAACAgIAAxkBAAICsF9CR_EsinSVHHK3Ki4umQNlwDBwAAI6AANVLHgLtEFkFMnjbXUbBA',
                'CAACAgIAAxkBAAIC9l9CS_2j0JRKYCEU1_3mBL2rRy0FAAJIAANVLHgLrdGEPAUZbDkbBA',
                'CAACAgIAAxkBAAIC-F9CTBDL5kJm3up9FzjKWJwitWfZAAJeAANVLHgLoWJrPQAB9SdrGwQ',
                'CAACAgIAAxkBAAIC-l9CTB0BppgHX8GIU6RFh12AoX50AAJkAANVLHgLyMWmuBdfutMbBA',
                'CAACAgIAAxkBAAIC_F9CTDc2thLuluUiJZ8SgmuTsv0IAAJWAANVLHgLFYCAw0L8ftQbBA',
                'CAACAgIAAxkBAAIC_l9CTEyTI0NMB9Kd-KL0WpTbCq8KAAJgAANVLHgLYruxBTysRgEbBA'
                ]
    rand_num = randint(0, stickers.__len__() - 1)
    sticker = stickers[rand_num]
    bot.send_sticker(message.chat.id, sticker)

@bot.message_handler(commands=['problems'])
def problems_command(message: telebot.types.Message):
    text = "Возможные проблемы этого бота:\n"\
        "- Кнопка одного из треков вызывает сообщение об ошибке или присылает не тот трек. "\
        "Эта проблема связана с тем, что база данных самоочистилась и данного трека в ней нет.\n"\
        "Решение: повторите запрос используя команду \"/m\"."
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['user_info', 'bot_info'])
def info_command(message: telebot.types.Message):
    if 'user' in message.text:
        bot.send_message(message.chat.id, message.from_user)
    else:
        bot.send_message(message.chat.id, bot.get_me())

@bot.message_handler(commands=['get_chat_id'])
def get_chat_id_command(message: telebot.types.Message):
    bot.send_message(message.chat.id, str(message.chat.id))

@bot.message_handler(commands=['update'])
def update_command(message: telebot.types.Message):
    bot.set_my_commands(commands_list)
    
@bot.message_handler(commands=['pic'])
def animalpic_command(message: telebot.types.Message):
    photo = config.send_animalpic()
    bot.send_photo(message.chat.id, photo, caption="=)")
    
    
@bot.message_handler(commands=['w'])
def weather_command(message: telebot.types.Message):
    try:
        query = message.text.split('@', maxsplit=1)[1]
    except IndexError:
        bot.send_message(message.chat.id, "Ошибка в оформлении запроса.")
        return None
    weather_info = config.send_weather(query)
    bot.send_message(message.chat.id, weather_info[0])
    if weather_info[1] != list():
        for item in weather_info[1]:
            bot.send_photo(message.chat.id, item)


@bot.message_handler(commands=['m'])
def music_command(message: telebot.types.Message):
    try:
        query = message.text.split('@', maxsplit=1)[1]
    except IndexError:
        bot.send_message(message.chat.id, "Ошибка в оформлении запроса.")
        return None
    funcs = [config.parse_gdespaces_com,
             config.parse_w1_musify_club,
            ]
    urls, artists, titles = [], [], []
    for i in range(len(funcs)):
        u, a, t = funcs[i](query)
        urls = urls + u
        artists = artists + a
        titles = titles + t
        #print(urls, artists, titles)
    if urls != []:
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        with config.connect_to_db() as mydb:
            len_db = config.count_music(mydb)
            counter = len_db+1 if len_db > 0 else 1
            if len_db > 10000:
                config.clear_music(mydb)
                counter = 1
            for i in range(len(urls)):
                markup.add(telebot.types.InlineKeyboardButton(
                    f'{artists[i]} - {titles[i]}', callback_data=counter))
                counter += 1
            config.save_music(urls, artists, titles, mydb)
        bot.send_message(
            message.chat.id, f'Треки по запросу: {query}', reply_markup=markup)
        return
    if urls == []:
        bot.send_message(message.chat.id, 'Произошла ошибка.',
                         reply_to_message_id=message.message_id)
                         
@bot.callback_query_handler(func=lambda call: True)
def callback(call: telebot.types.CallbackQuery):
    bot.answer_callback_query(call.id)
    url, artist, title = config.get_music(int(call.data))
    if url is not None:
        bot.send_audio(call.message.chat.id, audio=url, title=title, performer=artist, \
            caption=f'{title} - {artist}')
    else:
        bot.send_message(
            call.message.chat.id, text='Запрос устарел, воспользуйтесь, пожалуйста, поиском.')
            
            
@app.route(f'/{telegram_token}/', methods=['POST'])
def get_updates():
    update = telebot.types.Update.de_json(
        request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return "ok", 200


if __name__ == '__main__' and os.environ.get('HOST_ENVIRONMENT') is not None:
    app.debug = True
    app.secret_key = os.environ.get('flask_secret_key')
    # app.secret_key = f'{telegram_token}'
    app.run('0.0.0.0')
elif __name__ == '__main__':
    bot.infinity_polling()