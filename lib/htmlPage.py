# -*- coding: utf-8 -*-

import re, codecs, sys,  mimetypes
                                 
from urllib.parse import urljoin, urlsplit,  urlparse
from html.entities import name2codepoint
from io import StringIO

#import chardet, 
import charade
#import slate

from bs4 import BeautifulSoup
from bs4 import UnicodeDammit

	
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter#process_pdf
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams

#from cStringIO import StringIO


verbose = False
#verbose = True
#verbose = 2

if verbose:import traceback

newLineTags = ["</div>","<table>","</td>","</tr>","</h1>","</h2>","</h3>","<br>","<br/>","</p>","<p>","<hr>","<hr/>", "<center>", "</center>", "<ul>", "</ul>"]
getRid = ["\/\*","\*\/"]  # some garbage to kick out
#special88591CommonGarbage = [(u"‘","&lsquo;"), (u"’","&rsquo;"),(u"…","&#133;"),(u"€","&euro;"),(u"•","&#149;")] # currently not used
uselessUrlEndings=["/index.html",  "/index.htm", "/index.cgi","/index.xml","/index.rxml", "/index.php",  "/default.asp", "/index.asp", "/default.aspx","/index.aspx","/index.shtml"]

windowsGarbage = {130 :"‚", 131 :"ƒ", 132 :"„", 133 :"…", 134 :"†", 135 :"‡", 136 :"ˆ", 137 :"‰", 138 :"Š", 139 :"‹", 140 :"Œ", 145 :"‘", 146 :"’", 147 :"“", 148 :"”", 149 :"•", 150 :"–", 151 :"—", 152 :"˜", 153 :"™", 154:"š", 155 :"›", 156 :"œ", 159 :"Ÿ"}

windowsGarbageRe=re.compile("["+"".join([chr(c) for c in windowsGarbage ] ) +"]", re.U)

isoUtf8Garbage =["ž","Ÿ","","¡","¢","£","¤","¥","¦","§","¨","©","ª","«","¬","­","®","¯","°", "±","²","³","´","µ","¶", "·","¸" ,"¹","º","»" ,"¼","½","¾", "¿"]

########## regexes ########"
#sentenceSplit=re.compile(r"(([\?\!？](?![\?\!])|((?<!\s[A-ZÀÈÌÒÙÁÉÍÓÚÝÂÊÎÔÛÄËÏÖÜÃÑÕÆÅÐÇØ])\.。！……\s)|\s\|)\s*)", re.M+re.U)


#sentenceSplit=re.compile(ur"(\s*\n+\s*|(?<!\s[A-ZÀÈÌÒÙÁÉÍÓÚÝÂÊÎÔÛÄËÏÖÜÃÑÕÆÅÐÇØ])[\?\!？\!\.。！……]+\s+|\s+\|\s+|[？。！……]+)", re.M+re.U)


newLineRe=re.compile("|".join(newLineTags ) , re.M+re.I)
anyTagRe=re.compile(r"<.*?>", re.M+re.U)
whiteSpaceRe=re.compile(r"(\s)+", re.M)
scriptex = re.compile("<script.*?</script>",re.I)
styleex = re.compile("<style.*?</style>",re.I)
rssex = re.compile("<rss.*?</rss>",re.I)
commentex = re.compile("<!--.*?-->",re.I)
imageex = re.compile("<img.*?>",re.I)
charsetex = re.compile("(?<=charset\=)[\w\-]+",re.I+re.U)

fileex=re.compile("file\:\/+",re.I)

#redirectre = re.compile('<meta[^>]*?url=(.*?)["\']', re.IGNORECASE)

linkex = re.compile(r"""href=[ ]*["'](.*?)["']""",re.I)

class Page:
	def __init__(self, urlOrSource, groopener,  sentenceSplit, defaultEncoding="utf-8", takePdf=True):
#		,  followRedirect=True
		
		if verbose>1: print("*********** htmlPage ************",urlOrSource.encode("utf-8"))
		
		# initialization
		self.groopener=groopener
		self.sentenceSplit=sentenceSplit
		self.defaultEncoding = defaultEncoding
		self.takePdf = takePdf
