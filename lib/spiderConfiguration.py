# -*- coding: utf-8 -*-

#try:import win32com.client
#except:pass
#from sys import platform
import os
#from Ui_configWidget import Ui_ConfigWidget
from configobj import ConfigObj

verbose=False
#verbose = True

"""
two functions, saveWiz and fillWiz, used for copying all data from and to a spiderConfigWizard
"""


def saveWiz(wiz):
	
	filename=str(os.path.join(os.path.expanduser('~'),"gromoteur",".settings",str(wiz.configName.text())+".gro.cfg" ))

	config = ConfigObj(encoding="UTF-8")
	config.BOM=True
	config["spider configuration"]={}

	for o in wiz.stringObjectList:
		oname=str(o.objectName())
		try:config["spider configuration"][oname] = str(o.text())
		except:
			if verbose: print("problem saving",oname,o)

#	for o in wiz.specialStringObjectList:
#		oname=unicode(o.objectName())
#		try:config["spider configuration"][oname] = ' '+unicode(o.text())+' '
#		except:
#			if verbose: print "problem saving",oname,o

	for o in wiz.checkObjectList:
		oname=str(o.objectName())
		if oname=="__qt__passive_wizardbutton6":oname="expert"
		if o.isChecked(): config["spider configuration"][oname] = "yes"
		else: config["spider configuration"][oname] = "no"
		try:
			if o.isChecked(): config["spider configuration"][oname] = "yes"
			else: config["spider configuration"][oname] = "no"
		except:
			if verbose: 
				print("problem saving",oname,o,  o.isChecked(),  config["spider configuration"][oname])
	for o in wiz.valueObjectList:
		oname=str(o.objectName())
		try: config["spider configuration"][oname] = str(o.value())
		except:
			if verbose: print("problem saving",oname,o)

	for o in wiz.comboObjectList:
		oname=str(o.objectName())
		if oname == "language":
			if o.currentIndex()==0: txt = "any language"
			else: txt = o.currentText()
		else:
			txt = o.currentText()
		try: config["spider configuration"][oname] = str(txt)
		except:
			if verbose: print("problem saving",oname,o)
			
	config.filename=filename
	config.write()
	
	
def fillWiz(configName, wiz,  useDefault=False):

	""" puts all the values from config in the right place"""

	filename=str(os.path.join(os.path.expanduser('~'),"gromoteur",".settings",str(configName)+".gro.cfg" ))
	if os.path.exists(filename) and not useDefault:
		try:
			config = ConfigObj(filename,encoding="UTF-8")
			config.BOM=True
			if verbose : print("read", filename)
		except Exception as e:
			if verbose : print("can't read config file:",filename,e)
	else:
			config = ConfigObj(str("gro.cfg.default"),encoding="UTF-8")
			config.BOM=True
			
	for o in wiz.stringObjectList:
			oname=str(o.objectName())
			try: o.setText(config["spider configuration"][oname])
			except Exception as e:
				if verbose : print("stringObjectList,strange thing in the config file:",oname,e)
				
#	for o in wiz.specialStringObjectList:
#			oname=unicode(o.objectName())
#			try: o.setText(config["spider configuration"][oname].strip())
#			except Exception, e:
#				if verbose : print "comboObjectList,strange thing in the config file:",oname,e
				
	for o in wiz.checkObjectList:
			oname=str(o.objectName())
			if oname=="__qt__passive_wizardbutton6":oname="expert"
			try: 
				o.setChecked(config["spider configuration"][oname]=="yes")
			except Exception as e:
				if verbose : print("checkObjectList,strange thing in the config file:",oname,e)
				
	for o in wiz.valueObjectList:
			oname=str(o.objectName())
			try: 
				try:
					o.setValue(int(config["spider configuration"][oname]))
				except:
					o.setValue(-1)
			except Exception as e:
				if verbose : print("valueObjectList,strange thing in the config file:",oname,e)
				
	for o in wiz.comboObjectList:
			oname=str(o.objectName())
			try:
				if oname == "language" and config["spider configuration"]["language"] == "any language":
					o.setCurrentIndex(0)
				else:
					try: 	o.setCurrentIndex(o.findText(config["spider configuration"][oname]))
					except Exception as e:
						if verbose : print("comboObjectList, strange thing in the config file:",oname,e)
			except:
				print("ooh",o)
	# special:
	if wiz.startWithURL.isChecked() : 	 	wiz.startWithURL.click()
	if wiz.startWithUrlFile.isChecked() : 	 	wiz.startWithUrlFile.click()
	if wiz.startWithSearchEngine.isChecked() : 	wiz.startWithSearchEngine.click()
