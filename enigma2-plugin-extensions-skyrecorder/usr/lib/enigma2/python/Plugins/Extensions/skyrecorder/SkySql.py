#-*- coding: utf-8 -*-
import re, sqlite3
from Components.config import config
from SkyMainFunctions import getPluginPath
import os

class sqlcmds:
	def __init__(self):
		self.con = None
		
	def connect(self):
		try:
			self.my_db_path = config.plugins.skyrecorder.skydb.value
		except:
			self.my_db_path = "{0}/skydb.db".format(getPluginPath())
		
		try:
			sizeb = os.path.getsize(self.my_db_path)
		except:
			sizeb = 0
		if not os.path.exists(self.my_db_path) or sizeb == 0:
			from SkyCreateDatabase import buildSkydb
			res = buildSkydb(self.my_db_path,rebuild=True,backup=False)
		
		self.con = sqlite3.connect(self.my_db_path)
		self.con.text_factory = str # we need utf-8 strings
		self.cur = self.con.cursor()
		self.cur.execute('SELECT SQLITE_VERSION()')
		data = self.cur.fetchone()
		if data:
			return True			
		else:
			return False

	def disconnect(self):
		if self.con:
			self.con.close()
		

		
##########################
#### event statements ####
##########################

	def addEvent(self,title, description, sky_id, image,id_channel, id_genre, status="False"):
		id_events = self.existEvent(title, description, sky_id, id_channel, id_genre)
		title = title.replace("'","''")
		description = description.replace("'","''")
		image = image.replace("'","''")
		if id_events:
			#go = """UPDATE events SET sky_id == '{0}' WHERE id_events == {1}""".format(sky_id,id_events)
			#self.cur.execute(go)
			#self.con.commit()
			return id_events
		
		go = """INSERT OR IGNORE INTO events
				VALUES (NULL,'{0}','{1}','{2}','{3}','{4}','{5}','{6}')""".format(title, description,sky_id,image,id_channel,id_genre,status)
		self.cur.execute(go)
		self.con.commit()
		go = "SELECT MAX(id_events) FROM events" 
		self.cur.execute(go)
		id_events = self.cur.fetchone()
		#id_events = cur.lastrowid
		if not id_events:
			return False
		return int(id_events[0])

	def existEvent(self,title, description, sky_id, id_channel, id_genre):
		title = title.replace("'","''")
		description = description.replace("'","''")
		# Sky is reusing old sky_id, so we cannot use this field in search. hopefully we are unique enough
		go = """SELECT id_events FROM events
				WHERE title LIKE '{0}'
				AND description LIKE '{1}'
				AND id_channel=={2}
				AND id_genre=={3}""".format(title, description,id_channel,id_genre)
		self.cur.execute(go)
		id_events = self.cur.fetchone()
		#print count
		if not id_events:
			return False
		return int(id_events[0])
	
	
	def addEventList(self,dayname, datum, starttime, endtime, status, id_events):
		id_eventslist = self.existEventList(datum, starttime, endtime, id_events)
		if id_eventslist:
			return id_eventslist
		
		go = "INSERT OR IGNORE INTO eventslist VALUES (NULL,'{0}','{1}','{2}','{3}','{4}','{5}')".format(dayname, datum, starttime, endtime, status, id_events)
		self.cur.execute(go)
		self.con.commit()
		go = "SELECT MAX(id_eventslist) FROM eventslist" 
		self.cur.execute(go)
		id_eventslist = self.cur.fetchone()
		#id_eventslist = cur.lastrowid
		if not id_eventslist:
			return False
		return int(id_eventslist[0])
			
			
	def existEventList(self,datum, starttime, endtime, id_events):
		go = "SELECT id_eventslist FROM eventslist WHERE datum=='{0}' AND starttime=={1} AND endtime=={2} AND id_events=={3}".format(datum, starttime, endtime, id_events)
		self.cur.execute(go)
		id_eventslist = self.cur.fetchone()
		#print count
		if not id_eventslist:
			return False
		return int(id_eventslist[0])
		
	
	def getEventDetails(self,id_events):
		go = """SELECT handlung, is_hd, is_169, is_dolby, is_dualch, highlight, live, is_last, is_3d, is_ut, is_new
				FROM eventdetails
				WHERE id_events=={0}
				ORDER BY id_eventdetails DESC LIMIT 1""".format(id_events)
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows
		
		
	def existEventDetails(self,id_events):
		go = "SELECT id_eventdetails FROM eventdetails WHERE id_events=={0}".format(id_events)
		self.cur.execute(go)
		id_eventdetails = self.cur.fetchone()
		#print count
		if not id_eventdetails:
			return False
		return int(id_eventdetails[0])
	

	def addEventDetails(self,id_events, handlung, is_hd, is_169, is_dolby, is_dualch, highlight, live, is_last, is_3d, is_ut, is_new):
		id_eventdetails = self.existEventDetails(id_events)
		if id_eventdetails:
			return id_eventdetails
		handlung = handlung.replace("'","''")
		go = """INSERT OR IGNORE INTO eventdetails
				VALUES
				(NULL,{0},'{1}','{2}','{3}','{4}','{5}','{6}','{7}','{8}','{9}','{10}','{11}')
				""".format(id_events, handlung, is_hd, is_169, is_dolby, is_dualch, highlight, live, is_last, is_3d, is_ut, is_new)
		self.cur.execute(go)
		self.con.commit()
		go = "SELECT MAX(id_eventdetails) FROM eventdetails" 
		self.cur.execute(go)
		id_eventdetails = self.cur.fetchone()
		#id_eventdetails = cur.lastrowid
		if not id_eventdetails:
			return False
		return int(id_eventdetails[0])
	
	
	def resetEventStatus(self):
		go = "UPDATE events SET status == 'False'"
		self.cur.execute(go)
		self.con.commit()
		return True
	
	
	def getEventListStatus(self,id_events, starttime):
		if not starttime:
			go = "SELECT status FROM eventslist WHERE id_events=={0}".format(id_events)
		else:
			go = "SELECT status FROM eventslist WHERE starttime=={0} AND id_events=={1}".format(starttime, id_events)
		self.cur.execute(go)
		id_eventslist = self.cur.fetchone()
		if not id_eventslist:
			return False
		return str(id_eventslist[0])
		
	
	def updateEventListStatus(self,id_events,starttime,status="False"):
		if not id_events:
			return False
		go = "SELECT status FROM eventslist WHERE id_events == {0}".format(id_events) 
		self.cur.execute(go)
		data = self.cur.fetchone()
		if not data:
			return False
		if starttime and starttime > 0:
			go = "UPDATE eventslist SET status == '{2}' WHERE id_events == {0} AND starttime == {1}".format(id_events,starttime,status)
		else:
			go = "UPDATE eventslist SET status == '{1}' WHERE id_events == {0}".format(id_events,status)
		self.cur.execute(go)
		self.con.commit()
		return True
	
	
	def readEvents(self, do_group = False, order = "DESC"):
		go = "SELECT * FROM events INNER JOIN eventslist ON eventslist.id_events = events.id_events"
		if do_group:
			go = go + " GROUP BY events.id_events"
		go = go + " ORDER BY events.title {0}".format(order)
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows
		
		
	def getEventsMain(self,order = "ASC", only_is_new=True, current_group_idx=None, min_date=None):
		go = """SELECT events.id_events, events.title, events.description,
					events.id_channel, genre.genre, genre.id_genre, events.status,channel.channel,
					events.image, events.sky_id, eventslist.starttime, eventslist.endtime,
					eventdetails.is_new, COUNT(events.id_events) AS anz
					FROM events
					INNER JOIN eventslist ON eventslist.id_events = events.id_events"""
		if min_date and min_date > 0:
			go += """ AND eventslist.starttime > {0}""".format(min_date)
		
		go += """ INNER JOIN channel ON channel.id_channel = events.id_channel AND channel.status == 'True'
				INNER JOIN genre ON genre.id_genre = events.id_genre AND genre.status == 'True'"""
						
		if only_is_new:
			go += """ INNER JOIN eventdetails ON (eventdetails.id_events = events.id_events AND eventdetails.is_new = 1)"""
		else:
			go += """ INNER JOIN eventdetails ON eventdetails.id_events = events.id_events"""
		
		if current_group_idx and current_group_idx > 0:
			go += """ INNER JOIN genregroup ON genregroup.id_genre = events.id_genre
					INNER JOIN groups ON groups.id_groups = genregroup.id_groups
					AND groups.id_groups = {0}""".format(current_group_idx)
					
		go += """ GROUP BY events.id_events ORDER BY MIN(eventslist.starttime) {0}""".format(order)
		
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows
		
		
	def getEventsMainAutoCheck(self,order = "ASC"):
		go = """SELECT events.id_events, events.title, events.description,
						events.id_channel, genre.genre, genre.id_genre, events.status,channel.channel,
						events.image, events.sky_id, eventslist.starttime, eventslist.endtime, eventdetails.is_new
						FROM events
						INNER JOIN eventslist ON eventslist.id_events = events.id_events 
						INNER JOIN channel ON channel.id_channel = events.id_channel AND channel.status == 'True'
						INNER JOIN genre ON genre.id_genre = events.id_genre AND genre.status == 'True'
						INNER JOIN eventdetails ON (eventdetails.id_events = events.id_events AND eventdetails.is_new = 1)
						WHERE events.status != 'Hidden'
					GROUP BY events.id_events
					ORDER BY MIN(eventslist.starttime) {0}""".format(order)
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows


	def getEventsTimer(self,id_events,order = "ASC", min_date=None):
		go = """SELECT eventslist.dayname,eventslist.datum, eventslist.starttime, eventslist.endtime,
						channel.channel, eventslist.status, events.title, events.description
				FROM eventslist
				INNER JOIN events ON eventslist.id_events = events.id_events"""
		if min_date and min_date > 0:
			go += """ AND eventslist.starttime > {0}""".format(min_date)
			
		go += """ INNER JOIN channel ON events.id_channel = channel.id_channel
				WHERE eventslist.id_events == {0}
				ORDER BY eventslist.starttime {1}""".format(id_events,order)
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows
	
	
	def getEventsForTimerlist(self,title, description, starttime, id_channel):
		title = title.replace("'","''")
		description = description.replace("'","''")
		go = """SELECT eventslist.id_events, events.id_genre, channel.channel
				FROM eventslist
				INNER JOIN events ON eventslist.id_events = events.id_events
				INNER JOIN channel ON events.id_channel = channel.id_channel
				WHERE events.title LIKE '{0}'
				AND events.description LIKE '{1}'
				AND eventslist.starttime == {2}
				AND events.id_channel == {3}
				GROUP BY events.id_events """.format(title, description, starttime, id_channel)
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows
	

	def deleteEventCoverByIdEvents(self,id_events):
		go = "DELETE FROM eventcover WHERE id_events=={0}".format(id_events)
		self.cur.execute(go)
		self.con.commit()
		

	def existEventCover(self,id_events):
		go = "SELECT id_eventcover FROM eventcover WHERE id_events=={0}".format(id_events)
		self.cur.execute(go)
		id_eventcover = self.cur.fetchone()
		#print count
		if not id_eventcover:
			return False
		return int(id_eventcover[0])
		
	
	def addEventCover(self,id_events, cover):
		id_eventcover = self.existEventCover(id_events)
		if id_eventcover:
			return id_eventcover
		binary = sqlite3.Binary(cover)
		self.cur.execute("INSERT OR IGNORE INTO eventcover(id_events,cover) VALUES(?,?)", (id_events,binary))
		self.con.commit()
		go = "SELECT MAX(id_eventcover) FROM eventcover" 
		self.cur.execute(go)
		id_eventcover = self.cur.fetchone()
		if not id_eventcover:
			return False
		return int(id_eventcover[0])
	
	def getEventCover(self,id_events):
		go = """SELECT cover
				FROM eventcover
				WHERE id_events=={0}
				ORDER BY id_events DESC LIMIT 1""".format(id_events)
		self.cur.execute(go)
		data = self.cur.fetchone()
		if data:
			return str(data[0])
		else:
			return False
	
	
	def deleteEvents(self, mindate):
		go = """SELECT eventslist.id_events
				FROM eventslist
				WHERE eventslist.starttime <= {0}""".format(mindate)
		self.cur.execute(go)
		rows = self.cur.fetchall()
		n = 0
		if rows:
			for id_events in rows:
				n +=1
				go = """DELETE FROM eventslist
					WHERE eventslist.id_events == {0}
					AND eventslist.starttime <= {1}""".format(id_events[0],mindate)
				self.cur.execute(go)
				self.con.commit()
				go = """SELECT COUNT(eventslist.id_events) FROM eventslist
					WHERE eventslist.id_events == {0}""".format(id_events[0])
				self.cur.execute(go)
				count = self.cur.fetchone()
				if count and int(count[0]) < 1:
					go = """DELETE FROM eventcover
						WHERE eventcover.id_events == {0}""".format(id_events[0])
					self.cur.execute(go)
					self.con.commit()
					try:
						go = """DELETE FROM events
							WHERE events.id_events == {0}""".format(id_events[0])
						self.cur.execute(go)
						self.con.commit()
					except:
						return -1
		return n
		
		
	def deleteEventById(self, id_events):
		if not id_events or id_events < 1:
			return False
		go = """DELETE FROM eventslist WHERE id_events == {0}""".format(id_events)
		self.cur.execute(go)
		self.con.commit()

		go = """DELETE FROM eventcover WHERE id_events == {0}""".format(id_events)
		self.cur.execute(go)
		self.con.commit()
		
		go = """DELETE FROM events WHERE id_events == {0}""".format(id_events)
		self.cur.execute(go)
		self.con.commit()
		
		return True


	def existEventGuide(self,title, description, id_channel):
		title = title.replace("'","''")
		description = description.replace("'","''")
		go = """SELECT id_events FROM events
				WHERE title LIKE '{0}'
				AND description LIKE '{1}'
				AND id_channel=={2}""".format(title, description,id_channel)
		self.cur.execute(go)
		id_events = self.cur.fetchone()
		#print count
		if not id_events:
			return False
		return int(id_events[0])
		
		
	def existEventGuideIsNew(self,title, description, id_channel):
		title = title.replace("'","''")
		description = description.replace("'","''")
		go = """SELECT events.id_events
				FROM events
				INNER JOIN eventdetails ON (eventdetails.id_events = events.id_events AND eventdetails.is_new = 1)
				WHERE events.title LIKE '{0}'
				AND events.description LIKE '{1}'
				AND events.id_channel=={2}""".format(title, description,id_channel)
		self.cur.execute(go)
		id_events = self.cur.fetchone()
		#print count
		if not id_events:
			return False
		return int(id_events[0])

