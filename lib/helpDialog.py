# -*- coding: utf-8 -*-

"""
Module implementing helpDialog.
"""

from PyQt5.QtWidgets import  QDialog


from PyQt5 import QtCore

from .Ui_helpDialog import Ui_helpDialog
import os, codecs, webbrowser

class helpDialog(QDialog, Ui_helpDialog):
	"""
	Class documentation goes here.
	"""
	def __init__(self, parent = None):
		"""
		Constructor
		"""
		QDialog.__init__(self, parent)
		self.setupUi(self)
		try:
			self.helpWebView.load(QtCore.QUrl("http://gromoteur.ilpga.fr"))
			self.about.setSource(QtCore.QUrl(os.path.join("lib","resources","about.html")))
			self.gnulicence.setPlainText (codecs.open(os.path.join("lib","resources","gpl.txt")).read())
		except Exception as e: print("help text files not present",e)
		
	
	def link_clicked(self,link):
		ulink=str(link.toString())
		if ulink.endswith(".pdf"):webbrowser.open_new(ulink) # that way the pdf files are left for the default webbrowser do deal with. firefox and chrome can directly show them
		else: self.helpWebView.load(link)
