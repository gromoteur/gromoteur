# -*- coding: utf-8 -*-

"""
Module implementing GroMainWindow.
"""

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import  QMainWindow, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import  pyqtSlot,  QDateTime,  QObject, QEvent,  Qt,   QDir
# , QSplitter, QSize
from PyQt5 import QtGui, QtWidgets

from PyQt5.QtSql import QSqlDatabase,  QSqlTableModel, QSqlQuery

import sys,  os, functools,  codecs,  shutil,  re, itertools, mimetypes # magic
from datetime import datetime
from time import sleep
from .Ui_groWindow import Ui_GroMainWindow


from .helpDialog import helpDialog
from .languageDetector import languageDialog
from .preferencesDialog import PreferencesDialog
from .goDialog import GoDialog
from .fieldselector import FieldSelector
from .groTools import GroTools
from .exporter import Exporter
from .groBase import GroBase
from configobj import ConfigObj
from .importer import Importer
from . import utils
#import groressources_rc
from . import groressources_rc
from . import ngram

#from memory_profiler import profile

textlen=200 # max length of text showing in table


debug=False
#debug=True


class GroMainWindow(QMainWindow, Ui_GroMainWindow):
	"""
	Gromoteur's main window
	"""
	
	def __init__(self, parent = None):
		"""
		Constructor
		"""
		
		QMainWindow.__init__(self, parent)
		self.base=None
		self.row=0
		self.column=0
		self.selectedColumnName=None
		self.textualization=""
		self.importexport=""
		self.qtdb=None  #qt base
		self.rowconditions="" # something like: rowid <= 2 and title like '%Toute%' 
		self.readjustingSelections=False
		self.columnUpdate=False
		self.justcreated=False
		self.filterframelist=[]
		self.filterConditions=[]
		self.condi=""
		self.groups={}
		self.selections=[]
		self.columns=[]
		self.ng = ngram.Ngram()
		
		self.ty2choices={	"nb":["=","≤", "≥", "≠"], 
				"txt":["match whole word", "contains the word", "equals"],  # TODO: , "match regex"
				"time":["before", "after"]}
		self.nbchoice2sym={"=":"=","≤":"<=", "≥":">=", "≠":"!="}
		
		grocfg = os.path.join(os.path.expanduser('~'), "gromoteur", ".settings", "gro.cfg")
		settingsfolder=os.path.join(os.path.expanduser('~'),"gromoteur",".settings")
		if not os.path.isfile(grocfg): # emergency repair. maybe useless
			shutil.copy(os.path.join("lib","gro.cfg"), settingsfolder)
		
		try:
			self.config = ConfigObj(grocfg,encoding="UTF-8")
			self.config.BOM=True
			if debug : print("read", grocfg)
			self.config["configuration"]
		except Exception as e:
			if debug : print("can't read config file: gro.cfg",e)
			self.config = ConfigObj(grocfg,encoding="UTF-8")
			self.config.BOM=True
			self.config["configuration"]={}
			self.config.filename=grocfg
			self.config.write()
		self.sentenceSplit=re.compile(self.config["configuration"]["sentenceSplit"], re.M+re.U)
		self.setupUi(self) # graphic setup of Ui_GroMainWindow
		self.guisetup()
		#self.retranslateUi(self)
		#answer=QtGui.QMessageBox.warning(self, "Really?",
				#"<p>Completely erase this file?</p>", 
				#QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Yes)
		
		
		
		
	def guisetup(self):
		"""
		graphic setup
		"""
		self.showAllDatabaseItems()
		
		self.columnsMenu=QtWidgets.QMenu(self)
#		self.columnsMenu.setWindowFlags(Qt.Tool)
#		self.columnsMenu.setWindowFlags(self.columnsMenu.windowFlags() | Qt.FramelessWindowHint);
		#self.columnsMenu.setAttribute(Qt.WA_TranslucentBackground);
		self.columnsMenu.setStyleSheet("QMenu{\nbackground-image : url(:images/images/quartercogtrans.png);\nbackground-position:bottom right;\nbackground-repeat:no-repeat;\n}");
		self.columnsButton.setMenu(self.columnsMenu)		
		self.on_corpuslistWidget_itemSelectionChanged()
		self.exportDialog = None
		
		
#		self.matchDateTimeEdit.hide()
#		self.matchNumberBox.hide()
		self.statusbar.showMessage("Welcome!", 20000)
		self.pb = QtWidgets.QProgressBar(self.statusBar())
		self.statusBar().addPermanentWidget(self.pb)
		self.pb.hide()
		self.setAttribute(Qt.WA_DeleteOnClose)		
		
		# TODO: fix this memory leak if i add these splitters!
		
		#self.vsplitter=QSplitter(2, self.centralwidget)  # 2=vertical orientation
		#self.centralGridLayout.addWidget(self.vsplitter,  0, 1)
		#self.vspgridLayout = QtGui.QGridLayout(self.vsplitter)
		#self.vspgridLayout.setSpacing(0)
		#self.vspgridLayout.setContentsMargins(2, 0, 2, 0)
		#self.vspgridLayout.addWidget(self.databaseContentGroupBox, 0, 0)
		
		#self.hsplitter=QSplitter(1, self.vsplitter) # 1=horizontal orientation
		#self.hsplitter.setHandleWidth(8)
		
		#self.hspgridLayout = QtGui.QGridLayout(self.hsplitter)
		#self.hspgridLayout.setSpacing(0)
		#self.hspgridLayout.setContentsMargins(2, 0, 2, 0)
		
		#self.vspgridLayout.addWidget(self.hsplitter)
		#self.vsplitter.setHandleWidth(8)

		##self.hspgridLayout.addWidget(self.tabFrame, 1, 0)
		
		self.filterTableWidget.cellClicked.connect(self.filterTableCellClicked)
		self.filterTableWidget.cellChanged.connect(self.filterTableCellChanged)
		self.corpuslistWidget.itemChanged.connect(self.corpusNameChanged)
		self.groupTableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows);
		self.groupTableWidget.selectionModel().selectionChanged.connect(self.groupSelectionChanged)
		self.groupTableWidget.setSortingEnabled(True)
		#self.tableView.doubleClicked.connect(self.tableViewDoubleClicked)
		
		self.invertAction=QtWidgets.QAction("invert selection", self.columnsMenu)
		self.invertAction.setFont(QtGui.QFont("Helvetica", 10, QtGui.QFont.Bold) )
		self.invertAction.setIcon(QtGui.QIcon ( QtGui.QPixmap(":images/images/invert.png") ))
		
		self.invertAction.triggered.connect(self.invertColumnSelection)
		
		
		#self.hspgridLayout.addWidget(self.tabWidget, 0, 0) # this line causes the memory leak
		self.lff=LoseFocusFilter(self)
		self.commentTextEdit.installEventFilter(self.lff)
		self.filterTableWidget.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		self.filterTableWidget.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
		self.filterTableWidget.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
		self.filterTableWidget.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
		
	
		#self.tableView.setSelectionMode(QtGui.QTableView.SingleSelection)
		#self.tableView.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
		self.tableView.horizontalHeader().resizeSections(QtWidgets.QHeaderView.ResizeToContents)
		#self.tableView.setRowHeight(50)
		#self.tableView.verticalHeader().setDefaultSectionSize(5);
		
		self.tableView.horizontalHeader().setStretchLastSection(True)
		
		
		headers = self.tableView.horizontalHeader()
		headers.setContextMenuPolicy(Qt.CustomContextMenu)
		headers.customContextMenuRequested.connect(self.openTableContextMenu)
		
		
		
		#self.connect(headers, SIGNAL('customContextMenuRequested(const QPoint&)'), self.openTableContextMenu)
		# Popup Menu is not visible, but we add actions from above
		self.tablePopMenu = QtWidgets.QMenu( self )
		self.tablePopMenu.addAction( self.actionOnly_this_column )
		self.tablePopMenu.addAction( self.actionHide_this_column)
		self.tablePopMenu.addAction(self.invertAction )
		self.tablePopMenu.addAction(self.actionShow_all_columns )

	
	#def tableViewDoubleClicked(self, index):
		#print "___",index
	
	################### corpus list #################
	################################################
	
	def showAllDatabaseItems(self,  select=None):	
		"""
		showing all the existing databases
		"""
		groDataIcon=QtGui.QIcon ( QtGui.QPixmap(":images/images/databaseGromoteurXL.png") )
		self.corpuslistWidget.clear()
		databaseList = []
		for f in os.listdir("corpora")+os.listdir(os.path.join(os.path.expanduser('~'),"gromoteur","corpora")):
			try:	
				if f.endswith(".sqlite"):
			# horrible stuff because of strange ntfs encodings from usb-sticks when non ascii chars :-/
					databaseList += [QtWidgets.QListWidgetItem(groDataIcon, os.path.normcase(f)[:-7] , self.corpuslistWidget)]
			except:
					try:	
						if f.decode('cp1252').endswith(".sqlite"):
							databaseList += [QtWidgets.QListWidgetItem(groDataIcon, os.path.normcase(f).decode('cp1252')[:-7] , self.corpuslistWidget)]
					except:	pass
					
		
		for db in databaseList:		
			db.setFlags(db.flags() | Qt.ItemIsEditable)
		
		if select and len:
			matchedItems = self.corpuslistWidget.findItems(select, Qt.MatchExactly)
			if len(matchedItems) > 0:
				self.corpuslistWidget.setCurrentItem(matchedItems[0]) # select 
	
	
		
	#@profile
	
	@pyqtSlot() # signal with no arguments
	def on_corpuslistWidget_itemSelectionChanged(self):
		"""
		called if a new corpus item is selected (or none is selected)
		
		"""
		dbselected=(len(self.corpuslistWidget.selectedItems())==1)  # one item selected 
		
		self.actionDelete.setEnabled(dbselected)
		self.actionImport_from_Web.setEnabled(dbselected)
		self.actionDatabaseFillFromFolder.setEnabled(dbselected)
		self.actionFieldSelect.setEnabled(dbselected)
		self.actionTools.setEnabled(dbselected)
