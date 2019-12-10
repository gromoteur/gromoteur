# -*- coding: utf-8 -*-

"""
Module implementing Dialog.
"""

from PyQt5.QtWidgets import  QDialog
from PyQt5.QtCore import  QObject,   QDir,  QEventLoop, pyqtSlot
from PyQt5 import QtGui, QtWidgets

import sys, os
from datetime import date

from .Ui_goDialog import Ui_GoDialog
from .spiderConfigWizard import  SpiderConfigWizard
from .groSpider import GroSpider
from . import spiderConfiguration
from . import groressources_rc


verbose=False
#verbose=True

newconfig="New spider configuration"

class GoDialog(QDialog, Ui_GoDialog):
	"""
	The spider dialog: configure and spider
	"""
	def __init__(self, parent = None,  base=None):
		"""
		Constructor
		"""
		QDialog.__init__(self, parent)
		self.groWindow=parent
		self.setupUi(self)
		
		self.messages.setStyleSheet("""
			QTextEdit { 
			background-color: rgb(255, 255, 255);
			background-image : url(:/images/images/quartercogtrans.png);
			background-position:bottom right;
			background-attachment: fixed;
			background-repeat:no-repeat; }
			""")
		
		self.base=base
		try:self.DBLabel.setText("Database: "+base.name) # TODO: check whether necessary for windows! #.decode("utf-8")
		except:self.DBLabel.setText("Database: "+base.name)
		self.spiderConfigurationsComboBox = QtWidgets.QComboBox(self)
		self.spiderConfigurationsComboBox.setObjectName("spiderConfigurationsComboBox")
		self.spiderConfigurationsComboBox.setMaxVisibleItems(22)
		self.spiderConfigurationsComboBox.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
		self.spiderConfigurationsComboBox.setMinimumContentsLength(2)
		font = QtGui.QFont()
		font.setPointSize(8)
		font.setBold(False)
		self.spiderConfigurationsComboBox.setFont(font)
		self.spiderConfigurationsComboBox.setObjectName("spiderConfigurationsComboBox")
		self.configicon = QtGui.QIcon()
		self.configicon.addPixmap(QtGui.QPixmap(":images/images/configure.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.settingsLayout.insertWidget(0, self.spiderConfigurationsComboBox)
		self.listConfigs() 
		
		self.wiz=None
		self.spider=None
		self.running=False
		self.configName=""
		
		############
		self.spiderConfigurationsComboBox.currentIndexChanged['QString'].connect(self.on_spiderConfigurationsComboBox_currentIndexChanged)
		try :  self.spiderConfigurationsComboBox.setCurrentIndex(self.spiderConfigurationsComboBox.findText(self.groWindow.config["configuration"].get("lastSelectedSpiderConfig")))
		except: 
			if verbose: print("can't read the last selected spider config")
			
                
                
                

			
	def listConfigs(self, item=None):
		self.spiderConfigurationsComboBox.clear()
		self.spiderConfigurationsComboBox.addItem(self.configicon, newconfig)
		
		configList = [os.path.normcase(str(f))[:-8] for f in os.listdir( os.path.join(os.path.expanduser('~'), "gromoteur", ".settings")) if f.endswith(".gro.cfg")]
		for cf in configList: self.spiderConfigurationsComboBox.addItem(cf)
		if item:
			self.spiderConfigurationsComboBox.setCurrentIndex(self.spiderConfigurationsComboBox.findText(item))
		else:
			self.spiderConfigurationsComboBox.setCurrentIndex(self.spiderConfigurationsComboBox.findText(newconfig))
			self.spiderConfigurationsComboBox.setCurrentIndex(0)

	#@pyqtSignature("")
	@pyqtSlot() # signal with no arguments
	def on_configDelButton_clicked(self):
		"""
		delete configuration
		"""
		self.configName = str(self.spiderConfigurationsComboBox.currentText())
		
		message = QtWidgets.QMessageBox(self)
		message.setText("<b>Deleting configuration <i>"+self.configName+"</i>.</b>")
		message.setInformativeText("Completely erase this configuration file?")
		message.setIcon(QtWidgets.QMessageBox.Warning)
		message.setStandardButtons(QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Yes)
		result=message.exec_()
		if  result== message.Yes: 
			try:
				configFile=os.path.join(os.path.expanduser('~'),"gromoteur",".settings",self.configName+".gro.cfg" )
				os.remove(configFile)
			except:
				print("can't remove the config file",self.configName+".gro.cfg")
		self.listConfigs()
			
	#@pyqtSignature("QString")
	def on_spiderConfigurationsComboBox_currentIndexChanged(self, itemName):
		"""
		different configuration selected
		"""
		self.goButton.setEnabled(itemName!=newconfig)
		self.configDelButton.setEnabled(itemName!=newconfig)
		self.wiz=SpiderConfigWizard(db=self.base,  config=itemName, ng=self.groWindow.ng)
		if itemName=="": 		self.spiderConfigurationsComboBox.setCurrentIndex(0)
		elif itemName!=newconfig:	spiderConfiguration.fillWiz(itemName, self.wiz)
		
		
		self.wiz.expert(self.wiz.expertButton.isChecked())
		
		self.configName=str(itemName)
		self.groWindow.config["configuration"]["lastSelectedSpiderConfig"]=itemName
		self.groWindow.config.write()	
		
			
	
	#@pyqtSignature("")
	@pyqtSlot() # signal with no arguments
	def on_setupButton_clicked(self):
		"""
		Configures and starts the spider wizard
		"""
		self.configName = str(self.spiderConfigurationsComboBox.currentText())
		if self.configName==newconfig:
			self.configName=QDir.home().dirName()+"-Configuration-"+str(date.today())
			self.wiz=SpiderConfigWizard(db=self.base,  config=self.configName, ng=self.groWindow.ng)
			spiderConfiguration.fillWiz("", self.wiz,  True)
		if self.wiz.exec_():
			spiderConfiguration.saveWiz(self.wiz)
			self.listConfigs(str(self.wiz.configName.text()))
	
	#@pyqtSignature("")
	@pyqtSlot() # signal with no arguments
	def on_goButton_clicked(self):
		"""
		Go (or Stop) button is clicked
		"""
		if self.running:
			if verbose: print("clicked for stopping")
			self.messages.append("\nStopping...")
			self.goButton.setText("Stopping...")					
			self.goButton.setEnabled(False)
			self.pauseButton.setEnabled(False)
			QEventLoop().processEvents()
			self.spider.theEnd()
			self.spider.running=False
			
		else:
			if verbose: print("starting ", self.wiz.nbThreads.value(), "threads")
			self.goButton.setText("Stop")
			self.goButton.setIcon(QtGui.QIcon(":images/images/gromoteurstop.png"))
			self.buttonBox.setEnabled(False)
			self.messages.setText("we are getting going...\n")
			if hasattr(self, 'spider') and hasattr(self.spider, 'base'):
				self.spider.base.close()
				del self.spider
			self.spider=GroSpider(self)
			self.running=True
			self.setupButton.setEnabled(not self.running)
			self.configDelButton.setEnabled(not self.running)
			self.pauseButton.setEnabled(self.running)
			self.spiderConfigurationsComboBox.setEnabled(not self.running)
			
	def end(self):
		"""
		finish downloading 
		"""
		if verbose: print("running => stopping")
			
		self.running=False
		self.goButton.setIcon(QtGui.QIcon(":images/images/gromoteurgo.png"))
		self.goButton.setText("")
		self.goButton.setChecked(False)
		self.pauseButton.setChecked(False)
		self.statusbar.setText("all done!")
		
		self.goButton.setEnabled(True)
		self.buttonBox.setEnabled(True)
		self.setupButton.setEnabled(not self.running)
		self.configDelButton.setEnabled(not self.running)
		self.pauseButton.setEnabled(self.running)
		self.spiderConfigurationsComboBox.setEnabled(not self.running)
		
		QEventLoop().processEvents()
		self.messages.append("\nWe finished. - All done...\n")
		
	def scrollToBottom(self,textedit):
		curs = textedit.textCursor()
		curs.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
		textedit.setTextCursor(curs)
		textedit.ensureCursorVisible ()
	

	#@pyqtSignature("")
	@pyqtSlot() # signal with no arguments
	def on_pauseButton_clicked(self):
		"""
		pause button is clicked
		"""
		self.spider.paused=self.pauseButton.isChecked()
			
	#@pyqtSignature("")
	@pyqtSlot() # signal with no arguments
	def on_buttonBox_accepted(self):
		"""
		Ok button is clicked
		"""
		if self.spider:
			self.spider.theEnd()
			self.spider.running=False
				
				

if __name__ == "__main__":
	from .groBase import GroBase
	base=GroBase("a")
	app = QtWidgets.QApplication(sys.argv)
	window = GoDialog(None, base)
	window.show()
	sys.exit(app.exec_())
	
