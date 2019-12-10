# -*- coding: utf-8 -*-

"""
Module implementing MainWindow of Nexico
"""

import codecs,  re,  sys,   pkgutil,  encodings,  signal, unicodedata
from PyQt5.QtGui import QPixmap, QPainter, QFontDatabase
from PyQt5.QtWidgets import  QMainWindow, QFileDialog, QMessageBox, QApplication, QTableWidgetItem
from PyQt5.QtPrintSupport import  QPrinter
from PyQt5.QtSvg import QSvgGenerator
from PyQt5 import QtGui, QtCore, QtWidgets

try: 	from PyQt5.QtWebEngineWidgets import QWebEngineView as QWebView, QWebEnginePage as QWebPage
except:	from PyQt5.QtWebKitWidgets import QWebView, QWebPage


#from PyQt5.QtCore import pyqtSignature,  SIGNAL
from PyQt5.QtCore import  pyqtSlot,  QDateTime,  QObject, QEvent,  Qt,   QDir, QUrl,  QRect,  QSize,  QSizeF

#,  QSplitter
from time import sleep

from . import groressources_rc

from .preferencesDialog import PreferencesDialog
from .nexicollocations import Collocations, RecenterClass

try: 			_fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:	_fromUtf8 = lambda s: s

from .Ui_NexicoMain import Ui_MainWindow


debug=False
#debug=True

class Nexico(QMainWindow, Ui_MainWindow):
	"""
	Nexico user interface main class
	"""
	def __init__(self, splash, nexicoBase, config, selectionName="standard",parent=None):
		"""
		Constructor	
		"""
		QMainWindow.__init__(self)
		self.setupUi(self)
		qfdb=QFontDatabase()
		fi=qfdb.addApplicationFont(":fonts/resources/FreeSans.otf")
		
		try:	self.font = qfdb.font(qfdb.applicationFontFamilies(fi)[0],  "Light", False)
		except:	self.font=None
		
		self.config=config
		self.nbBestKids=int(self.config["configuration"]["nbBestKids"])
		self.currentSection=None
		self.selectedWord=""
		self.selectedTokeni=None
		self.sectList=[]
		self.base=nexicoBase
		self.wordTableWidget.setHorizontalHeaderLabels([self.tr("word"), self.tr("frequency")])
		self.autoSelect = 0
		
		
		
		
		false_positives = set(["aliases", "undefined"])
		self.encodings = set(name for imp, name, ispkg in pkgutil.iter_modules(encodings.__path__) if not ispkg)
		self.encodings.difference_update(false_positives)
		self.encodings=sorted(self.encodings)
		
		self.statusbar.showMessage(self.tr("Welcome!"), 20000)
		self.fileNameEdit.setText(selectionName)
		self.pb = QtWidgets.QProgressBar(self.statusBar())
		self.statusBar().addPermanentWidget(self.pb)
		self.pb.hide()
		self.splash=splash
		self.selecting=False
		self.graphicsView.setRenderHints(QtGui.QPainter.Antialiasing or QtGui.QPainter.SmoothPixmapTransform)
		self.ngra=self.ngraDial.sliderPosition()
		self.renoword=re.compile("\W+$",re.U+re.I+re.M)
		
		self.webView = QWebView()  
		self.collocations=Collocations(self)
		
		#self.gridLayout_3.addWidget(self.graphcanvas, 0, 0, 1, 1)
		self.gridLayout_3.addWidget(self.webView, 0, 0, 1, 1)
		
		# start with collocation open?
		#openwithcolloc=int(self.config["configuration"]["openwithcolloc"]) # False
		openwithcolloc=False
		self.actionCollocations.setChecked(openwithcolloc)
		self.on_actionCollocations_toggled(openwithcolloc)
		#self.graphButton.setChecked(True)
		
		#self.specos=None # dict of collocations for current word
		
		# TODO: solve the memory problem of qsplitter:
		#self.hsplitter=QSplitter(1, self.centralwidget)  # 2=vertical orientation
		#self.centralGridLayout.addWidget(self.hsplitter,  0, 1)
		#self.vspgridLayout = QtGui.QGridLayout(self.hsplitter)
		#self.vspgridLayout.setSpacing(0)
		#self.hsplitter.setHandleWidth(8)
		#self.vspgridLayout.setContentsMargins(2, 0, 2, 0)
		#self.vspgridLayout.addWidget(self.westwidget, 0, 0)
		#self.vspgridLayout.addWidget(self.eastwidget)
		
		
		self.load() 
		self.filter.textChanged.connect(self.filterChanged)
		self.colfilter.textChanged.connect(self.colfilterChanged)
		
		self.recenter=RecenterClass()
	
#			
	def load(self, encoding="autodetect"):
