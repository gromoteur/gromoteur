#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, os, subprocess
from PyQt5.QtGui import QColor
from PyQt5 import QtCore
from PyQt5.QtCore import QDateTime, pyqtSlot, pyqtSignal
#from PyQt4.QtCore import Qt

#from nexicoMain import Nexico

from gensim.corpora.dictionary import Dictionary

#from collections import OrderedDict
from itertools import permutations
import platform

if platform.system()=="Linux":
	if platform.architecture()[0]=='64bit': specfile="specificity64"
	elif platform.architecture()[0]=='32bit': specfile="specificity32"
elif platform.system()=="Windows":
	if platform.architecture()[0]=='64bit': specfile="specificity64.exe"
	elif platform.architecture()[0]=='32bit': specfile="specificity32.exe"
elif platform.system()=="Darwin": # TODO: check how this works!!
	if platform.architecture()[0]=='64bit': specfile="specificity.mac"
	elif platform.architecture()[0]=='32bit': specfile="specificity.mac"
	else:specfile="specificity.mac"

#TODO: configuration:
#lower=True # put all tokens to lower case
mulcoljoiner="\n" # elements beween columns
#threshold=5 # significance p-value in %
#wordlimit=r"([^\w\/]+)"

class NexicoBase(QtCore.QThread):
	"""
	
	"""
	progressChanged = pyqtSignal(int, str)
	progressFinished = pyqtSignal()
	
	def __init__(self, groWindow=None): 
#		sectionlimit=r"[\r\n]+", 
#	def __init__(self, filename, encoding, sectionlimit=r"m", wordlimit=r"\W"):
		super(NexicoBase, self).__init__()
		#QtCore.QThread.__init__(self)
		#print self
		#print self.progressChanged
		self.groWindow=groWindow
		self.yieldFunction=self.oneDocAtATime
		self.rowIdFunction=self.docForRowId
		#self.rewordlimit=re.compile(wordlimit, re.U+re.M)
		#print groWindow.config["configuration"]["wordlimit"]
		if groWindow:
			self.groups = self.groWindow.groups
			self.grouping=self.groups and self.groWindow.useGroupsCheckBox.isChecked()
			if self.grouping:	self.nbSections=len(self.groups)
			else:		self.nbSections=groWindow.nbFilteredRows
			self.groBase = self.groWindow.base
			self.selectstatement = self.groWindow.selectstatement
			#self.wordlimit
			self.rewordlimit=re.compile(str(groWindow.config["configuration"]["wordlimit"]), re.U) 
			self.threshold=int(groWindow.config["configuration"]["threshold"])
			self.lower=groWindow.config["configuration"]["lower"]=="yes"
			self.specColor=QColor()
			self.specColor.setRgba(int(groWindow.config["configuration"]["specColor"]))
			self.freqColor=QColor()
			self.freqColor.setRgba(int(groWindow.config["configuration"]["freqColor"]))
			
			
			# TODO: make multi line an option! maybe replace return by .replace("\n",u"↩") as in tab file output
		else:
			pass
			#TODO:
			
			
			
		self.d=Dictionary() # token => tokeni
		self.d.freqs={} # tokeni => total frequency in the corpus
		self.d.idtotoken={} # tokeni => token
#		self.sectrasts=[]
		self.sectrast=None
		
		
#		self.sectionlimit=sectionlimit
		#self.wordlimit=wordlimit
		#self.threshold=threshold
	
	def run(self):
		self.sectrast=SectRast(self, self.threshold, lower=self.lower)


	def oneDocAtATime(self):
		"""
		returns a triple: id, name, plain text
		plaintext = "\n"-join of all visible columns
		"""
		if self.groWindow and self.groups and self.groWindow.useGroupsCheckBox.isChecked():
			
			for ri, g in enumerate(sorted(self.groups, key=lambda k: len(self.groups[k]), reverse=True )):
								
				#grouptext=self.groWindow.getgrouptext(g)
				grouptext=self.getgrouptext(g)
				yield ri,g,grouptext
			
				
		else:
			for entry in self.groBase.select(self.selectstatement):
				#yield int(entry[0])-1,"\n".join([unicode(col) for col in entry[1:]]) unicode
				#print entry
				yield int(entry[0])-1,entry[1],mulcoljoiner.join([str(col) for col in entry[1:]])
			
			
	def docForRowId(self, id):
		#id,url=idurl
		if self.grouping:
			
			grouptext=self.getgrouptext(self.sectrast.urls[self.sectrast.sections.index(id)])
			return grouptext
		else:
			entry =next(self.groBase.select( self.groWindow.rowidselectstatement, (str(id+1),) ))
			#print entry unicode
			return "\n".join([str(col) for col in entry])
	

	def getgrouptext(self,g):
		commarowids=",".join([str(i) for i in self.groups[g]])
		if self.groWindow and self.groWindow.rowconditions: 	wherecondi=" WHERE "+self.groWindow.rowconditions+" and rowid in ({rowids})"
		else:						wherecondi=" WHERE rowid in ({rowids})"
		self.groWindow.groupselectstatement=("SELECT  "+", ".join(self.groWindow.columns)+" FROM "+self.groWindow.textualization+wherecondi+" ;").format(rowids=commarowids) # rowid, url,
		grouptext=""
		for rr in self.groBase.select( self.groWindow.groupselectstatement ):
			for i, col in enumerate(self.groWindow.columns):
				piece=str(rr[i]) #[:50]
				if col:
					grouptext+=piece+"\n"
		return grouptext
	
	
	
			

		
