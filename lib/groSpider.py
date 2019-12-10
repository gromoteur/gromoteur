# -*- coding: utf-8 -*-

"""
spider class 
"""
import os, psutil, urllib.robotparser, codecs, re, socket # re is used in eval!!!

#from datetime import date
from random import choice
from time import time,  sleep
#from urllib import FancyURLopener
#import requesocks as requests # FIXME: as soon as requests includes socks change this to: import requests
import requests # FIXME: test socks
from urllib.parse import urlparse, urljoin

from . import spiderThread, htmlPage
from PyQt5 import QtCore, QtWidgets

from .groBase import GroBase
from . import browsercookie

verbose = False  #choose whether to print messages ....  when verbose=False , not print ; when verbose=True ,print 
#verbose = True


userAgents = [
	"Mozilla/5.0 (compatible; gromoteur/1.0; http://gromoteur.ilpga.fr/)",
	"Mozilla/5.0 (compatible; googlebot/2.1; +http://www.google.com/bot.html)",
	"Mozilla/3.0 (Slurp/si; slurp@inktomi.com; http://www.inktomi.com/slurp.html)",
	"randomly any of the below:",
	'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'
	'Opera/9.25 (Windows NT 5.1; U; en)',
	'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
	'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Trident/4.0)',
	'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0)',
	'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
	'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
	'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
	'Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.0 Safari/532.0', 
	'Mozilla/5.0 ;iPhone; CPU iPhone OS 8_1_2 like Mac OS X; AppleWebKit/600.1.4 ;KHTML, like Gecko; Version/8.0 Mobile/12B440 Safari/600.1.4', 
	'Mozilla/5.0 (SymbianOS/9.2; U; Series60/3.1 NokiaE51-1/400.34.011; Profile/MIDP-2.0 Configuration/CLDC-1.1 ) AppleWebKit/413 (KHTML, like Gecko) Safari/413  	', 
	'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:41.0) Gecko/20100101 Firefox/41.0'
	]




class GroOpener():

	def __init__(self, userAgentIndex=0, proxies={}, allow_redirects=True, timeout=False, timeoutsec=3, browserLogin=False):
		self.proxies=proxies
		self.userAgentIndex=userAgentIndex
		self.allow_redirects=allow_redirects
		self.userAgentRandomIndex=userAgents.index("randomly any of the below:")
		self.timeout=timeout
		self.timeoutsec=.1
		self.session = requests.Session()
		if browserLogin:
			cj = browsercookie.load() # tries first chrome or chromium, then firefox, last cookies overrules first
			self.session.cookies = cj
		
		
	def getUserAgent(self):
		if self.userAgentIndex==self.userAgentRandomIndex:  	return choice(userAgents[self.userAgentRandomIndex+1:])
		else: 							return userAgents[self.userAgentIndex]

	def open(self, url):
		r = self.session.get(url, headers={'User-Agent': self.getUserAgent()},  proxies=self.proxies, allow_redirects=self.allow_redirects, timeout=self.timeoutsec if self.timeout else None, stream=True) # , #TODO: find out what this changes: stream=True
		return r
		


#class Communicate(QtCore.QObject):
	#closeApp = QtCore.pyqtSignal() 
	
	
