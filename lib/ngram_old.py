# -*- coding: utf-8 -*-
import os, sys, re, codecs, glob, unicodedata
from operator import itemgetter
from heapq import nlargest
debug = False
#debug = 1

langs = {
'af':'Afrikaans',
'als':'Alsatian',
'ar':'Arabic',
'az':'Azerbaijan',
'be':'Belorussian',
'bg':'Bulgarian',
'bi':'Bislama',
'bn':'Bengali',
'br':'Breton',
'bs':'Bosnian',
'ca':'Catalan',
'cdo':'Cantonese (Roman script)',
'chr':'Cherokee',
'co':'Corsican',
'cs':'Czech',
'csb':'Kashubian',
'cy':'Welsh',
'da':'Danish',
'de':'German',
'dk':'Danish',
'dv':'Dhivehi',
'el':'Greek',
'en':'English',
'eo':'Esperanto',
'es':'Spanish',
'et':'Estonian',
'eu':'Basque',
'fa':'Persian',
'fi':'Finnish',
'fo':'Faroese',
'fr':'French',
'fy':'Frisian',
'ga':'Irish Gaelic',
'gd':'Scottish Gaelic',
'gl':'Galician',
'gn':'Guarani',
'gu':'Gujarati',
'gv':'Manx',
'he':'Hebrew',
'hi':'Hindi',
'hr':'Croatian',
'hu':'Hungarian',
'ia':'Interlingua',
'id':'Indonesian',
'io':'Ido',
'is':'Icelandic',
'it':'Italian',
'ja':'Japanese',
'jv':'Javanese',
'ka':'Georgian',
'km':'Khmer',
'ko':'Korean',
'ks':'Kashmiri',
'ku':'Kurdish',
'la':'Latin',
'lt':'Latvian',
'lv':'Livonian',
'mg':'Malagasy',
'mi':'Maori',
'minnan':'Min-Nan',
'mk':'Macedonian',
'ml':'Malayalam',
'mn':'Mongolian',
'mr':'Marathi',
'ms':'Malay',
'na':'Nauruan',
'nah':'Nahuatl',
'nb':'Norwegian (Bokmal)',
'nds':'Lower Saxon',
'nl':'Dutch',
'no':'Norwegian',
'nn':'Norwegian (Nynorsk)',
'oc':'Occitan',
'om':'Oromo',
'pcm':'Naija',
'pl':'Polish',
'ps':'Pashto',
'pt':'Portuguese',
'ro':'Romanian',
'roa-rup':'Aromanian',
'ru':'Russian',
'sa':'Sanskrit',
'sh':'OBSOLETE, Serbocroatian',
'si':'Sinhalese',
'simple':'Simple English',
'sk':'Slovakian',
'sl':'Slovenian',
'sq':'Albanian',
'sr':'Serbian',
'st':'Sesotho',
'su':'Sundanese',
'sv':'Swedish',
'sw':'Swahili',
'ta':'Tamil',
'th':'Thai',
'tl':'Tagalog',
'tlh':'Klingon',
'tokipona':'Toki Pona',
'tpi':'Tok Pisin',
'tr':'Turkish',
'tt':'Tatar',
'uk':'Ukrainian',
'ur':'Urdu',
'uz':'Uzbek',
'vi':'Vietnamese',
'vo':'Volapuk',
'wa':'Walon',
'xh':'isiXhosa',
'yi':'Yiddish',
'yo':'Yoruba',
'wo':'Wolof',
'za':'Zhuang',
'zh':'Chinese',
'zh-cn':'Simplified Chinese',
'zh-tw':'Traditional Chinese'
}
rtlLanguages=['Arabic','Hebrew','Pashto','Persian','Urdu']
decPunctex=re.compile(r"\d*\W*", re.U+re.I)


def mostcommon(iterable, n=None):
    """Return a sorted list of the most common to least common elements and
    their counts.  If n is specified, return only the n most common elements.
    """
    bag = {}
    bag_get = bag.get
    for elem in iterable:
        bag[elem] = bag_get(elem, 0) + 1
    if n is None:
        return sorted(iter(bag.items()), key=itemgetter(1), reverse=True)
    it = enumerate(bag.items())
    nl = nlargest(n, ((cnt, i, elem) for (i, (elem, cnt)) in it))
    return [(elem, cnt) for cnt, i, elem in nl]


