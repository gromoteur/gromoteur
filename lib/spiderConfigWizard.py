# -*- coding: utf-8 -*-

"""
Module implementing SpiderConfigWizard.
"""

from PyQt5.QtWidgets import  QWizard
from PyQt5.QtCore import  QThread,  QObject,  QEvent
#from PyQt5 import *, QtWidgets
from PyQt5 import *

import sys, os,  re, webbrowser
#import bingwebsearch
from . import bing
#from . import ngram
from .groSpider import userAgents
#from utils import get_free_space
from . import utils

from .Ui_spiderConfigWizard import Ui_SpiderConfigWizard
from . import groressources_rc

verbose=True
verbose=False

class SpiderConfigWizard(QWizard, Ui_SpiderConfigWizard):
	"""
	Subclass of the Ui_SpiderConfigWizard
	specifies behavior, in particular expert stuff and lose focus stuff
	"""
	
	def __init__(self, parent = None, db="", config="", ng=None):
		"""
		Constructor
		"""
		QWizard.__init__(self, parent)
		self.setupUi(self)
		self.URLgroupBox.setVisible(True)
		self.URLFileGroupBox.setVisible(False)
		self.bingGroupBox.setVisible(False)
		self.ng=ng
		self.db=db
		if db: self.currentDatabase=db.name
		else: self.currentDatabase=""
		self.configName.setText(config)
		
		self.problemBox.hide()
		
		self.selectedBaseGroupBox.setTitle("selected base: "+self.currentDatabase)
		self.coreLabel.setText("This computer has %i cores."% QThread.idealThreadCount())
		
		self.expertButton = self.button(self.CustomButton1)
		self.expertButton.setIcon(QtGui.QIcon(QtGui.QPixmap(":images/images/expert.png")))
		self.expertButton.setToolTip("toggle expert mode")
		self.expertButton.setCheckable(True)
#		self.expertButton.toggle()
		self.expertObjects = ["baseInfoFrame","takePdf","pageIgnoreCase","defaultEncodingFrame", 
							"textLabelMaxSubdomains", "maxSubdomains", 
							"pathGroupBox", 
							"linkRestriction", 
							"spiderTraps",
							"timeout",
							"trytimes",
							"timeoutsec",
							"followRedirects",
							"parallelGroupBox","identityGroupBox",
							"politenessGroupBox","proxyGroupBox",
							"levelFrom","levelTo","levelFromLabel","levelToLabel"
							]
		
		self.expert(self.expertButton.isChecked())
		
		self.diskSizeInfoLabel.setText("of the "+str(utils.get_free_space(os.path.join(os.path.expanduser('~'),"gromoteur","corpora")))+" Mb of free space in the corpus folder")
		for lang in sorted(self.ng.alllangs.values()): self.language.addItem(str(lang))
		for ua in userAgents: self.userAgent.addItem(str(ua))
#		print "*********************************"
		self.checkConfigName()
#		print "============", list(self.findChildren(QtGui.QCheckBox,QtCore.QRegExp(r'\w*')))
		
#		self.specialStringObjectList=[self.searchEngineQuery]
		self.stringObjectList=list(self.findChildren(QtWidgets.QLineEdit))
		self.stringObjectList=[c for c in self.stringObjectList if c.objectName()!="qt_spinbox_lineedit" and not c.isReadOnly()  and c.objectName()!="configName"]
		self.checkObjectList=list(self.findChildren(QtWidgets.QCheckBox))+list(self.findChildren(QtWidgets.QGroupBox))+list(self.findChildren(QtWidgets.QRadioButton))+[self.expertButton]
		self.checkObjectList=[c for c in self.checkObjectList if c.isCheckable()]
		self.valueObjectList=list(self.findChildren(QtWidgets.QSpinBox))
		self.valueObjectList=[c for c in self.valueObjectList if not c.isReadOnly()]
		self.comboObjectList=list(self.findChildren(QtWidgets.QComboBox))
		
		self.nbpages.setText(str(self.db.nbPages))
		self.nbsentences.setText(str(self.db.nbSentences))
		self.nbwords.setText(str(self.db.nbCharacters))
		self.comments.setPlainText(self.db.comments)
		
		if self.db.nbPages==0:
			self.fromdatabase.setEnabled(False)
			self.fromdatabase.setChecked(False)
			self.dataErase.setChecked(True)
		else:
			self.fromdatabase.setEnabled(True)
		self.lff=LoseFocusFilter(self)
		self.downloadURL.installEventFilter(self.lff)
		self.downloadAvoidURL.installEventFilter(self.lff)
		self.pageRestriction.installEventFilter(self.lff)
		self.linkDomain.installEventFilter(self.lff)
		self.linkAvoidURL.installEventFilter(self.lff)
		
		self.downloadURL.wiz=self
		self.downloadAvoidURL.wiz=self
		self.pageRestriction.wiz=self
		self.linkDomain.wiz=self
		self.linkAvoidURL.wiz=self
		self.language.setEnabled(True)
		self.webSearchUrl=None
