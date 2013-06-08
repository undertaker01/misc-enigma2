#-*- coding: utf-8 -*-
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.ActionMap import NumberActionMap, ActionMap
from Components.config import config
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap, MovingPixmap
from enigma import gFont, eTimer, ePicLoad, loadPNG, getDesktop, eListboxPythonMultiContent, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, eServiceReference
from enigma import eServiceCenter, iServiceInformation
from Components.Sources.ServiceEvent import ServiceEvent
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InfoBar import MoviePlayer
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_HDD
from Tools.LoadPixmap import LoadPixmap
import time
import sys
import os

# our custom classes
from SkyMainFunctions import getPluginPath
from SkySql import *

#MEDIAFILES_MOVIE = ("ts", "avi", "divx", "mpg", "mpeg", "mkv", "mp4", "mov", "iso")
MEDIAFILES_MOVIE = ("ts")

class SkyRecorderArchiv(Screen):

	def __init__(self, session):
		self.session = session
		path = "%s/skins/%s/screen_archiv.xml" % (getPluginPath(), config.plugins.skyrecorder.anytime_skin.value)
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		
		Screen.__init__(self, session)
		
		pluginName = config.plugins.skyrecorder.pluginname.value
		contentSize = config.plugins.skyrecorder.contentsize.value
		
		# try to get the ayntimefolder
		try:
			anytimefolder = config.plugins.skyrecorder.anytimefolder.value
		except Exception:
			sys.exc_clear()
			anytimefolder = resolveFilename(SCOPE_HDD)
		
		self.anytimefolder = anytimefolder
		
		self.serviceHandler = eServiceCenter.getInstance()
		
		self["actions"]  = ActionMap(["OkCancelActions", "ShortcutActions", "EPGSelectActions", "WizardActions", "ColorActions", "NumberActions", "MenuActions", "MoviePlayerActions"], {
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keySwitchList,
			"left" : self.keySwitchList,
			"red": self.keyRed,
			"green": self.keyGreen,
			"prevBouquet" : self.keyPageDown,
			"nextBouquet" : self.keyPageUp
		}, -1)
		
		# Genrelist
		self.showGenreList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.showGenreList.l.setFont(0, gFont('Regular', contentSize))
		self.showGenreList.l.setItemHeight(25)
		self['genreselect'] = self.showGenreList
		self['genreselect'].setList([])
		
		#Movielist
		self.showMovieList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.showMovieList.l.setFont(0, gFont('Regular', contentSize))
		self.showMovieList.l.setItemHeight(25)
		self['movieselect'] = self.showMovieList
		self['movieselect'].setList([])
		
		# Auswahl der liste welche als erstes angezeigt werden soll
		self["genreselect"].selectionEnabled(0)
		self["movieselect"].selectionEnabled(1)
		self.currentList = "movieselect"
		
		self['mainselect'] = Label("SkyRecorder Archiv")
		self['handlung'] = Label("")
		
		self.onLayoutFinish.append(self.getGenreList)
		self['movieselect'].onSelectionChanged.append(self.showDetails)
		
		
	def skyAnytimeGenreListEntry(self,entry):
		neu  = "/usr/lib/enigma2/python/Plugins/Extensions/skyrecorder/images/neu.png"
		return [entry,
			(eListboxPythonMultiContent.TYPE_TEXT, 50, 0, 210, 40, 0, RT_HALIGN_CENTER, str(entry))
			]

	def skyAnytimeMovieListEntry(self,entry):
		neu  = "/usr/lib/enigma2/python/Plugins/Extensions/skyrecorder/images/neu.png"
		begin_date = time.strftime("%d.%m.%Y %H:%M", time.localtime(float(entry[2])))
		return [entry,
			(eListboxPythonMultiContent.TYPE_TEXT, 50, 0, 200, 25, 0, RT_HALIGN_LEFT, str(begin_date)),
			(eListboxPythonMultiContent.TYPE_TEXT, 250, 0, 445, 25, 0, RT_HALIGN_LEFT, str(entry[0])),
			(eListboxPythonMultiContent.TYPE_TEXT, 700, 0, 200, 25, 0, RT_HALIGN_LEFT, str(entry[1]))
			]


	def showDetails(self):
		self['handlung'].setText(" ")
		if len(self.movielist) < 1:
			return

		try:
			serviceref = self['movieselect'].getCurrent()[0][4]
		except Exception:
			return
		
		if not serviceref:
			return
		
		try:
			info = self.serviceHandler.info(serviceref)
			title = info.getName(serviceref)	
			filminfo = info.getEvent(serviceref).getExtendedDescription()
		except Exception:
			return
		self['handlung'].setText(filminfo)


	def getMyDirs(self, my_folder = None, max_depth = 3, my_group="A-Z"):
		self.movielist = []
		
		if not my_folder or not os.path.isdir(my_folder):
			my_folder = self.anytimefolder
		
		my_dirs = []
		my_dirs.append(my_folder) # append base folder
		n = 0
		for root, dirs, files in os.walk(my_folder):
			if len(dirs) != 0:
				n += 1
				for a_dir in dirs:
					if a_dir[-1:] != "/":
						a_dir += "/"
					my_dirs.append(os.path.join(root, a_dir))
			if n == max_depth:
				break
		
		self.loadFiles(my_dirs, my_group)


	def loadFiles(self, my_dirs = None, my_group="A-Z"):
		
		self['handlung'].setText(" ")
		self.movielist = [ ]
		
		if not my_dirs:
			return
		
		my_list = None
		tags = set()
		
		for a_dir in my_dirs:
			if not os.path.isdir(a_dir):
				continue
			
			root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + a_dir)
			my_list = self.serviceHandler.list(root)
			if my_list is None:
				#print "listing of movies failed"
				continue
			
			# get current folder name for group mapping
			if a_dir[-1:] != "/":
				basedir_name = a_dir.split('/')[-1:][0]
			else:
				basedir_name = a_dir.split('/')[-2:-1][0] # -2 is true, because we have a leading slash in a_dir string
							
			while 1:
				serviceref = my_list.getNext()
				if not serviceref.valid():
					break
				
				filetype = serviceref.toString().split('.')
				filetype = filetype[-1].lower()
				if not filetype in MEDIAFILES_MOVIE:
					continue
				
				info = self.serviceHandler.info(serviceref)
				if info is None:
					continue
				
				begin = info.getInfo(serviceref, iServiceInformation.sTimeCreate)
				description = info.getInfoString(serviceref, iServiceInformation.sDescription)
				moviefile = os.path.realpath(serviceref.getPath())
				title = info.getName(serviceref)
				#channel = ServiceReference(info.getInfoString(parent, iServiceInformation.sServiceref)).getServiceName()	# Sender
				
				if my_group != "A-Z":
					if not basedir_name == my_group: # skip this folder, if the name does not match our group and we are not in A-Z
						group_check = None
						group_check = sql.getGenregroupByGenre(description)
						if not group_check or my_group != group_check:
							continue

				# convert space-seperated list of tags into a set
				this_tags = info.getInfoString(serviceref, iServiceInformation.sTags).split(' ')
				if this_tags == ['']:
					this_tags = []
				this_tags = set(this_tags)
				tags |= this_tags
			
				self.movielist.append((title, description, begin, moviefile, serviceref))
				
		if len(self.movielist) < 1:
			self.keySwitchList(set_list="genreselect")
			self.showMovieList.setList([ ])
		else:
			if my_group != "A-Z":
				self.movielist.sort(key=lambda x: -x[2]) # sort by date and time, if we are not in A-Z
			else:
				self.movielist = sorted(self.movielist, key=lambda x: x[0], reverse=False)
			self.showMovieList.setList(map(self.skyAnytimeMovieListEntry, self.movielist))
			self.keySwitchList(set_list="movieselect")

	
	def getGenreList(self):
		# get groupnames
		self.groupnames = []
		self.groupnames.append(("A-Z"))
		rows = sql.readGroupsShort()
		for t_row in rows:
			row = list(t_row)
			self.groupnames.append(row[1])
		self.showGenreList.setList(map(self.skyAnytimeGenreListEntry, self.groupnames))
		
		#self.loadFiles("A-Z")
		self.getMyDirs(self.anytimefolder, 3, "A-Z")
		
	def keySwitchList(self,set_list=None):
		if set_list:
			if set_list == "movieselect":
				if len(self.movielist) < 1:
					return
				self["genreselect"].selectionEnabled(0)
				self["movieselect"].selectionEnabled(1)
				self.currentList = set_list
			else:
				self["movieselect"].selectionEnabled(0)
				self["genreselect"].selectionEnabled(1)
				self.currentList = set_list
		else:
			if self.currentList == "genreselect":
				self["genreselect"].selectionEnabled(0)
				self["movieselect"].selectionEnabled(1)
				self.currentList = "movieselect"
			else:
				self["movieselect"].selectionEnabled(0)
				self["genreselect"].selectionEnabled(1)
				self.currentList = "genreselect"
			
	def keyPageDown(self):
		exist = self[self.currentList].getCurrent()
		if exist == None:
			return
		self[self.currentList].pageDown()
		
	def keyPageUp(self):
		exist = self[self.currentList].getCurrent()
		if exist == None:
			return
		self[self.currentList].pageUp()
		
	def skysettings(self):
		pass

	def keyLeft(self):
		pass
		exist = self[self.currentList].getCurrent()
		if exist == None:
			return
		self[self.currentList].pageUp()

	def keyRight(self):
		pass
		exist = self[self.currentList].getCurrent()
		if exist == None:
			return
		self[self.currentList].pageDown()

	def keyUp(self):
		exist = self[self.currentList].getCurrent()
		if exist == None:
			return	
		self[self.currentList].up()


	def keyDown(self):
		exist = self[self.currentList].getCurrent()
		if exist == None:
			return	
		self[self.currentList].down()


	def keyRed(self):
		#pass
		self.close()

	def keyGreen(self):
		#pass
		self.keyOK()

	def keyYellow(self):
		pass

	def keyBlue(self):
		self.close()

	def keyOK(self):
		if self.currentList == "genreselect":
			exist = self['genreselect'].getCurrent()
			if exist == None:
				return
			genre_auswahl = self['genreselect'].getCurrent()[0]
			#self.loadFiles(genre_auswahl)
			self.getMyDirs(self.anytimefolder, 3, genre_auswahl)
			
		else:
			exist = self['movieselect'].getCurrent()
			if exist == None:
				return
			title = self['movieselect'].getCurrent()[0][0]
			file = self['movieselect'].getCurrent()[0][3]
			if fileExists(file):
				self.play(title, file)
			else:
				print "Aufnahme nicht vorhanden."
				message = self.session.open(MessageBox, _("Die Aufnahme ist noch nicht vorhanden.\n'{0}'".format(file)), MessageBox.TYPE_INFO, timeout=-1)
			
			
	def play(self,title,file):
		sref = eServiceReference(1, 0, file)
		sref.setName(title)
		self.mp = self.session.open(MoviePlayer, sref)
		self.mp.leavePlayer = self.leavePlayerForced # overwrite MoviePlayer leave function
	
	def leavePlayerForced(self):
		self.mp.leavePlayerConfirmed([True, "quit"])
		
	def keyCancel(self):
		self.close()

