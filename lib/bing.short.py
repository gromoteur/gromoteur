# -*- coding: utf-8 -*-

import requests, requests.utils, re, urllib.request, urllib.parse, urllib.error
from .py_ms_cognitive_search import PyMsCognitiveSearch



## first part modified from: https://github.com/tristantao/py-ms-cognitive/blob/master/py_ms_cognitive/py_ms_cognitive_search/py_ms_cognitive_web_search.py
##
## Web Search
##
##

reurl=re.compile(r"&r\=(.*)&p\=",re.U)

class PyMsCognitiveWebSearchException(Exception):
    pass

class PyMsCognitiveWebSearch(PyMsCognitiveSearch):

    SEARCH_WEB_BASE = 'https://api.cognitive.microsoft.com/bing/v7.0/search'

    def __init__(self, api_key, query, safe=False, count='50',custom_params='',offset=0,mkt=None):
        query_url = self.SEARCH_WEB_BASE + custom_params
        PyMsCognitiveSearch.__init__(self, api_key, query, query_url, safe=safe)
        self.current_offset=offset
        self.mkt=mkt
        self.totalEstimatedMatches=0
        self.webSearchUrl=""

    def _search(self, limit, format, offset=0):
        '''
        Returns a list of result objects, with the url for the next page MsCognitive search url.
        '''
        if offset:	self.current_offset=offset
        payload = {
          'q' : self.query,
          'count' : '50', #currently 50 is max per search.
          'offset': self.current_offset,
          'safesearch' : 'Off', #optional
        }
	if self.mkt:	payload['mkt']=self.mkt
	if limit:	payload['count']=str(limit)
        headers = { 'Ocp-Apim-Subscription-Key' : self.api_key }
        if self.safe:
            QueryChecker.check_web_params(payload, headers)
        response = requests.get(self.QUERY_URL, params=payload, headers=headers)
        json_results = self.get_json_results(response)
        self.totalEstimatedMatches=json_results["webPages"]["totalEstimatedMatches"]
        self.webSearchUrl=json_results["webPages"]["webSearchUrl"]
        packaged_results = [WebResult(single_result_json) for single_result_json in json_results["webPages"]["value"]]
        self.current_offset += min(50, limit, len(packaged_results))
        return packaged_results

class WebResult(object):
    '''
    The class represents a SINGLE search result.
    Each result will come with the following:
    the variable json will contain the full json object of the result.
    title: title of the result (alternately name)
    url: the url of the result. Seems to be a Bing redirect
    displayUrl: the url used to display
    snippet: description for the result (alternately description)
    id: MsCognitive id for the page
    '''

    def __init__(self, result):
        self.json = result
        self.url = result.get('url')
        self.display_url = result.get('displayUrl')
        self.name = result.get('name')
        self.snippet = result.get('snippet')
        self.id = result.get('id')

        #maintain compatibility
        self.title = result.get('name')
        self.description = result.get('snippet')



def search(query, accountkey, location=None, skip=0):
	"""
	called from spiderConfigWizard.py and spiderThread.py
	returns 
	- 50 results
	- the totalEstimatedMatches 
	- webSearchUrl
	"""
	if not location or location=="automatic location detection":mkt=None
	else:mkt = location
	print("***",accountkey, query, False, skip,mkt)
	search_service = PyMsCognitiveWebSearch(accountkey, query, safe=False, offset=skip,mkt=mkt)
	results = search_service.search(limit=50, format='json') #1-50
	
	return [res.url for res in results], search_service.totalEstimatedMatches, search_service.webSearchUrl #.decode('utf8')
	
	

if __name__ == "__main__":
	#print search('"kim gerdes"', 'f01034f73f0042e5b03b0dd3a5dca3b8', skip=2)
	print(search('"kim gerdes"', '8409cc774f804e06b2d0ce4a02fb5d84', skip=0))
	
