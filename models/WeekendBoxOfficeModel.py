# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 12:02:50 2020

@author: Jason
"""

from utilities.Database import mongo
from utilities.DatetimeHelper import convert_to_utc, get_most_recent_day
from models.MovieModel import MovieModel
from models.BidModel import BidModel
from enums.DaysOfWeek import DaysOfWeek
import arrow

class WeekendBoxOfficeModel():
    def __init__(self, id, title, weekendGross, totalGross, owner, purchasePrice, openingWeekend):
        self.id = id
        self.title = title
        self.weekendGross = weekendGross
        self.totalGross = totalGross
        self.owner = owner
        self.purchasePrice = purchasePrice
        self.openingWeekend = openingWeekend
    
    def serialize(self): 
        return {           
        'id': self.id,
        'title': self.title,
        'weekendGross': self.weekendGross,
        'totalGross': self.totalGross,
        'owner': self.owner,
        'purchasePrice': self.purchasePrice,
        'openingWeekend': self.openingWeekend
        }
        
    @classmethod
    def load_weekend_box_office(cls, gameId):
        weekendEnding = get_most_recent_day(DaysOfWeek.Monday.value)
        
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

            if not highBid or not highBid.user_id:
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
                    openingWeekend=movie['openingWeekend']
                    )
            weekend.append(weekendBoxOfficeModel)
        return weekend