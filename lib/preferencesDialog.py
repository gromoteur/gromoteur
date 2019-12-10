# -*- coding: utf-8 -*-

"""
Module implementing PreferencesDialog.
"""

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import  QDialog, QColorDialog
#from PyQt5.QtCore import pyqtSignature

from .Ui_preferencesDialog import Ui_PreferencesDialog
import re
from . import groressources_rc

class PreferencesDialog(QDialog, Ui_PreferencesDialog):
	"""
	Class documentation goes here.
	"""
	def __init__(self, parent = None):
		"""
		Constructor
		"""
		QDialog.__init__(self, parent)
		
		self.parent=parent
		self.config=parent.config["configuration"]
		
		
		self.setupUi(self)
		self.groBox.show()
		self.nexicoBox.hide()
		
		self.specColor.setStyleSheet("background-color: rgb"+str(QColor(int(self.config["specColor"])).getRgb())+";")
		self.freqColor.setStyleSheet("background-color: rgb"+str(QColor(int(self.config["freqColor"])).getRgb())+";")
		
		self.newLineTags.setPlainText(self.config["newLineTags"].replace("|","\n"))
		self.nbRobotsInMemory.setValue(int(self.config["nbRobotsInMemory"]))
		self.nbBestKids.setValue(int(self.config["nbBestKids"]))
		
		self.nbAccessDomInMemory.setValue(int(self.config["nbAccessDomInMemory"]))
		self.nbPageMaxCounterInMemory.setValue(int(self.config["nbPageMaxCounterInMemory"]))
		self.cutMessages.setValue(int(self.config["cutMessages"]))
		self.threshold.setValue(int(self.config["threshold"]))
		
		self.wordlimit.setText(self.config["wordlimit"])
		self.sentenceSplit.setText(self.config["sentenceSplit"])
		
		self.lower.setChecked(self.config["lower"]=="yes")
		
		self.colcompComboBox.setCurrentIndex(self.colcompComboBox.findText(self.config["colcomp"]))
		
		
	
	def makeColor(self,specOrFreq):
		col=QColor()
		col.setRgba(int(self.config[specOrFreq]))
		col=QColorDialog.getColor(col,self,"Choose color of "+specOrFreq+" in the graph",QColorDialog.ShowAlphaChannel)
		self.config[specOrFreq]=str(col.rgba())
		return col
		
	#@pyqtSignature("")
	def on_specColor_clicked(self):
		"""
		Slot documentation goes here.
		"""
		self.specColor.setStyleSheet("background-color: rgb"+str(self.makeColor("specColor").getRgb())+";")
			
	
	#@pyqtSignature("")
	def on_freqColor_clicked(self):
		"""
		Slot documentation goes here.
		"""
		self.freqColor.setStyleSheet("background-color: rgb"+str(self.makeColor("freqColor").getRgb())+";")
		
	

	#@pyqtSignature("")
	def on_listWidget_itemSelectionChanged(self):
		"""
		Slot documentation goes here.
		"""

		if self.listWidget.currentRow():
			self.groBox.hide()
			self.nexicoBox.show()
		else:
			self.groBox.show()
			self.nexicoBox.hide()
		# TODO: not implemented yet
		#        raise NotImplementedError
	
	#@pyqtSignature("")
	def on_buttonBox_accepted(self):
		"""
		Slot documentation goes here.
		"""
		
		
		nl=re.compile("\s*\n\s*")
		
		self.config["newLineTags"]= "|".join(nl.split(str(self.newLineTags.toPlainText())))
		
		# int values from spins
		self.config["nbRobotsInMemory"]=self.nbRobotsInMemory.value()
		self.config["nbAccessDomInMemory"]=self.nbAccessDomInMemory.value()
		self.config["nbPageMaxCounterInMemory"]=self.nbPageMaxCounterInMemory.value()
		self.config["cutMessages"]=self.cutMessages.value()
		self.config["threshold"]=self.threshold.value()
		# txt values from lineedits
		self.config["wordlimit"]=str(self.wordlimit.text())
		self.config["sentenceSplit"]=str(self.sentenceSplit.text())
		
		self.config["lower"]="yes" if self.lower.isChecked() else "no"
		#self.lower.setChecked(self.config["lower"]=="yes")
		self.config["nbBestKids"]=str(self.nbBestKids.value())
		self.config["colcomp"]=self.colcompComboBox.currentText()
