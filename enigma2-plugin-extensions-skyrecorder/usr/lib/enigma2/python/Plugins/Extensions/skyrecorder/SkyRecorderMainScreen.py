#-*- coding: utf-8 -*-
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText
from Components.ActionMap import NumberActionMap, ActionMap
from Components.config import config
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap, MovingPixmap
from Components.AVSwitch import AVSwitch
from enigma import gFont, eTimer, ePicLoad, loadPNG, getDesktop, eListboxPythonMultiContent, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER
from Screens.Screen import Screen
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap
from twisted.web.client import downloadPage, getPage, error
from twisted.internet import defer
import urllib, re, shutil, datetime, time
from urllib import unquote
import os
import sys
# for sorted lists
from operator import itemgetter, attrgetter

# our custom classes
from SkyChannelSelect import SkyChannelSelect
from SkySkipWordsSelect import SkySkipWordsSelect
from SkyRecorderSettings import SkyRecorderSettings
from SkyGenreSelect import SkyGenreSelect
#from SkyGetTvGuide import SkyGetTvGuide
from SkyTimerRec import SkyTimerRec
from SkyTimer import SkyTimer
from SkySql import *
#from SkyMainFunctions import nonHDeventList, buildSkyChannellist, decodeHtml, getHttpHeader, getHttpHeader2, getUserAgent, getPluginPath, checkForInternet
from SkyMainFunctions import *

# TODO Archiv Screen
from SkyRecorderArchiv import SkyRecorderArchiv


