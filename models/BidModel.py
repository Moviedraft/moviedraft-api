# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 07:28:06 2020

@author: Jason
"""
from utilities.Database import mongo
from utilities.DatetimeHelper import string_format_date
from bson.objectid import ObjectId

class BidModel():
    def __init__(self, id, game_id, user_id, movie_id, auctionExpiry, 
                 auctionExpirySet, bid, dollarSpendingCap, userHandle):
        self.id = id
        self.game_id = game_id
        self.user_id = user_id
        self.movie_id = movie_id
        self.auctionExpiry = auctionExpiry
        self.auctionExpirySet = auctionExpirySet
        self.bid = bid
        self.dollarSpendingCap = dollarSpendingCap
        self.userHandle = userHandle

    def serialize(self): 
        return {           
        'id': self.id,
        'game_id': self.game_id,
        'user_id': self.user_id,
        'movie_id': self.movie_id,
        'auctionExpiry': self.auctionExpiry,
        'auctionExpirySet': self.auctionExpirySet,
        'bid': self.bid,
        'dollarSpendingCap': self.dollarSpendingCap,
        'userHandle': self.userHandle
        }
        
    def update_bid(self):
        if not ObjectId.is_valid(self.user_id):
            userId = None
        else:
            userId = ObjectId(self.user_id)
        mongo.db.bids.replace_one({'_id': ObjectId(self.id)}, 
                                        {'game_id': ObjectId(self.game_id),
                                         'user_id': userId,
                                         'movie_id': ObjectId(self.movie_id),
                                         'auctionExpiry': self.auctionExpiry,
                                         'auctionExpirySet': self.auctionExpirySet,
                                         'bid': self.bid,
                                         'dollarSpendingCap': self.dollarSpendingCap,
                                         'userHandle': self.userHandle
                                         })
        updatedRecord = BidModel.load_bid_by_id(self.id)
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
        bid = mongo.db.bids.find_one(queryDict)
        if not bid:
            return None
        return BidModel(
                id=str(bid['_id']),
                game_id=str(bid['game_id']),
                user_id=str(bid['user_id']),
                movie_id=str(bid['movie_id']),
                auctionExpiry=string_format_date(bid['auctionExpiry']),
                auctionExpirySet=bid['auctionExpirySet'],
                bid=bid['bid'],
                dollarSpendingCap=bid['dollarSpendingCap'],
                userHandle=bid['userHandle']
                )
    
    @classmethod
    def load_bids_by_gameId(cls, gameId):
        if not ObjectId.is_valid(gameId):
            return None
        queryDict = {'game_id': ObjectId(gameId)}
        bids = cls.load_bids(queryDict)  
        return bids
    
    @classmethod
    def load_bids_by_userId(cls, userId):
        if not ObjectId.is_valid(userId):
            return None
        queryDict = {'user_id': ObjectId(userId)}
        bids = cls.load_bids(queryDict)  
        return bids
    
    @classmethod
    def load_bids_by_gameId_and_userId(cls, gameId, userId):
        if not ObjectId.is_valid(gameId) or not ObjectId.is_valid(userId):
            return None
        queryDict = {'game_id': ObjectId(gameId), 'user_id': ObjectId(userId)}
        bids = cls.load_bids(queryDict)  
        return bids
    
    @classmethod
    def load_bids(cls, queryDict):
        bids = mongo.db.bids.find(queryDict)
        if not bids:
            return None
        movieBids = []
        for bid in bids:
            movieBid = BidModel(
                    id=str(bid['_id']),
                    game_id=str(bid['game_id']),
                    user_id=str(bid['user_id']),
                    movie_id=str(bid['movie_id']),
                    auctionExpiry=string_format_date(bid['auctionExpiry']),
                    auctionExpirySet=bid['auctionExpirySet'],
                    bid=bid['bid'],
                    dollarSpendingCap=bid['dollarSpendingCap'],
                    userHandle=bid['userHandle']
                    )
            movieBids.append(movieBid)
        return movieBids
        
    @classmethod
    def create_empty_bid(cls, game_id, movie_id, auctionExpiry, dollarSpendingCap):
        id = ObjectId()
        mongo.db.bids.insert_one({'_id': id,
                                  'game_id': ObjectId(game_id),
                                  'user_id': None,
                                  'movie_id': ObjectId(movie_id),
                                  'auctionExpiry': auctionExpiry,
                                  'auctionExpirySet': False,
                                  'bid': None,
                                  'dollarSpendingCap': dollarSpendingCap,
                                  'userHandle': None
                                 })
        bidItem = mongo.db.bids.find_one({'_id': id})
        return BidModel(
                id=str(bidItem['_id']),
                game_id=str(bidItem['game_id']),
                user_id=str(bidItem['user_id']),
                movie_id=str(bidItem['movie_id']),
                auctionExpiry=string_format_date(bidItem['auctionExpiry']),
                auctionExpirySet=bidItem['auctionExpirySet'],
                bid=bidItem['bid'],
                dollarSpendingCap=bidItem['dollarSpendingCap'],
                userHandle=bidItem['userHandle']
                )
    
    @classmethod
    def delete_bids_by_game_id(cls, game_id):
        if not ObjectId.is_valid(game_id):
            return None
        queryDict = {'game_id': ObjectId(game_id)}
        result = cls.delete_bids(queryDict)
        return result
    
    @classmethod
    def delete_bids_by_game_id_and_movie_id(cls, game_id, movie_id):
        if not ObjectId.is_valid(game_id)or not ObjectId.is_valid(movie_id):
            return None
        queryDict = {'game_id': ObjectId(game_id), 'movie_id': ObjectId(movie_id)}
        result = cls.delete_bids(queryDict)
        return result
    
    @classmethod
    def delete_bids(cls, queryDict):
        mongo.db.bids.delete_many(queryDict)
