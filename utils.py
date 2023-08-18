# -*- coding: utf-8 -*-
import re
from bs4 import BeautifulSoup


def sub_strip(matchobj):   
    return matchobj.group(0).replace(u"\u2009", "")

def convert_text(w):
	w = w.replace('class="upper-index">', 'class="upper-index">^')

	'''NEED TO PUT PUT CODE HERE TO REMOVE SPACES IN NEGATIVE EXPONENTS'''
	w = re.sub('class="upper-index">(.+?)</sup>', sub_strip, w, re.S)

	w = w.replace("</p>", "\n</p>")
	w = w.replace("<br", "\n<br")

	w = w.replace("</div>", "\n</div>")
	w = w.replace("</center>", "\n</center>")

	w = BeautifulSoup(w, "html.parser").get_text()
	w = w.replace("All submissions for this problem are available.", "")

	w = re.sub('Read problems statements in (.+?)\\\\n', '', w, re.M)
	w = re.sub('Subtasks(.+?)Example', 'Example', w, re.S)

	w = w.replace("\u003C","<")
	w = w.replace("\u003E",">")

	w = w.replace("\n\n\n\n\n\n","\n\n\n")
	w = w.replace("\n\n\n\n","\n\n\n")

	# w = w.replace("\\","\\\\")

	w = w.replace("\xe2"," ")
	w = w.replace("\xc2"," ")
	w = w.replace("\u2009","")

	# content = w.encode('utf-8').decode('unicode-escape')

	return w
