from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import re
from datetime import datetime
from datetime import timedelta
from bs4 import BeautifulSoup

def parseTime(text):
	text = text.lower()
	time = datetime.now()
	
	if 'domani' in text:
		time += timedelta(days=1)
		text = text.replace('domani ', '')
	if '.' in text:
		splitChar = '.'
	if ':' in text:
		splitChar = ':'
	tupla = text.partition(splitChar)
	time = time.replace(hour=int(tupla[0]), minute=int(tupla[2]))
	return time

def isTime(text):
	try:
		pattern = re.compile('^[0-9]([0-9]|(\\.|:))((\\.|:)|[0-9])([0-9]|)([0-9]|)')
		if pattern.match(text):
			if '.' in text:
				splitChar = '.'
			if ':' in text:
				splitChar = ':'
			tupla = text.partition(splitChar)
			#Controlla che la data inserita sia successiva alla data corrente
			now = datetime.now()
			if (int(tupla[0]) < 25 and int(tupla[2]) < 60) and ((int(tupla[0]) > now.hour) or (int(tupla[0]) == now.hour and int(tupla[2]) > now.minute)):
				return True
		
		pattern = re.compile('^(domani\\s)([0-9])([0-9]|(\\.|:))((\\.|:)|[0-9])([0-9]|)([0-9]|)', re.IGNORECASE)
		if pattern.match(text):
			if '.' in text:
				splitChar = '.'
			if ':' in text:
				splitChar = ':'
			text = text.replace('domani ', '')
			tupla = text.partition(splitChar)
			if int(tupla[0]) < 25 and int(tupla[2] < 60):
				return True
		return False
	except:
		return False
	return False


def isValidCommand(text):
	if text == '/base' or text == '/basespedizionegratuita' or text == '/offertagiorno' or text == '/offertagiornospedizionegratuita':
		return True
	else:
		return False


def isLink(text):
	if "https://amzn.to" in text:
		return True
	else:
		return False


def getResponseKeyboard(url):
	keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Compra ora! 🔥', url=url)]])
	return keyboard


def parsePage(page):
	soup = BeautifulSoup(page, 'html.parser')
	#nomeProdotto = soup.body.find('span', attrs={'id':'productTitle'}).text
	#<span id='productTitle'>
	#return nomeProdotto
	return 'prova'