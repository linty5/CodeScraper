# -*- coding: utf-8 -*-
import shutil
import os
import re
import requests
from bs4 import BeautifulSoup
import time
import argparse
import json

from description_scraper import get_description
from testcases_scraper import get_testcases

def get_submission_ids(name, language, ver):
	
	# check your JSESSIONID and 39ce7 from cookies'''

	d = {'JSESSIONID': '38394F746A5A47E823B68D943B704931-n1', '39ce7': 'CFFq98Ot'}

	url = 'https://codeforces.com/contest/' + name[0] + '/status/page/1'

	print("url: ", url)

	c = requests.get(url, cookies = d)

	m = re.search('meta name="X-Csrf-Token" content="(.*)"', c.text)

	if not m:
		raise 'unable to get csrf token'

	csrf_token = m.groups(1)[0]

	language_dict = {'c': 'c.gcc11', 'c++': 'cpp.g++17', 'python3': 'python.3', 'python2': 'python.2',
		  			 'php': 'php.5', 'kotlin16': 'kotlin16', 'kotlin17': 'kotlin17', 'ruby': 'ruby.3',
					 'javascript': 'v8.3', 'nodejs': 'v8.nodejs', 'rust': 'rust.2021', 'java17': 'java17', 
		  			 'delphi': 'pas.dpr', 'perl': 'perl.5', 'd': 'd', 'haskell': 'haskell.ghc', 
					 'ocaml': 'ocaml', 'fpc': 'pas.fpc', 'pascalabc': 'pas.pascalabc'}
	
	if language not in language_dict:
		print("Haven't include this language --> ", language)

	# ver_default = 'anyVerdict'
	ver_dict = {'OK': 'OK',  'REJECTED': 'REJECTED', 'WA': 'WRONG_ANSWER', 'RE': 'RUNTIME_ERROR', 'TLE': 'TIME_LIMIT_EXCEEDED', 'MLE': 'MEMORY_LIMIT_EXCEEDED', 'CE': 'COMPILATION_ERROR'}

	print(language, " search, value: ", language_dict[language], " ver: ", ver_dict[ver])

	c = requests.post(url,
	data = {'csrf_token':csrf_token, 'action':'setupSubmissionFilter', 'frameProblemIndex':name[1], 
	 	    'verdictName':ver_dict[ver], 'programTypeForInvoker':language_dict[language], 
			'comparisonType':'NOT_USED', 'judgedTestCount':'', '_tta':'199'},  
	headers = {'X-Csrf-Token':csrf_token},
	cookies = d
	)

	page = requests.get(url, cookies = d)
	if str(page) == "<Response [503]>":
		while str(page) == "<Response [503]>":
			time.sleep(1)
			page = requests.get(url)

	html_content = page.text
	soup = BeautifulSoup(html_content, "html.parser") # making soap
	text = soup.select("body a")
	count = 0

	messages = []
	author_list = []
	message = []

	for row in text:
		raw = str(row)
		submissionid = re.search('submissionid="(.*)" t', raw)
		participantid = re.search('href="/profile/(.+?)" title', raw)

		if submissionid != None:
			sid = str(submissionid.group(1))
			message.append(sid)
		if participantid != None:
			pid = str(participantid.group(1))
			if len(message) > 0:
				if pid in author_list:
					message = []
					continue
				else:
					author_list.append(pid)
					message.append(pid)
					messages.append(message)
					message = []
					count += 1
					if count == 3:
						break

	return messages

def get_submissions(contest, messages, l, ver):
	submissions = {}
	for i in messages:
		data = get_submission(contest, i, l, ver)
		if data[2] == None:
			submissions[data[0]] = data[1]

	# #failed_to_download_s = []
	# with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
	# 	future_to_url = {executor.submit(get_solution, contest, i): i for i in solution_ids}
	# 	for future in concurrent.futures.as_completed(future_to_url):
	# 		print("------------future-----------", future)
	# 		data = future.result()

	# 		if data[2] == None:
	# 			solutions[data[0]] = data[1]

	return submissions

