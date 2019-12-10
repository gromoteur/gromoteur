# -*- coding: utf-8 -*-

import sys, signal,  codecs, re, os
from PyQt5 import QtCore

from time import time,  sleep

from random import choice
from . import groBase as base
from . import bing
from . import htmlPage

signal.signal(signal.SIGINT, signal.SIG_DFL) # allows stopping all by ctrl-c

debug = 0
debug = 1

class Communicate(QtCore.QObject):
	signal = QtCore.pyqtSignal([dict]) 
	endtrigger = QtCore.pyqtSignal()

class SpiderThread(QtCore.QThread):

	def __init__(self, name, spider):
		"""
		name: threadname spider-0,...
		"""
		QtCore.QThread.__init__(self)
		self.name = name
		self.spider=spider		
		self.msg,  self.encoding,  self.url ="", "", ""
		self.level=-1
		self.refreshtime  = 0
		self.stopped = False
		self.status = "starting "+self.name
		self.sentenceSplit=spider.sentenceSplit
		
		self.c = Communicate()
		self.c.signal[dict].connect(self.refreshView)     
		self.c.endtrigger.connect(self.finished)   
		#self.c.closeApp.connect(self.refreshView)  
		

	def run(self):
		"""
		
		the main thread function:
		
		"""
		self.starttime = time()

		while not self.stopped:
			
			while self.spider.paused: 	sleep(1)
			
			if debug:print(self.name,"is trying to lock")

			self.spider.mutex.lock() ########################### begin lock
			
			# if no more links in list and some other thread is working: continue and wait for new links
			# if no more links in list and _no_ other thread is working: if we're on bing-searching: try to get more links from bing
			#                                                                                          if other types of searching: that's the end

			if not self.spider.links2do : # if no more links in list
				if not self.spider.currently  : # if no one is currently working
					if debug: print(self.name,"no one else working")
					if self.spider.startWithSearchEngine:
						self.spider.links2do=self.moreBing()
						if self.spider.links2do == []:  self.stopped = True
					else :	self.stopped = True # stop myself
				else:
					if debug: print("another thread is working:", self.spider.currently) 
				# whether someone is working or not, unlock the variables:
				self.spider.mutex.unlock()
				if debug: print(self.name,"unlocked no links")
				sleep(1) # wait a second
				continue # and try "while" again
			
			self.url, self.level, origin, status = self.spider.getLink()
			self.spider.mutex.unlock() ############################# end lock
			
			if status != "ok":
				if status == "wait!": # the server has already been asked more than the restrictions allow
					if debug:print(self.name, "waits... ....................................")
					sleep(1)
					continue # and try "while" again
				if debug:print(self.name, "doesn't do ", self.url, self.level, "because", status)# .encode("utf-8")
				if self.spider.maxAttained: 	self.stopped = True
				self.msg+= self.url+" was not taken. reason:"+status+"\n"# .encode("utf-8")
				self.notify()
				continue
				
			# is the url OK? (urls taken from bing or a list may not fit the conditions...)
			urlOk =( not self.spider.downloadRestriction	 # either no restrictions
								or  # or restrictions OK:
								( 	(not self.spider.downloadURL  or self.spider.downloadURL.search(self.url) )
									and (not self.spider.downloadAvoidURL  or  not self.spider.downloadAvoidURL.search(self.url))
								)
						)
						
			if self.stopped or self.url in self.spider.linksDone or  (self.spider.pageLinkRestrict and not urlOk):
					if debug: 
						print("the link",self.url,"is already done, or we only take good urls and this url doesn't match:", end=' ') 
						if self.stopped: print("self.stopped")
						if self.url in self.spider.linksDone: print(" self.url in self.spider.linksDone")
						if self.spider.pageLinkRestrict and not urlOk: print("self.spider.pageLinkRestrict and not urlOk")
						print("spiderthread strange!",self.url,self.spider.downloadURL,self.spider.downloadURL.search(self.url) )
					# so we can do a continue, because this current page is useless
					self.spider.mutex.lock() 
					if self.url in self.spider.currently: self.spider.currently.remove(self.url)
					self.spider.mutex.unlock() 
					continue 
		
			self.status = self.name + ": "+self.url[:min(len(self.url),100)]+" ..."
			self.msg += self.name +" opens: "+self.url+"\n"
			self.notify()
			if debug: print(self.name +" opens: "+self.url)#.encode("utf-8"))
			# #############################################
			self.page = htmlPage.Page(	str(self.url),
							self.spider.groopener,
							self.sentenceSplit,
							str(self.spider.defaultEncoding), 
							self.spider.takePdf) # ###### here it happens ######
			# #############################################
			
			# --------- checking if the page produced an error
			if self.page.error:
				
				if str(self.page.error)=="Timeout" and self.spider.linksDone==[]:
					# nothing worked! network error?
					self.msg="Can't get started!"
				else:
					self.msg=self.name +" error "+str(self.page.error)+" "+self.url+"\n"
				if debug: print(self.msg)# .encode("utf-8")
				self.notify()
				self.spider.mutex.lock() ###########################
				if self.url in self.spider.currently: self.spider.currently.remove(self.url)
				
				nrfailed=self.spider.failedLinks.get(self.url, 0)
				if nrfailed < self.spider.trytimes and self.url not in self.spider.links2do : self.spider.links2do.append( (self.url, self.level, origin) )
				self.spider.failedLinks[self.url]=nrfailed+1
				
				self.spider.updatesStats( 0, 0,  0,  0)
				self.spider.mutex.unlock() #############################
							
				continue
				
			# --------- checking if the redirects are ok
			if self.spider.followRedirects and self.spider.redirectMustMatch:
				for redurl in self.page.urls:
					urlOk =( not self.spider.downloadRestriction	 # either no restrictions
							or  # or restrictions OK:
							( 	
									(not self.spider.downloadURL  or self.spider.downloadURL.search(redurl) )
								and 	(not self.spider.downloadAvoidURL  or  not self.spider.downloadAvoidURL.search(redurl))
							)
						)
					if not urlOk: break # some url on the way didn't match the conditions => drop this page.
			
			# --------- checking if the content, the language, and the level of the page is ok
			self.encoding=self.page.encoding			
			contentOk=False
			if urlOk and self.level>=self.spider.levelFrom: # case 1: the url and the level are ok for downloading
				contentOk=True
				if self.spider.downloadRestriction and self.spider.pageRestriction: # testing whether the page content is ok
					contentOk = self.spider.pageRestriction.search(self.page.text)
					if contentOk: 
						if debug: print("content OK")
					else:
						if debug: print("page doesn't contain the page restriction.")
						self.msg += self.url+" doesn't match the page content restriction." #.encode("utf-8")
						self.notify()
				if contentOk and self.spider.ngram : # testing whether the content's language is ok
					score,lang = self.spider.ngram.guessLanguage(self.page.text, removeDecPunct=True)
					print ("oooooooooo", score, lang)
					lang = self.spider.langs.get(lang, "language not in list")
