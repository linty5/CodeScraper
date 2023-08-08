# -*- coding: utf-8 -*-
import re
import requests
import time

from utils import convert_text

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
		notes = re.search('<div class="section-title">Note</div>(.*?)</div>', body)
		if notes != None:
			descriptions["notes"] = convert_text(notes.group(1))
		
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