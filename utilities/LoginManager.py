# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 11:10:32 2019

@author: Jason
"""

from flask_login import LoginManager
from utilities.Database import mongo
from models.UserModel import UserModel

login = LoginManager()

@login.user_loader
def load_user(username):
    user = mongo.db.users.find_one({'username': username})
    if not user:
        return None
    return UserModel(
            username=user['username'],
            firstName = user['firstName'],
            lastName = user['lastName'],
            email = user['emailAddress'],
            profilePic = user['picture'],
            role = user['role']
            )