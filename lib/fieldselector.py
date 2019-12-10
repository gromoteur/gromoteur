# -*- coding: utf-8 -*-

"""
Module implementing FieldSelector.
"""


from PyQt5.QtWidgets import  QDialog
#from PyQt4.QtGui import QProgressDialog
#from PyQt5.QtCore import pyqtSignature
from PyQt5 import QtWidgets

from .Ui_fieldselector import Ui_FieldSelector

from time import sleep
from html.entities import name2codepoint

#from htmlPage import sentenceSplit

from bs4 import BeautifulSoup
#from PyQt5.QtWebKit import *
from PyQt5.QtWebEngineWidgets import QWebEngineView as QWebView,QWebEnginePage as QWebPage

from PyQt5.QtCore import  pyqtSlot
import re
#, codecs, sys  

#verbose = True # decide whether to output information 
verbose=False

#sentenceSplit=re.compile(r"(([\?\!？](?![\?\!])|((?<!\s[A-ZÀÈÌÒÙÁÉÍÓÚÝÂÊÎÔÛÄËÏÖÜÃÑÕÆÅÐÇØ])\.。！……\s)|\s\|)\s*)", re.M+re.U)
#newLineTags = ["</div>","<table>","</td>","</tr>","</h1>","</h2>","</h3>","<br>","</p>","<p>"] #To keep paragraph information when producing text

windowsGarbage = {130 :"‚", 131 :"ƒ", 132 :"„", 133 :"…", 134 :"†", 135 :"‡", 136 :"ˆ", 137 :"‰", 138 :"Š", 139 :"‹", 140 :"Œ", 145 :"‘", 146 :"’", 147 :"“", 148 :"”", 149 :"•", 150 :"–", 151 :"—", 152 :"˜", 153 :"™", 154:"š", 155 :"›", 156 :"œ", 159 :"Ÿ"}
getRid = ["\/\*","\*\/"] # some garbage to kick out
########## regexes ########"


#sentenceSplit=re.compile(r"(([\?\!？](?![\?\!])|((?<!\s[A-ZÀÈÌÒÙÁÉÍÓÚÝÂÊÎÔÛÄËÏÖÜÃÑÕÆÅÐÇØ])\.。！……\s)|\s\|)\s*)", re.M+re.U)







anyTagRe=re.compile(r"<.*?>", re.M+re.U)
redoubleclick=re.compile(r"\&lt\;a .*?/a&gt;")
# problem of type:
#&lt;a href="http://ad.doubleclick.net/jump/n6747.popsci/announcements;kw=announcements,announcements,june_2013,table_of_contents;pos=x03;sz=88x31;tile=7;ord=1368932776?"&gt; &lt;/a&gt;

whiteSpaceRe=re.compile(r"(\s)+", re.M+re.U)
spaceRe=re.compile(r" ", re.M+re.U)

scriptex = re.compile("<script.*?</script>",re.I)
styleex = re.compile("<style.*?</style>",re.I)
rssex = re.compile("<rss.*?</rss>",re.I)
commentex = re.compile("<!--.*?-->",re.I)
imageex = re.compile("<img.*?>",re.I)


class FieldSelector(QDialog, Ui_FieldSelector):
	"""
	Class documentation goes here.
	"""

	textualId=-1
	columnId=-1
	
	def __init__(self, base, url, currenttextualization,  inColumnName, newLineTags,sentenceSplit):
		"""
		Constructor
		"""
		QDialog.__init__(self)
		self.setupUi(self)
		self.base=base
		self.currenturl=url
		self.constraints=None
#		self.content=""
		
		self.columnName='' 
#		self.inColumnName=inColumnName
		self.textualName=''
		self.sourceTextualName=currenttextualization
		self.selectableTags=["div","span","p","h1","h2","h3","tr","ul","li"]
		
		#print newLineTags
		#print "|".join(newLineTags )
		self.newLineRe=re.compile(newLineTags , re.M+re.I)
		self.sentenceSplit=sentenceSplit
		self.progressBar.hide()
		
		self.selectedColor='#b0c4de'
		self.webView.mousePressEvent = self.mousePressed
		self.selectColumnName=None
		if inColumnName:
			if self.base.columnIsSourceColumn(currenttextualization, inColumnName):
				self.selectColumnName=inColumnName
				
		self.getWebViewPage(self.currenturl)
		self.listTextualizations()
		self.listTextColumns()
		
		
	
	def getWebViewPage(self, url):
		self.currentrowid, source=self.base.getSourceByURL(url, self.sourceTextualName, self.selectColumnName)
		self.url.setText(url)
		if self.currentrowid==1:self.backButton.setEnabled(False)
		if source: self.showPage(source)

	def showPage(self, source):	
		"""
		inserts interactive js into a page before showing it in the webView
		the interactive js copies the element under the mouse into an invisible node 'grogro'
		"""
		soup=BeautifulSoup(source , "html.parser")

		js="""
	
		function cli(e, ele) {
			ele.style.borderStyle = 'solid';
			event.cancelBubble = true; 
			host=document.getElementById("grogro");
			oldnode=host.firstChild;
			newnode=ele.cloneNode(true)
			host.replaceChild(newnode, oldnode);
			return false
			}


			"""
		#insert js
		newTag=soup.new_tag('script')
		newString=soup.new_string(js)
		newTag.append(newString)
