# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 11:20:36 2019

@author: Jason
"""

class Movie:
    def __init__(self, releaseDate, title, releaseType, distributor, url):
        self.releaseDate = releaseDate
        self.title = title
        self.releaseType = releaseType
        self.distributor = distributor
        self.url = url

from selenium import webdriver
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
import sys

client = MongoClient('mongodb+srv://JasonK58:e7g3Xy5WwPSD1k5H@cluster0-mxtug.gcp.mongodb.net/MovieDraft?retryWrites=true&w=majority')

options = webdriver.ChromeOptions()
options.add_argument('headless')

#First argument of the Chrome instantiator is the path to ChromeDriver.
driver = webdriver.Chrome(sys.argv[1], options=options)

driver.get('https://www.the-numbers.com/movies/release-schedule')

content = driver.page_source
soup = BeautifulSoup(content, features='lxml')
table = driver.find_element_by_xpath('//div[@id=\'page_filling_chart\']/table/tbody')

movieArray = []

for row in table.find_elements_by_xpath('.//tr'):
    x = []
    for td in row.find_elements_by_xpath('.//td'):
        x.append(td.text)
    movieArray.append(x)
    if len(movieArray) == 10:
        break

for row in movieArray:
    if not all(' ' == entry for entry in row) and len(row) == 1:
        year = row[0][row[0].find(', ')+2:]
        
    if not len(row) > 3:
        continue

    if row[0]:
        date = row[0]
    else:
        row[0] = date

    releaseDateString = row[0] + ', ' + year
    releaseDate = datetime.strptime(releaseDateString, '%B %d, %Y')
    releaseDateFormattedString = releaseDate.strftime('%Y-%m-%d')
    properReleaseDate = datetime.strptime(releaseDateFormattedString, '%Y-%m-%d')
    
    title = str.strip(row[1][0:row[1].find('(')])
    releaseType = row[1][row[1].find('(')+1:row[1].find(')')]
    
    movieUrlElement = table.find_element_by_link_text(title)
    url = movieUrlElement.get_property('href')
    
    movie = Movie(properReleaseDate, title, releaseType, row[2], url)
    existingMovie = client.MovieDraft.Movies.find_one({"url": url})
    if existingMovie:
        client.MovieDraft.Movies.replace_one(existingMovie, movie.__dict__)
        print('Replaced movie title: {}'.format(movie.title))
    else:
        client.MovieDraft.Movies.insert_one(movie.__dict__)
        print('Inserted movie title: {}'.format(movie.title))
