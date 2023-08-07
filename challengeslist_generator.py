# -*- coding: utf-8 -*-
import re
import requests
from bs4 import BeautifulSoup
import time
import json
import random
from tqdm import *

def get_problem_list(url, content):
	
	page = requests.get(url)
	if str(page) == "<Response [503]>":
		while str(page) == "<Response [503]>":
			time.sleep(1)
			page = requests.get(url)
	html_content = page.text

	soup = BeautifulSoup(html_content, "html.parser") # making soap

	case = soup.select("body tr")

	for row in case:
		message = ""
		raw = str(row)
		body = re.search(' href="/problemset/problem/(.*)">', raw)
		if body != None:
			w = body.group(1)
			message = str(w)
			c = list(message.split('/'))

			difficulty = re.search('<span class="ProblemRating" title="Difficulty">(.*)</span>', raw)
			if difficulty != None:
				c.append(str(difficulty.group(1)))
			else:
				c.append(str(None))

			tags = re.findall('<a class="notice" href="/(.*)" style', raw)
			tags_clean = []
			for tag in tags:
				tags_clean.append(tag.split('=')[1])
			c.append(tags_clean)
			content["infos"].append(c)

	return content

def download_all_challenge_names(filename):
	content = {"infos":[]}

	for page_idx in tqdm(range(1,89)):
		page_url = 'http://codeforces.com/problemset/page/' + str(page_idx+1)
		content = get_problem_list(page_url, content)

	with open(filename, 'w', encoding='utf-8') as target:
		json.dump(content, target)

	random.shuffle(content["infos"])
	sampled_content = {"infos": content["infos"][:150]}

	with open('challenges_sampled.json', 'w', encoding='utf-8') as target:
		json.dump(sampled_content, target)

download_all_challenge_names('challenges_all.json')