#		self.specTableWidget.hide()
		self.wordTableWidget.clear()
		self.sectionMap.clear()
		#print 14
		self.base.progressChanged.connect(self.updateProgress)
		self.base.finished.connect(self.loadFinished)
		self.base.start()
		
		
	def updateProgress(self, i, message="Loading..."):
		if self.pb.isHidden(): self.pb.show()
		self.pb.setValue(i)
		if message:
			self.statusbar.showMessage(message)
		
	def loadFinished(self):
		"""
		loading of base is finished
		"""
		self.base.progressChanged.emit(95.0, "Showing table for first section...")
		if not len(self.sectionMap):  # first time:
			self.splash.finish(self)
			self.sectrast=self.base.sectrast #s[0] #my default sectrast is the first of the base i just created
			#self.sectionMap.clear()
			if self.sectrast:
				for si,section in enumerate(self.sectrast.sections): # pour chaque section 
#					u"\u25A1" u"◻"
					carre=QtWidgets.QListWidgetItem("\u25A1", self.sectionMap)
					carre.section=section
					carre.setToolTip("<b>"+str(section)+":</b>"+(self.sectrast.urls[si] or ""))
					if self.font:	carre.setFont(self.font)
					
				self.sectionMap.setCurrentRow ( 0 ) # select the first square
		
			#self.actionComputeSpecificity.setEnabled(True)
			
		self.statusbar.showMessage("Finished loading",  2000)
		self.pb.hide()
		
		if self.actionCollocations.isChecked():
			# autostart the collocation stuff:
			self.wordTableWidget.selectRow(0)
			self.graphButton.setChecked(True)
		
		
		
	
	def fillTokenTable(self):
		"""
		fills the token table with:
		- all the tokens
		- for each token:
			its total frequency
			its frequency in the selected selection
			its specificity for the selected selection
			
		called for new section selection 
		"""
		
		if debug:print("fillTokenTable", self.selection)
		
		self.wordTableWidget.clear()
		self.wordTableWidget.setSortingEnabled(False)	
		self.wordTableWidget.setRowCount(len(self.base.d))
		self.wordTableWidget.setColumnCount(4)
		
		fi=re.compile(str(self.filter.text()))
			
		
		for i,  tokeni in  enumerate(self.base.d):
			s=self.base.d.idtotoken[tokeni]#.decode("utf-8")
			worditem=QtWidgets.QTableWidgetItem(s)
			if self.renoword.match(s): # nowords get tooltip
				# TODO: check what's going on here:  0x8e ValueError: no such name
				#for l in s:
				#	print l.encode("utf-8"),type(l),len(l),hex(ord(l))
				#	print unicodedata.name(unicode(l))
				try:worditem.setToolTip(" - ".join(   [unicodedata.name(str(l)) for l in s]    ))
				except ValueError:
					try:
						worditem.setToolTip("special control character: "+" - ".join([unicodedata.category(str(l))+":"+hex(ord(str(l))) for l in s])) 
					except:
						print("can't find unicode data for",[s])#,s.encode("iso-8859-1")
			if debug:print("fillTokenTable", self.selection,2)
			self.wordTableWidget.setItem(i, 0, worditem)
			if debug:print("fillTokenTable", self.selection,3)
			self.wordTableWidget.setRowHidden(i, not  fi.search(self.wordTableWidget.item(i, 0).text()))
			totfreqitem=QtWidgets.QTableWidgetItem( )
			if debug:print("fillTokenTable", self.selection,4)
			#totfreqitem.setData(Qt.EditRole, len(self.sectrast.tokens[token]))
			totfreqitem.setData(Qt.EditRole, self.base.d.freqs[tokeni])
			totfreqitem.setTextAlignment(QtCore.Qt.AlignRight)
			self.wordTableWidget.setItem(i, 1,  totfreqitem)
			if debug:print("fillTokenTable", self.selection,5)
		
			freqitem=QtWidgets.QTableWidgetItem('%7d' % sum([self.base.sectrast.bows[se].get(tokeni,0) for se in self.selection]))
			freqitem.setTextAlignment(QtCore.Qt.AlignRight)
			self.wordTableWidget.setItem(i, 2,  freqitem)
			if debug:print("fillTokenTable", self.selection,6)
			specitem=QtWidgets.QTableWidgetItem()