class GroSpider(QtCore.QObject):
	"""
	Class documentation goes here.
	"""
	def __init__(self, goWindow):
		"""
		GroSpider Constructor
		"""
		QtCore.QObject.__init__(self)
		self.goWindow=goWindow
		self.wiz=goWindow.wiz
		self.base=goWindow.base
	
		self.readWiz(self.wiz)   
		
		dbFile=self.base.filename
		#dbName=self.base.name
		if self.base:
			self.base.close()
		self.goWindow.base.close()
		if self.goWindow.groWindow.qtdb:
			self.goWindow.groWindow.qtdb.close()
		self.goWindow.groWindow.base.close()
		if self.dataErase:
			try:
				os.remove(dbFile)
			except:
				pass
		self.base=GroBase(self.base.name)
		self.configName=goWindow.configName
		self.totalNbPages= goWindow.base.nbPages
		self.totalNbSentences= goWindow.base.nbSentences
		self.totalNbWords = goWindow.base.nbCharacters
		self.nbSearchEngineAccesses = goWindow.base.nbSearchEngineAccesses
		
		self.nbRobotsInMemory=int(self.goWindow.groWindow.config["configuration"]["nbRobotsInMemory"])
		self.nbAccessDomInMemory=int(self.goWindow.groWindow.config["configuration"]["nbAccessDomInMemory"])
		self.nbPageMaxCounterInMemory=int(self.goWindow.groWindow.config["configuration"]["nbPageMaxCounterInMemory"])
				
		self.cutMessages=int(self.goWindow.groWindow.config["configuration"]["cutMessages"])  #10000 characters
		self.sentenceSplit=self.goWindow.groWindow.sentenceSplit
		

		self.mutex = QtCore.QMutex()
		
		self.running, self.end, self.maxAttained,  self.paused = False, False, False, False
		self.links2do, self.simplelinks2do, self.linksDone, self.currently, self.subdomains = [],[],[],[],[]
		self.numPagesSinceRestart, self.numSentences, self.numGoodPages,self.numGoodPagesSinceRestart,self.numWords, self.numBingVisits= 0,0,0,0,0, 0
		self.threads, self.starttime, self.refreshtime  = [],time(), 0

		self.bingNum=0
		
		self.robotstxtsl, self.robotstxtsd = [], {}
		self.lastAccessDoml, self.lastAccessDomd = [], {}
		self.maxCountDoml, self.maxCountDomd = [], {}
		
#		global userAgentIndex
		proxies={}
		if self.proxyGroupBox:
			if str(self.httpProxyName).strip()[:4] in ["http", "sock"]: proxies["http"]=str(self.httpProxyName).strip()
			if str(self.httpsProxyName).strip()[:4] in ["http", "sock"]: proxies["https"]=str(self.httpProxyName).strip()
				
		self.groopener = GroOpener(userAgentIndex=self.wiz.userAgent.currentIndex(), proxies=proxies,  allow_redirects=self.followRedirects, timeout=self.timeout, timeoutsec=self.timeoutsec, browserLogin=self.browserLogin)
		
		self.failedLinks={} # url --> nr of times failed
		if self.timeout: socket.setdefaulttimeout(self.timeoutsec*2.0) # used for robots.txt request timeout 
		#print "timeoutsec",self.timeoutsec
		self.ngram,  self.langs = None, None
		if self.downloadRestriction and self.language!="any language":
			self.ngram = self.goWindow.groWindow.ng
			self.langs=self.goWindow.groWindow.ng.alllangs
		
		
		if self.fromdatabase: # TODO: database start should imply a much simpler config wizard as it's not taken into account
			for link,  in self.base.select("select linksDone from linksDone;") :
				self.linksDone.append(link)
			for link, level, origin in self.base.select("select linksTodo,level,origin from linksTodo;"):
				links=(link, level, origin)
				self.links2do.append(links)
		else:
			if self.startWithURL:
				self.links2do = []
				for link in str(self.wiz.startURL.text()).strip().split():
					if not urlparse(link).netloc: link = "http://"+link
					#if link.endswith("/"): link=link[:-1]
					self.links2do += [(link,0, 0)]
					if verbose: print(self.links2do)
			elif self.startWithUrlFile:
				try:
					urlfile=codecs.open( str(self.wiz.startUrlFile.text()),"r", "utf-8" )
					for link in urlfile:
						self.links2do += [(str(link.strip()),0, 0)]
					urlfile.close()
				except:
					message = QtWidgets.QMessageBox(self.goWindow)
					message.setText("<b>Can't read the file "+str(self.wiz.startUrlFile.text())+"!</b>")
					message.setInformativeText("You may want to check that the file looks OK and is encoded in UTF-8 before starting again.")
					message.setIcon(QtWidgets.QMessageBox.Warning)
					message.setStandardButtons(QtWidgets.QMessageBox.Ok)
					result=message.exec_()
					self.theEnd()
					return
					
					
			else:
				self.bingNum=0
		
		if self.dataErase:
			self.numSentences, self.numGoodPages,self.numWords= 0,0,0
		else:
			(self.numGoodPages, self.numSentences, self.numWords,) =next(self.base.select("select nbPages,nbSentences,nbCharacters from information"))
			
		self.running=True
	
		self.nbThreads=self.wiz.nbThreads.value()
				
		for n in range(self.nbThreads):
			t = spiderThread.SpiderThread("spider-"+str(n+1), self)			
			t.start()
			self.threads.append(t)
		
		if verbose: print("end of groSpider init")
		
