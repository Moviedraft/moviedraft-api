# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 21:14:25 2019

@author: Jason
"""

from utilities.Database import mongo
from datetime import datetime
from bson.objectid import ObjectId

class GameModel():
    def __init__(self, id, gameName, gameNameLowerCase, startDate, endDate, auctionDate,
                 playerBuyIn, dollarSpendingCap, movies, auctionItemsExpireInSeconds, 
                 rules, commissionerId, playerIds):
        self._id = id
        self.gameName = gameName
        self.gameNameLowerCase = gameNameLowerCase
        self.startDate = startDate
        self.endDate = endDate
        self.auctionDate = auctionDate
        self.playerBuyIn = playerBuyIn
        self.dollarSpendingCap = dollarSpendingCap
        self.movies = movies
        self.auctionItemsExpireInSeconds = auctionItemsExpireInSeconds
        self.rules = rules
        self.commissionerId = commissionerId
        self.playerIds = playerIds
    
    def update_game(self):
        mongo.db.games.replace_one({'_id': ObjectId(self._id)}, 
                                   {'gameName': self.gameName,
                                    'gameNameLowerCase': self.gameName.lower(),
                                    'startDate': self.startDate,
                                    'endDate': self.endDate,
                                    'auctionDate': self.auctionDate,
                                    'playerBuyIn': self.playerBuyIn,
                                    'dollarSpendingCap': self.dollarSpendingCap,
                                    'movies': self.movies,
                                    'auctionItemsExpireInSeconds': self.auctionItemsExpireInSeconds,
                                    'rules': self.rules,
                                    'commissionerId': self.commissionerId,
                                    'playerIds': self.playerIds
                                    })
        updatedGame = GameModel.load_game_by_name(self.gameName)
        return updatedGame
    
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
                id=str(game['_id']),
                gameName=game['gameName'],
                gameNameLowerCase=game['gameName'].lower(),
                startDate=datetime.strftime(game['startDate'], '%Y-%m-%d'),
                endDate=datetime.strftime(game['endDate'], '%Y-%m-%d'),
                auctionDate=game['auctionDate'],
                playerBuyIn=game['playerBuyIn'],
                dollarSpendingCap=game['dollarSpendingCap'],
                movies=game['movies'],
                auctionItemsExpireInSeconds=game['auctionItemsExpireInSeconds'],
                rules=game['rules'],
                commissionerId=game['commissionerId'],
                playerIds=game['playerIds']
                )