#		self.filterScrollArea.setEnabled(dbselected)
		self.actionSelection.setEnabled(dbselected)
		self.actionNexico.setEnabled(dbselected) #  and self.selectionsTableWidget.rowCount()
		self.actionOpen_Table.setEnabled(dbselected) 
		self.actionKeepSelectedRows.setEnabled(False) 
		self.actionRemoveSelectedRows.setEnabled(False) 
		
		self.actionKeep_only_current_rows.setEnabled(self.rowconditions!="")
		self.actionRemove_current_rows.setEnabled(self.rowconditions!="")
		
		if dbselected :
			if hasattr(self, 'base') and self.base and self.base.isAlive(): 
				self.base.close()
				del self.base 
			dbfilename=self.corpuslistWidget.currentItem().text()
			try:
				self.base=GroBase(dbfilename)
			except:
				QtWidgets.QMessageBox.critical(self, "Cannot open database",
				"Unable to establish a database connection with the file {dbfilename}.".format(dbfilename=dbfilename), 
				QtWidgets.QMessageBox.Cancel)								
				self.base=None
		else:
			self.base = None
		if debug: print("on_corpuslistWidget_itemSelectionChanged. base:",self.base)
		#return # ##########################
		self.databaseShowInfo()
		if self.base:
			self.tableView.setStyleSheet("")
			self.tableView.setAutoFillBackground(False)
			self.tableView.horizontalHeader().setStyleSheet("")
			self.allCollumns=self.base.getColumns(self.textualization)
			self.columns=[]
			for i, action in enumerate(self.columnsMenu.actions()):
				if action.isChecked(): self.columns+=[str(action.text())]
			self.filterTableWidget.setRowCount(0)
			self.addEmptyFilter()
			self.updateGroupComboBox()
			
		self.tabWidget.setCurrentWidget(self.informationTab)
		self.duplicateButton.setChecked ( False )
		
		
	def databaseShowInfo(self):
		"""
		 when a database is selected, showing the general information concerning the database
		"""

		dbselected=(self.base!=None)
		self.tabWidget.setEnabled(dbselected)
		
		self.textualizationFrame.setEnabled(dbselected)
		self.actionExport.setEnabled(dbselected)
		self.actionDuplicateDatabase.setEnabled(dbselected)
		
		if self.base:
			nbPages, nbSentences, nbWords,  comments, configfile, lastaccess,  nbLinksToDo,nbLinksDone	= self.base.nbPages, self.base.nbSentences, self.base.nbCharacters,  self.base.comments, self.base.configfile, self.base.lastaccess,  self.base.nbLinksToDo,self.base.nbLinksDone
			
			size=utils.fileSize(self.base.filename)
			self.listTextualizations()
		else:
			nbPages, nbSentences, nbWords,  comments, configfile, lastaccess,  size, nbLinksToDo,nbLinksDone = 0, 0, 0, "", "",  0,  0, 0, 0
		#return ####################"
		self.pageSpinbox.setValue(nbPages)
		self.sentenceSpinbox.setValue(nbSentences or 0)
		self.wordSpinbox.setValue(nbWords or 0)
		self.sizeSpinbox.setValue(size or 0)
		self.commentTextEdit.setPlainText (comments or "")
		self.configFileEdit.setText(configfile)
		self.dateTimeEdit.setDateTime(QDateTime.fromTime_t ( int( lastaccess ) ) )
		#if nbLinksToDo and nbLinksDone:
		self.links2DoSpinbox.setValue(nbLinksToDo)
		self.linksDoneSpinbox.setValue(nbLinksDone)
		self.tabWidget.setCurrentWidget(self.informationTab)
	
	################### main table view #################
	################################################
	
	
	def tableviewselectionChanged(self, a):
		try:
			self.on_tableView_clicked(a.indexes()[0])
		except:
			pass

			
	#@pyqtSignature("QModelIndex")
	def on_tableView_clicked(self, index):
		model=self.tableView.model()
		self.selectedColumnName= str(model.headerData(index.column(), 1, 0)) # .toString ()
		self.row= index.row()
		self.column= index.column()
		i=index
		self.tabWidget.setCurrentIndex(1) # show the information tab
		try:		self.cellcontent.setPlainText(self.model.datacomplete(i) )
		except:		self.cellcontent.setPlainText(self.model.datacomplete(i) ) # .toString()
		self.actionKeepSelectedRows.setEnabled(True) 
		self.actionRemoveSelectedRows.setEnabled(True) 
	
	
	@pyqtSlot()
	def on_recomputePushButton_clicked(self):
		"""
		computes simple statistics based on the nb columns		
		"""
		self.updateProgress(33)
		self.stopqtdb()				
		self.base.recomputeStats(self.textualization, str(self.commentTextEdit.toPlainText()))
		self.updateProgress(66)
		self.waitForBase()
		self.databaseShowInfo()
		self.on_corpuslistWidget_itemSelectionChanged()
		if not self.checkDatabaseOK():
			QtWidgets.QMessageBox.critical(self, "Recomputation failed",
					"Unable to compute the general data for {filename}!".format(filename=self.base.filename), 
					QtWidgets.QMessageBox.Cancel)
		self.endProgress()
		self.duplicateButton.setChecked ( False )
		
	
	################### which columns to show in main table? ################# 
	########################################################################
	
	
		
	def columnSelectionChanged(self):
		"""
		triggered if the selection of the columns changed, triggered by each column action in the columnsMenu
		"""
		
		self.sql()
		if self.columnUpdate:return
		if not self.readjustingSelections:
			self.columnsMenu.exec_() 
			self.readjustingSelections=False
		self.columns=[]
		for i, action in enumerate(self.columnsMenu.actions()):
			if action.isChecked(): self.columns+=[str(action.text())]
		self.updatereductions()


	def invertColumnSelection(self):
		"""
		the invert button triggers this
		"""
		self.columnUpdate=True
		self.columns=[]
		for action in self.columnsMenu.actions():
			action.setChecked(not action.isChecked())
			if action.isChecked():
				self.columns+=[str(action.text())]
		self.columnUpdate=False
		self.updateFilterConditions()
		if not self.readjustingSelections:
			self.columnsMenu.exec_() 
			self.readjustingSelections=False
	
	
	
	@pyqtSlot() # signal with no arguments
	def on_actionShow_all_columns_triggered(self):
		"""
		action in context menu of table header
		"""		
		self.columnUpdate=True
		self.columns=[]
		for i,action in enumerate(self.columnsMenu.actions()[:-2]):
			action.setChecked(True)
			print(str(action.text()))
			self.columns+=[str(action.text())]
		self.columnUpdate=False
		
	
	
	#@pyqtSignature("QModelIndex")
	#def on_selectionsTableWidget_clicked(self, index):
		#"""
		#handle clicks in the selection table
		#"""
		#if index.column()==4: # the 4th column is the delete column
			## remove selection
			#self.selectionsTableWidget.removeRow(index.row())
			#self.selections.pop(index.row())
		#else:
			## choose selection
			#self.readjustingSelections=True
