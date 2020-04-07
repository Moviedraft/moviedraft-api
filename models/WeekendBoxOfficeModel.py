# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 12:02:50 2020

@author: Jason
"""

from utilities.Database import mongo
from utilities.DatetimeHelper import convert_to_utc, get_most_recent_monday
from models.MovieModel import MovieModel
from models.BidModel import BidModel
import arrow

class WeekendBoxOfficeModel():
    def __init__(self, id, title, weekendGross, totalGross, owner, 
                 purchasePrice, note):
        self.id = id
        self.title = title
        self.weekendGross = weekendGross
        self.totalGross = totalGross
        self.owner = owner
        self.purchasePrice = purchasePrice
        self.note = note
    
    def serialize(self): 
        return {           
        'id': self.id,
        'title': self.title,
        'weekendGross': self.weekendGross,
        'totalGross': self.totalGross,
        'owner': self.owner,
        'purchasePrice': self.purchasePrice,
        'note': self.note
        }
        
    @classmethod
    def load_weekend_box_office(cls, gameId):
        weekendEnding = get_most_recent_monday()
        
        weekendEndingFilterCondition = { '$lte': convert_to_utc(arrow.get(weekendEnding).shift(days=2)),
                                      '$gte': convert_to_utc(weekendEnding) }
        
        weekendMovies = mongo.db.weekendboxoffice.find({'$query': {'weekendEnding': weekendEndingFilterCondition}, '$orderby': {'weekendGross': -1}})
        if not weekendMovies:
            return None
        
        weekend = []
        for movie in weekendMovies:
            dbMovie = MovieModel.load_movie_by_title(movie['title'])
            
            if not dbMovie:
                highBid = None
            else:
                highBid = BidModel.load_bid_by_gameId_and_movieId(gameId, dbMovie.id)
            
            note = None
            if not highBid or not highBid.user_id:
                note = 'Not in Game'
                owner = None
                purchasePrice = None
            else:
                owner = highBid.userHandle
                purchasePrice = highBid.bid
                
            weekendBoxOfficeModel = WeekendBoxOfficeModel(
                    id=str(movie['_id']),
                    title=movie['title'],
                    weekendGross=movie['weekendGross'],
                    totalGross=movie['totalGross'],
                    owner=owner,
                    purchasePrice=purchasePrice,
                    note=note
                    )
            weekend.append(weekendBoxOfficeModel)
        return weekend