class Ngram:

	def __init__(self):
		self.n=3
		self.ngramnum = 500
		self.charnum = 200 # if too small, doesn't recognize chinese!
		
		self.freqmulti = 1000000
		
		self.langfolder = os.path.join("lib","languages")
		self.langext = "lang.txt"
		self.ngramext = ".ng"
		self.ngrams={}
		self.replare = re.compile(r"\s+")
		
		self.charGuesser = 	[	
		("Lo","CJK","zh"),
		("Lo","HANGUL","ko"),
		("Lo","HIRAGANA","ja"),
		("Lo","KATAKANA","ja"),
		("Ll","GREEK","el"),
		("Lu","GREEK","el"),
		("Lo","GUJARATI","gu"),
		("Lo","GEORGIAN","ka"),
		("Lo","BENGALI","bn"),
		("Lo","TAMIL","ta"),
		("Lo","THAI","th"),
		("Lo","THAANA","dv"),	
		("Lo","DEVANAGARI","ngram"),
		("Ll","CYRILLIC","ngram"),
		("Lu","CYRILLIC","ngram"),
		("Lo","ARABIC","ngram"),
		("Lo","ARABIC","ngram"),
		("Ll","LATIN","ngram"),
		("Lu","LATIN","ngram")
		]
		
		self.alllangs = langs
		self.readNgrams()
		
		
	

	def guessLanguage(self,text, removeDecPunct=False):
		"""
		takes a text,
		gives back the code of the most probable language by:
		- first looking at the unicode categories and keys of the self.charnum most common characters
		- if self.charGuesser gives a name, give back that name
		- if self.charGuesser gives 'ngram', try ngram approach
		"""
		if removeDecPunct:
			langCat, langK = self.mostCommonUnicodeKeys(decPunctex.sub(" ", text))	
		else:
			langCat, langK = self.mostCommonUnicodeKeys(text)	
		if debug: print("langCat,langK", langCat,langK)
		for cat,key,name in self.charGuesser:
			#print(cat,key,name)
			if langCat == cat and langK == key:
				if name == "ngram":
					#if debug: print("highestNgramMatches",self.highestNgramMatches(text))
					res = self.highestNgramMatches(text)
					if res: return res[0]
				else: return 100,name
					
		return 0, "unknown language! information: "+langCat+" "+ langK
				

	def guessLanguageRealName(self,text):
		"""
		wrapper class for guessLanguage
		gives back real name
		"""
		
		return self.alllangs.get(self.guessLanguage(text)[1],"an unknown language, maybe "+str(self.mostCommonUnicodeKeys(text)))
	
	def guessLanguageList(self,text, removeDecPunct=False):
		"""
		takes a text,
		gives back the code of the most probable language by:
		- first looking at the unicode categories and keys of the self.charnum most common characters
		- if self.charGuesser gives a name, give back that name
		- if self.charGuesser gives 'ngram', try ngram approach
		"""
		if removeDecPunct:
			langCat, langK = self.mostCommonUnicodeKeys(decPunctex.sub(" ", text))	
		else:
			langCat, langK = self.mostCommonUnicodeKeys(text)	
		if debug: print("langCat,langK", langCat,langK)
		for cat,key,name in self.charGuesser:
			#print(cat,key,name)
			if langCat == cat and langK == key:
				if name == "ngram":
					#if debug: print("highestNgramMatches",self.highestNgramMatches(text))
					res = self.highestNgramMatches(text)
					if res: return res
				else: return [(100,name)]
					
		return [(0, "unknown language! information: "+langCat+" "+ langK)]
		
		
		
	def distance(self,text,lang):
		textlen=len(text)
		if textlen==0:return
		text = self.replare.sub("_"," "+text+" ".lower())
		textNgrams={}
		distance=0
		# computing the value added for each ngram found
		addValue = int((1.0/textlen)*self.freqmulti)
		
		textNgrams = self.ngramList(text,self.n,addValue)[:self.ngramnum]
		
		for f,nuple in textNgrams:#.iteritems(): # for each ngram
			distance= distance + abs(self.ngrams[lang].get(nuple,0)-f)
		distance = (float(distance)/addValue/textlen-1)*(-100)
		
		return distance			
		
			

	def readNgrams(self):
		folder = os.path.join(self.langfolder,'*'+self.ngramext)
		for filename in glob.glob(os.path.normcase(folder)):
			language = os.path.split(filename)[-1].split(".")[0]
			self.ngrams[language]={}
			file = codecs.open(filename,"r", "utf-8" )
			for line in file:
				try:
					g,f=line.split("\t")
					self.ngrams[language][g]=int(f)
				except:
					print("error in file",filename)

	def allLanguages(self):
		"""
		gives a list of all languages we have information about
		"""
		codes = []
		names = []
		for cat,key,name in self.charGuesser:
			if name != "ngram":codes+=[name]
			
		
		folder = os.path.join(self.langfolder,'*'+self.ngramext)
		for filename in glob.glob(os.path.normcase(folder)):
			language = filename.split("/")[-1].split(".")[0]
			codes+=[language]
		
		codes=list(set(codes))
		codes.sort()
		for c in codes:
			names+= [self.alllangs.get(c,c)]
		return codes,names

	def makeNgrams(self):
		folder = os.path.join(self.langfolder,'*'+self.langext)
		if debug: print("making",str(self.n)+"-grams...")
		number=0
		languagesDone=[]
		for infilename in glob.glob(os.path.normcase(folder)): # for each minicorpus of a language
			language = infilename.split("/")[-1].split(".")[0]
			
			#if debug: print language,
			infile = codecs.open(infilename,"r", "utf-8" )
			outfile = codecs.open(os.path.join(self.langfolder,language+self.ngramext) ,"w", "utf-8" )
			#print(language, outfile)
			text = infile.read()
			
			textlen=len(text)
			if textlen==0:continue
			text = self.replare.sub("_"," "+text+" ".lower())
			
			addValue = int((1.0/textlen)*self.freqmulti)			
			sordico = self.ngramList(text,self.n,addValue)[:self.ngramnum]
			
			#print len(text)
			for f,g in sordico:
				outfile.write(g+"\t"+str(f)+"\n")
			number+=1
			languagesDone+=[language]
		for lang in langs:
			if lang not in languagesDone:
				print("no files found for",lang)
		print("  done",number,"languages")
		print(langs)
		print(languagesDone)

	def ngramList(self,text,n,addValue):
		"""
		for a text, the size of the ngram and the value to add for each ngram found,
		the function gives back
		a list of couples: frequency, ngram
		"""
		thesengrams={}
		for i in range(len(text)-n):
			nuple = text[i:i+n]
			thesengrams[nuple]=thesengrams.get(nuple,0)+addValue
		sordico = [(f,g) for g,f in thesengrams.items()]
		sordico.sort()
		sordico.reverse()
		return sordico
		
	

	def mostCommonUnicodeKeys(self,text):
		"""
		takes a text,
		gives back 
		- the most common unicodedata.category (of the self.charnum most common characters)
		- the most common first word in the unicodedata.name (of the self.charnum most common characters)
		
		category values:
		* Lu - uppercase letters
		* Ll - lowercase letters
		* Lt - titlecase letters
		* Lm - modifier letters
		* Lo - other letters
		* Nl - letter numbers
		* Mn - nonspacing marks
		* Mc - spacing combining marks
		* Nd - decimal numbers
		* Pc - connector punctuations	
		"""
		textlen=len(text)
		if textlen<2:return "",""
		text = self.replare.sub(" ",text) 
		#frequentLetters=[]
