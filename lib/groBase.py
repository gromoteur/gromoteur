#!/usr/bin/python
# -*- coding: utf-8 -*-

try:
    import pysqlite2.dbapi2 as sqlite3
except ImportError:
    import sqlite3

#from os       import environ
#from sys      import exit
import sys, os, re, signal
from time import time
#import urllib
#from _mysql_exceptions import OperationalError
from configobj import ConfigObj

from threading import Thread
from queue import Queue
#from htmlPage import sentenceSplit

signal.signal(signal.SIGINT, signal.SIG_DFL) # allows stopping all by ctrl-c

verbose=False
#verbose=True

defaultSentenceSplit="(\s*\n+\s*|(?<!\s[A-ZÀÈÌÒÙÁÉÍÓÚÝÂÊÎÔÛÄËÏÖÜÃÑÕÆÅÐÇØ])[\?\!？\!\.。！……]+\s+|\s+\|\s+|[？。！……]+)"

class GroBase(Thread):
	"""
	GroBase is an independent thread giving access to gromoteur's databases
	
	it has to run in an independent thread because a sqlite db cannot be modified from different threads
	
	a gromoteur database has the following tables
	
	information: ( nbPages INTEGER, nbSentences INTEGER, nbCharacters INTEGER, nbSearchEngineAccesses INTEGER, comments TEXT , configfile TEXT, lastaccess INTEGER )
	linksDone: list of urls
	linksTodo: triple: url, level, origine
	sources: the source information:  (url VARCHAR, "linkOrigin_rowid" INTEGER, nbSentences INTEGER, nbCharacters INTEGER, time INTEGER, source TEXT)
	textcolumns: names of columns: standard: title, text
	texts: the cleaned text segments. standard: title, text
	textualcolumns: textualid, columnid
	textualizations: name of views	
	
	"""		
	textual=['standard', 'texts'] #each time we add a new textualization,we make a new view and  the view is according to what the user has done
	textualcolumns=[] #store the information in the textualcolumns  [textualid,columnid,columnname]
	textualizations=[] #[textualid,name]
	
	
	
	def __init__(self, corpusName):
		super(GroBase, self).__init__()
		self.name=corpusName
		
		sampleCorpusPath=os.path.join("corpora",str(corpusName)+".sqlite" )
		if os.path.isfile(sampleCorpusPath):
			self.filename = sampleCorpusPath
		else:
			self.filename = os.path.join(os.path.expanduser('~'),"gromoteur","corpora",str(corpusName)+".sqlite" )
		self.reqs=Queue()
		self.last=None
		#firsttime=False
		self.repairedAlredy=0
		self.sentenceSplit=self.getSentenceSplit()
		self.infoTableCreation='''CREATE TABLE IF NOT EXISTS information ( 
						nbPages INTEGER, 
						nbSentences INTEGER, 
						nbCharacters INTEGER, 
						nbSearchEngineAccesses INTEGER, 
						nbLinksToDo INTEGER, 
						nbLinksDone INTEGER, 
						comments TEXT, 
						configfile TEXT, 
						lastaccess INTEGER ) ;'''
		if  not os.path.exists(self.filename):
			self.newGroBase()
		self.errorState=None
		self.start()
		self.readInfo()
		self.col2ty={"rowid":"nb", "url":"txt",  "time":"time", "linkOrigin":"nb", "text":"txt" }
		if verbose: print("GroBase init terminated. ))))))))")

	
	def run(self):
		self.db= sqlite3.connect(self.filename)
		self.cursor = self.db.cursor()
		
		while True:
			req, arg, res = self.reqs.get()
			id=None
			if req=='--close--': break
			elif req=="--page--":
				page, origin, dataOverwrite  = arg
				if dataOverwrite:
					self.cursor.execute("SELECT rowid, nbSentences, nbCharacters from sources WHERE url=? LIMIT 1;",(page.url, ))
					for a in self.cursor:
						id, negNbSentences, negNbWords=a
						self.cursor.execute("""UPDATE sources 
								set linkOrigin_rowid=?, source=?, nbSentences=?, nbCharacters=?, time=?
								WHERE url=? 
								""", (origin, page.source, page.nbSentences, page.nbWords, time(), page.url , ) )
						self.cursor.execute("UPDATE texts set text=?, nbSentences=?, nbCharacters=? WHERE sourceid=? AND textualid=? AND columnid=?", (page.title,page.titleSenNum, page.titleWordNum, id,1,1, ) )
						self.cursor.execute("UPDATE texts set text=? , nbSentences=?, nbCharacters=? WHERE sourceid=? AND textualid=? AND columnid=? ", (page.text, page.nbSentences, page.nbWords, id, 1,2, ) )
				if not dataOverwrite or not id:
					self.cursor.execute("""INSERT INTO sources( url, source, linkOrigin_rowid, time, nbSentences, nbCharacters) VALUES (?,?,?,?,?,?) 
							""", (page.url, page.source, origin, time(),page.nbSentences, page.nbWords, ) )
					id, = self.cursor.execute('SELECT last_insert_rowid()').fetchone()
					self.cursor.execute("INSERT INTO texts (sourceid,textualid, columnid, text,nbSentences,nbCharacters) VALUES (?,?,?,?,?,?) ;", (id, 1,1,page.title, page.titleSenNum, page.titleWordNum, ) )
					self.cursor.execute("INSERT INTO texts (sourceid,textualid, columnid, text,nbSentences,nbCharacters) VALUES (?,?,?,?,?,?) ;", (id, 1,2,page.text, page.nbSentences, page.nbWords, ) )
					negNbSentences, negNbWords=None, None
				res.put( (id, negNbSentences, negNbWords) )
				try:self.db.commit()
				except:pass
			elif req=="--links--":
				# arg is linksDone, res= linksTodo
				self.cursor.executemany("insert into linksDone values  (?) ;", [ (l, ) for l in arg] )
				self.cursor.executemany("insert into linksTodo values  (?,?,?) ;", res)
				
			elif req=="--script--":
				self.cursor.executescript(arg)
			elif req=="--commit--":
				self.tryCommit()
				#TODO: think of ways to catch an exception in this thread in the main window try: except:
			else:
				if verbose: print("groBase, executing", req, arg) 
				try:
#					if req.endswith(";;"):self.cursor.executescript(req)
#					else:
					self.cursor.execute(req, arg)
				except Exception as e:
					if verbose : 
						print(req, arg)
						print("error",e)
				if res:
					for rec in self.cursor:
						res.put(rec)
					res.put('--no more--')
			# try: 
				# print "committing"
				# # self.db.commit()
			# except:
				# if verbose:print "couldn't commit"
				# else: pass
			
		self.tryCommit()
		self.db.close()
		
	def execute(self, req, arg=None, res=None):
		self.reqs.put((req, arg or tuple(), res))
		
	def select(self, req, arg=None):
		res=Queue()
		self.execute(req, arg, res)
		while True:
			#print "___",res
			rec=res.get()
			if rec=='--no more--': break
			yield rec
			
	def close(self):
		self.execute('--close--')
		
	
	def enterSource(self, page, origin, dataOverwrite=False):
		"""
		linkOrigin  >0 : rowid of source url that provided the link
		# linkOrigin -1 : bing
		# linkOrigin 0 : directly from config file
		
		"""
		if verbose:  
			print("enterSource", page.url.encode("utf-8"), dataOverwrite)
			
		res=Queue()
		self.execute("--page--", (page, origin, dataOverwrite ), res)
		rec=res.get()

		id, negNbSentences, negNbWords=rec
		self.execute('--commit--')
		return id, negNbSentences, negNbWords
	
	def tryCommit(self):
		try:
			self.db.commit()
			self.errorState=None
		except sqlite3.OperationalError as e:  
			self.errorState=str(e)
			print("groBase",self.errorState)
		except: 
			print("Unexpected error:", sys.exc_info()[0])
			raise
	
	###########################################
	### new base
	###########################################
	
	def newGroBase(self):
		self.db = sqlite3.connect(self.filename)
		self.cursor = self.db.cursor()
		
		self.cursor.execute(self.infoTableCreation)
		self.cursor.execute("INSERT INTO information( nbPages, nbSentences, nbCharacters, nbSearchEngineAccesses, nbLinksToDo, nbLinksDone, comments, configfile, lastaccess) VALUES (?,?,?,?,?,?,?,?,?) ",
					(0, 0, 0, 0,0,0,"no comment yet", "none", time(), ))
		self.cursor.execute('''CREATE TABLE sources (
			url VARCHAR, 
			"linkOrigin_rowid" INTEGER, 
			nbSentences INTEGER, 
			nbCharacters INTEGER, 
			time INTEGER, 
			source TEXT, 
			CONSTRAINT "sources_linkOrigin_id_fk" FOREIGN KEY("linkOrigin_rowid") REFERENCES sources (id) )''')

		#change the table text
		#self.cursor.execute('''CREATE VIRTUAL TABLE texts USING fts4( sourceid,textualid,columnid, text,nbSentences,nbCharacters) ;''')
		self.cursor.execute('''CREATE TABLE texts ( 
			sourceid INTEGER,
			textualid INTEGER,
			columnid INTEGER, 
			text TEXT,
			nbSentences INTEGER,
			nbCharacters INTEGER, 
			primary key (sourceid,textualid,columnid)) ;''')
		#the format to store the information
		self.cursor.execute('''CREATE TABLE IF NOT EXISTS textualizations ( id INTEGER PRIMARY KEY, name VARCHAR); ''')
		#store the column name to each textualizations
		self.cursor.execute('''CREATE TABLE IF NOT EXISTS textcolumns ( id INTEGER PRIMARY KEY, name VARCHAR); ''')
		#to store the relationship  between  textualizations  and textcolumns
		self.cursor.execute('''CREATE TABLE IF NOT EXISTS textualcolumns (textualid INTEGER, columnid INTEGER); ''')
		
		self.execute("CREATE TABLE linksTodo ( linksTodo VARCHAR, level INTEGER, origin INTEGER ) ;")
		self.execute("CREATE TABLE linksDone ( linksDone VARCHAR ) ;")
		
		standardtextfields=["title", "text"]
		for n in standardtextfields:
			self.cursor.execute("INSERT INTO textcolumns( name) VALUES (?) ",(n, ))
		
		self.makeTextualization( "standard", standardtextfields)
	
		self.db.commit()	
		if verbose: print("created", self.name)
	
	
		
		
		
	def makeTextualization(self, textualizationName, columnlist):
		"""
		name of textualizations
		columnlist: list of fields to create
		change the way to make textualization
		"""
		self.cursor.execute("INSERT INTO textualizations(name) VALUES (?) ",(textualizationName, ))
		textualid, = self.cursor.execute("select id from textualizations  where name = ? ",(textualizationName, )).fetchone()
		for column in columnlist:
			columnid, =  self.cursor.execute("select id from textcolumns where name = ? ",(column, )).fetchone()
			self.cursor.execute("INSERT INTO textualcolumns( textualid , columnid ) VALUES (?,?) ",(textualid, columnid, ))
				
		c="create view "+textualizationName+" as select s.rowid, s.url, s.time, s.linkOrigin_rowid, texts1.nbCharacters as title_nbCharacters, texts1.nbSentences as title_nbSentences,"
		c+="texts1.text as title, texts2.nbCharacters as text_nbCharacters, texts2.nbSentences as text_nbSentences,texts2.text as text  from sources s, texts texts1, texts texts2 "
		c+="where s.rowid = texts1.sourceid and  texts1.columnid=1 and texts2.columnid=2 and texts1.sourceid = texts2.sourceid"

		self.cursor.execute(c)
		self.db.commit()
	
	# def deleteTextualization(self, textualizationName):