#		self.followRedirect = followRedirect
		self.text,  self.encoding,  self.source,  self.links,  self.urls = "",  None,  "",  [],  []
		self.nbSentences,  self.nbWords= 0, 0
		self.title=""
		self.error=False
		self.titleWordNum, self.titleSenNum=0, 0
		
		
		# start
		self.scheme = urlsplit(urlOrSource)[0].lower() # get scheme (http, file, ...)	
		if verbose:print("_______________htmlPage scheme:",self.scheme)
		if self.scheme in ["http",  "https"]: # first case: normal URL
			self.url = urlOrSource
			self.subdomain = getSubdomain(self.url)
			self._openLink(self.url)
		elif self.scheme in ["file"]:
			if sys.platform.startswith("win"):self.url = fileex.sub("", urlOrSource)
			elif sys.platform.startswith("linux"): self.url = fileex.sub("/", urlOrSource)
			elif sys.platform.startswith("darwin"): self.url = fileex.sub("/", urlOrSource)
			self.urls=[self.url]
			
			self.mime, _ =mimetypes.guess_type(self.url)
			
			if self.mime=='application/pdf':
				try:self.text = self.pdf2text(open(self.url, "r").read())
				except:self.text=""
				self.title
				self.title=self.url.split("/")[-1]
				if self.title.endswith(".pdf"):self.title=self.title[:-4]
				self.source="pdf"
			else:
				self.mime='mime == "text/html"'
				f=codecs.open(self.url, "r", "utf-8")
				self.source = f.read()
				self.soup = BeautifulSoup(self.source, "html.parser")
				self.source = str(self.soup)
				self.text=self.html2text()
				title=None
				if self.soup.head: title=self.soup.head.title
				if not title: title=self.soup.title
				if title:	self.title=title.text
				else: self.title=self.url.split("/")[-1]
					
			self.computeStat()
			
			
		elif "<body" in urlOrSource or "<BODY" in urlOrSource: # second case: normal source
				self.source = urlOrSource
				self.url="string" # TODO: what to do with sources???
				
		elif self.scheme == "" : # third case: no scheme found, let's guess it's a url
			self.url = "http://"+urlOrSource
			self.subdomain = getSubdomain(self.url)
			self._openLink(self.url)
		else : # other scheme. can't do that...
			if verbose: print("url scheme of webpage is unsupported")
			self.url = ""
			self.source = ""

		
	def _openLink(self,link):
		if verbose: print("trying: --------------- "+link.encode("utf-8")+ " ---------------------")
		try:  
			r=self.groopener.open(link)
			self.urls=[]
			self.mime = r.headers.get('content-type', None)
#			.info().gettype()
			if verbose: print("self.mime",self.mime)
			if self.mime and self.mime.startswith("text"): ######### text, html, or xml
				
#				network.read()
				if verbose: print("reading text or html: "+link.encode("utf-8")+ " ok")
