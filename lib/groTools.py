# -*- coding: utf-8 -*-

"""
Module implementing GroTools.
"""

from PyQt5.QtWidgets import  QDialog
#from PyQt4.QtCore import pyqtSignature
#from PyQt5.QtCore.QCoreApplication import translate
from PyQt5.QtCore import QCoreApplication
from .Ui_groTools import Ui_GroTools
import re, codecs,  os,  subprocess,  shlex
from time import sleep
#from htmlPage import sentenceSplit

from sys import platform
from PyQt5 import QtWidgets
from . import groressources_rc


#try:
	#from pymmseg import mmseg
#except:
	#import mmseg

#import pattern

debug=False
#debug=True

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QCoreApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QCoreApplication.translate(context, text, disambig)


class GroTools(QDialog, Ui_GroTools):
	"""
	Class documentation goes here.
	"""
	def __init__(self, base, textualization, parent):
		"""
		Constructor
		"""
		QDialog.__init__(self)
		
		self.setupUi(self)
		self.progressBar.hide()
		self.infoLabel.setText("<i>'"+textualization+ "'</i> "+_translate("GroTools", "is the input view", None))
		
		self.allcolumns=base.getTextColumns(textualization)
		self.base=base
		self.textualization=textualization
		(self.textualId, )=next(self.base.select( "select id from textualizations where name='"+self.textualization+"';"))
		
		#self.textcolumns=parent.textcolumns
		self.columns=parent.textcolumns
		#self.columnslabel.setText(_translate("GroTools", "source columns: ", None)+", ".join(self.columns))
		self.columnslabel.setText(self.tr("source columns: ")+", ".join(self.columns))
		
		
		lemmatizeLanguages={"en":"English", "de":"German", "es":"Spanish", "nl":"Dutch","fr":"French","it":"Italian"}
		for l in sorted(lemmatizeLanguages.values()):
			self.language.addItem(l)
		self.language.setCurrentIndex(1)
		
		self.urheenfile=""
		self.urheenoption=""
		
		self.reslash=re.compile("\/",re.U+re.I+re.M)
		self.reslashinv=re.compile("&slash;",re.U+re.I+re.M)
		self.reponct=re.compile(r"((</span>)? (<span class='\w+'>)|(</span>) (<span class='\w+'>)?| )(?P<punct>[.,;()])",re.U+re.I+re.M)
		self.renewline=re.compile("\n+",re.U+re.I+re.M)
		self.sentenceSplit=parent.sentenceSplit
		
		if parent.rowconditions: 		wherecondi=" WHERE "+parent.rowconditions
		else: wherecondi=""
		self.selectstatement="SELECT rowid,"+", ".join(self.columns)+" FROM "+self.textualization+wherecondi+" ;"
		self.selectcountstatemnt="SELECT count(rowid) FROM "+self.textualization+wherecondi+" ;"
		(self.totalnum,)=next(self.base.select( self.selectcountstatemnt))
		
		
		#if parent.rowconditions: 		wherecondi=" WHERE "+parent.rowconditions+" and rowid=?"
		#else:					wherecondi=" WHERE rowid=?"
		#self.rowidselectstatement="SELECT "+", ".join(self.columns)+" FROM "+self.textualization+wherecondi+";"
		
		#self.currentselect=self.base.select( self.selectstatement)
		
		self.insertColumns=[]
