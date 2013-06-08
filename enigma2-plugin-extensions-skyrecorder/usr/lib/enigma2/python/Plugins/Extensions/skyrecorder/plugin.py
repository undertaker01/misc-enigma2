#-*- coding: utf-8 -*-
from Components.config import config
from Plugins.Plugin import PluginDescriptor
from ServiceReference import ServiceReference
import os
import sys

# our custom classes
#from SkyRecorderSettings import SkyRecorderSettings
from SkyRecorderMainScreen import SkyRecorderMainScreen
from SkyGetTvGuide import SkyGetTvGuide
from SkyMainFunctions import checkForInternet

def autostart(reason, **kwargs):
	if reason == 0 and (config.plugins.skyrecorder.autoupdate_database and config.plugins.skyrecorder.autoupdate_database.value):
		if "session" in kwargs:
			
			try:
				import sqlite3
				ver = sqlite3.sqlite_version
				print "ok, found sqlite3 with version number {0}".format(ver)
				del(sqlite3)
			except Exception:
				sys.exc_clear()
				print "[SkyRecorder] ERROR: could not import sqlite3. Please run: 'opkg update; opkg install python-sqlite3; opkg install sqlite3'"
				return False
			
			# check if we have to create the database from scratch
			res = True
			try:
				if config.plugins.skyrecorder.skydb.value:
					try:
						sizeb = os.path.getsize(config.plugins.skyrecorder.skydb.value)
					except Exception:
						sys.exc_clear()
						sizeb = 0
					if not os.path.exists(config.plugins.skyrecorder.skydb.value) or sizeb == 0:
						from SkyCreateDatabase import buildSkydb
						res = buildSkydb(config.plugins.skyrecorder.skydb.value,rebuild=True,backup=False)
			except Exception:
				sys.exc_clear()
				from SkyCreateDatabase import buildSkydb
				res = buildSkydb(rebuild=True,backup=False)
				
			if res:
				if not checkForInternet():
					return
				session = kwargs["session"]
				SkyGetTvGuide(session, True)

def wakeMeUp():
	if config.plugins.skyrecorder.autoupdate_database and config.plugins.skyrecorder.wakeup:
		if config.plugins.skyrecorder.autoupdate_database.value and config.plugins.skyrecorder.wakeup.value:
			if int(config.plugins.skyrecorder.next_update.value) > 0:
				wecker = int(config.plugins.skyrecorder.next_update.value)
				#return int(time.mktime(datetime.datetime.now().timetuple())) + 30 # wake up in 30 seconds from now
				return wecker
			return -1 # happy dreaming
	pass
	
def main(session, **kwargs):
	# let us try to import sqlite3 to see if we have the extension installed
	try:
		import sqlite3
		ver = sqlite3.sqlite_version
		print "ok, found sqlite3 with version number {0}".format(ver)
		del(sqlite3)
	except Exception:
		sys.exc_clear()
		from Screens.MessageBox import MessageBox
		message = session.open(MessageBox, _("""Konnte SkyRecorder nicht starten.\nBitte 'python-sqlite3' bzw. 'sqlite3' installieren.\n\nBefehle zum Installieren:\nopkg update\nopkg install python-sqlite3\nopkg install sqlite3"""), MessageBox.TYPE_ERROR, timeout=-1)
		# and so we die
		return False

	# check if we have to create the database from scratch
	res = True
	try:
		if config.plugins.skyrecorder.skydb.value:
			try:
				sizeb = os.path.getsize(config.plugins.skyrecorder.skydb.value)
			except Exception:
				sys.exc_clear()
				sizeb = 0
			if not os.path.exists(config.plugins.skyrecorder.skydb.value) or sizeb == 0:
				from SkyCreateDatabase import buildSkydb
				res = buildSkydb(config.plugins.skyrecorder.skydb.value,rebuild=True,backup=False)
	except Exception:
		sys.exc_clear()
		from SkyCreateDatabase import buildSkydb
		res = buildSkydb(rebuild=True,backup=False)
	if res:
		session.open(SkyRecorderMainScreen)

def Plugins(**kwargs):
	# thanks to plugin EPGrefresh
	# we now have a clean list and deep standby wake up :)
	list = [
		PluginDescriptor(
			name = "SkyRecorder",
			description = ("Plugin, angelehnt an Sky Anytime"),
			where = [
				PluginDescriptor.WHERE_AUTOSTART,
				PluginDescriptor.WHERE_SESSIONSTART
			],
			fnc = autostart,
			wakeupfnc = wakeMeUp,
		),
		PluginDescriptor(
			name = "SkyRecorder",
			description = ("Plugin, angelehnt an Sky Anytime"),
			icon="plugin.png",
			where = PluginDescriptor.WHERE_PLUGINMENU,
			fnc = main
		),
	]
	return list
