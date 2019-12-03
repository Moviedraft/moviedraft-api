# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 21:14:25 2019

@author: Jason
"""

from models.Database import mongo

class GameModel():
    def __init__(self, gameName, gameNameLowerCase, dollarSpendingCap):
        self.gameName = gameName
        self.gameNameLowerCase = gameNameLowerCase
        self.dollarSpendingCap = dollarSpendingCap
        
    def load_game(gameNameLowerCase):
        game = mongo.db.games.find_one({"gameNameLowerCase": gameNameLowerCase})
        if not game:
            return None
        return GameModel(
                gameName=game['gameName'],
                gameNameLowerCase=game['gameNameLowerCase'],
                dollarSpendingCap=game['dollarSpendingCap']
                )