# -*- coding: utf-8 -*-
"""
Created on Mon Jan 27 13:07:21 2020

@author: Jason
"""

from pymongo import MongoClient
from datetime import datetime
import requests
import sys
import string

movieSearchUrl = sys.argv[1]
moviePosterUrl = sys.argv[2]

client = MongoClient(sys.argv[3])
db = client.get_database(sys.argv[4])

movies = db.movies.find({}, {'title':1, 'releaseDate':1, '_id':1})

for movie in movies:
    print('Updating \'{}\''.format(movie['title']))
    formattedMovieTitle = movie['title'].translate(movie['title'].maketrans('', '', string.punctuation))
    url = movieSearchUrl + formattedMovieTitle
    response = requests.get(url = url)
    data = response.json()
    if 'results' not in data:
        print('Could not find any results for \'{}\''.format(formattedMovieTitle))
        continue
    for result in data['results']:
        if 'release_date' not in result:
            print('No release date set for \'{}\' result'.format(formattedMovieTitle))
            continue
        releaseYear = result['release_date'].split('-')[0]
        movieReleaseYear = movie['releaseDate'].strftime("%Y")
        if releaseYear == movieReleaseYear and formattedMovieTitle in result['title']:
            posterPath = result['poster_path']
            if not posterPath:
                print('No poster available for this \'{}\' result'.format(formattedMovieTitle))
                continue
            posterUrl = moviePosterUrl + posterPath
            db.movies.update_one({'_id': movie['_id']}, {'$set': {'posterUrl': posterUrl,
                                  'lastUpdated': datetime.strptime(datetime.today().isoformat() , '%Y-%m-%dT%H:%M:%S.%f')}})
            print('Updated \'{}\' with movie poster'.format(movie['title']))
            break