#				if self.followRedirect:match=redirectre.search(self.source)
#				while self.followRedirect and link not in self.urls and redirectre.search(self.source):
#					link = urljoin(link, redirectre.search(self.source).groups()[0].strip())
#					network=self.groopener.open(link)					
#					self.source = network.read()
#					self.urls+=[link]
				self.urls= [x.url for x in r.history]
				if link[-1]=="/":link=link[:-1] # strangely enough normal pages without redirects are not added to the history
				if link not in self.urls and link+"/" not in self.urls: self.urls+=[link] # 
				if self.defaultEncoding.strip(): # an encoding should be forced. use BeautifulSoup
					self.source = r.content
					self.soup = BeautifulSoup(self.source, "html.parser" , from_encoding=self.defaultEncoding)
					self.encoding = self.soup.original_encoding
					self.source = str(self.soup)
				else:
					self.source = r.content
					self.encoding = charade.detect(r.content)['encoding']
					if self.encoding:
						self.soup = BeautifulSoup(self.source, "html.parser", from_encoding=self.encoding )
						
						#if u"ĂŠ" in unicode(self.soup) or u"Ã©" in unicode(self.soup):
						if "Ă" in str(self.soup): # key for finding most wrong windows encodings inside utf-8
						
							for g in isoUtf8Garbage: # check whether it's at least one other typical character
								if "Ă"+g in str(self.soup):
									if verbose: print("Ă + some typical garbage - it's in fact utf-8")
									# typical errors when something is in fact utf-8 but it's decoded as western
									self.encoding = "utf-8"
									self.soup = BeautifulSoup(self.source, "html.parser" ) # .decode("utf-8",'replace')
									break
							
					else:
						self.soup = BeautifulSoup(self.source, "html.parser")
						self.encoding = r.encoding
					if verbose:
						print("htmlPage self.soup.contains_replacement_characters",self.soup.contains_replacement_characters)
						print("self.soup.original_encoding",self.soup.original_encoding)
					#self.encoding = r.encoding
					self.source = str(self.soup)
					#if verbose:print self.source.encode("utf-8")
				
				
				self.links=self._getLinks()
				self.source = self.getCleanHtml()
				self.text=self.html2text()
				title=None
				if self.soup.head: title=self.soup.head.title
				if not title: title=self.soup.title
				if title:	self.title=title.text
				self.computeStat()
				
				
			elif self.mime=="application/pdf" and self.takePdf :######### pdf
				self.source = r.content		# TODO: how about encoding of pdf pages?
				if verbose: print("reading pdf: "+link.encode("utf-8")+ " ok")
				try:self.text = self.pdf2text(self.source)
				except:self.text=""
				self.computeStat()
				self.title=link.split("/")[-1]
				if self.title.endswith(".pdf"):self.title=self.title[:-4]
				self.source="pdf" # TODO: what to do with the pdf source code??? can't put it easily into sqlite!
				
			elif verbose:
				print("wrong mime type", self.mime)
		except IOError:
			if verbose: 
				print("timeout with ",link.encode("utf-8"))
			self.error="Timeout"
			
		except Exception as msg:
			if verbose: 
				print(traceback.format_exc())
				print(msg) 
				print("problem with ",link.encode("utf-8"))
				self.error=str(traceback.format_exc())+" "+str(msg)
			else: self.error="other exception:"+str(msg)
			
	def computeStat(self):
		"""
		when computing the nbWords, we just calculate the number of the character
		
		"""
		self.nbWords=len(str(self.text))  # count the num of Chinese characters
		self.titleWordNum=len(str(self.title))
		self.titleSenNum=len(self.sentenceSplit.findall(self.title))
		if self.titleSenNum==0:
			self.titleSenNum=1
			
		self.nbSentences=0
		for line in self.text.split("\n"):
			num=len(self.sentenceSplit.findall(line))
			if num==0:
				self.nbSentences=self.nbSentences+1
			else:
				self.nbSentences=self.nbSentences+len(self.sentenceSplit.findall(line))

	def _getLinks(self):
		"""
		gets all 'a' and 'area' links in the current source
		corrected into complete urls (http://...)
		except strange links, javascript links, and pure anchor links
		"""
		goodLinks = []
		for atag in self.soup.findAll({'a' : True, 'area' : True}):
			match=linkex.search(str(atag))
			if match: 
				link = match.group(1).split("#")[0] # on coupe les ancres et on vire les liens qui sont des ancres dans la meme page
				link = self._specialChar2UTF8(link)
				if link and (link == "" or link.lower().strip().startswith("javascript:") or link.lower().strip().startswith("mailto:")):
					continue
				link = urljoin(self.url,link) # the magic line ! 
				link = re.sub("\.\.\/","",link)
				if urlparse(link).path=="/": 
					link=link[:-1] # TODO: think of when a url is equivalent with or without / behind a folder: taz.de/politik != taz.de/politik/
				for ending in uselessUrlEndings:
					if link.lower().endswith(ending):
						link=link[:-len(ending)]
						break
				goodLinks.append(link)
		return goodLinks
		
	def selectLinks(self, linkRestriction, urlEx, avoidUrlEx, knownLinks):
		"""
		linkRestriction: boolean, if true, check;  match urlEx  and not match avoidUrlEx
		list of knownLinks
		
		gives back a list of good links
		"""

		filteredLinks = []

		for link in self.links:

			if link not in knownLinks and link not in filteredLinks :
				urloc = urljoin(link,"/") #the join "/" gives the url of the network location TODO: verify if necessary!
				if  ( not linkRestriction)  or ( not urlEx or urlEx.search(link) and (not avoidUrlEx  or (not avoidUrlEx.search(link))) ) :
						filteredLinks.append(link)
				else :
					if verbose>1: print("BAD:\t\t ",link,"BAD:\t\t ", urloc,"not matching:\t",urlEx.pattern, avoidUrlEx, urlEx.search(link))
	
		return filteredLinks
	
	
	def _anySourceToUnicode(self,sour=None):
		"""
		decodes
		takes the encoding info from the frame, for European pages it's still often 'iso-8859-1'
		"""
		if not sour:  sour = self.source
		theSoup = BeautifulSoup(sour, "html.parser"  )
		htmlSource = str(theSoup)
		self.encoding=theSoup.originalEncoding
		return htmlSource


	def getCleanHtml(self,  source=None):
		"""
		all the source in one line!
		cleans redundant spacing, scripts, styles, rss, html comments
		"""
		if source: htmlSource=source
		else: htmlSource = self.source
		
		# TODO: make this cleaning optional
		
		htmlSource = whiteSpaceRe.sub(" ",htmlSource) # all white space (including new line) => simple space

		htmlSource = scriptex.sub(" ",htmlSource)
		htmlSource = styleex.sub(" ",htmlSource)
		htmlSource = rssex.sub(" ",htmlSource)
		htmlSource = commentex.sub(" ",htmlSource)
		htmlSource = imageex.sub(" ",htmlSource)
		
		return htmlSource

	def html2text(self,htmlSource=None):
		if htmlSource == None: htmlSource = self.source

		htmlSource = newLineRe.sub("\n", htmlSource)
		pureText = anyTagRe.sub(" ", htmlSource)		# the great moment: we're down to pure text !
		pureText = self._specialChar2UTF8(pureText)
		#print windowsGarbage,windowsGarbageRe
		if windowsGarbageRe.search(pureText):
			
			for c in windowsGarbage: # badly coded characters are repleced by correct ones
				#print windowsGarbage[c],unichr(c).encode('utf-8'), "mmmm"
				pureText=pureText.replace(chr(c),windowsGarbage[c])#.decode("utf-8")
		for g in getRid : 
			pureText = re.sub(g," ",pureText)
		pureText = re.sub("[ \t\r\f\v\n]*\n+[ \t\r\f\v\n]*","\n",pureText)
		pureText = re.sub("[ \t\r\f\v]+"," ",pureText)[1:-1]
		return pureText
	
	

	def pdf2text(self, pdfname):
		if pdfSource == None: pdfSource = self.source
		#f = StringIO(pdfSource)
		# PDFMiner boilerplate
		rsrcmgr = PDFResourceManager()
		sio = StringIO(pdfSource)
		codec = 'utf-8'
		laparams = LAParams()
		device = TextConverter(rsrcmgr, sio, codec=codec, laparams=laparams)
		interpreter = PDFPageInterpreter(rsrcmgr, device)

		# Extract text
		fp = file(pdfname, 'rb')
		for page in PDFPage.get_pages(fp):
			interpreter.process_page(page)
		fp.close()

		# Get text from StringIO
		text = sio.getvalue()

		# Cleanup
		device.close()
		sio.close()

		return text
	
	def oldpdf2text(self,  pdfSource=None):
		if pdfSource == None: pdfSource = self.source
		f = StringIO(pdfSource)
		doc = slate.PDF(f)
		return "".join([p for p in doc]) # .decode("utf-8")
		
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


