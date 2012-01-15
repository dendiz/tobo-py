import xmpp,sys
from config import Config
from engine import Engine
from reminder import Reminder
import MySQLdb
import logging
config = Config()
logging.basicConfig(filename=config.get('logfile'),level=logging.DEBUG)
dbuser = config.get('dbuser');
dbpasswd = config.get('dbpasswd');
server = config.get('server')
user = config.get('user')
password = config.get('password')
auths = []
def presenceCB(session, pres):
	logging.debug('Got presence type: %s' % pres.getType())
	nick=pres.getFrom().getStripped()
	if pres.getType() == "subscribe":
		if nick in auths: pass
		else:
			logging.info('subscribing to jid: %s' % pres.getFrom());
			conn.getRoster().Authorize(pres.getFrom())
			conn.getRoster().Subscribe(pres.getFrom())
			cursor = db.cursor()
			sql = "insert into users (jid) values ('%s')" % nick
			logging.debug("sql: %s" % sql)
			cursor.execute(sql)
			auths.append(nick)
			session.send(xmpp.Message(pres.getFrom(),config.get('welcome_msg')))
	if pres.getType() == "unsubscribe":
		cursor = db.cursor()
		sql = "delete from users where jid='%s'" % pres.getFrom().getStripped()
		logging.debug("sql: %s" % sql)
		cursor.execute(sql)
		auths.remove(nick)

def messageCB(session,mess):
	text = mess.getBody()
	user = mess.getFrom()
	logging.debug("MSG: %s from %s" % (text, user))
	if text is None: return 
	logging.debug("dispatching to parser engine")
	engine = Engine(user.getStripped())
	msg = engine.parse(text)
	session.send(xmpp.Message(user,msg))

def getCmd(conn):
	try:
		tasklist = rmd.tryRun()
		#TODO if task list contains task ids, send out reminder messages
		cursor = db.cursor(MySQLdb.cursors.DictCursor)
		for taskid in tasklist:
			if taskid is None: pass
			sql = "select * from todos where id = '%s'" % taskid
			cursor.execute(sql)
			row = cursor.fetchone()
			conn.send(xmpp.Message(row["jid"] , "reminder:\n%s" % row['todo']))
		conn.Process(1)
	except KeyboardInterrupt: return 0
	return 1

rmd = Reminder()
db = MySQLdb.connect(host = "localhost" , user = dbuser, passwd=dbpasswd, db="tobo")
cursor = db.cursor(MySQLdb.cursors.DictCursor)
sql = "select * from users"
cursor.execute(sql)
rows = cursor.fetchall()
for row in rows:
	auths.append(row['jid'])
#conn = xmpp.Client(server, debug=['always', 'nodebuilder'])
conn = xmpp.Client(server, debug=[])
conres = conn.connect()
if not conres:
	logging.error("Unable to connect to jabber server")
	sys.exit(1)
if conres <> 'tls':
	logging.warning("TLS failed, using plain")
authres = conn.auth(user, password)
if not authres:
	logging.error("cannot authenticate. exiting.")
	sys.exit(1)

if authres <> 'sasl':
	print 'Warning: cannot use encrypted authentication'

conn.RegisterHandler('message', messageCB)
conn.RegisterHandler('presence', presenceCB)
conn.sendInitPresence()
print 'Tobo started'
logging.info("Tobo started")
while getCmd(conn): pass

