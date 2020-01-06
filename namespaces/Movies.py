# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 13:42:32 2019

@author: Jason
"""

from flask import request
from flask_login import login_required
from flask_restplus import Namespace, Resource, fields
from datetime import datetime
from models.Database import mongo
from models.MovieModel import MovieModel
from enums.MovieReleaseType import MovieReleaseType

movies_namespace = Namespace('movies', description='Retrieve movie data.')

movieModel = movies_namespace.model('Movies',{ 
        'id': fields.String,
        'releaseDate': fields.String,
        'title': fields.String,
        'releaseType': fields.String,
        'distributor': fields.String,
        'lastUpdated': fields.String
        })

@movies_namespace.route('')
class Movies(Resource):
    @movies_namespace.response(200, 'Success', movieModel)
    @login_required
    def get(self):
        movies = []
        releaseType = request.args.get('releaseType')
        startDate = request.args.get('startDate')
        endDate = request.args.get('endDate')
    
        if not startDate:
            startDate = datetime.min.isoformat().split('T', 1)[0]
        if not endDate:
            endDate = datetime.max.isoformat().split('T', 1)[0]
    
        releaseDateFilterCondition = { '$lte': datetime.strptime(endDate, '%Y-%m-%d'),
                                      '$gte': datetime.strptime(startDate, '%Y-%m-%d') }

        if releaseType:
            if MovieReleaseType.has_value(releaseType):
                moviesResult = mongo.db.movies.find({'releaseType': releaseType, 
                                                     'releaseDate': releaseDateFilterCondition}).sort('releaseDate', 1)
                for movie in moviesResult:
                    movieModel = MovieModel(
                        movie['_id'], 
                        movie['releaseDate'], 
                        movie['title'], 
                        movie['releaseType'], 
                        movie['distributor'], 
                        movie['lastUpdated'])
                    movies.append(movieModel.__dict__)
            return movies
        else:
            moviesResult = mongo.db.movies.find({'releaseDate': releaseDateFilterCondition}).sort('releaseDate', 1) 
            for movie in moviesResult:
                movieModel = MovieModel(
                    movie['_id'], 
                    movie['releaseDate'], 
                    movie['title'], 
                    movie['releaseType'], 
                    movie['distributor'], 
                    movie['lastUpdated'])
                movies.append(movieModel.__dict__)
            return movies