def get_submission(contest, messages, l, ver):
	submission_id = messages[0]
	participant_id = messages[1]

	url = 'http://codeforces.com/contest/' + str(contest[0]) + '/submission/' + str(submission_id)
	print(url)

	page = requests.get(url)
	if str(page) == "<Response [503]>":
		while str(page) == "<Response [503]>":
			time.sleep(1)
			page = requests.get(url)
	html_content = page.text

	# table_content = re.search('<div class="datatable""(.*?)</div>', html_content).group(1)

	soup = BeautifulSoup(html_content, "html.parser")

	text = soup.select("body > div > div > div > div > pre")

	failed_to_download = None
	submission = None


	if len(text)==0:
		failed_to_download = submission_id
	else:
		body = BeautifulSoup(str(text[0]), "html.parser").get_text()

		body = body.replace("\\","\\\\")
		submission = body.encode('utf-8').decode('unicode-escape')


	submission_content = {}

	submission_content["lang"] = l
	submission_content["source_code"] = submission

	submission_content["tags"] = contest[3]
	submission_content["lang_cluster"] = l
	submission_content["id"] = contest[0] + "-" + contest[1]
	submission_content["submission_id"] = str(submission_id)
	submission_content["participant_id"] = str(participant_id)
	submission_content["difficulty"] = contest[2]
	submission_content["exec_outcome"] = ver

	return submission_id, submission_content, failed_to_download

def download_descriptions_solutions(filename, index_n):
	root_dir = 'codeforces_data'
	exists_list = []
	check_flag = 1
	if os.path.exists(root_dir):
		exists_list = os.listdir(root_dir)

	with open(filename, 'r', encoding='utf-8') as f:
		content = json.load(f)

	all_infos = content["infos"]

	language = ["c++", "delphi", "perl", "d"] # "java17", "python3", "c++", "c"]

	for _, info in enumerate(all_infos):

		print("info: ", info)
		if check_flag:
			if (info[0] + "_" + info[1]) in exists_list:
				continue
			else:
				check_flag = 0
		descriptions, left_out, failed_to_download_d = get_description(info)
		if info not in left_out:
			if not os.path.exists(root_dir):
				os.makedirs(root_dir)

			save_dir = root_dir + "/" + info[0] + "_" + info[1]

			if not os.path.exists(save_dir):
				os.makedirs(save_dir)

			description_dir = save_dir + "/description"

			if not os.path.exists(description_dir):
				os.makedirs(description_dir)

			description_file_path = description_dir + "/description.json"

			with open(description_file_path, 'w', encoding='utf-8') as description_file:
				json.dump(descriptions, description_file)

			testcases_flag = 1

			for l in language:
					
				solution_dir = save_dir + "/" + l

				if not os.path.exists(solution_dir):
					os.makedirs(solution_dir)

				ver_simplelist = ['OK', 'REJECTED']
				# ver_list = ['OK', 'WA', 'RE', 'TLE', 'MLE', 'CE']

				messages_l = []

				for ver in ver_simplelist:
					
					submission_dir = solution_dir + "/" + ver

					messages = get_submission_ids(info, l, ver)
					messages_l.append(messages)

					print("messages: ", messages)
					submissions = get_submissions(info, messages, l, ver)
					
					print('len(submissions): ', len(submissions))

					if len(submissions) == 0:
						continue
					
					if testcases_flag:
						testcases_dir = save_dir + "/testcases"

						if not os.path.exists(testcases_dir):
							os.makedirs(testcases_dir)

						testcases_file_path = testcases_dir + "/testcases.json"

						testcases, failed_to_download_t = get_testcases(info, list(submissions.keys())[0])

						with open(testcases_file_path, 'w', encoding='utf-8') as testcases_file:
							json.dump(testcases, testcases_file)

						testcases_flag = 0

					if not os.path.exists(submission_dir):
						os.makedirs(submission_dir)

					for _, j in enumerate(submissions):
						submission_file_path = submission_dir + "/" + j + ".json"
						with open(submission_file_path, 'w', encoding='utf-8') as submission_file:
							json.dump(submissions[j], submission_file)

				if len(messages_l) == 0:
					shutil.rmtree(solution_dir)

		if len(failed_to_download_d) > 0:
			print("Following challenges failed to download descriptions: " + str(failed_to_download_d))

		if len(failed_to_download_t) > 0:
			print("Following submissions failed to download testcases: " + str(failed_to_download_t))
	
parser = argparse.ArgumentParser()
parser.add_argument('--index', type=str, default="0", help='')
args = parser.parse_args()

index_n = args.index

download_descriptions_solutions('challenges_sampled.json', index_n)

