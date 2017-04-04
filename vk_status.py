import requests
import time
import os
from datetime import datetime
from math import floor
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import locale
import ast
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import pymysql, pymysql.cursors

tg_token = os.environ.get('tg_token')
vk_token = os.environ.get('vk_token')
lastfm_user = os.environ.get('lfm_user')
lastfm_token = os.environ.get('lfm_token')
steam_user = os.environ.get('steam_user')
steam_api_key = os.environ.get('steam_key')

vkStatus = ''


def setStatus(stat):
    global vkStatus
    vk_l = 'https://api.vk.com/method/'
    token = '&access_token=' + vk_token + '&v=' + '5.52'
    try:
        r = requests.get(vk_l + 'status.set?text=' + stat + token).json()
        try:
            if r['response'] == 1:
                vkStatus = stat
                print('VK Status updated\n' + stat)
        except:
            try:
                print("VK returned error: " + r['error']['error_msg'])
            except:
                print('Request from VK: ' + r)
    except:
        print('Error connecting to VK')


def getLastFm():
    lfm_api = 'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=' + lastfm_user + '&api_key=' + lastfm_token + '&format=json'
    try:
        lfm = requests.get(lfm_api).json()
        try:
            if lfm['recenttracks']['track'][0]['@attr']['nowplaying'] == 'true':
                firstTrack = lfm['recenttracks']['track'][0]
                lfm_track = " | 🎧 " + str(firstTrack['artist']['#text']) + " — " + str(firstTrack['name'])
                lfm_track = lfm_track.replace('&', '%26')
                lfm_track = lfm_track.replace('#', '%23')
                return lfm_track
        except:
            return ''
    except:
        print('Error connecting to LastFM')
        return ' | LastFM error'


def getSteam():
    try:
        stApi = 'http://api.steampowered.com/'
        stGetUsr = 'ISteamUser/GetPlayerSummaries/v0002/'
        stKey = '?key=' + steam_api_key
        stUsr = '&steamids=' + steam_user
        stStatus = 'Steam: '
        steamInfo = requests.get(stApi + stGetUsr + stKey + stUsr).json()
        stStates = ['не в сети', 'в сети', 'не беспокоить', 'нет на месте', 'спит', 'хочет обменяться', 'хочет играть'];
        userInfo = steamInfo['response']['players'][0]
        lastLogOff = userInfo['lastlogoff']
        state = userInfo['personastate']

        jar = requests.cookies.RequestsCookieJar()
        jar.set('steamCountry', 'UA%7C7e6eab972569ec77b5d70baea9be6f58')
        soup = BeautifulSoup(requests.get('http://steamcommunity.com/id/bionic-leha', headers={"Accept-language": "ru"},
                                          cookies=jar).text, 'html.parser')

        stHeader = str(soup.find_all("div", class_="profile_in_game_header"))
        stGame = str(soup.find_all("div", class_="profile_in_game_name"))
        stHeader = stHeader[37:stHeader.find("</div>")]
        stGame = stGame[35:stGame.find("</div>")]

        stStatus = 'Steam: ' + stStates[state]

        if len(stGame) > 1:
            stStatus = '🎮 ' + stGame

        if state == 0:
            lastOnline = datetime.fromtimestamp(int(lastLogOff)).strftime('%H:%M:%S %d-%m-%Y')
            timeLeft = round(time.time()) - lastLogOff
            timeInt = []
            timeInt.insert(0, floor(timeLeft / 86400))
            timeInt.insert(1, floor(timeLeft / 3600) - timeInt[0] * 24)
            timeInt.insert(2, floor(timeLeft / 60) - timeInt[1] * 60)
            timeInt.insert(3, floor(timeLeft) - timeInt[1] * 3600 - timeInt[2] * 60)
            timeStr = ''
            if timeInt[0] > 0:
                timeStr += str(timeInt[0]) + ' дн. '
            if timeInt[1] > 0 and timeInt[0] < 5:
                timeStr += str(timeInt[1]) + ' ч. '
            if timeInt[2] > 0 and timeInt[0] == 0:
                timeStr += str(timeInt[2]) + ' мин. '
            if timeInt[3] > 0 and timeInt[2] == 0 and timeInt[1] == 0:
                timeStr += str(timeInt[3]) + ' сек. '
            stStatus = 'Steam: ' + 'был в сети ' + timeStr + 'назад'
        return stStatus
    except:
        print('Error connecting to steam')
        return 'Steam error'