#		while True:
#			print self.threads
#			print [t.isRunning() for t in self.threads]
#			sleep(1)
#			self.goWindow.update()
#		
		
		
	def getLink(self):
		"""
		a link is a triple : (url, level, origin)
		
		first case: we access every server only every self.everyServerSeconds
			try to find a link on a server that has not been accessed for self.everyServerSeconds
				if we find one: check whether the server is not over the self.pageByServer level
					if over the level: try the next, 
						if in the end no link with good timing AND good max: try all over again without good max
				if we haven't found a good link: wait!
		second case: we have only the maxOneServer restriction:
			 try to find a link on a server that has not too many pages
			 if not found: just take the first link
		third case: neither everyServerSeconds nor maxOneServer restriction:
			take the first link
			
		returns a quadruple: url, level, origin, status
		"""
		if self.spiderTraps and self.everyServer: 		# first case: we access every server only every self.everyServerSeconds
			url,level,o =  self.selectGoodLink(self.maxOneServer)
			if not url and self.maxOneServer: 				# if in the end no link with good timing AND good max: try all over again without good max
				url,level,o =  self.selectGoodLink(False)
			if not url: 													# if we haven't found a good link: wait!
				return url, level,o, "wait!"
		elif self.spiderTraps and self.maxOneServer:	 # second case: we have only the maxOneServer restriction:
			url,level,o =  self.selectMaxOkLink() 				
			if not url: url,level,o =  self.links2do.pop(0)	# if not found: just take the first link
		else:
			url,level,o =  self.links2do.pop(0) # take the first on the list of links to do

		if verbose: print("groSpider: trying: ",url.encode("utf-8"),"level:",level)
		
		# level OK?
		if self.downloadRestriction and self.levelTo>=0 and level>self.levelTo: # shouldn't happen because links are checked => useless??? 
			if verbose: print("holy shit, wrong level",level)
			return url, level,o, "wrong level"

		# max of pages reached?
		if self.maxPages != 0 and  self.numGoodPagesSinceRestart >= self.maxPages :
			self.maxAttained=True
			return url, level,o,"page maximum per crawl has been attained"
		
		# min of disk space reached?
		#print 'utils.get_free_space("corpora")',psutil.disk_usage("corpora").free/1024/1024,self.diskMin
		#if utils.get_free_space("corpora")<self.diskMin:
		if psutil.disk_usage(os.path.join(os.path.expanduser('~'),"gromoteur","corpora")).free/1024/1024<self.diskMin:
			self.maxAttained=True
			return url, level,o,"not enough disk space"
	
		# max of sentences reached?
		if self.maxSentences != 0 and  self.numSentences >= self.maxSentences :
			self.maxAttained=True
			return url, level,o,"total sentence maximum attained"

		# max of subdomains reached?
		subd = htmlPage.getSubdomain(url)
		if self.maxSubdomains != 0 and subd not in self.subdomains :
			if len(self.subdomains) >= self.maxSubdomains :
				return url, level,o,"total subdomain maximum attained"
			else : self.subdomains.append(subd)
		# robots.txt allows this link?
		if self.obeyRobots and not self.checkRobotstxt(url):
			if verbose: print("holy shit, robots.txt doesnt want me to take",url.encode("utf-8"))
