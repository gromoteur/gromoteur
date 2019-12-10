# -*- coding: utf-8 -*-

"""
Module implementing Exporter.
"""

from PyQt5.QtWidgets import  QDialog
from PyQt5.QtCore import QDateTime, pyqtSlot, pyqtSignal

from PyQt5 import QtCore, QtWidgets

from .Ui_exporter import Ui_Exporter
import sys,  webbrowser,  os,  codecs, re, errno
from datetime import date
#from time import time,  sleep
from . import ngram

verbose=True
#verbose=False

class Exporter(QDialog, Ui_Exporter):
	"""
	Exports the database into text files
	"""
	progressChanged = pyqtSignal(int)
	progressFinished = pyqtSignal()
	
	def __init__(self, parent = None):
		"""
		Constructor
		"""
		QDialog.__init__(self, parent)
		self.setupUi(self)
		self.base=parent.base
		self.parent=parent

		self.textualization=parent.textualization
		
		self.exportName=self.textualization
		#print "self.parent.filterConditions",self.parent.filterConditions
		if self.parent.filterConditions:
			self.rowconditions=self.parent.condi
		else:
			self.rowconditions=None
		
		condi=""
		if self.rowconditions:
			condi="and "+self.rowconditions.replace("url", self.exportName+".url").replace("time", self.exportName+".time")
		self.sourceselectstatement="SELECT sources.url,source FROM sources,{exportname} WHERE sources.url={exportname}.url {condi};".format(exportname=self.exportName, condi=condi)
		
		self.makeColumnLists()
				
		#if "url" not in self.columnList:  self.columnList.insert(1, "url")
		
		
		
		allcolumns=", ".join(self.allColumnList)
		condi=""
		if self.rowconditions: 		condi=" WHERE "+self.rowconditions
		self.selectstatement="SELECT "+allcolumns+" FROM "+self.exportName+condi+" ;"
		if condi: conn=" and "
		else:	conn=" where "
			
		self.groupselectstatement="SELECT "+allcolumns+" FROM "+self.exportName+condi+conn+"rowid in (?);"
		
		
		self.countselectstatement="SELECT count(*) from "+self.exportName+condi+";"
		
		
		self.nbPages= int(parent.pageSpinbox.value())
		self.info=parent.commentTextEdit.toPlainText().replace("\n", "<br/>")+"<br/> axpromimately "
		self.info += str(self.nbPages)+" pages, "
		self.info += str(parent.sentenceSpinbox.value())+" sentences, and "
		self.info += str(parent.wordSpinbox.value())+" words<br/>"
		
		self.multipleToolBox.setItemText(0, "exporting current view of "+self.base.name+" / "+self.textualization)
		self.combinedToolBox.setItemText(0, "exporting current view of "+self.base.name+" / "+self.textualization)

		self.on_resultFile_editTextChanged(str(self.resultFile.text()))
		self.resultFolder.setText(os.path.join(os.path.expanduser('~'),"gromoteur","export-"+str(self.base.name)))
		
		#self.resultFolder.setText(_translate("Exporter", "corpora/export", None))
		
		self.rtl = False
		
		self.languageDirection()
		self.filesURL.setChecked(True)
		self.plainText.setChecked(True)
		
		# needed only for autoselection from last config
		self.textSourceGroup = QtWidgets.QButtonGroup(self)
		self.textSourceGroup.addButton(self.textExport)
		self.textSourceGroup.addButton(self.sourceExport)
		
		self.radios=[self.textExport]
		self.checks=[self.overwrite, self.viewFileAfter, self.exportHTML, self.surroundMatch, self.concordOutput, self.surroundByColumnNames, self.escapeTags, self.groupGroupBox, self.wordBoundaries, self.ignoreCase, self.overwriteFiles, self.filesURL]
		self.texts=[self.resultFile, self.match, self.concMatch, self.groupSeparatorBefore, self.groupSeparatorAfter, self.matchBefore, self.matchAfter, self.pageSeparatorBefore, self.pageSeparatorAfter, self.pageSeparatorHtmlBefore, self.pageSeparatorHtmlAfter, self.templateFile, self.concTemplateFile, self.slashesInto, self.addtofile]
		if "exportTab" in self.parent.config["configuration"]:self.tabWidget.setCurrentIndex(int(self.parent.config["configuration"]["exportTab"]))
		for r in self.radios:
			#trick: == yes --> click the source button, !=yes: click the text button:
			r.group().buttons()[self.parent.config["configuration"].get(str(r.objectName()),"yes")!="yes"].click()
		for c in self.checks:
			c.setChecked(self.parent.config["configuration"].get(str(c.objectName()),"yes")=="yes")
		for t in self.texts:
			if str(t.objectName())in self.parent.config["configuration"]: 
				t.setText(self.parent.config["configuration"].get(str(t.objectName()),"yes"))
		
		
		
		#try:	# recovering last state of the exporter
			
			
			
			
			#self.exportHTML.setChecked(self.parent.config["configuration"]["exportHTML"]=="yes")
			#self.surroundMatch.setChecked(self.parent.config["configuration"]["surroundMatch"]=="yes")			
			
			#self.concordOutput.setChecked(self.parent.config["configuration"]["concordOutput"]=="yes")
		#except:	pass
		
	
	
	def languageDirection(self):

		sample=self.base.getSample(self.textualization, -1,  1000) # -1 = last column, 1000=chars
		if len(sample)<10:
			self.guessLanguage.setText("Guessing left to right")
			
		else: 
			score,lang = ngram.Ngram().guessLanguage(sample)
			lang =ngram.langs.get(lang, "language not in list")
			self.rtl = lang in ngram.rtlLanguages
			if self.rtl: rtlInfo="right to left"
			else: rtlInfo="left to right"
			self.guessLanguage.setText("Guess language ("+lang+", "+rtlInfo+")")
		

	def makeColumnLists(self):
		self.columnList=[]
		for i, action in enumerate(self.parent.columnsMenu.actions()):
			if action.isChecked(): self.columnList+=[str(action.text())]
		self.allColumnList=["rowid","url","time"]+self.columnList
		#if "url" not in self.columnList:self.columnList+=["url"]
			
	
	#@pyqtSignature("")
	@pyqtSlot() # signal with no arguments
	def on_buttonBox_rejected(self):
		self.writeConfig()
	
	#@pyqtSignature("")
	@pyqtSlot() # signal with no arguments
	def on_buttonBox_accepted(self):
		"""
		ok is clicked, we export.
		"""
		#self.progressbar.show()
		self.progressChanged.emit(0)
		(totalnum,) =next(self.base.select(self.countselectstatement))
		counter=0		
