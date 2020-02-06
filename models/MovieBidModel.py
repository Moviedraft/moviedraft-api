# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 07:28:06 2020

@author: Jason
"""
from utilities.Database import mongo
from bson.objectid import ObjectId

class MovieBidModel():
    def __init__(self, id, game_id, user_id, movie_id, bid):
        self.id = id
        self.game_id = game_id
        self.user_id = user_id
        self.movie_id = movie_id
        self.bid = bid

    def update_bid(self):
        mongo.db.moviebids.replace_one({'_id': ObjectId(self.id)}, 
                                        {'game_id': ObjectId(self.game_id),
                                         'user_id': ObjectId(self.user_id),
                                         'movie_id': ObjectId(self.movie_id),
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
                bid=bid['bid']
                ) 