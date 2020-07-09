# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 00:14:05 2020

@author: Jason
"""

from flask import make_response, abort, jsonify
from flask_restplus import Namespace, Resource, fields, reqparse
from flask_jwt_extended import get_jwt_identity,jwt_required
from models.UserModel import UserModel
from models.BidModel import BidModel

users_namespace = Namespace('users', description='User information.')

userPatch = users_namespace.model('UserPatch',{
        'userHandle': fields.String,
        'picture': fields.String
        })

users_namespace.model('User',{
        'id': fields.String,
        'userHandle': fields.String,
        'firstName': fields.String,
        'lastName': fields.String,
        'email': fields.String,
        'picture': fields.String,
        'role': fields.Integer,
        'lastLoggedIn': fields.DateTime(dt_format=u'%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'games': fields.List(
                fields.Nested(users_namespace.model('UserGame', {
                        'id': fields.String,
                        'game_id': fields.String,
                        'user_id': fields.String,
                        'gameName': fields.String
                        }))
                )
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
    
    @jwt_required
    @users_namespace.expect(userPatch)
    @users_namespace.response(200, 'Success', users_namespace.models['User'])
    @users_namespace.response(500, 'Internal Server Error')
    def patch(self):
        parser = reqparse.RequestParser()
        parser.add_argument('userHandle')
        parser.add_argument('picture')
        args = parser.parse_args()
        
        userIdentity = get_jwt_identity()
        currentUser = UserModel.load_user_by_id(userIdentity['id'])
        
        for key, value in args.items():
            setattr(currentUser, key, value or getattr(currentUser, key))
            
        updatedUser = currentUser.update_user()
        
        currentBids = BidModel.load_bids_by_userId(updatedUser.id)
        for bid in currentBids:
            bid.userHandle = updatedUser.userHandle
            updatedBid = bid.update_bid()
            if not updatedBid:
                abort(make_response(jsonify('bid ID: \'{}\' could not be updated.'
                                            .format(bid.id)), 500))
        
        return make_response(updatedUser.__dict__, 200)
        
        