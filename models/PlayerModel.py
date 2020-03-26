# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 13:22:31 2020

@author: Jason
"""

from models.MovieModel import MovieModel
from models.UserModel import UserModel

class PlayerModel():
    def __init__(self, id, userHandle, totalSpent, totalGross, moviesPurchasedTitles, value):
        self.id = id
        self.userHandle = userHandle
        self.totalSpent = totalSpent
        self.totalGross = totalGross
        self.moviesPurchasedTitles = moviesPurchasedTitles
        self.value = value
    
    def serialize(self):
        return {
                'id': self.id,
                'userHandle': self.userHandle,
                'totalSpent': self.totalSpent,
                'totalGross': self.totalGross,
                'moviesPurchasedTitles': self.moviesPurchasedTitles,
                'value': self.value
                }
        
    @classmethod
    def loadPlayer(cls, playerId, gameBids):
        player = UserModel.load_user_by_id(playerId)
        if not player:
            return None
        
        playerBids = [bid for bid in gameBids if bid.user_id == player.id]

        totalSpent = sum(bid.bid for bid in playerBids)

        moviesPurchased = MovieModel.load_movies_by_ids([playerBid.movie_id for playerBid in playerBids])
        totalGross = sum(movie.domesticGross for movie in moviesPurchased)
        movieTitles = [movie.title for movie in moviesPurchased]
        
        value = round(totalGross / totalSpent)

        return PlayerModel(
                id=playerId,
                userHandle=player.userHandle,
                totalSpent=totalSpent,
                totalGross=totalGross,
                moviesPurchasedTitles=movieTitles,
                value=value
                )

        