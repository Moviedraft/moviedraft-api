# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 10:39:46 2020

@author: Jason
"""

from utilities.Database import mongo
from bson.objectid import ObjectId

class UserGameModel():
    def __init__(self, id, game_id, user_id, gameName):
        self._id = id
        self.game_id = game_id
        self.user_id = user_id
        self.gameName = gameName
    
    def serialize(self): 
        return {           
        'id': self._id,
        'game_id': self.game_id,
        'user_id': self.user_id,
        'gameName': self.gameName
        }
    
    def update_userGameModel(self):
        result = mongo.db.usergames.update_one({'_id': ObjectId(self._id)}, 
                                            { '$set': {'game_id': ObjectId(self.game_id),
                                             'user_id': ObjectId(self.user_id),
                                             'gameName': self.gameName
                                            }})
        if result.modified_count == 1:
            return self.load_user_game_by_id(self._id)
        
        return None
    
    @classmethod
    def create_userGameModel(cls, game_id, user_id, gameName):
        if not ObjectId.is_valid(game_id) or not ObjectId.is_valid(user_id):
            return None
        
        userGameModel=UserGameModel(id=ObjectId(),
                                    game_id=ObjectId(game_id),
                                    user_id=ObjectId(user_id),
                                    gameName=gameName)
        result = mongo.db.usergames.insert_one(userGameModel.__dict__)
        
        if result.acknowledged:
            insertedUserGame = cls.load_user_game_by_id(str(result.inserted_id))
            return insertedUserGame
        
        return None
    
    @classmethod
    def load_user_game_by_id(cls, id):
        if not ObjectId.is_valid(id):
            return None
        queryDict = {'_id': ObjectId(id)}
        userGames = cls.load_user_games(queryDict)
        return userGames
    
    @classmethod
    def load_user_game_by_game_id(cls, game_id):
        if not ObjectId.is_valid(game_id):
            return None
        queryDict = {'game_id': ObjectId(game_id)}
        userGames = cls.load_user_games(queryDict)
        return userGames
    
    @classmethod
    def load_user_games_by_user_id(cls, user_id):
        if not ObjectId.is_valid(user_id):
            return None
        queryDict = {'user_id': ObjectId(user_id)}
        userGames = cls.load_user_games(queryDict)
        return userGames
        
    
    @classmethod
    def load_user_games(cls, queryDict):
        games = mongo.db.usergames.find(queryDict)
        userGames = []
        for game in games:
            userGame = UserGameModel(id=str(game['_id']), 
                                     game_id=str(game['game_id']), 
                                     user_id=str(game['user_id']), 
                                     gameName=game['gameName']
                                     )
            userGames.append(userGame)
        
        return userGames
    
    @classmethod
    def delete_user_games_by_game_id(cls, game_id):
        if not ObjectId.is_valid(game_id):
            return None
        queryDict = {'game_id': ObjectId(game_id)}
        result = cls.delete_user_games(queryDict)
        return result
    
    @classmethod
    def delete_user_games(cls, queryDict):
        mongo.db.usergames.delete_many(queryDict)
        