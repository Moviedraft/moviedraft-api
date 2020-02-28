# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 13:35:46 2019

@author: Jason
"""

# =============================================================================
# Script requires three arguements to be passed when running:
#     The connection string to MongoDB
#     The database name
#     The file path for ChromeDriver
# =============================================================================

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

movies = db.movies.find({}, {'title':1, 'url':1, 'releaseDate':1, '_id':1})

for movie in movies:
    if movie['releaseDate'] >= datetime.today():
        print('Skipping \'{}\': not released.'.format(movie['title']))
        continue
    driver.get(movie['url'])
    domesticGrossTable = driver.find_element_by_id('movie_finances')
    domesticGross = domesticGrossTable.find_elements_by_class_name('data')[0].text
    formattedDomesticGross = int(domesticGross[1:].replace(',',''))
    
    db.movies.update_one({'_id': movie['_id']},  
                          {'$set': {'domesticGross': formattedDomesticGross, 
                                    'lastUpdated': datetime.strptime(datetime.utcnow().isoformat() , '%Y-%m-%dT%H:%M:%S.%f') }})
    
    print('Movie title: \'{}\' updated'.format(movie['title']))
    