#		self.textid2textname=self.base.getTextColumns(self.textualization)
#		self.textname2textid=dict((v,k) for k,v in self.textid2textname.iteritems())
#		self.insertTextIds=[self.textname2textid[c]  for c in self.columns]
		
		
		self.refind=None
		self.currentTestRow=1
		self.replacements=0
		self.replacedPages=0
		
		self.makeCurrentExampleText()
		
		self.lemma.clicked.connect(self.lemmaClicked)
		self.tag.clicked.connect(self.tagClicked)
		self.lemmatag.clicked.connect(self.lemmatagClicked)
		self.complete.clicked.connect(self.completeClicked)
		
		self.goButton.setEnabled(True)
		
	def lemmaClicked(self):		self.affix.setText("_lem")
	def tagClicked(self):		self.affix.setText("_tag")
	def lemmatagClicked(self):	self.affix.setText("_lt")
	def completeClicked(self):	self.affix.setText("_a")

	
	#@pyqtSignature("")
	def on_goButton_clicked(self):
		self.goButton.setEnabled(False)
		
		
		if self.toolTabs.currentIndex() ==0: ##################### euro languages
			self.infoLabel.setText("lemmatizing")
			
			self.prepareColumns(self.affix)
			
			
			if self.language.currentText()=="Dutch": from pattern.nl import parse
			if self.language.currentText()=="English": from pattern.en import parse
			if self.language.currentText()=="French": from pattern.fr import parse
			if self.language.currentText()=="German": from pattern.de import parse
			if self.language.currentText()=="Italian": from pattern.it import parse
			if self.language.currentText()=="Spanish": from pattern.es import parse
			
			self.parse=parse
			
			self.makeNewColumns(self.parseEuro, self.insertTextIds)
				
		elif self.toolTabs.currentIndex() ==1: ##################### chinese and english
			
			
			if self.mmseg.isChecked():
				
				mmseg.dict_load_defaults()
				
				self.infoLabel.setText("mmseg word segmentation")
				self.prepareColumns(self.segaffix)
				print("self.insertTextIds",self.insertTextIds)
				self.makeNewColumns(self.segmentChineseMmseg,  self.insertTextIds)
				
			else:
				if platform.startswith("linux"):		self.urheenfile="urheen"
				elif platform.startswith("win"):		self.urheenfile="urheen.exe"
				
				self.prepareColumns(self.segaffix)
				message="urheen is very slow around 33% progress!)\nPlease be patient"
				if self.urheenseg.isChecked():
					self.infoLabel.setText(message)
					self.urheenoption=" -i urheen.in.txt -o urheen.out.txt -t seg"
				elif self.urheensegpos.isChecked():
					self.infoLabel.setText(message)
					self.urheenoption=" -i urheen.in.txt -o urheen.out.txt -t segpos"
				elif self.urheentok.isChecked():
					self.infoLabel.setText(message)
					self.urheenoption=" -i urheen.in.txt -o urheen.out.txt -t tok"
				elif self.urheentag.isChecked():
					self.infoLabel.setText(message)
					self.urheenoption=" -i urheen.in.txt -o urheen.out.txt -t tokpos"
				self.makeNewColumnsUrheen()
				
		elif self.toolTabs.currentIndex() ==2: ##################### replacement

			self.infoLabel.setText("replacing")
			self.textid2textname=self.base.getTextColumns(self.textualization)
			#print self.textid2textname
			self.textname2textid=dict((v,k) for k,v in self.textid2textname.items())
			#print self.textname2textid
			self.sourceTextIds=[self.textname2textid[c]  for c in self.columns]
			findtext=str(self.find.text())
			if findtext:
#			try:
				self.refind=re.compile(findtext, re.M+re.U+re.I)
				self.makeNewColumns(self.replacing, self.sourceTextIds)
#			except Exception, e:
#				self.infoLabel.setText("problem with regular expression "+unicode(e))
#				self.goButton.setEnabled(True)
#				self.progressBar.hide()
#				return

		todo=self.base.reqs.qsize()
		self.progressBar.setMaximum(todo)
		
		while not self.base.reqs.empty():
			if debug: print("not empty",self.base.reqs.qsize())
			self.progressBar.setValue(todo-self.base.reqs.qsize())
			sleep(1)
			
		self.goButton.setEnabled(True)
		self.progressBar.hide()
		
		self.done(11)
		
		
	
	def prepareColumns(self,  affix):
		if debug:print("prepareColumns", affix)
		self.insertColumns=[c+str(affix.text()) for c in self.columns]

		
		count=len(self.allcolumns)
		if debug:
			print("insertColumns", self.insertColumns)
			print("self.allcolumns", self.allcolumns)
		for ic in self.insertColumns:
			print("***",list(self.allcolumns.values()),ic)
			if ic not in list(self.allcolumns.values()):
				count+=1
				self.base.execute("insert into textcolumns(name) values  (?) ;", (ic, )) # put name insertcolumn
				self.base.execute("insert into textualcolumns(textualid,columnid) values  (?,?) ;", (self.textualId, count, ))
				self.base.execute("--commit--")
				print("insert into textcolumns(name) values  (?) ;", (ic, ))
				print("insert into textualcolumns(textualid,columnid) values  (?,?) ;", (self.textualId, count, ))
		while not self.base.reqs.empty(): pass
		sleep(1) # wait for the database to close completely before giving back the textualName
		
		self.textid2textname=self.base.getTextColumns(self.textualization)
		print("self.textid2textname", self.textid2textname)
		self.textname2textid=dict((v,k) for k,v in self.textid2textname.items())
		#print "self.textname2textid", self.textname2textid
		self.insertTextIds=[self.textname2textid[c]  for c in self.insertColumns]
		self.sourceTextIds=[self.textname2textid[c]  for c in self.columns]
		if debug: print("insertTextIds", self.insertTextIds)
