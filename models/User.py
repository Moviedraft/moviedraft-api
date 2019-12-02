# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 10:03:06 2019

@author: Jason
"""
from werkzeug.security import check_password_hash

class User():
    def __init__(self, username, name, email, profilePic):
        self.username = username
        self.name = name
        self.email = email
        self.profilePic = profilePic

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