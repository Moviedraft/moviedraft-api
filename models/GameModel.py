# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 21:14:25 2019

@author: Jason
"""

from utilities.Database import mongo
from datetime import datetime

class GameModel():
    def __init__(self, gameName, gameNameLowerCase, startDate, endDate, 
                 playerBuyIn, dollarSpendingCap, movies, rules, commissionerId, playerIds):
        self.gameName = gameName
        self.gameNameLowerCase = gameNameLowerCase
        self.startDate = startDate
        self.endDate = endDate
        self.playerBuyIn = playerBuyIn
        self.dollarSpendingCap = dollarSpendingCap
        self.movies = movies
        self.rules = rules
        self.commissionerId = commissionerId
        self.playerIds = playerIds
        
    def load_game(gameNameLowerCase):
        game = mongo.db.games.find_one({'gameNameLowerCase': gameNameLowerCase})
        if not game:
            return None
        return GameModel(
                gameName=game['gameName'],
                gameNameLowerCase=game['gameName'].lower(),
                startDate=datetime.strftime(game['startDate'], '%Y-%m-%d'),
                endDate=datetime.strftime(game['endDate'], '%Y-%m-%d'),
                playerBuyIn=game['playerBuyIn'],
                dollarSpendingCap=game['dollarSpendingCap'],
                movies=game['movies'],
                rules=game['rules'],
                commissionerId=game['commissionerId'],
                playerIds=game['playerIds']
                )