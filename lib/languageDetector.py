# -*- coding: utf-8 -*-

"""
Module implementing languageDialog.
"""

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QDialog, QTableWidgetItem

from .Ui_languageDetector import Ui_languageDialog


class languageDialog(QDialog, Ui_languageDialog):
	"""
	Class documentation goes here.
	"""
	def __init__(self, parent=None):
		"""
		Constructor
		
		@param parent reference to the parent widget
		@type QWidget
		"""
		super(languageDialog, self).__init__(parent)
		self.setupUi(self)
		self.parent = parent
		self.tableWidget.setSortingEnabled(True)	
		
		self.tableWidget.setColumnCount(3)
		self.ngramtableWidget.setColumnCount(2)
		
		self.tableWidget.horizontalHeader().setStretchLastSection(True)
		self.ngramtableWidget.horizontalHeader().setStretchLastSection(True)
		self.recomputengrams()
		self.reguess()
		
		self.newcodes=[]
	
	def makengramdic(self,text):
		textlen=len(text)
		if textlen==0: return {}
		text = self.parent.ng.replare.sub("_"," "+text+" ".lower())
		addValue = int((1.0/textlen)*self.parent.ng.freqmulti)			
		sordico = self.parent.ng.ngramList(text,self.parent.ng.n,addValue)[:self.parent.ng.ngramnum]
		return {g:f for f,g in sordico}
		
		
		
	def recomputengrams(self):
		text = str(self.trainTextEdit.toPlainText())
		ngramdic = self.makengramdic(text)
		self.ngramtableWidget.clear()
		self.ngramtableWidget.setHorizontalHeaderLabels([self.tr("ngram"), self.tr("freq * "+str(self.parent.ng.freqmulti))])
		self.ngramtableWidget.setRowCount(len(ngramdic))
		for i,ng in enumerate(sorted(ngramdic,key=ngramdic.get,reverse=True)):

		
		
		#for i, (score, code) in enumerate(hnm):
			scoreitem=QTableWidgetItem()
			scoreitem.setData(Qt.EditRole, ngramdic[ng])
			scoreitem.setTextAlignment(Qt.AlignRight)
			self.ngramtableWidget.setItem(i, 1, scoreitem)
			
			codeitem=QTableWidgetItem(ng)
			self.ngramtableWidget.setItem(i, 0, codeitem)
			
		
	def reguess(self):
		hnm = self.parent.ng.guessLanguageList(str(self.testTextEdit.toPlainText()))
		#print(hnm)
		self.tableWidget.clear()
		self.tableWidget.setHorizontalHeaderLabels([self.tr("score"), self.tr("code"), self.tr("name")])
		self.tableWidget.setRowCount(len(hnm))
		for i, (score, code) in enumerate(hnm):
			scoreitem=QTableWidgetItem()
			scoreitem.setData(Qt.EditRole, score)
			scoreitem.setTextAlignment(Qt.AlignRight)
			self.tableWidget.setItem(i, 0, scoreitem)
			
			codeitem=QTableWidgetItem(code)
			self.tableWidget.setItem(i, 1, codeitem)
			
			nameitem=QTableWidgetItem(self.parent.ng.alllangs.get(code,"no name found"))
			self.tableWidget.setItem(i, 2, nameitem)
	
	@pyqtSlot()
	def on_testTextEdit_textChanged(self):
		"""
		Slot documentation goes here.
		"""
		self.reguess()
		
	@pyqtSlot()
	def on_trainTextEdit_textChanged(self):
		"""
		Slot documentation goes here.
		"""
		self.recomputengrams()
		
		
		
		
	
	@pyqtSlot()
	def on_learnButton_clicked(self):
		"""
		Slot documentation goes here.
		"""
		text = str(self.trainTextEdit.toPlainText())
		code = str(self.newlanguagecodelineEdit.text())
		name = str(self.newlanguagenamelineEdit.text())
		
		
		
		self.parent.ng.ngrams[code]=self.makengramdic(text)
		self.parent.ng.alllangs[code]=name
		self.reguess()
		if code not in self.newcodes: self.newcodes+=[code]
		
		
	
	@pyqtSlot()
	def on_buttonBox_rejected(self):
		"""
		Slot documentation goes here.
		"""
		from . import ngram
		self.parent.ng = ngram.Ngram()

	
	@pyqtSlot()
	def on_buttonBox_accepted(self):
		"""
		Slot documentation goes here.
		"""
		print("added the following codes",self.newcodes)
