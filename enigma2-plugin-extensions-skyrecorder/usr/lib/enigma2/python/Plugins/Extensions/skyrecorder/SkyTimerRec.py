#-*- coding: utf-8 -*-
from Components.UsageConfig import preferredTimerPath, preferredInstantRecordPath
from Components.config import config
from Screens.MessageBox import MessageBox
import os

# Navigation (RecordTimer)
import NavigationInstance

# Timer
from ServiceReference import ServiceReference
from RecordTimer import RecordTimerEntry
from RecordTimer import RecordTimer, parseEvent, AFTEREVENT

from Components.TimerSanityCheck import TimerSanityCheck
from SkyMainFunctions import getChannelByRef, getRecordFilename, buildSkyChannellist

class SkyTimerRec():

	#def __init__(self, session):
	#	self.session = session
	
	@staticmethod	
	def getTimersList():
	
		recordHandler = NavigationInstance.instance.RecordTimer
		
		entry = None
		timers = []
		sky_chlist = buildSkyChannellist()
		
		for timer in recordHandler.timer_list:
			if timer and timer.service_ref and timer.eit is not None:

				location = 'NULL'
				channel = 'NULL'
				recordedfile ='NULL' 
				if timer.dirname:
					location = timer.dirname
				channel = getChannelByRef(sky_chlist,str(timer.service_ref))
				if channel:
					recordedfile = getRecordFilename(timer.name,timer.description,timer.begin,channel)
				timers.append({
					"title": timer.name,
					"description": timer.description,
					"id_channel": 'NULL',
					"channel": channel,
					"id_genre": 'NULL',
					"begin": timer.begin,
					"end": timer.end,
					"serviceref": timer.service_ref,
					"location": location,
					"recordedfile": recordedfile,
					"tags": timer.tags
				})
		return timers		
	
	
	@staticmethod
	def removeTimerEntry(entry_dict):
	
		recordHandler = NavigationInstance.instance.RecordTimer
		timers = []
		removed = False
		for timer in recordHandler.timer_list:
			if timer and timer.service_ref:
				if str(timer.name) == entry_dict['name'] and str(timer.description) == entry_dict['description']:
					#if int(timer.begin) == entry_dict['timer_starttime'] and str(timer.service_ref) == entry_dict['channelref']:
					#	removed = "removed"
					#	recordHandler.removeEntry(timer)
					#	return True
					if str(timer.service_ref) == entry_dict['channelref']:
						removed = "removed"
						recordHandler.removeEntry(timer)
						removed = True
		return removed
		
		
		
		
	@staticmethod	
	def addTimer(session, serviceref, begin, end, name, description, disabled, justplay, afterevent, dirname, tags, repeated, logentries=None, eit=0):
	
		recordHandler = NavigationInstance.instance.RecordTimer
		
		msgTimeout = config.plugins.skyrecorder.msgtimeout.value
			
		if not dirname:
			try:
				dirname = config.plugins.skyrecorder.anytimefolder.value
			except Exception:
				dirname = preferredTimerPath()
	
		print "mao1", dirname
			
		try:
			timer = RecordTimerEntry(
				ServiceReference(serviceref),
				begin,
				end,
				name,
				description,
				eit,
				disabled,
				justplay,
				afterevent,
				dirname=dirname,
				tags=tags)
	
			timer.repeated = repeated
	
			if logentries:
				timer.log_entries = logentries
				print "rrgggg"
				
			conflicts = recordHandler.record(timer)
			if conflicts:
				errors = []
				for conflict in conflicts:
					errors.append(conflict.name)
	
				print "duuuupppppppeeeeee"
				return {
					"result": False,
					"message": "Conflicting Timer(s) detected! %s" % " / ".join(errors)
				}
		except Exception, e:
			print "adupppeee"
			print e
			return {
				"result": False,
				"message": "Could not add timer '%s'!" % name
			}
			
		print "[skyrecorder] timer added."
		if config.plugins.skyrecorder.silent_timer_mode.value == False:
			message = session.open(MessageBox, _("%s - %s added.\nZiel: %s") % (name, description, dirname), MessageBox.TYPE_INFO, timeout=msgTimeout)
		
		return {
			"result": True,
			"message": "Timer '%s' added" % name
		}
	
					
		