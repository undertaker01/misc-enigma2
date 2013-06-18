#######################################################################
#
#    MyNobile
#    Plugin originally coded by iMaxxx for MyMetrix (c) 2013
#    MyNobile MOD by arn354 for Nobile
#
#
#  This plugin is licensed under the Creative Commons
#  Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#  To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#  or send a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially
#  distributed other than under the conditions noted above.
#
#######################################################################

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.Console import Console
from Screens.Standby import TryQuitMainloop
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.config import config, configfile, ConfigYesNo, ConfigSubsection, getConfigListEntry, ConfigSelection, ConfigNumber, ConfigText, ConfigInteger
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Language import language
from os import environ, listdir, remove, rename, system
from skin import parseColor
from Components.Pixmap import Pixmap
from Components.Label import Label
import gettext
from enigma import ePicLoad
from Tools.Directories import fileExists, resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS

lang = language.getLanguage()
environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("MyNobile", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/MyNobile/locale/"))

def _(txt):
	t = gettext.dgettext("MyNobile", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

def translateBlock(block):
	for x in TranslationHelper:
		if block.__contains__(x[0]):
			block = block.replace(x[0], x[1])
	return block

config.plugins.MyNobile = ConfigSubsection()
				#General
config.plugins.MyNobile.Image = ConfigSelection(default="main-custom-openatv", choices = [
				("main-custom-openatv", _("openATV")),
				("main-custom-openmips", _("openMips"))
				])
config.plugins.MyNobile.ChannelSelection = ConfigSelection(default="channelselection-channel-left", choices = [
				("channelselection-channel-left", _("Channellist left")),
				("channelselection-channel-center", _("Channellist center"))
				])
config.plugins.MyNobile.ChannelSelectionFontSize = ConfigSelection(default='serviceItemHeight="28" serviceNumberFont="Regular;18" serviceNameFont="Bold;20" serviceInfoFont="Regular;20"', choices = [
				('serviceItemHeight="28" serviceNumberFont="Regular;18" serviceNameFont="Bold;20" serviceInfoFont="Regular;20"', _("Default")),
				('serviceItemHeight="22" serviceNumberFont="Regular;16" serviceNameFont="Bold;18" serviceInfoFont="Regular;18"', _("50 Zoll <")),
				('serviceItemHeight="34" serviceNumberFont="Regular;24" serviceNameFont="Bold;26" serviceInfoFont="Regular;26"', _("< 40 Zoll"))
				])
				
class MyNobile(ConfigListScreen, Screen):
	skin = """
  <screen name="MyNobile-Setup" position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="#90000000">
    <eLabel name="new eLabel" position="40,40" zPosition="-2" size="1200,640" backgroundColor="#20000000" transparent="0" />
    <eLabel font="Regular; 20" foregroundColor="unffffff" backgroundColor="#20000000" halign="left" position="77,645" size="250,33" text="Cancel" transparent="1" />
    <eLabel font="Regular; 20" foregroundColor="unffffff" backgroundColor="#20000000" halign="left" position="375,645" size="250,33" text="Save" transparent="1" />
    <eLabel font="Regular; 20" foregroundColor="unffffff" backgroundColor="#20000000" halign="left" position="682,645" size="250,33" text="Reboot" transparent="1" />
    <widget name="config" position="61,107" scrollbarMode="showOnDemand" size="590,506" transparent="1" />
    <eLabel position="60,55" size="348,50" text="MyNobile" font="Regular; 40" valign="center" transparent="1" backgroundColor="#20000000" />
    <eLabel position="343,58" size="349,50" text="Setup" foregroundColor="unffffff" font="Regular; 30" valign="center" backgroundColor="#20000000" transparent="1" halign="left" />
    <eLabel position="665,640" size="5,40" backgroundColor="#e5dd00" />
    <eLabel position="360,640" size="5,40" backgroundColor="#61e500" />
    <eLabel position="60,640" size="5,40" backgroundColor="#e61700" />
    <widget name="helperimage" position="669,112" size="550,500" zPosition="1" />
    <eLabel text="Plugin originally coded by iMaxxx for MyMetrix" position="692,48" size="540,25" zPosition="1" font="Regular; 15" halign="right" valign="top" backgroundColor="#20000000" transparent="1" />
    <eLabel text="MOD MyNobile by arn354" position="692,70" size="540,25" zPosition="1" font="Regular; 15" halign="right" valign="top" backgroundColor="#20000000" transparent="1" />
  </screen>
"""

	def __init__(self, session, args = None, picPath = None):
		self.skin_lines = []
		Screen.__init__(self, session)
		self.session = session
		self.skinfile = "/usr/share/enigma2/Nobile/skin.xml"
		self.skinfileTMP = "/usr/share/enigma2/Nobile/skin.xml.tmp"
		self.skindata = "/usr/lib/enigma2/python/Plugins/Extensions/MyNobile/data/"
		self.picPath = picPath
		self.Scale = AVSwitch().getFramebufferScale()
		self.PicLoad = ePicLoad()
		self["helperimage"] = Pixmap()
		list = []
		list.append(getConfigListEntry(_("NobileImage"), config.plugins.MyNobile.Image))
		list.append(getConfigListEntry(_("Channellist Position"), config.plugins.MyNobile.ChannelSelection))
		list.append(getConfigListEntry(_("Channellist Font Size"), config.plugins.MyNobile.ChannelSelectionFontSize))
				
		ConfigListScreen.__init__(self, list)
		self["actions"] = ActionMap(["OkCancelActions","DirectionActions", "InputActions", "ColorActions"], {"left": self.keyLeft,"down": self.keyDown,"up": self.keyUp,"right": self.keyRight,"red": self.exit,"yellow": self.reboot, "blue": self.showInfo, "green": self.save,"cancel": self.exit}, -1)
		self.onLayoutFinish.append(self.UpdatePicture)
		
	def GetPicturePath(self):
		try:
			returnValue = self["config"].getCurrent()[1].value
			path = "/usr/lib/enigma2/python/Plugins/Extensions/MyNobile/images/" + returnValue + ".jpg"
			return path
		except:
			return "/usr/lib/enigma2/python/Plugins/Extensions/MyNobile/images/nohelperimage.jpg"
		
	def UpdatePicture(self):
		self.PicLoad.PictureData.get().append(self.DecodePicture)
		self.onLayoutFinish.append(self.ShowPicture)
	
	def ShowPicture(self):
		self.PicLoad.setPara([self["helperimage"].instance.size().width(),self["helperimage"].instance.size().height(),self.Scale[0],self.Scale[1],0,1,"#002C2C39"])
		self.PicLoad.startDecode(self.GetPicturePath())
		
	def DecodePicture(self, PicInfo = ""):
		ptr = self.PicLoad.getData()
		self["helperimage"].instance.setPixmap(ptr)	

	def keyLeft(self):	
		ConfigListScreen.keyLeft(self)	
		self.ShowPicture()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.ShowPicture()
	
	def keyDown(self):
		self["config"].instance.moveSelection(self["config"].instance.moveDown)
		self.ShowPicture()
		
	def keyUp(self):
		self["config"].instance.moveSelection(self["config"].instance.moveUp)
		self.ShowPicture()
	
	def reboot(self):
		restartbox = self.session.openWithCallback(self.restartGUI,MessageBox,_("Do you really want to reboot now?"), MessageBox.TYPE_YESNO)
		restartbox.setTitle(_("Restart GUI"))
		
	def showInfo(self):
		self.session.open(MessageBox, _("Information"), MessageBox.TYPE_INFO)

	def save(self):
		for x in self["config"].list:
			if len(x) > 1:
					x[1].save()
			else:
					pass

		try:
			###header XML
			self.appendSkinFile(self.skindata + "header.xml")
			###main XML
			self.appendSkinFile(self.skindata + "main.xml")
			###main-custom XML
			self.appendSkinFile(self.skindata + config.plugins.MyNobile.Image.value + ".xml")
			###channelselection XML
			self.appendSkinFile(self.skindata + config.plugins.MyNobile.ChannelSelection.value + ".xml")
			###footer XML
			self.appendSkinFile(self.skindata + "footer.xml")
			
			xFile = open(self.skinfileTMP, "w")
			for xx in self.skin_lines:
				xFile.writelines(xx)
			xFile.close()
			o = open(self.skinfile,"w")
			for line in open(self.skinfileTMP):
			#	line = line.replace("#00149bae", config.plugins.MyNobile.SkinColor.value )
				line = line.replace('serviceItemHeight="28" serviceNumberFont="Regular;18" serviceNameFont="Bold;20" serviceInfoFont="Regular;20"', config.plugins.MyNobile.ChannelSelectionFontSize.value )
				o.write(line)
			o.close()
			system('rm -rf ' + self.skinfileTMP)

		except:
			self.session.open(MessageBox, _("Error creating Skin!"), MessageBox.TYPE_ERROR)

		configfile.save()
		restartbox = self.session.openWithCallback(self.restartGUI,MessageBox,_("GUI needs a restart to apply the changed skin.\nDo you want to Restart the GUI now?"), MessageBox.TYPE_YESNO)
		restartbox.setTitle(_("Restart GUI"))

	def appendSkinFile(self,appendFileName):
		skFile = open(appendFileName, "r")
		file_lines = skFile.readlines()
		skFile.close()	
		for x in file_lines:
			self.skin_lines.append(x)

	def restartGUI(self, answer):
		if answer is True:
			configfile.save()
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()

	def exit(self):
		for x in self["config"].list:
			if len(x) > 1:
					x[1].cancel()
			else:
					pass
		self.close()

def main(session, **kwargs):
	session.open(MyNobile,"/usr/lib/enigma2/python/Plugins/Extensions/MyNobile/images/nohelperimage.jpg")

def Plugins(**kwargs):
	return PluginDescriptor(name="MyNobile", description=_("Configuration tool for Nobile mod by satinfo"), where = PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main)