# MySQL
sqldbc = pymysql.connect(host='us-cdbr-iron-east-03.cleardb.net', user='b0c8671f5877e8', password='1798e26c',
                         db='heroku_6c46a1f67ca0243', autocommit=True, charset='utf8mb4',
                         cursorclass=pymysql.cursors.DictCursor)


def rsDataBase():
    sqldbc.close()
    sqldbc.connect()
    print('Reconnecting to database')


def readSysDB(name):
    try:
        # sqldbc.connect()
        with sqldbc.cursor() as cursor:
            sql = "SELECT value FROM sysvars WHERE name=(%s)"
            cursor.execute(sql, (name))
            for row in cursor:
                return row['value']
                # sqldbc.close()
    except:
        print('Error getting sysvars from db')
        rsDataBase()
        return 0
        # sqldbc.close()


def updateSysDB(name, value):
    try:
        # sqldbc.connect()
        with sqldbc.cursor() as cursor:
            sql = "UPDATE `sysvars` SET `value`=%s WHERE `name`=%s"
            data = (value, name)
            cursor.execute(sql, data)
            return value
            # sqldbc.close()
    except:
        print('Error updating sysvars in db')
        rsDataBase()


def createSysDB(name, value):
    try:
        # sqldbc.connect()
        with sqldbc.cursor() as cursor:
            sql = "INSERT INTO `sysvars` (`name`, `value`) VALUES (%s, %s)"
            cursor.execute(sql, (name, value))
            # sqldbc.close()
    except:
        print('Error create sysvar in db')
        rsDataBase()


def addPostInfo(id, link):
    try:
        with sqldbc.cursor() as cursor:
            sql = "INSERT INTO posts (id, link) VALUES (%s, %s)"
            cursor.execute(sql, (id, link))
    except:
        rsDataBase()
        print('Error adding data to posts')


def getPostLink(pid):
    try:
        rsDataBase()
        with sqldbc.cursor() as cursor:
            sql = "select link from posts where id={}".format(pid)
            cursor.execute(sql)
            for i in cursor:
                return i
    except:
        print('Error checking account')
        rsDataBase()


def userExist(uid):
    try:
        rsDataBase()
        with sqldbc.cursor() as cursor:
            sql_f = "select id from users where id={}".format(uid)
            cursor.execute(sql_f)
            for i in cursor:
                return True
    except:
        print('Error checking account')
        rsDataBase()


def addSubDB(uid):
    try:
        with sqldbc.cursor() as cursor:
            sql = "INSERT INTO `users` (`id`) VALUES (%s)"
            if not userExist(uid):
                cursor.execute(sql, (uid))
                print('Added subscriber, id: ' + str(uid))
                bot.sendMessage(chat_id=uid, text="Подписка оформлена", parse_mode=telegram.ParseMode.HTML)
            else:
                bot.sendMessage(chat_id=uid, text="По нашим сведениям, вы уже подписаны :)",
                                parse_mode=telegram.ParseMode.HTML)
    except:
        print('Error writing Sub ID')
        bot.sendMessage(chat_id=uid, text="К сожалению, произошла ошибка. Повторите попытку еще раз.",
                        parse_mode=telegram.ParseMode.HTML)
        rsDataBase()


def getUsersData(name, uid):
    try:
        rsDataBase()
        if userExist(uid):
            with sqldbc.cursor() as cursor:
                sql = "select {} from users where id={}".format(name, uid)
                cursor.execute(sql)
                for row in cursor:
                    return str(row[name])
        else:
            bot.sendMessage(chat_id=uid, text="Для продолжения, вы должны быть подписчиком.\nПодписаться - /subscribe",
                            parse_mode=telegram.ParseMode.HTML)
    except:
        print('Error getting from users table')
        bot.sendMessage(chat_id=uid, text="К сожалению, произошла ошибка. Повторите попытку еще раз.",
                        parse_mode=telegram.ParseMode.HTML)


def delSubDB(uid):
    try:
        rsDataBase()
        with sqldbc.cursor() as cursor:
            sql = "DELETE FROM `users` WHERE `id`=(%s)"
            if userExist(uid):
                cursor.execute(sql, (uid))
                print('Deleted subscriber, id: ' + str(uid))
                bot.sendMessage(chat_id=uid, text="Подписка отменена, а так же удалены все данные",
                                parse_mode=telegram.ParseMode.HTML)
            else:
                bot.sendMessage(chat_id=uid,
                                text="Для продолжения, вы должны быть подписчиком.\nПодписаться - /subscribe",
                                parse_mode=telegram.ParseMode.HTML)
    except:
        print('Error removing sub')
        bot.sendMessage(chat_id=uid, text="К сожалению, произошла ошибка. Повторите попытку еще раз.",
                        parse_mode=telegram.ParseMode.HTML)
        rsDataBase()


