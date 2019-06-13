import os
import time
import logging
import configparser
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from session import Session
from post import Post
from datetime import datetime
from datetime import timedelta
from tornado import ioloop
from threading import Thread
import requests
import utils


def handle(msg):
	if 'from' in msg and 'username' in msg['from']:
		logging.info('>request from user: ' + msg['from']['username'])
		username = msg['from']['username']

	if 'from' in msg and 'id' in msg['from']:
		currId = str(msg['from']['id'])
		logging.info('>id: ' + currId)

		# Check if user is authorized
		if not isAuthorized(currId):
			logging.error('>user ' + currId + ' not authorized!')
			return

		text = msg['text']
		logging.info('>text: ' + text)

		if utils.isValidCommand(text):
			tipoPost = text.replace('/', '');
			logging.debug('>tipoPost: ' + tipoPost)
			logging.info('>command - currId: ' + currId)
			bot.sendMessage(currId, 'Invia il link')
			setSession(currId, 'scelta', text, '', tipoPost)
			return

		currentSession = getSession(currId)

		if currentSession.step == 'scelta' and utils.isLink(text):
			link = text
			logging.info('>link - currId: ' + currId)
			rand = os.urandom(10)
			idPost = int.from_bytes(rand, 'big')
			res = ''
			try:
				logging.debug('>begin download page')
				pageObj = requests.get(link)
				logging.debug('>end download page')
				#logging.debug(pageObj)
				page = pageObj.text
				logging.debug('>page: ' + page)
				res = utils.parsePage(page) # TODO: Parsa la pagina per ottenere i dati
			except Exception as e:
				logging.error('>Error in parsing page: ' + link + ' - currId: ' + currId)
				logging.error(e)
				bot.sendMessage(currId, 'Errore, invia un link valido')
				return

			logging.info('>res: ' + res)
			setSession(currId, 'link', idPost, link, currentSession.tipoPost)
			tipoPost = currentSession.tipoPost
			logging.debug('>tipoPost: ' + tipoPost)
			# TODO: Prendi i dati da res
			post = Post(idUtente=currId, idPost=idPost, conferma=False, orario='', link=link, nomeProdotto='mio prodotto', prezzoPieno='', prezzoAttuale='', sconto='', scontoPercentuale='', tipoPost=tipoPost, inviato=False)
			postList.append(post)
			postText = composePost(post)
			keyboard = utils.getResponseKeyboard(link)
			bot.sendMessage(currId, postText, reply_markup=keyboard, parse_mode='Markdown')
			bot.sendMessage(currId, 'Invia l\'orario di programmazione')
			return

		if currentSession.step == 'link':
			if utils.isTime(text):
				logging.info('>time - currId: ' + currId)
				setSession(currId, 'orario', currentSession.note, currentSession.link, currentSession.tipoPost)
				orario = utils.parseTime(text)
				post = getPost(currentSession.note)
				post.orario = orario
				minute = str(orario.minute)
				if len(minute) == 1:
					minute = '0' + minute
				bot.sendMessage(currId, 'Confermi la programmazione in data ' + orario.strftime("%d/%m/%y") + ' ' + str(orario.hour) + ':' + minute + ' ?')
			else:
				bot.sendMessage(currId, 'Orario errato. Riprova')
			return

		if currentSession.step == 'orario' and (text.lower() == 's' or text.lower() == 'si'): #TODO: Modifica con un bottone
			logging.info('>confirm - currId: ' + currId)
			logging.debug('>idPost: ' + str(currentSession.note))
			post = getPost(currentSession.note)
			post.conferma = True
			logging.info('>post: ' + str(post.idPost) + ' confirmed currId: ' + currId)
			telegram_channel = config['telegram_api']['telegram_channel']
			#bot.sendMessage(telegram_channel, str(post.idPost))
			bot.sendMessage(currId, 'Post programmato correttamente')
			setSession(currId, 'conferma', '', '', '')

	else:
		logging.error('>unable to get id from request')


def isAuthorized(userId):
	# Check if user is authorized
	isAuthorized = False
	for x in range(0, len(authorizedUsers)):
		if authorizedUsers[x] == userId:
			isAuthorized = True
	return isAuthorized

def getPost(idPost):
	for x in range(0, len(postList)):
		if postList[x].idPost == idPost:
			return postList[x]

def getSession(currId):
	logging.info('>getSession currId: ' + currId)
	for x in range(0, len(sessionList)):
		logging.debug('>getSession in for')
		logging.debug('sessionList[' + str(x) + '].currId ' + sessionList[x].currId)
		if sessionList[x].currId == currId:
			logging.debug('>getSession in if')
			return sessionList[x]


def setSession(currId, step, note, link, tipoPost):
	logging.info('>setSession currId: ' + currId)
	isIn = False
	for x in range(0, len(sessionList)):
		logging.info('>setSession in for')
		if sessionList[x].currId == currId:
			logging.info('>setSession in if')
			sessionList[x].step = step
			sessionList[x].note = note
			sessionList[x].link = link
			sessionList[x].tipoPost = tipoPost
			isIn = True

	if not isIn:
		logging.info('>setSession if not isIn')
		currentSession = Session(currId, step, note, link, tipoPost)
		sessionList.append(currentSession)


def sendPost(post, telegramChannel):
	postText = composePost(post)
	keyboard = utils.getResponseKeyboard(post.link)
	bot.sendMessage(telegramChannel, postText, reply_markup=keyboard, parse_mode='Markdown')

def composePost(post):
	templateParser = configparser.ConfigParser()
	templateParser.read('post.template')
	logging.debug('>composePost post.tipoPost ' + post.tipoPost)
	template = templateParser['post_template'][post.tipoPost]
	template = template.replace('nomeProdotto', post.nomeProdotto)
	template = template.replace('prezzoPieno', post.prezzoPieno)
	template = template.replace('prezzoAttuale', post.prezzoAttuale)
	template = template.replace('sconto', post.sconto)
	template = template.replace('percentuale', post.scontoPercentuale)
	return template


def startMainLoop():
	MessageLoop(bot, handle).run_forever()

def startScheduleLoop():
	telegram_channel = config['telegram_api']['telegram_channel']
	while True:
		now = datetime.now()
		for x in range(0, len(postList)):
			if isinstance(postList[x].orario, datetime) and now.date() == postList[x].orario.date() and now.hour == postList[x].orario.hour and now.minute == postList[x].orario.minute:
				logging.info('>sending post idPost ' + str(postList[x].idPost))
				sendPost(postList[x], telegram_channel);
				#bot.sendMessage(telegram_channel, str(postList[x].idPost))
				del postList[x]
				break
		time.sleep(2)


config = configparser.ConfigParser()
config.read('config.ini')

log_file = config['environment']['log_file']
logging.basicConfig(filename=log_file, level=logging.DEBUG)

telegram_token = config['telegram_api']['telegram_token']
bot = telepot.Bot(telegram_token)

# Lista delle sessioni
sessionList = []

# Lista dei post
postList = []

# Lista di utenti autorizzati
authorizedUsers = []
user1 = config['authorized_users']['user_1']
authorizedUsers.append(user1)

#print (bot.getMe())

logging.info('START')

t1 = Thread(target=startMainLoop)
t2 = Thread(target=startScheduleLoop)

t1.start()
t2.start()