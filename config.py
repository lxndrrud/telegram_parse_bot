import requests
import datetime
import sqlite3
from pytz import timezone
from bs4 import BeautifulSoup
from private_info import mlemapi_host, mlemapi_key, weather_api_key


def send_animalpic():
    url = "https://mlemapi.p.rapidapi.com/randommlem/"
    my_headers = {
        'x-rapidapi-host': mlemapi_host,
        'x-rapidapi-key': mlemapi_key
    }
    response = requests.request('GET', url, headers=my_headers)
    response_json = response.json()
    return response_json['url']
    
def send_weather(query):
    user_timezone = timezone('Europe/Moscow')
    print(f'Weather query: {query}')
    url = f'http://api.openweathermap.org/data/2.5/weather?q={query}&appid={weather_api_key}&units=metric&lang=ru'
    try:
        response = requests.request('GET', url)
        response_json = response.json()
        try:
            rain_and_snow = f"\nОбъем дождя(?) за последний час: {response_json['rain']['1h']} мм\n" \
                            f"Объем снега(?) за последний час: {response_json['snow']['1h']} мм"
        except KeyError:
            rain_and_snow = ""
        weather_info = f"Погода в {response_json['name']}\n" \
                       f"Описание: {response_json['weather'][0]['description']}\n" \
                       f"Температура: {response_json['main']['temp']} C\n" \
                       f"Давление: {response_json['main']['pressure']} hPa\n" \
                       f"Влажность: {response_json['main']['humidity']} %\n" \
                       f"Скорость ветра: {response_json['wind']['speed']} м/c\n" \
                       f"Облачность: {response_json['clouds']['all']} %\n" \
                       f"Время сбора информации: {datetime.datetime.fromtimestamp(response_json['dt'], tz=user_timezone)}"
        weather_info += rain_and_snow
        weather_info_icons = list()
        for item in response_json['weather']:
            weather_info_icons.append(
                f"http://openweathermap.org/img/wn/{item['icon']}@2x.png")
        response.close()
    except KeyError:
        weather_info = "Ошибка в запросе или подключении."
        weather_info_icons = list()
    return [weather_info, weather_info_icons]

    
def parse_gdespaces_com(query):
    fetched_query = query.replace(' ', '%20')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    url = f"https://gdespaces.com/musicat/search/index/?sq={fetched_query}"
    try:
        response = requests.request('GET', url, headers=headers)
        print(response.status_code)
        urls, artists, titles = [], [], []
        soup = BeautifulSoup(response.text, features="html.parser")
        info = soup.find_all('div', attrs={
            'class': 'player_item player_item_old p_i_tools oh'})
        counter = 1
        for i in range(len(info)):
            if counter > 5:
                break
            url = info[i].get('data-src')
            urls.append(url)
            artist = info[i].get('data-artist')
            artists.append(artist)
            title = info[i].get('data-title')
            titles.append(title)
            counter += 1
    except AttributeError:
        return [], [], []
    #print(urls, artists, titles)
    return urls, artists, titles


def parse_w1_musify_club(query: str):
    url = "https://w1.musify.club/search"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    try:
        response = requests.post(
            url, data={'SearchText': f'{query}'}, headers=headers)
        print(response.status_code)
        soup = BeautifulSoup(response.text, features='html.parser')
        urls, artists, titles = [], [], []
        info_urls = soup.find_all('a', attrs={'itemprop': 'audio'})
        info_a_t = soup.find_all('div', attrs={'class': 'playlist__item'})
        counter = 1
        for i in range(len(info_urls)):
            if counter > 5:
                break
            url = info_urls[i].get('href')
            url = 'https://w1.musify.club/' + url
            urls.append(url)
            artist = info_a_t[i].get('data-artist')
            artists.append(artist)
            title = info_a_t[i].get('data-name')
            titles.append(title)
            counter += 1
    except AttributeError:
        return [], [], []
    return urls, artists, titles 


def connect_to_db():
    mydb = sqlite3.connect("bot.db")
    print(mydb)
    cursor = mydb.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS music (url TEXT(500), artist CHAR(100), title CHAR(60))"
    )
    return mydb

def count_music(mydb):
    cursor = mydb.cursor()
    cursor.execute('SELECT count(rowid) FROM music')
    for i in cursor:
        return i[0]


def save_music(urls, artists, titles, mydb):
    cursor = mydb.cursor()
    values = ''
    for i in range(len(urls)):
        values += f" ('{urls[i]}', '{artists[i]}', '{titles[i]}'),"
    values = values[:-1]
    #print('INSERT INTO music(url) VALUES'+values)
    cursor.execute('INSERT INTO music(url, artist, title) VALUES'+values)
    mydb.commit()


def clear_music(mydb):
    cursor = mydb.cursor()
    cursor.execute('DROP TABLE music')
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS music (url TEXT(500), artist CHAR(100), title CHAR(60))"
    )


def get_music(id: int):
    with connect_to_db() as mydb:
        cursor = mydb.cursor()
        cursor.execute(f'SELECT url, artist, title FROM music WHERE rowid={id}')
        list_ = cursor.fetchall()[0]
        if list_ == []:
            return None, None, None
        else:
            return list_[0], list_[1], list_[2]