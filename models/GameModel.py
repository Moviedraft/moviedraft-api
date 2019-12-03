# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 21:14:25 2019

@author: Jason
"""

from models.Database import mongo

class GameModel():
    def __init__(self, gameName, gameNameLowerCase, playerBuyIn, dollarSpendingCap, movies, rules):
        self.gameName = gameName
        self.gameNameLowerCase = gameNameLowerCase
        self.playerBuyIn = playerBuyIn
        self.dollarSpendingCap = dollarSpendingCap
        self.movies = movies
        self.rules = rules
        
    def load_game(gameNameLowerCase):
        game = mongo.db.games.find_one({'gameNameLowerCase': gameNameLowerCase})
        if not game:
            return None
        return GameModel(
                gameName=game['gameName'],
                gameNameLowerCase=game['gameName'].lower(),
                playerBuyIn=game['playerBuyIn'],
                dollarSpendingCap=game['dollarSpendingCap'],
                movies=game['movies'],
                rules=game['rules']
                )