# #		textualid, = self.cursor.execute("select id from textualizations where name = ? ",(textualizationName, )).fetchone()
		# try: 
			# textualid, = self.select("select id from textualizations where name = ? ;", (textualizationName, )).next()

			# self.execute("DELETE FROM texts WHERE textualid=?;", str(textualid))
			# self.execute("DELETE FROM textualcolumns WHERE textualid=?;", str(textualid))
			# self.execute("DROP VIEW if exists "+ textualizationName+ ";")
			# self.execute("DELETE FROM textualizations WHERE id=?;", str(textualid))
			# self.execute('--commit--')

		# except:
				# print "couldn't delete textualization", textualizationName
#			
	
	###########################################
	### deleting reducing
	###########################################
	
	def deleteTextualization(self, textualizationName):
#		textualid, = self.cursor.execute("select id from textualizations where name = ? ",(textualizationName, )).fetchone()
		try: 
			textualid, = next(self.select("select id from textualizations where name = ? ;", (textualizationName, )))

			self.execute("DELETE FROM texts WHERE textualid=?;", str(textualid))
			self.execute("DELETE FROM textualcolumns WHERE textualid=?;", str(textualid))
			self.execute("DROP VIEW if exists "+ textualizationName+ ";")
			self.execute("DELETE FROM textualizations WHERE id=?;", str(textualid))
			self.execute('--commit--')
			
		except:
				print("couldn't delete textualization", textualizationName)
