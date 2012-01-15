from datetime import datetime
from config import Config
import MySQLdb
import logging
import time
class Reminder:
	lastrun = 0

	def __init__(self):
		self.config = Config()
		logging.basicConfig(filename=self.config.get('logfile'),level=logging.DEBUG)
		self.dbuser = self.config.get('dbuser');
		self.dbpasswd = self.config.get('dbpasswd');

	def tryRun(self):
		now = datetime.now().timetuple()[5]
		taskids = []
		if self.lastrun == 0: 
			self.lastrun = now
			return self.run()
		if abs(self.lastrun - now) < 5: 
			return taskids
		self.lastrun = now
		return self.run()
		
	def run(self):
		logging.debug("checking for reminders.")
		db = MySQLdb.connect(host = "localhost", user = self.dbuser, passwd = self.dbpasswd, db="tobo")
		cursor = db.cursor(MySQLdb.cursors.DictCursor)
		now = datetime.now().timetuple()[5]
		self.lastrun = now
		sql = "select * from reminders where processed = 0 and now()+0  between rdate-100 and rdate+100"
		cursor.execute(sql)
		rows = cursor.fetchall()
		taskids = []
		for row in rows:
			logging.info("processed reminder id %s" % row["id"])
			sql = "update reminders set processed = 1 where id = %s" % row["id"]
			cursor.execute(sql)
			taskids.append(row['todo_id'])
		return taskids

if __name__ == "__main__":
	r = Reminder()
	print r.tryRun()
	time.sleep(3)
	print r.tryRun()
	time.sleep(3)
	print r.tryRun()
