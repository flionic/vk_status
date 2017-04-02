import requests
import time
import os
from datetime import datetime
from math import floor
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import locale
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import pymysql, pymysql.cursors

sqldb = pymysql.connect(host='us-cdbr-iron-east-03.cleardb.net', user='b0c8671f5877e8', password='1798e26c', db='heroku_6c46a1f67ca0243', autocommit=True) 
sqldbc = pymysql.connect(host='us-cdbr-iron-east-03.cleardb.net', user='b0c8671f5877e8', password='1798e26c', db='heroku_6c46a1f67ca0243', autocommit=True, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor) 

tg_token = os.environ.get('tg_token')
vk_token = os.environ.get('vk_token')
lastfm_user = os.environ.get('lfm_user')
lastfm_token = os.environ.get('lfm_token')
steam_user = os.environ.get('steam_user')
steam_api_key = os.environ.get('steam_key')

vkStatus = ''
def setStatus(stat):
	vk_l = 'https://api.vk.com/method/'
	token = '&access_token=' + vk_token + '&v=' + '5.52'
	try:
		r = requests.get(vk_l + 'status.set?text=' + stat + token).json()
		try:
			if r['response'] == 1:
				print('Status is set')
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
		soup = BeautifulSoup(requests.get('http://steamcommunity.com/id/bionic-leha', headers={"Accept-language":"ru"}, cookies=jar).text, 'html.parser')

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
			timeInt.insert(1, floor(timeLeft / 3600) - timeInt[0]*24)
			timeInt.insert(2, floor(timeLeft / 60) - timeInt[1]*60)
			timeInt.insert(3, floor(timeLeft) - timeInt[1]*3600 - timeInt[2]*60)
			timeStr = ''
			if timeInt[0] > 0:
				timeStr += str(timeInt[0]) + ' дн. '

			if timeInt[1] > 0:
				timeStr += str(timeInt[1]) + ' ч. '

			if timeInt[2] > 0 and timeInt[0] == 0 and timeInt[1] < 5:
				timeStr += str(timeInt[2]) + ' мин. '

			if timeInt[3] > 0 and timeInt[2] == 0 and timeInt[1] == 0:
				timeStr += str(timeInt[3]) + ' сек. '

			stStatus = 'Steam: ' + 'был в сети ' + timeStr + 'назад'
		return stStatus
	except:
		print('Error connecting to steam')
		return 'Steam error'
		
# MySQL
def readSysDB():
	global rssUpdDate, lastPostId
	try:
		with sqldbc.cursor() as cursor:
			sql = "SELECT `name`, `value` FROM `sysvars`"
			cursor.execute(sql)
			result = cursor.fetchone()
			for row in cursor:
				if row['name'] == 'lastPostId':
					lastPostId = int(row['value'])
				if row['name'] == 'rssUpdDate':
					rssUpdDate = int(row['value'])
				#print(str(row))
	except:
		pass
	#finally:
		#sqldbc.close()
		
def updateSysDB(name, value):
	try:
		with sqldbc.cursor() as cursor:
			sql = "UPDATE `sysvars` SET `value`=%s WHERE `name`=%s"
			data = (value, name)
			cursor.execute(sql, data)
	except:
		print('Error updating sysvars in db')
		
def createSysDB(name, value):
	try:
		with sqldbc.cursor() as cursor:
			sql = "INSERT INTO `sysvars` (`name`, `value`) VALUES (%s, %s)"
			cursor.execute(sql, (name, value))
	except:
		print('Error create sysvar in db')

def addSubDB(uid):
	try:
		with sqldbc.cursor() as cursor:
			sql = "INSERT INTO `users` (`id`) VALUES (%s)"
			cursor.execute(sql, (uid))
			print('Added subscriber, id: ' + str(uid))
			bot.sendMessage(chat_id=uid, text="Подписка оформлена", parse_mode=telegram.ParseMode.HTML)
	except:
		print('Error writing Sub ID')
		bot.sendMessage(chat_id=uid, text="К сожалению, произошла ошибка. Возможно, вы уже подписаны.", parse_mode=telegram.ParseMode.HTML)	
		
def delSubDB(uid):
	try:
		with sqldbc.cursor() as cursor:
			sql = "DELETE FROM `users` WHERE `id`=(%s)"
			cursor.execute(sql, (uid))
			print('Deleted subscriber, id: ' + str(uid))
			bot.sendMessage(chat_id=uid, text="Подписка отменена", parse_mode=telegram.ParseMode.HTML)
	except:
		print('Error deleting Sub ID')
		bot.sendMessage(chat_id=uid, text="К сожалению, произошла ошибка. Возможно, вы еще не подписаны.", parse_mode=telegram.ParseMode.HTML)