def getSubs():
    try:
        # sqldbc.connect()
        with sqldbc.cursor() as cursor:
            cursor.execute("SELECT id FROM users;")
            ids = []
            [ids.append(str(row['id'])) for row in cursor]
            return ids
            # sqldbc.close()
    except:
        print('Error while reading subs')
        rsDataBase()
        return 0


def updUsersData(name, value, uid):
    try:
        with sqldbc.cursor() as cursor:
            sql = 'UPDATE users SET {}="{}" WHERE id={}'.format(name, value, uid)
            if userExist(uid):
                cursor.execute(sql)
                print('Adding account {}: {}'.format(uid, name))
                bot.sendMessage(chat_id=uid, text="К вашему аккаунту успешно добавлен " + name,
                                parse_mode=telegram.ParseMode.HTML)
            else:
                bot.sendMessage(chat_id=uid,
                                text="Для начала вы должны быть подписчиком бота.\nПодписаться - /subscribe",
                                parse_mode=telegram.ParseMode.HTML)
    except:
        print('Error while adding userData')
        bot.sendMessage(chat_id=uid, text="Ошибка отправки " + name, parse_mode=telegram.ParseMode.HTML)


rssUpdDate = 0
lastPostId = int(readSysDB('lastPostId'))

session = requests.Session()
err = ''

def parseFlance(fid=''):
    global rssUpdDate, lastPostId, err
    try:
        rss = ET.fromstring(requests.get('https://freelance.ua/orders/rss').text.encode('utf-8'))
        locale.setlocale(locale.LC_TIME, "en_US.UTF-8")
        rssPubDate = datetime.strptime(rss[0][5].text, '%a, %d %b %Y %H:%M:%S %z').timestamp() + 10700
        if (rssPubDate > rssUpdDate) or fid:
            print('Parsing freelance.ua...')
            get_site = session.get('https://freelance.ua/')
            err = get_site.status_code + ' ' + get_site.json()
            soup = BeautifulSoup(get_site.text, "lxml")
            orders = soup.find_all("li", class_="j-order")
            for order in reversed(orders):
                if not order.find_all('i', class_='fa fa-thumb-tack c-icon-fixed'):
                    name = order.find('a').text
                    link = order.find('a').get('href')
                    for item in rss.iter('item'):
                        if item.find('link').text == order.find('a').get('href'):
                            categ = item.find('category').text
                            pdate = item.find('pubDate').text
                            locale.setlocale(locale.LC_TIME, "en_US.UTF-8")
                            postTime = datetime.strptime(pdate, '%a, %d %b %Y %H:%M:%S %z')
                            postTimeStamp = int(postTime.timestamp())
                            locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")
                            date = postTime.strftime('%a, %d %b %Y %H:%M:%S')
                    price = order.find('span').text
                    desc = order.find('p').text
                    pid = int(link[link.find('orders/') + 7:link.find('-')])
                    rssUpdDate = updateSysDB('rssUpdDate', rssPubDate)
                    if (pid > lastPostId) or fid or rssUpdDate == 0:
                        msg = '🔗 [{}]({})\n\n💵 {}\n\n🆔 {}\n🗃 {}\n🕒️ {}\n\n📝 {}'.format(name, link, price, pid,
                                                                                             categ, date, desc)
                        if not fid:
                            addPostInfo(pid, link)
                            [bot.sendMessage(chat_id=id, text=msg, parse_mode=telegram.ParseMode.MARKDOWN,
                                             disable_web_page_preview=True) for id in getSubs()]
                            print('New offer: ' + name)
                            lastPostId = updateSysDB('lastPostId', pid)
                        else:
                            bot.sendMessage(chat_id=fid, text=msg, parse_mode=telegram.ParseMode.MARKDOWN,
                                            disable_web_page_preview=True)
    except:
        print('Error parse freelance.ua ' + str(err))


