# -*- coding: utf-8 -*-
from Components.ActionMap import *
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Button import Button
from Components.Label import Label
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.ActionMap import NumberActionMap, ActionMap
from Components.config import config, ConfigSelection, getConfigListEntry, ConfigText, ConfigDirectory, ConfigYesNo, ConfigSelection, ConfigSubsection, ConfigPIN, configfile
from Components.FileList import FileList, FileEntryComponent
from Components.GUIComponent import GUIComponent
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap, MovingPixmap
from Components.PluginList import PluginEntryComponent, PluginList
from Components.AVSwitch import AVSwitch
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmap, MultiContentEntryPixmapAlphaTest
from Components.ServiceEventTracker import ServiceEventTracker

from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import MoviePlayer
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from enigma import iPlayableService, iServiceInformation, eServiceReference, eTimer
from enigma import gFont, eTimer, eConsoleAppContainer, ePicLoad, loadPNG, getDesktop, eListboxPythonMultiContent, eListbox, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER
from Tools.Directories import pathExists, fileExists, SCOPE_SKIN_IMAGE, resolveFilename
from Tools.LoadPixmap import LoadPixmap
from Tools import Notifications

import urllib2, re, os, shutil, time
from Tools.Downloader import downloadWithProgress

already_open = False
MoviePlayer.originalOpenEventView = MoviePlayer.openEventView

config.plugins.mediainfo = ConfigSubsection()
config.plugins.mediainfo.donemsg = ConfigYesNo(default = True)
config.plugins.mediainfo.savetopath = ConfigText(default = "/media/hdd/movie/",  fixed_size=False)
config.plugins.mediainfo.buffersize = ConfigSelection(default = "1", choices = [("1",(1)),("2",(2)),("4",(4)),("8",(8)),("12",(12)),("16",(16)),("32",(32))])

