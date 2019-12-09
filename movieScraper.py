# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 11:20:36 2019

@author: Jason
"""

# =============================================================================
# Script requires three arguements to be passed when running:
#     The connection string to MongoDB
#     The database name
#     The file path for ChromeDriver
# =============================================================================
    
class Movie:
    def __init__(self, releaseDate, title, releaseType, distributor, url):
        self.releaseDate = releaseDate
        self.title = title
        self.releaseType = releaseType
        self.distributor = distributor
        self.url = url
        self.lastUpdated = datetime.strptime(datetime.today().isoformat() , '%Y-%m-%dT%H:%M:%S.%f')     

from selenium import webdriver
from pymongo import MongoClient
from datetime import datetime
import sys

client = MongoClient(sys.argv[1])
db = client.get_database(sys.argv[2])

options = webdriver.ChromeOptions()
options.add_argument('headless')

driver = webdriver.Chrome(sys.argv[3], options=options)
driver.get('https://www.the-numbers.com/movies/release-schedule')

table = driver.find_element_by_xpath('//div[@id=\'page_filling_chart\']/table/tbody')

movieArray = []

for row in table.find_elements_by_xpath('.//tr'):
    x = []
    for td in row.find_elements_by_xpath('.//td'):
        x.append(td.text)
    movieArray.append(x)

for row in movieArray:
    if not all(' ' == entry for entry in row) and len(row) == 1:
        releaseYear = row[0][row[0].find(', ')+2:]
        
    if not len(row) > 3:
        continue

    if row[0]:
        date = row[0]
    else:
        row[0] = date

    releaseMonth = row[0][0:row[0].find(' ')]
    releaseDay = row[0][row[0].find(' ')+1:]
    releaseDateString = releaseYear + '-' + releaseMonth + '-' + releaseDay
    try: 
        releaseDate = datetime.strptime(releaseDateString, '%Y-%B-%d')
    except ValueError:
        releaseDate = datetime.max

    title = str.strip(row[1][0:row[1].rfind('(')])
    
    releaseType = row[1][row[1].rfind('(')+1:row[1].rfind(')')]
    if releaseType == 'IMAX' or releaseType == 'Expands Wide':
        releaseType = 'wide'
        
    movieUrlElement = table.find_element_by_partial_link_text(title)
    url = movieUrlElement.get_property('href')
    
    movie = Movie(releaseDate, title, releaseType.lower(), row[2], url)
    
    existingMovie = db.movies.find_one({"url": url})
    if existingMovie:
        db.movies.replace_one(existingMovie, movie.__dict__)
        print('Replaced movie title: {}'.format(movie.title))
    else:
        db.movies.insert_one(movie.__dict__)
        print('Inserted movie title: {}'.format(movie.title))
