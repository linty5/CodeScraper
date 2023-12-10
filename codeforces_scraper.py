# -*- coding: utf-8 -*-
import shutil
import os
import re
import requests
from bs4 import BeautifulSoup
import time
import argparse
import json
import func_timeout
from func_timeout import func_set_timeout
# import concurrent.futures

from description_scraper import get_description
from testcases_scraper import get_testcases

def get_submission_ids(args, name, language, ver):
	
	# check your JSESSIONID and 39ce7 from cookies'''
	d = {'JSESSIONID': '32495D9A74CBDAAE4711E60BCBF95F75-n1', '39ce7': 'CFlhlxqQ'}

	url = 'https://codeforces.com/contest/' + name[0] + '/status/page/1'

	print("url: ", url)

	c = requests.get(url, cookies = d)
	m = re.search('meta name="X-Csrf-Token" content="(.*)"', c.text)

	if not m:
		print('unable to get csrf token')
		time.sleep(args.common_wait)
		return [], True


	csrf_token = m.groups(1)[0]
	print("csrf_token: ", csrf_token)

	language_dict = {'c': ['c.gcc11'], 
				  	 'c++': ["cpp.clang++-c++20-diagnose", "cpp.clang++-diagnose", "cpp.g++14", 'cpp.g++17', "cpp.gcc11-64-winlibs-g++20", "cpp.ms2017", "cpp.msys2-mingw64-9-g++17"], 
				     'csharp': ["csharp.dotnet-core", "csharp.dotnet-sdk-6", "csharp.mono"],
					 'd': ['d'], 
					 'go':["go"],
 					 'haskell': ['haskell.ghc'], 
					 'java': ["java11", "java17", "java21", "java8"],
					 'kotlin': ["kotlin16", 'kotlin17'],
					 'ocaml': ["ocaml"],
					 'delphi': ['pas.dpr'], 
					 'pas': ['pas.fpc', "pas.pascalabc"],
					 'perl': ['perl.5'],
					 'php': ['php.5'], 
					 'python': ['python.3', 'python.2', "python.pypy2", "python.pypy3", "python.pypy3-64"],
					 'ruby': ['ruby.3'],
					 'rust': ['rust.2021'], 
					 'scala': ["scala"],
					 'javascript': ['v8.3'], 
					 'nodejs': ["v8.nodejs"]}

	
	if language not in language_dict:
		print("Haven't include this language --> ", language)

	count = 0

	for l in language_dict[language]:
		if count == 5:
			break
		# ver_default = 'anyVerdict'
		ver_dict = {'OK': 'OK',  'REJECTED': 'REJECTED', 'WA': 'WRONG_ANSWER', 'RE': 'RUNTIME_ERROR', 'TLE': 'TIME_LIMIT_EXCEEDED', 'MLE': 'MEMORY_LIMIT_EXCEEDED', 'CE': 'COMPILATION_ERROR'}

		print(language, " search, value: ", l, " ver: ", ver_dict[ver])

		c = requests.post(
			url,
			data = {'csrf_token':csrf_token, 'action':'setupSubmissionFilter', 'frameProblemIndex':name[1], 
					'verdictName':ver_dict[ver], 'programTypeForInvoker':l, 
					'comparisonType':'NOT_USED', 'judgedTestCount':'', '_tta':'199'},  
			# headers = {'X-Csrf-Token':csrf_token},
			headers = {'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"},
			cookies = d
		)
		
		if c.status_code != 200:
			print('detected')
			time.sleep(args.fail_wait)
			return [], True

		page = requests.get(url, cookies = d)
		if str(page) == "<Response [503]>":
			while str(page) == "<Response [503]>":
				time.sleep(1)
				page = requests.get(url)

		html_content = page.text
		soup = BeautifulSoup(html_content, "html.parser")
		text = soup.select("body a")

		messages = []
		author_list = []
		message = []

		cur_count = 0

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
						cur_count += 1
						if cur_count == 3:
							break
		
		count += cur_count
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


@func_set_timeout(1500)
def each_language(args, save_dir, info, l, testcases_flag):
	solution_dir = save_dir + "/" + l

	if not os.path.exists(solution_dir):
		os.makedirs(solution_dir)

	ver_simplelist = ['OK', 'REJECTED']
	# ver_list = ['OK', 'WA', 'RE', 'TLE', 'MLE', 'CE']

	messages_l = []

	for ver in ver_simplelist:
		
		submission_dir = solution_dir + "/" + ver

		messages, fail_flag = get_submission_ids(args, info, l, ver)
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
			failed_to_download_t = []

			repeat_time = 0 + args.repeat_time

			while(repeat_time):
				testcases, failed_to_download_t = get_testcases(info, list(submissions.keys())[0])
				repeat_time -= 1
				if len(failed_to_download_t) > 0:
					print("fail to download testcase ", info)
					time.sleep(args.fail_wait)
				else:
					with open(testcases_file_path, 'w', encoding='utf-8') as testcases_file:
						json.dump(testcases, testcases_file)
					break

			testcases_flag = 0

		if not os.path.exists(submission_dir):
			os.makedirs(submission_dir)

		for _, j in enumerate(submissions):
			submission_file_path = submission_dir + "/" + j + ".json"
			with open(submission_file_path, 'w', encoding='utf-8') as submission_file:
				json.dump(submissions[j], submission_file)

	if len(messages_l) == 0:
		shutil.rmtree(solution_dir)
	
	return testcases_flag

def download_descriptions_solutions(filename, args):
	root_dir = args.root_dir
	if not os.path.exists(root_dir):
		os.makedirs(root_dir)
		
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
			all_infos = [x for x in all_infos if (x[0] + "_" + x[1] + ".txt") not in fail_list]
			
	failed_to_download_d, failed_to_download_t = [], []

	# language_dict = {'c': ['c.gcc11', ], 
	# 			  	 'c++': ["cpp.clang++-c++20-diagnose", "cpp.clang++-diagnose", "cpp.g++14", 'cpp.g++17', "cpp.gcc11-64-winlibs-g++20", "cpp.ms2017", "cpp.msys2-mingw64-9-g++17"], 
	# 			     'csharp': ["csharp.dotnet-core", "csharp.dotnet-sdk-6", "csharp.mono"],
	# 				 'd': ['d'], 
	# 				 'go':["go"],
 	# 				 'haskell': ['haskell.ghc'], 
	# 				 'java': ["java11", "java17", "java21", "java8"],
	# 				 'kotlin': ["kotlin16", 'kotlin17'],
	# 				 'ocaml': ["ocaml"],
	# 				 'delphi': ['pas.dpr'], 
	# 				 'pas': ['pas.fpc', "pas.pascalabc"],
	# 				 'perl': ['perl.5'],
	# 				 'php': ['php.5'], 
	# 				 'python': ['python.3', 'python.2', "python.pypy2", "python.pypy3", "python.pypy3-64"],
	# 				 'ruby': ['ruby.3'],
	# 				 'rust': ['rust.2021'], 
	# 				 'scala': ["scala"],
	# 				 'javascript': ['v8.3'], 
	# 				 'nodejs': ["v8.nodejs"]}


	language = ["python", "c", "csharp", "ruby", "go", "kotlin", "php", "rust", "javascript", "nodejs", "perl"]

	for _, info in enumerate(all_infos):

		if (info[0] + "_" + info[1]) in exists_list:
			print("completed info: ", info)
			continue
		else:
			print("start info: ", info)
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
				try:
					testcases_flag = each_language(args, save_dir, info, l, testcases_flag)
					time.sleep(args.common_wait)
				except func_timeout.exceptions.FunctionTimedOut:
					print(l, " time out")
				
		else:
			print("fail to download description ", info)

			fail_dir = root_dir + "/fail/"
			if not os.path.exists(fail_dir):
				os.makedirs(fail_dir)
			f = open(fail_dir + str(info[0]) + "_" + info[1] + ".txt", "w")
			f.close()
			
			time.sleep(args.fail_wait)

	if len(failed_to_download_d) > 0:
		print("Following challenges failed to download descriptions: " + str(failed_to_download_d))

	if len(failed_to_download_t) > 0:
		print("Following submissions failed to download testcases: " + str(failed_to_download_t))
		
	
parser = argparse.ArgumentParser()
parser.add_argument('--root_dir', type=str, default='codeforces_data', help='The folder where the collected data is stored.')
parser.add_argument('--common_wait', type=int, default=30, help='Interval between collection of each language')
parser.add_argument('--fail_wait', type=int, default=300, help='Waiting interval for recapture after being monitored by the website')
parser.add_argument('--clean_fail', type=bool, default=True, help='Whether or not to skip data that failed to be collected')
parser.add_argument('--repeat_time', type=int, default=3, help='The total number of re-attempts to collect testcases after failing to do so.')
# parser.add_argument('--num_workers', type=str, default=1, help='')

args = parser.parse_args()

download_descriptions_solutions('challenges_all.json', args)