class chooseMenuList(MenuList):
	def __init__(self, list):
		MenuList.__init__(self, list, True, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setItemHeight(40)

global joblist
joblist = []

class dlm:
	def __init__(self, filename, url):
		self.filename = filename
		self.url = url
		self.totalMB = 0
		self.end = 100
		#self.path = "/media/hdd/movie/"
		self.path = config.plugins.mediainfo.savetopath.value
		self.downloadsfile = "/usr/lib/enigma2/python/Plugins/Extensions/mediainfo/downloads"
		self.storepath = "%s%s" % (self.path, self.filename)
		print "[Download] info: url='%s', fileName='%s%s'" % (self.url, self.path, self.filename)
		
	def run(self, checkname):
		self.checkname = checkname
		print "[Download] startet: %s" % checkname
		self.totalMB = 0
		self.download = downloadWithProgress(self.url,self.storepath)
		self.download.addProgress(self.http_progress)
		self.download.start().addCallback(self.http_finished).addErrback(self.http_failed)
		
	def check(self, checkname):
		print "[Download] restart: %s" % checkname
		self.totalMB = 0
		self.checkname = checkname
		self.download = downloadWithProgress(self.url,self.storepath)
		self.download.addProgress(self.http_progress2)
		self.download.start().addCallback(self.http_finished).addErrback(self.http_failed)

	def stop(self, name):
		print "[Download] gestoppt: %s" % name
		self.download.stop()
		dlfile = open(self.downloadsfile, "r")
		dlfile_tmp = open(self.downloadsfile+".tmp", "w")
		for rawData in dlfile.readlines():
			data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
			if data:
				(filename, storepath, url, totalMB, status, starttime) = data[0]
				if filename == name:
					dlfile_tmp.write('"%s" "%s" "%s" "%s" "%s" "%s"\n' % (filename, storepath, url, totalMB, "Stop", starttime))
				else:
					dlfile_tmp.write('"%s" "%s" "%s" "%s" "%s" "%s"\n' % (filename, storepath, url, totalMB, status, starttime))
		dlfile_tmp.close()
		dlfile.close()
		shutil.move(self.downloadsfile+".tmp", self.downloadsfile)
		print "[Download] move:", self.downloadsfile+".tmp", self.downloadsfile
		
	def http_progress(self, receivedBytes, totalBytes):
		if self.totalMB == 0:
			self.receivedMb = int(float(receivedBytes/1024/1024))
			self.totalMB = int((totalBytes/1024/1024))
			print "[Download] start:", self.receivedMb, "von", self.totalMB
						
			if fileExists(self.downloadsfile):
				dlfile = open(self.downloadsfile, "a")
				dlfile.write('"%s" "%s" "%s" "%s" "%s" "%s"\n' % (self.filename, self.storepath, self.url, self.totalMB, "Download", int(time.time())))
				dlfile.close()
			else:
				dlfile = open(self.downloadsfile, "w")
				dlfile.write('"%s" "%s" "%s" "%s" "%s" "%s"\n' % (self.filename, self.storepath, self.url, self.totalMB, "Download", int(time.time())))
				dlfile.close()
				
	def http_progress2(self, receivedBytes, totalBytes):
		if self.totalMB == 0:
			self.receivedMb = int(float(receivedBytes/1024/1024))
			self.totalMB = int((totalBytes/1024/1024))
			print "[Download] start:", self.receivedMb, "von", self.totalMB
			if fileExists(self.downloadsfile):
				dlfile = open(self.downloadsfile, "r")
				dlfile_tmp = open(self.downloadsfile+".tmp", "w")
				for rawData in dlfile.readlines():
					data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
					if data:
						(filename, storepath, url, totalMB, status, starttime) = data[0]
						if filename == self.checkname:
							dlfile_tmp.write('"%s" "%s" "%s" "%s" "%s" "%s"\n' % (filename, storepath, url, totalMB, "Download", int(time.time())))
						else:
							dlfile_tmp.write('"%s" "%s" "%s" "%s" "%s" "%s"\n' % (filename, storepath, url, totalMB, status, starttime))
				dlfile_tmp.close()
				dlfile.close()
				shutil.move(self.downloadsfile+".tmp", self.downloadsfile)
				print "[Download] move:", self.downloadsfile+".tmp", self.downloadsfile
			
	def http_finished(self, string=""):
		print "[Download] done:", self.checkname
		if config.plugins.mediainfo.donemsg.value:
			Notifications.AddNotification(MessageBox, _("%s is Done.") %(self.checkname), type=MessageBox.TYPE_INFO, timeout=10)
			
		dlfile = open(self.downloadsfile, "r")
		dlfile_tmp = open(self.downloadsfile+".tmp", "w")
		for rawData in dlfile.readlines():
			data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
			if data:
				(filename, storepath, url, totalMB, status, starttime) = data[0]
				print self.checkname, filename
				if filename == self.checkname:
					print "replace it..."
					dlfile_tmp.write('"%s" "%s" "%s" "%s" "%s" "%s"\n' % (filename, storepath, url, totalMB, "Done", starttime))
				else:
					dlfile_tmp.write('"%s" "%s" "%s" "%s" "%s" "%s"\n' % (filename, storepath, url, totalMB, status, starttime))
		dlfile_tmp.close()
		dlfile.close()
		shutil.move(self.downloadsfile+".tmp", self.downloadsfile)
		print "[Download] move:", self.downloadsfile+".tmp", self.downloadsfile

	def http_failed(self, failure_instance=None, error_message=""):
		print "[Download] http_failed"
		if error_message == "" and failure_instance is not None:
			error_message = failure_instance.getErrorMessage()
			print "[Download] http_failed " + error_message
	
			if error_message != "200 OK":
				print "[Download] error:", self.checkname
				dlfile = open(self.downloadsfile, "r")
				dlfile_tmp = open(self.downloadsfile+".tmp", "w")
				for rawData in dlfile.readlines():
					data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
					if data:
						(filename, storepath, url, totalMB, status, starttime) = data[0]
						print self.checkname, filename
						if filename == self.checkname:
							print "replace it..."
							dlfile_tmp.write('"%s" "%s" "%s" "%s" "%s" "%s"\n' % (filename, storepath, url, totalMB, "Error", starttime))
						else:
							dlfile_tmp.write('"%s" "%s" "%s" "%s" "%s" "%s"\n' % (filename, storepath, url, totalMB, status, starttime))
				dlfile_tmp.close()
				dlfile.close()
				shutil.move(self.downloadsfile+".tmp", self.downloadsfile)
				print "[Download] move:", self.downloadsfile+".tmp", self.downloadsfile
			
class mediaInfoSetup(ConfigListScreen, Screen):
	skin = """
		<screen name="MediaInfo Setup" position="center,center" size="1050,515" backgroundColor="#00060606" title="MediaInfo Setup" flags="wfNoBorder">
			<widget name="config" position="0,125" size="1050,350" backgroundColor="#00101214" scrollbarMode="showOnDemand" transparent="0" />
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/mediainfo/buttons/key_red.png" position="20,480" size="30,30" alphatest="blend" />
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/mediainfo/buttons/key_green.png" position="240,480" size="30,30" alphatest="blend" />
			<widget source="key_red" render="Label" position="60,480" size="180,26" zPosition="1" font="Regular;20" halign="left" foregroundColor="grey" backgroundColor="black" transparent="1" />
			<widget source="key_green" render="Label" position="280,480" size="180,26" zPosition="1" font="Regular;19" halign="left" foregroundColor="grey" backgroundColor="black" transparent="1" />
			</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		
		self.configlist = []
		ConfigListScreen.__init__(self, self.configlist)
		self.configlist.append(getConfigListEntry("Zeige Nachricht bei fertigen Download:", config.plugins.mediainfo.donemsg))
		self.configlist.append(getConfigListEntry("Buffer Size:", config.plugins.mediainfo.buffersize))
		self.configlist.append(getConfigListEntry("Speicher Downloads nach:", config.plugins.mediainfo.savetopath))
		
		self["config"].setList(self.configlist)
		
		self["key_red"] = Label(_('Cancel'))
		self["key_green"] = Label(_('Save'))
		
		self["actions"]  = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions", "NumberActions", "MenuActions"], {
			"green" : self.keySave,
			"red": self.keyCancel
		}, -1)
		
	def keySave(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()
		self.close(True)
	
	def keyCancel(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close(False)
		
def dlListEntry(entry):
	if entry[6] == "":
		dlspeed = ""
	else:
		dlspeed = " @  %s" % str(entry[6])
		
	currentMB = "%smb / %smb %s" % (str(entry[3]), str(entry[4]), dlspeed)
	
	if int(entry[3]) > 0:
		currentProgress = int(float(100) / float(int(entry[4])) * int(entry[3]))
	else:
		currentProgress = 0
		
	color2 = 0x00ffffff #Weiss

	return [entry,
		(eListboxPythonMultiContent.TYPE_TEXT, 20, 0, 380, 25, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0], color2, color2, None, None),
		(eListboxPythonMultiContent.TYPE_TEXT, 425, 0, 360, 25, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, currentMB, color2, color2 , None, None),
		(eListboxPythonMultiContent.TYPE_PROGRESS, 760, 0, 140, 22, int(currentProgress), None, None, color2, None),
		(eListboxPythonMultiContent.TYPE_TEXT, 920, 0, 130, 25, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[5], color2, color2, None, None)
		]
class mediaInfo(ConfigListScreen, Screen):
	skin = """
		<screen name="MediaInfo" position="center,center" size="1050,515" backgroundColor="#00060606" title="MediaInfo v0.6" flags="wfNoBorder">
			<widget name="pname" position="25,20" size="1025,30" zPosition="0" font="Regular;26" transparent="1" foregroundColor="white" />
			<widget name="pinfo" position="25,50" size="1025,30" zPosition="0" font="Regular;26" transparent="1" foregroundColor="white" />
			<widget name="head" position="0,100" size="1050,25" backgroundColor="#00aaaaaa" zPosition="5" foregroundColor="#00000000" font="Regular;23" halign="center"/>
			<widget name="dllist" position="0,125" size="1050,350" backgroundColor="#00101214" scrollbarMode="showOnDemand" transparent="0" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/mediainfo/buttons/sel.png"/>
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/mediainfo/buttons/key_red.png" position="20,480" size="30,30" alphatest="blend" />
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/mediainfo/buttons/key_green.png" position="240,480" size="30,30" alphatest="blend" />
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/mediainfo/buttons/key_yellow.png" position="460,480" size="30,30" alphatest="blend" />
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/mediainfo/buttons/key_blue.png" position="700,480" size="30,30" alphatest="blend" />
			<widget source="key_red" render="Label" position="60,480" size="180,26" zPosition="1" font="Regular;20" halign="left" foregroundColor="grey" backgroundColor="black" transparent="1" />
			<widget source="key_green" render="Label" position="280,480" size="180,26" zPosition="1" font="Regular;19" halign="left" foregroundColor="grey" backgroundColor="black" transparent="1" />
			<widget source="key_yellow" render="Label" position="500,480" size="200,26" zPosition="1" font="Regular;19" halign="left" foregroundColor="grey" backgroundColor="black" transparent="1" />
			<widget source="key_blue" render="Label" position="740,480" size="160,26" zPosition="1" font="Regular;20" halign="left" foregroundColor="grey" backgroundColor="black" transparent="1" />
			</screen>"""

	def __init__(self, session, livestreaming):
		Screen.__init__(self, session)
		self.session = session
		self.livestreaming = livestreaming

		self["pname"] = Label("")
		self["pinfo"] = Label("")
		self['head'] = Label("Current Downloads:")

		self["key_red"] = Label(_('Delete'))
		self["key_green"] = Label(_('Add'))
		self["key_yellow"] = Label(_('Start/Stop'))
		self["key_blue"] = Label(_('Settings'))
				
		self.dllist = []
		self.chooseMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList.l.setFont(0, gFont('Regular', 24))
		self.chooseMenuList.l.setItemHeight(25)
		self['dllist'] = self.chooseMenuList

		self.downloadsfile = "/usr/lib/enigma2/python/Plugins/Extensions/mediainfo/downloads"
		self.refreshTimer = eTimer()
		self.refreshTimer.callback.append(self.refresh)
		self.refreshTimer.start(1000)
		self.updateTimer = eTimer()
		self.updateTimer.callback.append(self.get_info)
		self.joblist = []
		self.onClose.append(self.__onClose)
		
		if self.livestreaming:
			self.onLayoutFinish.append(self.get_info)

		self["actions"] = ActionMap(["WizardActions"],
		{
			"back": self.exit,
		}, -1)
		
		self["actions"]  = ActionMap(["OkCancelActions", "ShortcutActions", "EPGSelectActions", "WizardActions", "ColorActions", "NumberActions", "MenuActions", "MoviePlayerActions", "InfobarSeekActions"], {
			"ok" : self.exit,
			"info" : self.exit,
			"cancel" : self.exit,
			"red" : self.dlremove,
			"green" : self.dlrun,
			"yellow" : self.dlcheck,
			"blue" : self.dlmenu
		}, -1)

	def dlrun(self):
		service = self.session.nav.getCurrentService()
		filename = service.info().getName()
		url = self.session.nav.getCurrentlyPlayingServiceReference().getPath()
		filename = ''.join(re.split(r'[.;:!&?,]', filename))
		filetype = re.findall('(\.avi|\.mp4|\.ts|\.mp3|\.mpg|\.mpeg)', url, re.I)
		if filetype:
			filetype = filetype[0]
		else:
			filetype = ".flv"
		filename = "%s%s" % (filename.replace(' ','_'), filetype)
		
		if not any(filename in job for job in joblist):
			if re.match('.*?http', url, re.S):
				try:
					req = urllib2.Request(url)
					res = urllib2.urlopen(req)
					url = res.geturl()
					print "[Download] added: %s - %s" % (filename, url)
					self.currentDownload = dlm(filename, url)
					joblist.append((filename, self.currentDownload))
					self.currentDownload.run(filename)
				except urllib2.HTTPError, error:
					print error
					message = self.session.open(MessageBox, ("Fehler: %s" % error), MessageBox.TYPE_INFO, timeout=6)
				except urllib2.URLError, error:
					print error.reason
					message = self.session.open(MessageBox, ("Fehler: %s" % error.reason), MessageBox.TYPE_INFO, timeout=6)
			else:
				message = self.session.open(MessageBox, ("No rtmp download support, only http protocl."), MessageBox.TYPE_INFO, timeout=6)
		else:
			print "[Download] dupe: %s" % filename
		
	def dlcheck(self):
		exist = self['dllist'].getCurrent()
		if exist == None:
			return
			
		checkname = self['dllist'].getCurrent()[0][0]
		url = self['dllist'].getCurrent()[0][2]
		status = self['dllist'].getCurrent()[0][5]
		print "[Download] info:", checkname, url, status

		if status == "Download":
			global joblist
			for (name,job) in joblist:
				if name == checkname:
					job.stop(checkname)

		elif status == "Stop":
			global joblist
			for (name,job) in joblist:
				if name == checkname:
					job.check(checkname)

	def dlremove(self):
		exist = self['dllist'].getCurrent()
		if exist == None:
			return
			
		checkname = self['dllist'].getCurrent()[0][0]
		status = self['dllist'].getCurrent()[0][5]
		print "[Download] remove: %s" % checkname
		
		if status == "Download":
			global joblist
			for (name,job) in joblist:
				if name == checkname:
					job.stop(checkname)
					
		joblist_tmp = []
		for (name,job) in joblist:
			print name,job
			if name != checkname:
				joblist_tmp.append((name, job))

		joblist = joblist_tmp
		print "---------------------------------------------------"
		
		for (name,job) in joblist:
			print name,job

		if fileExists(self.downloadsfile):
			dlfile = open(self.downloadsfile, "r")
			dlfile_tmp = open(self.downloadsfile+".tmp", "w")
			for rawData in dlfile.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(filename, storepath, url, totalMB, status, starttime) = data[0]
					if filename != checkname:
						dlfile_tmp.write('"%s" "%s" "%s" "%s" "%s" "%s"\n' % (filename, storepath, url, totalMB, status, starttime))
	
			dlfile_tmp.close()
			dlfile.close()
			shutil.move(self.downloadsfile+".tmp", self.downloadsfile)
			print "[Download] move:", self.downloadsfile+".tmp", self.downloadsfile			

	def refresh(self):
		if fileExists(self.downloadsfile):
			dlfile = open(self.downloadsfile, "r")
			self.dllist = []
			for rawData in dlfile.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(filename, storepath, url, totalMB, status, starttime) = data[0]
					try:
						currentSizeMB = os.path.getsize(storepath)/1024/1024
					except OSError:
						currentSizeMB = 0
						print "[Download] EEEEERRRROOOORRR currenSize: %s" % currentSizeMB
					#Robin_Hood_ /media/hdd/movie/Robin_Hood_ http://dl.loadtv.c.nmdn.net/loadtv_vod/flashmedia/kinderkino-kostenlos/robin-hood.mp4 313 dl
					if status == "Download":
						endtime = int(time.time())
						#print endtime, starttime
						runtime = endtime - int(starttime)
						if runtime == 0:
							print "[Download] set runtime: 1sec."
							runtime = 1
						if currentSizeMB == 0:
							print "[Download] set currentSize: 1 mb."
							currentSizeMB = 1
							
						dlspeed = (currentSizeMB * 1024) / runtime
						#resttime = (int(totalMB) * 1024) / dlspeed
						resttime = (((int(totalMB) - currentSizeMB) * 1024) / (currentSizeMB * 1024)) * runtime
						if dlspeed > 1024:
							dlspeed = "%.2f mb/s" % (float(dlspeed) / 1024)
						else:
							dlspeed = "%s kb/s" % dlspeed
							
						#print "[Download] dl-speed: %s - finish in: %s sec." % (dlspeed, str(resttime))	
					else:
						dlspeed = ""
						resttime = ""
						
					#currentMB = "%smb / %smb" % (str(currentSizeMB), str(totalMB))
					self.dllist.append((filename, storepath, url, str(currentSizeMB), str(totalMB), status, str(dlspeed), str(resttime)))
			self.chooseMenuList.setList(map(dlListEntry, self.dllist))

	def get_info(self):
		self.updateTimer.stop()
		service = self.session.nav.getCurrentService()
		#service.streamed().setBufferSize(config.plugins.mediainfo.buffersize.value)
		service.streamed().setBufferSize(long(int(config.plugins.mediainfo.buffersize.value)) * 1024 * 1024)
		bufferInfo = service.streamed().getBufferCharge()
		pname_text = service.info().getName()
		url_text = self.session.nav.getCurrentlyPlayingServiceReference().getPath()
	
		if bufferInfo != None: 
			if bufferInfo[2] != 0:
				self.bufferSeconds = bufferInfo[4] / bufferInfo[2] #buffer size / avgOutRate
			else:
				self.bufferSeconds = 0
				
			self.bufferPercent = bufferInfo[0]
			self.bufferSecondsLeft = self.bufferSeconds * self.bufferPercent / 100
			self["pname"].setText("%s" % str(pname_text))
			self["pinfo"].setText("Stream %s - Bitrate: %s - Buffer: %s filled %s (%s sec.)" % (self.formatKB(bufferInfo[1]), self.formatKBits(bufferInfo[2]), self.bufferPercent, self.formatKB(bufferInfo[4]), self.bufferSecondsLeft))
			self.updateTimer.start(1000)
		

	def dlmenu(self):
		self.session.open(mediaInfoSetup)
	
	def exit(self):
		already_open = False
		self.close()
		
	def __onClose(self):
		print "[Download] windows closed"
		self.updateTimer.stop()
		self.refreshTimer.stop()
		
	def formatKBits(self, value, ending="Bit/s", roundNumbers=2):
		bits = value * 8
		if bits > (1024*1024):
			return str(    round(float(bits)/float(1024*1024),roundNumbers)  )+" M"+ending
		if bits > 1024:
			return str(    round(float(bits)/float(1024),roundNumbers)       )+" K"+ending
		else:
			return str(bits)+" "+ending
		
	def formatKB(self, value, ending="B", roundNumbers=2):
		byte = value
		if byte > (1024*1024):
			return str(    round(float(byte)/float(1024*1024),roundNumbers) )+" M"+ending
		if byte > 1024:
			return str(    round(float(byte)/float(1024),roundNumbers)      )+" K"+ending
		else:
			return str(byte)+" "+ending
		
def openMoviePlayerEventView(self):
	already_open = False
	if True and not already_open:
		already_open = True
		service = self.session.nav.getCurrentService()
		filename = service.info().getName()
		url = self.session.nav.getCurrentlyPlayingServiceReference().getPath()
		if re.match('.*?http://', url, re.S):
			self.session.open(mediaInfo, True)
		else:
			self.session.open(mediaInfo, False)
	else:
		MoviePlayer.originalOpenEventView(self)
		
MoviePlayer.InfoPressed = openMoviePlayerEventView

def autostart(reason, **kwargs):
	downloadsfile = "/usr/lib/enigma2/python/Plugins/Extensions/mediainfo/downloads"
	if fileExists(downloadsfile):
		dlfile = open(downloadsfile, "r")
		dlfile_tmp = open(downloadsfile+".tmp", "w")
		for rawData in dlfile.readlines():
			data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
			if data:
				(filename, storepath, url, totalMB, status, starttime) = data[0]
				dlfile_tmp.write('"%s" "%s" "%s" "%s" "%s" "%s"\n' % (filename, storepath, url, totalMB, "Stop", starttime))
				currentDownload = dlm(filename.replace(' ','_'), url)
				global joblist
				joblist.append((filename.replace(' ','_'), currentDownload))
		dlfile.close()
		dlfile_tmp.close()
		print "[Download] move:", downloadsfile+".tmp", downloadsfile
		shutil.move(downloadsfile+".tmp", downloadsfile)

def main(session,**kwargs):
	session.open(mediaInfo, False)
	
def Plugins(**kwargs):
	return [PluginDescriptor(name="MediaInfo", description="StreamDownloads", where = [PluginDescriptor.WHERE_PLUGINMENU], fnc=main),
			PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART], fnc=autostart)]