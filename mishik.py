# Оголошення бібліотек, що будуть використані
from cgitb import text
from turtle import pen
import requests
from urllib.request import Request, urlopen
import html2text
from lxml import html
from youtube_dl import YoutubeDL
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand
import sqlite3
# Підключення до файлу з БД, присвоєння курсиву змінній
con = sqlite3.connect('db.db')
cur = con.cursor()
# Присвоєння Токену бота змінній
API_TOKEN = '5289340949:AAFy6IEjrEgo8SAp7QXfT4RqOALyNmnrkxE'

# Ініціалізація бота ти диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
# функція встановлення команд бота
async def set_commands(bot: Bot):
    commands = [ # Список команд та їх опису
        BotCommand(command="/start", description="Start or reload bot"),
        BotCommand(command="/lyrics", description="Search lyrics"),
        BotCommand(command="/hist", description="Wiev you searched songs"),
    ]
    await bot.set_my_commands(commands) # Присвоєння команд

class SearchLyrics(StatesGroup): # Оголошення класу SearchLyrics
    song_name = State() # Перший стан класу

# Команда /start
@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    await set_commands(bot) # застосування меню з командами
    await message.reply('Type /lyrics to start search lyrics \nOr /hist to show history ') # Повідомлення відповідь клієнту
# Команда /lyrics
@dp.message_handler(commands="lyrics")
async def cmd_start(message: types.Message):
    await SearchLyrics.song_name.set() # Ініціалізація початку StatesGroup
    await message.reply('Enter exact song name: ') # Повідомлення відповідь клієнту

@dp.message_handler(state=SearchLyrics.song_name)
async def openLibrary_mainMenu(message: types.Message, state: FSMContext):
    await state.finish() # Ініціалізація закінчення StatesGroup
# фарматування запиту користувача під загальноприйняті назви пісень
    a = str(search(message.text)).lower()
    title = (a[a.find("""'title': '"""):a.find("""', 'formats'""")]).replace("""'title': '""", '')
    if '[official music video]' in title:
        title = title.replace('[official music video]', '')
    elif '(official music video)' in title:
        title = title.replace('(official music video)', '')
    elif '(visualizer)' in title:
        title = title.replace('(visualizer)', '')
    elif '(feat.' in title:
        mm = title.split('(feat.')[0]
        title = mm
    elif 'feat.' in title:
        mm = title.split('feat.')[0]
        title = mm
    elif '(official' in title:
        mm = title.split('(official')[0]
        title = mm
    elif '[official' in title:
        mm = title.split('[official')[0]
        title = mm
    elif ' [' in title:
        mm = title.split(' [')[0]
        title = mm
    elif ' [video' in title:
        mm = title.split(' [video')[0]
        title = mm
    elif '"' in title:
        title = title.replace('"', '')
    
    print(title)

    title_to_db = title # Присвоєння змінній даних для занотовування в БД
# форматування під URL-адресацію
    title = title.replace(' - ', '-')
    title = title.replace(' ', '-')
    title = title.replace('--', '-')
    print(title)
# створення URL посилання для пошуку необхідних даних
    req_url = f'https://genius.com/{title}'
    try: # перевірка наявності даних
        if req_url[-1] == '-':
            req_url = req_url + 'lyrics'
        else:
            req_url = req_url + '-lyrics'
        print(req_url)
        req = Request(req_url, headers={'User-Agent': 'Mozilla/5.0'})

        webpage_b = urlopen(req).read()
    
    except: # Помилка запиту
        await message.reply("Something went wrong, try another song,\nДопобачення телебачення!") # Повідомлення відповідь клієнту
# форматування даних для подальшого відправлення користувачеві
    webpage = webpage_b.decode('utf-8')
    _lyrics = html2text.html2text(str(webpage))
    _lyrics = _lyrics[_lyrics.find('Release Date'):_lyrics.find('\nHow to Format Lyrics:')]
    todel = _lyrics[_lyrics.find('Release Date\n'):_lyrics.find('\n##')]
    todel1 = _lyrics[_lyrics.find('Embed'):_lyrics.find('Cancel')]
    _lyrics = _lyrics.replace(todel, '').replace(todel1, '')
    size = len(_lyrics)
    _lyrics = _lyrics[:size - 12]
    _lyrics = (_lyrics[2:])[1:]
    _lyrics =  _lyrics.replace('[', '')
    _lyrics =  _lyrics.replace(']', '') 
    status_replase = False
    tmp = ""
    for i in range(len(_lyrics)): # Фільтрація лишнього тексту
        if _lyrics[i] == '(':
            if _lyrics[i+1] == '/':
                status_replase = True
        elif (_lyrics[i-1] == ')') and status_replase:
            status_replase = False
        if not status_replase:
            tmp = tmp + _lyrics[i]
    _lyrics = tmp

# Занотовування отриманих даних в БД з попередньою перевіркою на наявність таких
    cur.execute("SELECT songname FROM user_history WHERE userid = ? AND songname=?", (message.chat.id, title_to_db,))
    data=cur.fetchall()
    if len(data)==0: # перевірка наявності композиції в базі
        frequency = 0
        cur.execute(f"INSERT INTO user_history VALUES ({message.chat.id}, '{title_to_db}', {frequency})") # Додавання композициї в БД
        con.commit()
    # Приріст частоти запитів композиції користувачем
    cur.execute(f"UPDATE user_history SET frequency = frequency + 1 WHERE userid = ? AND songname = ?", (message.chat.id, title_to_db,))
    con.commit()

# Вивід і відправлення користувачеві відповіді на його запит
    print(_lyrics)
    await message.answer(_lyrics)

# Перевірка введених даних через пошук у YouTube
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
def search(arg):
    with YoutubeDL(YDL_OPTIONS) as ydl:
        try: # перевірка запиту
            requests.get(arg) 
        except: # Помилка
            video = ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]
        else:
            video = ydl.extract_info(arg, download=False)
    return video
    
# Команда /hist
@dp.message_handler(commands="hist")
async def cmd_hist(message: types.Message):
    cur.execute("SELECT songname FROM user_history WHERE userid = ?", (message.chat.id,)) # Діставання з БД songname користувача
    data=cur.fetchall() # Форматування даних з БД
    if len(data)==0: # Якщо БД порожня
        await message.reply("You have no search history") # Повідомлення відповідь клієнту
    else:
        msg = 'You searched songs lyrics:\n'
        for i in data:
            msg = msg + f' - "{i[0].title()}"\n' # Сумування даних з БД в одне повідомлення
        await message.reply(msg) # Повідомлення відповідь клієнту

# Оголошення режиму Long-polling для aiogram
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)