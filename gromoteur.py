#!/usr/bin/python3  
# -*- coding: utf-8 -*-

"""
Module implementing Gromoteur.
"""
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import  QMainWindow
from PyQt5.QtWidgets import  QMessageBox, QApplication
from PyQt5.QtCore import  Qt,  QLocale,  QTranslator,  QLibraryInfo
from PyQt5 import QtGui, QtWidgets

import sys, signal, os, shutil
from sys import platform
from lib import groWindow,  groressources_rc

from PyQt5.QtGui import *
import importlib
#from PyQt4.QtCore import *

signal.signal(signal.SIGINT, signal.SIG_DFL)

class Gromoteur(groWindow.GroMainWindow):
	"""
	Main window wrapper
	"""
	def __init__(self, parent = None):
		"""
		Constructor
		"""
		groWindow.GroMainWindow.__init__(self,None)



if __name__ == "__main__":

	importlib.reload(sys)
	#sys.setdefaultencoding("utf-8")
	app = QtWidgets.QApplication(sys.argv)
	#print app.style().objectName()
	
	try:
		os.environ["QT_XCB_GL_INTEGRATION"] = "xcb_egl" # weird error, solution taken from here: https://bugs.launchpad.net/ubuntu/+source/qtbase-opensource-src/+bug/1761708
	except:
		print("QT_XCB_GL_INTEGRATION failed")
	
	if platform.startswith("win"):app.setStyle(QtWidgets.QStyleFactory.create("Cleanlooks"))
	splashpix = QtGui.QPixmap(":images/images/grosplash.png")
	splash = QtWidgets.QSplashScreen(splashpix)
	splash.setMask(splashpix.mask());
	splash.show()


	#QLocale.setDefault(QLocale(QLocale.French, QLocale.France)) # #TODO: comment to get actual locale
	#QLocale.setDefault(QLocale(QLocale.Chinese, QLocale.China)) # #TODO: comment to get actual locale
	#QLocale.setDefault(QLocale(QLocale.German, QLocale.Germany)) # #TODO: comment to get actual locale
	locale = QLocale().name()	
	#print locale
	#qsdf
	qttranslator = QTranslator()
	qttranslator.load('qt_%s' % locale, QLibraryInfo.location(QLibraryInfo.TranslationsPath)), QLibraryInfo.location(QLibraryInfo.TranslationsPath)
	app.installTranslator(qttranslator)
	
	mytranslator = QTranslator()
	mytranslator.load(os.path.join('lib','translations','trans.%s.qm' % locale))
	app.installTranslator(mytranslator)
	
	#	locale = QLocale.system().name()
	#	print qttranslator.load('qt_fr.qm')
	#print "zzzzzzzzzzzzz", locale,  QLibraryInfo.location(QLibraryInfo.TranslationsPath)
	#locale="fr_FR"
	#	print translator.load('qt_%s' % locale,    QLibraryInfo.location(QLibraryInfo.TranslationsPath))
	#	print "^^", translator.load("trans.fr.qm")
	
	# check for gromoteur folders	
	grohome = os.path.join(os.path.expanduser('~'),"gromoteur")
	if not os.path.isdir(grohome): 		os.makedirs(grohome)
	corporafolder=os.path.join(grohome,"corpora")
	if not os.path.isdir(corporafolder): 	os.makedirs(corporafolder)
	settingsfolder=os.path.join(grohome,".settings")
	if not os.path.isdir(settingsfolder): 	os.makedirs(settingsfolder)
	grocfg = os.path.join(settingsfolder,"gro.cfg")
	if not os.path.isfile(grocfg):		shutil.copy(os.path.join("lib","gro.cfg"), settingsfolder)
	
	
	window = Gromoteur()
	window.setAttribute(Qt.WA_DeleteOnClose)
	if app.desktop().screenGeometry().height()<1000:window.showMaximized()	
	else: window.show()
	splash.finish(window)
	
	
	status=app.exec_()
	
	
	
	window.delqtdb()
	# base maybe None when no corpus item is selected
	if hasattr(window, 'base') and window.base and window.base.isAlive():
		window.base.close()
	app.exit()
	sys.exit(status)
	