#		

	def reduceRows(self, textualization, inn, statement):
		self.execute("DELETE FROM texts WHERE sourceid "+inn+" ( {statement} );".format(statement=statement) )
		self.execute("DELETE FROM sources WHERE rowid not in ( select sourceid from texts );" )
		self.execute('--commit--')

	
	
	
	def keeponly(self, columnlist, table):
		cs=", ".join(columnlist)
		if verbose: print("keeponly", cs)
		script="""BEGIN TRANSACTION;
			CREATE TEMPORARY TABLE {table}_backup({cs});
			INSERT INTO {table}_backup SELECT {cs} FROM {table};
			DROP TABLE {table};
			CREATE TABLE {table}({cs});
			INSERT INTO {table} SELECT {cs} FROM {table}_backup;
			DROP TABLE {table}_backup;
			COMMIT;
			""".format(table=table, cs=cs)
		self.execute("--script--", script)
		self.execute('--commit--')
	
	def reduceColumns(self, columnlist, textualization):
		if verbose: print("reduce", columnlist)
		if not columnlist: return
		textualid, = next(self.select("select id from textualizations where name = ? ;", (textualization, )))
		s=set(["url","linkOrigin_rowid" ,"nbSentences", "nbCharacters", "time", "source"])
		scs=set(columnlist)&s
		
		if verbose: print("scs", scs)
		if scs: self.keeponly(s-scs, "sources")
			
				
		tcs=set(columnlist)-scs
		if verbose: print("tcs", tcs)
		if tcs: 
			if verbose: print(tcs)
			
			for c in tcs:
				columnid, = next(self.select("select id from textcolumns where name = ? ;", (c, )))
				
				if verbose: 
					print("DELETE FROM texts WHERE textualid=? and columnid=?;", (textualid, columnid)) 
					print("DELETE FROM textualcolumns WHERE textualid=? and columnid=?;", (textualid, columnid)) 
					print("DELETE FROM textcolumns WHERE id=?;", (columnid, )) 
				self.execute("DELETE FROM texts WHERE textualid=? and columnid=?;", (textualid, columnid) )
				self.execute("DELETE FROM textualcolumns WHERE textualid=? and columnid=?;", (textualid, columnid)  )
				self.execute("DELETE FROM textcolumns WHERE id=?;", (columnid, )  )
		self.makeTextual(textualization, textualid)
		self.execute('--commit--')

	def kickOutDoubles(self, seq):
		seen = set()
		seen_add = seen.add
		return [ x for x in seq if x not in seen and not seen_add(x)]
	
	def dropLinks(self, linksDone , links2do ):
		"""
		when download stopped, put links2do and linksDone into database 
		2 tables :one for links2do and one for linksDone    link2do: a link is a triple : (url, level, origin)
		when choose the 4th mode, the downloading will start from the database; the 4th mode enabled only when the base isn't new. 
		
		This really takes some time , Todo : make it shorter
		
		"""
		self.execute("drop table if exists linksTodo")
		self.execute("drop table if exists linksDone")
		self.execute("CREATE TABLE linksTodo ( linksTodo VARCHAR, level INTEGER, origin INTEGER ) ;")
		self.execute("CREATE TABLE linksDone ( linksDone VARCHAR ) ;")
		linksDone=self.kickOutDoubles(linksDone)
		links2do=self.kickOutDoubles(links2do)
		print("dropping links...")
		self.execute("--links--",linksDone , links2do)
		self.execute('--commit--')

	###########################################
	### stat/info
	###########################################		
	
	def readInfo(self):
		try: 	
			#print "yyyy",self.getColumns("information")
			#self.repairInfoTable()
			self.nbPages, self.nbSentences, self.nbCharacters, self.nbSearchEngineAccesses, self.nbLinksToDo,self.nbLinksDone,self.comments, self.configfile, self.lastaccess, = next(self.select("SELECT * FROM information;"))
			#nbPages, nbSentences, nbCharacters, nbSearchEngineAccesses, nbLinksToDo, nbLinksDone, comments, configfile, lastaccess
		except Exception as e:
			if verbose : print("can't read info",e.message, e.args)
			self.repairedAlredy+=1
			self.repairInfoTable()
			

	def enterInfo(self, nbPages=0, nbSentences=0, nbCharacters=0, nbSearchEngineAccesses=0, nbLinksToDo=0, nbLinksDone=0, configfile="unknown", comments=None):
		"""							self.numGoodPages,self.totalNbSentences, self.totalNbWords, 
		                           self.nbSearchEngineAccesses+self.numBingVisits, self.configName
		enter into information
		"""
		if verbose: print("enterInfo", nbPages, nbSentences, nbCharacters, nbSearchEngineAccesses, nbLinksToDo, nbLinksDone, configfile, comments)
		if comments!=None:
			self.execute("UPDATE information SET nbPages=?, nbSentences=?, nbCharacters=?, nbSearchEngineAccesses=?, nbLinksToDo=?, nbLinksDone=?,comments=?, configfile=?, lastaccess=? where rowid=1;",
			(nbPages, nbSentences, nbCharacters, nbSearchEngineAccesses,nbLinksToDo, nbLinksDone, comments, configfile, time(), ))
		else:
			self.execute("UPDATE information SET nbPages=?, nbSentences=?, nbCharacters=?, nbSearchEngineAccesses=?, nbLinksToDo=?, nbLinksDone=?, configfile=?, lastaccess=? where rowid=1;",
			(nbPages, nbSentences, nbCharacters, nbSearchEngineAccesses,nbLinksToDo, nbLinksDone, configfile, time(), ))
		self.execute('--commit--')		
	
	def getColumns(self, table):
		"""
		to create cloumn view in the groWindow
		"""
		answ=self.select("PRAGMA table_info("+table+");")
		if answ:
			li = [b for a, b, c, d, e, f in answ]
			return li
		else: return ["problem retrieving the table information for "+table+"."]
		
	
	def repairInfoTable(self):
		"""
		needed to add missing columns to information table or other corrupted files
		"""
		if self.repairedAlredy>1:
			print("second try!")
			self.recomputeStats()
			return
		print("repairing info table")
		cols = self.getColumns("information")
		(nrrows,) = next(self.select("select count(*) from information;"))
		#print "____",cols,nrrows
		if len(cols) and nrrows: # some information there
			try:self.execute("ALTER TABLE information RENAME TO Tempinformation;")
			except:
				self.execute("DROP TABLE Tempinformation;")
				self.repairInfoTable()
			#Then create the new table with the missing column:
			self.execute(self.infoTableCreation)
			#And populate it with the old data:
			cols=", ".join(cols)
			self.execute("INSERT into information ("+cols+") SELECT "+cols+" FROM Tempinformation;")
			#Then delete the old table:
			self.execute("DROP TABLE Tempinformation;")
			
		else:
			print("making new info table")
			try:self.execute("DROP TABLE information;")
			except:pass
			self.execute(self.infoTableCreation)
			self.execute("INSERT INTO information( nbPages, nbSentences, nbCharacters, nbSearchEngineAccesses, nbLinksToDo, nbLinksDone, comments, configfile, lastaccess) VALUES (?,?,?,?,?,?,?,?,?) ",
						(0, 0, 0, 0, 0, 0,"no comment yet", "none", time(), ))
			
		nbPages, nbSentences, nbCharacters, nbSearchEngineAccesses,nbLinksToDo,nbLinksDone, configfile, comments= next(self.select("SELECT nbPages, nbSentences, nbCharacters, nbSearchEngineAccesses, nbLinksToDo,nbLinksDone, configfile, comments FROM information;"))
		if verbose: print(nbPages, nbSentences, nbCharacters, nbSearchEngineAccesses, configfile, comments)
		self.enterInfo(nbPages, nbSentences, nbCharacters, nbSearchEngineAccesses,nbLinksToDo,nbLinksDone, configfile, comments)
		self.readInfo() # got to call this before so that the info self.X variables get instanciated
		self.recomputeStats()



	def nbFilteredRows(self, textualization, selectconditions):
		"""
		called from groWindow to compute how many pages are shown
		"""
		
		if selectconditions: 	selectstatement = "SELECT count(rowid) from {txtu} where {cond};".format(txtu=textualization, cond=selectconditions)
		else: 			selectstatement = "SELECT count(rowid) from {txtu} ;".format(txtu=textualization)
		if verbose: print(selectstatement)
		try:
			x=next(self.select(selectstatement))
			if verbose:print("groBase",x)
			answ, = x
		
		except:
			print("groBase oh x=self.select(selectstatement).next()")
			return 
		if verbose: print("$$$",answ)
		return answ

	#def getDuplicateSelection(self, columns, rowconditions )
	
	
	def getSample(self, viewname, index, chars):
		"""
		called from exporter for the detection of the language direction
		index: column index (-1 = text)
		chars: how many chars
		"""
		sample=" "
		answ=self.select("SELECT * FROM "+ viewname)
		try:
			while answ and len(sample)<chars:  sample+=answ.next()[index]
		except:pass
		return sample

		
	def updateComment(self, comments):
		"""
		called from losefocusfilter in growindow
		"""
		self.execute("UPDATE information SET comments=? where rowid=1;",( comments, ))
		self.execute('--commit--')

	def getTextualizations(self):
		""""
		show textualizations in the mainWindow
		"""
		textualName=[]
		for name, in self.select("SELECT name FROM textualizations"):
			textualName.append(name)
		if verbose: print("getTextualizations", textualName)
		self.textual=textualName

		return self.textual
		
	def getTextColumns(self, textualization):
		
		textualid, = next(self.select("select id from textualizations where name = ? ;", (textualization, )))
		
		columns={}
		for nr, name, in self.select("select textcolumns.id,textcolumns.name from textualcolumns,textcolumns where textualcolumns.textualid = ? and textcolumns.id=textualcolumns.columnid;", (textualid, )):
			columns[nr]=name
			
		return columns
		
		