class SectRast(object):
	"""
	liste de sections pour une base donnée
	sdelimit: délimiteur des sections	
	"""
	def __init__(self, nexicoBase, threshold, ngra=5,lower=True):
		self.base = nexicoBase
		self.nbSections = nexicoBase.nbSections
		self.threshold=threshold
		self.sections=[] # simple list of sections containing just the ids
		self.urls=[] # same length list as section containing tooltip info for the section
		self.bows={} # section id => bow : each bow (bag of words) is a dict: tokenid ==> freq
		self.collocs={} # ngra => { wordidb => { wordidc => nbr of occurrences of c around b} }
		self.nrtoks={} # section id => nrtoks
		self.ids={} # section id => list of ids (for the computation of ngrams)
		self.size=0 #in tokens
#		self.numChars=0 # in chars
#		self.base.d.freqs={} # tokeni => total frequency in the corpus
		self.specificity={} # tokeni => {tuple of sections => specificity of the token in this section }
		self.specollocs={} # ngra => { tokeni => { tokeni => specificity of the nbr of occurrences of c around b} }
		counter=0.0
		for si, url, t in nexicoBase.yieldFunction(): # go through each page
			self.sections+=[ si ]
			self.urls+=[ url ]
			if lower:	t=t.lower()
			toks = nexicoBase.rewordlimit.split(t)
			#else:		toks = nexicoBase.rewordlimit.split(t)
			
			self.nrtoks[(si)]=len(toks)
			self.size+=self.nrtoks[(si)]
			
			di=dict(self.base.d.doc2bow(toks, allow_update=True))
			self.bows[si] = di # , return_missing=True)
			
			#print self.base.d.token2id 
			try:self.ids[si]=[self.base.d.token2id[tt] for tt in toks] # make list of token ids correponding to text
			except:self.ids[si]=[self.base.d.token2id[tt] for tt in toks]#.encode("utf-8")
			self.makecollocs(self.ids[si],ngra,self.collocs)
			
			self.progress(counter/self.nbSections*10.0, "Reading the database into memory...")
			counter+=1
		self.base.d.idtotoken = dict((id, token) for token, id in self.base.d.token2id.items()) # to have it precomputed
		self.computeStandardSpecificity()

	def progress(self,i,t=""):
		self.base.progressChanged.emit(i,t)
		
	def makecollocs(self,tlist,n,d={},multipleCount=False):
		"""
		tlist is a list of token ids for the given section, e.g. [7, 0, 20, 19, 9, 14, 13, 24, 17, 18, 15, 23, 16, 21, 5, 22, 9]
		n is an integer, e.g. 5
		d is self.collocs, explained above
		"""
		#print "makecollocs",tlist,n
		#print d
		d[n]=d.get(n,{}) # initialize ngra colloc
		for x in tlist: d[n][x]=d[n].get(x,{}) # initialize colloc dics if not already present
		if multipleCount:
			for ngram in zip(*[tlist[i:] for i in range(n)]): # miracle line making ngrams
				# for each different couple (1,2), (2,1), but not (1,1) add one encounter in the same ngram
				#print "ngram",ngram
				for x,y in permutations(ngram,2):
					#print x,y
					d[n][x][y]=d[n][x].get(y,0)+1
		else: 	# idea: first take all combinations, then only the ones with the newest (last) token id.
			ngrams=list(zip(*[tlist[i:] for i in range(n)]))
			#print "___",ngrams
			#print "ngram",ngrams[0]
			for x,y in permutations(ngrams[0],2):
					#print x,y
					d[n][x][y]=d[n][x].get(y,0)+1
			for ngram in ngrams[1:]:
				#print "ngram",ngram
				y=ngram[-1]
				for x in ngram[:-1]:
					#print x,y
					d[n][x][y]=d[n][x].get(y,0)+1
					#print y,x
					d[n][y][x]=d[n][y].get(x,0)+1
	
	def computeStandardSpecificity(self):
		"""
		calcule la spécificité de chaque section et pour chaque type
		
		this computes many specificities at once: one per section (a simple tuple, consisting of one section only)
		"""
		self.progress(10.0,"Computing the frequency and specificity of all words in all sections...")
		# création du fichier pour l'exécutable C, format indiqué dans Notice Spectab
		outable=open(os.path.join("lib", "tools", "TabLexIn.txt"), "w")		
		
		# écriture des paramères
		# 1ère ligne : 		
		#		nb de types (= tokens différents), nb de sections, nb de tokens, 1, seuil
		outable.write("{difftok}\t{sects}\t{nrtoks}\t1\t{threshold}\n".format( difftok=len(self.base.d), 
												sects=len(self.sections),
												nrtoks=self.size, 
												threshold=self.threshold
										))
		# 2e ligne : pour chaque section, sa longueur
		outable.write("\t".join([str(self.nrtoks[si]) for si in self.sections])+"\n")
		
		# pour chaque type, une ligne contenant le  nombre d'occurrences de ce type dans la section correspondante:
		# tokenid, totfreq of token, [freq in each section] 
		kn=len(list(self.base.d.keys()))
		k=0.0
		for tokeni in  sorted(self.base.d.keys()):
			k+=1
			freq=sum([self.bows[si].get(tokeni, 0) for si in self.sections])
			self.base.d.freqs[tokeni]=freq
			outable.write("\t".join([ str(tokeni), str(freq)  ]+[str(self.bows[si].get(tokeni, 0) ) for si in self.sections]) + "\n")
			self.progress(10+k/kn*70,"Computing the frequency and specificity of all words in all sections...")
			
		outable.close()
		
		# fichier tableau terminé
		
		self.progress(80.0)
		# lancement de l'exéctuable
		p1 = subprocess.Popen([os.path.join( os.getcwd(),"lib", "tools/", specfile)],shell=True, stdout=subprocess.PIPE, cwd=os.path.join( os.getcwd(),"lib", "tools/") )
		p1.stdout.read() # wait until finished
		self.progress(92.0)
		# lecture des résultats
		intable=open(os.path.join("lib","tools","Resuspec.txt"), "r")
		
		for line in intable:
			lis=line.split()
			try:self.specificity[ int(lis[0])   ]=dict([( (self.sections[int(i)], ), int(j)) for i, j in enumerate(lis[2:])  ])
			except:print("bloed")
		intable.close()
		
		self.progress(96.0)
	

	
	def computeOtherSpecificity(self, sections, progress=None):
		"""
		sections is a tuple containing the sections
		here we only compute the specificiy of all words in relation to this tuple (of sections)
		
		(whose unification, the access, is the part we want to compute the specificity of here)
		the function adds the tuple of sections to the keys of the specificity dictionary
		"""
