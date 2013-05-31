#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#######################################################################
#
#    MetrixWeather for VU+
#    Coded by iMaxxx (c) 2013
#    Support: www.vuplus-support.com
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
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially
#  distributed other than under the conditions noted above.
#
#
#######################################################################
from Renderer import Renderer
from Components.VariableText import VariableText
#import library to do http requests:
import urllib
from enigma import eLabel
#import easy to use xml parser called minidom:
from xml.dom.minidom import parseString
from Components.config import config, ConfigSubsection, configfile, ConfigText, ConfigNumber, ConfigDateTime,ConfigSelection

config.plugins.MetrixWeather = ConfigSubsection()
config.plugins.MetrixWeather.refreshInterval = ConfigNumber(default="10")
config.plugins.MetrixWeather.woeid = ConfigNumber(default="640161") #Location (visit metrixhd.info)
config.plugins.MetrixWeather.tempUnit = ConfigSelection(default="Celsius", choices = [
				("Celsius", _("Celsius")),
				("Fahrenheit", _("Fahrenheit"))
				])
config.plugins.MetrixWeather.currentLocation = ConfigText(default="N/A")
config.plugins.MetrixWeather.currentWeatherCode = ConfigText(default="(")
config.plugins.MetrixWeather.currentWeatherText = ConfigText(default="N/A")
config.plugins.MetrixWeather.currentWeatherTemp = ConfigText(default="0")

config.plugins.MetrixWeather.forecastTodayCode = ConfigText(default="(")
config.plugins.MetrixWeather.forecastTodayText = ConfigText(default="N/A")
config.plugins.MetrixWeather.forecastTodayTempMin = ConfigText(default="0")
config.plugins.MetrixWeather.forecastTodayTempMax = ConfigText(default="0")

config.plugins.MetrixWeather.forecastTomorrowCode = ConfigText(default="(")
config.plugins.MetrixWeather.forecastTomorrowText = ConfigText(default="N/A")
config.plugins.MetrixWeather.forecastTomorrowTempMin = ConfigText(default="0")
config.plugins.MetrixWeather.forecastTomorrowTempMax = ConfigText(default="0")