#		frequentChars=[]
		
#		for f,c in self.ngramList(text,1,1.0/textlen):
#			cat = unicodedata.category(c)
#			if cat[0]=="L":
#				frequentLetters+=[(f,c)]
#			frequentChars += [(f,c)]
		frequentChars = [(f,c) for f,c in self.ngramList(text,1,1.0/textlen)][:self.charnum]
#		print "frequentChars", frequentChars
		#frequentLetters=frequentLetters[:self.charnum]
		
		langCats=[]
		langKeys=[]
		for f,c in frequentChars:
			#print "*",f,"."+c+".","*****",unicodedata.category(c),ord(c),unicodedata.name(c)
			langCats+=[unicodedata.category(c)]
			#langKeys+=[unicodedata.name(c).split()[0]]
			try:langKeys+=[unicodedata.name(c).split()[0]] # can happen for characters that don't have a name (windows garbage, ...) !!!
			except:pass
		
		
		#for a,b in frequentLetters : print a,b,unicodedata.category(b),unicodedata.name(b)
		langCat = mostcommon(langCats,1)[0][0]
		langK = mostcommon(langKeys,1)[0][0]
		return langCat,langK
		
						

	def highestNgramMatches(self, text):
		""" 
		takes a text, 
		gives back a list of all (score,language_code), starting with the highest score
		"""
		
		textlen=len(text)
		text = self.replare.sub("_"," "+text+" ".lower())
		textNgrams={}
		distdico={}
		
		if textlen==0:return
		# computing the value added for each ngram found
		addValue = int((1.0/textlen)*self.freqmulti)
		if debug: print("addValue",addValue)
		#print 1/0
		#for i in range(len(text)-self.n+1):
			#nuple = text[i:i+self.n]
			##print nuple,textNgrams.get(nuple,0)+addValue
			#textNgrams[nuple]=textNgrams.get(nuple,0)+addValue
		
		textNgrams = self.ngramList(text,self.n,addValue)[:self.ngramnum]
		
		#sordico = sordico[:self.ngramnum]
		for f,nuple in textNgrams:#.iteritems(): # for each ngram
			if debug: print("___",nuple,f)
			#print "$$$",self.ngrams
			for l,ng in self.ngrams.items(): # for each language
				#print l, ng
				
				distdico[l]= distdico.get(l,0) + abs(ng.get(nuple,0)-f)
				if debug: print(nuple,l,"f:",f,"ng.get(nuple,0):",ng.get(nuple,0),abs(ng.get(nuple,0)-f))
		langlist = [((float(dist)/addValue/textlen-1)*(-100),l) for l,dist in distdico.items()]
		langlist.sort()
		langlist.reverse()
		return langlist			

	def extractGoodLanguageParags(self, text, goodLanguageCode):
		newtext=""
		for sentence in text.split("\n"):
			if self.guessLanguage(sentence)[1]==goodLanguageCode:
				newtext+=sentence+"\n"
		return newtext
	################################################# end of class Ngram #############################"
	
	
	
	
	
	
	