#	def getTextualizationName(self):
#		
#		textualName=[] #store the textualization Name in the database
#		textualId=[]  #store the  textualId 
#		self.textualcolumns=[]
#		self.textualizations=[]
#
#		for name,id, in self.select("SELECT name,id FROM textualizations"):
#			relation=[]
#			textualName.append(name)
#			textualId.append(id)
#			relation.append(id)
#			relation.append(name)
#			self.textualizations.append(relation)
#					
#		for textualid, columnid, in self.select("select textualid,columnid from textualcolumns"):
#			relation=[]
#			relation.append(textualid)
#			relation.append(columnid)
#			self.textualcolumns.append(relation)
#			
#		for id, columnname, in self.select("select id,name from textcolumns"):
#			self.textualcolumns[id-1].append(columnname)
#					
#		return textualName, self.textualizations, self.textualcolumns
	
	
	
	def enterUpsert(self, id, textualid, columnid, insertText, nbSentences, nbCharacters ):
		
		self.execute("""INSERT OR REPLACE INTO texts (sourceid, textualid, columnid, text, nbSentences, nbCharacters) VALUES (  ?,?,?,?,?,? );""", 
								  (id, textualid, columnid, insertText, nbSentences, nbCharacters ))
	
	
	
	def enterData(self, id, url, title, text, columnids, textualid):
