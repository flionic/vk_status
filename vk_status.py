import requests
import time
from datetime import datetime
from math import floor
from bs4 import BeautifulSoup

vk_l = 'https://api.vk.com/method/'
stApi = 'http://api.steampowered.com/'

vk_t = '&access_token=' + '2c4edb33b0fb9816c8710aa07689736c65bbfa5a7f39198477f84a8ad01824633fef3433e0a28fa3be3b9' + '&v=' + '5.52'

lfm_api = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=bionic_leha&api_key=7c4df306bed3b7aacc413e3b17584c1a&format=json"

stGetUsr = 'ISteamUser/GetPlayerSummaries/v0002/'
stKey = '?key=' + 'C9A4A291E1DC1FF91EA8AC964E73D443'
stUsr = '&steamids=' + '76561198118803413'
stName = 'Steam: '
stStatus = ['не в сети', 'в сети', 'не беспокоить', 'нет на месте', 'спит', 'хочет обменяться', 'хочет играть'];
vkStat = ''
vkStatOld = ''

def setStatus(stat):
	try:
		r = requests.get(vk_l + 'status.set?text=' + stat + vk_t).json()
		try:
			if r['response'] == 1:
				print('Статус установлен успешно')
		except:
			try:
				print("Ошибка на стороне VK: " + r['error']['error_msg'])
			except:
				print(r)
	except:
		print('Ошибка подключения к VK')

def getSteam():
	global vkStat
	global vkStatOld
	try:
		steamInfo = requests.get(stApi + stGetUsr + stKey + stUsr).json()
		userInfo = steamInfo['response']['players'][0]
		lastLogOff = userInfo['lastlogoff']
		state = userInfo['personastate']
		#print(userInfo)
		
		jar = requests.cookies.RequestsCookieJar()
		jar.set('steamCountry', 'UA%7C7e6eab972569ec77b5d70baea9be6f58')
		soup = BeautifulSoup(requests.get('http://steamcommunity.com/id/bionic-leha', headers={"Accept-language":"ru"}, cookies=jar).text, 'html.parser')

		stHeader = str(soup.find_all("div", class_="profile_in_game_header"))
		stGame = str(soup.find_all("div", class_="profile_in_game_name"))

		stHeader = stHeader[37:stHeader.find("</div>")]
		stGame = stGame[35:stGame.find("</div>")]


		vkStat = stName + stStatus[state]

		if len(stGame) > 1:
			#vkStat = '🎮 ' + userInfo['gameextrainfo']
			vkStat = '🎮 ' + stGame

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

			vkStat = stName + ' был в сети ' + timeStr + 'назад'
			
		try:
			lfm = requests.get(lfm_api).json()
			if lfm['recenttracks']['track'][0]['@attr']['nowplaying'] == 'true':
				firstTrack = lfm['recenttracks']['track'][0]
				vkStat += " | 🎧 " + str(firstTrack['artist']['#text']) + " — " + str(firstTrack['name'])
		except:
			pass
			
		vkStat = vkStat.replace('&', '%26')
		vkStat = vkStat.replace('#', '%23')

		if vkStat != vkStatOld:
			print(vkStat)
			setStatus(vkStat)
			vkStatOld = vkStat

	except:
		print('Ошибка подключения к steam')

print(stApi + stGetUsr + stKey + stUsr)

while True:
	getSteam()
	time.sleep(3)