##########################
#### genre statements ####
##########################
		
	def changeGenre(self, genrename):
		print genrename
		go = "SELECT Status FROM genre WHERE genre == '{0}'".format(genrename)
		self.cur.execute(go)
		data = self.cur.fetchone()
		print data
		if data[0] == "True":
			print "is True set False"
			go = "UPDATE genre SET status == 'False' WHERE genre LIKE '{0}'".format(genrename)
			self.cur.execute(go)
			self.con.commit()
		else:
			print "is False set True"
			go = "UPDATE genre SET status == 'True' WHERE genre LIKE '{0}'".format(genrename)
			self.cur.execute(go)
			self.con.commit()

	def checkGenre(self,genre):
		if self.existGenre(genre):
			go = "SELECT status FROM genre WHERE genre LIKE '{0}'".format(genre)
			self.cur.execute(go)
			status = self.cur.fetchone()
			self.con.commit()
			if status[0] == "True":
				return True
			else:
				return False
		else:
			return False

	def existGenre(self,genre):
		go = "SELECT COUNT(*) FROM genre WHERE genre LIKE '{0}'".format(genre)
		self.cur.execute(go)
		count = self.cur.fetchone()
		if count and int(count[0]) > 0:
			return True
		else:
			return False
			
	def getGenreFromId(self,id):
		go = "SELECT genre FROM genre WHERE id_genre == '{0}'".format(id)
		self.cur.execute(go)
		genre_name = self.cur.fetchone()
		if genre_name:
			return genre_name[0]
		else:
			return False		
			
	def getIdGenre(self,genre):
		if not genre:
			return False
		genre = genre.replace("'","''")
		go = "SELECT id_genre FROM genre WHERE genre LIKE '{0}'".format(genre)
		self.cur.execute(go)
		id_genre = self.cur.fetchone()
		if id_genre:
			return id_genre[0]
		else:
			return False
			
	def readGenre(self):
		go = "SELECT genre, status FROM genre"
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows

	def getActiveGenre(self):
		go = "SELECT id_genre FROM genre WHERE status == 'True'"
		self.cur.execute(go)
		rows = self.cur.fetchall()
		templist = []
		for row in rows:
			templist.append(row[0])
		return tuple(templist)

	def readGenreJoinGenregroup(self):
		go = """SELECT genre.genre, genre.status, genregroup.id_genregroup, genregroup.id_genre, genregroup.id_groups
				FROM genre
				INNER JOIN genregroup ON genregroup.id_genre = genre.id_genre
				"""
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows



