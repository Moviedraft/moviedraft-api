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

driver = webdriver.Chrome(sys.argv[3], options=options)

today = datetime.strptime(datetime.today().isoformat() , '%Y-%m-%dT%H:%M:%S.%f')

movies = db.movies.find({}, {'title':1, 'url':1, 'lastUpdated':1, '_id':1})

for movie in movies:
    driver.get(movie['url'])
    domesticGrossTable = driver.find_element_by_id('movie_finances')
    domesticGross = domesticGrossTable.find_elements_by_class_name('data')[0].text
    formattedDomesticGross = int(domesticGross[1:].replace(',',''))
    
    db.movies.update_one({'_id': movie['_id']},  {'$set': {'domesticGross': formattedDomesticGross, 'lastUpdated': today }})
    
    print('Movie title: \'{}\' updated'.format(movie['title']))
    