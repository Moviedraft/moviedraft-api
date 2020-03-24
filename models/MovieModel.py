# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 14:53:49 2019

@author: Jason
"""

from utilities.Database import mongo
from utilities.DatetimeHelper import string_format_date
from bson.objectid import ObjectId

class MovieModel():
    def __init__(self, id, releaseDate, title, releaseType, distributor, domesticGross, lastUpdated, posterUrl):
        self.id = str(id)
        self.releaseDate = releaseDate
        self.title = title
        self.releaseType = releaseType
        self.distributor = distributor
        self.domesticGross = domesticGross
        self.lastUpdated = lastUpdated
        self.posterUrl = posterUrl
    
    @classmethod
    def load_movie_by_id(cls, id):
        if not ObjectId.is_valid(id):
            return None
        queryDict = {'_id': ObjectId(id)}
        movie = cls.load_movie(queryDict)  
        return movie
    
    @classmethod
    def load_movies_by_ids(cls, ids):
        validIds = [id for id in ids if ObjectId.is_valid(id)]
        queryDict = {'_id': {'$in': [ObjectId(id) for id in validIds]}}
        movie = cls.load_movies(queryDict)  
        return movie
    
    @classmethod
    def load_movie(cls, queryDict):
        movie = mongo.db.movies.find_one(queryDict)
        if not movie:
            return None
        posterUrl = '' if 'posterUrl' not in movie else movie['posterUrl']
        return MovieModel(
                id=movie['_id'],
                releaseDate=string_format_date(movie['releaseDate']),
                title=movie['title'],
                releaseType=movie['releaseType'],
                distributor=movie['distributor'],
                domesticGross=movie['domesticGross'],
                lastUpdated=string_format_date(movie['lastUpdated']),
                posterUrl=posterUrl
                )
    
    @classmethod
    def load_movies(cls, queryDict):
        movies = mongo.db.movies.find(queryDict)
        
        movieModels = []
        for movie in movies:
            posterUrl = '' if 'posterUrl' not in movie else movie['posterUrl']
            movieModel = MovieModel(
                id=movie['_id'],
                releaseDate=string_format_date(movie['releaseDate']),
                title=movie['title'],
                releaseType=movie['releaseType'],
                distributor=movie['distributor'],
                domesticGross=movie['domesticGross'],
                lastUpdated=string_format_date(movie['lastUpdated']),
                posterUrl=posterUrl
                )
            movieModels.append(movieModel)
            
        return movieModels