###########################		
#### groups statements ####
###########################

	def getGroupnames(self):
		go = "SELECT groupname FROM groups"
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows

	def readGroupsShort(self):
		go = "SELECT id_groups,groupname FROM groups"
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows
		
	def readJoindGroupsShort(self, id_genregroup):
		go = """SELECT groups.id_groups, groups.groupname
				FROM groups
				INNER JOIN genregroup ON genregroup.id_genregroup = {0}
				INNER JOIN genre ON genre.id_genre = genregroup.id_genre
				""".format(id_genregroup)
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows
		
	def readGenregroup(self):
		go = "SELECT id_genregroup,id_groups,id_genre FROM genregroup"
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows

	def updateGenregroup(self,id_genregroup, id_groups, do_commit=True):
		go = """UPDATE genregroup
				SET id_groups == {1}
				WHERE id_genregroup == {0}""".format(id_genregroup, id_groups)
		self.cur.execute(go)
		if do_commit:
			self.con.commit()


	def getGenregroupByGenre(self,genre):
		if not genre:
			return False
		if genre == "" or genre == " ":
			genre = "-"
		else:
			genre = genre.replace("'","''")
		go = """SELECT groups.groupname
				FROM groups
				INNER JOIN genregroup ON genregroup.id_groups = groups.id_groups
				INNER JOIN genre ON genregroup.id_genre = genre.id_genre
				AND genre.genre == '{0}'
				""".format(genre)
		self.cur.execute(go)
		row = self.cur.fetchone()
		if row:
			return row[0]
		else:
			return False


	def getGenregroupByGenreId(self,id_genre):
		if not id_genre:
			return False
		go = """SELECT groups.groupname
				FROM groups
				INNER JOIN genregroup ON genregroup.id_groups = groups.id_groups
				INNER JOIN genre ON genregroup.id_genre = genre.id_genre
				AND genre.id_genre == {0}
				""".format(id_genre)
		self.cur.execute(go)
		row = self.cur.fetchone()
		if row:
			return row[0]
		else:
			return False