#		print 
#		self.expert(self.expertButton.isChecked())
#		self.keywordsLabel.linkActivated.connect(self.about)
		
		
	def expert(self,exp):
#		print "xxx", exp
		if exp:	sh = ".show()"
		else: 	sh= ".hide()"
		for o in self.expertObjects:
			try:	eval("self."+o+sh)
			except Exception as e:  
				if verbose : print("strange expert object name:",o,e)	
	
	def checkConfigName(self):
		"""
		called from init and each time the config name is changed
		"""
		configname=str(self.configName.text()).strip()
		self.button(self.FinishButton).setEnabled(configname!="")
		configFile=os.path.join(os.path.expanduser('~'),"gromoteur",".settings",str(configname)+".gro.cfg" )
		if os.path.exists(configFile):
			self.configInfoLabel.setText("Existing configuration will be overwritten.")
		else:
			self.configInfoLabel.setText("")
		
		
	#@pyqtSignature("QString")
	def on_configName_textChanged(self, p0):
		self.checkConfigName()
	
	#@pyqtSignature("QString")
	def on_keywordsLabel_linkActivated(self, link):
		webbrowser.open_new_tab(link)
		
	#@pyqtSignature("")
	@QtCore.pyqtSlot() # signal with no arguments
	def on_searchEngineTryButton_clicked(self):			
		print("\n\n***************")
		keywords=str(self.searchEngineQuery.text())
		if not keywords.strip(): 
			self.searchEngineTryButton.setChecked(False)
			return
#		print unicode(self.searchEngineAppId.text()),  keywords.encode("utf-8")
		if self.location.currentIndex() == 0:	loca = "automatic location detection"
		else:					loca=str(self.location.currentText())
		#links, total, self.webSearchUrl = bing.search( keywords.encode("utf-8"), unicode(self.searchEngineAppId.text()),loca   )
		try:
			links, total, self.webSearchUrl = bing.search( keywords.encode("utf-8"), str(self.searchEngineAppId.text()),loca   )
		#except:
		except Exception as e:
			#print e, type(e), unicode(e)
			message = QtWidgets.QMessageBox(self)
			message.setText("<b>Can't connect to Bing!</b>")
			#message.setInformativeText("Is your internet connection working? Can you reach Bing in a browser?")
			message.setInformativeText(str(e))
			message.setIcon(QtWidgets.QMessageBox.Warning)
			message.setStandardButtons(QtWidgets.QMessageBox.Ok)
			result=message.exec_()
			self.searchEngineNumberResultsSpin.setSpecialValueText("error")
			self.searchEngineNumberResultsSpin.setValue(0)
			return
			
			
		#if links=="error" :
				
		#else:
				#self.searchEngineNumberResultsSpin.setSpecialValueText("No results")
		self.searchEngineNumberResultsSpin.setValue(total)
		self.searchEngineTryButton.setChecked(False)
		
	
	#@pyqtSignature("")
	@QtCore.pyqtSlot() # signal with no arguments
	def on_bingfirefoxButton_clicked(self):
		if self.webSearchUrl:
			webbrowser.open_new_tab(self.webSearchUrl)
		else:
			url='http://bing.com/search?q='
			url+=str(self.searchEngineQuery.text())
			url = url.replace('"',"%22")
			if verbose:	print(url)
			webbrowser.open_new_tab(url)
		
	#@pyqtSignature("bool")
	@QtCore.pyqtSlot(bool)
	def on___qt__passive_wizardbutton6_clicked(self, checked):
		"""
		expert.Button
		"""
		self.expert(self.expertButton.isChecked())
	
	#@pyqtSignature("")
	@QtCore.pyqtSlot() # signal with no arguments
	def on_urlFileButton_clicked(self):
		print(QtCore.QDir.homePath())
		filename=QtWidgets.QFileDialog.getOpenFileName (self, "File that contains the URLs",QtCore.QDir.homePath(),"All files (*.*)")[0]
		if filename:
			self.startUrlFile.setText(os.path.realpath(str(filename)) )
	
	
	
class LoseFocusFilter(QObject):
	"""
	class added to track lost focus and update the database immediatelly
	"""
	
	def __init__(self, parent=None):
		super(LoseFocusFilter, self).__init__(parent)
		self.ed=parent
	def eventFilter(self, obj, event):
		if event.type() == QEvent.FocusOut:
			try:
				re.compile(str(obj.text()).strip())
				obj.wiz.problemBox.hide()
				obj.setStyleSheet("")
				obj.wiz.button(QWizard.NextButton).setEnabled(True)
			except Exception as e:
				obj.wiz.infoBar.setText("Regular expression incorrect: "+str(e))
				obj.wiz.problemBox.show()
				obj.setStyleSheet("border: 2px solid rgb(223, 76, 39);")
				obj.wiz.button(QWizard.NextButton).setEnabled(False)
#				
			return True
		else:
			return QObject.eventFilter(self, obj, event)	

if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	window = SpiderConfigWizard()
	window.show()
	sys.exit(app.exec_())
	

