# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 13:22:31 2020

@author: Jason
"""

from utilities.DatetimeHelper import string_format_date
from models.MovieModel import MovieModel
from models.UserModel import UserModel
from models.RuleModel import RuleModel
from models.SideBetModel import SideBetModel

class PlayerModel():
    def __init__(self, id, userHandle, totalSpent, totalGross, movies, value, bonus_in_millions):
        self.id = id
        self.userHandle = userHandle
        self.totalSpent = totalSpent
        self.totalGross = totalGross
        self.movies = movies
        self.value = value
        self.bonus_in_millions = bonus_in_millions
    
    def serialize(self):
        return {
                'id': self.id,
                'userHandle': self.userHandle,
                'totalSpent': self.totalSpent,
                'totalGross': self.totalGross,
                'movies': self.movies,
                'value': self.value,
                'bonusInMillions': self.bonus_in_millions
                }
        
    @classmethod
    def loadPlayer(cls, game_id, playerId, gameBids, rules):
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

        side_bets_won = SideBetModel.load_side_bet_by_game_id_and_winner_id(game_id, playerId)
        bonus_in_millions = sum(side_bet.prize_in_millions for side_bet in side_bets_won)

        return PlayerModel(
                id=playerId,
                userHandle=player.userHandle,
                totalSpent=totalSpent,
                totalGross=totalGross,
                movies=movies,
                value=value,
                bonus_in_millions=bonus_in_millions
                )

        