def readSubsDB():
	try:
		with sqldbc.cursor() as cursor:
			cursor.execute("SELECT id FROM users;")
			ids = []
			[ids.append(str(row['id'])) for row in cursor]
			return ids
	except:
		print('Error reading subs from db')
	
session = requests.Session()
rssUpdDate = 0
lastPostId = 0

readSysDB()
subs = readSubsDB()

tg_admin = '37772301'
bot = telegram.Bot(token=tg_token)
getBot = bot.getMe();
print('Telegram auth: {} as {}, id: {}'.format(getBot.first_name, getBot.username, getBot.id))

def parseFeed(force=False, fid=''):
	global rssUpdDate, lastPostId
	try:
		rss = ET.fromstring(requests.get('https://freelance.ua/orders/rss').text.encode('utf-8'))
		locale.setlocale(locale.LC_TIME, "en_US.UTF-8")
		rssPubDate = datetime.strptime(rss[0][5].text, '%a, %d %b %Y %H:%M:%S %z').timestamp()
		print(str(rssPubDate > rssUpdDate))
		print(str(rssPubDate))
		print(str(rssUpdDate))
		if (rssPubDate > rssUpdDate) or force:
			print('Parsing freelance.ua...')
			soup = BeautifulSoup(session.get('https://freelance.ua/').text, "lxml")
			orders = soup.find_all("li", class_="j-order")
			
			for i in reversed(orders):
				if not i.find_all('i', class_='fa fa-thumb-tack c-icon-fixed'):
					name = i.find('a').text
					link = i.find('a').get('href')
					for item in rss.iter('item'):
						if item.find('link').text == i.find('a').get('href'):
							categ = item.find('category').text
							pdate = item.find('pubDate').text
							locale.setlocale(locale.LC_TIME, "en_US.UTF-8")
							postTime = datetime.strptime(pdate, '%a, %d %b %Y %H:%M:%S %z')
							postTimeStamp = int(postTime.timestamp())
							locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")
							date = postTime.strftime('%a, %d %b %Y %H:%M:%S')
					price = i.find('span').text
					desc = i.find('p').text
					pid = int(link[link.find('orders/')+7:link.find('-')])
					if (pid > lastPostId) or force:
						msg = '🔗 [{}]({})\n\n💵 {}\n\n🆔 {}\n🗃 {}\n🕒️ {}\n\n📝 {}'.format(name, link, price, pid, categ, date, desc)
						if not force:
							[bot.sendMessage(chat_id=id, text=msg, parse_mode=telegram.ParseMode.MARKDOWN, disable_web_page_preview=True) for id in subs]
							print('New offer: ' + name)
							lastPostId = pid
							rssUpdDate = rssPubDate
							updateSysDB('lastPostId', lastPostId)
							updateSysDB('rssUpdDate', rssUpdDate)
						if force:
							bot.sendMessage(chat_id=fid, text=msg, parse_mode=telegram.ParseMode.MARKDOWN, disable_web_page_preview=True)
	except:
		pass
# Telegram Updater
updater = Updater(token=tg_token)
dispatcher = updater.dispatcher

def tgmStart(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    bot.sendMessage(chat_id=update.message.chat_id, text="Привет! Это бот сайта freelance.ua. Здесь вы можете отслеживать ленту заказов в реальном времени, получая уведомления прямо на свой телефон. Список команд: /help", parse_mode=telegram.ParseMode.HTML)
	
def tgmHelp(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    bot.sendMessage(chat_id=update.message.chat_id, text='Команды: \n/getOffers - получить список заказов с 1 страницы.\n/subscribe - позволяет получать заказы в реальном времени\n/unsubscribe  - отписаться от получения заказов.\n/help - помощь по командам.\n/login - авторизоваться на сайте.\n/offer [id] - предложить свою кандидатуру.\n/offermsg [text] - сообщение предложения', parse_mode=telegram.ParseMode.HTML)

def tgmGetOffers(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    parseFeed(True, update.message.chat_id)
	
def tgmSubs(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    addSubDB(update.message.chat_id)

def tgmUnsub(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    delSubDB(update.message.chat_id)	
	
dispatcher.add_handler(CommandHandler('start', tgmStart))
dispatcher.add_handler(CommandHandler('help', tgmHelp))
dispatcher.add_handler(CommandHandler('get_offers', tgmGetOffers))
dispatcher.add_handler(CommandHandler('subscribe', tgmSubs))
dispatcher.add_handler(CommandHandler('unsubscribe', tgmUnsub))

updater.start_polling()

while True:
	status = getSteam() + getLastFm()
	if status != vkStatus:
		print(status)
		setStatus(status)
		vkStatus = status
	parseFeed()
	time.sleep(3)