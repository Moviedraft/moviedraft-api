# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 13:42:32 2019

@author: Jason
"""

from flask import request, make_response, jsonify, abort
from flask_restplus import Namespace, Resource, fields, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from utilities.Database import mongo
from utilities.DatetimeHelper import convert_to_utc, string_format_date
from models.MovieModel import MovieModel
from models.MovieBidModel import MovieBidModel
from models.GameModel import GameModel
from models.UserModel import UserModel
from enums.MovieReleaseType import MovieReleaseType
import arrow

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

movies_namespace.model('MovieBidRequest', {
        'gameId': fields.String,
        'userId': fields.String,
        'movieId': fields.String,
        'auctionExpiry': fields.DateTime(dt_format=u'%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'bid': fields.Integer
        })

movieBidPost = movies_namespace.model('MovieBidPost', {
        'gameId': fields.String,
        'movieId': fields.String,
        'bid': fields.Integer
        })

movies_namespace.model('MovieBidPostResponse', {
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
            startDate = datetime.min
        if not endDate:
            endDate = datetime.max
    
        releaseDateFilterCondition = { '$lte': convert_to_utc(endDate),
                                      '$gte': convert_to_utc(startDate) }
        
        print(releaseDateFilterCondition)

        if releaseType:
            if MovieReleaseType.has_value(releaseType):
                moviesResult = mongo.db.movies.find({'releaseType': releaseType, 
                                                     'releaseDate': releaseDateFilterCondition}).sort('releaseDate', 1)
                for movie in moviesResult:
                    posterUrl = '' if 'posterUrl' not in movie else movie['posterUrl']
                    movieModel = MovieModel(
                        movie['_id'], 
                        string_format_date(movie['releaseDate']), 
                        movie['title'], 
                        movie['releaseType'], 
                        movie['distributor'],
                        movie['domesticGross'],
                        string_format_date(movie['lastUpdated']),
                        posterUrl)
                    movies.append(movieModel.__dict__)
            return make_response(jsonify(movies=movies), 200)
        else:
            moviesResult = mongo.db.movies.find({'releaseDate': releaseDateFilterCondition}).sort('releaseDate', 1) 
            for movie in moviesResult:
                posterUrl = '' if 'posterUrl' not in movie else movie['posterUrl']
                movieModel = MovieModel(
                    movie['_id'], 
                    string_format_date(movie['releaseDate']), 
                    movie['title'], 
                    movie['releaseType'], 
                    movie['distributor'],
                    movie['domesticGross'],
                    string_format_date(movie['lastUpdated']),
                    posterUrl)
                movies.append(movieModel.__dict__)
            return make_response(jsonify(movies=movies), 200)

@movies_namespace.route('/bid/<string:gameId>/<string:movieId>')
class GameMovies(Resource):
    @jwt_required
    @movies_namespace.response(200, 'Success', movies_namespace.models['MovieBidRequest'])
    @movies_namespace.response(401, 'Authentication Error')
    @movies_namespace.response(404, 'Not Found')
    @movies_namespace.response(500, 'Internal Server Error')
    def get(self, gameId, movieId):
        game = GameModel.load_game_by_id(gameId)
        if not game:
            abort(make_response(jsonify(message='Game name: \'{}\' could not be found.'.
                                        format(gameId)), 404))
        
        if not MovieModel.load_movie_by_id(movieId):
            abort(make_response(jsonify(message='Movie ID: \'{}\' could not be found.'.
                                        format(movieId)), 404))
        
        bidItem = MovieBidModel.load_bid_by_gameId_and_movieId(gameId, movieId)
        
        if not bidItem:
            abort(make_response(jsonify(message='Could not find bid for gameId: \'{}\' and movieId: \'{}\'.'.
                                        format(gameId, movieId)), 404))
        
        if arrow.utcnow() > arrow.get(game.auctionDate) and bidItem.auctionExpirySet == False:
                bidItem.auctionExpiry = datetime.utcnow() + timedelta(seconds=game.auctionItemsExpireInSeconds)
                bidItem.auctionExpirySet = True
                bidItem = bidItem.update_bid()
        
        return make_response(bidItem.__dict__, 200)
    
@movies_namespace.route('/bid')
class MovieBid(Resource):
    @jwt_required
    @movies_namespace.expect(movieBidPost)
    @movies_namespace.response(200, 'Success', movies_namespace.models['MovieBidPostResponse'])
    @movies_namespace.response(401, 'Authentication Error')
    @movies_namespace.response(403, 'Forbidden')
    @movies_namespace.response(404, 'Not Found')
    @movies_namespace.response(500, 'Internal Server Error')
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('gameId', required=True)
        parser.add_argument('movieId', required=True)
        parser.add_argument('bid', type=int, required=True)
        args = parser.parse_args()
        
        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity['id'])
        
        game = GameModel.load_game_by_id(args['gameId'])
        if not game:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.
                                        format(args['gameId'])), 404))

        if not MovieModel.load_movie_by_id(args['movieId']):
            abort(make_response(jsonify(message='Movie ID: \'{}\' could not be found.'.
                                        format(args['movieId'])), 404))
        
        highestBid = MovieBidModel.load_bid_by_gameId_and_movieId(args['gameId'], args['movieId'])
        
        if not highestBid:
            abort(make_response(jsonify(message='Bid item for gameId: \'{}\' and movieId: \'{}\' could not be found.'.
                                        format(args['gameId'], args['movieId'])), 404))

        if highestBid.auctionExpiry == game.auctionDate:
            abort(make_response(jsonify(message='Auction for gameId: \'{}\' and movieId: \'{}\' has not begun yet.'.
                                        format(args['gameId'], args['movieId'])), 403))
        
        if arrow.utcnow() > arrow.get(highestBid.auctionExpiry):
            abort(make_response(jsonify(message='Bid item for gameId: \'{}\' and movieId: \'{}\' has closed.'.
                                        format(args['gameId'], args['movieId'])), 403))
            
        if highestBid.bid == None or args['bid'] > highestBid.bid:
            highestBid.bid = args['bid']
            highestBid.user_id = ObjectId(current_user.id)
            updatedRecord = highestBid.update_bid()
            return make_response(updatedRecord.__dict__, 200)
        else:
            abort(make_response(jsonify(message='Bid of: ${} did not exceed minimum bid of ${}.'.
                                        format(args['bid'], highestBid.bid)), 400))