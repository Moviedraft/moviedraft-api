# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 13:16:53 2020

@author: Jason
"""

from flask import make_response, jsonify, abort
from flask_restplus import Namespace, Resource, fields, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from models.MovieModel import MovieModel
from models.BidModel import BidModel
from models.GameModel import GameModel
from models.UserModel import UserModel
from utilities.DatetimeHelper import convert_to_utc
import arrow

bids_namespace = Namespace('bids', description='Retrieve auction bid data.')

bids_namespace.model('BidRequest', {
        'gameId': fields.String,
        'userId': fields.String,
        'movieId': fields.String,
        'auctionExpiry': fields.DateTime(dt_format=u'%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'bid': fields.Integer,
        'dollarSpendingCap': fields.Integer,
        'userHandle': fields.String
        })

bids_namespace.model('Bids',{
        'bids': fields.List(fields.Nested(bids_namespace.models['BidRequest']))
        })

bidPost = bids_namespace.model('BidPost', {
        'gameId': fields.String,
        'movieId': fields.String,
        'bid': fields.Integer
        })

bids_namespace.model('BidPostResponse', {
        'gameId': fields.String,
        'userId': fields.String,
        'movieId': fields.String,
        'auctionExpiry': fields.DateTime(dt_format=u'%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'bid': fields.Integer,
        'dollarSpendingCap': fields.Integer,
        'userHandle': fields.String
        })

@bids_namespace.route('/<string:gameId>')
class GameBids(Resource):
    @jwt_required
    @bids_namespace.response(200, 'Success', bids_namespace.models['Bids'])
    @bids_namespace.response(401, 'Authentication Error')
    @bids_namespace.response(500, 'Internal Server Error')
    def get(self, gameId):
        bids = BidModel.load_bids_by_gameId(gameId)

        return make_response(jsonify(bids=[bid.serialize() for bid in bids]), 200)
        

@bids_namespace.route('/<string:gameId>/<string:movieId>')
class GameMovieBids(Resource):
    @jwt_required
    @bids_namespace.response(200, 'Success', bids_namespace.models['BidRequest'])
    @bids_namespace.response(401, 'Authentication Error')
    @bids_namespace.response(404, 'Not Found')
    @bids_namespace.response(500, 'Internal Server Error')
    def get(self, gameId, movieId):
        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity['id'])
        
        game = GameModel.load_game_by_id(gameId)
        if not game:
            abort(make_response(jsonify(message='Game name: \'{}\' could not be found.'.
                                        format(gameId)), 404))
        
        if not MovieModel.load_movie_by_id(movieId):
            abort(make_response(jsonify(message='Movie ID: \'{}\' could not be found.'.
                                        format(movieId)), 404))
        
        bidItem = BidModel.load_bid_by_gameId_and_movieId(gameId, movieId)
        
        if not bidItem:
            abort(make_response(jsonify(message='Could not find bid for gameId: \'{}\' and movieId: \'{}\'.'.
                                        format(gameId, movieId)), 404))
        
        if (str(game.commissionerId) == current_user.id 
            and arrow.utcnow() > arrow.get(game.auctionDate) 
            and bidItem.auctionExpirySet == False):
                bidItem.auctionExpiry = convert_to_utc(arrow.utcnow().shift(seconds=+game.auctionItemsExpireInSeconds))
                bidItem.auctionExpirySet = True
                bidItem = bidItem.update_bid()
        
        return make_response(bidItem.__dict__, 200)
    
@bids_namespace.route('')
class Bid(Resource):
    @jwt_required
    @bids_namespace.expect(bidPost)
    @bids_namespace.response(200, 'Success', bids_namespace.models['BidPostResponse'])
    @bids_namespace.response(400, 'Bad Request')
    @bids_namespace.response(401, 'Authentication Error')
    @bids_namespace.response(403, 'Forbidden')
    @bids_namespace.response(404, 'Not Found')
    @bids_namespace.response(500, 'Internal Server Error')
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
        
        highestBid = BidModel.load_bid_by_gameId_and_movieId(args['gameId'], args['movieId'])
        
        if not highestBid:
            abort(make_response(jsonify(message='Bid item for gameId: \'{}\' and movieId: \'{}\' could not be found.'.
                                        format(args['gameId'], args['movieId'])), 404))

        if highestBid.auctionExpiry == game.auctionDate:
            abort(make_response(jsonify(message='Auction for gameId: \'{}\' and movieId: \'{}\' has not begun yet.'.
                                        format(args['gameId'], args['movieId'])), 403))
        
        if arrow.utcnow() > arrow.get(highestBid.auctionExpiry):
            abort(make_response(jsonify(message='Bid item for gameId: \'{}\' and movieId: \'{}\' has closed.'.
                                        format(args['gameId'], args['movieId'])), 403))
            
        if args['bid'] > game.dollarSpendingCap:
            abort(make_response(jsonify(message='Bid must be below game\'s bid cap: ${}'.
                                        format(game.dollarSpendingCap)), 400))
        
        currentBids = BidModel.load_bids_by_gameId_and_userId(args['gameId'], current_user.id)
        totalSpent = sum(bid.bid for bid in currentBids)
        if totalSpent + args['bid'] > game.dollarSpendingCap:
            abort(make_response(jsonify(message='You have ${} left in the auction to spend.'.
                                        format(game.dollarSpendingCap - totalSpent)), 400))
            
        if highestBid.bid == None or args['bid'] > highestBid.bid:
            highestBid.bid = args['bid']
            highestBid.user_id = ObjectId(current_user.id)
            highestBid.userHandle = current_user.userHandle
            highestBid.auctionExpiry = convert_to_utc(arrow.get(highestBid.auctionExpiry).shift(seconds=+game.auctionTimeIncrement))
            updatedRecord = highestBid.update_bid()
            return make_response(updatedRecord.__dict__, 200)
        else:
            abort(make_response(jsonify(message='Bid of: ${} did not exceed minimum bid of ${}.'.
                                        format(args['bid'], highestBid.bid)), 400))