#		print "____________", soup.head
		if soup.html==None:	return
			
#		print soup.html, soup.html==None
		if not soup.head:	soup.html.append(soup.new_tag("head"))
		if not soup.body:	soup.html.append(soup.new_tag("body"))
		soup.head.append(newTag)
		
		#insert invisible div in the end
		new_tag = soup.new_tag("div", id="grogro", style="visibility:hidden")
		new_tag.append("nothing")
		soup.body.append(new_tag)		
		
		for tag in self.selectableTags:
			for d in soup.findAll(tag):
				d['onmouseover'] = "cli(event,this);"
				d['onmouseout'] = "this.style.borderStyle='none';"


		self.webView.setHtml(str(soup))
		
		

#	@pyqtSignature("bool")
#	def on_webView_loadFinished(self, p0):
#		"""
#		Slot documentation goes here.
#		"""
#		self.webViewIsLoading=False
		
		
#	@pyqtSignature("QMouseEvent")
	def mousePressed(self, me):
		"""
		Slot documentation goes here.
		"""
		self.constraints=[None, None, None]
		doc = self.webView.page().mainFrame().documentElement()
		
		host=doc.findFirst("div[id='grogro']").firstChild()
		
		#show the tag name
		self.tagCheckBox.setText('tag : '+host.tagName())
		self.tagCheckBox.setEnabled(True)
		self.constraints[0]=str(host.tagName())
		
		#show the id name 
		if host.hasAttribute('id'):
			self.idCheckBox.setText('id : '+host.attribute('id'))
			self.idCheckBox.setEnabled(True)	
			self.constraints[1]=str(host.attribute('id'))
		else:
			self.idCheckBox.setText('id')
			self.idCheckBox.setEnabled(False)
			
		#show the class name
		if host.hasAttribute('class'):
			self.classCheckBox.setText('class : '+host.attribute('class'))
			self.classCheckBox.setEnabled(True)
			self.constraints[2]=str(host.attribute('class'))
		else:
			self.classCheckBox.setText('class')
			self.classCheckBox.setEnabled(False)
		
		#self.sourceText.setPlainText(self.applyConstraints()[0])	
		self.applyConstraints()
#		self.sourceText.setPlainText(BeautifulSoup(unicode(host.toOuterXml()) ).get_text())
		
		#if self.constraints: 
			#self.textualComboBox.setEnabled(True)
			#self.listTextualizations()
			
		#else: 
			#self.textualComboBox.setEnabled(False)
			