##			print self.filterConditions
			#sel=self.selections[index.row()]
			#self.textualizations.setCurrentIndex(self.textualizations.findText(sel.textualization))
			#for i, action in enumerate(self.columnsMenu.actions()):
##				print i,  action,  action.text(),  action.isChecked()
				#if action.text() in sel.columns: action.setChecked(True)
				#else:action.setChecked(False)
		#self.columnsMenu.close()
	
	
	#def on_actionSelection_triggered(self):
		#"""
		#fixes the current view to a new selection
		#"""
		#if debug: print "on_actionSelection_triggered",selection.condi
		#selection=Selection(self)
		#self.selections+=[selection]
		
		#self.tabWidget.setCurrentIndex(5) # show the selections table
		#self.selectionsTableWidget.setEnabled(True)
		
		#row=self.selectionsTableWidget.rowCount()
		#self.selectionsTableWidget.setRowCount(row+1)
		#self.selectionsTableWidget.setItem(row, 0, QTableWidgetItem(str(row)))	
		#self.selectionsTableWidget.setItem(row, 1, QTableWidgetItem(selection.textualization))
		#self.selectionsTableWidget.setItem(row, 2, QTableWidgetItem(" ".join(selection.columns)))
		#self.selectionsTableWidget.setItem(row, 3, QTableWidgetItem(selection.condi))
		#self.selectionsTableWidget.setItem(row, 4, QTableWidgetItem(QIcon(":images/images/delete.png"),  ""))
		#qsdf
	
	
			
	def openTableContextMenu(self, point):
		"""
		triggered when right click in table header
		"""
		self.tableColumnIndex=self.tableView.indexAt(point).column()
		if self.tableColumnIndex<0:return
		columnName=self.columnsMenu.actions()[self.tableColumnIndex].text()
		self.actionOnly_this_column.setText('Show only the column "'+columnName+'"')
		self.actionHide_this_column.setText('Hide the column "'+columnName+'"')
		self.readjustingSelections=True
		self.tablePopMenu.exec_( self.tableView.horizontalHeader().mapToGlobal(point) )
		self.readjustingSelections=False
		self.updateFilterConditions()
		if not self.readjustingSelections: self.readjustingSelections=False
	
	
	
	@pyqtSlot() # signal with no arguments
	def on_actionOnly_this_column_triggered(self):
		"""
		action in context menu of table header
		"""		
		self.columnUpdate=True
		self.columns=[]
		for i,action in enumerate(self.columnsMenu.actions()):
			action.setChecked(i==self.tableColumnIndex)
			if action.isChecked(): self.columns+=[str(action.text())]
		self.columnUpdate=False
		#self.updateFilterConditions()
		#if not self.readjustingSelections:
			#self.readjustingSelections=False
	
	
	@pyqtSlot() # signal with no arguments
	def on_actionHide_this_column_triggered(self):
		"""
		action in context menu of table header
		"""		
		self.columnUpdate=True
		self.columns=[]
		for i,action in enumerate(self.columnsMenu.actions()):
			if i==self.tableColumnIndex: action.setChecked(False)
			if action.isChecked(): self.columns+=[str(action.text())]
		self.columnUpdate=False
		#self.updateFilterConditions()
		#if not self.readjustingSelections:
			#self.readjustingSelections=False
	
	
	
	
	
	################### group stuff   ########
	##########################################
	
	@pyqtSlot()
	def on_groupPushButton_clicked(self):
		"""
		here the grouping is done
		"""
		matchtext=str(self.groupLineEdit.text())
		self.groups={}
		if matchtext:
			self.pb.setMaximum(int(self.pageSpinbox.value()))
			counter=0
			if self.ignoreCaseCheckBox.isChecked(): 	matcher=re.compile(matchtext, re.U+re.I+re.M)
			else:					matcher=re.compile(matchtext, re.U+re.M)
			condi=""
			if self.rowconditions: 			condi=" WHERE "+self.rowconditions
			self.selectstatement="SELECT rowid,"+ str(self.groupComboBox.currentText())+" FROM "+self.textualization+condi+" ;"
			
			#grobase vs qbase:
			#for entry in self.base.select(self.selectstatement):
			self.completemodel.setQuery(QSqlQuery(self.selectstatement))
			for i in range(self.completemodel.rowCount()):
				#print "___",self.completemodel.data(self.completemodel.index(i,1)).toString()
				self.updateProgress(counter)
				counter+=1
				rowid =		int(self.completemodel.data(self.completemodel.index(i,0))) # .toString()
				itemcontent=	self.completemodel.data(self.completemodel.index(i,1)) # .toString()
				match=matcher.search(str(itemcontent))
				if match:
					try:key=match.group(1)
					except:key="_other_"
				else: key="_other_"
				if self.ignoreCaseCheckBox.isChecked():key=key.lower()
				self.groups[key]=self.groups.get(key, [])+[rowid]			
			self.completemodel.setQuery(QSqlQuery(None))
			
			self.groupTableWidget.setRowCount(len(self.groups))
			
			for ri, g in enumerate(sorted(self.groups, key=lambda k: len(self.groups[k]), reverse=True )):
				#print ri,g,len(self.groups[g])
				it=QTableWidgetItem(g)
				it.setFlags( Qt.ItemIsSelectable |  Qt.ItemIsEnabled )
				self.groupTableWidget.setItem(ri, 0, it)
				it=QTableWidgetItem()
				it.setData(Qt.EditRole, len(self.groups[g]))
				it.setFlags( Qt.ItemIsSelectable |  Qt.ItemIsEnabled )
				self.groupTableWidget.setItem(ri, 1, it)
			
			self.useGroupsCheckBox.setChecked(True)
			self.endProgress()
		else:
			self.useGroupsCheckBox.setChecked(False)
			self.groupTableWidget.setRowCount(0)
			self.groupTableWidget.clear()
		#
		
		
	@pyqtSlot()
	def on_groupLineEdit_returnPressed(self):
		"""
		"""
		self.on_groupPushButton_clicked()
		
	
	def updateGroupComboBox(self):
		self.groupComboBox.clear()
		for colname in self.allCollumns:
			self.groupComboBox.addItem(colname)
		if "url" in self.allCollumns:
			self.groupComboBox.setCurrentIndex ( self.allCollumns.index("url") )
	
	def groupSelectionChanged(self):
		"""
		some groups were selected
		select the corresponding rows in the main table
		"""
		self.tableView.selectionModel().clearSelection()
		
		# disconnect showing the source of a selected item in the main table
		self.tableView.selectionModel().selectionChanged.disconnect(self.tableviewselectionChanged)
		
		# get the selected groups
		selectedgroups={}
		for r in self.groupTableWidget.selectionModel().selectedRows():
			selectedgroups[str(self.groupTableWidget.item(r.row(),0).text())]=None
		
		# get the corresponding rowids
		ichain = list(itertools.chain.from_iterable([self.groups[g] for g in selectedgroups]))
		self.tableView.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
		# select the corresponding rows in the main table
		for i in range(self.tableView.model().rowCount()):
			if int(self.tableView.model().data(self.tableView.model().index(i,0))) in ichain : #.toString()
				self.tableView.selectRow(i)
		
		# reconnect showing the source of a selected item in the main table
		self.tableView.selectionModel().selectionChanged.connect(self.tableviewselectionChanged)
	
		self.updatereductions()
	
	################### start subwindows    ########
	################################################
	
	
	@pyqtSlot() # signal with no arguments
	def on_actionlanguageDetector_triggered(self):
		"""
		opening the help dialog
		"""
		languageDialog(self).exec_()
	
	
	@pyqtSlot() # signal with no arguments
	def on_actionGromoteur_Help_triggered(self):
		"""
		opening the help dialog
		"""
		helpDialog().exec_()
	
	
	@pyqtSlot() # signal with no arguments
	def on_actionPreferences_triggered(self):
		"""
		opening the help dialog
		"""
		PreferencesDialog(self).exec_()
		
	
	
	@pyqtSlot() # signal with no arguments
	def on_actionImport_from_Web_triggered(self):
		""""
		the main subwindow: opening the goDialog
		
		"""
		if self.qtdb: self.qtdb.close()
		if self.base and self.base.isAlive():
			self.base.close()

		self.goDialog = GoDialog(parent=self, base=self.base)
				
		if QtWidgets.QDesktopWidget().availableGeometry( QtWidgets.QDesktopWidget().primaryScreen()).height()<1000: self.goDialog.showMaximized()
		
		self.goDialog.exec_()

		sleep(.01) # wait for the database to close completely before giving back the textualName
		
		self.on_corpuslistWidget_itemSelectionChanged()
	
	
	@pyqtSlot() # signal with no arguments
	def on_actionFieldSelect_triggered(self):
		"""
		opening fieldselector window: selecting the part of a page you want 
		"""
		index=self.completemodel.index(self.row ,1) # column 1 is the url
		
		url= str(index.data()) or "" # .toString()
		if self.qtdb: self.qtdb.close()
		
		self.model.setQuery(QSqlQuery(None))
		self.completemodel.setQuery(QSqlQuery(None))

		fieldselector = FieldSelector(self.base, url,  self.textualization, self.selectedColumnName, self.config["configuration"]["newLineTags"],self.sentenceSplit)
		result=fieldselector.exec_()
		self.qtdb.open()
		
		if result and fieldselector.textualName:
			self.databaseShowInfo()
			self.textualizations.setCurrentIndex(self.textualizations.findText(fieldselector.textualName))
			
		else:
			self.textualizations.setCurrentIndex(0)
			self.databaseShowInfo()
			
	
	@pyqtSlot() # signal with no arguments
	def on_actionTools_triggered(self):
		"""
		opening tools window: lemmatizer, segmenter
		"""
				
		columns=self.columns[:]
		
		if self.qtdb: self.qtdb.close()
		self.model.setQuery(QSqlQuery(None))
		self.completemodel.setQuery(QSqlQuery(None))
		
		groTools = GroTools(self.base, str(self.textualizations.currentText()),  self)
		
		result=groTools.exec_()
		self.on_corpuslistWidget_itemSelectionChanged()
		
		columns+=groTools.insertColumns # adding newly created columns to visible 
		
		self.readjustingSelections=True
		for i, action in enumerate(self.columnsMenu.actions()):
				if action.text() in columns: action.setChecked(True)
				else:action.setChecked(False)
		self.readjustingSelections=False
		if len(groTools.insertColumns):	message="Created "+" ".join(groTools.insertColumns)+"!"
		elif groTools.replacements: 		message="Modified {occ} occurrences in {pag} pages!".format(occ=str(groTools.replacements), pag=str(groTools.replacedPages))
		else: 				message="Nothing changed"
		self.statusbar.showMessage(message, 20000)
	
	
	
	
	
	
	@pyqtSlot() # signal with no arguments
	def on_actionExport_triggered(self):
		"""
		Shows the export dialog.
		"""
		while self.qtdb.isOpen():  self.qtdb.close()

		self.importexport="Exporting"
		self.exportDialog = Exporter(self)
		self.textualization=str(self.textualizations.currentText())
	
		#self.exportDialog.show()
		#self.exportDialog.progressChanged.connect(self.updateProgress)
		self.exportDialog.progressChanged.connect(self.updateProgress)
		self.exportDialog.progressFinished.connect(self.endProgress)
		result=self.exportDialog.exec_()

		
		
		self.on_corpuslistWidget_itemSelectionChanged()
	
	def endProgress(self):
		"""
		when export is completed, hide the progressbar
		"""
		self.pb.hide()
		self.statusbar.showMessage(self.importexport+" terminated", 20000)
		
		
	def updateProgress(self, i):
		"""
		when exporting the database into files, showing the progress 
		"""
		if self.pb.isHidden():self.pb.show()
		self.statusbar.showMessage(self.importexport+"...")
		self.pb.setValue(i)
	
	
	
	
	@pyqtSlot() # signal with no arguments
	def on_actionNexico_triggered(self):
		"""
		starts Nexico!
		"""
		from .groNexico import startNexico
		self.nexico=startNexico(self)	
	
	
	
	################### import stuff ###############
	################################################
	
	
	@pyqtSlot() # signal with no arguments
	def on_actionDatabaseFillFromFolder_triggered(self):
		"""
		import a whole folder of text or pdf files
		"""
		
		foldername=str( QFileDialog.getExistingDirectory(self, "Choose directory to completely import into the database",os.path.join(os.path.expanduser('~'),"gromoteur","corpora"), QFileDialog.DontUseNativeDialog))
		if foldername:
			filelist=[]
			filelist=self.addFolderToDatabase( foldername,  filelist)
			self.importexport="Importing"
			self.importer = Importer(self, filelist)
			self.importer.message.setText("Adding <b>"+str(len(filelist))+"</b> files from <br><i>"+foldername+"</i><br> and its subfolders to the database.<br><br>If the files exist in the database, they will be overwritten.<br><br>Are you sure?")
			
			qlist =  filelist
			self.importer.listWidget.addItems(qlist)
			
			self.importer.show()
			self.importer.progressChanged.connect(self.updateProgress)
			self.importer.progressFinished.connect(self.endProgress)
		
		
	def addFolderToDatabase(self, foldername,   filelist):
		for r,d,f in os.walk(foldername,   followlinks=True):
			for file in f:
				# print "uuu",file
				if file.startswith("."):continue
				fp = str(os.path.join(r,file))
				#filemime=self.mime.from_file(fp.encode("utf-8"))
				filemime,guessedencoding=mimetypes.guess_type(fp)# .encode("utf-8")
				#print fp,filemime
				if filemime and (filemime.startswith("text") or filemime.startswith("ASCII") or filemime.startswith("UTF-8") or filemime=="application/pdf"):