#		print "enterData", id, url
#		print title, text, columnids, textualid
		self.execute("""INSERT OR REPLACE INTO sources (rowid, url, linkOrigin_rowid, nbSentences, nbCharacters, time, source) VALUES (  ?,?,?,?,?,?,? );""", 
								  (id, url, -1, 0, 0, 0, "" ))
#						OR REPLACE 		  
		nbs, nbc = self.computeStat(title)
		self.execute("""INSERT OR REPLACE INTO texts (sourceid, textualid, columnid, text, 	  nbSentences, nbCharacters) VALUES (  ?,?,?,?,?,? );""", 
								  (id, textualid, columnids[0], title, nbs, nbc ))
								  
		nbs, nbc = self.computeStat(text)
		self.execute("""INSERT OR REPLACE INTO texts (sourceid, textualid, columnid, text, 	  nbSentences, nbCharacters) VALUES (  ?,?,?,?,?,? );""", 
								  (id, textualid, columnids[1], text, nbs, nbc ))
								  
		self.execute('--commit--')						  
#		c="create view "+textualizationName+" as select s.rowid, s.url, s.time, s.linkOrigin_rowid, texts1.nbCharacters as title_nbCharacters, texts1.nbSentences as title_nbSentences,"
#		c+="texts1.text as title, texts2.nbCharacters as text_nbCharacters, texts2.nbSentences as text_nbSentences,texts2.text as text  from sources s, texts texts1, texts texts2 "
#		c+="where s.rowid = texts1.sourceid and  texts1.columnid=1 and texts2.columnid=2 and texts1.sourceid = texts2.sourceid"
	
	
	def computeStat(self, text):
		"""
		instead of computing the nbWords, we just calculate the number of characters
		
		"""
		
		return len(self.sentenceSplit.findall(text)), len(str(text)) 
	
	def getSentenceSplit(self):
		try:
			
			
			
			config = ConfigObj(os.path.join(os.path.expanduser('~'),"gromoteur",".settings","gro.cfg"),encoding="UTF-8")
			config.BOM=True
			if verbose : print("read", os.path.join(os.path.expanduser('~'),"gromoteur",".settings","gro.cfg"))
			return re.compile(config["configuration"]["sentenceSplit"], re.M+re.U)
		except Exception as e:
			try:
				config = ConfigObj(os.path.join("lib","gro.cfg"),encoding="UTF-8")
				config.BOM=True
				if verbose : print("read", os.path.join("lib","gro.cfg"))
				return re.compile(config["configuration"]["sentenceSplit"], re.M+re.U)
			except Exception as e:
				if verbose : print("can't read config file: gro.cfg",e)
				return re.compile(defaultSentenceSplit, re.M+re.U)
			
			
	
	def makeTextual(self, textualName, textualId):
		"""
			make a new view 
		"""
		if verbose: print("makeTextual", textualName, textualId)
		columnId=[]
		columnName=[]
		
		for columnid, in self.select("select columnid from textualcolumns where textualid=?", (textualId, )):
			if columnid not in columnId: columnId.append(columnid)
		
		actualcolumnids = [columnid for columnid, in self.select("select DISTINCT columnid FROM texts;")   ] 
		if verbose: print("actualcolumnids",actualcolumnids)
		columnId = [cid for cid in columnId if cid in actualcolumnids]
		for columnid in columnId:
			(columnname, )=next(self.select("select name from textcolumns where id=?", (columnid, )))
			if columnname not in columnName: columnName.append(columnname)
		if verbose: print("groBase",888,columnName,columnId)	
		c="create view "+textualName+" as select s.rowid, s.url, s.time, s.linkOrigin_rowid"
		r=""
		num=0
		for i in columnId:
			r=r+", texts"+str(num+1)+".nbCharacters as "+columnName[num]+"_nbCharacters, texts"+str(num+1)+".nbSentences as "+columnName[num]+"_nbSentences "+", texts"+str(num+1)+".text as "+columnName[num]
			num=num+1
			
		c=c+r
		c=c+" from sources  s"
		for i in range(len(columnId)):
			c=c+", texts texts"+str(i+1)
		
		c=c+" where s.rowid=texts1.sourceid"
		
		for i in range(len(columnId)):
			c=c+" and texts"+str(i+1)+".columnid= "+str(columnId[i])+" and texts"+str(i+1)+".textualid="+str(textualId)
			
		if len(columnId)>1:			
			for i in range(len(columnId)-1):
				c=c+" and texts"+str(i+1)+".sourceid=texts"+str(i+2)+".sourceid"
		
		if len(columnId)>2:
				c=c+" and texts"+str(1)+".sourceid=texts"+str(len(columnId))+".sourceid"
								
		self.execute("drop view if exists "+textualName)
		self.execute(c)
		
		if verbose: print("made textualization", c)
		self.execute('--commit--')
	
	###########################################
	### access functions for the fieldselector
	###########################################
	def getSourceByURL(self, url, textual, selectColumnName):
		"""
		called from fieldselector
		"""
		if textual and selectColumnName: selecttext="SELECT rowid, "+ selectColumnName +" FROM "+textual+" WHERE url=?;"
		else:	selecttext="SELECT rowid, source FROM sources WHERE url=?;"
		
		try: rowid, source, = next(self.select(selecttext, (url, )))
		except: rowid, source=None, None
		return rowid, source
		
	def getSourceById(self, id, textual, selectColumnName):
		"""
		called from fieldselector 
		used for getting the source by id
		"""
		if textual and selectColumnName: selecttext="SELECT "+ selectColumnName +" FROM "+textual+" WHERE rowid=?;"
		else:	selecttext="SELECT source FROM sources WHERE rowid=?;"
		if verbose: print("___ getSourceById", selecttext, "id:",id)
		n=self.select(selecttext, (id, ))
		if verbose: print("nnn",n)
		try: source, = next(n)
		except: 
			print("failed!!!!!!!!!!!!!!!!!!")
			return ""
		return source

	
