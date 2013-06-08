#-*- coding: utf-8 -*-
from Screens.ChannelSelection import service_types_tv
from enigma import eServiceCenter, eServiceReference
from ServiceReference import ServiceReference
import os, sys
from random import randint

from Components.config import config
from time import localtime, strftime, time
import datetime, time

# for timer names
from Tools import ASCIItranslit
# for timer xml
from Tools.XMLTools import stringToXML
import xml.etree.cElementTree




def checkForInternet():
	import urllib2
	try:
		response=urllib2.urlopen('http://www.google.de',timeout=3)
		return True
	except urllib2.URLError as err:	pass
	return False
	


def nonHDeventList():
	list = ['Eurosport HD']
	return list

#def convertData(text):
#	return text
#	if isinstance(text, dict):
#		return {convertData(key): convertData(value) for key, value in text.iteritems()}
#	elif isinstance(text, list):
#		return [convertData(element) for element in text]
#	elif isinstance(text, unicode):
#		#return decodeHtml(text.encode("utf-8"))
#		return text.encode("utf-8")
#	else:
#		return text
			

def getServiceList(ref):
	root = eServiceReference(str(ref))
	serviceHandler = eServiceCenter.getInstance()
	return serviceHandler.list(root).getContent("SN", True)

def getTVBouquets():
	return getServiceList(service_types_tv + ' FROM BOUQUET "bouquets.tv" ORDER BY bouquet')


def buildSkyChannellist():
	sky_chlist = None
	sky_chlist = []
	print "[SkyRecorder] read channellist.."
	tvbouquets = getTVBouquets()
	print "[SkyRecorder] found %s bouquet: %s" % (len(tvbouquets), tvbouquets)

	for bouquet in tvbouquets:
		bouquetlist = []
		bouquetlist = getServiceList(bouquet[0])
		for (serviceref, servicename) in bouquetlist:
			#print servicename, serviceref
			sky_chlist.append((servicename, serviceref))
	return sky_chlist


def getChannelByRef(sky_chlist,serviceref):
	for (channelname,channelref) in sky_chlist:
		if channelref == serviceref:
			return channelname


def decodeHtml(text):
	if not text or text == "":
		return ""
		
	#text1 = text.decode("iso-8859-15")
	#text = text1.encode("utf-8")
	
	#text = text.decode('utf-8')
	#text = str(text)
	
	#import HTMLParser
	#h = HTMLParser.HTMLParser()
	#text = h.unescape(text)
	#del(h)
	#return text #text.decode('utf-8') #text.decode('raw-unicode-escape')
	
	text = text.encode('utf-8')
	import re
	import HTMLParser
	h = HTMLParser.HTMLParser()
	
	regexp = "&.+?;"
	list_of_html = re.findall(regexp, text)
	for e in list_of_html:
		unescaped = h.unescape(e) #finds the unescaped value of the html entity
		text = text.replace(e, unescaped) #replaces html entity with unescaped value
	del(h)
	return text.encode('utf-8')
	
	text = text.replace('&amp;','&').replace('&#038;','&').replace('&#38;','&')
	text = text.replace('&szlig;','ß')
	text = text.replace('&auml;','ä').replace('&Auml;','Ä').replace('&ouml;','ö')
	test = text.replace('&ouml;','Ö').replace('&uuml;','ü').replace('&Uuml;','Ü')
	text = text.replace('&#228;','ä').replace('&#246;','ö').replace('&#252;','ü').replace('&#223;','ß')
	text = text.replace('\u00c4','Ä').replace('\u00e4;',"ä").replace('\u00d6',"Ö").replace('\u00f6','ö')
	text = text.replace('\u00dc','Ü').replace('\u00fc',"ü").replace('\u00df',"ß")
	text = text.replace('&#196;','Ä').replace('&#228;',"ä").replace('&#214;',"Ö")
	text = text.replace('&#246;',"ö").replace('&#220;',"Ü").replace('&#252;',"ü")
	
	text = text.replace('&quot;','\"').replace('&gt;','\'').replace('&#8230;','...')
	text = text.replace('&#8222;',',').replace('&#8220;',"'").replace('&#8216;',"'").replace('&#8217;',"'").replace('&#8211;',"-")
	text = text.replace('&#8230;','...').replace('&#8217;',"'").replace('&#128513;',":-)").replace('&#8221;','"')
	text = text.replace('&#039;',"'")
	text = text.replace('<br />\n','').replace('Ã','ss')
	text = text.replace('&#39;',"'")
	
	#text = text.replace('Ö','Oe').replace('Ü',"Ue").replace('Ä',"Ae").replace('ö','oe').replace('ü','ue').replace('ä','ae')
	#text = text.replace('ß','ss')
	
	# something more special
	#text = text.replace('á','a')
	return text
	
	