#					print 'adding', fp
					filelist+=[fp]
		for directory in d:
			self.addFolderToDatabase(self, os.path.join(r, directory),  filelist)
		return sorted(filelist)
		
	
	@pyqtSlot() # signal with no arguments
	def on_actionOpen_Table_triggered(self):
		"""
		import of tab separated file
		"""
		
		filename, filt=QtWidgets.QFileDialog.getOpenFileName(self,"Choose the tab-separated file to import",
								"",
								"all files (*.*)") # , QtWidgets.QFileDialog.DontUseNativeDialog
		if filename:
			with codecs.open(filename, "r", "utf-8") as f:
			
				textualid, =next(self.base.select( "select id from textualizations where name='"+self.textualization+"';"))
			
				textid2textname=self.base.getTextColumns(self.textualization)
				textname2textid=dict((v,k) for k,v in textid2textname.items())
				insertTextIds=[textname2textid[c]  for c in ["title", "text"] ]
				i=0
				for line in f:
					
					eles = line.strip().split("\t")
					if len(eles)==0:
						continue
					elif len(eles)==1:
						i+=1
						self.base.enterData(i,  filename, str(i), eles[0], insertTextIds,  textualid)
					elif len(eles)>=2:
						i+=1
						self.base.enterData(i,  filename, " ".join(eles[0:-1]), eles[-1], insertTextIds,  textualid)	
				
				todo=self.base.reqs.qsize()
				self.pb.setMaximum(todo)
				self.pb.show()
				while not self.base.reqs.empty():
					self.statusbar.showMessage(str(self.base.reqs.qsize())+" to go...")
					self.pb.setValue(todo-self.base.reqs.qsize())
					sleep(1)
				self.pb.hide()
				self.on_corpuslistWidget_itemSelectionChanged()	
				self.statusbar.showMessage("Import has finished", 20000)
			
	
	
	################### database operations ########
	################################################
	
		
	
	@pyqtSlot() # signal with no arguments
	def on_actionNew_triggered(self):
		"""
		new database.
		"""
		self.justcreated=True
		corpusname, ok=QtWidgets.QInputDialog.getText(self, "new corpus","Please indicate the name of the new corpus:",QtWidgets.QLineEdit.Normal, QDir.home().dirName()+"Corpus-"+datetime.strftime(datetime.now(), '%Y_%m_%d_%H_%M_%S')) 
		if not ok: return
		db=str(corpusname).lower()
		dbFile= os.path.join(os.path.expanduser('~'),"gromoteur","corpora",db+".sqlite" )

		if os.path.exists(dbFile):
			message = QtWidgets.QMessageBox(self)
			message.setText("<b>The corpus <i>"+db+"</i> exists.</b>")
			message.setInformativeText("Do you want to overwrite this corpus?")
			message.setIcon(QtWidgets.QMessageBox.Warning)
			message.setStandardButtons(QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Yes)
			result=message.exec_()
			if  result== message.Yes:
				if self.base.name.lower() == db.lower():
					self.base.close()
					self.delqtdb()
				os.remove(dbFile)
			else:return

		# KAPOR: the previous one may still be open, close it before creating a new one
		if self.base and self.base.isAlive():
			self.base.close()
			del self.base
		self.base=GroBase(db)
		self.showAllDatabaseItems(db)
		self.justcreated=False
	
	
	@pyqtSlot() # signal with no arguments
	def on_actionDuplicateDatabase_triggered(self):
		"""
		duplicate database.
		"""
		corpusname, ok=QtWidgets.QInputDialog.getText(self, "new corpus","Please indicate the name of the duplicate database:",QtWidgets.QLineEdit.Normal, self.base.name+".bak")
		if not ok: return
		
		self.delqtdb()
		if self.base:
			try:
				if hasattr(self, 'goDialog'):
					self.goDialog.base.close()
					if self.goDialog.spider:
						self.goDialog.spider.base.close()
					del self.goDialog
				filename=self.base.filename
				self.base.close()
				sleep(0.1)
				shutil.copy2(filename, os.path.join(os.path.expanduser('~'),"gromoteur","corpora", str(corpusname)+".sqlite"))
			except:
				QtWidgets.QMessageBox.critical(self, "Cannot duplicate database",
					"Unable to duplicate the file {filename}. Check permissions!".format(filename=self.base.filename), 
					QtWidgets.QMessageBox.Cancel)
		self.showAllDatabaseItems()
	
	def corpusNameChanged(self,  item):
		if self.justcreated:return
		self.delqtdb()
		newname=None
		if self.base:
			try:
				if hasattr(self, 'goDialog'):
					self.goDialog.base.close()
					if self.goDialog.spider:
						self.goDialog.spider.base.close()
					del self.goDialog
				oldname=self.base.filename
				newname=str(item.text())
				self.base.close()
				sleep(0.1)
				shutil.move(oldname, os.path.join(os.path.expanduser('~'),"gromoteur","corpora", newname+".sqlite"))
			except:
				QtWidgets.QMessageBox.critical(self, "Cannot duplicate database",
					"Unable to change the name of the database {filename}. Check permissions!".format(filename=oldname), 
					QtWidgets.QMessageBox.Cancel)
				return
		if newname:		self.showAllDatabaseItems(newname)	
	
	
	@pyqtSlot() # signal with no arguments
	def on_actionDelete_triggered(self):
		"""
		delete database
		"""
		try:t="<b>Deleting corpus <i>"+str(self.base.name)+"</i>.</b>"
		except:t="<b>Deleting corpus.</b>"
		answer=QtWidgets.QMessageBox.warning(self, "Really?",
				t+"<p>Completely erase this file?</p>", 
				QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Yes)

		if  answer== QtWidgets.QMessageBox.Yes: 
			self.delqtdb()
			if self.base:
				if hasattr(self, 'goDialog'):
					self.goDialog.base.close()
					if self.goDialog.spider:
						self.goDialog.spider.base.close()
					del self.goDialog
				filename=self.base.filename
				self.base.close()
				sleep(0.1)
				try:
					os.remove(filename)
				except:
					QtWidgets.QMessageBox.critical(self, "Cannot erase database",
				"Unable to erase the file {filename}. Check permissions!".format(filename=filename), 
				QtWidgets.QMessageBox.Cancel)
			else: # case there was some problem opening the file in the first place
				filename=os.path.join(os.path.expanduser('~'),"gromoteur","corpora",str(self.corpuslistWidget.currentItem().text())+".sqlite" )