#
			try:
				specitem.setData(Qt.EditRole, self.sectrast.specificity[tokeni][self.selection] )
			except:
				self.sectrast.computeOtherSpecificity(self.selection)
				specitem.setData(Qt.EditRole, self.sectrast.specificity[tokeni][self.selection])
				self.loadFinished()
				
			specitem.setTextAlignment(QtCore.Qt.AlignRight)
			if debug:print("fillTokenTable", self.selection,7)
			self.wordTableWidget.setItem(i, 3,  specitem)
			if debug:print("fillTokenTable", self.selection,8)
	
		self.wordTableWidget.setHorizontalHeaderLabels([self.tr("token"), self.tr("totfreq"), self.tr("freq"), self.tr("spec") ])
		self.wordTableWidget.verticalHeader().setStyleSheet("QHeaderView { font-size: 6pt; }")
		self.wordTableWidget.resizeColumnsToContents()
		self.wordTableWidget.setSortingEnabled(True)	
		if debug:print("fillTokenTable", self.selection,9)
		self.wordTableWidget.sortItems(3, 1) # sort by specificity, descending
		self.actionSaveTable.setEnabled(True)
		self.actionSaveGraph.setEnabled(True)
		
		
	
	def filterChanged(self, text): # TODO: redo that with a real QAbstractItemModel and QSortFilterProxyModel
		try:fi=re.compile(str(text))
		except:return # TODO: show errors in regex?
		for i in range(self.wordTableWidget.rowCount()):
			self.wordTableWidget.setRowHidden(i, not  fi.search(self.wordTableWidget.item(i, 0).text()))
	def colfilterChanged(self, text): # TODO: redo that with a real QAbstractItemModel and QSortFilterProxyModel
		try:fi=re.compile(str(text))
		except:return # TODO: show errors in regex?
		for i in range(self.collocTableWidget.rowCount()):
			self.collocTableWidget.setRowHidden(i, not  fi.search(self.collocTableWidget.item(i, 0).text()))
	
	#def selectToken(self,token):
		
	
	def colloc(self, token):
		"""
		
		fills the colloc table
		
		"""
		
		if debug:print("fillCollocTable", token)
		
		if self.ngra not in self.sectrast.specollocs: self.sectrast.computeCollocations(self.ngra) # compute collocations only the first time
		
		if not token:
			self.pb.hide()
			return
		#selectedTokeni = self.base.d.token2id[self.selectedWord]
		#d=self.sectrast.specollocs[selectedTokeni]
		#for coi in sorted(d,key=d.get,reverse=True):
			#print "___",self.base.d.idtotoken[coi],d[coi]
		try:self.selectedTokeni = self.base.d.token2id[token] # .encode("utf-8")
		except:self.selectedTokeni = self.base.d.token2id[token]
		specos={i:sp for i,sp in self.sectrast.specollocs[self.ngra][self.selectedTokeni].items() if sp!=0}
		#print self.selectedTokeni
		self.collocTableWidget.clear()
		self.collocTableWidget.setSortingEnabled(False)	
		self.collocTableWidget.setRowCount(len(specos))
		self.collocTableWidget.setColumnCount(4)
		
		fi=re.compile(str(self.colfilter.text())) 
		
		
		
		for i,  tokeni in  enumerate(specos):
			s=self.base.d.idtotoken[tokeni]#.decode("utf-8")
			worditem=QtWidgets.QTableWidgetItem(s)
			if self.renoword.match(s): # nowords get tooltip
				# TODO: check what's going on here:  0x8e ValueError: no such name
				#for l in s:
				#	print l.encode("utf-8"),type(l),len(l),hex(ord(l))
				#	print unicodedata.name(unicode(l))
				try:worditem.setToolTip(" - ".join(   [unicodedata.name(str(l)) for l in s]    ))
				except ValueError:
					try:
						worditem.setToolTip("special control character: "+" - ".join([unicodedata.category(str(l))+":"+hex(ord(str(l))) for l in s])) 
					except:
						print("can't find unicode data for",[s])#,s.encode("iso-8859-1")
			self.collocTableWidget.setItem(i, 0, worditem)
			self.collocTableWidget.setRowHidden(i, not  fi.search(self.collocTableWidget.item(i, 0).text()))
			totfreqitem=QtWidgets.QTableWidgetItem( )
			#totfreqitem.setData(Qt.EditRole, len(self.sectrast.tokens[token]))
			totfreqitem.setData(Qt.EditRole, self.base.d.freqs[tokeni])
			totfreqitem.setTextAlignment(QtCore.Qt.AlignRight)
			self.collocTableWidget.setItem(i, 1,  totfreqitem)
		
			freqitem=QtWidgets.QTableWidgetItem('%7d' % self.sectrast.collocs[self.ngra][self.selectedTokeni].get(tokeni,0)  )
			freqitem.setTextAlignment(QtCore.Qt.AlignRight)
			self.collocTableWidget.setItem(i, 2,  freqitem)
			
			specitem=QtWidgets.QTableWidgetItem()
			specitem.setData(Qt.EditRole, specos[tokeni] )
			
			#try:
				#specitem.setData(Qt.EditRole, self.sectrast.specificity[tokeni][self.selection] )
			#except:
				#self.sectrast.computeOtherSpecificity(self.selection)
				#specitem.setData(Qt.EditRole, self.sectrast.specificity[tokeni][self.selection])
				#self.loadFinished()
				
			specitem.setTextAlignment(QtCore.Qt.AlignRight)
			self.collocTableWidget.setItem(i, 3,  specitem)
	
		self.collocTableWidget.setHorizontalHeaderLabels([self.tr("token"), self.tr("totfreq"), self.tr("cooc"), self.tr("spec") ])
		self.collocTableWidget.verticalHeader().setStyleSheet("QHeaderView { font-size: 6pt; }")
		self.collocTableWidget.resizeColumnsToContents()
		self.collocTableWidget.setSortingEnabled(True)	
		#print 7777
		self.collocTableWidget.sortItems(3, 1) # sort by specificity, descending
		#self.actionSaveTable.setEnabled(True)
		#self.actionSaveGraph.setEnabled(True)
		self.statusbar.showMessage("Finished loading",  3000)
		self.pb.hide()
	
	
	def updateInfo(self):
		"""
		fills 
		- the text above the token table
		- the information line under the sectionMap
		"""
		
		if len(self.selection)==1:
			infospec ="Specificity table for section {nr}.".format(nr=str(self.selection[0]))
		elif  len(self.selection)<10:
			infospec="sections {nr}.".format( nr=str(self.selection)[1:-1])
		else:
			infospec="{totalselect} sections: {start}...{end}".format( totalselect=len(self.selection),  start=str([s for s in self.selection[:3]])[1:-1],  end=str([s for s in self.selection[-3:]])[1:-1]   )
		self.tableBox.setTitle(infospec)
		self.pageNameLabel.setText(str(sum([ self.sectrast.nrtoks[s] for s in self.selection ]))+" tokens" ) # todo: think of how to show the names of files: self.selection[0][1].split("/")[-1]+" - "+
		infomap="Text with {totok} tokens in {totsec} sections.".format( totok=self.sectrast.size, totsec=len(self.sectrast.sections))
		
		if self.selectedWord:
			infograph= "Occurrences of '{token}'".format( token=str(self.selectedWord))
			#
			self.graphicsBox.setTitle(infograph)
			if self.graphButton.isChecked():self.graphicsBox.setToolTip(infograph+". Colors show specificity of the token.".format( token=str(self.selectedWord)))
			
			infomap=infomap+" Colors show occurrences (pink squares) and specifities (red +, green - background) of '{token}'.".format( token=str(self.selectedWord))
		
		self.mapBox.setTitle(infomap)
		self.mapBox.setToolTip(infomap)
			
		
		
	@pyqtSlot()
	def on_sectionMap_itemSelectionChanged (self):
		"""
		Slot documentation goes here.
		"""
		if not len(self.sectionMap.selectedItems()): return
		if self.selecting: return
		if debug: print("on_sectionMap_itemSelectionChanged",1)
		#self.selection=tuple([s.section.id for  s in self.sectionMap.selectedItems()])
		self.selection=tuple([s.section for s in self.sectionMap.selectedItems()])
		
		if len(self.selection)>=1:
			remot = re.compile(r"\b("+str(self.selectedWord)+r")\b", re.U)
			#text=remot.sub(r"<span style='color:red'>\1</span>", self.sectionMap.selectedItems()[0].section.getText())
			text=remot.sub(r"<span style='color:red'>\1</span>", self.base.rowIdFunction( self.sectionMap.selectedItems()[0].section) )
			if debug: print("on_sectionMap_itemSelectionChanged",2)
			self.editSection.setHtml(text)
			if debug: print("on_sectionMap_itemSelectionChanged",3)