def authFlance(uid, ulogin='', upassw=''):
    try:
        login = [getUsersData('login', uid), ulogin][len(ulogin) > 0]
        passw = [getUsersData('pass', uid), upassw][len(upassw) > 0]
        if type(login) is str and type(passw) is str:
            form_data = {'email': login, 'pass': passw, 'remember': True, 'submit': 'submit'}
            response = session.post('https://freelance.ua/user/login', data=form_data).json()
            if response['data']['success']:
                print('Successful auth')
                updUsersData('cookie', str(session.cookies.get_dict()), uid)
                bot.sendMessage(chat_id=uid, text='Успешная авторизация', parse_mode=telegram.ParseMode.MARKDOWN)
            elif not response['data']['success']:
                print('Auth error: ' + str(response['errors']))
                bot.sendMessage(chat_id=uid, text='Ошибка авторизации: ' + str(response['errors'][
                                                                                   0]) + '\n\nОтправьте сообщения по типу:\n\n/login your_login / email\n/pass your_password',
                                parse_mode=telegram.ParseMode.HTML)
                # getLogin()
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text='Недостаточно данных для авторизации.\nОтправьте сообщения по типу:\n\n/login your_login / email\n/pass your_password',
                            parse_mode=telegram.ParseMode.HTML)
    except:
        print('Error auth on Flance' + str(response.status_code))
        # print(rp.text)


def loginFlance(uid):
    try:
        # cook = [authFlance(uid),ast.literal_eval(getUsersData('cookie', uid))][ast.literal_eval(getUsersData('cookie', uid))]
        cook = ast.literal_eval(getUsersData('cookie', uid))
        if cook:
            jar = requests.cookies.RequestsCookieJar()
            for i in cook:
                jar.set(i, cook[i])
            response = session.get('https://freelance.ua/', cookies=jar)
            soup = BeautifulSoup(response.text, "lxml")
            try:
                uname = soup.find("li", class_="hidden-xs").text
                bot.sendMessage(chat_id=uid, text='Авторизация успешная. Привет, {}!'.format(uname),
                                parse_mode=telegram.ParseMode.HTML)
            except:
                bot.sendMessage(chat_id=uid, text='Что-то пошло не так...Возможно сессия устарела?',
                                parse_mode=telegram.ParseMode.HTML)
        else:
            authFlance(uid)
    except:
        print("Error loggining to site")


