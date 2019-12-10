# -*- coding: UTF-8 -*-

from sqlite3   import connect


def newGroBase(corpusFileName):
	db = connect(corpusFileName)
	cursor = db.cursor()
#	cursor.execute('''CREATE VIRTUAL TABLE information USING fts3( name, comments,  nbPages, nbSentences, nbWords, config file ) ;''')
	cursor.execute('''CREATE VIRTUAL TABLE sources USING fts3(  url, source, linkOrigin,  ts) ;''') #,link origin: page index or config
#	cursor.execute('''CREATE VIRTUAL TABLE texts USING fts3(sourceIndex, text) ;''')  # TODO: think how many of these tables  i need and when to create them
	
	db.commit()
	db.close()
	print("created", corpusFileName)
	
	
