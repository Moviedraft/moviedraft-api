# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 21:14:25 2019

@author: Jason
"""

from utilities.Database import mongo
from datetime import datetime
from bson.objectid import ObjectId

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
    
    @classmethod
    def load_game_by_id(cls, id):
        if not ObjectId.is_valid(id):
            return None
        queryDict = {'_id': ObjectId(id)}
        game = cls.load_game(queryDict)  
        return game

    @classmethod
    def load_game_by_name(cls, name):
        queryDict = {'gameNameLowerCase': name.lower()}
        game = cls.load_game(queryDict)  
        return game

    @classmethod
    def load_game(cls, queryDict):
        game = mongo.db.games.find_one(queryDict)
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