def getSubdomain(url):
	try :
		subdom  = ".".join(urljoin(url,"/")[7:].split(".")[:-2])
	except :
		if verbose: print("Unexpected error:", sys.exc_info()[0])
		if verbose: print("problem with ",url)
		subdom = ""
	return subdom



#def pdf_to_csv(filename):
    #from cStringIO import StringIO  
    #from pdfminer.converter import LTChar, TextConverter
    #from pdfminer.layout import LAParams
    #from pdfminer.pdfparser import PDFDocument, PDFParser
    #from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter

    #class CsvConverter(TextConverter):
        #def __init__(self, *args, **kwargs):
            #TextConverter.__init__(self, *args, **kwargs)

        #def end_page(self, i):
            #from collections import defaultdict
            #lines = defaultdict(lambda : {})
            #for child in self.cur_item._objs:                #<-- changed
                #if isinstance(child, LTChar):
                    #(_,_,x,y) = child.bbox                   
                    #line = lines[int(-y)]
                    #line[x] = child._text.encode(self.codec) #<-- changed

            #for y in sorted(lines.keys()):
                #line = lines[y]
                #self.outfp.write(";".join(line[x] for x in sorted(line.keys())))
                #self.outfp.write("\n")

    ## ... the following part of the code is a remix of the 
    ## convert() function in the pdfminer/tools/pdf2text module
    #rsrc = PDFResourceManager()
    #outfp = StringIO()
    #device = CsvConverter(rsrc, outfp, codec="utf-8", laparams=LAParams())
        ## becuase my test documents are utf-8 (note: utf-8 is the default codec)

    #doc = PDFDocument()
    #fp = open(filename, 'rb')
    #parser = PDFParser(fp)       
    #parser.set_document(doc)     
    #doc.set_parser(parser)       
    #doc.initialize('')

    #interpreter = PDFPageInterpreter(rsrc, device)

    #for i, page in enumerate(doc.get_pages()):
        #outfp.write("START PAGE %d\n" % i)
        #if page is not None:
            #interpreter.process_page(page)
        #outfp.write("END PAGE %d\n" % i)

    #device.close()
    #fp.close()

    #return outfp.getvalue()