############################		
#### channel statements ####
############################

	def changeChannel(self,channel=""):
		channel = channel.replace("'","''")
		go = "SELECT status FROM channel WHERE channel == '{0}'".format(channel)
		self.cur.execute(go)
		data = self.cur.fetchone()
		print data
		if data[0] == "True":
			print "is True set False"
			go = "UPDATE channel SET status == 'False' WHERE channel LIKE '{0}'".format(channel)
			self.cur.execute(go)
			self.con.commit()
		else:
			print "is False set True"
			go = "UPDATE channel SET status == 'True' WHERE channel LIKE '{0}'".format(channel)
			self.cur.execute(go)
			self.con.commit()

	def checkChannel(self,channel=""):
		if self.existChannel(channel):
			channel = channel.replace("'","''")
			go = "SELECT status FROM channel WHERE channel LIKE '{0}'".format(channel)
			self.cur.execute(go)
			status = self.cur.fetchone()
			self.con.commit()
			if status[0] == "True":
				return True
			else:
				return False
		else:
			return False
			
	def existChannel(self,channel=""):
		channel = channel.replace("'","''")
		go = "SELECT COUNT(*) FROM channel WHERE channel LIKE '{0}'".format(channel)
		self.cur.execute(go)
		count = self.cur.fetchone()
		if count and int(count[0]) > 0:
			return True
		else:
			return False
			
	def getIdChannel(self,channel="",stb=False):
		channel = channel.replace("'","''")
		if stb:
			go = "SELECT id_channel FROM channel WHERE channel_stb LIKE '{0}'".format(channel)
		else:
			go = "SELECT id_channel FROM channel WHERE channel LIKE '{0}'".format(channel)
		self.cur.execute(go)
		id_channel = self.cur.fetchone()
		if id_channel:
			return id_channel[0]
		else:
			return False
			
	def getChannelFromChannel(self,channel="",stb=False):
		channel = channel.replace("'","''")
		if stb:
			go = "SELECT channel_stb FROM channel WHERE channel LIKE '{0}'".format(channel)
		else:
			go = "SELECT channel FROM channel WHERE channel_stb LIKE '{0}'".format(channel)
		self.cur.execute(go)
		id_channel = self.cur.fetchone()
		if id_channel:
			return id_channel[0]
		else:
			return False

	def readChannel(self):
		go = "SELECT channel,status FROM channel"
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows
	
	def getActiveChannel(self):
		go = "SELECT id_channel FROM channel WHERE status == 'True'"
		self.cur.execute(go)
		rows = self.cur.fetchall()
		templist = []
		for row in rows:
			templist.append(row[0])
		return tuple(templist)

	def getChannelIdSky(self, active=True):
		if active:
			go = "SELECT channel_id_sky FROM channel WHERE status == 'True'"
		else:
			go = "SELECT channel_id_sky FROM channel"
		self.cur.execute(go)
		rows = self.cur.fetchall()
		templist = []
		for row in rows:
			templist.append(row[0])
		return templist
	
	def readChannelAll(self):
		go = "SELECT * FROM channel"
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows
	
	def updateChannelnameSTB(self,id_channel, channel_stb):
		if not channel_stb:
			return False
		channel_stb = channel_stb.replace("'","''")
		go = "UPDATE channel SET channel_stb == '{0}' WHERE id_channel == {1}".format(channel_stb,id_channel)
		self.cur.execute(go)
		self.con.commit()
	
