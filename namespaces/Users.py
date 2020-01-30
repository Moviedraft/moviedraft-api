# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 00:14:05 2020

@author: Jason
"""

from flask import make_response
from flask_restplus import Namespace, Resource, fields
from flask_jwt_extended import get_jwt_identity,jwt_required
from models.UserModel import UserModel

users_namespace = Namespace('users', description='User information.')

users_namespace.model('User',{
        'id': fields.String,
        'userHandle': fields.String,
        'firstName': fields.String,
        'lastName': fields.String,
        'email': fields.String,
        'picture': fields.String,
        'role': fields.Integer
        })

@users_namespace.route('/current')
class Users(Resource):
    @jwt_required
    @users_namespace.response(200, 'Success', users_namespace.models['User'])
    @users_namespace.response(500, 'Internal Server Error')
    def get(self):
        userIdentity = get_jwt_identity()
        currentUser = UserModel.load_user_by_id(userIdentity['id'])
        return make_response(currentUser.__dict__, 200)
        