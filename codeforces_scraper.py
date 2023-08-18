# -*- coding: utf-8 -*-
import shutil
import os
import re
import requests
from bs4 import BeautifulSoup
import time
import argparse
import json
import concurrent.futures

from description_scraper import get_description
from testcases_scraper import get_testcases

def get_submission_ids(name, language, ver):
	
	# check your JSESSIONID and 39ce7 from cookies'''
	# JSESSIONID=BA4D5B876D89A91157BA703D813C2546-n1; 39ce7=CF1rNf9Q

	d = {'JSESSIONID': 'BA4D5B876D89A91157BA703D813C2546-n1', '39ce7': 'CF1rNf9Q'}

	url = 'https://codeforces.com/contest/' + name[0] + '/status/page/1'

	print("url: ", url)

	c = requests.get(url, cookies = d)
	m = re.search('meta name="X-Csrf-Token" content="(.*)"', c.text)

	if not m:
		print('unable to get csrf token')
		time.sleep(300)
		return [], True


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

	return messages, False

def get_submissions(contest, messages, l, ver, args):
	submissions = {}
	# num_workers = args.num_workers

	# if num_workers > 1:
	# 	with concurrent.futures.ProcessPoolExecutor(num_workers) as executor:
	# 		future_to_url = {executor.submit(get_submission, contest, i, l, ver): i for i in messages}
	# 		for future in concurrent.futures.as_completed(future_to_url):
	# 			data = future.result()
	# 			if data[2] == None:
	# 				submissions[data[0]] = data[1]
	# else:
	for i in messages:
		data = get_submission(contest, i, l, ver)
		if data[2] == None:
			submissions[data[0]] = data[1]

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

	soup = BeautifulSoup(html_content, "html.parser")
	table_content = str(soup.find('table'))
	text = soup.select("body > div > div > div > div > pre")

	table_list = re.findall('<td>(.*?)</td>', table_content, re.DOTALL)

	failed_to_download = None
	submission = None

	if len(text)==0:
		failed_to_download = submission_id
	else:
		body = BeautifulSoup(str(text[0]), "html.parser").get_text()
		body = body.replace("\\","\\\\")
		submission = body.encode('utf-8').decode('unicode-escape')


	submission_content = {}

	try:
		submission_content["lang"] = table_list[3].strip()
		submission_content["verdict"] = re.search('>(.*?)</span>', table_list[4]).group(1)
		submission_content["time"] = table_list[5].strip()
		submission_content["memory"] = table_list[6].strip()
		submission_content["sent"] = table_list[7].strip()
		submission_content["judged"] = table_list[8].strip()

		submission_content["source_code"] = submission
		submission_content["tags"] = contest[3]
		submission_content["lang_cluster"] = l
		submission_content["id"] = contest[0] + "-" + contest[1]
		submission_content["submission_id"] = str(submission_id)
		submission_content["participant_id"] = str(participant_id)
		submission_content["difficulty"] = contest[2]
		submission_content["exec_outcome"] = ver
	except:
		failed_to_download = submission_id

	return submission_id, submission_content, failed_to_download

def download_descriptions_solutions(filename, args):
	root_dir = args.root_dir
	if not os.path.exists(root_dir):
		os.makedirs(root_dir)

	continue_flag = args.continue_flag
	clean_fail = args.clean_fail

	exists_list = []
	if os.path.exists(root_dir):
		exists_list = os.listdir(root_dir)

	with open(filename, 'r', encoding='utf-8') as f:
		content = json.load(f)

	all_infos = content["infos"]

	if clean_fail:
		fail_dir = root_dir + "/fail/"
		if os.path.exists(fail_dir):
			fail_list = os.listdir(fail_dir)
			all_infos = [x for x in all_infos if (str(x[0]) + ".txt") not in fail_list]

	failed_to_download_d, failed_to_download_t = [], []

	language = ["c++", "delphi", "perl", "d"] # "java17", "python3", "c++", "c"]

	for _, info in enumerate(all_infos):

		print("info: ", info)
		if continue_flag:
			if (info[0] + "_" + info[1]) in exists_list:
				continue
			else:
				continue_flag = 0
		descriptions, left_out, failed_to_download_d = get_description(info)
		if info not in left_out and info not in failed_to_download_d:

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

					messages, fail_flag = get_submission_ids(info, l, ver)
					if fail_flag:
						continue
					messages_l.append(messages)

					print("messages: ", messages)
					submissions = get_submissions(info, messages, l, ver, args)
					
					print('len(submissions): ', len(submissions))

					if len(submissions) == 0:
						print("fail to download submission", messages)
						# time.sleep(args.common_wait)
						continue
					
					if testcases_flag:
						testcases_dir = save_dir + "/testcases"

						if not os.path.exists(testcases_dir):
							os.makedirs(testcases_dir)

						testcases_file_path = testcases_dir + "/testcases.json"

						testcases, failed_to_download_t = get_testcases(info, list(submissions.keys())[0])

						if len(failed_to_download_t) > 0:
							print("fail to download testcase ", info)
							time.sleep(args.fail_wait)

						else:
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
		
		else:
			print("fail to download description ", info)

			fail_dir = root_dir + "/fail/"

			if not os.path.exists(fail_dir):
				os.makedirs(fail_dir)
			
			f = open(fail_dir + str(info[0]) + ".txt", "w")
			f.close()
			
		time.sleep(args.common_wait)

	if len(failed_to_download_d) > 0:
		print("Following challenges failed to download descriptions: " + str(failed_to_download_d))

	if len(failed_to_download_t) > 0:
		print("Following submissions failed to download testcases: " + str(failed_to_download_t))
		
	
parser = argparse.ArgumentParser()
parser.add_argument('--root_dir', type=str, default='codeforces_data_5', help='')
# parser.add_argument('--num_workers', type=str, default=1, help='')
parser.add_argument('--common_wait', type=int, default=60, help='')
parser.add_argument('--fail_wait', type=int, default=300, help='')
parser.add_argument('--continue_flag', type=bool, default=True, help='')
parser.add_argument('--clean_fail', type=bool, default=True, help='')

args = parser.parse_args()

download_descriptions_solutions('challenges_sampled_5.json', args)