#		self.buttonBox.setEnabled(True)
		
	def listTextualizations(self):
		"""
		shows the textualizations existing in the base
		"""
		self.textualNames=[] #remember the names that exist in the database
		self.textualComboBox.clear()
		#self.textualComboBox.addItem("")
		for cf in self.base.getTextualizations():
			self.textualComboBox.addItem(cf)
			self.textualNames.append(cf)
		self.textualComboBox.setCurrentIndex(self.textualComboBox.count()-1)
		self.textualName=str(self.textualComboBox.currentText())
		self.textualComboBox.setEnabled(False)
		
	def listTextColumns(self):
		"""
		get the column name you want
		1.if use the textualizations existing in the database , then list the column name belongs to the textualizations
			we can choose the existing column name or creat new names we want
		2. if we creat a new textualizations , then  no list for the column ,and we can creat a new name 
		3. the name can only Start with 'A~Z' and 'a~z
		
		"""
		self.columnNames=[]
		self.textcolComboBox.clear()
		if self.textualName in self.textualNames:
			(textualId, )=next(self.base.select( "select id from textualizations where name='"+self.textualName+"';"))
			for id,  in self.base.select("select columnid from textualcolumns where textualid="+str(textualId)+";"):
				(columnName,) =next(self.base.select("select name from textcolumns where  id="+str(id)+";"))
				self.columnNames.append(columnName)
			self.textcolComboBox.addItem("")
			for cf in self.columnNames:self.textcolComboBox.addItem(cf)
			self.columnName=str(self.textcolComboBox.currentText())
		else:
			self.textcolComboBox.clear()
		
	#@pyqtSignature("int")
	def on_textualComboBox_currentIndexChanged(self, index):
		"""
		Slot documentation goes here.
		"""
		self.textualName=str(self.textualComboBox.currentText())
		self.listTextColumns()
		self.setExtractionEnabled()
			
			
	#@pyqtSignature("QString")
	@pyqtSlot(str)
	def on_textualComboBox_editTextChanged(self, p0):
		"""
		Slot documentation goes here.
		"""
		self.textualName=str(self.textualComboBox.currentText())
		if len(self.textualName)==0:
			self.textcolComboBox.clear()
			self.textcolComboBox.clearEditText()
			self.warnLabel.setText("")
		else:
			if self.textualName<'A' or 'Z'<self.textualName[0] <'a' or self.textualName[0] >='z':
				self.warnLabel.setText("Illegal Name . Please Start with 'A~Z' and 'a~z'")
			else:
				self.warnLabel.setText("")
		self.listTextColumns()
		self.setExtractionEnabled()
			
	#@pyqtSignature("int")
	def on_textcolComboBox_currentIndexChanged(self, index):
			"""
			Slot documentation goes here.
			"""
			self.columnName=str(self.textcolComboBox.currentText())
			self.setExtractionEnabled()


	#@pyqtSignature("QString")
	@pyqtSlot(str)
	def on_textcolComboBox_editTextChanged(self, p0):
		"""
		Slot documentation goes here.
		"""
		self.columnName=str(self.textcolComboBox.currentText())
		if len(self.columnName)==0:
			self.warnLabel.setText("")
		else:
			if self.columnName<'A' or 'Z'<self.columnName[0] <'a' or self.columnName[0] >'z':
				self.warnLabel.setText("Illegal Name . Please Start with a letter")
			elif self.columnName in self.columnNames:
				self.warnLabel.setText("Existing columns will be overwritten!")
			else:
				self.warnLabel.setText("")
		self.setExtractionEnabled()
		

	#@pyqtSignature("")
	def on_additionTagLineEdit_returnPressed(self):
#		print "iiii"
		newselectabletag=str(self.additionTagLineEdit.text())
		if newselectabletag:
			self.selectableTags=list(set(self.selectableTags+[newselectabletag]))
		#print self.selectableTags

	def setExtractionEnabled(self):
		if self.columnName!='' and self.textualName!='' and (self.warnLabel.text()=="" or self.warnLabel.text()=="Existing columns will be overwritten!"):
			self.extractFrame.setEnabled(True )
			self.newcolumnButton.setEnabled(True )
			self.textExtraction.setEnabled(True )
		else:
			self.extractFrame.setEnabled(False)
			self.newcolumnButton.setEnabled(False )
			self.textExtraction.setEnabled(False )

	def applyConstraints(self):
		"""
		marks the divs of the current html document corresponding to the selected constraints
		gives back the selection as text and as source
		"""
		
#		print "marking constraints"
		
		doc = self.webView.page().mainFrame().documentElement()
		
#		for ele in doc.findAll("div") + doc.findAll("p")+doc.findAll("span"):
		for tag in self.selectableTags:
			for ele in doc.findAll(tag):
				ele.setStyleProperty('background-color', '#ffffff') # TODO: make this customizable or the contrary of the font color to remain readable
		
		
		if self.tagCheckBox.isChecked():
			constring=self.constraints[0] or "*"
		else: 	
			constring="*"
		if self.idCheckBox.isChecked() and self.constraints[1]:
			constr1='['+"id="+'"'+self.constraints[1]+'"'+']'		
			constring+=constr1
		if self.classCheckBox.isChecked() and self.constraints[2]:
			constr2='['+"class="+'"'+self.constraints[2]+'"'+']'	
			constring+=constr2
		#the format of the css selector is  span[hello="Cleveland"][goodbye="Columbus"] { color: blue; } !important
			
		elemsSource=""
		#paint the node
		if constring!="*":
			for elem in doc.findAll(constring):
				
				elemsSource+=str(elem.toOuterXml())+" "
