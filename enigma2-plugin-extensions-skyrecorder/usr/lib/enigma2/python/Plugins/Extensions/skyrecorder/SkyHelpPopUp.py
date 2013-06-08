#-*- coding: utf-8 -*-
import codecs
from Components.ScrollLabel import ScrollLabel
from Screens.Screen import Screen

from SkyMainFunctions import getPluginPath

class SkyHelpAll(Screen):
	skin = """
		<screen zPosition="3" position="center,center" size="800,500" title="Message" flags="wfNoBorder">
			<widget name="text" position="10,10" size="780,480" backgroundColor="#26181d20" transparent="1" font="Regular;20" valign="top" halign="left" zPosition="1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		
		self["text"] = ScrollLabel("Hilfe")
		
	
	def loadHelpText(self):
		path = "%s/skyrecorder_help_all.txt" % getPluginPath()
		with codecs.open(path, "r", "utf-8") as f:
			text = f.read()
			self['text'].setText(str(text))