#		sys.exit()
		
	
	def makeNewColumns(self, newfunction, textids):
		"""
		called when the go button is clicked
		"""
		
		#(totalnum,) =self.base.select("select count(*) from sources;").next()
		self.progressBar.setMaximum(self.totalnum)
		self.progressBar.show()
		if debug: print("self.selectstatement",self.selectstatement)
		sele=self.base.select(self.selectstatement)
		#go extract the part we choose
		while True:	
			c=0
			
			try:columns = next(sele)
			except:break
			
			i=columns[0]
			for columncontent in columns[1:]:
				if debug:
					try:print("oldcolumn",str(columncontent)[:100])
					except:pass
#				try: (columncontent, )=columncontent
#				except:pass
#				break
				newcolumn=newfunction(str(columncontent))
				if debug: 
					try:print("newcolumn",textids[c], newcolumn[:100]) # in try to avoid encoding problems
					except:pass
				nbs, nbc = self.computeStat(newcolumn)
				self.base.enterUpsert( i, self.textualId,  textids[c],  newcolumn, nbs, nbc)
				c+=1
			
			
#			self.base.enterNewText(i, self.textualId, self.columnId, textcontent, nbSentences, nbWords, self.overwrite)
			
			self.progressBar.setValue(i)
		
		if debug: print("makeTextual", self.textualization, self.textualId)
		self.base.makeTextual(self.textualization, self.textualId)
		# self.base.execute("--commit--")
	
	def makeNewColumnsUrheen(self):
		"""
		called when the go button is clicked
		"""
		self.progressBar.setMaximum(self.totalnum)
		self.progressBar.show()
		
		urheenin=codecs.open(os.path.join("lib", "tools", "urheen.in.txt"), "w", "GB18030",  'replace')	
		
		sele=self.base.select(self.selectstatement)
		#go extract the part we choose
		#for i in range(1, totalnum+1):
		rowids=[]
		while True:	
			c=0
			
			try:columns = next(sele)
			except:break
			
			i=columns[0]
			rowids+=[i]
			# print self.rowidselectstatement
			#if debug: 
				#try:print self.rowidselectstatement, (str(i), )
				#except:pass
			#try:columns = self.base.select(self.rowidselectstatement, (str(i), )).next()
			#except:continue
			for columncontent in columns[1:]:
				if debug: 
					try:print(i,"columncontent", columncontent[:100])
					except:pass
				urheenin.write(columncontent+"\n<grocolumn>\n")
				
			urheenin.write("<grorow>\n") #columncontent
			
			self.progressBar.setValue(i/3)
		urheenin.close()
		
		if debug: print([os.path.join( os.getcwd(),"lib", "tools", self.urheenfile)] + shlex.split( self.urheenoption)) 
		if platform.startswith("linux"):		command=" ".join([os.path.join( os.getcwd(),"lib", "tools", self.urheenfile)] + shlex.split( self.urheenoption) )
		else:									command=[os.path.join( os.getcwd(),"lib", "tools", self.urheenfile)] + shlex.split( self.urheenoption)	
		p1 = subprocess.Popen(command , shell=True, stdout=subprocess.PIPE,  cwd=os.path.join( os.getcwd(),"lib", "tools")) 
		
		p1.stdout.read() # wait until finished
		# sleep(2)
		# sys.exit()
		if debug: print("urheen has finished")
		# sys.exit()
		urheenout=codecs.open(os.path.join("lib", "tools", "urheen.out.txt"), "r", "GB18030",  'replace')
		
		column=""
		i=1
		c=0
		rid=rowids.pop(0)
		if debug: print("self.insertTextIds[c]", self.insertTextIds)
		
		for line in urheenout:
			lstrip=line.strip()
			if lstrip in ["<grorow>" ,"< grorow >" ,"</PU grorow/NR >/PU",  "<grorow>/:" ]:
				nbs, nbc = self.computeStat(column)
				i+=1
				c=0
				if rowids:rid=rowids.pop(0)
				#else: print "end"
				#print "rid",rid
				self.progressBar.setValue(self.totalnum*2/3+i/3)
			elif lstrip in ["<grocolumn>" , "< grocolumn >",  "</PU grocolumn/NR >/PU",  "<grocolumn>/:"]  : # bullshit analysis of tags by urheen
				nbs, nbc = self.computeStat(column)
				if debug:print(i, c, self.insertTextIds, self.insertTextIds[c], "____", len(rowids), column[10:])
				self.base.enterUpsert( rid, self.textualId,  self.insertTextIds[c],  column, nbs, nbc)
				column=""
				
				c+=1
