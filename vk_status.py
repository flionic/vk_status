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

tg_token = '358729650:AAH92APduIYym0C50XGDCscYxzRJppXaqM4'
tg_admin = '37772301'

bot = telegram.Bot(token=tg_token)

getBot = bot.getMe();
print('Telegram auth: {} as {}, id: {}'.format(getBot.first_name, getBot.username, getBot.id))

vk_token = os.environ.get('vktoken')
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
				firstTrack = " | 🎧 " + lfm['recenttracks']['track'][0]
				lfm_track = str(firstTrack['artist']['#text']) + " — " + str(firstTrack['name'])
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

			if timeInt[2] > 0 and timeInt[0] == 0:
				timeStr += str(timeInt[2]) + ' мин. '

			if timeInt[3] > 0 and timeInt[2] == 0 and timeInt[1] == 0:
				timeStr += str(timeInt[3]) + ' сек. '

			stStatus = 'Steam: ' + 'был в сети ' + timeStr + 'назад'
		return stStatus
	except:
		print('Error connecting to steam')
		return 'Steam error'
		
session = requests.Session()
lastCheck = datetime.now().timestamp() - 3600
lastPostId = 0

def parseFeed():
	global lastCheck, lastPostId
	nowTime = int(datetime.today().timestamp())
	
	if nowTime > (lastCheck + 300):
		print('Updating FL RSS...')
		rss = ET.fromstring(requests.get('https://freelance.ua/orders/rss').text.encode('utf-8'))
		rp = session.get('https://freelance.ua/')
		soup = BeautifulSoup(rp.text, "lxml")
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
				if pid > lastPostId:
					msg = '🔗 [{}]({})\n\n💵 {}\n\n🆔 ID: {}\n🗃 {}\n⌚️ {}\n\n📝 {}'.format(name, link, price, pid, categ, date, desc)
					bot.sendMessage(chat_id=tg_admin, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)
					#sendMsg(msg)
					print('Новый заказ: ' + name)
					lastPostId = pid
		lastCheck = datetime.now().timestamp()
		
def sendMsg(msg):
	response = session.get('https://api.telegram.org/bot214670545:AAGrL2TckiAs1tbaIvP0Tx70nb3Ty-e8KMU/sendMessage?parse_mode=markdown&disable_web_page_preview=true&text=' + msg + '&chat_id=37772301').json()

while True:
	status = getSteam() + getLastFm()
	if status != vkStatus:
		setStatus(status)
		vkStatus = status
		print(status)
	parseFeed()
	time.sleep(3)