#			print text
			self.sectionBox.setTitle("Content of section "+str(self.selection[0])+" - "+(self.sectrast.urls[self.sectrast.sections.index(self.selection[0])] or "").split("/")[-1] + " - "+str(self.sectrast.nrtoks[self.selection[0]])+" tokens")
			if debug: print("on_sectionMap_itemSelectionChanged",4)
			#print self.sectrast.nrtoks[self.selection[0]]
		else:
			self.sectionBox.setTitle("No section selected ")
			self.editSection.setHtml("")
		self.fillTokenTable()
		self.updateInfo()
	
	# TODO: make multi-word specificities possible
#	@pyqtSlot()
#	def on_wordTableWidget_itemSelectionChanged(self):
#		print self.wordTableWidget.selectedIndexes()
#		rows=sorted(set([i.row() for i in  self.wordTableWidget.selectedIndexes()] ))
#		self.selectedWords = sorted([unicode(self.wordTableWidget.item(r, 0).text()) for r in rows])
#		self.selectedTokenis = [self.base.d.token2id[unicode(self.wordTableWidget.item(r, 0).text())] for r in rows]
#		print self.selectedTokenis
	
	#@pyqtSignature("QTableWidgetItem*, QTableWidgetItem*")
	@pyqtSlot(QTableWidgetItem,QTableWidgetItem)
	def on_collocTableWidget_currentItemChanged(self, item,  previous):
		if not item: item=previous
		print(46546 , item, previous)
		try: 	
			selectedWord = str(self.collocTableWidget.item(item.row(), 0).text())
			#self.selectedTokeni = self.base.d.token2id[self.selectedWord]
			print(selectedWord)
			self.selectWordInWordTableWidget(selectedWord)	
		except Exception as e: 
			print("oh, something wrong",Exception,  e)
			#self.selectedTokeni=0
		
	
	def selectWordInWordTableWidget(self,word):
		for i in range(self.wordTableWidget.rowCount()):
			if self.wordTableWidget.item(i,0).text()==word:
				self.wordTableWidget.selectRow(i)
				break
			

				
	#@pyqtSignature("QTableWidgetItem*, QTableWidgetItem*")
	def on_wordTableWidget_currentItemChanged(self, item,  previous):
		#print "000",item, previous
		if not item: item=previous
		try: 	
			self.selectedWord = str(self.wordTableWidget.item(item.row(), 0).text())
			try:self.selectedTokeni = self.base.d.token2id[self.selectedWord] # TODO: clean this mess up! .encode("utf-8")
			except:self.selectedTokeni = self.base.d.token2id[self.selectedWord]
		except Exception as e: 
			print("oh, something wrong",Exception,  e)
			self.selectedTokeni=0
		#print 8888
		
		self.sectionMap.clearSelection()
		red=QtGui.QColor("red")
		green=QtGui.QColor("green")
		whitebrush=QtGui.QBrush(QtCore.Qt.white, QtCore.Qt.NoBrush)
		self.smin, self.smax, self.fmax=0, 0, 0
