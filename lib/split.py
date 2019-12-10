# -*- coding: utf-8 -*-

import codecs, re

renum=re.compile(r"^\d+$", re.U)
c=0
currout=codecs.open("hitch."+str(c).zfill(3)+".txt", "w", "utf-8")
lastempty=True
for li in codecs.open("hitch.txt"):
	if renum.match(li.strip()):
		currout.close()
		c+=1
		currout=codecs.open("hitch."+str(c).zfill(3)+".txt", "w", "utf-8")
	if li.strip():
		currout.write(li)
		lastempty=False
	else:
		if not lastempty:currout.write(li)
		lastempty=True
currout.close()
