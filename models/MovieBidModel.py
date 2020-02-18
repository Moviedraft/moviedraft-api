# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 07:28:06 2020

@author: Jason
"""
from utilities.Database import mongo
from bson.objectid import ObjectId

class MovieBidModel():
    def __init__(self, id, game_id, user_id, movie_id, auctionExpiry, auctionExpirySet, bid):
        self.id = id
        self.game_id = game_id
        self.user_id = user_id
        self.movie_id = movie_id
        self.auctionExpiry = auctionExpiry
        self.auctionExpirySet = auctionExpirySet
        self.bid = bid

    def update_bid(self):
        if not ObjectId.is_valid(self.user_id):
            userId = None
        else:
            userId = ObjectId(self.user_id)
        mongo.db.moviebids.replace_one({'_id': ObjectId(self.id)}, 
                                        {'game_id': ObjectId(self.game_id),
                                         'user_id': userId,
                                         'movie_id': ObjectId(self.movie_id),
                                         'auctionExpiry': self.auctionExpiry,
                                         'auctionExpirySet': self.auctionExpirySet,
                                         'bid': self.bid
                                         })
        updatedRecord = MovieBidModel.load_bid_by_id(self.id)
        return updatedRecord
    
    @classmethod
    def load_bid_by_id(cls, id):
        if not ObjectId.is_valid(id):
            return None
        queryDict = {'_id': ObjectId(id)}
        bid = cls.load_bid(queryDict)  
        return bid
    
    @classmethod
    def load_bid_by_gameId_and_movieId(cls, gameId, movieId):
        if not ObjectId.is_valid(gameId) or not ObjectId.is_valid(movieId):
            return None
        queryDict = {'game_id': ObjectId(gameId), 'movie_id': ObjectId(movieId)}
        bid = cls.load_bid(queryDict)  
        return bid
    
    @classmethod
    def load_bid(cls, queryDict):
        bid = mongo.db.moviebids.find_one(queryDict)
        if not bid:
            return None
        return MovieBidModel(
                id=str(bid['_id']),
                game_id=str(bid['game_id']),
                user_id=str(bid['user_id']),
                movie_id=str(bid['movie_id']),
                auctionExpiry=bid['auctionExpiry'],
                auctionExpirySet=bid['auctionExpirySet'],
                bid=bid['bid']
                )
    
    @classmethod
    def create_empty_bid(cls, game_id, movie_id, auctionExpiry):
        id = ObjectId()
        mongo.db.moviebids.insert_one({'_id': id,
                                       'game_id': ObjectId(game_id),
                                       'user_id': None,
                                       'movie_id': ObjectId(movie_id),
                                       'auctionExpiry': auctionExpiry,
                                       'auctionExpirySet': False,
                                       'bid': None
                                      })
        bidItem = mongo.db.moviebids.find_one({'_id': id})
        return MovieBidModel(
                id=str(bidItem['_id']),
                game_id=str(bidItem['game_id']),
                user_id=str(bidItem['user_id']),
                movie_id=str(bidItem['movie_id']),
                auctionExpiry=bidItem['auctionExpiry'],
                auctionExpirySet=bidItem['auctionExpirySet'],
                bid=bidItem['bid']
                )