def encodingQuatsch():
	
	from .groSpider import GroOpener
	import requests
	global encoding
	import codecs
	import charade
	import pickle
	errors={}
	encoding=""
	def decodeErrorCounter(e):
		#print e
		#print "error",encoding
		#print errors
		errors[encoding]+=1
		return ('-',e.start + 1)

	codecs.register_error('counterrors',decodeErrorCounter)
	#s = u'My name is é©¬å…‹.'
	#print s.encode('ascii','counterrors') 
	
	def decode(s, encodings=('ascii', 'utf-8', 'utf-16', 'latin2', 'iso-8859-1', 'windows-1252', 'windows-1255')):
		
		print(ord(s[0]),ord(s[1]),ord(s[2]))
		
		global encoding
		for enc in encodings:
			encoding=enc
			#print "________________",encoding
			errors[encoding]=0
			
			#for c in s:
			try:
				sdec = s.decode(encoding,'counterrors')
				#print "good",encoding
				#return sdec
			except UnicodeDecodeError:
				print("error",encoding)
				#errors[encoding]+=1
			#print sdec.encode('utf-8')
		#print errors
		print([ enc for enc in errors if not errors[enc] ])# , reverse=True sorted(errors,key=errors.get)
		#return s.decode('ascii', 'ignore')
	
	def findEncodingInfo(raw):
		m=charsetex.search(raw)
		if m: print("findEncodingInfo",m.group(0))
		else: print("no encoding info")
	
	def dec(raw):
		print("mmm",charade.detect(raw)['encoding'])
		encoding=None
		for enc in ('utf-8', "CP1252", 'utf-16', 'utf-32'):
			try:
				sdec = raw.decode(enc)
				encoding=enc
				break
				#print "good",encoding
				
				#return sdec
			except UnicodeDecodeError:
				print("error",enc)
		if encoding:
			print("found encoding", encoding)
			#print sdec
			if "Ã©" in sdec:
				print("ooooooooooooooooooo")
		else:
			findEncodingInfo(raw)
			decode(raw)
			print("chardet.detect(raw)",chardet.detect(raw))
	
	def soupcode(raw):
		dammit=UnicodeDammit(raw)
		print(dammit.unicode_markup)
		return dammit.original_encoding
	
	#dec('http://lequipe.fr')
	def test(url):
		
		print("___",url)
		filename = url.split("/")[-1]
		try:
			raw = pickle.load(filename)
			
			
		except:
			r = requests.get(url, stream=True)
			raw = r.content
			with open(filename,'wb') as f:
				pickle.dump(raw,f)
		sdec = raw.decode("utf-8",'replace')
		
		for li in sdec.split("\n"):
			if "\uFFFD" in li:
				print(li)
		
		#print sdec
		#dec(raw)
		#print raw.decode("iso-8859-1",'replace')
		if "Ã©" in raw.decode("iso-8859-1",'replace'):
			print("zzzzzzzzzzzzzzzzzzakia")
			print(str( BeautifulSoup(raw, from_encoding="utf-8" ), "html.parser" ))
		#print unicode(sdec)
		
	#test('http://www.vosgesmatin.fr')
	#test('http://leprogres.fr')
	#test('http://leveil.fr')
	#test('')
	
	#s=u"rцsdfqq".encode("KOI8-U")
	#decode(s)
	#print soupcode(s)
	
	#print "___"
	#s=u"ééßqsdf楡敤洠牥qq".encode("utf-16")
	#decode(s)
	#print soupcode(s)
	
	#print "___"
	#s=u"ééßqsdf“qq putain de merdeŒ€¤¼".encode("CP1252")
	#decode(s)
	#print soupcode(s)
	#print charade.detect(s)['encoding']
	
	#print s.decode("iso-8859-1")
	#print chardet.detect(s)
	#decode(s)
	
	#go= GroOpener()
	#p=Page("http://patft.uspto.gov/netacgi/nph-Parser?patentnumber=6473006",  GroOpener())
	#p=Page("http://www.elnorte.ec/",  GroOpener())
	p=Page("http://www.verif.com/societe/HAFRAD-RACHID-537661829/", GroOpener(), sentenceSplit=re.compile(r"(([\?\!？](?![\?\!])|((?<!\s[A-ZÀÈÌÒÙÁÉÍÓÚÝÂÊÎÔÛÄËÏÖÜÃÑÕÆÅÐÇØ])\.。！……\s)|\s\|)\s*)", re.M+re.U) )
	print(p.text)
	print(p.encoding, p.soup.original_encoding)
	#r=go.open("http://www.goethe.de/ins/cn/lp/sdl/zh11711214.htm")
	#r=go.open("http://lequipe.fr")
	
	
	#print chardet.detect(r.content)
	#r = requests.get(, stream=True)
	#findEncodingInfo(r.content)
	
	
	#decode(r.content)
	
	
	
	
	#print r.content[:1333]
	##for c in r.content:
		##print c,c.decode("utf-8")
	#for i in range(126,1000):
		#print "____________________",i
		
		#print r.content[i*1000:(i+1)*1000]
		#print r.content[i*1000:(i+1)*1000].decode("utf-8")
	#print r, r.encoding
	
	##print r.raw.read(9111)
	

			