################################		
#### timer added statements ####
################################
	
	
	# id_added,title,description,id_channel,id_genre,begin,end,serviceref,location,recordedfile
		
	def addAdded(self,title,description,id_channel,id_genre,begin,end,serviceref,location,recordedfile):
		if not self.checkAdded(title,description,id_channel,id_genre):
			title = title.replace("'","''")
			description = description.replace("'","''")
			recordedfile = recordedfile.replace("'","''")
			go = """INSERT OR IGNORE INTO added
					(title,description,id_channel,id_genre,begin,end,serviceref,location,recordedfile)
					VALUES
					('{0}','{1}',{2},{3},{4},{5},'{6}','{7}','{8}')
					""".format(title, description, id_channel, id_genre, begin, end, serviceref, location, recordedfile)
			self.cur.execute(go)
			self.cur.fetchone()
			self.con.commit()
			return True
		else:
			return False

	def checkAdded(self,title,description,id_channel,id_genre):
		title = title.replace("'","''")
		description = description.replace("'","''")
		go = """SELECT id_added FROM added
				WHERE title LIKE '{0}' AND
				description LIKE '{1}' AND
				id_channel = {2} AND
				id_genre = {3}""".format(title,description,id_channel,id_genre)
		self.cur.execute(go)
		id_added = self.cur.fetchone()
		if id_added:
			return int(id_added[0])
		else:
			return False
			

	def checkAddedReturnEntry(self,title,description,id_channel,id_genre):
		title = title.replace("'","''")
		description = description.replace("'","''")
		go = """SELECT * FROM added
				WHERE title LIKE '{0}' AND
				description LIKE '{1}' AND
				id_channel = {2} AND
				id_genre = {3}""".format(title,description,id_channel,id_genre)
		self.cur.execute(go)
		rows = self.cur.fetchall()
		if rows:
			return rows
		else:
			return False

	
	def resetAdded(self,id_added=None):
		if id_added:
			go = "DELETE FROM added WHERE id_added == {0}".format(id_added)
		else:
			go = "DELETE FROM added"
		self.cur.execute(go)
		self.con.commit()
		go = "UPDATE eventslist SET status == 'False' WHERE status != 'Done'"
		self.cur.execute(go)
		self.con.commit()
		go = "UPDATE events SET status == 'False' WHERE status != 'Done'"
		self.cur.execute(go)
		self.con.commit()


	def removeFromAdded(self,title,description,id_channel,id_genre,hidden=False):
		title = title.replace("'","''")
		description = description.replace("'","''")
		if hidden is not True:
			go = """DELETE FROM added
					WHERE title LIKE '{0}'
					AND description LIKE '{1}'
					AND id_channel = {2}
					AND id_genre = {3}""".format(title,description,id_channel,id_genre)
		else:
			go = """DELETE FROM added
				WHERE title LIKE '{0}'
				AND description LIKE '{1}'
				AND id_channel = {2}
				AND id_genre = {3}
				AND begin == 0""".format(title,description,id_channel,id_genre)
		self.cur.execute(go)
		self.con.commit()
			
	def readAdded(self):
		go = "SELECT recordedfile FROM added"
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows
		

	def readAddedEdit(self):
		go = """SELECT id_added,title,description,id_channel,id_genre,recordedfile,begin
				FROM added
				ORDER BY begin ASC"""
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows

	def readAddedAll(self):
		go = "SELECT * FROM added"
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows


	def readAddedByGroupname(self,groupname=None):
		if not groupname:
			return
		groupname = groupname.replace("'","''")
		go = """SELECT * FROM added
				INNER JOIN genre ON genre.id_genre == added.id_genre
				INNER JOIN genregroup ON genregroup.id_genre == genre.id_genre
				INNER JOIN groups ON groups.id_groups == genregroup.id_groups"""
		if groupname.lower() == "all" or groupname.lower() == "a-z":
			go += """ ORDER BY added.title ASC"""
		else: 
			go += """ WHERE groups.groupname == '{0}' ORDER BY added.title ASC""".format(groupname)
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows


