#-*- coding: utf-8 -*-
def buildSkydb(target=None,rebuild=False,backup=True):
	
	import os
	import sys
	import sqlite3
	import datetime
	import time
	
	databaseName = 'skydb.db'
	debugprefix = '[SkyRecorder]'
	
	if not target:
		my_path = os.path.dirname(os.path.abspath(__file__)) + '/'
		my_anytime_path=os.path.dirname(os.path.abspath(my_path)) + '/skyrecorder/'
		my_db_path = my_anytime_path + 'skydb.db'
	else:
		if os.path.isdir(target):
			if target[-1:] != "/":
				target += "/"
			my_db_path = target + databaseName
		elif not os.path.isdir(target) and os.path.exists(target):
			my_path = os.path.dirname(os.path.abspath(target)) + '/'
			my_db_path = my_path + databaseName
		elif not os.path.exists(target) and not os.path.isdir(target):
			my_db_path = target
			
	print my_db_path


	if os.path.exists(my_db_path) and backup is True:
		now = datetime.datetime.now()
		now = int(time.mktime(now.timetuple()))
		skydb_backupfile = my_db_path + "_bak_" + str(now)
		
		print "{0} erstelle Backup in '{1}'".format(debugprefix,skydb_backupfile)
		
		# build backup file by renaming the old one
		try:
			os.rename(my_db_path, skydb_backupfile)
		except Exception:
			sys.exc_clear()
			print "{0} ERROR: could not create backup file '{1}'. Is the file in use?".format(debugprefix,skydb_backupfile)
			return False
	
	if os.path.exists(my_db_path) and rebuild is False:
		print "{0} Datenbankdatei '{1}' existiert schon".format(debugprefix,my_db_path)
		return False
	
	if os.path.exists(my_db_path) and rebuild is True:
		try:
			os.remove(my_db_path)
		except Exception:
			sys.exc_clear()
			return False
	
	print "{0} skydb databasefile '{1}'".format(debugprefix,my_db_path)
	print "{0} creating database".format(debugprefix)
		
	connection=sqlite3.connect(my_db_path)
	connection.text_factory = str #we need to make use of utf-8 encoding for the database connection. Otherwise unicode would be the default
	curser=connection.cursor()

	print "{0} creating table: added".format(debugprefix)
	curser.execute("""CREATE TABLE [added] (
		[id_added] INTEGER  NOT NULL PRIMARY KEY,
		[title] TEXT  NULL,
		[description] TEXT  NULL,
		[id_channel] INTEGER  NULL,
		[id_genre] INTEGER  NULL,
		[begin] INTEGER  NULL,
		[end] INTEGER  NULL,
		[serviceref] TEXT  NULL,
		[location] TEXT  NULL,
		[recordedfile] TEXT  NULL
	)""")

	print "{0} creating table: channel".format(debugprefix)
	curser.execute("""CREATE TABLE [channel] (
		[id_channel] INTEGER  NULL PRIMARY KEY,
		[channel] TEXT  NULL,
		[channel_stb] TEXT  NULL,
		[status] TEXT  NULL,
		[position] INTEGER  NULL,
		[channel_id_sky] INTEGER  NULL
	)""")
	
	print "{0} creating table: skip".format(debugprefix)
	curser.execute("""CREATE TABLE [skip] (
		[id_skip] INTEGER  NULL PRIMARY KEY,
		[skipword] TEXT  NULL,
		[status] TEXT  NULL
	)""")

	print "{0} creating table: groups".format(debugprefix)
	curser.execute("""CREATE TABLE [groups] (
		[id_groups] INTEGER  PRIMARY KEY NOT NULL,
		[groupname] TEXT  NULL,
		[status] TEXT  NULL,
		[position] INTEGER  NULL
	)""")

	print "{0} creating table: genre".format(debugprefix)
	curser.execute("""CREATE TABLE [genre] (
		[id_genre] INTEGER  NOT NULL PRIMARY KEY,
		[genre] TEXT  NULL,
		[status] TEXT  NULL,
		[position] INTEGER  NULL
	)""")

	print "{0} creating table: genregroup".format(debugprefix)
	curser.execute("""CREATE TABLE [genregroup] (
		[id_genregroup] INTEGER  NOT NULL PRIMARY KEY,
		[id_genre] INTEGER  NULL,
		[id_groups] INTEGER  NULL,
		FOREIGN KEY(id_genre) REFERENCES genre(id_genre),
		FOREIGN KEY(id_groups) REFERENCES groups(id_groups)
	)""")

	print "{0} creating table: events".format(debugprefix)
	curser.execute("""CREATE TABLE [events] (
		[id_events] INTEGER  PRIMARY KEY NULL,
		[title] TEXT  NULL,
		[description] TEXT  NULL,
		[sky_id] TEXT  NULL,
		[image] TEXT  NULL,
		[id_channel] INTEGER  NULL,
		[id_genre] INTEGER  NULL,
		[status] TEXT  NULL,
		FOREIGN KEY(id_channel) REFERENCES channel(id_channel),
		FOREIGN KEY(id_genre) REFERENCES genre(id_genre)
	)""")

	print "{0} creating table: eventslist".format(debugprefix)
	curser.execute("""CREATE TABLE [eventslist] (
		[id_eventslist] INTEGER  NOT NULL PRIMARY KEY,
		[dayname] TEXT  NULL,
		[datum] TEXT  NULL,
		[starttime] INTEGER  NULL,
		[endtime] INTEGER  NULL,
		[status] TEXT  NULL,
		[id_events] INTEGER  NULL,
		FOREIGN KEY(id_events) REFERENCES events(id_events)
	)""")

	print "{0} creating table: eventdetails".format(debugprefix)
	curser.execute("""CREATE TABLE [eventdetails] (
		[id_eventdetails] INTEGER  PRIMARY KEY NOT NULL,
		[id_events] INTEGER  NULL,
		[handlung] TEXT  NULL,
		[is_hd] INTEGER NULL,
		[is_169] INTEGER NULL,
		[is_dolby] INTEGER NULL,
		[is_dualch] INTEGER NULL,
		[highlight] INTEGER NULL,
		[live] INTEGER NULL,
		[is_last] INTEGER NULL,
		[is_3d] INTEGER NULL,
		[is_ut] INTEGER NULL,
		[is_new] INTEGER NULL,
		FOREIGN KEY(id_events) REFERENCES events(id_events)
	)""")
	
	print "{0} creating table: eventcover".format(debugprefix)
	curser.execute("""CREATE TABLE [eventcover] (
		[id_eventcover] INTEGER  PRIMARY KEY NOT NULL,
		[id_events] INTEGER  NULL,
		[cover] BLOB  NULL,
		FOREIGN KEY(id_events) REFERENCES events(id_events)
	)""")
	

	### Tigger
	print "{0} creating trigger".format(debugprefix)
	curser.execute("""CREATE TRIGGER update_events_status AFTER UPDATE ON eventslist 
		BEGIN
			UPDATE events SET status = new.status WHERE id_events = new.id_events;
  		END""")

		
	### insert defaults
	print "{0} inserting default channellist".format(debugprefix)
	channelset = (
		('Sky Cinema','Sky Cinema','False',0,55),
		('Sky Cinema +1','Sky Cinema +1','False',0,57),
		('Sky Cinema +24','Sky Cinema +24','False',0,58),
		('Sky Action','Sky Action','False',0,59),
		('Sky Comedy','Sky Comedy','False',0,61),
		('Sky Emotion','Sky Emotion','False',0,62),
		('Sky Nostalgie','Sky Nostalgie','False',0,63),
		('Sky Hits','Sky Hits','False',0,64),
		('Disney Cinemagic','Disney Cinemagic','False',0,66),
		('MGM','MGM','False',0,68),
		('MGM HD','MGM HD','False',0,160),
		('E! Entertainm. HD','E! Entertainm. HD','False',0,117),
		('Sky Sport News','Sky Sport News','False',0,21),
		('Sky Sport News HD','Sky Sport News HD','False',0,17),
		('Sky Sport Austria','Sky Sport Austria','False',0,47),
		('Discovery Channel','Discovery Channel','False',0,82),
		('National Geographic','National Geographic','False',0,80),
		('National Geographic Wild','NatGeo Wild','False',0,87),
		('Spiegel Geschichte','Spiegel Geschichte','False',0,84),
		('motorvision TV','Motorvision TV','False',0,52),
		('Sky Krimi','Sky Krimi','False',0,1),
		('RTL Crime','RTL Crime','False',0,7),
		('13th Street','13th Street','False',0,9),
		('13th Street HD','13th Street HD','False',0,116),
		('Syfy','Syfy','False',0,8),
		('Syfy HD','Syfy HD','False',0,115),
		('FOX Serie','Fox Serie','False',0,3),
		('TNT Serie','TNT Serie','False',0,5),
		('RTL Passion','RTL Passion','False',0,11),
		('Heimatkanal','Heimatkanal','False',0,72),
		('Disney Channel','Disney Channel','False',0,91),
		('Disney Channel HD','Disney Channel HD','False',0,90),
		('MTV Live HD','MTV Live HD','False',0,101),
		('Disney XD','Disney XD','False',0,93),
		('Disney Junior','Disney Junior','False',0,92),
		('Junior','Junior','False',0,96),
		('Goldstar TV','Goldstar TV','False',0,98),
		('Classica','Classica','False',0,99),
		('Beate-Uhse.TV','Beate-Uhse.TV','False',0,73),
		('Sky Atlantic HD','Sky Atlantic HD','False',0,2),
		('Sky Cinema HD','Sky Cinema HD','False',0,56),
		('Sky Action HD','Sky Action HD','False',0,60),
		('Sky Hits HD','Sky Hits HD','False',0,65),
		('Sky Sport HD 1','Sky Sport HD 1','False',0,18),
		('Sky Sport HD 2','Sky Sport HD 2','False',0,19),
		('Sky Select HD','Sky Select HD','False',0,113),
		('Sky Sport HD Extra','Sky Sport HD Extra','False',0,20),
		('Sky 3D','Sky 3D','False',0,54),
		('Disney Cinemagic HD','Disney Cinemagic HD','False',0,67),
		('Discovery Channel HD','Discovery HD','False',0,83),
		('FOX HD','Fox HD','False',0,4),
		('National Geographic HD','NatGeo HD','False',0,81),
		('National Geographic Wild HD','Nat Geo Wild HD','False',0,88),
		('History Channel HD','History HD','False',0,86),
		('TNT Serie HD','TNT Serie HD','False',0,6),
		('Eurosport HD','Eurosport HD','False',0,51),
		('ESPN America HD','ESPN America HD','False',0,49),
		('Sport1+ HD','Sport 1+ HD','False',0,53),
		('Sat.1 Emotions','Sat.1 Emotions','False',0,15),
		('AXN Action','AXN','False',0,12),
		('AXN HD','AXN HD','False',0,13),
		('TNT Film','TNT Film (TCM)','False',0,69),
		('kabel eins classics','kabel eins classics','False',0,71),
		('Kinowelt TV','Kinowelt TV','False',0,70),
		('Romance TV','Romance TV','False',0,16),
		('Nicktoons (S)','Nicktoons','False',0,97),
		('Boomerang','Boomerang','False',0,94),
		('Cartoon Network (S)','Cartoon Network','False',0,95),
		('History Channel','History','False',0,85),
		('Biography Channel','The Biography Channel','False',0,89),
		('RTL Living','RTL Living','False',0,10),
		('ANIMAX','Animax','False',0,14),
		('MTV Germany','MTV','False',0,100),
		('EuroSport 2 Deutschland','Eurosport 2 Deutschland','False',0,50),
		('ESPN America (S)','ESPN America','False',0,48),
		('sportdigital','sportdigital','False',0,114),
		('Sky Sport 1','Sky Sport 1','False',0,34),
		('Sky Sport 2','Sky Sport 2','False',0,35),
		('Sky Sport 3','Sky Sport 3','False',0,36),
		('Sky Sport 4','Sky Sport 4','False',0,37),
		('Sky Sport 5','Sky Sport 5','False',0,38),
		('Sky Sport 6','Sky Sport 6','False',0,39),
		('Sky Sport 7','Sky Sport 7','False',0,40),
		('Sky Sport 8','Sky Sport 8','False',0,41),
		('Sky Sport 9','Sky Sport 9','False',0,42),
		('Sky Sport 10','Sky Sport 10','False',0,43),
		('Sky Sport 11','Sky Sport 11','False',0,44),
		('Sky Sport 12','Sky Sport 12','False',0,45),
		('Sky Sport 13','Sky Sport 13','False',0,46),
		('Sky Select','Sky Select','False',0,102),
		('Sky Select 1','Sky Select 1','False',0,102),
		('Sky Select 2','Sky Select 2','False',0,103),
		('Sky Select 3','Sky Select 3','False',0,104),
		('Sky Select 4','Sky Select 4','False',0,105),
		('Sky Select 5','Sky Select 5','False',0,106),
		('Sky Select 6','Sky Select 6','False',0,107),
		('Sky Select 7','Sky Select 7','False',0,108),
		('Sky Select 8','Sky Select 8','False',0,109),
		('Sky Select 9','Sky Select 9','False',0,110),
		('Sky Select Event A','Sky Select Event A','False',0,111), 
		('Sky Select Event B','Sky Select Event B','False',0,112),
		('Sky Bundesliga','Sky Bundesliga', 'False',0,22),
		('Sky Bundesliga 1','Sky Bundesliga 1','False',0,23),
		('Sky Bundesliga 2','Sky Bundesliga 2','False',0,24),
		('Sky Bundesliga 3','Sky Bundesliga 3','False',0,25),
		('Sky Bundesliga 4','Sky Bundesliga 4','False',0,26),
		('Sky Bundesliga 5','Sky Bundesliga 5','False',0,27),
		('Sky Bundesliga 6','Sky Bundesliga 6','False',0,28),
		('Sky Bundesliga 7','Sky Bundesliga 7','False',0,29),
		('Sky Bundesliga 8','Sky Bundesliga 8','False',0,30),
		('Sky Bundesliga 9','Sky Bundesliga 9','False',0,31),
		('Sky Bundesliga 10','Sky Bundesliga 10','False',0,32),
		('Sky Bundesliga 11','Sky Bundesliga 11','False',0,33)
	)
	curser.executemany("INSERT OR IGNORE INTO channel (channel,channel_stb,status,position,channel_id_sky) values (?,?,?,?,?)", channelset)
	
	print "{0} inserting default genrelist".format(debugprefix)
	genreset = (
		(1,'Anwaltsserie','True'),(2,'Serie','True'),(3,'Miniserie','True'),(4,'Mystery-Serie','True'),(5,'Real-Life-Show','False'),
		(6,'Agentenserie','True'),(7,'Dramaserie','True'),(8,'Drama','True'),(9,'Action','True'),(10,'Dokumentarserie','True'),
		(11,'Dokumentation','True'),(12,'Komödie','True'),(13,'Tierdokumentation','True'),(14,'Horrorfilm','True'),
		(15,'Horrorserie','True'),(16,'Actionfilm','True'),(17,'Mysteryfilm','True'),(18,'Mysterythriller','True'),
		(19,'Animation','True'),(20,'Thriller','True'),(21,'Western','True'),(22,'Kriminalfilm','True'),(23,'Krimiserie','True'),
		(24,'Abenteuerfilm','True'),(25,'Science-Fiction','True'),(26,'Liebesfilm','True'),(27,'Zeichentrick','True'),
		(28,'Zeichentrickserie','True'),(29,'Politthriller','True'),(30,'Jugendfilm','True'),(31,'Fantasy-Action','True'),
		(32,'Monumentalfilm','True'),(33,'Animationsfilm','True'),(34,'Psychothriller','True'),(35,'Fantasy','True'),
		(36,'Liebeskomödie','True'),(37,'Horrorkomödie','True'),(38,'Actionthriller','True'),(39,'Biografie','True'),
		(40,'Romantikkomödie','True'),(41,'Actionkomödie','True'),(42,'Kriegsfilm','True'),(43,'Literaturverfilmung','True'),
		(44,'Computeranimation','True'),(45,'Show','True'),(46,'Sportlerdrama','True'),(47,'Talk','False'),(48,'Talkshow','False'),
		(49,'-','True'),(50,'Comic','True'),(51,'Science-Fiction-Horror','True'),(52,'Sitcom','True'),
		(53,'Spielfilm','True'),(54,'Kinderfilm','True'),
		(55,'Magazin','False'),(56,'Zeichentrick/Animation','True'),
		(57,'Familienfilm','True'),(58,'Dokumentarfilm','True'),(59,'Milieustudie','True'),
		(60,'Romanze','True'),(61,'Wrestling','False'),(62,'Erotikfilm','True')
	)
	curser.executemany("INSERT INTO genre (id_genre,genre,status) values (?,?,?)", genreset)

	print "{0} inserting default groups".format(debugprefix)
	groupset = (
		(1,'Film','True',1),
		(2,'Serie','True',2),
		(3,'Dokumentation','True',3),
		(4,'Sport','True',4),
		(5,'Sonstige','True',5),
		(6,'Sky Select','False',6)
	)
	curser.executemany("INSERT INTO groups (id_groups,groupname,status,position) values (?,?,?,?)", groupset)
	
	print "{0} inserting default genre-group-list".format(debugprefix)
	genregroupset = (
		(1,2),(2,2),(3,2),(4,2),(5,5),(6,2),(7,2),(8,1),(9,1),(10,2),
		(11,3),(12,1),(13,3),(14,1),(15,2),(16,1),(17,1),(18,1),(19,5),(20,1),
		(21,1),(22,1),(23,2),(24,1),(25,1),(26,1),(27,5),(28,2),(29,1),(30,1),
		(31,1),(32,1),(33,1),(34,1),(35,1),(36,1),(37,1),(38,1),(39,5),(40,1),
		(41,1),(42,1),(43,1),(44,5),(45,5),(46,1),(47,5),(48,5),(49,5),(50,5),
		(51,1),(52,5),(53,1),(54,1),(55,5),(56,1),(57,1),(58,3),(59,1),(60,1),
		(61,4),(62,1)
	)
	curser.executemany("INSERT OR IGNORE INTO genregroup (id_genre,id_groups) values (?,?)", genregroupset)
	
	try:
		connection.commit()
	except Exception:
		sys.exc_clear()
		print "{0} ERROR: could not commit changes".format(debugprefix)
		connection.close()
		return False
		
	connection.close()
	print "{0} done".format(debugprefix)
	return True

# start here
#buildSkydb(rebuild=True,backup=True)

