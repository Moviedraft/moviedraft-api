# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 10:03:06 2019

@author: Jason
"""

from utilities.Database import mongo
from bson.objectid import ObjectId
from models.UserGameModel import UserGameModel
from utilities.DatetimeHelper import convert_to_utc, string_format_date

class UserModel():
    def __init__(self, id, userHandle, firstName, lastName, email, picture, role, lastLoggedIn, games=[]):
        self.id = id
        self.userHandle = userHandle
        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        self.picture = picture
        self.role = role
        self.lastLoggedIn = lastLoggedIn
        self.games = games

    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.id

    def allowed(self, requiredRole):
        return self.role >= requiredRole
    
    def update_user(self):
        result = mongo.db.users.update_one({'_id': ObjectId(self.id)}, 
                                            { '$set': {'userHandle': self.userHandle,
                                             'firstName': self.firstName,
                                             'lastName': self.lastName,
                                             'email': self.email,
                                             'picture': self.picture,
                                             'role': self.role,
                                             'lastLoggedIn': convert_to_utc(self.lastLoggedIn)
                                            }})
        if result.modified_count == 1:
            return self.load_user_by_id(self.id)
        
        return None
    
    @classmethod
    def load_user_by_id(cls, id):
        if not ObjectId.is_valid(id):
            return None
        queryDict = {'_id': ObjectId(id)}
        user = cls.load_user(queryDict)  
        return user

    @classmethod
    def load_user_by_email(cls, email):
        queryDict = {'emailAddress': email.lower()}
        user = cls.load_user(queryDict)  
        return user

    @classmethod
    def load_user(cls, queryDict):
        user = mongo.db.users.find_one(queryDict)
        if not user:
            return None
        
        userGames = UserGameModel.load_user_games_by_user_id(str(user['_id']))
        
        return UserModel(id = str(user['_id']),
                userHandle = user['userHandle'],
                firstName = user['firstName'],
                lastName = user['lastName'],
                email = user['emailAddress'],
                picture = user['picture'],
                role = user['role'],
                lastLoggedIn = string_format_date(user['lastLoggedIn']),
                games=[userGame.serialize() for userGame in userGames])
    