#		try:

		if self.tabWidget.currentIndex():
			#############
			# multiple files #
			#############
			
			if not os.path.isdir(str(self.resultFolder.text())):
				try:
					os.makedirs(str(self.resultFolder.text()))
				except OSError as exc: # Python >2.5
					self.parent.statusbar.showMessage("Problem creating the designated export folder!", 20000)
					print("error")
					if exc.errno != errno.EEXIST: return
				except:
					self.parent.statusbar.showMessage("Problem creating the designated export folder!", 20000)
					return
			
			
			
			if  self.sourceExport.isChecked():
				# dumping source in multiple files
				
				for url,  source, in self.base.select(self.sourceselectstatement):
					counter+=1
					if self.filesNumbered.isChecked():
						#file named by the number
						filename=str(counter)+".htm"
						if not self.overwriteFiles.isChecked():
							while os.path.isfile( os.path.join(str(self.resultFolder.text()),filename)):
								filename=filename.split(".")[0]+self.addtofile.text() +".htm"
					else : #file named by the URL
						filename=url.split("//")[1].replace("/", self.slashesInto.text()) # TODO: make this a user choice
						if not self.overwriteFiles.isChecked():
							while os.path.isfile( os.path.join(str(self.resultFolder.text()),filename)):
								filename=filename+self.addtofile.text() 
					outFile=codecs.open( os.path.join(str(self.resultFolder.text()),filename),"w", "utf-8" )
					outFile.write(source)
					outFile.close()
					self.progressChanged.emit(100.0*counter/totalnum)
					
			else:
				# dumping text view in multiple files
				
				for entry in self.base.select(self.selectstatement):
					counter+=1
					if self.filesNumbered.isChecked(): #file named by the number
						filename=str(counter)
					else : #file named by the URL
						try:filename=entry[1].split("//")[1]
						except:filename=entry[1]
						filename=filename.replace("/", self.slashesInto.text())  
					if not self.overwriteFiles.isChecked():
						while os.path.isfile( os.path.join(str(self.resultFolder.text()),filename)+".txt"):
							filename=filename+self.addtofile.text()
					completeFileName=os.path.join(str(self.resultFolder.text()),filename)+".txt"
					if len(completeFileName)>255:
						completeFileName=completeFileName[:247]+"-ETC.txt"
						tinyAddon=1
						while os.path.isfile( completeFileName ):
							completeFileName=completeFileName[:-len(str(tinyAddon))]+str(tinyAddon)
							tinyAddon+=1
					outFile=codecs.open(completeFileName, "w", "utf-8" )
					#the format of the file
					if self.plainText.isChecked():  #just the content of the column, one column per line
						for col in entry[3:]:
							outFile.write(str(col))
							outFile.write("\n")
					elif self.columncolumn.isChecked():
						for i in range(len(entry[3:])):
							outFile.write(self.columnList[i]+":")
							outFile.write("\n")
							outFile.write(str(entry[3+i]))
							outFile.write("\n")
					else: # columnangle checked: < > 
						for i in range(len(entry[3:])):
							outFile.write("<"+self.columnList[i]+">")
							outFile.write("\n")
							outFile.write(str(entry[3+i]))
							outFile.write("\n")
					outFile.close()
					self.progressChanged.emit(100.0*counter/totalnum)
					
					
			
			
			
			
			
			
			
		else:
			#################
			# combined file #
			#################
			
			with codecs.open(os.path.expanduser(str(self.resultFile.text())),"w", "utf-8" ) as resultfile :
				if  self.sourceExport.isChecked():
					for url,  source, in self.base.select(self.sourceselectstatement):
						counter+=1	
						resultfile.write(url+"<hr>\n"+source+"<hr>\n\n")

				else: # only text view dump into combined file
					if self.exportHTML.isChecked():
						if self.forceLtr.isChecked():		self.rtl=False 
						elif self.forceRtl.isChecked():	self.rtl=True # else: keep the guessed rtl status
						with codecs.open(self.templateFile.text(),"r", "utf-8" ) as t :
							template=t.read()
						#t.close()
							template=template.replace("%name%",self.base.name+" / "+self.textualization)
							template=template.replace("%info%",self.info)
							template=template.replace("%date%",str(date.today()) )
							if self.rtl:	template=template.replace("%dir%","RTL")
							else: template=template.replace("%dir%","LTR")
							templateParts=template.split("%corpus%")
							resultfile.write(templateParts[0])
						
					if self.exportHTML.isChecked() and self.surroundMatch.isChecked():
						if self.ignoreCase.isChecked(): reoptions=re.I+re.U+re.M
						else:  reoptions= re.U+re.M
						if not str(self.match.text()):surrmatch=None
						elif self.matchWholeWords.isChecked(): surrmatch = re.compile(r"(\b"+str(self.match.text())+r"\b)",reoptions)
						else: surrmatch = re.compile(r"("+str(self.match.text())+r")",reoptions)
					else: surrmatch=None
					#self.getColumnList() ?????
					
					if self.exportHTML.isChecked():	
						if self.concordOutput.isChecked():	
							self.writeConcordancer(resultfile,  surrmatch)
						else:
							self.writePiecesHtml(resultfile,  surrmatch)
					else:  self.writePiecesText(resultfile)
					
					if self.exportHTML.isChecked(): resultfile.write(templateParts[1])
			#resultfile.close()
			self.progressFinished.emit()
			if self.viewFileAfter.isChecked(): self.on_viewResultFirefoxButton_clicked()
		
		#		except:
		#			self.parent.statusbar.showMessage("Problem exporting!", 20000)
		#			print "ooooooooh"
		self.writeConfig()
		self.parent.endProgress()
		
	
	def selectWrite(self, selectstatement, resultfile, beforePage, afterPage,counter, surroundList, escape=False, surrmatch=False, htmlnl=False, group=None):
		if verbose: 
			print(selectstatement)
			#qsdf
		for rr in self.base.select( selectstatement ):
			time=str(QDateTime.fromTime_t (int(float(rr[2]))).toString(QtCore.Qt.SystemLocaleLongDate))
			if group: resultfile.write(beforePage.replace("iii",str(rr[0])).replace("uuu",rr[1]).replace("ttt",time).replace("ggg",group))
			else:	resultfile.write(beforePage.replace("iii",str(rr[0])).replace("uuu",rr[1]).replace("ttt",time).replace('group="ggg"',''))
			counter+=1
			if self.nbPages:	self.progressChanged.emit(100.0*counter/self.nbPages)
			for i, col in enumerate(self.columnList):
				piece=str(rr[3+i]) 
				if escape and self.escapeTags.isChecked():	piece=piece.replace("<", "&lt;").replace(">", "&gt;")
				if col=="time":piece = time
				if surrmatch: piece = surrmatch.sub(str(self.matchBefore.text())+r"\1"+str(self.matchAfter.text()),  piece)
				if htmlnl: piece=piece.replace("\n", "<br/>")
				else: piece=piece+"\n"
				if col:
					if self.surroundByColumnNames.isChecked(): resultfile.write(surroundList[i][0]+piece+surroundList[i][1])
					else: resultfile.write(piece)
			resultfile.write(afterPage+"\n")
		return counter	
		
	
	
	def writePiecesText(self, resultfile):
		
		surroundList=[("<"+str(col) + ">\n",  "\n</"+str(col) + ">\n") for col in self.columnList]
		beforePage=str(self.pageSeparatorBefore.text())+"\n"
		afterPage=str(self.pageSeparatorAfter.text())+"\n"
		beforeGroup=str(self.groupSeparatorBefore.text())
		afterGroup=str(self.groupSeparatorAfter.text())
		counter = 0
		if self.groupGroupBox.isChecked() and self.parent.groups and self.parent.useGroupsCheckBox.isChecked():
			#print self.groupselectstatement
			for g in self.parent.groups:
				try:	bg=beforeGroup.replace("ggg",g)
				except: 	bg=beforeGroup
				resultfile.write(bg+"\n")
				commarowids=",".join([str(i) for i in self.parent.groups[g]])
				counter=self.selectWrite( self.groupselectstatement.replace("?",commarowids), resultfile, beforePage,afterPage, counter, surroundList, group=g )
				resultfile.write(afterGroup+"\n\n")		
					
		else: # no grouping:
			self.selectWrite( self.selectstatement, resultfile, beforePage,afterPage, counter, surroundList )
			
			
	def writePiecesHtml(self, resultfile,  surrmatch):
		colors=[str(hex(i*(256*256*256-2000000)/len(self.columnList)))[2:].rjust(6,"0") for i in range(1,len(self.columnList)+1)]
		colors[-1]="000"
		surroundList=[("<div name='"+str(col) + "' style='color: #"+colors[i]+";'>\n",  "\n</div>\n") for i, col in enumerate(self.columnList)]
		beforePage=str(self.pageSeparatorHtmlBefore.text())
		afterPage=str(self.pageSeparatorHtmlAfter.text())
		beforeGroup=str(self.groupSeparatorBefore.text())
		afterGroup=str(self.groupSeparatorAfter.text())
		counter = 0
		
		if self.groupGroupBox.isChecked() and self.parent.groups and self.parent.useGroupsCheckBox.isChecked():
			#print self.groupselectstatement
			for g in self.parent.groups:
				try:	bg=beforeGroup.replace("ggg",g)
				except: 	bg=beforeGroup
				resultfile.write(bg+g+"\n")
				commarowids=",".join([str(i) for i in self.parent.groups[g]])
				counter=self.selectWrite( self.groupselectstatement.replace("?",commarowids), resultfile, beforePage, afterPage,counter, surroundList, escape=True, surrmatch=surrmatch, htmlnl=True, group=g)	
		
		else: # no grouping:
		
			self.selectWrite(self.selectstatement, resultfile, beforePage, afterPage,counter, surroundList, escape=True, surrmatch=surrmatch, htmlnl=True)
	
	
	def writeConcordancer(self, resultfile,  surrmatch):
	
		t=codecs.open(str(self.concTemplateFile.text()) ,"r", "utf-8" )
		concTemplate=t.read()
		t.close()

		urlreg = re.compile(r"^.*%url%.*$",re.MULTILINE)
		urlmatch = urlreg.search(concTemplate)
		if urlmatch:
			urlline = urlmatch.group()
			concTemplate = urlreg.sub("",concTemplate)
		else: urlline="%url%"

		reg = re.compile(r"^.*%match%.*$",re.MULTILINE)
		match = reg.search(concTemplate)
		if match:
			matchline = match.group()
			concParts = concTemplate.split(matchline)
		else:
			return
		
		wordbound = self.wordBoundaries.isChecked()
			
		if self.ignoreCase.isChecked(): reoptions=re.I+re.U+re.M
		else:  reoptions= re.U+re.M
		if self.concMatchWholeWords.isChecked(): concmatch = re.compile(r"(\b"+str(self.concMatch.text())+r"\b)",reoptions)
		else: concmatch = re.compile(r"("+str(self.concMatch.text())+r")",reoptions)
		
		concBef = int(self.concBefore.value())
		concAft = int(self.concAfter.value())

		counter = 0

		tablestart = concParts[0].replace("%matching%", str(self.concMatch.text()).replace("<","&lt;").replace(">","&gt;"))
		if self.rtl:  tablestart = tablestart.replace( "%dir%","RTL") # right to left language ?
		else: tablestart = tablestart.replace( "%dir%","LTR")
		resultfile.write(tablestart)
		#print "self.columnList",self.columnList
		url=""
		for rr in self.base.select( self.selectstatement): # for each line in the table

			for i, col in enumerate(self.columnList): # for each column
				piece=str(rr[3+i]) 
				if col=="url":
					url=piece
					resultfile.write(re.sub("%url%",url, urlline))
					continue
		
				for i in concmatch.finditer(piece): # for each matching thing
					mat = i.group() # the thing that matched
					left = max(0,i.start()-concBef)
					concbefore = i.string[left:i.start()] # the string to the match
					concafter = i.string[i.end():i.end()+concAft] # the string behind the match
					if wordbound:
						if left: concbefore=" ".join(concbefore.split()[1:])
						if len(i.string) >= i.end()+concAft: concafter=" ".join(concafter.split()[:-1])
						                    
					counter+=1
					tableline = matchline.replace(
										"%number%",	str(counter)).replace(
										"%before%",concbefore).replace(
										"%match%",mat).replace(
										"%after%",concafter)
					if surrmatch: tableline = surrmatch.sub(str(self.matchBefore.text())+r"\1"+str(self.matchAfter.text()),  tableline)
					
					resultfile.write(tableline)
		resultfile.write(concParts[1])	
	
	#@pyqtSignature("")
	@pyqtSlot() # signal with no arguments
	def on_viewResultFirefoxButton_clicked(self):
		"""
		Slot documentation goes here.
		"""
		filename=str(self.resultFile.text())
		if filename and filename[0]!="/":filename=str(os.path.expanduser(filename))
		webbrowser.open_new("file:///"+filename)
	
	#@pyqtSignature("")
	@pyqtSlot() # signal with no arguments
	def on_ChooseResultFileButton_clicked(self):
		"""
		Slot documentation goes here.
		"""
		filename=str( QtWidgets.QFileDialog.getSaveFileName(self, "Save data as...",os.path.join(os.path.expanduser('~'),"gromoteur","export"),"All files (*.*)")[0])
		self.setFile(filename, self.resultFile,  self.viewResultFirefoxButton)
		
	#@pyqtSignature("")
	@pyqtSlot() # signal with no arguments
	def on_ChooseResultFolderButton_clicked(self):
		"""
		Slot documentation goes here.
		"""
		foldername=str( QtWidgets.QFileDialog.getExistingDirectory(self, "Save data in...",os.path.join(os.path.expanduser('~'),"gromoteur","export-"+str(self.base.name))))
		self.setFile(foldername, self.resultFolder,  self.viewResultFirefoxButton)
		
	def setFile(self, filename,  object,  viewbutton):
		if filename:
			#if filename.startswith(unicode(os.getcwdu())):filename=filename[len(unicode(os.getcwdu()))+1:]
			object.setText(filename)
			viewbutton.setEnabled(os.path.isfile(filename))
	
			
	def viewFile(self, object):
		filename=str(object.text())
		if filename :
			#if filename[0]!="/":filename=unicode(os.getcwdu())+"/"+filename
			webbrowser.open_new(str("file:///")+filename)
	
	#@pyqtSignature("")
	@pyqtSlot() # signal with no arguments
	def on_viewTemplateFirefoxButton_clicked(self):
		self.viewFile(self.templateFile)
	
	#@pyqtSignature("")
	@pyqtSlot() # signal with no arguments
	def on_viewConcTemplateFirefoxButton_clicked(self):
		self.viewFile(self.concTemplateFile)
		
	
	#@pyqtSignature("")
	@pyqtSlot() # signal with no arguments
	def on_chooseTemplateFileButton_clicked(self):
		"""
		Slot documentation goes here.
		"""
		filename=str(QtWidgets.QFileDialog.getOpenFileName(self,"Choose the HTML to use for HTML export",
								str(self.templateFile.text()),
								"HTML files (*.html)"))
		self.setFile(filename, self.templateFile,  self.viewTemplateFirefoxButton)
	
	#@pyqtSignature("")
	@pyqtSlot() # signal with no arguments
	def on_chooseConcTemplateFileButton_clicked(self):
		"""
		Slot documentation goes here.
		"""
		filename=str(QtWidgets.QFileDialog.getOpenFileName(self,"Choose the HTML to use for HTML export",
								str(self.concTemplateFile.text()),
								"HTML files (*.html)"))
		self.setFile(filename, self.concTemplateFile,  self.viewConcTemplateFirefoxButton)

	#@pyqtSignature("QString")
	@pyqtSlot(str) # signal with no arguments
	def on_resultFile_editTextChanged(self, p0):
		"""
		Slot documentation goes here.
		"""
		fileExists=os.path.isfile(os.path.expanduser(str(p0)))
		self.viewResultFirefoxButton.setEnabled(fileExists)
		self.overwrite.setEnabled(fileExists)
	
	# config preservation:
	
	#@pyqtSignature("int")
	def on_tabWidget_currentChanged(self, b):
		self.parent.config["configuration"]["exportTab"]=b
		self.parent.config.write()	
	
	#@pyqtSignature("int")
	def on_viewFileAfter_stateChanged(self, b):
		self.setConfig("viewFileAfter",b)
		
	#@pyqtSignature("bool")
	def on_exportHTML_toggled(self, b):
		self.setConfig("exportHTML",b)
		
	#@pyqtSignature("bool")
	def on_surroundMatch_toggled(self, b):
		self.setConfig("surroundMatch",b)
	
	#@pyqtSignature("bool")
	def on_concordOutput_toggled(self, b):
		self.setConfig("concordOutput",b)
	
	
	
	#@pyqtSignature("bool")
	def on_textExport_toggled(self, b):
		self.setConfig("textExport",b)
	
	
	def setConfig(self, key, b):
		if b: 	self.parent.config["configuration"][key]="yes"
		else:	self.parent.config["configuration"][key]="no"
		self.parent.config.write()
	
	def writeConfig(self):
		for c in self.checks+self.radios:
			if c.isChecked():	self.parent.config["configuration"][str(c.objectName())]="yes"
			else:		self.parent.config["configuration"][str(c.objectName())]="no"
		for t in self.texts:
			self.parent.config["configuration"][str(t.objectName())]=str(t.text())
		self.parent.config.write()
		
		
	
	# end config preservation

if __name__ == "__main__":
	
	#SELECT sources.url,source FROM sources,standard WHERE sources.url=standard.url ;

	
	
	app = QtWidgets.QApplication(sys.argv)
	window = Exporter(None)
	window.show()
	sys.exit(app.exec_())
	