#					print "iii", lang, self.spider.langs
					contentOk=(self.spider.language == lang)					
					#print self.spider.language
					#print lang
					if debug:
						if contentOk: 
							if debug: print("language ok")
						else: 
							if debug: print("page doesn't match the required language:", self.spider.language,lang,score,self.page.text[:100])
							self.msg+= self.url+" seems to be in "+str(lang)+" and doesn't match the required language.\n"#.encode("utf-8")
							self.notify()
				if contentOk:
					if debug: print("now "+self.name+" puts that into the database:", self.url, self.page.source[:22], "...")
					################### the big moment: #################################
#					self.spider.mutex.lock() 
					rowid,  negNbSentences, negNbWords=self.spider.base.enterSource( self.page,  origin,   self.spider.dataOverwrite)
#					self.spider.mutex.unlock() 
				else:
					negNbSentences, negNbWords, rowid = 0, 0, 0
			else:
				negNbSentences, negNbWords, rowid = 0, 0, 0
				
			# --------- extracting the links from the page
			newLinks = []
			if (contentOk or not self.spider.pageLinkRestrict): # content was ok or it's allowed to take links from pages that did not match			
				# 1st case: pure bing spidering
				if self.spider.startWithSearchEngine and self.spider.onlySearchEngineResults:  newLinks = []
				# 2nd case: getting links from pages and link levels are ok  (because it's useless to take links from levels higher than what's allowed)
				elif (not self.spider.downloadRestriction) or self.level+1 <= self.spider.levelTo or self.spider.levelTo	<0 : 
				
					nl=self.page.selectLinks(self.spider.linkRestriction, 
										self.spider.linkDomain, self.spider.linkAvoidURL, 
										self.spider.links2do+self.spider.linksDone) # TODO: add current urls
					newLinks = [(url,self.level+1, rowid) for url in  nl]
				else :
					newLinks = [] ############# 
					if debug: print("no links taken")
		
			if not self.spider.running:
				if debug: print(self.name +" stops everything after putting "+self.url)#.encode("utf-8")
				self.spider.mutex.lock() ###########################
				if self.url in self.spider.currently: self.spider.currently.remove(self.url)
				if self.url not in self.spider.linksDone : self.spider.linksDone.append(self.url)
				self.spider.linksDone.extend(self.page.urls) # in case of redirects, the redirect links are added to the done links
				if contentOk: self.spider.updatesStats( self.page.nbSentences, self.page.nbWords,  negNbSentences,  negNbWords)
				else: self.spider.updatesStats( 0, 0,  0,  0)
				self.spider.mutex.unlock() #############################
				self.stopped=True
				continue
				
			self.spider.mutex.lock() ###########################

			self.spider.addLinks(newLinks)
			if self.url in self.spider.currently: self.spider.currently.remove(self.url)
			#if self.url not in self.spider.linksDone : self.spider.linksDone.append(self.url) # TODO: check that this is really not needed. should be in urlS
			#print "adding",self.page.urls,"to",self.spider.linksDone
			self.spider.linksDone.extend(self.page.urls) # in case of redirects, the redirect links are added to the done links
			if contentOk: self.spider.updatesStats( self.page.nbSentences, self.page.nbWords,  negNbSentences,  negNbWords)
			else: self.spider.updatesStats( 0, 0,  0,  0)
			
			self.spider.mutex.unlock() #############################

			if debug:
				print(self.name +" has done: "+self.url, end=' ')#.encode("utf-8")
				print(" - remaining links (at least):",len(self.spider.links2do+newLinks))
				
			########## end while ###################################

		if self.spider.running == False: # case: the whole spider stopped running
			self.status = self.name+" is done!"
			self.msg+=self.name+" is done!\n"
			self.notify()
			if debug: print(self.name +" is done!") # last url: "+self.url.encode("utf-8")
			return
		self.msg+=self.name+" is finishing up.\n"
		self.notify()
		if debug: print(self.name,"ends. it took",int(time() - self.starttime),"seconds.")
		self.c.endtrigger.emit()

