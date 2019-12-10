# -*- coding: utf-8 -*-

"""
Module computing the d3 graph for Nexico
"""

import codecs, sys, os, json, webbrowser
from PyQt5 import QtCore


debug=False
#debug=True

nex=None

class Collocations():
	"""
	Collocations
	"""
	def __init__(self, parent=None):
		"""
		Constructor	
		"""
		self.nexicoWindow=parent
		global nex
		nex=parent
		self.html=None
	
	def dive(self, toki, links, id2label, label2level,specollocs, idtotoken, bestkids, level, maxlevel):
		#graph.add_node(toki)
		slabel=idtotoken[toki]#.decode("utf-8")
		id2label[toki]=slabel
		
		label2level[slabel]=min(level,label2level.get(slabel,999))
		spid=[(sp,id) for (id, sp) in specollocs[toki].items() if sp!=0 ]
		
		for sp,id in sorted(spid,reverse=True)[:bestkids]:
		#for (id,sp) in specollocs[toki].iteritems():
				
				#graph.add_weighted_edges_from([ (toki,id,sp) ])
				tlabel=idtotoken[id]#.decode("utf-8")
				label2level[tlabel]=min(level+1,label2level.get(tlabel,999))
				links+=[{"source":slabel,"target":tlabel,"spec":sp, "type":"suit"} ]
				id2label[id]=tlabel
				if level<maxlevel:
					self.dive(id,links,id2label,label2level,specollocs,idtotoken,bestkids,level+1,maxlevel)

	
	def graph(self,nbBestKids=5):
		links=[]
		self.id2label={}
		label2level={}
		self.dive(self.nexicoWindow.selectedTokeni, links, self.id2label, label2level, self.nexicoWindow.sectrast.specollocs[self.nexicoWindow.ngra], self.nexicoWindow.base.d.idtotoken,nbBestKids,0,1)
		#.attr("r", function(d, i) {return 9-6/maxlevel*d.level; }) 
		#<div class="cog"> </div>
		#.cog {
				#background: url("quartercogtrans.png") no-repeat scroll right bottom rgba(0, 0, 0, 0)
				#z-index: -111; 
				#position:fixed;
				#width:100%;
				#height:175px;
				#bottom:0; left:0;
				#}
		
		self.html="""<!DOCTYPE html>
			<meta charset="utf-8">
			<head>
			<title>Gromoteur Nexico - Collocation Graph</title>
			
			<style>
			
			body {
				padding:0;
				margin:0;
				font-family:Helvetica, Arial, sans-serif;
				font-size:10px;
			}
			
			.link {
				fill: none;
				stroke: #666;
				stroke-width: 1.5px;
			}
			circle {
				fill: #ccc;
				stroke: #333;
				stroke-width: 1.5px;
			}
			circle:hover {
				stroke: orangered;
			}
			text {
				font: 10px sans-serif;
				pointer-events: none;
				text-shadow: 0 1px 0 #fff, 1px 0 0 #fff, 0 -1px 0 #fff, -1px 0 0 #fff;
			}

			</style>
			
			</head>
			<body>
			
			
			<script src="d3.v3.min.js"></script>
			<script language="JavaScript">
			
			var links = """+json.dumps(links)+""";
			var label2level = """+json.dumps(label2level)+""";


			var nodes = {};
			var maxlevel = 0
			// Compute the distinct nodes from the links.
			links.forEach(function(link) {
				link.source = nodes[link.source] || (nodes[link.source] = {name: link.source, level:label2level[link.source]});
				link.target = nodes[link.target] || (nodes[link.target] = {name: link.target, level:label2level[link.target]});
				maxlevel=Math.max(maxlevel,label2level[link.target["name"]]);
			});
			var width = window.innerWidth-20;
			height = document.documentElement.clientHeight-20;

			var force = d3.layout.force()
			.nodes(d3.values(nodes))
			.links(links)
			.size([width, height])
			.linkDistance(Math.min(window.innerWidth,window.innerHeight)/4)
			.charge(-300)
			.on("tick", tick)
			
			.start();

			var svg = d3.select("body").append("svg")
			.attr("width", width)
			.attr("height", height);

			// Per-type markers, as they don't inherit styles.
			svg.append("defs").selectAll("marker")
			.data(["suit", "licensing", "resolved"])
			.enter().append("marker")
			.attr("id", function(d) { return d; })
			.attr("viewBox", "0 -5 10 10")
			.attr("refX", 15)
			.attr("refY", -1.5)
			.attr("markerWidth", 6)
			.attr("markerHeight", 6)
			.attr("orient", "auto")
			.append("path")
			.attr("d", "M0,-5L10,0L0,5");

			var path = svg.append("g").selectAll("path")
			.data(force.links())
			.enter().append("path")
			.attr("class", function(d) { return "link " + d.type; })
			.style("stroke-width", function(d) { return ((1-(1/d.spec)))+"px"; })
			.attr("marker-end", function(d) { return "url(#" + d.type + ")"; });

			var circle = svg.append("g").selectAll("circle")
			.data(force.nodes())
			.enter().append("circle")
			.attr("r", 3)
			.style("fill", function(d, i) 
				{ 
					if (d.level==0) 	{return "#6284B7";} 
					else 		{return "#ccc"; }
				})
			.on("dblclick", function(d) {pyObj.recenter(d.name) })
			.call(force.drag);

			var text = svg.append("g").selectAll("text")
			.data(force.nodes())
			.enter().append("text")
			.attr("x", 8)
			.attr("y", ".31em")
			.text(function(d) { return d.name; });

			// Use elliptical arc path segments to doubly-encode directionality. path.style("stroke-width", "3px")
			function tick() {
			path.attr("d", linkArc);
			circle.attr("transform", transform);
			text.attr("transform", transform);
			}

			function linkArc(d) {
			var dx = d.target.x - d.source.x,
			dy = d.target.y - d.source.y,
			dr = Math.sqrt(dx * dx + dy * dy);
			return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,1 " + d.target.x + "," + d.target.y;
			}

			function transform(d) {
			return "translate(" + d.x + "," + d.y + ")";
			}
			
			</script>
			
			</body>
			"""
		
		
		
		
		return self.html
	
	def viewGraphInBrowser(self):
		resultFolder=os.path.join(os.path.expanduser('~'),"gromoteur","export-Nexico")
		if not os.path.isdir(resultFolder):
			try:
				os.makedirs(resultFolder)
			except OSError as exc: # Python >2.5
				print("Problem creating the designated export folder!")
				if exc.errno != errno.EEXIST: return
			except:
				print("Problem creating the designated export folder!")
		
		with codecs.open(os.path.join(resultFolder,"graph.html"),"w","utf-8") as out:
			out.write(self.html.replace("lib/images","images").replace("pyObj.recenter(d.name)","").replace("d3.v3.min.js","http://d3js.org/d3.v3.min.js"))
		filename=str(os.path.join(resultFolder,"graph.html"))
		webbrowser.open_new("file:///"+filename)
 
class RecenterClass(QtCore.QObject):  
	"""Simple class with one slot"""  
	#def __init__(self):
		#"""
		#Constructor	
		#"""
		#super(RecenterClass, self).__init__()
		#self.word=None
		
	@QtCore.pyqtSlot(str)  
	def recenter(self, word): 
		"""
		function called by javascript from the webview
		"""
		#if word == self.word: 
			#print "word",word,"already"
			##sleep(1)
			#return
		#self.word = word
		global nex # a very bad way of getting an instance into this abstract class :-s
		#print "\n\nword",word,nex
		#QtGui.QMessageBox.information(None, "Info", word)  
		nex.autoSelect+=1
		#if nex.autoSelect>1:
			#nex.autoSelect=0
			##sleep(1)

			#return
		nex.selectWordInWordTableWidget(str(word))
		#print "999"
		#sleep(1)

		#nex.makeCollocGraph()
		nex.autoSelect=0
		
		#print 9999
		


	
if __name__ == "__main__":	
	sys.exit()
	
	
	
	
