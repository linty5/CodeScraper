# Code Scraper for Chanllenges (CSC)

code used for scraping contest codes

based on [Description2Code scraper](https://github.com/ethancaballero/description2code). Thanks a lot!:heart:

this project only support codeforces as source now

## Overview

The following code files are included, each serving the following purposes:<br>
- challengeslist_generator.py<br>
  Generate a to-be-collected list corresponding to the existing problems on the target site, and generate a json file after running it
- codeforces_scraper.py<br>
  The main collection code, when run, calls description_scraper.py and testcases_scraper.py
- description_scraper.py<br>
  Implementation of the function to collect the content of the problem
- testcases_scraper.py<br>
  Implementation of the function to collect the testcases of the problem
- utils.py<br>
  Implementation of the text content conversion function


## How to use

1. Please run challengeslist_generator.py first to generate current challenges list on codeforces.com. A json named challenges_all.json including problem name, difficulty and tags will be generated.<br>
2. Before you run codeforces_scraper.py, you need to download chrome and the corresponding version of chrome driver:<br>
    (1) To use chrome and driver for acquisition, you need to download the chrome driver. In addition to downloading chrome, you also need to download the chrome driver with the corresponding version number. enter chrome://version/ in the chrome address bar to check the version information, such as 117.0.5938.132 (official version) (64-bit) (cohort: Stable).<br>
       - You can download the latest driver at the following address: https://googlechromelabs.github.io/chrome-for-testing/#stable<br>
       - Older drivers (the latest version is preferred) can also be downloaded from the following address: https://chromedriver.storage.googleapis.com/index.html<br>
    (2) After downloading, update the chromedriver.exe address to testcases_scraper.py, e.g. chrome_driver_path = "E:\chromedriver-win64\chromedriver.exe".<br>
3. Then, you need to get the cookie: <br>
   Open your browser, open a codeforces title submission interface, log in to your account, F12 to view the source code, switch to network, press F5 to refresh the interface to reload the content, click on a setting, view the current cookie content, record the JSESSIONID and 39ce7 in it as well as the User-Agent at the bottom, and replace them all in codeforces_scraper.py.<br>
4. Then you can run codeforces_scraper.py, which will scrape description, testcases and code.<br>
