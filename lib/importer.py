# -*- coding: utf-8 -*-

import sys

from PyQt5 import QtCore 
#import SIGNAL
#,pyqtSignature
from PyQt5.QtWidgets import  QDialog

from .Ui_importer import Ui_Importer
from .groSpider import GroOpener
from .htmlPage import Page
from . import groressources_rc


class Importer(QDialog, Ui_Importer):
	"""
	used for folder import from groWindow (parent)
	"""
	progressChanged = QtCore.pyqtSignal(int)
	progressFinished = QtCore.pyqtSignal()
	def __init__(self, parent,  filelist):
		
		"""
		Constructor
		"""
		QDialog.__init__(self, parent)
		self.parent=parent
		self.filelist=filelist
		self.setupUi(self)
		self.sentenceSplit=parent.sentenceSplit
		
		
	#@pyqtSignature("")
	def on_buttonBox_accepted(self):
		"""
		ok is clicked, we import.
		"""	
		self.parent.pb.show()
		self.parent.statusbar.showMessage("Importing...")
		self.parent.pb.setValue(5)
		self.addFileListToDatabase(self.filelist,  GroOpener())
		self.progressFinished.emit()
		self.parent.qtdb.open()
		self.parent.on_corpuslistWidget_itemSelectionChanged()
	
	def addFileListToDatabase(self,  filelist,  groopener):
		for i, fp in enumerate(filelist):
			open(fp).read()
			if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):	url="file:///"+fp
			elif sys.platform.startswith("win"):						url="file:/"+fp
			page = Page(url,groopener, self.sentenceSplit) # ###### here it happens ######
			self.parent.base.enterSource( page,  -1,   True)
			self.progressChanged.emit(100.0*(i+1)/len(filelist))
