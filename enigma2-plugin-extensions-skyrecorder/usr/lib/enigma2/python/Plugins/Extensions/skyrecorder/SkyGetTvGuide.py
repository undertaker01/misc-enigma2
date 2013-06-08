#-*- coding: utf-8 -*-
from Components.config import config, configfile
from enigma import eTimer
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
from twisted.web.client import downloadPage, getPage, error
from twisted.internet import defer
import urllib, re, datetime, time
import os
import sys

# new
import json
#import urllib2

# our custom classes
from SkyRunAutocheck import SkyRunAutocheck
from SkyMainFunctions import nonHDeventList, buildSkyChannellist, decodeHtml, getHttpHeader, getHttpHeader1, getUserAgent, getHttpHeader2, getEventAllowedRange, getDayOfTheWeek, getDateFromTimestamp, getCurrentTimestamp, getHttpHeaderJSON, checkForInternet, setWecker
from SkySql import *


class SkyGetTvGuide():

	def __init__(self, session, oneShot = False):

		# singleton class - needed to call it at sessionstart
		SkyGetTvGuide.instance = self

		self.session = session
		self.oneShot = oneShot
		
		self.IS_RUNNING = False
		
		self.nonHDeventList = nonHDeventList()
		self.sky_chlist = buildSkyChannellist()
		self.agent = getUserAgent()
		self.headers = getHttpHeader()
		self.headersJSON = getHttpHeaderJSON()
		self.headers1 = getHttpHeader1()
		
		# update current agent for the header, too
		self.headers.update({'User-Agent': self.agent})
		self.headers1.update({'User-Agent': self.agent})
		self.headersJSON.update({'User-Agent': self.agent})
		
		self.pluginName = config.plugins.skyrecorder.pluginname.value
		
		self.ck = {}
		self.sky_log_path = "/usr/lib/enigma2/python/Plugins/Extensions/skyrecorder/sky_log"

		if self.oneShot and config.plugins.skyrecorder.autoupdate_database.value:
		
			# do we really need a new update right now?
			checktime = getCurrentTimestamp()
			nextcheck = checktime
			lastcheck = checktime
			try:
				lastcheck = int(config.plugins.skyrecorder.lastchecked.value)
				nextcheck = int(config.plugins.skyrecorder.next_update.value)
			except Exception:
				sys.exc_clear()
			if ((checktime + 300) >= nextcheck) and (lastcheck < nextcheck): # 5 minutes buffer should be ok, because the STB is starting to fast, sometimes
				print "[skyrecorder] timer AutotimerCheck gesetzt"
				
				# be sure we got a new timestamp, even something went wrong
				config.plugins.skyrecorder.lastchecked.value = checktime
				config.plugins.skyrecorder.lastchecked.save()
				# set new wecker for our timer
				if config.plugins.skyrecorder.database_update_time and config.plugins.skyrecorder.database_update_time.value:
					alarm = setWecker(config.plugins.skyrecorder.database_update_time.value, True) # be sure we shift one day
				else:
					alarm = setWecker([6,0], True) # be sure we shift one day
				config.plugins.skyrecorder.next_update.value = alarm
				config.plugins.skyrecorder.next_update.save()
				configfile.save()
				
				# let us start it right now. needed for wakMeUp function
				self.tempTimer = None
				self.tempTimer = eTimer()
				self.tempTimer.callback.append(self.start(self.oneShot))
				self.tempTimer.start(5000, True) # give us some time to breath, before we start
				
		# set the timer for the next update now
		if config.plugins.skyrecorder.autoupdate_database.value:
			self.refreshTimer = None
			self.refreshTimer = eTimer()
			self.refreshTimer.callback.append(self.start)
			if config.plugins.skyrecorder.next_update and config.plugins.skyrecorder.lastchecked:
				interval = int(config.plugins.skyrecorder.next_update.value) - getCurrentTimestamp()
				if interval > 60 and interval <= 5184000: # 60 seconds buffer, but lower or equal than 1 day
					#self.timerinterval = interval * 1000 # milliseconds
					#self.refreshTimer.start(self.timerinterval)
					self.timerinterval = interval
					self.refreshTimer.startLongTimer(self.timerinterval)
			
	def start(self,oneShot=False):
		self.oneShot = oneShot
		
		if not checkForInternet():
			return
		
		# update refresh timerinterval now
		if config.plugins.skyrecorder.autoupdate_database.value:
			try:
				if self.refreshTimer:
					if config.plugins.skyrecorder.database_update_time and config.plugins.skyrecorder.database_update_time.value:
						alarm = setWecker(config.plugins.skyrecorder.database_update_time.value, True) # be sure we shift one day
					else:
						alarm = setWecker([6,0], True) # be sure we shift one day
					config.plugins.skyrecorder.next_update.value = alarm
					config.plugins.skyrecorder.next_update.save()
					configfile.save()
					
					interval = int(config.plugins.skyrecorder.next_update.value) - getCurrentTimestamp()
					self.refreshTimer.stop()
					self.refreshTimer.startLongTimer(interval)
			except Exception:
				sys.exc_clear()
		
		
		if self.oneShot or config.plugins.skyrecorder.autoupdate_database.value:
			msg_log = "[skyrecorder] aktualisiere Datenbank..."
			print msg_log
			self.addLog(msg_log)

			try:
				sql.cur.execute('SELECT SQLITE_VERSION()')
			except Exception:
				sys.exc_clear()
				try:
					sql.connect()
				except Exception:
					self.IS_RUNNING = False
					return
			
			# first clean up old files
			msg_log = "[skyrecorder] entferne alte Eintraege..."
			print msg_log
			self.addLog(msg_log)
			n = sql.deleteEvents(getCurrentTimestamp())
			if n == 1:
				msg_log = "[skyrecorder] {0} Eintrag geloescht".format(n)
			else:
				msg_log = "[skyrecorder] {0} Eintraege geloescht".format(n)
			print msg_log
			self.addLog(msg_log)
			
			self.IS_RUNNING = True
			
			try:
				sql.cur.execute('SELECT SQLITE_VERSION()')
			except Exception:
				sys.exc_clear()
				try:
					sql.connect()
				except Exception:
					self.IS_RUNNING = False
					return
			
			self.station_id = -1
			self.last_station_idx = 0
			self.SkyStations = self.getSkyStations()
			self.maxStationLoop = len(self.SkyStations) - 1
			# start here
			try:
				self.getCookie()
			except Exception, e:
				msg_log = "ERROR: {0}".format(e)
				print msg_log
				self.addLog(msg_log)


	def getCookie(self, data=None):
		#url = "http://www.skygo.sky.de/index.html"
		url = "http://www.skygo.sky.de/skyguide"
		msg_log = "get page: '{0}'".format(url)
		print msg_log
		self.addLog(msg_log)
		getPage(url, headers=self.headers1, agent=self.agent, timeout=30, cookies=self.ck).addCallback(self.getSkyGuidePages).addErrback(self.dataError)


	def getSkyGuidePages(self,data=None):
		msg_log = "building urls"
		print msg_log
		self.addLog(msg_log)
		
		# settimestamp to preskip outdated events
		# later we will check again with time now()
		self.check_time = getCurrentTimestamp() + 900 #assume our check could takes 15 min
		
		self.is_done = False
		self.pages = None
		self.pages = []
		self.SKY_CHANNEL_LIST = "http://www.skygo.sky.de/epgd/web/channelList"
		self.SKY_GO_BASE = "http://www.skygo.sky.de"
		self.SEARCH_BASE = "http://www.skygo.sky.de/epgd/web/eventList"
		self.SEARCH_DAY = "06.03.2013" # just en example, real day(s) is set below
		
		# We want active channles only, or the full list?
		if config.plugins.skyrecorder.only_active_channels and config.plugins.skyrecorder.only_active_channels.value:
			channelid_list_sky = sql.getChannelIdSky(True)
			self.SEARCH_CHANNEL_IDS = ','.join(str(i) for i in channelid_list_sky)
		else:
			channelid_list_sky = sql.getChannelIdSky(False)
			self.SEARCH_CHANNEL_IDS = ','.join(str(i) for i in channelid_list_sky)
		
		if not self.SEARCH_CHANNEL_IDS or len(self.SEARCH_CHANNEL_IDS) < 1:
			self.IS_RUNNING = False
			self.checkDone("keine Sender aktiviert", set_stamp = True)
			return
		
		# build day list - we want to scan n-days at once
		self.guide_days_to_search = []
		future_days = 2 # means 1 day
		if config.plugins.skyrecorder.guide_days_to_scan and config.plugins.skyrecorder.guide_days_to_scan.value:
			future_days = int(config.plugins.skyrecorder.guide_days_to_scan.value)
			future_days += 1 # because of range n -1
		
		# include day yesterday in list, but only if we are looking for new broadcasts
		if config.plugins.skyrecorder.only_new_events and config.plugins.skyrecorder.only_new_events.value:
			self.guide_days_to_search.append((datetime.date.today() - datetime.timedelta(days=1)).strftime("%d.%m.%Y"))
		# include day today in list 
		self.guide_days_to_search.append(datetime.date.today().strftime("%d.%m.%Y"))
		
		for delta_day in range(1,future_days):
			self.guide_days_to_search.append((datetime.date.today() + datetime.timedelta(days=delta_day)).strftime("%d.%m.%Y"))
		
		maxpage = None
		self.maxpage = len(self.guide_days_to_search)
		self.cur_pagenr = 0
		
		# go
		self.startGuideDownload()
		
		
	def startGuideDownload(self):
		if self.cur_pagenr >= self.maxpage:
			try:
				del(self.tv_guide_list)
			except Exception:
				sys.exc_clear()
			self.IS_RUNNING = False
			self.checkDone("Datenbank aktualisiert", set_stamp = True)
		else:
			self.tv_guide_list = None
			self.tv_guide_list = []
			
			a_day = self.guide_days_to_search[self.cur_pagenr]
			self.cur_pagenr += 1
			
			my_url_str = self.SEARCH_BASE + "/" + str(a_day) + "/" + self.SEARCH_CHANNEL_IDS + "/"
			msg_log = "[skyrecorder] base guide url: {0}".format(my_url_str)
			print msg_log
			self.addLog(msg_log)
			
			urls = None
			urls = []
			urls.append(my_url_str)
			
			ds = defer.DeferredSemaphore(tokens=1)
			downloads = [ds.run(self.guideDataDownload,url).addCallback(self.guideDataGo).addErrback(self.dataError) for url in urls]
			finished = defer.DeferredList(downloads).addErrback(self.dataError)


	def guideDataDownload(self, url):
		return getPage(url, contextFactory=None, headers=self.headersJSON, agent=self.agent, timeout=30, cookies=self.ck)

	def guideDataGo(self, data):
		# wait a second
		time.sleep(0.3)
		self.guideData(data)
		#tempTimer = None
		#tempTimer = eTimer()
		#tempTimer.callback.append(self.guideData(data))
		#tempTimer.start(1000, True)
		

	def guideData(self, data):
		
		#data = decodeHtml(data).encode('utf-8')
		info = json.loads(data)
		if not info:
			msg_log = "ERROR: could not get TV-Guide"
			print msg_log
			self.addLog(msg_log)
			self.IS_RUNNING = False
			return
		msg_log = "[skyrecorder] Daten erhalten"
		print msg_log
		self.addLog(msg_log)
		
		# debug me
		#with open("/tmp/guide_data_base.txt" , "w") as f:
		#	f.write(str(info))
		
		msg_log = "[skyrecorder] lade Tag {0} von {1}".format(self.cur_pagenr, self.maxpage)
		print msg_log
		self.addLog(msg_log)
		
		self.cur_channels = None
		self.cur_channels = 0
		self.max_channels = None
		self.max_channels = len(info)
		
		for channel_id in info:
			self.cur_channels += 1
			
			# try to break, if we want so
			if self.IS_RUNNING == False:
				return
			
			msg_log = "[skyrecorder] lade Sender {0} von {1}".format(self.cur_channels, self.max_channels)
			print msg_log
			self.addLog(msg_log)
		
			eventnumber = 0
			maxevents = len(info[channel_id])
			if maxevents == 0:
				continue 
			
			id_channel = None
			channel = None
			channel = self.SkyStations[int(channel_id)]
			if not channel or channel == "":
				continue
			id_channel = sql.getIdChannel(channel,stb=False)
			if not id_channel:
				msg_log = "[skyrecorder] channel not found: {0}".format(channel)
				print msg_log
				self.addLog(msg_log)
				continue
			msg_log = "[skyrecorder] trying channel: {0}".format(channel)
			print msg_log
			self.addLog(msg_log)
			
			if maxevents > 1:
				maxevents = maxevents-1
			for n in range(0, maxevents):
				eventnumber += 1
				
				msg_log = "[skyrecorder] lade Sendung {0} von {1}".format(eventnumber, maxevents)
				print msg_log
				self.addLog(msg_log)
				
				my_db_dict = None
				my_db_dict = {}
				
				my_db_dict.update({"id_channel":id_channel})
				
				title = info[channel_id][n]["title"] or ""
				if title == "":
					continue
				title = str(decodeHtml(str(title)))
				my_db_dict.update({"title":title})
				
				description = info[channel_id][n]["subtitle"] or ""
				description = str(decodeHtml(str(description)))
				my_db_dict.update({"description":description})
				
				is_new = info[channel_id][n]["isNew"] or 0
				if config.plugins.skyrecorder.only_new_events and config.plugins.skyrecorder.only_new_events.value:
					if int(is_new) == 0:
						# second check, because only the first broadcast termin isNew.
						# But what, if we want the others as well?
						if not self.tv_guide_list or len(self.tv_guide_list) < 1:
							check = None
						else:
							check = next((item for item in self.tv_guide_list if item["id_channel"] == id_channel and item["title"] == title and item["description"] == description), None)
						if not check:
							# not in this day dict, but mabye in our database?
							if not sql.existEventGuideIsNew(title, description, id_channel):
								continue
						# we got an item in our list of dicts - remark the current event as new
						is_new = 1
				my_db_dict.update({"is_new":is_new})
				
				id_genre = None
				if description and description != "":
					id_genre = sql.getIdGenre(description)
				if not id_genre:
					id_genre = 49 # 49 = - (Sonstige)
				my_db_dict.update({"id_genre":id_genre})
				
				datum = info[channel_id][n]["startDate"] #startDate = 06.03.2013
				datum = str(datum)
				my_db_dict.update({"datum":datum})
				#endDate = 06.03.2013
				
				live = info[channel_id][n]["live"] or 0
				my_db_dict.update({"live":live})
				#length = 115
				
				highlight = info[channel_id][n]["highlight"] or 0
				my_db_dict.update({"highlight":highlight})
				
				starttime = info[channel_id][n]["startTime"]
				starttime = str(starttime)
				my_db_dict.update({"starttime":starttime})
				
				
				endtime = info[channel_id][n]["endTime"]
				endtime = str(endtime)
				my_db_dict.update({"endtime":endtime})
				
				# check if we can skip this broadcast date
				tstamp_start = self.unixtime(datum, starttime)
				tstamp_end = self.unixtime(datum, endtime)
				skytime = self.skyTimeStamp(starttime, tstamp_start, tstamp_end)
				
				# we will check this later
				#if self.check_time > skytime[0]:
				#	continue
				
				sky_id = info[channel_id][n]["id"] or "0"
				sky_id = str(sky_id)
				my_db_dict.update({"sky_id":sky_id})
				
				if not sky_id or sky_id == "0":
					self.addLog("no sky id found")
					continue
				my_url = "http://www.skygo.sky.de/epgd/web/eventDetail/" + sky_id + "/" + str(channel_id) + "/"
				my_db_dict.update({"details_url":my_url})
				
				# update our guide list
				self.tv_guide_list.append(my_db_dict)
				
				try:
					del(my_db_dict)
				except Exception:
					sys.exc_clear()
		
		# now get the event details
		if self.tv_guide_list and len(self.tv_guide_list) != 0:
			self.getGuideDetails()
		else:
			self.startGuideDownload()
		
	def getGuideDetails(self):
		urls = None
		urls = []
		idx = 0
		max_idx = len(self.tv_guide_list) - 1
		for entry in self.tv_guide_list:
			urls.append((idx, entry["details_url"]))
			idx += 1
		ds2 = None
		ds2 = defer.DeferredSemaphore(tokens=1)
		downloads = [ds2.run(self.guideDetailsDownload, url).addCallback(self.guideDataDetails, idx, max_idx, url).addErrback(self.dataError) for idx,url in urls]
		finished = defer.DeferredList(downloads).addErrback(self.dataError)
			
	
	def guideDetailsDownload(self, url):
		return getPage(url, contextFactory=None, headers=self.headersJSON, agent=self.agent, timeout=30, cookies=self.ck)
			
	def guideDataDetails(self, data, idx, max_idx, url):
	
		# try to break, if we have to
		if self.IS_RUNNING == False:
			return
				
		if data:
			# a robot does not sleep, but we do, sometimes
			if not idx % 3:
				time.sleep(0.3)
			#time.sleep(0.1)
			
			msg_log = "[skyrecorder] get url {0} for idx {1}/{2}".format(url, idx + 1, max_idx + 1)
			print msg_log
			self.addLog(msg_log)
			
			my_db_dict = None
			my_db_dict = {}
			details = None
			#data = decodeHtml(data).encode('utf-8')
			details = json.loads(data)
			
			handlung = details['detailTxt'] or ""
			handlung = str(decodeHtml(str(handlung)))
			my_db_dict.update({"handlung":handlung})
			
			image = details['imageUrl'] or "/bin/EPGEvent/web/event_default.png"
			image = self.SKY_GO_BASE + str(image)
			my_db_dict.update({"image":image})
			
			# get the special infos, such as id_hd or is serie
			is_hd = details['techIcons']['hd'] or 0
			my_db_dict.update({"is_hd":is_hd})
			
			is_169 = 1 # no field: details['techIcons']['hd']
			my_db_dict.update({"is_169":is_169})
			
			is_dolby = details['techIcons']['sound'] or 0
			my_db_dict.update({"is_dolby":is_dolby})
			
			is_dualch = details['techIcons']['multiLang'] or 0
			my_db_dict.update({"is_dualch":is_dualch})
			
			is_serie = details['techIcons']['serie'] or 0
			my_db_dict.update({"is_serie":is_serie})
			
			if int(is_serie) == 1 and int(self.tv_guide_list[idx]["id_genre"]) == 49:
				self.tv_guide_list[idx].update({"id_genre":2})
			
			is_ut = details['techIcons']['ut'] or 0
			my_db_dict.update({"is_ut":is_ut})
			
			is_last = details['techIcons']['lastChance'] or 0
			my_db_dict.update({"is_last":is_last})
			
			is_3d = details['techIcons']['v3d'] or 0
			my_db_dict.update({"is_3d":is_3d})
			
			self.tv_guide_list[idx].update(my_db_dict)
			
			try:
				del(my_db_dict)
			except Exception:
				sys.exc_clear()
			
			# we are done? start database update for this entry
			self.addToDatabase(self.tv_guide_list[idx], idx, max_idx)
		
		# got this day, see if we want more
		if idx == max_idx:
			time.sleep(1)
			# debug me
			#with open("/tmp/tv_guide_list.txt" , "w") as f:
			#	for e in self.tv_guide_list:
			#		f.write(repr(e) + "\n")
			#self.callDatabaseUpdate()
			
			try:
				del(self.tv_guide_list)
			except Exception:
				sys.exc_clear()
			
			if self.cur_pagenr < self.maxpage:
				self.startGuideDownload()
			else:
				self.IS_RUNNING = False
				self.checkDone("Datenbank aktualisiert", set_stamp = True)
		
	# if want to update database after we got the whole guide data - it nor recommend
	def callDatabaseUpdate(self):
		idx = 0
		max_idx = len(self.tv_guide_list) - 1
		for entry in self.tv_guide_list:
			self.addToDatabase(entry, idx, max_idx)
			idx += 1
		self.IS_RUNNING = False
		self.checkDone("Datenbank aktualisiert", set_stamp = True)
	
		
	def addToDatabase(self, entry, idx, max_idx):
		status = "False" # defaults to False, to indicate its unadded in recordtimer
		id_events = None
		try:
			sql.cur.execute('SELECT SQLITE_VERSION()')
		except Exception:
			sys.exc_clear()
			try:
				sql.connect()
			except Exception:
				return
	
		msg_log = "[skyrecorder] update database entry idx {0}/{1}".format(idx + 1, max_idx + 1)
		print msg_log
		self.addLog(msg_log)
		
		try:
			id_events = sql.addEvent(entry["title"], entry["description"], entry["sky_id"],entry["image"], entry["id_channel"], entry["id_genre"])
		except Exception, e:
			self.addLog(e)
		
		if not id_events:
			print "Fehler: addEvent"
			self.addLog("Fehler: addEvent")
		else:
			pass
		
		# if the starttime is in the past, continue to then next event
		tstamp_start = self.unixtime(entry["datum"], entry["starttime"])
		tstamp_end = self.unixtime(entry["datum"], entry["endtime"])
		skytime = self.skyTimeStamp(entry["starttime"], tstamp_start, tstamp_end)
		if getCurrentTimestamp() > skytime[0] and entry["is_new"] != 1: # need to add outdated is_new events to get newer ones later
			self.addLog("[skyrecorder] ignored entry idx {0}/{1}, event is outdated".format(idx + 1, max_idx + 1))
			
		elif sql.checkAdded(entry["title"], entry["description"], entry["id_channel"], entry["id_genre"]):
			# let us ignore finished recordnigs - we do not want new braodcast dates fot those events
			self.addLog("[skyrecorder] ignored entry idx {0}/{1}, event is already in table added".format(idx + 1, max_idx + 1))
		
		else:
			datum = None
			datum = getDateFromTimestamp(skytime[0])
			
			dayname = None
			dayname = getDayOfTheWeek(skytime[0], False)
			
			id_eventslist = None
			id_eventdetails = None
			try:
				id_eventslist = 0
				id_eventslist = sql.addEventList(dayname, datum, skytime[0], skytime[1], status, id_events)
			except Exception:
				return
			
			if not id_eventslist:
				print "Fehler: addEventList"
				self.addLog("Fehler: addEventList")
			else:
				pass
			
			if id_events:
				try:
					id_eventdetails = 0
					id_eventdetails = sql.addEventDetails(id_events, entry["handlung"], entry["is_hd"], entry["is_169"], entry["is_dolby"], entry["is_dualch"], entry["highlight"], entry["live"], entry["is_last"], entry["is_3d"], entry["is_ut"], entry["is_new"])
				except Exception:
					sys.exc_clear()
			
			msg = "[skyrecorder] done: id_events {0}, id_eventslist {1}, id_eventdetails {2}".format(id_events, id_eventslist, id_eventdetails)
			print msg
			self.addLog(msg)


	def checkDone(self, msg_log="", set_stamp = True):
		# we are done
		# store our latest update timestamp for the wakeMeUp function
		if set_stamp:
			config.plugins.skyrecorder.lastchecked.value = getCurrentTimestamp()
			config.plugins.skyrecorder.lastchecked.save()
			configfile.save()
			
			# delete outdated entries we needed for events which were tagged "is_new" in the past
			n = sql.deleteEvents(getCurrentTimestamp())
			if n == 1:
				msg = "[skyrecorder] {0} Eintrag geloescht".format(n)
			else:
				msg = "[skyrecorder] {0} Eintraege geloescht".format(n)
			print msg
			self.addLog(msg)
			
		print msg_log
		self.addLog(msg_log)
		
		# if we want automatic recordtimerentries, we start here
		if config.plugins.skyrecorder.auto_recordtimer_entries and config.plugins.skyrecorder.auto_recordtimer_entries.value:
			time.sleep(1)
			SkyRunAutocheck(self.session)	


	def dataError(self, error):
		print error
		self.addLog(error)
		self.IS_RUNNING = False
		return


	def unixtime(self, datum, uhrzeit):
		(std,min) = uhrzeit.split(':')
		(day,month,year) = datum.split('.')
		#year = "20%s" % year
		print year, month, day, std, min
		time_date = datetime.datetime(int(year), int(month), int(day), int(std), int(min))
		return int(time.mktime(time_date.timetuple()))


	def skyTimeStamp(self, uhrzeit, startstamp, endstamp):
		(std,min) = uhrzeit.split(':')
		# fix endtime is in the past
		if endstamp < startstamp:
			endstamp += (3600 * 24)
		# get duration	
		#stampdiff = endstamp - startstamp
		# build real start and end timestamps
		#if int(std) < 6 and int(std) >= 0:
		#	startstamp += (3600 * 24)
		#	endstamp = startstamp + stampdiff
		return [startstamp, endstamp]
		

	# fix sky-guide-time, cause skydays starting at 06:00
	#def skyTimeStamp(self, uhrzeit, startstamp, endstamp):
	#	(std,min) = uhrzeit.split(':')
	#	# fix endtime is in the past
	#	if endstamp < startstamp:
	#		endstamp += (3600 * 24)
	#	# get duration	
	#	stampdiff = endstamp - startstamp
	#	# build real start and end timestamps
	#	if int(std) < 6 and int(std) >= 0:
	#		startstamp += (3600 * 24)
	#		endstamp = startstamp + stampdiff
	#	return [startstamp, endstamp]


	def addLog(self, text):
		if len(text) < 1:
			return
		# check the current file size truncate the file if size is greater than defined limit 200 KB (204800 Bytes)
		sizeb = os.path.getsize(self.sky_log_path)
		if sizeb > 204800:
			# truncate only the first 100 lines in file - delete the oldest ones
			with open(self.sky_log_path, "r+") as f:
				for x in xrange(100):
					f.readline()
					f.truncate()

		lt = time.localtime()
		datum = time.strftime("%d.%m.%Y - %H:%M:%S", lt)
		with open(self.sky_log_path , "a") as write_log:
			write_log.write('"%s - %s"\n' % (datum,text))


	def buildSkyChannelList(self,sky_channels):
		my_channel_dict = None
		my_channel_dict = {}
		for channel in sky_channels["channelList"]:
			my_channel_dict.update({int(channel["id"]):str(channel["name"])})
		return my_channel_dict 
		
	
	# TODO: needs to replaced by database call
	def getSkyStations(self):
		sky_stationIds= {
			1: 'Sky Krimi', 2: 'Sky Atlantic HD', 3: 'FOX Serie', 4: 'FOX HD', 5: 'TNT Serie',
			6: 'TNT Serie HD', 7: 'RTL Crime', 8: 'Syfy', 9: '13th Street', 10: 'RTL Living',
			11: 'RTL Passion', 12: 'AXN Action', 13: 'AXN HD', 14: 'ANIMAX', 15: 'Sat.1 Emotions',
			16: 'Romance TV', 17: 'Sky Sport News HD', 18: 'Sky Sport HD 1', 19: 'Sky Sport HD 2',
			20: 'Sky Sport HD Extra', 21: 'Sky Sport News', 22: 'Sky Bundesliga', 23: 'Sky Bundesliga 1',
			24: 'Sky Bundesliga 2', 25: 'Sky Bundesliga 3', 26: 'Sky Bundesliga 4', 27: 'Sky Bundesliga 5',
			28: 'Sky Bundesliga 6', 29: 'Sky Bundesliga 7', 30: 'Sky Bundesliga 8', 31: 'Sky Bundesliga 9',
			32: 'Sky Bundesliga 10', 33: 'Sky Bundesliga 11', 34: 'Sky Sport 1', 35: 'Sky Sport 2',
			36: 'Sky Sport 3', 37: 'Sky Sport 4', 38: 'Sky Sport 5', 39: 'Sky Sport 6', 40: 'Sky Sport 7',
			41: 'Sky Sport 8', 42: 'Sky Sport 9', 43: 'Sky Sport 10', 44: 'Sky Sport 11',
			45: 'Sky Sport 12', 46: 'Sky Sport 13', 47: 'Sky Sport Austria', 48: 'ESPN America (S)',
			49: 'ESPN America HD', 50: 'EuroSport 2 Deutschland', 51: 'Eurosport HD', 52: 'motorvision',
			53: 'Sport1+ HD', 54: 'Sky 3D', 55: 'Sky Cinema', 56: 'Sky Cinema HD', 57: 'Sky Cinema +1',
			58: 'Sky Cinema +24', 59: 'Sky Action', 60: 'Sky Action HD', 61: 'Sky Comedy', 62: 'Sky Emotion',
			63: 'Sky Nostalgie', 64: 'Sky Hits', 65: 'Sky Hits HD', 66: 'Disney Cinemagic',
			67: 'Disney Cinemagic HD', 68: 'MGM', 69: 'TNT Film', 70: 'Kinowelt TV', 71: 'kabel eins classics',
			72: 'Heimatkanal', 73: 'Beate-Uhse.TV', 80: 'National Geographic', 81: 'National Geographic HD',
			82: 'Discovery Channel', 83: 'Discovery Channel HD', 84: 'Spiegel Geschichte', 85: 'History Channel',
			86: 'History Channel HD', 87: 'National Geopgraphic Wild', 88: 'National Geopgraphic Wild HD',
			89: 'Biography Channel', 90: 'Disney Channel HD', 91: 'Disney Channel', 92: 'Disney Junior',
			93: 'Disney XD', 94: 'Boomerang', 95: 'Cartoon Network (S)', 96: 'Junior', 97: 'Nicktoons (S)',
			98: 'Goldstar TV', 99: 'Classica', 100: 'MTV Germany', 101: 'MTV Live HD', 102: 'Sky Select 1',
			103: 'Sky Select 2', 104: 'Sky Select 3', 105: 'Sky Select 4', 106: 'Sky Select 5',
			107: 'Sky Select 6', 108: 'Sky Select 7', 109: 'Sky Select 8', 110: 'Sky Select 9',
			111: 'Sky Select Event A', 112: 'Sky Select Event B', 113: 'Sky Select HD', 114: 'sportdigital',
			115: 'Syfy HD', 116: '13th Street HD'
			}
		
		return sky_stationIds





