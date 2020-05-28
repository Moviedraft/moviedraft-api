# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 13:42:32 2019

@author: Jason
"""

from flask import request, make_response, jsonify
from flask_restplus import Namespace, Resource, fields
from flask_jwt_extended import jwt_required
from datetime import datetime
from utilities.DatetimeHelper import convert_to_utc
from models.MovieModel import MovieModel
from enums.MovieReleaseType import MovieReleaseType

movies_namespace = Namespace('movies', description='Retrieve movie data.')

movies_namespace.model('MovieModelFields',{ 
        'id': fields.String,
        'releaseDate': fields.DateTime(dt_format=u'%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'title': fields.String,
        'releaseType': fields.String,
        'distributor': fields.String,
        'domesticGross': fields.Integer,
        'lastUpdated': fields.DateTime(dt_format=u'%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'posterUrl': fields.String
        })

movies_namespace.model('Movies',{
        'movies': fields.List(fields.Nested(movies_namespace.models['MovieModelFields']))
        })

@movies_namespace.route('')
class Movies(Resource):
    @jwt_required
    @movies_namespace.response(200, 'Success', movies_namespace.models['Movies'])
    @movies_namespace.response(500, 'Internal Server Error')
    @movies_namespace.response(401, 'Authentication Error') 
    @movies_namespace.doc(params={'startDate': 'Earliest date of movie releases (YYYY-mm-dd).',
                                  'endDate': 'Latest date of movie releases (YYYY-mm-dd).',
                                  'releaseType': 'wide, limited'})
    def get(self):
        movies = []
        releaseType = request.args.get('releaseType')
        startDate = request.args.get('startDate')
        endDate = request.args.get('endDate')
    
        if not startDate:
            startDate = datetime.min
        if not endDate:
            endDate = datetime.max
    
        releaseDateFilterCondition = { '$lte': convert_to_utc(endDate),
                                      '$gte': convert_to_utc(startDate) }

        if releaseType:
            if MovieReleaseType.has_value(releaseType):
                moviesResult = MovieModel.load_movies({'releaseType': releaseType, 'releaseDate': releaseDateFilterCondition})
                moviesResult.sort(key = lambda x: x.releaseDate)
                for movie in moviesResult:
                    movies.append(movie.__dict__)

            return make_response(jsonify(movies=movies), 200)
        else:
            moviesResult = MovieModel.load_movies({'releaseDate': releaseDateFilterCondition})
            moviesResult.sort(key = lambda x: x.releaseDate)
            for movie in moviesResult:
                movies.append(movie.__dict__)
            return make_response(jsonify(movies=movies), 200)