#				self.content=unicode(elem.toOuterXml())+self.content
				elem.setStyleProperty('background-color', self.selectedColor)
				for tag in self.selectableTags:
					for child in elem.findAll(tag) : # all children
						child.setStyleProperty('background-color', self.selectedColor)
		pureText=self.html2text(elemsSource)				
		self.sourceText.setPlainText(pureText)
		return pureText, elemsSource


	def computeStat(self,  content=""):
		"""
		called from on_newcolumnButton_clicked
		when calculating the nbWords just calculate the number of characters
		
		"""	
#		content =content or self.content	
		if self.isLinguaContinua(content):
			nbWords=len(str(content)) #count the number of characters (word counting is too difficult for Chinese)
		else:
			nbWords=len(whiteSpaceRe.split(content))
		nbSentences=0
		for line in content.split("\n"):
			num=len(self.sentenceSplit.findall(line))
			if num==0:
				nbSentences=nbSentences+1
			else:
				nbSentences=nbSentences+len(self.sentenceSplit.findall(line))
		return nbWords, nbSentences
	
	
	def on_tagCheckBox_stateChanged(self, p0):
		self.applyConstraints()
		
	def on_idCheckBox_stateChanged(self, p0):
		self.applyConstraints()
		
		
	def on_classCheckBox_stateChanged(self, p0):
		self.applyConstraints()
		
	#@pyqtSignature("")
	pyqtSlot()
	def on_nextButton_clicked(self):
		#print 8888
		rowid,  url,  source = self.base.getNextSource(self.currentrowid, self.sourceTextualName, self.selectColumnName)
		if rowid: 
			#print 777
			self.url.setText(url)
			self.currentrowid+=1
			if not len(source.strip()): # if the next page was empty, take the following one.
				#print 999
				self.on_nextButton_clicked()
				return
			self.nextButton.setEnabled(True)
			self.backButton.setEnabled(True)
			self.currentrowid=rowid
			self.showPage(source)
			if self.constraints:self.applyConstraints()
			#print 7777
#			self.sourceText.clear()
		else:
			self.nextButton.setEnabled(False)


	#@pyqtSignature("")
	pyqtSlot()
	def on_backButton_clicked(self):
		#print 111
		rowid,  url,  source = self.base.getLastSource(self.currentrowid, self.sourceTextualName, self.selectColumnName)
		if rowid: 
			self.url.setText(url)
			self.currentrowid-=1
			if not len(source.strip()): 
				self.on_backButton_clicked()
				return
			self.backButton.setEnabled(True)
			self.nextButton.setEnabled(True)
			self.currentrowid=rowid
			self.showPage(source)
			if self.constraints:self.applyConstraints()
#			self.sourceText.clear()
			if rowid==1:self.backButton.setEnabled(False)
		else:
			self.backButton.setEnabled(False)
		
		
	def on_numElecomboBox_currentIndexChanged(self, index):

		raise NotImplementedError

	
	#@pyqtSignature("")
	pyqtSlot()
	def on_newcolumnButton_clicked(self):
		"""
		
		the function is to insert the new textualization and columnName information into the database 
		then extract the part we choose and insert into the database 
		show the progress bar and hide the progress bar
		
		in the database, should make the textualizations.
		
		"""
		#print "mmm",self.textualName,self.textualNames,self.textualName in self.textualNames
		if self.textualName in self.textualNames:
			(self.textualId, )=next(self.base.select( "select id from textualizations where name='"+self.textualName+"';"))
			if self.columnName not in self.columnNames:
				count=len(self.columnNames)+1
				self.base.execute("insert into textcolumns(name) values  (?) ;", (self.columnName, ))
				self.base.execute("insert into textualcolumns(textualid,columnid) values  (?,?) ;", (self.textualId, count, ))
				self.columnId=count
				self.overwrite=False
			else:
				# textualName  and  culumnName existed in the database . if the button are clicked, just overwrite 
				(self.columnId, )=next(self.base.select( "select id from textcolumns where name='"+self.columnName+"';"))
				self.overwrite=True
		else :
			qsdf
			self.textualId=len(self.textualNames)+1
			self.base.execute("insert into textualizations(name) values  (?) ;", (self.textualName, ))
			self.base.execute("insert into textcolumns(name) values  (?) ;", (self.columnName, ))
			(self.columnId, )=next(self.base.select( "select id from textcolumns where name='"+self.columnName+"';"))
			self.base.execute("insert into textualcolumns(textualid,columnid) values  (?,?) ;", (self.textualId, self.columnId, ))
			self.overwrite=False
		while not self.base.reqs.empty():
			pass
		sleep(.01) # wait for the database to close completely before giving back the textualName
		
		self.progressBar.show()
		(totalnum,) =next(self.base.select("select count(*) from sources;"))
		self.progressBar.setMaximum(totalnum)
		
		#go extract the part we choose
		for i in range(1, totalnum+1):
			source=self.base.getSourceById(i, self.textualName, self.selectColumnName)	#extract the part from the first to the last	
