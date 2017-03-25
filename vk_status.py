import requests
import time
from datetime import datetime
from math import floor
from bs4 import BeautifulSoup

vk_token = '2c4edb33b0fb9816c8710aa07689736c65bbfa5a7f39198477f84a8ad01824633fef3433e0a28fa3be3b9'

lastfm_user = 'bionic_leha'
lastfm_token = '7c4df306bed3b7aacc413e3b17584c1a'

steam_user = '76561198118803413'
steam_api_key = 'C9A4A291E1DC1FF91EA8AC964E73D443'

vkStatus = ''

def setStatus(stat):
	vk_l = 'https://api.vk.com/method/'
	token = '&access_token=' + vk_token + '&v=' + '5.52'
	try:
		r = requests.get(vk_l + 'status.set?text=' + stat + token).json()
		try:
			if r['response'] == 1:
				print('Статус установлен успешно')
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
		if lfm['recenttracks']['track'][0]['@attr']['nowplaying'] == 'true':
			firstTrack = lfm['recenttracks']['track'][0]
			lfm_track = " | 🎧 " + str(firstTrack['artist']['#text']) + " — " + str(firstTrack['name'])
			lfm_track = lfm_track.replace('&', '%26')
			lfm_track = lfm_track.replace('#', '%23')
			return lfm_track
	except:
		print('Ошибка подключения к LastFM')
		return ' ошибка LastFM'

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
			timeString = []
			timeString.insert(0, floor(timeLeft / 86400))
			timeString.insert(1, floor(timeLeft / 3600) - timeString[0]*86400)
			timeString.insert(2, floor(timeLeft / 60) - timeString[1]*60)
			timeString.insert(3, floor(timeLeft) - timeString[1]*3600 - timeString[2]*60)
			timeStr = ''
			if timeString[0] > 0:
				timeStr = timeStr + str(timeString[0]) + ' дн. '

			if timeString[1] > 0:
				timeStr = timeStr + str(timeString[1]) + ' ч. '

			if timeString[2] > 0 and timeString[0] == 0:
				timeStr = timeStr + str(timeString[2]) + ' мин. '

			if timeString[3] > 0 and timeString[2] == 0:
				timeStr = timeStr + str(timeString[3]) + ' сек. '

			stStatus = 'Steam: ' + 'был в сети ' + timeStr + 'назад'
			
		return stStatus

	except:
		print('Ошибка подключения к steam')
		return ' ошибка Steam'

while True:
	status = getSteam() + getLastFm()
	if status != vkStatus:
		print(vkStatus)
		setStatus(vkStatus)
	time.sleep(3)