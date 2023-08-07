# -*- coding: utf-8 -*-
import re
import requests
from bs4 import BeautifulSoup
import time
import random
from tqdm import *

def get_problem_list(url):
	page = requests.get(url)
	if str(page) == "<Response [503]>":
		while str(page) == "<Response [503]>":
			time.sleep(1)
			page = requests.get(url)
	html_content = page.text

	soup = BeautifulSoup(html_content, "html.parser") # making soap

	messages = []

	case = soup.select("body tr")

	for row in case:
		message = ""
		raw = str(row)
		body = re.search(' href="/problemset/problem/(.*)">', raw)
		if body != None:
			w = body.group(1)
			message = str(w)
			c = message.split('/')

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

			messages.append(c)
	return messages

def download_all_challenge_names(filename):
	target = open(filename, 'w')

	problem_list = []

	for i in tqdm(range(0,89)):
		a = 'http://codeforces.com/problemset/page/' + str(i+1)
		l = get_problem_list(a)
		for jdx, j in enumerate(l):
			if jdx % 2 == 0:
				problem_list.append(j)

	random.shuffle(problem_list)
	target.write(str(problem_list[:150]))

# download_all_challenge_names('challenges_all.txt')

download_all_challenge_names('challenges_sampled.txt')