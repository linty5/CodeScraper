# -*- coding: utf-8 -*-
import re
import requests
from bs4 import BeautifulSoup
import time

def get_problem_list(url):
	page = requests.get(url)
	if str(page) == "<Response [503]>":
		while str(page) == "<Response [503]>":
			time.sleep(1)
			page = requests.get(url)
	html_content = page.text

	soup = BeautifulSoup(html_content, "html.parser") # making soap

	messages = []

	text = soup.select("body a")

	for row in text:
		message = ""
		raw = str(row)
		body = re.search(' href="/problemset/problem/(.*)">', raw)

		if body != None:
			w = body.group(1)
			message = str(w)
			c = message.split('/')
			messages.append(c)

	return messages

def download_all_challenge_names(filename):
	target = open(filename, 'w')

	problem_list = []

	for i in range(0,89):
		a = 'http://codeforces.com/problemset/page/' + str(i+1)
		l = get_problem_list(a)
		for jdx, j in enumerate(l):
			if jdx % 2 == 0:
				problem_list.append(j)
	target.write(str(problem_list))

download_all_challenge_names('challenges_all.txt')