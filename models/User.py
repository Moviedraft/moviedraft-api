# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 10:03:06 2019

@author: Jason
"""
from werkzeug.security import check_password_hash
from models.Database import mongo

class User():
    def __init__(self, username, firstName, lastName, email, profilePic, role):
        self.username = username
        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        self.profilePic = profilePic
        self.role = role

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
        return self.username
    
    @staticmethod
    def validate_login(password_hash, password):
        return check_password_hash(password_hash, password)
    
    @staticmethod
    def get_user_id(username):
        user = mongo.db.users.find_one({'username': username})
        if not user:
            return None
        return user['_id']
    
    def allowed(self, requiredRole):
        return self.role >= requiredRole