if __name__ == "__main__":
	ngram = Ngram()
	ngram.langfolder = "languages"
	
	ngram.makeNgrams()
	ngram.readNgrams()
	print("_________")
	
	testset= [
	("fr","comment ça ça va ?"),
	("ar","تاگلديت ن لمغرب"),
	("fa","برای دیدن موارد مربوط به گذشته صفحهٔ بایگانی را ببینید."),
	("ps","""، کړ و وړو او نورو راز راز پژني او رواني اکرو بکرو... څرګندويي کوي او د چاپېريال او مهال څيزونه، ښکارندې، پېښې،ښه او بد... رااخلي. په بله وينا: ژبه د پوهاوي راپوهاوي وسيله ده.د ژبې په مټ خپل اندونه،واندونه (خيالونه)، ولولې، هيلې او غوښتنې سيده يا ناسيده، عمودي يا افقي نورو ته لېږدولای شو. خبرې اترې يې سيده او ليکنه يې ناسيده ډول دی.که بيا يې هممهالو ته لېږدوو، افقي او که راتلونکو پښتونو( نسلونو) ته يې لېږدوو، عمودي بلل کېږي."),"""),
	("en","the"),
	("ja","ウィキペディアはオープンコンテントの百科事典です。基本方針に賛同していただけるなら、誰でも記事を編集したり新しく作成したりできます。詳しくはガイドブックをお読みください。"),
	("el","Το κεντροδεξιό Εθνικό Κόμμα του Τζον Κέι κερδίζει τις εκλογές στη Νέα Ζηλανδία, αποκαθηλώνοντας από την εξουσία το Εργατικό Κόμμα της Έλεν Κλαρκ, έπειτα από εννέα χρόνια."),
	("ru","Голубь предпочитает небольшие, чаще всего необитаемые острова, где отсутствуют хищники. Живёт в джунглях."),
	("bg","За антихитлеристите месец август 1944 година се оказва добър. "),
	("hi","पहले परमाणु को अविभाज्य माना जाता था।"),
	("gl","Aínda que non nega que os asasinatos de civís armenios ocorreran na realidade, o goberno turco non admite que se tratase dun xenocidio, argumentando que as mortes non foron a resulta dun plano de exterminio masivo organizado polo estado otomán, senón que, en troques, foron causadas polas loitas étnicas, as enfermidades e a fame durante o confuso período da I Guerra Mundial. A pesares desta tese, case tódolos estudosos -até algúns turcos- opinan que os feitos encádranse na definición actual de xenocidio. "),
	("de","Was nicht daran liegt, dass das Unternehmen kein Interesse an der Verarbeitung biologisch angebauter Litschis hat. Die Menge an Obst aber, die Bionade inzwischen braucht, gibt es auf dem weltweiten Biomarkt nicht - oder nur zu einem sehr hohen Preis. Im Prinzip gebe es zwar ausreichend Litschis, allerdings werde ein Großteil der Früchte für den Frischobstmarkt angebaut und auch dort gehandelt. Wandelte man dieses Frischobst in Konzentrat um, würde dies zu teuer, sagte ein Geschäftspartner von Bionade gegenüber Foodwatch. scheiße"),
	("mr","भारतीय रेल्वे (संक्षेपः भा. रे.) ही भारताची सरकार-नियंत्रित सार्वजनिक रेल्वेसेवा आहे. भारतीय रेल्वे जगातील सर्वात मोठ्या रेल्वेसेवांपैकी एक आहे. भारतातील रेल्वेमार्गांची एकूण लांबी ६३,१४० कि.मी. "),
	("fa","""
	 ویکی‌پدیا یک پروژهٔ ناسودبر است: لطفاً امروز کمک کنید.
اکنون کمک کنید »
[نمایش]
حمایت از ویکی‌پدیا: یک پروژهٔ ناسودبر.
اکنون کمک کنید »
اتم
از ویکی‌پدیا، دانشنامهٔ آزاد
پرش به: ناوبری, جستجو
اتم
اتم هلیوم
This illustrates the nucleus (pink) and the electron cloud distribution (black) of the Helium atom. The nucleus (upper right) is in reality spherically symmetric, although this is not always the case for more complicated nuclei.
رده
کوچک‌ترین جز در شیمی عناصر
مشخصات
جرم : 	≈ 1.67×10-27
to 4.52×10-25
 kg
بار الکتریکی : 	صفر
قطر : (قطر به عنصر و ایزتوپ اتم بستگی دارد)‎ 	31 pm (He) تا 520 pm (Cs)‎
انواع اتمهای که تاکنون دیده ‌شده‌است: 	~1080[۱]
اتم کوچکترین واحد تشکیل دهنده یک عنصر شیمیایی است که خواص منحصر به فرد آن عنصر را حفظ می‌کند. تعريف ديگری آن را به عنوان کوچکترين واحدی در نظر ميگيرد که ماده را ميتوان به آن تقسيم کرد بدون اينکه اجزاء بارداری از آن خارج شود.[۲] اتم ابری الکترونی، تشکیل‌شده از الکترون‌ها با بار الکتریکی منفی، که هستهٔ اتم را احاطه کرده‌است. هسته نیز خود از پروتون که دارای بار مثبت است و نوترون که از لحاظ الکتریکی خنثی است تشکیل شده است. زمانی که تعداد پروتون‌ها و الکترون‌های اتم با هم برابر هستند اتم از نظر الکتریکی در حالت خنثی یا متعادل قرار دارد در غیر این صورت آن را یون می‌نامند که می‌تواند دارای بار الکتریکی مثبت یا منفی باشد. اتم‌ها با توجه به تعداد پروتون‌ها و نوترون‌های آنها طبقه‌بندی می‌شوند. تعداد پروتون‌های اتم مشخص کننده نوع عنصر شیمیایی و تعداد نوترون‌ها مشخص‌کننده ایزوتوپ عنصر است. [۳]
نظريه فيزيک کوانتم تصوير پيچيده ای از اتم ارائه ميدهد و اين پيچيدگی دانشمندان را مجبور ميکند که جهت توصيف خواص اتم بجای يک تصوير متوسل به تصاوير شهودی متفاوتی از اتم شوند. بعضی وقت ها مناسب است که به الکترون به عنوان يک ذره متحرک به دور هسته نگاه کرد و گاهی مناسب است به آنها عنوان ذراتی که در امواجی با موقعيت ثابت در اطراف هسته (مدار: orbits) توزيع شده اند نگاه کرد. ساختار مدار ها تا حد بسيار زيادی روی رفتار اتم تأثير گذارده و خواص شيميايی يک ماده توسط نحوه دسته بندی اين مدار ها معين ميشود.[۲]
فهرست مندرجات
[نهفتن]
    * ۱ اجزا
          o ۱.۱ ذرات بنیادی
          o ۱.۲ هسته
          o ۱.۳ ابر الکتررونی
    * ۲ مدل‌های اتمی
          o ۲.۱ مدل اتمی دالتون
          o ۲.۲ مدل اتمی تامسن
          o ۲.۳ مدل اتمی رادرفورد
          o ۲.۴ مدل اتمی لایه‌ای
    * ۳ منبع
[ویرایش] اجزا
جهت بررسی اجزاء يک ماده، ميتوان به صورت پی در پی آن را تقسيم کرد. اکثر مواد موجود در طبيعت ترکيب شلوغی از مولکول های مختلف است. با تلاش نسبتاً کمی ميتوان اين مولکول ها را از هم جدا کرد. مولکول ها خودشان متشکل از اتم ها هستند که توسط پيوند های شيميايی به هم پيوند خورده اند. با مصرف انرژی بيشتری ميتوان اتم ها را از مولکول ها جدا کرد. اتم ها خود از اجزاء ريزتری بنام هسته و الکترون تشکيل شده که توسط نيرو های الکتريکی به هم پيوند خورده اند و شکستن آنها انرژی بسی بيشتری طلب ميکند. اگر سعی در شکستن اين اجرا زير اتمی با صرف انرژی زياد بکنيم، کار ما باعث توليد شدن ذرات جديدی ميشويم که خيلی از آنها بار الکتريکی دارند. [۲]
همانطور که اشاره شد اتم از هسته و الکترون تشکيل شده است. جرم اصلی اتم در هسته قرار دارد؛ فضای اطراف هسته عموماً فضای خالی ميباشد. هسته خود از پروتن (که بر مثبت دارد)، و نوترن (که بر خنثی دارد) تشکيل شده. الکترون هم بار منفی دارد. اين سه ذره عمری طولانی داشته و در تمامی اتم های معمولی که به صورت طبيعی تشکيل ميشوند يافت ميشود. بجز اين سه ذره، ذرات ديگری نيز در ارتباط با آنها ممکن است موجود باشد؛ ميتوان اين ذرات ديگر را با صرف انرژی زياد نيز توليد کرد ولی عموماً اين ذرات زندگی کوتاهی داشته و از بين ميروند.[۲]
اتم ها مستقل از اينکه چند الکترون داشته باشند (۳ تا يا ۹۰ تا)، همه تقريباً يک اندازه دارند. به صورت تقريبی اگر ۵۰ ميليون اتم را کنار هم روی يک خط بگذاريم، اندازه آن يک سانتيمتر ميشود. به دليل اندازه کوچک اتم ها، آنها را با واحدی به نام انگسترم که برابر ۱۰- ۱۰ متر است مي سنجند.[۲]
[ویرایش] ذرات بنیادی
    نوشتار اصلی: ذرات زیراتمی
[ویرایش] هسته
    نوشتار اصلی: هسته اتم
[ویرایش] ابر الکتررونی
[ویرایش] مدل‌های اتمی
[ویرایش] مدل اتمی دالتون
نظریهٔ اتمی دالتون: دالتون نظریه اتمی خود را با اجرای آزمایش در هفت بند بیان کرد.
    * ماده از ذره‌های تجزیه ناپذیری به نام اتم ساخته شده‌است.
    * همهٔ اتم‌ها یک عنصر، مشابه یکدیگرند.
    * اتم‌ها نه به وجود می‌آیند و نه از بین می‌روند.
    * همهٔ اتم‌های یک عنصر جرم یکسان و خواص شیمیایی یکسان دارند.
    * اتم‌های عنصرهای مختلف به هم متصل می‌شوند و مولکول‌ها را به وجود می‌آورند.
    * در هر مولکول از یک ترکیب معین، همواره نوع و تعداد نسبی اتم‌های سازنده ی آن یکسان است.
    * واکنش‌های شیمیایی شامل جابه جایی اتم‌ها و یا تغییر در شیوهٔ اتصال آن‌ها است.
نظریه‌های دالتون نارسایی‌ها و ایرادهایی دارد و اما آغازی مهم بود. مواردی که نظریهٔ دالتون نمی‌توانست توجیه کند:
    * پدیدهٔ برقکافت (الکترولیز) و نتایج مربوط به آن
    * پیوند یونی ـ فرق یون با اتم خنثی
    * پرتو کاتدی
    * پرتوزایی و واکنش‌های هسته‌ای
    * مفهوم ظرفیت در عناصر گوناگون
    * پدیدهٔ ایزوتوپی
قسمت اول نظریهٔ دالتون تأیید فیلسوف یونانی (دموکریت) بود.
نظریهٔ دالتون از سه قسمت اصلی (قانون بقای جرم ـ قانون نسبت‌ها معین ـ قانون نسبت‌های چندگانه) می‌باشد.
مطالعهٔ اتم‌ها و ذرات ریزتر فقط به صورت غیرمستقیم و از روی رفتار (خواص) امکان پذیر است.
اولین ذرهٔ زیراتمی شناخته شده الکترون است. مواردی که به کشف و شناخت الکترون منجر شد:
    * الکتریسیتهٔ ساکن یا مالشی
    * پدیدهٔ الکترولیز (برقکافت)
    * پرتو کاتدی
    * ۴پدیدهٔ پرتوزایی
[ویرایش] مدل اتمی تامسن
مدل اتمی تامسون (کیک کشمشی، مدل هندوانه‌ای یا ژله میوه دار)
    * الکترون با بار منفی، درون فضای ابرگونه با بار مثبت، پراکنده شده‌اند.
    * اتم در مجموع خنثی است. مقدار با مثبت با بار منفی برابر است.
    * این ابر کروی مثبت، جرمی ندارد و جرم اتم به تعداد الکترون آن بستگی دارد.
    * جرم زیاد اتم از وجود تعداد بسیار زیادی الکترون در آن ناشی می‌شود.
[ویرایش] مدل اتمی رادرفورد
1)هر اتم دارای یک هسته کوچک است که بیشتر جرم اتم در آن واقع است.
2)هسته اتم دارای بار الکتریکی مثبت است.
3)حجم هسته در مقایسه با حجم اتم بسیار کوچک است زیرا بیشتر حجم اتم را فضای خالی تشکیل میدهد.
4)هسته اتم بوسیله الکترونها محاصره شده است.
[ویرایش] مدل اتمی لایه‌ای
[ویرایش] منبع
""")
	]
	for name,text in testset:
		l=ngram.guessLanguage(text)
		print(name,l, name==l[1])
		if not name==l[1]:print("guessed",l,"_________")
		
	#print ngram.highestNgramMatches(testset[-1][1].decode("utf-8"))
	#print ngram.allLanguages()
		
