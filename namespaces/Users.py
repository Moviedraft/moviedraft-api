# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 00:14:05 2020

@author: Jason
"""

from flask import make_response
from flask_restplus import Namespace, Resource, fields
from flask_login import login_required, current_user
from decorators.RoleAccessDecorator import requires_role
from enums.Role import Role

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
    @login_required
    @requires_role(Role.user.value)
    @users_namespace.response(200, 'Success', users_namespace.models['User'])
    @users_namespace.response(500, 'Internal Server Error')
    def get(self):
        return make_response(current_user.__dict__, 200)
        