# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 14:53:49 2019

@author: Jason
"""

from utilities.Database import mongo
from datetime import datetime
from bson.objectid import ObjectId

class MovieModel():
    def __init__(self, id, releaseDate, title, releaseType, distributor, lastUpdated):
        self.id = str(id)
        self.releaseDate = releaseDate
        self.title = title
        self.releaseType = releaseType
        self.distributor = distributor
        self.lastUpdated = lastUpdated
    
    @classmethod
    def load_movie_by_id(cls, id):
        if not ObjectId.is_valid(id):
            return None
        queryDict = {'_id': ObjectId(id)}
        movie = cls.load_movie(queryDict)  
        return movie
    
    @classmethod
    def load_movie(cls, queryDict):
        movie = mongo.db.movies.find_one(queryDict)
        if not movie:
            return None
        return MovieModel(
                id=movie['_id'],
                releaseDate=datetime.strftime(movie['releaseDate'], '%Y-%m-%d'),
                title=movie['title'],
                releaseType=movie['releaseType'],
                distributor=movie['distributor'],
                lastUpdated=datetime.strptime(datetime.today().isoformat() , '%Y-%m-%dT%H:%M:%S.%f')
                )