#				print "c", c
			else:
				column+=line

		 
		if debug: print("makeTextual", self.textualization, self.textualId)
		self.base.makeTextual(self.textualization, self.textualId)
		# self.base.execute("--commit--")
	
	
	
	def parseEuro(self,  text):
		""" 
		gives back the parsed text for given text
		type of text given back depends on clicked choice
		"""
#		print text, type(text)slash
		text = self.reslash.sub("&slash;",text)
		
		pc = self.parse(text, tokenize=True, tags=True, chunks=True, relations=True, lemmata=True, light=False)
		outs=""
		if self.complete.isChecked():
			outs = self.reslashinv.sub("/",pc)
			
			
		elif self.lemma.isChecked():
			for li in pc.split("\n"):
				li=li.strip()
				if li:
					for t in li.split():
						try:
							w,cat,ch,vp,php,l = t.split("/")
							outs+=self.reslashinv.sub("/",l)+" "
						except:
							self.infoLabel.setText(_translate("GroTools", "error with token", None)+" '"+str(t)+"'")
					outs+="\n"	
		elif self.tag.isChecked():
			for li in pc.split("\n"):
				li=li.strip()
				if li:
					for t in li.split():
						try:
							w,cat,ch,vp,php,l = t.split("/")
							outs+=self.reslashinv.sub("/",cat)+" "
						except:
							self.infoLabel.setText(_translate("GroTools", "error with token", None)+" '"+str(t)+"'")
					outs+="\n"
		elif self.lemmatag.isChecked():
			for li in pc.split("\n"):
				li=li.strip()
				if li:
					for t in li.split():
						try:
							w,cat,ch,vp,php,l = t.split("/")
							outs+=self.reslashinv.sub("/",l+"-"+cat)+" "
						except:
							self.infoLabel.setText(_translate("GroTools", "error with token", None)+" '"+str(t)+"'")
					outs+="\n"

		return outs
		
	
	def segmentChineseMmseg(self,  text):
		""" 
		gives back the space separated tokens of text, using mmseg
		"""
		
		algor = mmseg.Algorithm(text.encode("utf-8"))
		return " ".join([tok.text for tok in algor]) # .decode("utf-8","ignore")
	
	
	
	def replacing(self,  text):
		""" 
		replaces the text by regex
		"""
		t=str(self.replace.text()) # the replacement text field
		# print t
		nt,rep = self.refind.subn(t, text)
		self.replacements+=rep
		if rep: self.replacedPages+=1
		return nt
		
		
		
