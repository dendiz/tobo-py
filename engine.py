import MySQLdb
import re
from config import Config
import logging
import parsedatetime.parsedatetime as pdt
import parsedatetime.parsedatetime_consts as pdc 
class Engine:
	config = Config()
	logging.basicConfig(filename=config.get('logfile'),level=logging.DEBUG)
	dbuser = config.get('dbuser')
	dbpasswd = config.get('dbpasswd')
	conn = MySQLdb.connect(host = "localhost" , user = dbuser, passwd=dbpasswd, db="tobo")
	conn.set_character_set('utf8')
	jid = "hede@hede.com"
	def __init__(self, jid):
		self.jid = jid
		conn = MySQLdb.connect(host="localhost" , user=self.dbuser, passwd=self.dbpasswd, db="tobo")

	def add(self, params):
		logging.debug("add method for jid %s params %s" % (self.jid, params))
		cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)
		sql = "select max(pos) as maxpos from todos where jid='%s'" % self.jid
		cursor.execute(sql)
		row = cursor.fetchone()
		pos = 1
		if row["maxpos"] != None:
			pos = row["maxpos"] + 1 #use a hash type here
		sql = u'INSERT INTO todos (pos,jid, todo) values (%d, "%s", "%s")' % (pos, self.jid,params[0])
		logging.debug("SQL:" + sql)
		cursor.execute(sql)
		return "ok"
		
	def search(self, params):
		logging.debug("search method for jid %s params %s" % (self.jid, params))
		st = ""
		for param in params:
			print 'adding param:'+param
			st +="%%%s" % (param)
		st = st.replace(' ','%')
		sql = "select * from todos where jid='%s' and todo like '%s%%'" % (self.jid , st)
		logging.debug("SQL:" + sql)
		cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute(sql)
		rows = cursor.fetchall()
		reply = ""
		for row in rows:
			reply += '%d(%s): %s\n' % (row["pos"],row["status"], row["todo"])
		return (reply,"nothing here")[reply == ""]

	def getlist(self, params):
		logging.debug("getlist method for jid %s params %s" % (self.jid, params))
		if len(params) > 0: params = params[0]
		sql = "select * from todos where jid = '%s' order by pos asc" % self.jid
		if params == "done" or params == "complete":
			sql = "select * from todos where jid = '%s' and status = 'C' order by pos asc" % self.jid
		if params == "incomplete" or params=="pending":
			sql = "select * from todos where jid = '%s' and status = 'I' order by pos asc" % self.jid
		if params == "reminders":
			sql = "select pos,todo,status,rdate from todos t, reminders r where r.todo_id = t.id and t.jid = '%s' and r.processed = 0" % self.jid
		cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute(sql)
		rows = cursor.fetchall()
		reply = ""
		for row in rows:
			if row.has_key("rdate"):
				rdate = "(%s)" %row["rdate"]
			else:
				rdate = ""
			reply += '%d(%s): %s %s\n' % (row["pos"],row["status"], row["todo"],rdate)
		return (reply,"nothing here")[reply == ""]

	def complete(self, params):
		logging.debug("complete method for jid %s params %s" % (self.jid, params))
		if len(params) > 0: params = params[0]
		else: return "which todo item?"
		sql = "update todos set status = 'C' where jid ='%s' and pos = %s" % (self.jid, params)
		cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute(sql)
		return "ok"

	def delete(self, params):
		logging.debug("delete method for jid %s params %s" % (self.jid, params))
		if len(params) > 0: params = params[0]
		else: return "which todo item?"
		sql = "delete from todos where jid ='%s' and pos = %s" % (self.jid, params)
		cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute(sql)
		return "ok"
	def help(self, params):
		logging.debug("help method for jid %s params %s" % (self.jid, params))
		if len(params) > 0: params = params[0]
		if params == "add":
			return 'adds a new item to your todo list. Ex:add "help trip fix the warp core" (quote marks are required)'
		if params == "getlist":
			return 'return all the items complete and not complete in your list. Supplementary paramters: all,done|complete,pending|incomplete. Ex: getlist done'
		if params == "help":
			return "Doh."
		if params == "done" or params == "complete":
			return "mark an item as done. Ex: done 4"

		return "available commands are: add, getlist, del, complete|done, help. Type help <command> for a detailed help on that command"
	def reminder(self,params):
		targetdate = ""
		if params[1] == "remove":
			cursor = self.conn.cursor(MySQLdb.cursors.DictCursor);
			cursor.execute('select r.id FROM reminders r, todos t WHERE r.todo_id = t.id and t.pos = "%s" and t.jid="%s"' % (params[0], self.jid))
			row = cursor.fetchone()
			if row is None:
				return "That reminder doesn't exist"
			cursor.execute("delete from reminders where id = '%s'" % row["id"])
			return "removed reminder for %s" % params[0]
		c = pdc.Constants()
		p = pdt.Calendar(c)
		targetdate = p.parse(params[1])
		year = targetdate[0][0]
		month = targetdate[0][1]
		day = targetdate[0][2]
		hour = targetdate[0][3]
		minute = targetdate[0][4]
		cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)
		sql = "select id from todos where pos = '%s' and jid = '%s'" % (params[0], self.jid)
		cursor.execute(sql)
		row = cursor.fetchone()
		if row is None:
			return "That item doesnt exist"
		
		sql = "insert into reminders (todo_id, rdate) values ('%s', '%d-%d-%d %d:%02d:00')" % (row['id'], year,month,day,hour,minute)
		print 'reminder sql:'+sql
		cursor.execute(sql)
		return "reminder set for %d/%d/%d %d:%02d" % (month,day,year,hour,minute)
	def deldone(self, params):
		cursor=self.conn.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('delete from todos where jid="%s" and status="C"' % self.jid)
		return "ok"
	def parse(self, line):
		regexs = {
			self.add     : '^add\s\"(.*)\"',
			self.delete  : '^del\s([0-9]+)',
			self.getlist : '^getlist\s*(done|complete|incomplete|all|pending|reminders)*',
			self.help	 : '^help\s*(.*)',
			self.complete: '^complete\s([0-9]+)',
			self.complete: '^done\s([0-9]+)',
			self.search  : '^search\s*(.*)',
			self.reminder: '^remind\s([0-9]*)\s*(.*)',
			self.reminder: '^reminder\s([0-9]*)\s*(.*)',
			self.deldone : '^deldone.*$'
		}
		print "parsing line..."
		for cmd,regex in regexs.iteritems():
			p = re.compile(regex, re.IGNORECASE)
			if p.search(line) is not None:
				print 'Matched command:%s params: %s' % (cmd, p.search(line).groups())
				return cmd(p.search(line).groups())
		return "Invalid command. Type help, or visit http://tobo.dendiz.com for detailed command list"

if __name__ == "__main__":
	e = Engine("deniz.dizman@gmail.com")
	line = raw_input("enter command:")
	print "tobo says:"+e.parse(line)