#			if not self.webViewIsLoading:
			self.webView.setHtml(source)
			
			textcontent, sourcecontent=self.applyConstraints()  
#			self.webView._wait_load()
			
#			textcontent=self.html2text(self.content)   
#			if textcontent:
			nbWords, nbSentences=self.computeStat(textcontent) 
			if self.textExtraction.isChecked(): enterstuff= textcontent
			else: enterstuff = "<html>\n"+sourcecontent+"\n</html>"
				
			self.base.enterNewText(i, self.textualId, self.columnId, enterstuff, nbSentences, nbWords, self.overwrite)
			
			self.progressBar.setValue(i)
			if self.base.errorState:
#				print self.base.errorState
				QtWidgets.QMessageBox.critical(self, "Problem with database",
				self.base.errorState + "\n\nDoes another program access the database file?")
				break
		
		self.base.makeTextual(self.textualName, self.textualId)
#		self.textualizationName=self.textualName
		
		self.progressBar.hide()
		self.progressBar.setValue(totalnum)
		#self.textualComboBox.setCurrentIndex(self.textualComboBox.count())
		#self.textualComboBox.setEnabled(False)
		self.setExtractionEnabled()
		
	
	################## stuff for text extraction
	################################
	
	def html2text(self,htmlSource):
#		if "doubleclick" in htmlSource: print "doubleclick","\n\n", htmlSource, "\n"
		htmlSource = whiteSpaceRe.sub(" ",htmlSource) # all white space (including new line) => simple space
		
		htmlSource = scriptex.sub(" ",htmlSource)
		htmlSource = styleex.sub(" ",htmlSource)
		htmlSource = rssex.sub(" ",htmlSource)
		htmlSource = commentex.sub(" ",htmlSource)
		htmlSource = imageex.sub(" ",htmlSource)
		
		htmlSource = self.newLineRe.sub("\n", htmlSource)
#		if "doubleclick" in htmlSource:print "\n\navant", htmlSource, "\n\n"
		pureText = anyTagRe.sub(" ", htmlSource)		# the great moment: we're down to pure text !
		pureText = redoubleclick.sub(" ", pureText)		# just in case the evil guys from doubleclick where around
		
#		if "doubleclick" in htmlSource:print "\n\n après", htmlSource, "\n\n"
		pureText = self._specialChar2UTF8(pureText)
		for g in getRid : # des trucs bizarres à virer :
			pureText = re.sub(g," ",pureText)
		# enlever les espaces et passages à la ligne successifs :
		pureText = re.sub("[ \t\r\f\v\n]*\n+[ \t\r\f\v\n]*","\n",pureText)
		pureText = re.sub("[ \t\r\f\v]+"," ",pureText)[1:-1]
		return pureText
		
		
	
	def _specialChar2UTF8(self,codeHTML):
		"""
		trying to replace things of type &#1234; and &eacute; by the unicode chars
		"""
		codeHTML = re.sub("&.+?;",self._replacementHtmlUnicode,codeHTML)
		return codeHTML

	def _replacementHtmlUnicode(self,s):
		match = s.group()[1:-1] # get rid of & and ;

		if match[:2] == "#x" : # if of type &#xabcd;
			try :
			   return chr(int(match[2:], 16))
			except Exception as e:
				if verbose: print("0. strange html like thing:",match,e)
		elif match[0] == "#" :
			i = int(match[1:])
			if i in windowsGarbage:
				return windowsGarbage[i]#.decode("utf-8")
			else:
				try :
					return chr(i)  # if of type &#1234;
				except Exception as e:
					if verbose: print("1. strange html like thing:",match,e)
					return " "
		try :
			return chr(name2codepoint[match])
		except Exception as e:
				if verbose: print("2. strange html like thing:",match,e)
				return " "
		
	def isLinguaContinua(self,text, threshold=0.9):
		"""
		returns true if the percentage of spaces in the text is below 10%
		"""
		txt=spaceRe.sub("", text)
		return (float(len(txt))/len(text+" ") > threshold   )
		
		
#		if text == None: text = self.data
#		#print text
#		print len(text.split()), len(text, ), float(len(text.split()))/len(text)
#		return float(len(text.split()))/len(text)<0.08	
		
		
#	
#if __name__ == "__main__":
#	
#	print type(content)
#	print len(unicode(content))

	