def sendOffer(uid, link, desc=''):
    try:
        # link = 'https://freelance.ua/orders/12923-dizajn-sajta-tematika-avtomobili.html'
        descr = desc if desc else 'Доброго времени суток! Заинтересовало ваше предложение, готов работать!'

        soup = BeautifulSoup(session.get(link).text, "lxml")
        order_id = soup.find_all("input", attrs={"type": "hidden"})[2]['value']
        hash = soup.find("meta", attrs={"name": "csrf_token"})['content']

        headers = {'Origin': 'https://freelance.ua', 'Accept-Encoding': 'gzip, deflate, br',
                   'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
                   'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   'Accept': 'application/json, text/javascript, */*; q=0.01', 'Referer': link,
                   'X-Requested-With': 'XMLHttpRequest', 'Connection': 'keep-alive'}
        fdata = {'order_id': order_id, 'price_from': '', 'price_to': '', 'price_curr': '1', 'terms_from': '',
                 'terms_to': '', 'terms_type': '1', 'descr': descr, 'hash': hash}

        response = session.post(
            'https://freelance.ua/index.php?bff=ajax&s=orders&ev=offer_add&hash=' + hash + '&lng=ru&act=add',
            data=fdata, headers=headers)

        if response['data']['success']:
            bot.sendMessage(chat_id=uid, text='Запрос успешно добавлен. Отслеживать можно тут:\n' + link,
                            parse_mode=telegram.ParseMode.MARKDOWN)
        elif not response['data']['success']:
            print('Auth error: ' + str(response['errors']))
            bot.sendMessage(chat_id=uid, text='Ошибка авторизации: ' + str(response['errors'][0]) + '/auth_help',
                            parse_mode=telegram.ParseMode.HTML)
    except:
        bot.sendMessage(chat_id=uid, text='Что-то пошло не так...', parse_mode=telegram.ParseMode.HTML)


# Telegram
tg_admin = '37772301'
bot = telegram.Bot(token=tg_token)
updater = Updater(token=tg_token)
print('Telegram auth: {} as @{}, id: {}'.format(bot.getMe().first_name, bot.getMe().username, bot.getMe().id))
bot.sendMessage(tg_admin, 'Bot restarted')
dispatcher = updater.dispatcher


def tgmStart(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Привет! Это бот сайта freelance.ua. Здесь вы можете отслеживать ленту заказов в реальном времени, получая уведомления прямо на свой телефон. Список команд: /help",
                    parse_mode=telegram.ParseMode.HTML)


def tgmHelp(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    bot.sendMessage(chat_id=update.message.chat_id, text="""
	Команды:
	/get_offers - получить список заказов с 1 страницы
	/subscribe - подписка на заказы в реальном времени
	/unsubscribe  - отписаться от получения заказов
	/auth - авторизация на сайте
	/fauth [login] [pass] - авторизация на сайте, сохранятся только cookie)
	/help_auth - информация про авторизацию
	/offer [id] - предложить свою кандидатуру шаблоном
	/offer [id][text] - предложить свою кандидатуру с сообщением [text]
	/offermsg [text] - шаблон сообщения предложения
	""", parse_mode=telegram.ParseMode.HTML)


def tgmHelpSec(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    bot.sendMessage(chat_id=update.message.chat_id, text="""
Бот имеет два вида авторизации.

Первый: /auth
Универсальный метод авторизации, сначала ищет в базе данных куки, если их нет - ищет логин/пароль, а если нет и их - предлагает авторизоваться.
Сохраняет логин, пароль и куки. Спросит отдельно логин и пароль.

Второй: /fauth
Позволяет войти на сайт без сохранения пароля. Ваши логин и пароль единоразово уходят на сервер, в ответ бот получает куки, и уже их сохраняет. В этом случае в базе данных бота логин и пароль сохранятся не будет!
Пример такой авторизации:
"/fauth user_name password"
	""", parse_mode=telegram.ParseMode.HTML)


def tgmAuth(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    loginFlance(update.message.chat_id)
    # authFlance(update.message.chat_id)


def tgmAuthForce(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    try:
        login = update.message.text.split(" ")[1]
        passw = update.message.text.split(" ")[2]
        authFlance(update.message.chat_id, login, passw)
    except:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text='Проверьте правильность данных, вы что-то упустили.\nВаше сообщение должно выглядеть так:\n"/fauth login password"',
                        parse_mode=telegram.ParseMode.HTML)


def tgmLogin(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    if len(update.message.text) > 10:
        login = (update.message.text).split(" ")[1]
        updUsersData('login', login, update.message.chat_id)
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text='Вы не ввели логин.\nСообщение должно иметь вид:\n"/login my_name"',
                        parse_mode=telegram.ParseMode.HTML)


def tgmPass(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    if len(update.message.text) > 10:
        passw = (update.message.text).split(" ")[1]
        updUsersData('pass', passw, update.message.chat_id)
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text='Вы не ввели пароль.\nСообщение должно иметь вид:\n"/pass 1q2w3e4r5t"',
                        parse_mode=telegram.ParseMode.HTML)


def tgmGetOffers(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    parseFlance(update.message.chat_id)


def tgmSubs(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    addSubDB(update.message.chat_id)


def tgmUnsub(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    delSubDB(update.message.chat_id)


def tgmRsDb(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    rsDataBase()
    bot.sendMessage(chat_id=update.message.chat_id, text='Отправлена команда переподключения к серверу базы данных',
                    parse_mode=telegram.ParseMode.HTML)


def tgmAddOffer(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    try:
        pid = (update.message.text).split(" ")[1]
        bot.sendMessage(chat_id=update.message.chat_id, text='ID: {}\n\n{}'.format(pid, getPostLink(pid)),
                        parse_mode=telegram.ParseMode.HTML)
    # sendOffer(update.message.chat_id, link, (update.message.text).split(" ")[2])
    except:
        bot.sendMessage(chat_id=update.message.chat_id, text='ID поста не указан', parse_mode=telegram.ParseMode.HTML)


dispatcher.add_handler(CommandHandler('start', tgmStart))
dispatcher.add_handler(CommandHandler('help', tgmHelp))
dispatcher.add_handler(CommandHandler('help_auth', tgmHelpSec))
dispatcher.add_handler(CommandHandler('get_offers', tgmGetOffers))
dispatcher.add_handler(CommandHandler('subscribe', tgmSubs))
dispatcher.add_handler(CommandHandler('unsubscribe', tgmUnsub))
dispatcher.add_handler(CommandHandler('auth', tgmAuth))
dispatcher.add_handler(CommandHandler('fauth', tgmAuthForce))
dispatcher.add_handler(CommandHandler('login', tgmLogin))
dispatcher.add_handler(CommandHandler('pass', tgmPass))
dispatcher.add_handler(CommandHandler('reset_db', tgmRsDb))
dispatcher.add_handler(CommandHandler('offer', tgmAddOffer))

updater.start_polling()

while True:
    status = getSteam() + getLastFm()
    setStatus(status) if status != vkStatus else ''
    parseFlance()
    time.sleep(3)