#				print filename
				try:
					os.remove(filename)
				except:
					QtWidgets.QMessageBox.critical(self, "Cannot erase database",
				"Unable to erase the file {filename}. Check permissions!".format(filename=filename), 
				QtWidgets.QMessageBox.Cancel)
				
		self.showAllDatabaseItems()
	
	
	
	@pyqtSlot() # signal with no arguments
	def on_actionKeepSelectedRows_triggered(self):
		""""
		database reduction operation
		"""
		selectedrowids={}
		for it in self.tableView.selectionModel().selection().indexes():			
			selectedrowids[int(self.tableView.model().data(self.tableView.model().index(it.row(),0)))]=None	# .toString()	
		if selectedrowids:
			nbrows = len(selectedrowids)
			statement=",".join([str(i) for i in selectedrowids])
			self.reduceRows(nbrows, "not in", statement)
			self.checkDatabaseOK()

	
	@pyqtSlot() # signal with no arguments
	def on_actionRemoveSelectedRows_triggered(self):
		""""
		database reduction operation
		"""
		selectedrowids={}
		for it in self.tableView.selectionModel().selection().indexes():			
			selectedrowids[int(self.tableView.model().data(self.tableView.model().index(it.row(),0)))]=None	# .toString()
		if selectedrowids:
			nbrows = len(selectedrowids)
			statement=",".join([str(i) for i in selectedrowids])
			self.reduceRows(nbrows, "in", statement)
			self.checkDatabaseOK()
	
	
	@pyqtSlot() # signal with no arguments
	def on_actionKeep_only_current_rows_triggered(self):
		""""
		database reduction operation
		"""
		if self.rowconditions:where="where not "+self.rowconditions
		else: where=""
		countstatement="select count(rowid) from {view} {where};".format(view=self.textualization,  where=where)
		nbrows = self.base.totalNum(countstatement)
		statement="select rowid from {view} {where}".format(view=self.textualization,  where=where)
		self.reduceRows(nbrows, "in", statement)
		
		
	
	@pyqtSlot() # signal with no arguments
	def on_actionRemove_current_rows_triggered(self):
		""""
			database reduction operation
		"""
		if self.rowconditions:where="where "+self.rowconditions
		else: where=""
		countstatement="select count(rowid) from {view} {where};".format(view=self.textualization,  where=where)
		nbrows = self.base.totalNum(countstatement)
		statement="select rowid from {view} {where}".format(view=self.textualization,  where=where)
		self.reduceRows(nbrows, "in", statement)

	def reduceRows(self, nbrows, inn, statement):
		""""
		database reduction operation
		"""
		if not self.base:return # catch weird errors
	
		answer=QtWidgets.QMessageBox.warning(self, "Really?",
				"Do you really want to delete {nbrows} rows of this database?\nThis cannot be undone!".format(nbrows=nbrows), 
				QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Yes)
		if answer==QtWidgets.QMessageBox.Yes:
			self.importexport="Deleting"
			self.stopqtdb()
			self.updateProgress(50)			
			self.base.reduceRows(self.textualization, inn, statement )
			self.waitForBase()
			if self.checkDatabaseOK():
				self.endProgress()
		self.on_recomputePushButton_clicked()
		self.on_corpuslistWidget_itemSelectionChanged()
		
		
	
	def checkDatabaseOK(self):
		if not self.base:
			QtWidgets.QMessageBox.critical(self, "Problem with database",
			"\n\nDoes another program access the database file?")
			self.on_corpuslistWidget_itemSelectionChanged()
			return False
		if self.base.errorState:
			QtWidgets.QMessageBox.critical(self, "Problem with database",
			self.base.errorState + "\n\nDoes another program access the database file?")
			self.on_corpuslistWidget_itemSelectionChanged()
			return False
		return True


	
	@pyqtSlot() # signal with no arguments
	def on_actionKeep_only_current_columns_triggered(self):
		""""
		database reduction operation actionKeep_only_current_columns 
		TODO: currently absent. reintroduce this. difficulty: no column delete on sqlite, some columns in source, some in text table
		"""
		if debug: print("self.columns",self.columns)
		
		self.base.reduceColumns(set(self.base.getColumns(self.textualization))-set(self.columns),  self.textualization)
		
		self.on_corpuslistWidget_itemSelectionChanged()
	
	
	@pyqtSlot() # signal with no arguments
	def on_actionRemove_current_columns_triggered(self):
		""""
		database reduction operation
		"""
		if debug: print("self.columns",self.columns)
	
	def sql(self):
		"""
		does the qt sql stuff:
		filling the table with db content
		"""
		if self.qtdb: self.qtdb.close()
		else: self.qtdb = QSqlDatabase.addDatabase("QSQLITE")
		self.qtdb.setDatabaseName(self.base.filename)
		self.qtdb.open()

		self.model = GroSqlTableModel(self)
		self.model.setTable(self.textualization)
		self.updateFilterConditions()
		
		self.tableView.setModel(self.model)
		for i, action in enumerate(self.columnsMenu.actions()):
			if action.isEnabled(): self.tableView.setColumnHidden(i, not action.isChecked())

		
		self.allCollumns=self.base.getColumns(self.textualization)

		self.completemodel=GroSqlTableModel()
		self.completemodel.setQuery(QSqlQuery("SELECT * FROM "+ self.textualizations.currentText()))
		index=self.completemodel.index(self.row ,1)
		self.tableView.selectionModel().selectionChanged.connect(self.tableviewselectionChanged)
	
	
	
	def stopqtdb(self):
		while self.qtdb.isOpen():  
			self.qtdb.close()
			self.model.setQuery(QSqlQuery(None))
			self.completemodel.setQuery(QSqlQuery(None))
	
	def waitForBase(self):
		while not self.base.reqs.empty():
			if not self.checkDatabaseOK(): break
			if debug: print("database queue not empty")
		sleep(0.1)
	
	
	
	def delqtdb(self):
		if self.qtdb: self.qtdb.close()


	
	################### textualization stuff ################# TODO: check whether still useful!
	################################################

	def listTextualizations(self):
		"""
		showing the existing textualizations in the database
		"""
		self.textualizations.clear()
		for cf in self.base.getTextualizations(): self.textualizations.addItem(cf)			
	

	#@pyqtSignature("int")
	#@pyqtSlot(int, QObject)
	#@pyqtSlot(int)
	#@pyqtSlot(int, name='index')
	def on_textualizations_currentIndexChanged(self, index):
		"""
		initialization or user switched to another textualization
		"""
		
		#print "on_textualizations_currentIndexChanged"
		if isinstance(index,int) and index<0: return 
		#self.textualization=unicode(self.textualizations.itemText(index))
		#print "index",index,type(index)
		if isinstance(index,str):
			self.textualization=index
			#print 123
		else:
			self.textualization=self.textualizations.itemText(index)
			#print 456
		#print "1153 self.textualization"
		
		# TODO: solve this:
		self.textualization="standard"
	
		self.columnsMenu.clear()
		#self.columnsMenu.setTitle("visible Columns") # doesn't work!!!

		for it in self.base.getColumns(self.textualization): # showing the columns 
			action=QtWidgets.QAction(it, self.columnsMenu)
			action.setCheckable ( True )
			if "_nb" in action.text() or "rowid" in action.text() or action.text()=="time":	action.setChecked( False ) #or action.text()=="time"
			else:						action.setChecked( True )
			self.columnsMenu.addAction(action )
			action.changed.connect(self.columnSelectionChanged)
		
		self.columnsMenu.addAction(self.invertAction )
		#self.columnsMenu.addAction(self.actionShow_all_columns ) # TODO: make this work
		
		self.sql()
		self.cellcontent.clear()
		self.filterConditions=[]
		
		for ff in self.filterframelist:
			self.filterVerticalLayout.removeWidget(ff)
			ff.setParent(None)

		self.filterframelist=[]
		self.delTextualButton.setEnabled(isinstance(index,str) or index>0)
		
		#print 4566456,self.textualization
		
	
	@pyqtSlot()
	def on_delTextualButton_clicked(self):
		"""
		the currently selected textualization is deleted
		"""
		if debug: print("on_delTextualButton_clicked", self.textualizations.currentText())
		self.base.deleteTextualization(str(self.textualizations.currentText()))
		self.listTextualizations()
	
	
	
	
	
	
	
	
	
	
	
	
	
	################### filter #####################
	################################################
	def addEmptyFilter(self):
		"""
		adds a new selection (a selection of columns for a view)
		"""
		if debug: print("addEmptyFilter")
		
		self.tabWidget.setCurrentIndex(2) # show the filter table
		self.filterTableWidget.setEnabled(True)
		
		row=self.filterTableWidget.rowCount()
