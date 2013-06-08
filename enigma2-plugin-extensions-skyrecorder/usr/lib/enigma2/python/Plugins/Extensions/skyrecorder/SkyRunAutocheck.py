#-*- coding: utf-8 -*-
from Components.config import config, configfile
import urllib, re, datetime, time
import os
import sys

# for standby
import Screens.Standby
from Tools import Notifications
from Screens.MessageBox import MessageBox

# our custom classes
from SkyTimerRec import SkyTimerRec
from SkyMainFunctions import nonHDeventList, buildSkyChannellist, decodeHtml, getHttpHeader, getUserAgent, getEventAllowedRange, getDayOfTheWeek, getTimeFromTimestamp, getCurrentTimestamp, getRecordFilename
from SkySql import *


class SkyRunAutocheck():

	def __init__(self, session):

		if not config.plugins.skyrecorder.auto_recordtimer_entries:
			return

		self.session = session

		self.sky_chlist = buildSkyChannellist()

		self.ck = {}
		self.sky_log_path = "/usr/lib/enigma2/python/Plugins/Extensions/skyrecorder/sky_log"

		msg_log = "[skyrecorder] starte AutotimerCheck..."
		print msg_log
		self.addLog(msg_log)
		self.my_day_range = None

		try:
			self.my_day_range = config.plugins.skyrecorder.timerdays_allowed.value
		except Exception:
			sys.exc_clear()
			self.my_day_range = ["all"]
		
		dirname = None
		recordings_base_folder = None
		try:
			if config.plugins.skyrecorder.anytimefolder.value:
				recordings_base_folder = config.plugins.skyrecorder.anytimefolder.value
		except Exception:
			sys.exc_clear()
			recordings_base_folder = None
		
		self.pluginName = config.plugins.skyrecorder.pluginname.value
		fromtime = config.plugins.skyrecorder.fromtime.value
		totime = config.plugins.skyrecorder.totime.value
		range_allowed = None
		range_allowed = getEventAllowedRange(int(fromtime),int(totime), self.my_day_range)

		justplay = False
		if config.plugins.skyrecorder.timer_mode.value == "1":
			justplay = True

		filmliste = None
		filmliste = []

		try:
			skipset = sql.getSkipSelect()
		except Exception:
			sys.exc_clear()
			sql.connect()
			skipset = sql.getSkipSelect()
		
		maxParallelTimerLimit = 1000
		if config.plugins.skyrecorder.max_parallel_timers and config.plugins.skyrecorder.max_parallel_timers.value:
			maxParallelTimerLimit = int(config.plugins.skyrecorder.max_parallel_timers.value)
		
		
		# events.id_events, events.title, events.description, events.id_channel,
		# genre.genre, genre.id_genre, eventslist.status, channel.channel,events.image, events.sky_id
		# eventdetails.is_new
		#rows = sql.getEventsMain(channelset,genreset,order="ASC")
		
		# excecute modified sql-function which excludes hidden files
		rows = sql.getEventsMainAutoCheck(order="ASC")
		resultCount = len(rows)
		if resultCount > 0:
			for row in rows:
				filmliste.append(row)

			filmliste = sorted(filmliste, key=lambda stime: stime[7])

		canskip = False
		for event in filmliste:
			
			# only events which are marked as is_new should be added
			if int(event[12]) != 1:
				continue
				
			for skip in skipset:
				if re.match('.*?'+skip, event[1], re.I):
					print "skip word matched"
					canskip = True
					break
			if canskip:
				canskip = False
				continue

			id_events = None
			id_events = event[0]
			id_genre = None
			id_genre = event[5]
			id_channel = None
			id_channel = event[3]
			myList = None
			myList = []

			rows = sql.getEventsTimer(id_events,order="ASC")
			resultCount = len(rows)
			if resultCount < 1:
				continue

			for row in rows:
				myList.append(row)

			myList = sorted(myList, key=lambda stime: stime[2])
			
						
			if recordings_base_folder:
				if not config.plugins.skyrecorder.create_dirtree.value:
					dirname = recordings_base_folder
				else:
					# get our groupfoldername
					a_dir = sql.getGenregroupByGenreId(id_genre)
					if a_dir:
						group_dir = os.path.join(recordings_base_folder, a_dir + "/")
						if not os.path.exists(group_dir):
							try:
								os.makedirs(group_dir, mode=0777)
								dirname = group_dir
							except Exception:
								sys.exc_clear()
						else:
							dirname = group_dir
					
						
			for timerevent in myList:
				datum = timerevent[1]
				starttime = timerevent[2]
				endtime = timerevent[3]
				channel = timerevent[4]
				title = timerevent[6]
				desc = timerevent[7]
				if getCurrentTimestamp() > starttime:
					continue

				# FIXME
				hourmin = None
				hourmin = getTimeFromTimestamp(starttime)
				(std,min) = hourmin.split(':')
				event_day = getDayOfTheWeek(starttime, True)
				#self.addLog("std:" + std + " min:" + min)
				#self.addLog(str(range_allowed[0]) + " " + str(range_allowed[1]))


				if int(std) not in range_allowed[0] or str(event_day) not in range_allowed[1]:
					logtext = "[skyrecorder] skipped, day %s and hour %s is not in range_allowed" % (event_day, int(std))
					self.addLog(logtext)
					print logtext
					continue

				if sql.checkAdded(title.lower(), desc.lower(), id_channel, id_genre): 
					msg_log = "[skyrecorder] already added: %s - %s (%s)" % (title, desc, id_channel)
					print msg_log
					self.addLog(msg_log)
					break

				stb_channel = sql.getChannelFromChannel(channel,stb=True)
				channelref = self.getChannelref(stb_channel)
				if not channelref:
					break
					
				# use settings "margin_before" and "margin_after"
				# for the timers starttime and endtime adjustment
				timer_starttime = starttime - config.plugins.skyrecorder.margin_before.value * 60;
				timer_endtime = endtime + config.plugins.skyrecorder.margin_after.value * 60;
				
				# try to limit recordtimer-entries
				# reload timerlist for every broadcast event/date - neede to be up-to-date
				self.timerList = SkyTimerRec.getTimersList()
				if self.timerList and len(self.timerList) > 0 and maxParallelTimerLimit < 1000:							
					tc = 0
					for t_record in self.timerList:
						if (str(channelref) == str(t_record['serviceref'])) and maxParallelTimerLimit > 1:
							if timer_endtime > int(t_record['begin']):
								if timer_starttime < int(t_record['end']):
									tc += 1
						else:
							# 1 min buffer for events on different channels
							if (timer_endtime + 60) > int(t_record['begin']):
								if (timer_starttime - 60) < int(t_record['end']):
									tc += 1
				
					if tc >= maxParallelTimerLimit:
						continue
					
				# finally try to add record-timer
				# timer-sanitycheck is handled by system-timer itself.				
				result = SkyTimerRec.addTimer(self.session, channelref, timer_starttime, timer_endtime, title, desc, 0, justplay, 3, dirname, None, 0, None, eit=0)
				if result["result"]:

					# added by einfall
					#begin_date = time.strftime("%Y%m%d %H%M", time.localtime(starttime))
					file = getRecordFilename(title,desc,timer_starttime,stb_channel) #"%s - %s - %s.ts" % (begin_date,channel,title)

					# id_added,title,description,id_channel,id_genre,begin,end,serviceref,location,recordedfile
					if not sql.addAdded(title, desc, id_channel, id_genre, timer_starttime, timer_endtime, channelref, dirname, file): 
						logtext = "[skyrecorder] could not add %s %s %s to added table" % (title, desc, stb_channel)
						self.addLog(logtext)
						print logtext

					sql.updateEventListStatus(id_events,starttime,status="True")

					print "[skyrecorder] time config:", fromtime,totime,std
					print "[skyrecorder] added:", datum,starttime,endtime,stb_channel,title
					logtext = "Timer Added: %s %s %s %s %s" % (datum, timer_starttime, timer_endtime, stb_channel, title)
					self.addLog(logtext)
					break
				else:
					print "[skyrecorder] timer error: {0}".format(result["message"])
					self.addLog("[skyrecorder] timer error: {0}".format(result["message"]))
	
		
		# try to sleep again				
		try:
			# go on only if kill deep standby is set
			if config.plugins.skyrecorder.wakeup and config.plugins.skyrecorder.wakeup.value:
				if not Screens.Standby.inStandby and config.plugins.skyrecorder.autoupdate_database.value:
					if str(config.plugins.skyrecorder.after_update.value) == "deepstandby":
						mymsg = "{0}\nDie STB wird jetzt ausgeschaltet.".format(self.pluginName)
						self.session.openWithCallback(self.sleepWell,  MessageBox, _(mymsg), MessageBox.TYPE_YESNO, timeout=30, default=True)
					
					elif str(config.plugins.skyrecorder.after_update.value) == "standby":
						mymsg = "{0}\nDie STB geht jetzt in den Standby-Modus.".format(self.pluginName)
						self.session.openWithCallback(self.sendStandbyNotification,  MessageBox, _(mymsg), MessageBox.TYPE_YESNO, timeout=30, default=True)
		except Exception, e:
			print "[skyrecorder] {0}".format(e)
			self.addLog("[skyrecorder] timer error: {0}".format(e))
	

	def sendStandbyNotification(self, answer):
		if answer:
			Notifications.AddNotification(Screens.Standby.Standby)
	
	def sleepWell(self, answer):
		if answer:
			if not Screens.Standby.inTryQuitMainloop:
				self.session.open(
					Screens.Standby.TryQuitMainloop,
					retvalue=1,
					timeout=5,
					default_yes = True
				)


	def getChannelref(self, channel):
		for (channelname,channelref) in self.sky_chlist:
			if channelname.lower() == channel.lower():
				return channelref


	def addLog(self, text):
		# check the current file size truncate the file if size is greater than defined limit 100 KB (102400 Bytes)
		sizeb = os.path.getsize(self.sky_log_path)
		if sizeb > 102400:
			# truncate only the first 100 lines in file - delete the oldest ones
			with open(self.sky_log_path, "r+") as f:
				for x in xrange(100):
					f.readline()
					f.truncate()

		lt = time.localtime()
		datum = time.strftime("%d.%m.%Y - %H:%M:%S", lt)
		with open(self.sky_log_path , "a") as write_log:
			write_log.write('"%s - %s"\n' % (datum,text))

