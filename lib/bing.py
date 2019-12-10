# -*- coding: utf-8 -*-

import requests, requests.utils, re #, urllib.parse , urllib.errorurllib.request, 
from .py_ms_cognitive_search import PyMsCognitiveSearch


if False:
	import http.client, urllib.parse, json

	# **********************************************
	# *** Update or verify the following values. ***
	# **********************************************

	# Replace the subscriptionKey string value with your valid subscription key.
	subscriptionKey = "8409cc774f804e06b2d0ce4a02fb5d84"

	# Verify the endpoint URI.  At this writing, only one endpoint is used for Bing
	# search APIs.  In the future, regional endpoints may be available.  If you
	# encounter unexpected authorization errors, double-check this value against
	# the endpoint for your Bing Web search instance in your Azure dashboard.
	host = "api.cognitive.microsoft.com"
	path = "/bing/v7.0/search"

	term = "Microsoft Cognitive Services"

	def BingWebSearch(search):
		"Performs a Bing Web search and returns the results."

		headers = {'Ocp-Apim-Subscription-Key': subscriptionKey}
		conn = http.client.HTTPSConnection(host)
		query = urllib.parse.quote(search)
		conn.request("GET", path + "?q=" + query, headers=headers)
		response = conn.getresponse()
		headers = [k + ": " + v for (k, v) in response.getheaders()
				if k.startswith("BingAPIs-") or k.startswith("X-MSEdge-")]
		return headers, response.read()#.decode("utf8")

	if len(subscriptionKey) == 32:

		print(('Searching the Web for: ', term))

		headers, result = BingWebSearch(term)
		print("\nRelevant HTTP Headers:\n")
		print(("\n".join(headers)))
		print("\nJSON Response:\n")
		print((json.dumps(json.loads(result), indent=4)))

	else:

		print("Invalid Bing Search API subscription key!")
		print("Please paste yours into the source code.")












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
	
	return [res.url for res in results], search_service.totalEstimatedMatches, search_service.webSearchUrl # .decode('utf8')
	
	

if __name__ == "__main__":
	#print search('"kim gerdes"', 'f01034f73f0042e5b03b0dd3a5dca3b8', skip=2)
	print(search('"kim gerdes"', '8409cc774f804e06b2d0ce4a02fb5d84', skip=0))
	
	
def oldsearch(query,accountkey,location=None, skip=0):
	"""
	azure V2
	"""
	import urllib.request, urllib.parse, urllib.error,urllib.request,urllib.error,urllib.parse, base64

	from xml.dom.minidom import parseString

	if not location or location=="automatic location detection":location=""
	else:location = "&Market=%27{location}%27".format(location=location)
	url='https://api.datamarket.azure.com/Data.ashx/Bing/Search/v1/Composite?Sources=%27web%27&'
	query=query.encode("utf-8")
	url+=str(urllib.parse.urlencode({'Query': "'"+query+"'",'Adult':"'off'"}) )
	url+='&$top=50{location}&Options=%27DisableLocationDetection%27&$skip={skip}&$format=Atom'.format(skip=skip, location=str(location))
	if verbose:
		print("search:",  url,  accountkey)	
		print(location)

	password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
	password_mgr.add_password(None, url," ",accountkey)
	handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
	opener = urllib.request.build_opener(handler)
	urllib.request.install_opener(opener)
	#print url
	request = urllib.request.Request(url)
	
	#		base64string = base64.encodestring('%s:%s' % ("", accountkey )).replace('\n', '')
	#		request.add_header("Authorization", "Basic %s" % base64string)   
	result = urllib.request.urlopen(request)
	xml = result.read()
	dom = parseString(xml)
	if verbose>1: print(dom.toprettyxml())
	links=[node.firstChild.data for node in dom.getElementsByTagName('d:Url')]
	total=int([node.firstChild.data for node in dom.getElementsByTagName('d:WebTotal')][0])
	if verbose: print(len(links), "results")
	return links, total

	#links, total = search("gerdes","/oQLMwXhI0Ygpz/1Ma/Oce+VrWJL3mbjsJL4aA3Jo78=",0)
	#print links, total