#		print "addEmptyFilter", row
		self.filterTableWidget.setRowCount(row+1)
		
		
		columnBox=QtWidgets.QComboBox( self.filterTableWidget )
		columnBox.currentIndexChanged.connect(functools.partial(self.filterColumnChanged, row, 0))
		for colname in self.allCollumns:
			columnBox.addItem(colname)
		self.filterTableWidget.setCellWidget ( row, 0, columnBox );
		self.filterTableWidget.setItem(row, 1, QTableWidgetItem(str(row)))
		self.filterTableWidget.setItem(row, 2, QTableWidgetItem(""))
		self.filterTableWidget.setItem(row, 3, QTableWidgetItem(QIcon(":images/images/delete.png"),  ""))
	
		
	def filterColumnChanged(self, i, j, comboi):
				
		if j==0: # column selection has changed
#			try:
			equalBox= self.filterTableWidget.cellWidget(i, 1)
#			
			equalBox=QtWidgets.QComboBox( self.filterTableWidget )
			#col=
			ty=self.base.getColType(self.allCollumns[comboi])
			for choice in self.ty2choices.get(ty):
				equalBox.addItem(choice)
			self.filterTableWidget.setCellWidget ( i, 1, equalBox );
			equalBox.currentIndexChanged.connect(functools.partial(self.filterColumnChanged, i, 1))
			self.filterTableWidget.resizeColumnToContents(1) # resize the equal column
		if j==1: # equal selection has changed
			self.updateFilterConditions()
			self.filterTableWidget.resizeColumnToContents(1) # resize the equal column


	def filterTableCellChanged(self, i, j):
		"""
		update filter condition column
		connected to the filter table widget
		"""