def getHttpHeader():
	headers = {
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20100101 Firefox/19.0',
		'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Language': 'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3',
		'Accept-Encoding': 'gzip, deflate',
		'Content-Type':'application/x-www-form-urlencoded'}
	return headers

def getHttpHeader1():
	headers1 = {
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20100101 Firefox/19.0',
		'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Cache-Control': 'max-age=0',
		'Accept-Encoding': 'gzip, deflate',
		'Content-Type':'application/x-www-form-urlencoded',
		'Accept-Language': 'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3'}
	return headers1

def getHttpHeaderJSON():
	headers = {
		'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20100101 Firefox/19.0',
		'Accept':'application/json, text/javascript, */*; q=0.01',
		'Accept-Language':'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3'}
	return headers

def getHttpHeader2():
	headers2 = {
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20100101 Firefox/19.0',
		'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
		'Accept': 'image/jpeg; q=1, image/gif; q=0.2',
		'Accept-Language': 'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3'}
		
		#'Accept': 'image/jpeg; q=1, image/png; q=0.5, image/gif; q=0.2',
	return headers2

def getUserAgent():
	# get random user-agent string
	idx = randint(0, 13)
	agent = None
	agent = []
	agent.append({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17'})
	agent.append({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20100101 Firefox/19.0'})
	agent.append({'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100101 Firefox/11.0'})
	agent.append({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17'})
	agent.append({'User-Agent': 'Mozilla/5.0 (Windows; Windows NT 6.1) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2'})
	agent.append({'User-Agent': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'})
	agent.append({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5'})
	agent.append({'User-Agent': 'Mozilla/5.0 (Windows; Windows NT 6.1) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5'})
	agent.append({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0'})
	agent.append({'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0'})
	agent.append({'User-Agent': 'Opera/9.80 (Macintosh; Intel Mac OS X 10.7.4; U; en) Presto/2.10.229 Version/11.62'})
	agent.append({'User-Agent': 'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.10.229 Version/11.62'})
	agent.append({'User-Agent': 'Mozilla/5.0 (X11; Linux 3.5.4-1-ARCH i686; es) KHTML/4.9.1 (like Gecko) Konqueror/4.9'})
	agent.append({'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)'})
	
	# FIXME: getPage does not accept the full-agent dict, we have to return only the value, not key and value.
	try:
		return agent[idx]['User-Agent']
	except Exception:
		sys.exc_clear()
		return agent[2]['User-Agent']
	

def getPluginPath():
	return (os.path.dirname(sys.modules[__name__].__file__))


def setWecker(database_update_time,day_shift=False):
	today = datetime.datetime.today()
	alarm_hour, alarm_minute = database_update_time
	
	wecker = datetime.datetime(today.year,today.month, today.day, alarm_hour, alarm_minute, 0)
	if wecker < today or day_shift:
		wecker = wecker + datetime.timedelta(days=1)
		
	return int(time.mktime(wecker.timetuple()))

def getDayOfTheWeek(timestamp, as_day_short = True, my_local = "de_DE"):
	#import locale
	now = time.localtime(timestamp)
	timestamp = int(time.mktime(now))
	day = None
	#locale.setlocale(locale.LC_ALL, my_local)
	if as_day_short:
		index = (datetime.datetime.fromtimestamp(int(timestamp)).strftime('%w'))
		daylist = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
		day = daylist[int(index)]
	else:
		index = (datetime.datetime.fromtimestamp(int(timestamp)).strftime('%w'))
		daylist = ['Sonntag','Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag']
		day = daylist[int(index)]
	return day


def getDateFromTimestamp(timestamp):
	day = None
	now = time.localtime(timestamp)
	timestamp = int(time.mktime(now))
	day = (datetime.datetime.fromtimestamp(int(timestamp)).strftime('%d.%m.%y'))
	return day


def getTimeFromTimestamp(timestamp):
	mytime = None
	now = time.localtime(timestamp)
	timestamp = int(time.mktime(now))
	mytime = (datetime.datetime.fromtimestamp(int(timestamp)).strftime('%H:%M'))
	return mytime
	
def getDateTimeFromTimestamp(timestamp):
	mytime = None
	now = time.localtime(timestamp)
	timestamp = int(time.mktime(now))
	mytime = (datetime.datetime.fromtimestamp(int(timestamp)).strftime('%d.%m.%y %H:%M:%S'))
	return mytime
	
def getDateTimeFromTimestamp2(timestamp):
	mytime = None
	now = time.localtime(timestamp)
	timestamp = int(time.mktime(now))
	mytime = (datetime.datetime.fromtimestamp(int(timestamp)).strftime('%d.%m.%y %H:%M'))
	return mytime

def getCurrentTimestamp():
	#now = datetime.datetime.now()
	#return int(time.mktime(now.timetuple()))
	now = time.localtime()
	timestamp = int(time.mktime(now))
	return timestamp

def getEventAllowedRange(fromtime = 0, totime = 0, my_days = None, debugme = False):

	hx_hy = None
	set_hx_hy = None
	hour_range = None
	day_range = None
	
	hx_hy = range(0,24)
	days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
	day_range = days
	if my_days:
		my_days = my_days[1:-1].replace("'","").split(',')
		if "all" not in	my_days:
			day_range = list(set(days) & set(my_days))
	
	if fromtime < totime:
		set_hx_hy = range(fromtime,totime + 1)
		hour_range = list(set(hx_hy) & set(set_hx_hy))
	elif fromtime > totime:
		set_hx_hy = range(totime+1,fromtime)
		hour_range = list(set(hx_hy) ^ set(set_hx_hy))
	else:
		set_hx_hy = hx_hy
		hour_range = list(set(hx_hy) & set(set_hx_hy))
		
	# debug me
	if debugme:
		print "[skyrecorder] Tag 0-23..: " + str(hx_hy)
		print "[skyrecorder] von/bis...: " + str(set_hx_hy)
		print "[skyrecorder] Bereich...: " + str(hour_range)
	
	return [hour_range, day_range]
	
	
# for timer filepath settings
def getRecordFilename(title,description,begin,channel):
	
	begin_date = strftime("%Y%m%d %H%M", localtime(begin))
	begin_shortdate = strftime("%Y%m%d", localtime(begin))
			
	filename = begin_date + " - " + channel
	if title:
		if config.usage.setup_level.index >= 2: # expert+
			if config.recording.filename_composition.value == "short":
				filename = begin_shortdate + " - " + title
			elif config.recording.filename_composition.value == "long":
				filename += " - " + title + " - " + description
			else:
				filename += " - " + title # standard
		else:
			filename += " - " + title
	
	if config.recording.ascii_filenames.value:
		filename = ASCIItranslit.legacyEncode(filename)

	return filename



### parse timers.xml

def createTimerList(xml,sky_chlist):
	entry = None
	
	begin = int(xml.get("begin"))
	end = int(xml.get("end"))
	serviceref = ServiceReference(xml.get("serviceref").encode("utf-8"))
	description = xml.get("description").encode("utf-8")
	#repeated = xml.get("repeated").encode("utf-8")
	#disabled = long(xml.get("disabled") or "0")
	#justplay = long(xml.get("justplay") or "0")
	#afterevent = str(xml.get("afterevent") or "nothing")
	#afterevent = {
	#	"nothing": AFTEREVENT.NONE,
	#	"standby": AFTEREVENT.STANDBY,
	#	"deepstandby": AFTEREVENT.DEEPSTANDBY,
	#	"auto": AFTEREVENT.AUTO
	#	}[afterevent]
	#eit = xml.get("eit")
	#if eit and eit != "None":
	#	eit = long(eit);
	#else:
	#	eit = None
	location = xml.get("location")
	if location and location != "None":
		location = location.encode("utf-8")
	else:
		location = 'NULL'
	#tags = xml.get("tags")
	#if tags and tags != "None":
	#	tags = tags.encode("utf-8").split(' ')
	#else:
	#	tags = None

	name = xml.get("name").encode("utf-8")
	#filename = xml.get("filename").encode("utf-8")
	
	# id_added,title,description,id_channel,id_genre,begin,end,serviceref,location,recordedfile
	recordedfile = 'NULL'
	if serviceref:
		channel = getChannelByRef(sky_chlist,str(serviceref))
		if channel:
			recordedfile = getRecordFilename(name,description,begin,channel)
	entry = {
			"title":name,
			"description": description,
			"id_channel": 'NULL',
			"channel": channel,
			"id_genre": 'NULL',
			"begin": begin,
			"end": end,
			"serviceref": serviceref,
			"location": location,
			"recordedfile": recordedfile
			}
	return entry

def loadTimerList(sky_chlist,Filename="/etc/enigma2/timers.xml"):
	# TODO: PATH!
	try:
		doc = xml.etree.cElementTree.parse(Filename)
	except SyntaxError:
		print "timers.xml failed to load!"
	except IOError:
		print "timers.xml not found!"
		return

	root = doc.getroot()
		
	timerList = []
	for timer in root.findall("timer"):
		timerList.append(createTimerList(timer,sky_chlist))
		
	return timerList
### end parse timers.xml