#		print "computeOtherSpecificity", sections
		
		if not progress:progress=self.progress
		progress(5.0)
		outable=open(os.path.join("lib", "tools", "TabLexIn.txt"), "w")	
		# écriture des paramères
		# 1ère ligne : 		
		#		nb de types (= tokens différents), nb de sections, nb de tokens, 1, seuil
		outable.write("{difftok}\t{sects}\t{nrtoks}\t1\t{threshold}\n".format( 	difftok=len(self.base.d), 
										sects=1,
										nrtoks=self.size, 
										threshold=self.threshold
										))
										
		selectionTokenNr=sum([ self.nrtoks[si] for si in sections])
		progress(10.0)
		# 2e ligne : pour chaque selection de sections, sa longueur
		outable.write(str(selectionTokenNr)+"\n")
		
		# pour chaque type, une ligne contenant le  nombre d'occurrences de ce type dans la selection de sections correspondants:
		# tokenid, totfreq of token, [freq in each section] 
		kn=len(list(self.base.d.keys()))
		k=0.0
		 
		for tokeni in  sorted(self.base.d.keys()):
			selectionfreq=sum([self.bows[si].get(tokeni, 0) for si in sections])
			outable.write("\t".join([ str(tokeni), str(self.base.d.freqs[tokeni]), str( selectionfreq )  ] ) + "\n")
			progress(10+k/kn*70)
			k+=1

		outable.close()
		
		progress(80.0)
		
		p1 = subprocess.Popen([os.path.join( os.getcwd(),"lib", "tools/", specfile)],shell=True, stdout=subprocess.PIPE, cwd=os.path.join( os.getcwd(),"lib", "tools/") )
		p1.stdout.read() # wait until finished
		
		progress(92.0)
		# lecture des résultats
		intable=open(os.path.join("lib","tools","Resuspec.txt"), "r")
		for line in intable:
			lis=line.split()
			self.specificity[  (int(lis[0]))   ][sections] = int(lis[2])
			
		intable.close()
		progress(94.0)
		
	def computeCollocations(self, ngra):
		"""
		ngra is an integer
		"""
		#print "___________________",self.collocs
		if ngra not in self.collocs: # first time this ngra (if ngra changes, all the collocations have to be recomputed, the old ones are kept in memory
			for i,si in enumerate(self.sections):
				self.makecollocs(self.ids[si],ngra,self.collocs)
				self.progress(i/self.nbSections*100.0, "Making ngrams...")
		
		self.specollocs[ngra]=self.specollocs.get(ngra,{}) # initialize ngra colloc
		
		
		#print "llll"
		self.progress(5.0, "Computing collocations...")

		outable=open(os.path.join("lib", "tools", "TabLexIn.txt"), "w")
		sortedtokenis = sorted(self.base.d.keys())
		difftok=len(sortedtokenis)
		# écriture des paramères
		# 1ère ligne : 		
		#		nb de types (= tokens différents), nb de sections, nb de tokens, 1, seuil
		outable.write("{difftok}\t{sects}\t{nrtoks}\t1\t{threshold}\n".format( difftok=difftok, 
									sects=difftok,
									nrtoks=self.size, 
									threshold=self.threshold
										))
										