#		print self.currwordsectspecdic
		for i, section in enumerate(self.sectrast.sections):
				#s=self.currwordsectspecdic[(i, )]
				# print i,section,sorted(self.sectrast.specificity[self.selectedTokeni])
				# try:
				s=self.sectrast.specificity[self.selectedTokeni][(section, )] # TODO: check why error on windows!
				# except:s=0
				if s>0:
					#self.sectionMap.item(i).setBackgroundColor(red.darker(30*s))
					self.sectionMap.item(i).setBackground(QtGui.QBrush(QtGui.QColor(QtCore.Qt.red).darker(30*s)))
				elif s<0:
					self.sectionMap.item(i).setBackground(QtGui.QBrush(QtGui.QColor(QtCore.Qt.green).darker(30*-s)))
				else:
					self.sectionMap.item(i).setBackground(whitebrush)
				freq=self.sectrast.bows[section].get(self.selectedTokeni,0)
				if freq:
					self.sectionMap.item(i).setForeground(QtGui.QBrush(QtCore.Qt.magenta))
				else: 
					self.sectionMap.item(i).setForeground(QtGui.QBrush(QtCore.Qt.black))
				if s>self.smax:self.smax=s
				elif s<self.smin:self.smin=s
				
				if freq>self.fmax:self.fmax=freq
		
		self.updateInfo()
		#if self.currwordsectspecdic: 
		#print ";.isChecked()",self.graphButton.isChecked()
		#print self.autoSelect,"jjj"
		if self.actionCollocations.isChecked():		self.colloc(self.selectedWord)
		#print self.autoSelect,"uuu"
		if self.autoSelect: 
			#sleep(.5)
			#print self.recenter.word
			#if self.recenter.word==self.selectedWord:
			if self.autoSelect and self.graphButton.isChecked():
					#print "sleep",self.recenter.word
					
					#self.autoSelect=0
					#sleep(.5)
					baseUrl = QUrl.fromLocalFile(QDir.current().absoluteFilePath("lib/resources/about.html")) # any html file to base the setHtml!!!
					self.webView.setHtml(self.collocations.graph(self.nbBestKids), baseUrl) 
					#self.makeCollocGraph()
					#sleep(.5)
					self.webView.page().mainFrame().addToJavaScriptWindowObject("pyObj", self.recenter) 
					#self.autoSelect=1
					#print 111,self.recenter.word
			return
		
		if self.graphButton.isChecked():	self.makeCollocGraph()
		else:				self.makeSpecGraph()
		#print "www"
		self.actionSelect_sections_with_occurrences.setEnabled(True)
		self.actionSelectposspecificsections.setEnabled(True)
		self.actionSelectnegspecificsections.setEnabled(True)
		
		
		
		
	
	def makeSpecGraph(self, numMarks=10):
		"""
		draws the curve of the evolution of occurrences and specificities in the sections
		"""
		#if self.graphcanvas: self.graphcanvas.hide()
		self.graphicsView.show()
		#print "makeSpecGraph"
		size=self.graphicsView.size()
		
		scene = QtWidgets.QGraphicsScene(self)
