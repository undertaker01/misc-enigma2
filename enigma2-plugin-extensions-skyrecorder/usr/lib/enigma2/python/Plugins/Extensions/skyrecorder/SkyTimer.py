#-*- coding: utf-8 -*-
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
from enigma import gFont, eListboxPythonMultiContent, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER
from Components.ActionMap import NumberActionMap, ActionMap
from Components.MenuList import MenuList
from Components.Label import Label
from Tools.LoadPixmap import LoadPixmap
from Components.Pixmap import Pixmap, MovingPixmap
from twisted.web.client import getPage, error
from twisted.internet import defer
from Components.config import config
import re, datetime, time
import os
import sys

# our custom classes
from SkyTimerRec import SkyTimerRec
from SkySql import *
from SkyMainFunctions import nonHDeventList, buildSkyChannellist, getHttpHeader, getHttpHeader2, getUserAgent, getPluginPath, getDayOfTheWeek, getTimeFromTimestamp, getRecordFilename, getCurrentTimestamp


class SkyTimer(Screen):
		
	def __init__(self, session, id_events, id_channel, id_genre):
		self.session = session

		path = "%s/skins/%s/screen_timer_select.xml" % (getPluginPath(), config.plugins.skyrecorder.anytime_skin.value)
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
			
		Screen.__init__(self, session)
		
		self.id_events = str(id_events)
		self.id_channel = id_channel
		self.id_genre = id_genre
		
		self.nonHDeventList = nonHDeventList()
		self.sky_chlist = buildSkyChannellist()
		
		self.pluginName = config.plugins.skyrecorder.pluginname.value
		self.contentSize = config.plugins.skyrecorder.contentsize.value
				
		
		self["actions"]  = ActionMap(["OkCancelActions", "ShortcutActions", "EPGSelectActions", "WizardActions", "ColorActions", "NumberActions", "MenuActions", "MoviePlayerActions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)
		
		self['title'] = Label(self.pluginName)
		try:
			self['head'] = Label("Sendetermine")
		except Exception:
			sys.exc_clear()
		self['name'] = Label("Timer Auswahl")
		self['handlung'] = Label(" ")
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

		self.keyLocked = True
		self.streamMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.streamMenuList.l.setFont(0, gFont('Regular', self.contentSize))
		self.streamMenuList.l.setItemHeight(25)
		self['filmliste'] = self.streamMenuList
		
		self.onLayoutFinish.append(self.getTimerEventList)
	
	def skyAnytimerListEntry(self,entry):		
		if entry[5] == "True":
			icon = "/usr/lib/enigma2/python/Plugins/Extensions/skyrecorder/images/neu.png"
		elif entry[5] == "Done":
			icon = "/usr/lib/enigma2/python/Plugins/Extensions/skyrecorder/images/neu_blue.png"
		elif entry[5] == "Hidden":
			icon = "/usr/lib/enigma2/python/Plugins/Extensions/skyrecorder/images/neu_grau.png"
		else:
			icon = "/usr/lib/enigma2/python/Plugins/Extensions/skyrecorder/images/neu_green.png"
		# FIXME
		stime = getTimeFromTimestamp(entry[2])
		etime = getTimeFromTimestamp(entry[3])
			
		new = LoadPixmap(icon)
		return [entry,
			(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 20, 4, 28, 17, new),
			(eListboxPythonMultiContent.TYPE_TEXT, 70, 0, 150, 25, 0, RT_HALIGN_LEFT, entry[0]),
			(eListboxPythonMultiContent.TYPE_TEXT, 200, 0, 130, 25, 0, RT_HALIGN_LEFT, entry[1]),
			(eListboxPythonMultiContent.TYPE_TEXT, 330, 0, 100, 25, 0, RT_HALIGN_LEFT, stime),
			(eListboxPythonMultiContent.TYPE_TEXT, 430, 0, 100, 25, 0, RT_HALIGN_LEFT, etime),
			(eListboxPythonMultiContent.TYPE_TEXT, 530, 0, 230, 25, 0, RT_HALIGN_LEFT, entry[4])
			] 


	def getTimerEventList(self):
		# eventslist.dayname, eventslist.datum, eventslist.starttime, eventslist.endtime,
		# channel.channel, eventslist.status, events.title, events.description, eventslist.id_events
		try:
			sql.cur.execute('SELECT SQLITE_VERSION()')
		except Exception:
			sys.exc_clear()
			try:
				sql.connect()
			except Exception:
				return
				
		myList = None
		myList = []
		
		self['name'].setText("Timer Auswahl")
		
		rows = sql.getEventsTimer(self.id_events,"ASC", getCurrentTimestamp())
		resultCount = len(rows)
		if resultCount > 0:
			for row in rows:
				myList.append(row)
			
			self['handlung'].setText("Titel: \t" + myList[0][6] + "\nBeschreibung: \t" + myList[0][7])
			self.streamMenuList.setList(map(self.skyAnytimerListEntry, sorted(myList, key=lambda stime: stime[2])))
			#self['filmliste'].moveToIndex = 0
		try:
			self['head'].setText("%s Sendetermine" % str(resultCount))
		except Exception:
			sys.exc_clear()
				
	def getChannelref(self, channel):	
		for (channelname,channelref) in self.sky_chlist:
			if channelname.lower() == channel.lower():
				return channelref
				
	def keyPageDown(self):
		self['filmliste'].pageDown()
		
	def keyPageUp(self):
		self['filmliste'].pageUp()
						
	def keyOK(self):
		print "ok"
		datum = self['filmliste'].getCurrent()[0][1]
		starttime = self['filmliste'].getCurrent()[0][2]
		endtime = self['filmliste'].getCurrent()[0][3]
		channel = self['filmliste'].getCurrent()[0][4]
		title = self['filmliste'].getCurrent()[0][6]
		desc = self['filmliste'].getCurrent()[0][7]
		status = self['filmliste'].getCurrent()[0][5]
		
		dirname = None
		recordings_base_folder = None
		try:
			if config.plugins.skyrecorder.anytimefolder.value:
				recordings_base_folder = config.plugins.skyrecorder.anytimefolder.value
		except Exception:
			sys.exc_clear()
			recordings_base_folder = None
			
		# use settings "margin_before" and "margin_after"
		# for the timers starttime and endtime adjustment
		timer_starttime = starttime - config.plugins.skyrecorder.margin_before.value * 60
		timer_endtime = endtime + config.plugins.skyrecorder.margin_after.value * 60
		
		stb_channel = sql.getChannelFromChannel(channel,stb=True)
		channelref = self.getChannelref(stb_channel)
		
		print datum, starttime, endtime, stb_channel, channelref
		
		# try to delete this timerentry
		if status == "True":
			entry_dict = None
			entry_dict = {}
			entry_dict['name'] = title
			entry_dict['description'] = desc
			entry_dict['timer_starttime'] = timer_starttime
			entry_dict['channelref'] = channelref
			
			retval = SkyTimerRec.removeTimerEntry(entry_dict)
			#id_added = sql.checkAdded(title.lower(), desc.lower(), self.id_channel, self.id_genre)
			#if id_added: 
			#	sql.resetAdded(id_added)
			if retval:
				sql.updateEventListStatus(self.id_events,starttime,"False")
				if config.plugins.skyrecorder.silent_timer_mode.value == False:
					message = self.session.open(MessageBox, _("Timer gelöscht!"), MessageBox.TYPE_INFO, timeout=3)
			self.getTimerEventList()
			return
		
		if channelref != None:
			justplay = False
			if config.plugins.skyrecorder.timer_mode.value == "1":
				justplay = True
				
			if recordings_base_folder:
				if not config.plugins.skyrecorder.create_dirtree.value:
					dirname = recordings_base_folder
				else:
					# get our groupfoldername
					a_dir = sql.getGenregroupByGenreId(self.id_genre)
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
			
					
			result = SkyTimerRec.addTimer(self.session, channelref, timer_starttime, timer_endtime, title, desc, 0, justplay, 3, dirname, None, 0, None, eit=0)
			if result["result"]:
				sql.updateEventListStatus(self.id_events,starttime,status="True")
				
				# added by einfall
				#begin_date = time.strftime("%Y%m%d %H%M", time.localtime(starttime))
				file = getRecordFilename(title,desc,timer_starttime,stb_channel) # "%s - %s - %s.ts" % (begin_date,channel,title)
				
				# id_added,title,description,id_channel,id_genre,begin,end,serviceref,location,recordedfile
				if not sql.checkAdded(title.lower(), desc.lower(), self.id_channel, self.id_genre): 
					sql.addAdded(title, desc, self.id_channel, self.id_genre, timer_starttime, timer_endtime, channelref, dirname, file)
				
				self.getTimerEventList()
				#self.close()
			else:
				message = self.session.open(MessageBox, _("Fehler!\n%s") % (result["message"]), MessageBox.TYPE_INFO, timeout=-1)
	
	def keyCancel(self):
		self.close()