#		return self.refind.sub(unicode((self.replace.text()), text))
		
	
	
	#@pyqtSignature("QString")
	def on_language_currentIndexChanged(self, p0):
		"""
		Slot documentation goes here.
		"""
		pass
	
	#@pyqtSignature("QString")
	#@pyqtSlot(str)
	def on_affix_textChanged(self, p0):
		"""
		Slot documentation goes here.
		"""
		if debug:print("on_affix_textChanged")
		affix=str(p0)
		if len(affix)==0:
			self.infoLabel.setText(_translate("GroTools", "Please enter an affix for the new columns.", None))
			self.goButton.setEnabled(False)
		else:
			for c in self.columns:
				newColumnName=c+affix
#				if outColumnName<'A' or 'Z'<outColumnName[0] <'a' or outColumnName[0] >'z':
#					self.infoLabel.setText("Illegal Name . Please start with a letter")
#					self.goButton.setEnabled(False)
				if newColumnName in list(self.allcolumns.values()): 
					self.infoLabel.setText(_translate("GroTools", "Existing columns will be overwritten!", None))
					self.goButton.setEnabled(True)
					break
				else:
					self.infoLabel.setText("")
					self.goButton.setEnabled(True)
	
	#@pyqtSignature("QString")
	def on_find_textEdited ( self, p0):
		self.findFound.setText("")
		try:
			retest=re.compile(str(p0),re.U+re.I+re.M)
			self.findFeedback.setText("")
			
		except:
			self.findFeedback.setText("<span style='color:red'>"+_translate("GroTools", "syntax error in regular expression", None)+"</span>")
			return
		if len(p0)==0:
			self.findFound.setText("")
			return
		if debug:
			print(self.currentExampleText[:100])	
			print(type(self.currentExampleText))
		testmatch=retest.search(self.currentExampleText)
		if debug: print(testmatch,testmatch==None)
		if testmatch:
			matched = self.currentExampleText[max(0,testmatch.start()-10):testmatch.start()]
			matched += "<span style='color:red'>"+self.currentExampleText[testmatch.start():testmatch.end()]+"</span>"
			matched += self.currentExampleText[testmatch.end():testmatch.end()+10]
			matched=self.renewline.sub(" ",matched)
			#print matched
			#print testmatch.group(0)
			self.findFound.setText(matched)
		else:
			self.findFound.setText("<span style='color:grey'>☹</span>")
			
	#@pyqtSignature("")
	def on_nextFindButton_clicked(self):		
		
		#self.currentTestRow+=1
		self.makeCurrentExampleText()
		
		self.on_find_textEdited (self.find.text())
	
	def makeCurrentExampleText(self):
		#try:	rowconditions self.rowidselectstatement, self.currentTestRow, 
		#print self.selectstatement
		try:res=next(self.currentselect)
		except: # ende der fahnenstange
			self.currentselect=self.base.select( self.selectstatement)
			try:res=next(self.currentselect)
			except:res="" # empty database
		#res=self.base.select( self.rowidselectstatement, (str(self.currentTestRow),)).next()
		self.currentExampleText=" ".join([str(r) for r in res])
		#except:	self.currentExampleText=""
		
		
		
		
		
		
		
#	@pyqtSignature("QString")
#	def on_inputColumn_currentIndexChanged(self, p0):
#		"""
#		Slot documentation goes here.
#		"""
#		self.outputColumn.setText(p0+"_lemmatized")
	
	#@pyqtSignature("")
	def on_buttonBox_accepted(self):
		"""
		Slot documentation goes here.
		"""
		# TODO: not implemented yet
		raise NotImplementedError
	
	#@pyqtSignature("")
	def on_buttonBox_rejected(self):
		"""
		Slot documentation goes here.
		"""
		# TODO: not implemented yet
		raise NotImplementedError

	
	def computeStat(self,  text):
		"""
		when computing the nbWords, we just calculate the number of characters
		
		"""
		
		return len(self.sentenceSplit.findall(text)), len(str(text)) 
		
		
				
				
				
if __name__ == "__main__":
	
	subprocess.call("urheen.exe -i urheen.in.txt -o urheen.out.txt -t seg ", shell=True, stdout=subprocess.PIPE,  cwd=os.path.join( os.getcwd(), "tools") )
