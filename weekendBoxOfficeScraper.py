# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 14:52:04 2020

@author: Jason
"""

class WeekendBoxOffice:
    def __init__(self, title, weekendGross):
        self.title = title
        self.weekendGross = weekendGross
        self.weekendEnding = datetime.strptime(datetime.utcnow().isoformat() , '%Y-%m-%dT%H:%M:%S.%f') 
        
from selenium import webdriver
from pymongo import MongoClient
from datetime import datetime
import sys

client = MongoClient(sys.argv[1])
db = client.get_database(sys.argv[2])

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1280x1696')
options.add_argument('--hide-scrollbars')
options.add_argument('--single-process')
options.add_argument('--ignore-certificate-errors')
options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')

driver = webdriver.Chrome(sys.argv[3], options=options)

driver.get(sys.argv[4])
weekendGrossTable = driver.find_element_by_id('box_office_weekend_table')

movieArray = []

for row in weekendGrossTable.find_elements_by_xpath('.//tr')[:11]:
    tds = row.find_elements_by_xpath('.//td')
    
    if len(tds) == 0:
        continue

    linkWebElement = tds[2].find_elements_by_xpath('.//b/a')
    link = linkWebElement[0].get_attribute('href')
    databaseMovie = db.movies.find_one({'url': link.replace('#tab=box-office', '#tab=summary')})
    if not databaseMovie:
        print('{} not in db. Retrieving title from website.'.format(tds[2].text))
        movieDriver = webdriver.Chrome(sys.argv[3], options=options)
        movieDriver.get(link)
        movieTitle = movieDriver.find_element_by_xpath('//div[@id=\'main\']/div/h1').text[:-7]
    else:
        movieTitle = databaseMovie['title']
    
    weekendGross = tds[4].text
    formattedWeekendGross = ''.join(character for character in weekendGross if character.isnumeric())
    
    weekendBoxOffice = WeekendBoxOffice(movieTitle, int(formattedWeekendGross))
    
    db.weekendboxoffice.insert_one(weekendBoxOffice.__dict__)
    print('{} inserted into database'.format(weekendBoxOffice.title))
	
	