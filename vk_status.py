import requests
import time
import os
from datetime import datetime
from math import floor
from bs4 import BeautifulSoup

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
				print('Статус установлен')
		except:
			try:
				print("VK отдал ошибку: " + r['error']['error_msg'])
			except:
				print('Запрос к ВК вернул: ' + r)
	except:
		print('Ошибка подключения к VK')
		
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
		print('Ошибка подключения к LastFM')
		return ' | ошибка LastFM'

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
		print('Ошибка подключения к steam')
		return 'Ошибка Steam'

while True:
	status = getSteam() + getLastFm()
	if status != vkStatus:
		setStatus(status)
		vkStatus = status
		print(status + '\n')
	time.sleep(3)