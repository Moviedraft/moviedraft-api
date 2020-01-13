# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 10:03:06 2019

@author: Jason
"""
from werkzeug.security import check_password_hash

class UserModel():
    def __init__(self, id, userHandle, firstName, lastName, email, picture, role):
        self.id = id
        self.userHandle = userHandle
        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        self.picture = picture
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
    
    @staticmethod
    def validate_login(password_hash, password):
        return check_password_hash(password_hash, password)

    def get_id(self):
        return self.id

    def allowed(self, requiredRole):
        return self.role >= requiredRole