#			print self.robotstxtsd
			return url, level,o, "robots.txt disallows"
		
		# everything ok: we're going for it:
		self.currently.append(url)
		return url, level,o, "ok"
		

	def selectGoodLink(self,  checkMaxOne):
		"""
		called from getLink
		selects a url, level pair from self.links2do whose server has not been touched for self.everyServerSeconds
		"""
		if verbose: print("selectGoodLink", checkMaxOne)
		for url,level,o in self.links2do:
			netloc = urlparse(url).netloc
			if netloc in self.lastAccessDomd:
				t=self.lastAccessDomd[netloc]
				if time()-t > float(self.everyServerSeconds):
					self.addDelayTimestamp(netloc)
					if not checkMaxOne or self.maxCounterOk(netloc):
						self.links2do.remove( (url, level,o) )
						return url, level,o
			else: # case: i got no information on this site
				self.addDelayTimestamp(netloc)
				if not checkMaxOne or self.maxCounterOk(netloc):
					self.links2do.remove( (url, level, o) )
					return url, level,o
		# problem: no link is allowed right now.
		return None, None, None
		
	def selectMaxOkLink(self):			
		for url,level,o in self.links2do:
			netloc = urlparse(url).netloc
			if self.maxCounterOk(netloc):return url, level,o
		return None, None,  None
		
	def addDelayTimestamp(self, netloc):
		if len(self.lastAccessDomd)>=self.nbAccessDomInMemory:
			oldnetloc = self.lastAccessDoml.pop(0)
			del self.lastAccessDomd[oldnetloc]   
		self.lastAccessDoml+=[netloc]
		self.lastAccessDomd[netloc]=time()

	def maxCounterOk(self, netloc):
		acs = self.maxCountDomd.get(netloc, 0)<self.pageByServer
		if acs: self.addMaxCounter(netloc)
		return acs
		
	def addMaxCounter(self, netloc):
		if len(self.maxCountDomd)>=self.nbPageMaxCounterInMemory:
			oldnetloc = self.maxCountDoml.pop(0)
			del self.maxCountDomd[oldnetloc]   
			
		self.maxCountDoml+=[netloc]
		self.maxCountDomd[netloc]=self.maxCountDomd.get(netloc, 0)+1
		

	def addLinks(self, links):
		"""
		add links
		TODO: think about whether it's useful to check again if the links are already in the links2do
		because the thread may not know the latest additions.
		"""	
		
		links = [(li,level,o) for (li,level,o) in links if li not in self.simplelinks2do and li not in self.linksDone]
		simplelinks = [li for (li,level,o) in links]
		#print('links2do:',len(self.links2do),"https://www.jw.org/pcm/" in self.links2do, self.links2do)
		if self.breadthFirst: 	  
			self.links2do+=links
			self.simplelinks2do+=simplelinks
		else:			          
			self.links2do=links+self.links2do
			self.simplelinks2do+=simplelinks+self.simplelinks2do
		
	def updatesStats(self,  numSentences, numWords,  negNbSentences,  negNbWords):
		if verbose: print(self.numGoodPages,self.numGoodPagesSinceRestart,"updatesStats", numSentences, numWords,  negNbSentences,  negNbWords)
		
		if negNbSentences: # case 1: a page was updated
			self.totalNbSentences+=numSentences-negNbSentences
			self.totalNbWords+=numWords-negNbWords
		else:
			self.totalNbPages+=1
			self.numPagesSinceRestart+=1
			self.totalNbSentences+=numSentences
			self.totalNbWords+=numWords
		if numWords>0:
			self.numGoodPages+=1
			self.numGoodPagesSinceRestart+=1
			self.numSentences+=numSentences
			self.numWords+=numWords

	
	def checkRobotstxt(self, link):

		netloc = urlparse(link).netloc
		if netloc in self.robotstxtsd:
			rp=self.robotstxtsd[netloc]
		else:
			rp = urllib.robotparser.RobotFileParser()
			rp.set_url(urljoin(urlparse(link).scheme+"://"+netloc, "robots.txt"))
			try:	rp.read()
			except: rp=None
			if len(self.robotstxtsd)>=self.nbRobotsInMemory:
				oldnetloc = self.robotstxtsl.pop(0)
				del self.robotstxtsd[oldnetloc]   
			self.robotstxtsl+=[netloc]
			self.robotstxtsd[netloc]=rp
		if rp: 
			try:
				return rp.can_fetch("*", link)
			except:
				True
		else: return True # case: robots.txt doesn't exist
		
	
	def readWiz(self, wiz):
		"""
		read all the settings from the wiz into the spider as attributes
		"""
		regexObjects=["pageRestriction", "linkDomain","searchEngineFilter",  "linkAvoidURL","downloadURL","downloadAvoidURL"]
