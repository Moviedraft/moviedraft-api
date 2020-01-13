# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 13:45:07 2019

@author: Jason
"""

from flask import request, abort, make_response, jsonify
from flask import current_app as app
from flask_login import login_user, logout_user, login_required
from flask_restplus import Namespace, Resource, fields
from models.UserModel import UserModel
from utilities.Database import mongo
from utilities.WebApplicationClient import client
from decorators.RoleAccessDecorator import requires_role
from enums.Role import Role
import json
import requests

login_namespace = Namespace('login', description='Site login using Google Oauth2.')

login_namespace.model('User',{
        'id': fields.String,
        'userHandle': fields.String,
        'firstName': fields.String,
        'lastName': fields.String,
        'email': fields.String,
        'picture': fields.String,
        'role': fields.Integer
        })

login_namespace.model('RequestAuthUriModel',{ 
        'requestUri': fields.String
        })

@login_namespace.route('')
class RequestAuthUri(Resource):
    @login_namespace.response(200, 'Success', login_namespace.models['RequestAuthUriModel'])
    @login_namespace.response(500, 'Internal Server Error')
    def get(self):
        google_provider_cfg = get_google_provider_cfg()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        request_uri = client.prepare_request_uri(
                authorization_endpoint,
                redirect_uri=request.base_url + "/callback",
                scope=["openid", "email", "profile"]
                )
    
        return make_response(jsonify(requestUri=request_uri), 200)

@login_namespace.route('/callback')
class LoginCallback(Resource):
    @login_namespace.response(200, 'Success', login_namespace.models['User'])
    @login_namespace.response(500, 'Internal Server Error')
    def get(self):
        code = request.args.get('code')
        google_provider_cfg = get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]
    
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=request.base_url,
            code=code
            )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(app.config['GOOGLE_CLIENT_ID'], app.config['GOOGLE_CLIENT_SECRET'])
            )

        client.parse_request_body_response(json.dumps(token_response.json()))
    
        userinfo_endpoint = google_provider_cfg['userinfo_endpoint']
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
    
        if userinfo_response.json().get('email_verified'):
            userEmail = userinfo_response.json()['email']
            picture = userinfo_response.json()['picture']
            firstName = userinfo_response.json()['given_name']
            lastName = userinfo_response.json()['family_name']
        
        else:
            return abort(make_response(jsonify(message='User email not available or not verified by Google.'), 500))
    
        storedUser = mongo.db.users.find_one({'emailAddress': userEmail})
    
        if not storedUser:
            mongo.db.users.insert_one({
                'userHandle': userEmail.split('@')[0], 
                'firstName': firstName,
                'lastName': lastName,
                'emailAddress': userEmail, 
                'picture': picture,
                'role': 1
                })
    
            storedUser = mongo.db.users.find_one({'emailAddress': userEmail})

        userModel = UserModel(id=str(storedUser['_id']),
                    userHandle=storedUser['userHandle'], 
                    firstName=storedUser['firstName'], 
                    lastName=storedUser['lastName'], 
                    email=storedUser['emailAddress'], 
                    picture=storedUser['picture'],
                    role=storedUser['role'])
        
        login_user(userModel)

        return make_response(userModel.__dict__, 200)

logout_namespace = Namespace('logout', description='Site logout.')

@logout_namespace.route('')
class Logout(Resource):
    @login_required
    @requires_role(Role.user.value)
    @login_namespace.response(200, 'Success')
    @login_namespace.response(500, 'Internal Server Error')
    @login_namespace.response(401, 'Authentication Error')
    def get(self):
        logout_user()
        return make_response('', 200)    

def get_google_provider_cfg():
    return requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()