#	
	def totalNum(self, statement):
		'''
		get the total item in sources
		used in groWindow
		used in groWindow for recomputation of stats
		'''
		(num,) =next(self.select(statement))
		return num
	
	def getNextSource(self, rowid, textual, selectColumnName):
		"""
		called from fieldselector 
		used for checking if there is another source
		"""
#		print "))))textual", textual
#		print "))))selectColumnName",selectColumnName
		if textual and selectColumnName: selecttext="SELECT rowid, url, "+ selectColumnName +" FROM "+textual+" WHERE rowid>? ORDER BY rowid LIMIT 1;"
		else:	selecttext="SELECT rowid, url, source FROM sources WHERE rowid>? ORDER BY rowid LIMIT 1;"
#		print selecttext
		for rowid, url, source, in self.select(selecttext, (rowid, )):  return (rowid, url, source)			
		return (None, None, None)
		
	def getLastSource(self, rowid, textual, selectColumnName):
		
		if textual and selectColumnName: selecttext="SELECT rowid, url, "+ selectColumnName +" FROM "+textual+" WHERE rowid>? ORDER BY rowid desc LIMIT 1;"
		else:	selecttext="SELECT rowid, url, source FROM sources WHERE rowid<? ORDER BY rowid desc LIMIT 1;"
