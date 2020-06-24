# -*- coding: utf-8 -*-
'''
Created on Tue Nov 26 11:20:36 2019

@author: Jason
'''

# =============================================================================
# Script requires four arguements to be passed when running:
#     The connection string to MongoDB
#     The database name
#     The file path for ChromeDriver
#     The URL being used for scraping
# =============================================================================
    
class Movie:
    def __init__(self, releaseDate, title, releaseType, distributor, url, posterUrl, domesticGross):
        self.releaseDate = releaseDate
        self.title = title
        self.releaseType = releaseType
        self.distributor = distributor
        self.url = url
        self.posterUrl = posterUrl
        self.domesticGross = domesticGross
        self.lastUpdated = datetime.strptime(datetime.utcnow().isoformat() , '%Y-%m-%dT%H:%M:%S.%f')     

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from pymongo import MongoClient
from datetime import datetime
import sys

client = MongoClient(sys.argv[1])
db = client.get_database(sys.argv[2])

options = webdriver.ChromeOptions()
experimentalFlags = ['same-site-by-default-cookies@1','cookies-without-same-site-must-be-secure@1']
chromeLocalStatePrefs = { 'browser.enabled_labs_experiments' : experimentalFlags}
options.add_experimental_option('localState',chromeLocalStatePrefs)

caps = DesiredCapabilities().CHROME
caps['pageLoadStrategy'] = 'none'

options.add_argument('start-maximized')
options.add_argument('enable-automation')
options.add_argument('--blink-settings=imagesEnabled=false')
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-infobars')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-browser-side-navigation')
options.add_argument('--disable-gpu')
options.add_argument('--hide-scrollbars')
options.add_argument('--ignore-certificate-errors')

driver = webdriver.Chrome(sys.argv[3], options=options, desired_capabilities=caps)
driver.get(sys.argv[4])
WebDriverWait(driver, timeout=10).until(ec.visibility_of_element_located((By.ID, 'page_filling_chart')))

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

    if 'Untitled' in title or 'Event Film' in title:
        print('Skipping over {}'.format(title))
        continue
    
    releaseType = row[1][row[1].rfind('(')+1:row[1].rfind(')')].lower()
    
    if releaseType != 'wide' and releaseType != 'imax' and releaseType != 'expands wide' and releaseType != 'canceled':
        print('Skipping {} release of {}'.format(releaseType, title))
        continue
    
    if releaseType == 'imax' or releaseType == 'expands wide':
        releaseType = 'wide'

    if releaseType == 'canceled':
        releaseDate = datetime.max
        
    movieUrlElement = table.find_element_by_partial_link_text(title)
    url = movieUrlElement.get_property('href')

    #Need to go to the actual movie page to retrieve the proper movie url and title.
    #Without doing this, a movie could change its title and then a duplicate entry would be created.
    movieDriver = webdriver.Chrome(sys.argv[3], options=options, desired_capabilities=caps)
    movieDriver.get(url)
    WebDriverWait(movieDriver, timeout=10).until(ec.visibility_of_element_located((By.TAG_NAME, 'h1')))
    redirectMovieUrl = movieDriver.current_url
    title = movieDriver.find_element_by_xpath('//h1').text
    formattedTitle = str.strip(title[0:title.rfind('(')])
    movieDriver.close()

    movie = Movie(releaseDate, formattedTitle, releaseType, row[2], redirectMovieUrl, '', 0)

    existingMovie = db.movies.find_one({'url': url})
    if existingMovie:
        try:
            movie.domesticGross = existingMovie['domesticGross']
            movie.posterUrl = existingMovie['posterUrl']
        except KeyError:
            pass
        db.movies.replace_one(existingMovie, movie.__dict__)
        print('Replaced movie title: {}'.format(movie.title))
    else:
        db.movies.insert_one(movie.__dict__)
        print('Inserted movie title: {}'.format(movie.title))