#		print [o.objectName() for o in wiz.stringObjectList]
		for o in wiz.checkObjectList: setattr(self, str(o.objectName()), o.isChecked())
		for o in wiz.stringObjectList: setattr(self, str(o.objectName()), o.text())
#		if not self.defaultEncoding.strip(): self.defaultEncoding="utf-8"
		if self.pageIgnoreCase:		rei=",re.I"
		else:				rei=""
		
		for o in regexObjects: 
			t=str(eval( "wiz."+o+".text()")).strip()
			if t: 		setattr(self, o, eval( "re.compile(str(wiz."+o+".text()).strip()"+rei+")"))
			else: 		setattr(self, o, None)
				
		for o in wiz.valueObjectList: setattr(self, str(o.objectName()), o.value())
		for o in wiz.comboObjectList: setattr(self, str(o.objectName()), o.currentText())
		if wiz.language.currentIndex() == 0: self.language = "any language"
		if wiz.location.currentIndex() == 0: self.location = "automatic location detection"
		
	
	def threadFinished(self):
		"""
		every thread calls this when finishing
		"""
		if verbose : print("a thread Finished") #, threading.enumerate(), "still running..."

		if self.running: # only if natural death
			if verbose : print("2________gromoteur is running:",self.running)
			if self.links2do!=[] and not self.maxAttained: # in case another thread would find some more links
				if verbose : print("restarting...")
				for t in self.threads:
					if not t.isRunning(): t.start()
				return
			if verbose : print("all done===========================================")		
			if not self.end: self.theEnd()

		else :
			if verbose : print("gromoteur running:",self.running,"end:",self.end)
			if not self.end: self.theEnd()


	def theEnd(self,  terminateTime=5, deleteTime=10):
		if verbose: print("the end...") #,self.linksDone
		if self.end:return
		self.end=True
		
		ti=time()
		self.running=False
		anyone=True
		while anyone:
			anyone=False
			for t in self.threads:
				if not t.stopped: 
					if verbose: print(t.name, "is not stopped")
					anyone=True
			sleep(.1)
			if time()-ti>terminateTime:
				for t in self.threads:
					t.terminate()
			if time()-ti>deleteTime:
				for t in self.threads:
					del t
				anyone=False	
				
		if verbose: print("enterInfo...")
		self.base.enterInfo(self.numGoodPages,self.totalNbSentences, self.totalNbWords,
						self.nbSearchEngineAccesses+self.numBingVisits,len(self.links2do), len(self.linksDone), self.configName)
		self.goWindow.statusbar.setText("dropping "+str(len(self.linksDone)+len(self.links2do))+" links in the database")
		if verbose: print("enterInfo finished\ndropping",len(self.linksDone)+len(self.links2do),"links in the database")	
		self.base.dropLinks(self.linksDone, self.links2do)
			
		anyone=True
		while anyone:
			anyone=False
			anyone=not self.base.reqs.empty()
			sleep(1)
			if verbose: print("self.base.reqs.empty not empty", self.base.reqs.qsize())
			self.goWindow.statusbar.setText("Writing "+str(len(self.linksDone)+len(self.links2do))+" links to the database. Please wait!")
			self.goWindow.messages.append("Writing "+str(len(self.linksDone)+len(self.links2do))+" links to the database. Please wait!\n")
		if verbose: print("enterInfo finished")		

		self.goWindow.end()
		

	
	
	def nicetime(self,total_seconds):
		seconds = int(total_seconds) % 60
		total_minutes = round(total_seconds / 60)
		minutes = total_minutes % 60
		total_hours = round(total_minutes / 60)
		hours = total_hours % 24
		total_days = round(total_hours / 24)
		days = total_days % 365
		years = round(total_days / 365)
		per = [years, days, hours, minutes, seconds]
		pernom = ["year", "day", "hour", "minute", "second"]
		text=""
		for i in range(len(per)):
			if per[i] :
				text+= str(per[i]) + " "+pernom[i]
				if per[i]>1 : text+= "s"
				text+=" "
		return text


	def refreshView(self,s):
		"""
		called from the spiderThread by "notify"
		s contains a dictionary of information to show
		"""
		if verbose>1:
			print("refreshView is called")
			print("queue", self.base.reqs.qsize(), self.base.reqs.full())
		
		sec = time()-self.starttime
		niceti=self.nicetime(int(sec))
