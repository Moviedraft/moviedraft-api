# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 21:14:25 2019

@author: Jason
"""

from models.Database import mongo

class GameModel():
    def __init__(self, GameName, DollarSpendingCap):
        self.GameName = GameName
        self.DollarSpendingCap = DollarSpendingCap
        
    def load_game(gamename):
        game = mongo.db.Games.find_one({"GameName": gamename})
        if not game:
            return None
        return GameModel(
                GameName=game['GameName'], 
                DollarSpendingCap=game['DollarSpendingCap']
                )