class SkyRecorderMainScreen(Screen):

	def __init__(self, session):
		self.session = session
		
		self.agent = getUserAgent()
		self.headers = getHttpHeader()
		self.headers1 = getHttpHeader1()
		self.headers2 = getHttpHeader2()
		
		# set current agent to header, too
		self.headers.update({'User-Agent': self.agent})
		self.headers1.update({'User-Agent': self.agent})
		self.headers2.update({'User-Agent': self.agent})

		
		path = "%s/skins/%s/screen_main.xml" % (getPluginPath(), config.plugins.skyrecorder.anytime_skin.value)
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		
		Screen.__init__(self, session)
		
		self.pluginName = config.plugins.skyrecorder.pluginname.value
		self.contentSize = config.plugins.skyrecorder.contentsize.value
		
		self.onlyIsNew = True
		
		self.sky_chlist = buildSkyChannellist()
		
		self.current_group_idx = 0
		
		self.haveInternet = True
		if not checkForInternet():
			self.haveInternet = False
		
		
		self["actions"]  = ActionMap(["OkCancelActions", "ShortcutActions", "EPGSelectActions", "WizardActions", "ColorActions", "NumberActions", "MenuActions", "MoviePlayerActions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"red" : self.channelSelect,
			"green" : self.skipListe,
			"yellow" : self.genreListe,
			"blue"	: self.skyarchive, 
			"menu" : self.skysettings,
			"0" : self.toggleEventIgnored,
			"2" : self.toggleIsNew,
			"5" : self.refreshCover,
			"8" : self.deleteEvent,
			"9" : self.nextSort,
			"7" : self.previousSort,
			"nextService" : self.nextGroup,
			"prevService" : self.prevGroup
		}, -1)
		
		
		self['title'] = Label(self.pluginName)
		try:
			self['head'] = Label("Neuerscheinungen")
		except Exception:
			sys.exc_clear()
		self['name'] = Label("lade Sky TV-Guide ...")
		self['handlung'] = ScrollLabel("")
		self['image'] = Pixmap()
		self['image'].hide()
		
		self['hd'] = Pixmap()
		self['hd'].hide()
		
		self['169'] = Pixmap()
		self['169'].hide()
		
		self['dolby'] = Pixmap()
		self['dolby'].hide()
		
		self['dualch'] = Pixmap()
		self['dualch'].hide()
		
		self['sub'] = Pixmap()
		self['sub'].hide()
		
		self.ck = {}
		self.keyLocked = True
		
		self.read_system_timers = True

		
		self.streamMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.streamMenuList.l.setFont(0, gFont('Regular', self.contentSize))
		self.streamMenuList.l.setItemHeight(25)
		self['filmliste'] = self.streamMenuList
		
		self.last_index = 0		
		
		self['filmliste'].onSelectionChanged.append(self.loadPic)
		
		#self.onShown.append(self.getMainEventList)
		#self.onLayoutFinish.append(self.getMainEventList)
		
		self.tempTimer = eTimer()
		self.tempTimer.callback.append(self.getMainEventList)
		self.onShown.append(self.delayedGetMainEventList)
		
	
	def delayedGetMainEventList(self, infotext="lade ..."):
		self['title'].setText(infotext)
		#self['name'].setText(infotext)
		self.tempTimer.start(20, True)

	
	def getTimerlist(self):
		
		#try:
		#	default_before = int(config.recording.margin_before.value)
		#except Exception:
		#	default_before = 0
	
		#self.timerList = loadTimerList(self.sky_chlist,"/etc/enigma2/timers.xml")		
		self.timerList = SkyTimerRec.getTimersList()
		
		for t_record in self.timerList:
			if not t_record['channel']:
				continue
			res = sql.getIdChannel(t_record['channel'],stb=True)
			if not res:
				continue
			id_channel = res
			t_record['id_channel'] = id_channel
			
			starttime = int(t_record['begin'])
			starttime += config.plugins.skyrecorder.margin_before.value * 60 # in eventslist we stored the original starttime
			res = sql.getEventsForTimerlist(t_record['title'], t_record['description'], starttime, id_channel)
			if not res:
				continue
			#if not res and default_before != 0:
			#	# second check with system margin_before
			#	starttime += default_before * 60
			#	res = sql.getEventsForTimerlist(t_record['title'], t_record['description'], starttime, id_channel)
			#	if not res:
			#		continue
			for id_events, id_genre, channel in res:
				t_record['id_genre'] = id_genre
				t_record['channel'] = channel
				break
			
			if not sql.checkAdded(t_record['title'], t_record['description'], t_record['id_channel'],t_record['id_genre']):
				sql.addAdded(
							t_record['title'],
							t_record['description'],
							t_record['id_channel'],
							t_record['id_genre'],
							t_record['begin'],
							t_record['end'],
							t_record['serviceref'],
							t_record['location'],
							t_record['recordedfile'])
			# if we still have timers in system timerlist, we want to know about it			
			sql.updateEventListStatus(id_events,starttime,status="True")
		
	def getMainEventList(self):
		# events.id_events, events.title, events.description,
		# events.id_channel, genre.genre, genre.id_genre, events.status,channel.channel,
		# events.image, events.sky_id, eventslist.starttime, eventslist.endtime
		# eventdetails.is_new, anz
		
		try:
			sql.cur.execute('SELECT SQLITE_VERSION()')
		except Exception:
			sys.exc_clear()
			try:
				sql.connect()
			except Exception:
				return
		
		self.groupnames = None
		self.groupnames = []
		self.groupnames.append([0,"Alle"])
		rows = sql.readGroupsShort()
		for t_row in rows:
			row = list(t_row)
			self.groupnames.append(row)
		self.current_group = self.groupnames[self.current_group_idx][1]
		
		if self.read_system_timers:
			self.getTimerlist()
		self.read_system_timers = False
					
		filmliste = None
		filmliste = []
		channelset = None
		genreset = None
		
		self.clearFilmInfoScreen()
		skipset = sql.getSkipSelect()
		
		current_timestamp = getCurrentTimestamp()
		
		try:
			rows = sql.getEventsMain("ASC", self.onlyIsNew, self.current_group_idx, current_timestamp)
		except Exception, e:
			print "[skyrecorder] ERROR: {0}".format(e)
			sys.exc_clear()
			return
		
		if config.plugins.skyrecorder.main_list_order:
			self.sort_type = str(config.plugins.skyrecorder.main_list_order.value)
			self.sort_info = config.plugins.skyrecorder.main_list_order.getText()
			
		resultCount = len(rows)
		canskip = False
		
		# uniq sort_idx needed for correct sorting order
		sort_idx = 0
		if resultCount > 0:
			for t_row in rows:
				row = list(t_row)
				
				for skip in skipset:
					if re.match('.*?'+skip, row[1], re.I):
						print "skip word matched"
						canskip = True
						resultCount -= 1
						break
				skip = None
				if canskip:
					canskip = False
					continue
								
				# let us see if we have completed recordings. if so, we update status as "Done"
				# id_added, title, description, id_channel, id_genre, begin, end, serviceref, location, recordedfile
				addedlist_raw = sql.checkAddedReturnEntry(row[1], row[2], row[3], row[5])
				if addedlist_raw and len(addedlist_raw) != 0:
					for addedlist_raw_row in addedlist_raw:
						addedlist = list(addedlist_raw_row)
						
						if int(addedlist[6]) <= current_timestamp:
							if config.plugins.skyrecorder.margin_before and config.plugins.skyrecorder.margin_before.value:
								e_starttime = int(addedlist[5]) + config.plugins.skyrecorder.margin_before.value * 60
							else:
								e_starttime = int(addedlist[5])
							if sql.updateEventListStatus(row[0],e_starttime,"Done"):
							#if sql.updateEventListStatus(row[0],0,"Done"):
								row[6] = "Done"		
				addedlist = None
				
				# append sort index
				sort_idx += 1
				row.append(sort_idx)
				filmliste.append(row)				
			
			# apply some sortings to our list
			if self.sort_type == "channel":
				filmliste = sorted(filmliste, key=itemgetter(7,14))
			elif self.sort_type == "title":
				filmliste = sorted(filmliste, key=itemgetter(1))
			elif self.sort_type == "status":
				filmliste = sorted(filmliste, key=itemgetter(6), reverse=True)
			elif self.sort_type == "begin_desc":
				filmliste = sorted(filmliste, key=itemgetter(14), reverse=True)
			elif self.sort_type == "begin_asc":
				filmliste = sorted(filmliste, key=itemgetter(14))
			
			self.streamMenuList.setList(map(self.skyAnytimeListEntry, filmliste))
		
		if self.last_index < resultCount:
			self['filmliste'].moveToIndex(self.last_index)
		elif resultCount > 1:
			self['filmliste'].moveToIndex(resultCount -1)
		
		try:	
			#self['head'].setText("%s Neuerscheinungen" % str(resultCount))
			newnew = ""
			if self.onlyIsNew:
				newnew = " (Neu)"
			
			self['title'].setText("""{0} Einträge{1}, {2}, {3}""".format(resultCount, newnew, self.current_group, self.sort_info))
		except Exception:
			sys.exc_clear()
			
		self.keyLocked = False


	def skyAnytimeListEntry(self,entry):
		icon = None
		new = None
		if entry[6] == "True":
			icon = "/usr/lib/enigma2/python/Plugins/Extensions/skyrecorder/images/neu.png"
		elif entry[6] == "Done":
			icon = "/usr/lib/enigma2/python/Plugins/Extensions/skyrecorder/images/neu_blue.png"
		elif entry[6] == "Hidden":
			icon = "/usr/lib/enigma2/python/Plugins/Extensions/skyrecorder/images/neu_grau.png"
		elif str(entry[12]) == "1" and entry[6] == "False":
			icon = "/usr/lib/enigma2/python/Plugins/Extensions/skyrecorder/images/neu_green.png"
		#else:
		#	icon = "/usr/lib/enigma2/python/Plugins/Extensions/skyrecorder/images/not_new.png"
		if icon:
			new = LoadPixmap(icon)
		return [entry,
			(eListboxPythonMultiContent.TYPE_TEXT, 3, 0, 22, 25, 0, RT_HALIGN_RIGHT, str(entry[13])),
			(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 28, 4, 28, 17, new),
			(eListboxPythonMultiContent.TYPE_TEXT, 70, 0, 250, 25, 0, RT_HALIGN_LEFT, entry[7]),
			(eListboxPythonMultiContent.TYPE_TEXT, 320, 0, 450, 25, 0, RT_HALIGN_LEFT, entry[1]),
			(eListboxPythonMultiContent.TYPE_TEXT, 770, 0, 130, 25, 0, RT_HALIGN_LEFT, entry[4])
			]
	
	
	def dataError(self, error):
		self.clearFilmInfoScreen()
		self['name'].setText("Konnte Sky TV-Guide nicht laden.")
		self['handlung'].setText("%s" % error)
		print error		
		
	def clearFilmInfoScreen(self):
		self.streamMenuList.setList([])
		self['name'].setText("Keine neuen Sendungen gefunden")
		self['image'].hide()
		self['hd'].hide()
		self['169'].hide()
		self['dolby'].hide()
		self['dualch'].hide()
		self['sub'].hide()
		self['handlung'].setText("")
				
	def loadPic(self):
		try:
			id_events = self['filmliste'].getCurrent()[0][0]
		except Exception:
			return

		self['image'].hide()
		self['hd'].hide()
		self['169'].hide()
		self['dolby'].hide()
		self['dualch'].hide()
		self['sub'].hide()
		
		image = self['filmliste'].getCurrent()[0][8]
		sky_id = self['filmliste'].getCurrent()[0][9]
		name = self['filmliste'].getCurrent()[0][1]
		self['name'].setText(name)
		
		cover = None
		cover_file = None
		if image and image == "http://www.skygo.sky.de/bin/EPGEvent/web/event_default.png":
			cover_file = "/tmp/skyrecorder_cover_event_default.png"
		else:
			cover_file = "/tmp/skyrecorder_tempcover.png"
		
		cover = sql.getEventCover(id_events)
		if cover:
			with open(cover_file, "wb") as f:
				f.write(cover)
			self.ShowCover(cover_file)
		else:
			try:
				if self.haveInternet:
					downloadPage(image, "/tmp/skyrecorder_tempcover.png", headers=self.headers2, agent=self.agent).addCallback(self.downloadImage, "/tmp/skyrecorder_tempcover.png", id_events)
			except Exception, e:
				self.dataError(e)

		gotData = False
		if id_events:
			rows = sql.getEventDetails(id_events)
			if rows:
				# TODO: we got some new fields. What should we do with them?
				for handlung, is_hd, is_169, is_dolby, is_dualch, highlight, live, is_last, is_3d, is_ut, is_new in rows:
					gotData = True
					if handlung:
						self['handlung'].setText(handlung)
					else:
						self['handlung'].setText("Keine infos gefunden.")
					if int(is_hd) > 0:
						self['hd'].show()
					if int(is_169) > 0:
						self['169'].show()
					if int(is_dolby) > 0:
						self['dolby'].show()
					if int(is_dualch) > 0:
						self['dualch'].show()
					if int(is_ut) > 0:
						self['sub'].show()

		
	def downloadImage(self, data, imagedata, id_events):
		if id_events:
			time.sleep(0.123)
			with open(imagedata, "rb") as f:
				cover = f.read() 
				res = sql.addEventCover(id_events, cover)
		self.ShowCover(imagedata)
	
	def ShowCover(self, image_path):
		if fileExists(image_path):
			self['image'].instance.setPixmap(None)
			self.scale = AVSwitch().getFramebufferScale()
			self.picload = ePicLoad()
			size = self['image'].instance.size()
			self.picload.setPara((size.width(), size.height(), self.scale[0], self.scale[1], False, 1, "#FF000000"))
			if self.picload.startDecode(image_path, 0, 0, False) == 0:
				ptr = self.picload.getData()
				if ptr != None:
					self['image'].instance.setPixmap(ptr.__deref__())
					self['image'].show()
					del self.picload
					
	def poster_resize(self, poster_path):
		self["poster"].instance.setPixmap(None)
		self["poster"].hide()
		sc = AVSwitch().getFramebufferScale() # Maybe save during init
		self.picload = ePicLoad()
		size = self["poster"].instance.size()
		self.picload.setPara((size.width(), size.height(), sc[0], sc[1], False, 1, "#00000000")) # Background
		if self.picload.startDecode(poster_path, 0, 0, False) == 0:
			ptr = self.picload.getData()
			if ptr != None:
				self["poster"].instance.setPixmap(ptr)
				self["poster"].show()
		

	# button actions
	def nextGroup(self):
		self.current_group_idx += 1
		if self.current_group_idx > len(self.groupnames) -1:
			self.current_group_idx = 0
		self.delayedGetMainEventList()
		
	def prevGroup(self):
		self.current_group_idx -= 1
		if self.current_group_idx < 0:
			self.current_group_idx = len(self.groupnames) -1
		self.delayedGetMainEventList()	
	
	def nextSort(self):
		if not config.plugins.skyrecorder.main_list_order or self.keyLocked:
			return
		config.plugins.skyrecorder.main_list_order.handleKey(1)
		config.plugins.skyrecorder.main_list_order.save()
		self.delayedGetMainEventList()
		
	def previousSort(self):
		if not config.plugins.skyrecorder.main_list_order or self.keyLocked:
			return
		config.plugins.skyrecorder.main_list_order.handleKey(0)
		config.plugins.skyrecorder.main_list_order.save()
		self.delayedGetMainEventList()
	
	def toggleEventIgnored(self):
		if self.keyLocked:
			return
		exist = self['filmliste'].getCurrent()
		if exist == None:
			return
		id_events = self['filmliste'].getCurrent()[0][0]
		title = self['filmliste'].getCurrent()[0][1]
		desc = self['filmliste'].getCurrent()[0][2]
		id_channel = self['filmliste'].getCurrent()[0][3]
		id_genre = self['filmliste'].getCurrent()[0][5]
		self.last_index = self['filmliste'].getSelectionIndex()
		
		check_state = sql.getEventListStatus(id_events, False)
		if check_state and check_state == "Hidden": 
			sql.updateEventListStatus(id_events, None, status="False")
			# maybe we should delete this title from our skipword-list instead of disabling?
			if title != None or title == "":
				#sql.delSkip(title)
				sql.setSkipStatus(title, "False")
				
		elif check_state and check_state != "Hidden":
			if check_state == "True":
				addedlist_raw = None
				addedlist_raw = sql.checkAddedReturnEntry(title.lower(), desc.lower(), id_channel, id_genre)
				if addedlist_raw and len(addedlist_raw) != 0:
					for addedlist_raw_row in addedlist_raw:
						addedlist = list(addedlist_raw_row)
						
						entry_dict = None
						entry_dict = {}
						entry_dict['name'] = title
						entry_dict['description'] = desc
						entry_dict['timer_starttime'] = addedlist[5]
						entry_dict['channelref'] = addedlist[7]
						
						retval = SkyTimerRec.removeTimerEntry(entry_dict)
						if not retval:
							return
			sql.updateEventListStatus(id_events, None, status="Hidden")
			# append this title to our skipword-list, but mark it as disabled (-)
			if title != None or title == "":
				sql.addSkip(title, "False")
				
		self.delayedGetMainEventList()


	def deleteEvent(self):
		if self.keyLocked:
			return
		exist = self['filmliste'].getCurrent()
		if exist == None:
			return
		id_events = self['filmliste'].getCurrent()[0][0]
		title = self['filmliste'].getCurrent()[0][1]
		desc = self['filmliste'].getCurrent()[0][2]
		id_channel = self['filmliste'].getCurrent()[0][3]
		id_genre = self['filmliste'].getCurrent()[0][5]
		status = self['filmliste'].getCurrent()[0][6]
		self.last_index = self['filmliste'].getSelectionIndex()
		
		check_state = sql.getEventListStatus(id_events, False)
		if check_state and (status == "Hidden" or status == "Done"): 
			res = sql.deleteEventById(id_events)
			if res and not sql.checkAdded(title.lower(), desc.lower(), id_channel, id_genre): 
				sql.addAdded(title, desc, id_channel, id_genre, 0, 0, '-', '-', 'Hidden')
			self.delayedGetMainEventList()
			
			
	def refreshCover(self):
		if self.keyLocked:
			return
		exist = self['filmliste'].getCurrent()
		if exist == None:
			return
		id_events = self['filmliste'].getCurrent()[0][0]
		self.last_index = self['filmliste'].getSelectionIndex()
		sql.deleteEventCoverByIdEvents(id_events)
		self.delayedGetMainEventList("lade Bild neu ...")


	def toggleIsNew(self):
		if self.keyLocked:
			return
		exist = self['filmliste'].getCurrent()
		if exist == None:
			self.last_index = 0
		if self.onlyIsNew == True:
			self.onlyIsNew = False
		else:
			self.onlyIsNew = True
		self.delayedGetMainEventList()
	

	def channelSelect(self):
		self.session.openWithCallback(self.delayedGetMainEventList, SkyChannelSelect)

	def skipListe(self):
		self.session.openWithCallback(self.delayedGetMainEventList, SkySkipWordsSelect)

	def genreListe(self):
		self.session.openWithCallback(self.delayedGetMainEventList, SkyGenreSelect)

	def skysettings(self):
		self.read_system_timers = True
		self.session.openWithCallback(self.delayedGetMainEventList, SkyRecorderSettings)

	def skyarchive(self):
		self.session.openWithCallback(self.delayedGetMainEventList, SkyRecorderArchiv)

	def keyPageDown(self):
		if self.keyLocked:
			return
		self['handlung'].pageDown()
		#self.last_index = self['filmliste'].getSelectionIndex()

	def keyPageUp(self):
		if self.keyLocked:
			return
		self['handlung'].pageUp()
		#self.last_index = self['filmliste'].getSelectionIndex()

	def keyLeft(self):
		if self.keyLocked:
			return
		self['filmliste'].pageUp()
		self.last_index = self['filmliste'].getSelectionIndex()

	def keyRight(self):
		if self.keyLocked:
			return
		self['filmliste'].pageDown()
		self.last_index = self['filmliste'].getSelectionIndex()
		
	def keyUp(self):
		if self.keyLocked:
			return
		self['filmliste'].up()
		self.last_index = self['filmliste'].getSelectionIndex()

	def keyDown(self):
		if self.keyLocked:
			return
		self['filmliste'].down()
		self.last_index = self['filmliste'].getSelectionIndex()

	def keyOK(self):
		if self.keyLocked:
			return
		exist = self['filmliste'].getCurrent()
		if exist == None:
			return
		id_events = self['filmliste'].getCurrent()[0][0]
		id_channel = self['filmliste'].getCurrent()[0][3]
		id_genre = self['filmliste'].getCurrent()[0][5]
		self.last_index = self['filmliste'].getSelectionIndex()
		check_state = sql.getEventListStatus(id_events, False)
		if check_state and check_state == "Hidden":
			return
		self.session.openWithCallback(self.delayedGetMainEventList, SkyTimer, id_events, id_channel, id_genre)
	
	def keyCancel(self):
		self.close()


