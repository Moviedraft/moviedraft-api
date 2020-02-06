# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 13:42:32 2019

@author: Jason
"""

from flask import request, make_response, jsonify, abort
from flask_restplus import Namespace, Resource, fields, reqparse
from flask_jwt_extended import jwt_required
from datetime import datetime
from bson.objectid import ObjectId
from utilities.Database import mongo
from models.MovieModel import MovieModel
from models.MovieBidModel import MovieBidModel
from models.GameModel import GameModel
from models.UserModel import UserModel
from enums.MovieReleaseType import MovieReleaseType
import json

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

movies_namespace.model('MovieBidRequest', {
        'gameId': fields.String,
        'userId': fields.String,
        'movieId': fields.String,
        'bid': fields.Integer
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
    
@movies_namespace.route('/bid')
class MovieBid(Resource):
    @jwt_required
    @movies_namespace.response(200, 'Success', movies_namespace.models['MovieBidRequest'])
    @movies_namespace.response(401, 'Authentication Error')
    @movies_namespace.response(404, 'Not Found')
    @movies_namespace.response(500, 'Internal Server Error')
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('gameId', required=True)
        parser.add_argument('userId', required=True)
        parser.add_argument('movieId', required=True)
        parser.add_argument('bid', type=int, required=True)
        args = parser.parse_args()

        user = UserModel.load_user_by_id(args['userId'])
        if not user:
            abort(make_response(jsonify(message='User ID: \'{}\' could not be found.'.
                                        format(args['userId'])), 404))
        
        game = GameModel.load_game_by_id(args['gameId'])
        if not game:
            abort(make_response(jsonify(message='Game name: \'{}\' could not be found.'.
                                        format(args['gameName'])), 404))
        
        if not MovieModel.load_movie_by_id(args['movieId']):
            abort(make_response(jsonify(message='Movie ID: \'{}\' could not be found.'.
                                        format(args['movieId'])), 404))
        
        highestBid = MovieBidModel.load_bid_by_gameId_and_movieId(args['gameId'], args['movieId'])
        
        if not highestBid:
            highestBidModel = MovieBidModel(
                ObjectId(),
                ObjectId(args['gameId']),
                ObjectId(args['userId']),
                ObjectId(args['movieId']),
                args['bid']
                )
        
            result = mongo.db.moviebids.insert_one(highestBidModel.__dict__)
            highestBid = MovieBidModel.load_bid_by_id(str(result.inserted_id))
        
        if args['bid'] > highestBid.bid:
            highestBid.bid = args['bid']
            highestBid.user_id = ObjectId(args['userId'])
            updatedRecord = highestBid.update_bid()
            return make_response(updatedRecord.__dict__, 200)
        else:
            abort(make_response(jsonify(message='Bid of: ${} did not exceed minimum bid of ${}.'.
                                        format(args['bid'], highestBid.bid)), 400))