#
#	def stop(self):
#		self.stopped = True

	def notify(self):
		if not self: return
		if time()-self.refreshtime>self.spider.nbThreads/2 or self.stopped : #0:#self.spider.nbThreads/2 : 
			s={ 'currentURL':self.url,
				'currentLevel':str(self.level),
				'encoding':str(self.encoding),
				'msg':str(self.msg),
				'status':str(self.status)
				}
			if debug: print("notify in spiderthread", s)
			self.c.signal.emit(s)
			self.msg=""
			self.refreshtime=time()

	def refreshView(self, s):
		self.spider.refreshView(s)


	def finished(self):
		self.spider.threadFinished()


	def moreBing(self):
		try:	
			newLinks,  total, webSearchUrl = bing.search(str(self.spider.searchEngineQuery),  str(self.spider.searchEngineAppId), self.spider.location,  self.spider.bingNum)
		except Exception as e: 
			if debug: print("moreBing went wrong",e)
			newLinks="error"
		if newLinks=="error":
			if debug: print("Bing Error!")
			self.msg+=self.name+" created an error accessing Bing! Are you connected to the internet?\n"
			self.notify()
			return []
		else:
			goodNewLinks = [(link,0, -1) for link in newLinks if (not self.spider.searchEngineFilter) or self.spider.searchEngineFilter.search(link)]
			self.spider.bingNum += len(newLinks)
			self.spider.numBingVisits+=1
			if debug:print("goodNewLinks",goodNewLinks)
			#TODO: if goodNewLinks == [], try again until no more results at all...

			return goodNewLinks



#
#	def surroundMatch(self, text, restriction,matchBefore,matchAfter):
#		return restriction.sub(matchBefore+r"\1"+matchAfter,text)
#