#		print "filterTableCellChanged", i, j
		if not self.textualization: 
			#print "self.textualization",self.textualization,"empty"
			return
		#print "self.textualization",self.textualization
		if j==2:
#			print 'apply'
			if i==self.filterTableWidget.rowCount()-1: 
				## if it's the last filter: check if it's empty, if not add a new empty filter

				try:t=str(self.filterTableWidget.item(i, 2).text()).strip()
				except:t=""
				if t:
					self.addEmptyFilter()
					
			self.updateFilterConditions()
					
	
	def filterTableCellClicked(self, i, j):
		"""
		remove filter
		connected to the filter table widget
		"""
		
		if j==3 and self.filterTableWidget.rowCount()>1:
			self.filterTableWidget.removeRow(i)
			self.filterTableCellChanged(0, 2)
			for ii in range(i+1):
				self.filterTableWidget.cellWidget(ii, 0).currentIndexChanged.connect(functools.partial(self.filterColumnChanged, ii, 0))
				self.filterTableWidget.cellWidget(ii, 1).currentIndexChanged.connect(functools.partial(self.filterColumnChanged, ii, 1))
			
			
	def updateFilterConditions(self):
		"""
		update the filter conditions
		"""
#		print "update the filter conditions"
		if self.columnUpdate:return
		#print self.filterTableWidget.rowCount(),self.filterTableWidget.columnCount()
		filters=[]  # the conditions
		for i in range(self.filterTableWidget.rowCount()):
			item=self.filterTableWidget.item(i, 2)
			if item and self.filterTableWidget.cellWidget(i, 1) : #added and self.filterTableWidget.cellWidget(i, 1) for qt5
				t=str(item.text()).strip().replace("'","''") # duplicating single quotes
				#print "t", t, self.filterTableWidget.cellWidget(i, 1), self.filterTableWidget.columnCount()
				#print 54564,self.filterTableWidget.item(i, 0),self.filterTableWidget.item(i, 1),self.filterTableWidget.item(i, 2)
				eq=self.filterTableWidget.cellWidget(i, 1).currentText().strip()
				if self.filterTableWidget.cellWidget(i, 0): col=self.filterTableWidget.cellWidget(i, 0).currentText().strip()
				else: col=self.filterTableWidget.item(i, 0).text()
				#print self.filterTableWidget.cellWidget(i, 0), self.filterTableWidget.item(i, 0), self.filterTableWidget.item(i, 0).text()
				#col=self.filterTableWidget.cellWidget(i, 0).currentText().strip()
				if t:
#					print "col", col, "eq", eq
					if eq in ["=","≤", "≥", "≠"]: 
						filters+=[col+" "+self.nbchoice2sym[eq]+" "+t]
					elif eq=="match whole word":
						filters+=[col+" like '% "+t+" %' "]
#						TODO: the following is not working in sqlite!!!
#						filters+=["'#'"+col+'#' like '%[^a-z0-9]'+t+'[^a-z0-9]%'"]
					elif eq=="contains the word":
						filters+=[col+" like '%"+t+"%' "]
					elif eq=="before":
						filters+=[col+" <= "+t] # TODO: do the time thing right
					elif eq=="after":
						filters+=[col+" >= "+t]
					# TODO: add "match regex"
				else:
					if eq=="equals":
						filters+=[col+" = '"+t+"' "]
				
		self.rowconditions=" and ".join(filters)	
		if debug: print("updateFilterConditions: rowconditions",self.rowconditions,"filters:",filters,"self.textualization",self.textualization)
		
		self.nbFilteredRows=self.base.nbFilteredRows(self.textualization, self.rowconditions)
		self.statusbar.showMessage("Currently showing {nr} page{s}.".format(nr=self.nbFilteredRows,s=('' if self.nbFilteredRows == 1 else 's')))
		
		self.qtdb.open()
		self.model.setFilter(self.rowconditions)
		for i, action in enumerate(self.columnsMenu.actions()):
			self.tableView.setColumnHidden(i, not action.isChecked())
		self.model.select()
		self.tableView.setModel(self.model)
		self.tableView.show()	
		self.updatereductions()
		
	def updatereductions(self):
		"""
		enables and disables reduction actions in the edit menu
		
		"""
		self.actionKeep_only_current_rows.setEnabled(self.rowconditions!="")
		self.actionRemove_current_rows.setEnabled(self.rowconditions!="")
		self.actionKeep_only_current_columns.setEnabled(len(self.columns)<len(self.columnsMenu.actions()))
		self.actionRemove_current_columns.setEnabled(len(self.columns)<len(self.columnsMenu.actions()))
		self.textcolumns=self.base.filterTextColumns(self.columns,["url"])
		#print "columns",self.columns
		#print "textcolumns",self.textcolumns
		self.actionTools.setEnabled(len(self.textcolumns)>0)	


	
	
	################### duplicates #################
	################################################
	
	
	@pyqtSlot(bool)
	def on_duplicateButton_toggled(self, toggle):
		"""
		selection of duplicates
		
		title_nbCharacters
		"""
		#print toggle
		if toggle: # select
		
			self.duplicateButton.setText("Release selection")
			
			#print self.columns
			#print self.rowconditions
			
			sel = "SELECT rowid,url,COUNT(*) c FROM "+self.textualization+" GROUP BY {columns} HAVING c > 1;".format(columns=", ".join(self.columns))
			#print sel
			
				
			duplicates = []
			self.completemodel.setQuery(QSqlQuery(sel))
			for i in range(self.completemodel.rowCount()):
				#print self.getRowFromModel(self.completemodel, len(self.columns)+3, i)
				rowid, url, c = [ str(self.completemodel.datacomplete(self.completemodel.index(i,j))) for j in range(3)  ] # .toString()
				duplicates += [ (rowid, url) ]

			#print duplicates	
			
			goodrows=[]
			for (rowid, url) in duplicates:
				sell = "SELECT  rowid,url FROM "+self.textualization+" WHERE  "+" and ".join([col+" = (SELECT "+col+" FROM "+self.textualization+" WHERE rowid= "+rowid+")" for col in self.columns])+";"
				#print sell
				self.completemodel.setQuery(QSqlQuery(sell))
				group=[]
				for i in range(self.completemodel.rowCount()):
					r, u = [ str(self.completemodel.datacomplete(self.completemodel.index(i,j))) for j in range(2)  ] # .toString()
					#print r, u
					group+=[(r,u)]
				dupMode=str(self.duplicateComboBox.currentText())
				#print group
				if dupMode=="all but first": 		goodrows+=sorted(group)[1:]
				elif dupMode=="all but last": 		goodrows+=sorted(group)[:-1]
				elif dupMode=="all but shortest url": 		goodrows+=sorted(group,key=lambda x: len(x[1]))[1:]
				elif dupMode=="all but longest url": 		goodrows+=sorted(group,key=lambda x: len(x[1]))[:-1]
			
			#print goodrows
			if goodrows:
				self.rowconditions = "rowid in ("+",".join((r for r in zip(*goodrows)[0]))+")"
				#print self.rowconditions
			
				self.model.setFilter(self.rowconditions)
				for i, action in enumerate(self.columnsMenu.actions()):
					self.tableView.setColumnHidden(i, not action.isChecked())
				self.infoDuplicates.setText(str(len(duplicates))+" pages have duplicates and "+str(len(goodrows))+" rows can be removed.")
			else:
				self.infoDuplicates.setText("No duplicates found.")
			self.model.select()
			self.tableView.setModel(self.model)
			self.tableView.show()	
			self.updatereductions()
			#self.actionKeep_only_current_rows.setEnabled(True) 
			#self.actionRemove_current_rows.setEnabled(True) 
		
		else: # release selection
			self.duplicateButton.setText("Select")
			self.rowconditions=""
			self.model.setFilter("")
			self.model.select()
			self.tableView.setModel(self.model)
			self.tableView.show()	
			self.updatereductions()
			self.infoDuplicates.setText("")
			#self.actionKeep_only_current_rows.setEnabled(False) 
			#self.actionRemove_current_rows.setEnabled(False) 
	
	################### selections ################# TODO: make it work!
	################################################
	
	#@pyqtSignature("QModelIndex")
	def on_selectionsTableWidget_clicked(self, index):
		"""
		handle clicks in the selection table
		"""
		if index.column()==4: # the 4th column is the delete column
			# remove selection
			self.selectionsTableWidget.removeRow(index.row())
			self.selections.pop(index.row())
		else:
			# choose selection
			self.readjustingSelections=True