#############################	
#### skipword statements ####
#############################

	def changeSkip(self,skipword):
		if not skipword:
			return
		skipword = skipword.replace("'","''")
		go = "SELECT status FROM skip WHERE skipword == '{0}'".format(skipword) 
		self.cur.execute(go)
		data = self.cur.fetchone()
		print data
		if data[0] == "True":
			print "is True set False"
			go = "UPDATE skip SET status == 'False' WHERE skipword LIKE '{0}'".format(skipword)
			self.cur.execute(go)
			self.con.commit()
		else:
			print "is False set True"
			go = "UPDATE skip SET status == 'True' WHERE skipword LIKE '{0}'".format(skipword)
			self.cur.execute(go)
			self.con.commit()
			
	def checkSkip(self,skipword):
		if not skipword:
			return
		skipword = skipword.replace("'","''")
		go = "SELECT status FROM skip WHERE skipword LIKE '{0}'".format(skipword)
		self.cur.execute(go)
		status = self.cur.fetchone()
		self.con.commit()
		if status:
			if status[0] == "True":
				return True
			else:
				return False
		else:
			return False

	def readSkip(self):
		go = "SELECT skipword,status FROM skip WHERE status == 'True'"
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows
			
	def readSkipSelect(self):
		go = "SELECT skipword,status FROM skip"
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows
	
	def getSkipSelect(self):
		go = "SELECT skipword FROM skip WHERE status == 'True'"
		self.cur.execute(go)
		rows = self.cur.fetchall()
		templist = []
		for row in rows:
			templist.append(row[0])
		return tuple(templist)
	
	def addSkip(self,skipword, status="True"):
		if not skipword:
			return
		if not self.existSkip(skipword):
			skipword = skipword.replace("'","''")
			go="INSERT OR IGNORE INTO skip (skipword,status) VALUES ('{0}','{1}')".format(skipword, status)
			self.cur.execute(go)
			self.cur.fetchone()
			self.con.commit()
			return True
		else:
			return False
			
	def delSkip(self,skipword):
		if not skipword:
			return
		if self.existSkip(skipword):
			skipword = skipword.replace("'","''")
			go = "DELETE FROM skip WHERE skipword = '{0}'".format(skipword)
			self.cur.execute(go)
			self.cur.fetchone()
			self.con.commit()

	def existSkip(self,skipword):
		if not skipword:
			return
		skipword = skipword.replace("'","''")
		go = "SELECT COUNT (*) FROM skip WHERE skipword LIKE '{0}'".format(skipword)
		self.cur.execute(go)
		count = self.cur.fetchone()
		print count
		if count and int(count[0]) > 0:
			return True
		else:
			return False


	def setSkipStatus(self,skipword,status="False"):
		if not skipword:
			return
		skipword = skipword.replace("'","''")
		go = "UPDATE skip SET status == '{1}' WHERE skipword LIKE '{0}'".format(skipword, status)
		self.cur.execute(go)
		self.con.commit()


###########################
#### addlog statements ####
###########################

	def addLog(self,timestr,msg):
		go="INSERT OR IGNORE INTO log VALUES('{0}','{1}')".format(timestr,msg)
		self.cur.execute(go)
		#self.cur.fetchone()
		self.con.commit()

	def readLog(self):
		go = "SELECT * FROM log"
		self.cur.execute(go)
		rows = self.cur.fetchall()
		return rows



#############################
#### database statements ####
#############################
	
	def truncateDatabase(self,includeAdded=False):
		
		try:
			go = "DELETE FROM eventdetails"
			self.cur.execute(go)
			self.con.commit()
			go = "DELETE FROM eventslist"
			self.cur.execute(go)
			self.con.commit()
			go = "DELETE FROM eventcover"
			self.cur.execute(go)
			self.con.commit()
			go = "DELETE FROM events"
			self.cur.execute(go)
			self.con.commit()
			if includeAdded:
				go = "DELETE FROM added"
				self.cur.execute(go)
				self.con.commit()
		except:
			return False
		return True

# get instance	
sql = sqlcmds()