#		accessLength=sum([self.sectrast.tokens[token].count(s) for s in self.selection])
		#selectionTokenNr=sum([ self.nrtoks[si] for si in sections])
		self.progress(10.0, "Computing collocations (writing ngram frequency tables)...")
		# 2e ligne : pour chaque selection de sections, sa longueur
		
		outable.write("\t".join([str(self.base.d.freqs[btokeni]*ngra) for btokeni in sortedtokenis])+"\n") # TODO: think about this size of section!
		
		# pour chaque type, une ligne contenant le  nombre d'occurrences de ce type dans la selection de sections correspondants:
		# tokenid, totfreq of token, [freq in each section] 
		k=0.0
		 
		for ctokeni in  sortedtokenis:
			#freqinngrams=sum([self.bows[si].get(ctokeni, 0)  for ctokeni in sortedtokenis])
			#outable.write("\t".join([ str(tokeni), str(self.base.d.freqs[tokeni]), str( selectionfreq )  ] ) + "\n")
			
			outable.write("\t".join([ str(ctokeni), str(self.base.d.freqs[ctokeni])  ]+[str(self.collocs[ngra][ctokeni].get(btokeni, 0) ) for btokeni in sortedtokenis]) + "\n")
			
			self.progress(10+k/difftok*70,"Computing the frequency and specificity of all words combinations...")
			k+=1
			

		outable.close()
		self.progress(80.0, "Computing collocations (computing specificities)...")
		
		p1 = subprocess.Popen([os.path.join( os.getcwd(),"lib", "tools/", specfile)],shell=True, stdout=subprocess.PIPE, cwd=os.path.join( os.getcwd(),"lib", "tools/") )
		p1.stdout.read() # wait until finished
		
		self.progress(92.0, "Computing collocations (reading specificities into memory)...")
		
		# lecture des résultats
		intable=open(os.path.join("lib","tools","Resuspec.txt"), "r")
		
		for line in intable:
			lis=line.split()
			try:self.specollocs[ngra][ sortedtokenis[int(lis[0])]   ] = dict([( sortedtokenis[int(i)], int(j)) for i, j in enumerate(lis[2:]) if int(j)  ])
			except:print("bloed")
		intable.close()
		
		intable.close()
		self.progress(94.0,"Filling table...")
		#print self.specollocs[ngra]
	
	def __repr__(self):
		return "SectRast ("+str(len(self.sections))+" sections, "+str(self.size)+" tokens, "+str(len(self.tokens))+" different tokens)"
		

#def ramsch():
if __name__ == "__main__":
	rewordborder=re.compile(r'(\W+)', re.U)

	#toks=rewordborder.split(codecs.open("corpora/werther.de.txt","r","utf-8").read())
	
	
	#d=Dictionary()
	#print d
	#print "___"
	#print d.doc2bow("a b b c".split(), allow_update=True, return_missing=True)
	#bow, mis = d.doc2bow(toks, allow_update=True, return_missing=True)
	#print d
	#print "((("
	#print "bow", dir(bow)
	#print "d.token2id", d.token2id
	#print sorted([(tokenid, d[tokenid], docfreq) for tokenid, docfreq in bow if docfreq > 10], key=lambda x: x[2])
	#print sorted(d.dfs.iteritems(), key=operator.itemgetter(1))
	#print d.dfs

