# Code Scraper for Chanllenges (CSC)

code used for scraping contest codes

based on [Description2Code scraper](https://github.com/ethancaballero/description2code). Thanks a lot!:heart:

this project only support codeforces as source now

## How to use
Please run challengeslist_generator.py first to generate current challenges list on codeforces.com. A json named challenges_all.json including problem name, difficulty and tags will be generated. The challenges_sampled.json is sampled from challenges_all.json with 150 problems in it.

Then you can run codeforces_scraper.py, which will scrape description, testcases and code.
