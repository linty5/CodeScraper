# -*- coding: utf-8 -*-
import re
import requests
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_testcases(info, submission):
	testcases = {}
	testcases[str(info[0] + "_" + info[1])] = []
	failed_to_download_t = []

	url = 'http://codeforces.com/contest/' + str(info[0]) + '/submission/' + str(submission)
	# https://codeforces.com/contest/120/submission/217607666

	# (".click-to-view-tests").click

	chrome_driver_path = "E:\chromedriver-win64\chromedriver.exe" 

	chrome_options = webdriver.ChromeOptions()
	chrome_options.add_argument('--headless')
	chrome_options.add_argument('--disable-web-security') 
	chrome_options.add_argument('--ignore-certificate-errors')  
	chrome_options.add_argument('--allow-running-insecure-content')
	driver = webdriver.Chrome(executable_path=chrome_driver_path, options=chrome_options)

	driver.get(url)

	wait = WebDriverWait(driver, 1)
	click_link = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'click-to-view-tests')))
	click_link.click()

	time.sleep(1)
	tests_placeholder = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'tests-placeholder')))
	expanded_content = tests_placeholder.get_attribute('innerHTML')

	if expanded_content==None:
		failed_to_download_t.append(info)
		return testcases, failed_to_download_t

	# html_content = html_content.encode('utf-8').decode('unicode-escape')
	
	input_list = re.findall('<pre class="input">(.+?)</pre>', expanded_content, re.DOTALL)
	answer_list = re.findall('<pre class="answer">(.+?)</pre>', expanded_content, re.DOTALL)
	time_list = re.findall('<span class="timeConsumed">(.+?)</span>', expanded_content, re.DOTALL)
	mem_list = re.findall('<span class="memoryConsumed">(.+?)</span>', expanded_content, re.DOTALL)

	for i in range(1, len(time_list)):
		tmp = {"input":[], "answer":[], "time":[], "mem":[]}
		tmp["input"].append(input_list[i])
		tmp["answer"].append(answer_list[i])
		tmp["time"].append(time_list[i])
		tmp["mem"].append(mem_list[i])
		testcases[str(info[0] + "_" + info[1])].append(tmp)

	driver.quit()

	return testcases, failed_to_download_t