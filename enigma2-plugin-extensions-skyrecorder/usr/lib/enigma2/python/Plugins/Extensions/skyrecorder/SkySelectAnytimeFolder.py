#-*- coding: utf-8 -*-
from Components.ActionMap import ActionMap
from Components.config import config
from Components.FileList import FileList
from Components.Label import Label
from Components.Sources.StaticText import StaticText
import NavigationInstance
from Screens.Screen import Screen
import sys

# our custom classes
from SkyMainFunctions import getPluginPath
#from SkySql import *


class SkySelectAnytimeFolder(Screen):

	
	def __init__(self, session, initDir, plugin_path = None):
		self.session = session
		path = "%s/skins/%s/screen_folder_anytime.xml" % (getPluginPath(), config.plugins.skyrecorder.anytime_skin.value)
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Screen.__init__(self, session)

		self["folderlist"] = FileList(initDir, inhibitMounts = False, inhibitDirs = False, showMountpoints = False, showFiles = False)
		self["media"] = Label()
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "EPGSelectActions"],
		{
			"back": self.cancel,
			"left": self.left,
			"right": self.right,
			"up": self.up,
			"down": self.down,
			"ok": self.ok,
			"green": self.green,
			"red": self.cancel
		}, -1)
		self.title=("SkyRecorder Zielordner auswählen")
		try:
			self["title"]=StaticText(self.title)
		except Exception:
			sys.exc_clear()

	def cancel(self):
		self.close(None)

	def green(self):
		directory = self["folderlist"].getCurrentDirectory()
		if (directory.endswith("/")):
			self.fullpath = self["folderlist"].getCurrentDirectory()
		else:
			self.fullpath = self["folderlist"].getCurrentDirectory() + "/"
		self.close(self.fullpath)

	def up(self):
		self["folderlist"].up()
		self.updateFile()

	def down(self):
		self["folderlist"].down()
		self.updateFile()

	def left(self):
		self["folderlist"].pageUp()
		self.updateFile()

	def right(self):
		self["folderlist"].pageDown()
		self.updateFile()

	def ok(self):
		if self["folderlist"].canDescent():
			self["folderlist"].descent()
			self.updateFile()

	def updateFile(self):
		currFolder = self["folderlist"].getSelection()[0]
		if self["folderlist"].getFilename() is not None:
			directory = self["folderlist"].getCurrentDirectory()
			if (directory.endswith("/")):
				self.fullpath = self["folderlist"].getCurrentDirectory()
			else:
				self.fullpath = self["folderlist"].getCurrentDirectory() + "/"
			
			self["media"].setText(self["folderlist"].getCurrentDirectory())
		else:
			currFolder = self["folderlist"].getSelection()[0]
			if currFolder is not None:
				self["media"].setText(currFolder)
			else:
				self["media"].setText("Invalid Choice")


		
