# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 21:14:25 2019

@author: Jason
"""

from models.Database import mongo

class GameModel():
    def __init__(self, gameName, dollarSpendingCap):
        self.gameName = gameName
        self.dollarSpendingCap = dollarSpendingCap
        
    def load_game(gameName):
        game = mongo.db.games.find_one({"gameName": gameName})
        if not game:
            return None
        return GameModel(
                gameName=game['gameName'], 
                dollarSpendingCap=game['dollarSpendingCap']
                )