#			print self.filterConditions
			sel=self.selections[index.row()]
			self.textualizations.setCurrentIndex(self.textualizations.findText(sel.textualization))
			for i, action in enumerate(self.columnsMenu.actions()):
#				print i,  action,  action.text(),  action.isChecked()
				if action.text() in sel.columns: action.setChecked(True)
				else:action.setChecked(False)
		self.columnsMenu.close()
	
	
	@pyqtSlot() # signal with no arguments
	def on_actionSelection_triggered(self):
		"""
		fixes the current view to a new selection
		"""
		if debug: print("on_actionSelection_triggered")
		selection=Selection(self)
		self.selections+=[selection]
		
		self.tabWidget.setCurrentIndex(5) # show the selections table
		self.selectionsTableWidget.setEnabled(True)
		
		row=self.selectionsTableWidget.rowCount()
		self.selectionsTableWidget.setRowCount(row+1)
		self.selectionsTableWidget.setItem(row, 0, QTableWidgetItem(str(row)))	
		self.selectionsTableWidget.setItem(row, 1, QTableWidgetItem(selection.textualization))
		self.selectionsTableWidget.setItem(row, 2, QTableWidgetItem(" ".join(selection.columns)))
		self.selectionsTableWidget.setItem(row, 3, QTableWidgetItem(selection.condi))
		self.selectionsTableWidget.setItem(row, 4, QTableWidgetItem(QIcon(":images/images/delete.png"),  ""))
		#print selection.condi

	
	
	
	
	################################################### end groWindow
	################################################### end groWindow
	################################################### end groWindow
	################################################### end groWindow
	################################################### end groWindow
	################################################### end groWindow




class Selection():
	def __init__(self, groWindow):
		"""
		Constructor
		"""
		self.name=str(len(groWindow.selections))
		self.textualization=groWindow.textualization
		self.condi=groWindow.condi
		self.filterConditions=groWindow.filterConditions[:]
		
		self.columns=[]
		for i, action in enumerate(groWindow.columnsMenu.actions()):
			if action.isChecked(): self.columns+=[str(action.text())]
#		print self.columns
		
	def __str__(self):
		return self.name+" textualization: "+self.textualization+" - "+" ".join(self.columns)+" - "+self.condi
	def __repr__(self):
		return self.__str__()

		
class   GroSqlTableModel(QSqlTableModel):
	def __init__(self, parent = None, db = QSqlDatabase(),  limit=None):
			QSqlTableModel.__init__(self, parent, db)

	def data(self, index, role = Qt.DisplayRole):
		"""
		function used to populate the table
		"""
		value = QSqlTableModel.data(self, index, role)
		#print value, index, role
		#if (role == Qt.DisplayRole): # pyqt5: and value.isValid()
			##print value.toString()
		if (role == Qt.DisplayRole): # what to give back when we're wanting to fill the qtable:
			col = index.column()	
			
			if (index.model().headerData(col, 1, role) == "time"):  	
				value = QDateTime.fromTime_t(int(value))
			elif (index.model().headerData(col, 1, role) == "url"): 
				pass
			elif len(str(value))>textlen:
				#value=value.toString()[:textlen/2]+"\n ... \n"+value.toString()[-textlen/2:]
				value=value[:int(textlen/2)]+"\n ... \n"+value[-int(textlen/2):]
		return value			
		
	def datacomplete(self, index, role = Qt.DisplayRole):
		value = QSqlTableModel.data(self, index, role)
		#if (value.isValid()):
		if (role == Qt.DisplayRole): # what to give back when we're wanting to fill the qtable:
			col = index.column()	
			if (index.model().headerData(col, 1, role) == "time"):  # .toString ()	
				value = QDateTime.fromTime_t (value ) #.toInt()[0]
		return value
					
	
class LoseFocusFilter(QObject):
	"""
	class added to the comment text area to track lost focus and update the database immediatelly
	"""
	
	def __init__(self, parent=None):
		super(LoseFocusFilter, self).__init__(parent)
		self.ed=parent
	def eventFilter(self, obj, event):
		if event.type() == QEvent.FocusOut:
			
			gw=obj.parent().parent().parent().parent().parent().parent() ######### ugly hack, but what the heck...
			
			if gw.base:
				gw.base.updateComment(str(gw.commentTextEdit.toPlainText()))
			return True
		else:
			return QObject.eventFilter(self, obj, event)


if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	splashpix = QtGui.QPixmap(":images/images/grosplash.png")
	splash = QtWidgets.QSplashScreen(splashpix)
	splash.setMask(splashpix.mask())
	splash.show()
	window = GroMainWindow()
	window.setAttribute(Qt.WA_DeleteOnClose)
	window.show()
	splash.finish(window)
	status=app.exec_()
	if window.base:	window.base.close()
	if window.qtdb:	del window.qtdb
	sys.exit(status)