#		print selecttext
		for rowid, url, source, in self.select(selecttext, (rowid, )):  return (rowid, url, source)	
		return (None, None, None)
	
	def columnIsSourceColumn(self, textual, columnname):
		for source, in self.select("SELECT "+columnname+" FROM "+textual+";"):  
			if source: # not empty
				return source[:6]=="<html>"
		return False
	
	###########################################
	### other
	###########################################
	
	
	def recomputeStats(self, textualization="standard", comments=None, textcolumn="text", textualid=1):
		'''
		recompute simple statistics
		'''
		if verbose: print("recomputeStats",textualization, "comments",comments, "textcolumn",textcolumn, "textualid",textualid)
		self.makeTextual(textualization, textualid)
		if not comments: 		
				try:comments,=next(self.select("SELECT comments FROM information;"))
				except: # case of corrupt database:
					comments=""
					self.comments=comments
					self.lastaccess=time()
		try:	self.nbSearchEngineAccesses
		except:	self.nbSearchEngineAccesses=0
		try:	self.configfile
		except:	self.configfile="unknown"
		(self.nbPages,) = next(self.select("select count(rowid) from sources"))
		(self.nbCharacters,self.nbSentences,) = next(self.select("select sum("+textcolumn+"_nbCharacters), sum("+textcolumn+"_nbSentences) from "+textualization+";"))
		
		(self.nbLinksToDo,) = next(self.select("select count(rowid) from linksTodo"))
		(self.nbLinksDone,) = next(self.select("select count(rowid) from linksDone"))
		print("self.nbLinksToDo,self.nbLinksDone",self.nbLinksToDo,self.nbLinksDone)
		self.enterInfo(self.nbPages, self.nbSentences, self.nbCharacters, self.nbSearchEngineAccesses, self.nbLinksToDo,self.nbLinksDone, self.configfile, comments=comments)
				
		#return self.nbPages,self.nbCharacters,self.nbSentences,self.nbLinksToDo,self.nbLinksDone
	
	

	def enterNewText(self, sourceId, textualId, columnid,text, nbSentences, nbCharacters, overwrite):
		"""
		 enter the extracted information
		 called from fieldselector
		"""
#		print "entering", sourceId, textualId, columnid,text
		if overwrite:  #overwrite==True
			self.execute("update texts set text=?,nbSentences=?,nbCharacters=? where sourceid=? and textualid=? and columnid=?", (text, nbSentences, nbCharacters, sourceId, textualId, columnid, ))
		else:
			self.execute("insert into texts(sourceid,textualid,columnid,text,nbSentences,nbCharacters) Values (?,?,?,?,?,?);", (sourceId, textualId, columnid,text, nbSentences, nbCharacters, ))
		self.execute('--commit--')	
	
	def filterTextColumns(self,collist,removelist=[]):
		textColumns=[] # only take text columns:
		for col in collist:
			if col not in removelist:
				ty=self.getColType(col)
				
				#ty=parent.col2ty.get(col, None)
				#if not ty: # type not found yet
					#if "_" in col:
						#rest=col.split("_")[-1]
						#if rest.startswith("nb") or rest=="rowid":
							#ty="nb"
						#else:  ty="txt"
					#else: ty="txt"
					
					
				if ty=="txt":textColumns+=[col]
		return textColumns
	
	def getColType(self,col):
		ty=self.col2ty.get(col, None)
		if not ty: # type not found yet
			if "_" in col:
				rest=col.split("_")[-1]
				if rest.startswith("nb") or rest=="rowid":
					ty="nb"
				else: ty="txt"
			else: ty="txt"
		return ty
######################### 
def test(t): 
	print("bonjour")
	base=GroBase("a")
	from .htmlPage import Page
	from .groSpider import GroOpener
	p=Page("http://www.cestlafete.fr/nosmagasins/paulescar.html", GroOpener())
	base.enterSource(p, 0)
	base.execute("--close--")
	
#	s=base.select(t)
#	while True:
#		try: ooo = s.next()[0]
#		except: break
	
	

if __name__ == "__main__":
	print("bonjour")
	test(None)
	
#	t=time()
#	test("select * from sources;")
#	print "sources",time()-t
#	
#	t=time()
#	test("select * from standard;")
#	print "standard",time()-t
#	
#	t=time()
#	test("select * from lu;")
#	print " lu",time()-t
#	
#	t=time()
#	test("select * from standard;")
#	print "standard",time()-t
#	
#	t=time()
#	test("select * from lu;")
#	print " lu",time()-t
#	
#	print "au revoir"
	
	