#		if self.mutex.tryLock(18): #############################
		self.mutex.lock() #############################
		#if True:
		try:
			if self.running : self.goWindow.duration.setText(niceti)
			if verbose>1:print("refreshView got mutex")
			if str(s['msg'])=="Can't get started!":	
				message = QtWidgets.QMessageBox(self.goWindow)
				message.setText("<b>Can't connect to the links you provided!</b>")
				message.setInformativeText("Is your internet connection working?\nCan you reach the desired pages in a browser?")
				message.setIcon(QtWidgets.QMessageBox.Warning)
				message.setStandardButtons(QtWidgets.QMessageBox.Ok)
				result=message.exec_()	
			if self.cutMessages:
				mess = str(self.goWindow.messages.toPlainText())
				mess = str(mess)+str(s['msg'])
				mess = mess[-self.cutMessages:] 
				self.goWindow.messages.setText(mess)
			else:
				self.goWindow.messages.append(s['msg'])
			self.goWindow.scrollToBottom(self.goWindow.messages)

			if sec == 0 : sec = 1
		
			self.goWindow.currentURL.setText(s['currentURL'])
			self.goWindow.currentLevel.setText(s['currentLevel'])
			self.goWindow.encoding.setText(s['encoding'])

			self.goWindow.sentences.setText(str(self.numSentences))
			self.goWindow.smin.setText(str(int(round(self.numSentences/sec*60))))
			self.goWindow.words.setText(str(self.numWords))

			self.goWindow.bingVisits.setText(str(self.numBingVisits))
			self.goWindow.wmin.setText(str(int(round(self.numWords/sec*60))))
			self.goWindow.pages.setText(str(len(self.linksDone)))
			self.goWindow.goodPages.setText(str(self.numGoodPages))
			self.goWindow.tookPages.setText(str(self.numGoodPagesSinceRestart))
			self.goWindow.goodPagesMin.setText(str(round(self.numGoodPagesSinceRestart/sec*60, 2)))
			self.goWindow.pmin.setText(str(round(self.numPagesSinceRestart/sec*60, 2)))
			self.goWindow.links.setText(str(len(self.links2do)))
			self.goWindow.repaint()

			if self.goWindow.running  :self.goWindow.statusbar.setText(s['status'])
		except Exception as e: 
			print("refreshView went wrong",e)
		
		self.mutex.unlock() #############################
		
	
if __name__=="__main__":
	
	groopener = GroOpener(userAgentIndex=0, proxies={},  allow_redirects=True, timeout=True, timeoutsec=1, browserLogin=True)
	