#		scene.addText(self.selectedWord)
		specpath=QtGui.QPainterPath()
		specpath.setFillRule(Qt.WindingFill)
		freqpath=QtGui.QPainterPath()
		specpath.moveTo(0, 0)
		freqpath.moveTo(0, 0)

		nrsects=len(self.sectrast.sections)
		
			
		snry=size.height()/(self.smax-self.smin+1)*.75
		fnry=size.height()/(self.fmax+1)*.5
		
		tex=int(nrsects/numMarks)
		if nrsects>100: pathw=1.0
		else: pathw=3.0
		
		for i, si in enumerate(self.sectrast.sections):
			s=self.sectrast.specificity[self.selectedTokeni][(si, )]
			specpath.lineTo(QtCore.QPointF(i*size.width()*.8/nrsects, -s*snry))
			freqpath.lineTo(QtCore.QPointF(i*size.width()*.8/nrsects, -self.sectrast.bows[si].get(self.selectedTokeni,0)*fnry))
			if not tex or not i%tex:
				num=scene.addText(str(i), QtGui.QFont("Helvetica",  6))
				num.setPos(QtCore.QPointF(i*size.width()*.8/nrsects, 0))
		specpath.lineTo(QtCore.QPointF(i*size.width()*.8/nrsects,0))
		freqpath.lineTo(QtCore.QPointF(i*size.width()*.8/nrsects,0))
		specpath.lineTo(0,0)
		freqpath.lineTo(0,0)
		
		scene.addPath(specpath,  QtGui.QPen(self.base.specColor, pathw, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin),  QtGui.QBrush(self.base.specColor))
		scene.addPath(freqpath,  QtGui.QPen(self.base.freqColor, pathw, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

		self.graphicsView.centerOn(0, 0)
		
		scene.addText(self.selectedWord).moveBy(0, 20)
		self.graphicsView.setScene(scene)
		self.graphicsView.fitInView(scene.sceneRect (), 1)
		
		self.graphicsView.show()
		self.actionCopyGraphToClipboard.setEnabled(True)
#		print self.graphicsView.sceneRect () , size, self.graphicsView.size()



	@pyqtSlot()
	def on_actionSaveGraph_triggered(self):
		if self.selectedWord: 	filename=self.selectedWord+"-specificity.png"
		else:			filename="specificity.png"
		fileName = QFileDialog.getSaveFileName(self, "Save Graph as png, svg, or pdf", filename, "PNG Image (*.png);;PDF File(*.pdf);;SVG File(*.svg)")[0];
		if str(fileName).endswith(".png"):
			#pixMap=QPixmap.grabWidget( self.graphicsView)
			pixMap=self.graphicsView.grab( )
			pixMap.save(fileName)
		elif str(fileName).endswith(".pdf"):
			pdfPrinter=QPrinter()
			pdfPrinter.setOutputFormat( QPrinter.PdfFormat )
			pdfPrinter.setPaperSize( QSizeF(self.graphicsView.width(), self.graphicsView.height()), QPrinter.Point )
			pdfPrinter.setFullPage(True)
			pdfPrinter.setOutputFileName( fileName )
			pdfPainter=QPainter()
			pdfPainter.begin( pdfPrinter)
			self.graphicsView.render( pdfPainter )
			pdfPainter.end()
		elif str(fileName).endswith(".svg"):
			svgGen=QSvgGenerator()
			svgGen.setFileName(fileName)
			svgGen.setSize(QSize(self.graphicsView.width(), self.graphicsView.height()))
			svgGen.setViewBox(QRect(0, 0, self.graphicsView.width(),self.graphicsView.height()))
			svgGen.setTitle(filename)
			svgGen.setDescription("Specificity graph generated by Gromoteur")
			painter=QPainter(svgGen)
			self.graphicsView.render(painter)
			painter.end()
	
	@pyqtSlot()
	def on_actionOpen_graph_in_browser_triggered(self):
		self.collocations.viewGraphInBrowser()

	@pyqtSlot()
	def on_actionCopyGraphToClipboard_triggered(self):
		#pixMap=QPixmap.grabWidget( self.graphicsView)
		pixMap=self.graphicsView.grab( )
		# print type(pixMap)
		clipboard = QApplication.clipboard()

		clipboard.setPixmap(pixMap)
	
#		QApplication::clipboard()->setPixmap( QPixmap( "path to my png" ) )

	@pyqtSlot()
	def on_actionSaveTable_triggered(self):
#		self.specTableWidget.show()
		
		#replacer=re.compile("\n

		filename=QFileDialog.getSaveFileName(self, self.tr("Save the table"),"nexico-export.csv","*.*")[0]
		if filename:
			if debug:print("filename",filename)
			out=codecs.open(filename, "w", "utf-8")
			out.write("\t".join([str(self.wordTableWidget.horizontalHeaderItem(c).text()) for c in range(self.wordTableWidget.columnCount())])+"\n")
			
			for r in range(self.wordTableWidget.rowCount()):
				out.write("\t".join([str(self.wordTableWidget.item(r, 0).text()).replace("\n","↩").replace("\t","⇥")]+[str(self.wordTableWidget.item(r, c).text()).strip() for c in range(1, self.wordTableWidget.columnCount())])+"\n")
			out.close()
			self.statusbar.showMessage("Exported "+filename,  3000)
	
	
		
	@pyqtSlot()
	def on_actionSelect_sections_with_occurrences_triggered(self):
		"""
		select the sections that contain the selected token
		"""
		if debug: print("actionSelect_sections_with_occurrences")
		self.selecting=True
		for i, si in enumerate(self.sectrast.sections):
			freq=self.sectrast.bows[si].get(self.selectedTokeni,0)
			if freq:
				self.sectionMap.item(i).setSelected(True)
			else: 
				self.sectionMap.item(i).setSelected(False)
		
		self.selecting=False
		self.on_sectionMap_itemSelectionChanged()

		
	@pyqtSlot()
	def on_actionSelectposspecificsections_triggered(self):
		"""
		select the sections that are marked as positive specificity
		"""
		if debug: print("on_actionSelectposspecificsections_activated")
		self.selecting=True
		for i, si in enumerate(self.sectrast.sections):
			s=self.sectrast.specificity[self.selectedTokeni][(si, )]
			if s>0:
				self.sectionMap.item(i).setSelected(True)
			else:
				self.sectionMap.item(i).setSelected(False)
		self.selecting=False
		self.on_sectionMap_itemSelectionChanged()
			
	@pyqtSlot()
	def on_actionSelectnegspecificsections_triggered(self):
		"""
		select the sections that are marked as negative specificity
		"""
		if debug: print("on_actionSelectnegspecificsections_activated")
		self.selecting=True
		for i, si in enumerate(self.sectrast.sections):
			s=self.sectrast.specificity[self.selectedTokeni][(si, )]
			if s<0:
				self.sectionMap.item(i).setSelected(True)
			else:
				self.sectionMap.item(i).setSelected(False)
		self.selecting=False
		self.on_sectionMap_itemSelectionChanged()
	
	@pyqtSlot()
	def on_actionPreferences_triggered(self):
		"""
		opening the help dialog
		"""
		PreferencesDialog(self).exec_()
		self.nbBestKids=int(self.config["configuration"]["nbBestKids"])
	
	#@pyqtSignature("bool")
	def on_actionCollocations_toggled(self,checked):
		"""
		
		"""	
		self.colloGroupBox.setVisible(checked)
		self.collocationlabel.setVisible(checked)
		#if checked: 
		self.graphButton.setChecked(checked)
		
		self.wordTableWidget.selectRow(0)
		
		self.config["configuration"]["openwithcolloc"]=int(checked)
		self.config.write()

	@pyqtSlot()
	def on_ngraDial_sliderReleased(self):
		"""
		ngra slider released: new value of ngra
		"""
		self.ngraDial.setEnabled(False)
		self.ngra=self.ngraDial.sliderPosition()
		if self.ngra not in self.sectrast.specollocs: 	self.sectrast.computeCollocations(self.ngra)
		if self.actionCollocations.isChecked():		self.colloc(self.selectedWord)
		self.ngraDial.setEnabled(True)
		
	@pyqtSlot()
	def on_actionInformationNexico_triggered(self):
		"""
		select the sections that are marked as negative specificity
		"""	
		QMessageBox.about(self,  "Nexico! - information",  "Nexico is a tool for textual statistics inside Gromoteur.\nThis is free software distributed under GPL Version 3.\nPlease visit gromoteur.ilpga.fr for further information.")
		#QMessageBox::about ( QWidget * parent, const QString & title, const QString & text )
	
	def makeCollocGraph(self):
		#print "makeCollocGraph"
		if (self.autoSelect or not self.selectedTokeni or self.ngra not in self.sectrast.specollocs): return
	
		self.graphicsBoxTitle = self.graphicsBox.title()
		if debug:QtWebKit.QWebSettings.globalSettings().setAttribute(QtWebKit.QWebSettings.DeveloperExtrasEnabled,True)
		self.webView.setPage(None) # necessary for repeated recentering
		#self.recenter=RecenterClass()
		
		#self.webView.settings().setUserStyleSheetUrl(QUrl(":images/images/graphstyle.css"));
		
		
		baseUrl = QUrl.fromLocalFile(QDir.current().absoluteFilePath("lib/resources/about.html")) # any html file to base the setHtml!!!
		self.webView.setHtml(self.collocations.graph(self.nbBestKids), baseUrl) 
		#self.webView.page().mainFrame().addToJavaScriptWindowObject("pyObj", self.recenter)  
		#self.webView.page().mainFrame().addToJavaScriptWindowObject("pyObj", self.recenter)  # 2019 to recreate! https://doc.qt.io/qt-5/qtwebenginewidgets-qtwebkitportingguide.html
		#print 3
		self.graphicsBox.setTitle("Collocations")
		self.actionOpen_graph_in_browser.setEnabled(True)
	
	#@pyqtSignature("bool")
	def on_graphButton_toggled(self,checked):
		"""
		Show and hide the cooc graph
		"""
		if checked:
			self.graphicsView.hide()
			self.makeCollocGraph()
			self.webView.show()
			
		else:
			self.webView.hide()
			self.graphicsBox.setTitle(self.graphicsBoxTitle)
			self.graphicsView.show()


	def clean(self, text):
		"""
		not used
		"""
		text=re.sub(r"\s+", " ", text, re.U)
		text=re.sub(r"\t+", " ", text, re.U)
		text=text.replace("...","…")
		apost = re.compile(r"[\‘\’]", re.U)
		text=apost.sub(r"'", text)
		return text	
	
	def words(self, text):
		"""
		not used
		"""
		text = self.clean(text)
		ponct = re.compile(r"(?<=\w)([\!\,\?\.\:\;»«])", re.U)
		text=ponct.sub(r" \1", text)
		apost = re.compile(r"([\'\(»«\‘\’])", re.U)
		text=apost.sub(r"\1 ", text)
		words=text.split()
		return words


#class NexicoGraphics( QtGui.QGraphicsView):
	#def __init__(self, parent = None):
		#"""
		#Constructor
		#"""
		#QtGui.QGraphicsView.__init__(self, parent)
		
	#def paintEvent(self, e):
		
		#painter = QtGui.QPainter(self)
		#painter.setRenderHint( QtGui.QPainter.Antialiasing, True)
		#path=QtGui.QPainterPath()
		#path.moveTo(20, 80)
		#path.lineTo(20, 30)
		#path.cubicTo(80, 0, 50, 50, 80, 80)
		#painter.drawPath(path)

class NexicoFileDialog(QFileDialog):
	"""
	Class documentation goes here.
	"""
	def __init__(self, parent = None):
		"""
		Constructor
		"""
		QFileDialog.__init__(self, parent)

		self.encodingComboBox = QtWidgets.QComboBox(self)
		self.encodingComboBox.setObjectName("encodingComboBox")
		self.encodingLabel = QtWidgets.QLabel("encoding", self)
		self.encodingLabel.setBuddy(self.encodingComboBox)
		self.layout().addWidget(self.encodingLabel)
		self.layout().addWidget(self.encodingComboBox)
		self.encodingComboBox.addItem(self.tr("autodetect"))
		for enc in parent.encodings: self.encodingComboBox.addItem(enc)
		self.encodingComboBox.setCurrentIndex(0)
		
		
	

#class GraphCanvas(FigureCanvas):
	#"""
	#Simple canvas used for drawing the collocation network
	#"""

	#def __init__(self, parent=None, width=5, height=4, dpi=100, color="#8691b7"):
		
		##print "__init__"
		#fig = Figure(figsize=(width, height), dpi=dpi)
		#self.axes = fig.add_subplot(111)
		#self.color=color
		#FigureCanvas.__init__(self, fig)
		#self.setParent(parent)
		
		#self.mpl_connect('pick_event',self.onpick)
		
	
	#def dive(self, toki, graph, id2label, specollocs, idtotoken, bestkids, level, maxlevel):
		#graph.add_node(toki)
		#id2label[toki]=idtotoken[toki].decode("utf-8")
		#spid=[(sp,id) for (id, sp) in specollocs[toki].iteritems() if sp!=0 ]
		#for sp,id in sorted(spid,reverse=True)[:bestkids]:
		##for (id,sp) in specollocs[toki].iteritems():
			##:
				#graph.add_weighted_edges_from([ (toki,id,sp) ])
				#id2label[id]=idtotoken[id].decode("utf-8")
				#if level<maxlevel:
					#self.dive(id,graph,id2label,specollocs,idtotoken,bestkids,level+1,maxlevel)

	#def compute(self, toki, specollocs, idtotoken, nexico):
		##G=nx.star_graph(20)
		##G=nx.random_geometric_graph(60,0.125)
		##G=nx.Graph()
		##print "compute"
		#self.nexico=nexico
		#self.DG=nx.DiGraph()
		#self.DG.clear()
		#self.axes.clear()
		#self.id2label={}
		
		#self.dive(toki,self.DG,self.id2label,specollocs,idtotoken,5,0,1)
		
		##print "_____",self.DG.nodes(data=True)
		
		##pos=nx.graphviz_layout(G)
		#pos=nx.spring_layout(self.DG)
		#nodes = nx.draw_networkx_nodes(self.DG,pos,ax=self.axes,node_size=50,node_color=self.color,alpha=0.4)
		#nodes.set_picker(True)
		#edges = nx.draw_networkx_edges(self.DG,pos,ax=self.axes,edge_color="#0d0d0d",alpha=0.4,with_labels=True)
		
		#nx.draw_networkx_labels(self.DG, pos, ax=self.axes,labels=self.id2label, font_size=8)




	#def onpick(self,event):
		
		##print self.id2label[self.DG.nodes()[event.ind[0]]]
		#self.nexico.selectWordInWordTableWidget(self.id2label[self.DG.nodes()[event.ind[0]]])
		
	
if __name__ == "__main__":
	
	pass
	
	sys.exit()
	app = QtWidgets.QApplication(sys.argv)
	signal.signal(signal.SIGINT, signal.SIG_DFL)
	splashpix = QtGui.QPixmap(":images/images/NexicoSplash.png")
	splash = QtWidgets.QSplashScreen(splashpix)
	splash.setMask(splashpix.mask());
	
	splash.show()
	window = Nexico(splash,None)
	window.setAttribute(Qt.WA_DeleteOnClose)
	#window.show()	
	window.showMaximized()
	sys.exit(app.exec_())
	
	
	
