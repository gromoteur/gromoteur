#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal
from PyQt5 import QtGui, QtWidgets

#, QtCore
from PyQt5.QtCore import Qt

from .nexicoMain import Nexico
from .nexicoBase import NexicoBase


def startNexico(groWindow):
	
	if groWindow.rowconditions: 		wherecondi=" WHERE "+groWindow.rowconditions
	else: wherecondi=""
	groWindow.selectstatement="SELECT rowid,url,"+", ".join(groWindow.columns)+" FROM "+groWindow.textualization+wherecondi+" ;"
	if groWindow.rowconditions: 		wherecondi=" WHERE "+groWindow.rowconditions+" and rowid=?"
	else:				wherecondi=" WHERE rowid=?"
	groWindow.rowidselectstatement="SELECT "+", ".join(groWindow.columns)+" FROM "+groWindow.textualization+wherecondi+";"
	
	selectionName="standard: "+(groWindow.rowconditions or "")
	
	signal.signal(signal.SIGINT, signal.SIG_DFL)
	splashpix = QtGui.QPixmap(":images/images/NexicoSplash.png")
	splash = QtWidgets.QSplashScreen(splashpix)
	splash.setMask(splashpix.mask());
	
	splash.show()
	
	nexicoBase=NexicoBase(groWindow)	
	nexico = Nexico(splash, nexicoBase, groWindow.config, selectionName)
	
	nexico.setAttribute(Qt.WA_DeleteOnClose)
	nexico.show()	
	#nexico.showMaximized()
	return nexico



