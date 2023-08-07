# -*- coding: utf-8 -*-
import shutil
import os
import re
import requests
from bs4 import BeautifulSoup
import time
import argparse
import json

def sub_strip(matchobj):   
    return matchobj.group(0).replace(u"\u2009", "")


def get_submission_ids(name, language, ver):
	
	# check your JSESSIONID and 39ce7 from cookies'''

	d = {'JSESSIONID': '38394F746A5A47E823B68D943B704931-n1', '39ce7': 'CFFq98Ot'}

	url = 'https://codeforces.com/contest/' + name[0] + '/status/page/'

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
	# ver_simpledict = {'OK': 'OK', 'REJECTED': 'REJECTED'}
	ver_dict = {'OK': 'OK', 'WA': 'WRONG_ANSWER', 'RE': 'RUNTIME_ERROR', 'TLE': 'TIME_LIMIT_EXCEEDED', 'MLE': 'MEMORY_LIMIT_EXCEEDED', 'CE': 'COMPILATION_ERROR'}

	print(language, " search, value: ", language_dict[language], " ver: ", ver_dict[ver])

	c = requests.post(url,
	data = {'csrf_token':csrf_token, 'action':'setupSubmissionFilter', 'frameProblemIndex':str(name[1]), 
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

	messages = []

	text = soup.select("body a")

	count = 0

	for row in text:
		message = ""
		raw = str(row)
		body = re.search('submissionid="(.*)" t', raw)

		if body != None:
			w = body.group(1)
			message = str(w)
			messages.append(message)
			count += 1
			if count == 3:
				break

	return messages

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

	w = w.replace("\\","\\\\")

	w = w.replace("\xe2"," ")
	w = w.replace("\xc2"," ")
	w = w.replace("\u2009","")

	# content = w.encode('utf-8').decode('unicode-escape')

	return w


def get_description(info):
	descriptions = {}
	left_out = []
	failed_to_download_d = []

	url = 'http://codeforces.com/contest/' + str(info[0]) + '/problem/' + str(info[1])
	# https://codeforces.com/contest/2/problem/B

	page = requests.get(url)

	if str(page) == "<Response [503]>":
		while str(page) == "<Response [503]>":
			time.sleep(1)
			page = requests.get(url)

	html_content = page.text

	if re.search('"message":"requests limit exhausted"', html_content) != None:
		while re.search('message":"requests limit exhausted', html_content) != None:
			time.sleep(1)
			page = requests.get(url)
			html_content = page.text

	if html_content==None:
		failed_to_download_d.append(info)

	# html_content = html_content.encode('utf-8').decode('unicode-escape')

	if re.search('src="http://codeforces.com/predownloaded', html_content.replace("\\", "")) == None and re.search('src="http://espresso.codeforces.com', html_content.replace("\\", "")) == None and re.search('"message":"Problem is not visible now. Please try again later."', html_content) == None and re.search('Statement is not available', html_content) == None:
		
		# body = re.findall('</div></div><div>(.+?)<script type="text/javascript">', html_content, flags=re.S)
		
		body = re.search('<div class="problem-statement">(.*)</div>', html_content).group(1)

		descriptions["title"] = re.search('<div class="title">(.*?)</div>', body).group(1)
		descriptions["description"] = convert_text(re.search('</div></div><div><p>(.*?)<div class="input-specification">', body).group(1))
		descriptions["input_from"] = re.search('input</div>(.*?)</div>', body).group(1)
		descriptions["output_to"] = re.search('output</div>(.*?)</div>', body).group(1)
		descriptions["time_limit"] = re.search('time limit per test</div>(.*?)</div>', body).group(1)
		descriptions["memory_limit"] = re.search('memory limit per test</div>(.*?)</div>', body).group(1)
		descriptions["input_spec"] = convert_text(re.search('<div class="section-title">Input</div><p>(.*?)</div>', body).group(1))
		descriptions["output_spec"] = convert_text(re.search('<div class="section-title">Output</div><p>(.*?)</div>', body).group(1))
		descriptions["notes"] = convert_text(re.search('<div class="section-title">Note</div>(.*?)</div>', body).group(1))
		
		sample_inputs_list = re.findall('<div class="title">Input</div><pre>(.*?)</pre></div>', body)
		descriptions["sample_inputs"] = []
		for sample_inputs in sample_inputs_list:
			descriptions["sample_inputs"].append(convert_text(sample_inputs))
		
		sample_outputs_list = re.findall('<div class="title">Output</div><pre>(.*?)</pre></div>', body)
		descriptions["sample_outputs"] = []
		for sample_outputs in sample_outputs_list:
			descriptions["sample_outputs"].append(convert_text(sample_outputs))
		
		descriptions["id"] = info[0] + "-" + info[1]
		descriptions["difficulty"] = info[2]
		descriptions["tags"] = info[3]

	else:
		left_out.append(info)

	return descriptions, left_out, failed_to_download_d


def get_submissions(contest, submission_ids, l, ver):
	submissions = {}
	for i in submission_ids:
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

def get_submission(contest, submission_id, l, ver):
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
	submission_content["difficulty"] = contest[2]
	submission_content["exec_outcome"] = ver

	return submission_id, submission_content, failed_to_download

def download_descriptions_solutions(filename, index_n):
	root_dir = 'codeforces_data'

	with open(filename, 'r', encoding='utf-8') as f:
		content = json.load(f)

	all_infos = content["infos"]

	language = ["delphi"] # , "perl", "d", "java17", "python3", "c++", "c"]

	for _, info in enumerate(all_infos):

		print("info: ", info)
		descriptions, left_out, failed_to_download_d = get_description(info)
		if info not in left_out:
			if not os.path.exists(root_dir):
				os.makedirs(root_dir)

			'''
			cat_dir = root_dir + "/" + category

			if not os.path.exists(cat_dir):
			    os.makedirs(cat_dir)

			save_dir = cat_dir + "/" + i
			#'''

			save_dir = root_dir + "/" + info[0] + "_" + info[1]

			#'''
			if not os.path.exists(save_dir):
				os.makedirs(save_dir)

			description_dir = save_dir + "/description"

			if not os.path.exists(description_dir):
				os.makedirs(description_dir)

			description_file_path = description_dir + "/description.json"

			with open(description_file_path, 'w', encoding='utf-8') as description_file:
				json.dump(descriptions, description_file)

			for l in language:
					
				solution_dir = save_dir + "/" + l

				if not os.path.exists(solution_dir):
					os.makedirs(solution_dir)

				# ver_simplelist = ['OK', 'REJECTED']
				ver_list = ['OK', 'WA', 'RE', 'TLE', 'MLE', 'CE']

				ids_l = []

				for ver in ver_list:
					
					submission_dir = solution_dir + "/" + ver

					ids = get_submission_ids(info, l, ver)
					ids_l.append(ids)

					print("ids: ", ids)
					submissions = get_submissions(info, ids, l, ver)
					
					print('len(submissions): ', len(submissions))

					if len(submissions) == 0:
						continue

					if not os.path.exists(submission_dir):
						os.makedirs(submission_dir)

					for _, j in enumerate(submissions):
						submission_file_path = submission_dir + "/" + j + ".txt"
						with open(submission_file_path, 'w', encoding='utf-8') as submission_file:
							json.dump(submissions[j], submission_file)

						# if len(submissions[j]) < 10000:
						# 	submission_file_path = submission_dir + "/" + j + ".txt"
						# 	submission_file = open(submission_file_path, 'w', encoding = 'utf-8')
						# 	submission_file.write(submissions[j])

				if len(ids_l) == 0:
					shutil.rmtree(solution_dir)

		if len(failed_to_download_d) > 0:
			print("Following challenges failed to download: " + str(failed_to_download_d))
	
parser = argparse.ArgumentParser()
parser.add_argument('--index', type=str, default="0", help='')
args = parser.parse_args()

index_n = args.index

download_descriptions_solutions('challenges_sampled.json', index_n)

