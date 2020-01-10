# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 13:42:32 2019

@author: Jason
"""

from flask import request, make_response, jsonify
from flask_login import login_required
from flask_restplus import Namespace, Resource, fields
from datetime import datetime
from utilities.Database import mongo
from models.MovieModel import MovieModel
from enums.MovieReleaseType import MovieReleaseType
from decorators.RoleAccessDecorator import requires_role
from enums.Role import Role

movies_namespace = Namespace('movies', description='Retrieve movie data.')

movies_namespace.model('MovieModelFields',{ 
        'id': fields.String,
        'releaseDate': fields.String,
        'title': fields.String,
        'releaseType': fields.String,
        'distributor': fields.String,
        'lastUpdated': fields.String
        })

movies_namespace.model('Movies',{
        'movies': fields.List(fields.Nested(movies_namespace.models['MovieModelFields']))
        })

@movies_namespace.route('')
class Movies(Resource):
    @login_required
    @requires_role(Role.user.value)
    @movies_namespace.response(200, 'Success', movies_namespace.models['Movies'])
    @movies_namespace.response(500, 'Internal Server Error')
    @movies_namespace.response(401, 'Authentication Error') 
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
            return make_response(jsonify(movies=movies), 200)
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
            return make_response(jsonify(movies=movies), 200)
