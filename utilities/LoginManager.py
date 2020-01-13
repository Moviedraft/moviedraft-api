# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 11:10:32 2019

@author: Jason
"""

from flask_login import LoginManager
from bson.objectid import ObjectId
from utilities.Database import mongo
from models.UserModel import UserModel

login = LoginManager()

@login.user_loader
def load_user(id):
    print(id)
    user = mongo.db.users.find_one({'_id': ObjectId(id)})
    if not user:
        return None
    return UserModel(id=str(user['_id']),
            userHandle=user['userHandle'],
            firstName = user['firstName'],
            lastName = user['lastName'],
            email = user['emailAddress'],
            picture = user['picture'],
            role = user['role']
            )