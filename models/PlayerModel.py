# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 13:22:31 2020

@author: Jason
"""

from utilities.DatetimeHelper import string_format_date
from models.MovieModel import MovieModel
from models.UserModel import UserModel
from models.RuleModel import RuleModel

class PlayerModel():
    def __init__(self, id, userHandle, totalSpent, totalGross, movies, value):
        self.id = id
        self.userHandle = userHandle
        self.totalSpent = totalSpent
        self.totalGross = totalGross
        self.movies = movies
        self.value = value
    
    def serialize(self):
        return {
                'id': self.id,
                'userHandle': self.userHandle,
                'totalSpent': self.totalSpent,
                'totalGross': self.totalGross,
                'movies': self.movies,
                'value': self.value
                }
        
    @classmethod
    def loadPlayer(cls, playerId, gameBids, rules):
        player = UserModel.load_user_by_id(playerId)
        if not player:
            return None
        
        playerBids = [bid for bid in gameBids if bid.user_id == player.id]

        totalSpent = sum(bid.bid for bid in playerBids)

        moviesPurchased = MovieModel.load_movies_by_ids([playerBid.movie_id for playerBid in playerBids])

        totalGross = RuleModel.apply_rules(moviesPurchased, rules, playerBids)

        movies = [{ 'title': movie.title,
                    'cost': next((bid.bid for bid in playerBids if bid.movie_id == movie.id)),
                    'releaseDate': string_format_date(movie.releaseDate) } for movie in moviesPurchased]
        
        value = round(totalGross / totalSpent) if totalSpent else 0

        return PlayerModel(
                id=playerId,
                userHandle=player.userHandle,
                totalSpent=totalSpent,
                totalGross=totalGross,
                movies=movies,
                value=value
                )

        