if __name__=="__main__":
	
	encodingQuatsch()
	
	#print pdf_to_csv("/home/kim/Dropbox/Android intro.pdf")
	
	
	#a=u"朗斯基：是的，20多年前我有幸来过中国。那次，我和几个朋友一起在中国旅行，通过喀喇昆仑公路从巴基斯坦进入中国，一路经过吐鲁番、乌鲁木齐、敦煌、兰州、西安、北京、上海和香港，最后回到印度。在公路、火车和飞机上的旅行给我留下了非常美好的印象。"
	#print sentenceSplit.findall(a)
	#print len(sentenceSplit.findall(a))
	#
	
	# print "******************************************"
	
	
	#from groSpider import GroOpener
	#p=Page("http://lequipe.fr",GroOpener(),re.compile(r"(([\?\!？](?![\?\!])|((?<!\s[A-ZÀÈÌÒÙÁÉÍÓÚÝÂÊÎÔÛÄËÏÖÜÃÑÕÆÅÐÇØ])\.。！……\s)|\s\|)\s*)", re.M+re.U), defaultEncoding="" )
	#http://www.vosgesmatin.fr
	#print p.encoding, p.soup.original_encoding
	#print "_______________________",unicode(p.soup)[7500:8500]#.encode("utf-8")
	# p=Page("http://www.cestlafete.fr/nosmagasins/paulescar.html",  GroOpener())

# #	print 'eeeee', p.text[:500].encode("utf-8"), 'rrrrrrr'
	# print 'eeeee', p.text[:500], 'rrrrrrr'
	# print "fini"