class MetrixWeatherUpdater(Renderer, VariableText):



	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self) 
		self.test = "3"
		config.plugins.MetrixWeather.save()        
		configfile.save()
		self.woeid = config.plugins.MetrixWeather.woeid.value
		self.timer = 1
	GUI_WIDGET = eLabel
	
	def changed(self, what):
		if self.timer == 1:
			try:
				self.GetWeather()
			except:
				pass
		elif self.timer >= int(config.plugins.MetrixWeather.refreshInterval.value) * 60:
			self.timer = 0
		self.timer = self.timer + 1
			
		
			
	def onShow(self):
		self.text = config.plugins.MetrixWeather.currentWeatherCode.value


	def GetWeather(self):
		print "MetrixWeather lookup for ID " + str(self.woeid)
		url = "http://query.yahooapis.com/v1/public/yql?q=select%20item%20from%20weather.forecast%20where%20woeid%3D%22"+str(self.woeid)+"%22&format=xml"
		#url = "http://query.yahooapis.com/v1/public/yql?q=select%20item%20from%20weather.forecast%20where%20woeid%3D%22"+str(self.woeid)+"%22%20u%3Dc&format=xml"
		
		
		# where location in (select id from weather.search where query="oslo, norway")
		file = urllib.urlopen(url)
		data = file.read()
		file.close()
		
		dom = parseString(data)
		title = self.getText(dom.getElementsByTagName('title')[0].childNodes)
		config.plugins.MetrixWeather.currentLocation.value = str(title).split(',')[0].replace("Conditions for ","")
		
		currentWeather = dom.getElementsByTagName('yweather:condition')[0]
		currentWeatherCode = currentWeather.getAttributeNode('code')
		config.plugins.MetrixWeather.currentWeatherCode.value = self.ConvertCondition(currentWeatherCode.nodeValue)
		currentWeatherTemp = currentWeather.getAttributeNode('temp')
		config.plugins.MetrixWeather.currentWeatherTemp.value = self.getTemp(currentWeatherTemp.nodeValue)
		currentWeatherText = currentWeather.getAttributeNode('text')
		config.plugins.MetrixWeather.currentWeatherText.value = currentWeatherText.nodeValue
		
		currentWeather = dom.getElementsByTagName('yweather:forecast')[0]
		currentWeatherCode = currentWeather.getAttributeNode('code')
		config.plugins.MetrixWeather.forecastTodayCode.value = self.ConvertCondition(currentWeatherCode.nodeValue)
		currentWeatherTemp = currentWeather.getAttributeNode('high')
		config.plugins.MetrixWeather.forecastTodayTempMax.value = self.getTemp(currentWeatherTemp.nodeValue)
		currentWeatherTemp = currentWeather.getAttributeNode('low')
		config.plugins.MetrixWeather.forecastTodayTempMin.value = self.getTemp(currentWeatherTemp.nodeValue)
		currentWeatherText = currentWeather.getAttributeNode('text')
		config.plugins.MetrixWeather.forecastTodayText.value = currentWeatherText.nodeValue
	
		currentWeather = dom.getElementsByTagName('yweather:forecast')[1]
		currentWeatherCode = currentWeather.getAttributeNode('code')
		config.plugins.MetrixWeather.forecastTomorrowCode.value = self.ConvertCondition(currentWeatherCode.nodeValue)
		currentWeatherTemp = currentWeather.getAttributeNode('high')
		config.plugins.MetrixWeather.forecastTomorrowTempMax.value = self.getTemp(currentWeatherTemp.nodeValue)
		currentWeatherTemp = currentWeather.getAttributeNode('low')
		config.plugins.MetrixWeather.forecastTomorrowTempMin.value = self.getTemp(currentWeatherTemp.nodeValue)
		currentWeatherText = currentWeather.getAttributeNode('text')
		config.plugins.MetrixWeather.forecastTomorrowText.value = currentWeatherText.nodeValue
	
	def getText(self,nodelist):
	    rc = []
	    for node in nodelist:
	        if node.nodeType == node.TEXT_NODE:
	            rc.append(node.data)
	    return ''.join(rc)
	   
	def ConvertCondition(self, c):
		c = int(c)
		condition = "("
		if c == 0 or c == 1 or c == 2:
			condition = "S"
		elif c == 3 or c == 4:
			condition = "Z"
		elif c == 5  or c == 6 or c == 7 or c == 18:
			condition = "U"
		elif c == 8 or c == 10 or c == 25:
			condition = "G"
		elif c == 9:
			condition = "Q"
		elif c == 11 or c == 12 or c == 40:
			condition = "R"
		elif c == 13 or c == 14 or c == 15 or c == 16 or c == 41 or c == 46 or c == 42 or c == 43:
			condition = "W"
		elif c == 17 or c == 35:
			condition = "X"
		elif c == 19:
			condition = "F"
		elif c == 20 or c == 21 or c == 22:
			condition = "L"
		elif c == 23 or c == 24:
			condition = "S"
		elif c == 26 or c == 44:
			condition = "N"
		elif c == 27 or c == 29:
			condition = "I"
		elif c == 28 or c == 30:
			condition = "H"
		elif c == 31 or c == 33:
			condition = "C"
		elif c == 32 or c == 34:
			condition = "B"
		elif c == 36:
			condition = "B"
		elif c == 37 or c == 38 or c == 39 or c == 45 or c == 47:
			condition = "0"
		else:
			condition = ")"
		return str(condition)
		
	def getTemp(self,temp):
		if config.plugins.MetrixWeather.tempUnit.value == "Fahrenheit":
			return str(int(round(float(temp),0)))
		else:
			celsius = (float(temp) - 32 ) * 5 / 9
			return str(int(round(float(celsius),0)))