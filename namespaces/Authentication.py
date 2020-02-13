# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 13:45:07 2019

@author: Jason
"""

from flask import request, abort, make_response, jsonify, redirect, url_for
from flask import current_app as app
from flask_restplus import Namespace, Resource, fields
from flask_jwt_extended import (
        create_access_token, 
        create_refresh_token, 
        jwt_refresh_token_required, 
        get_jwt_identity, 
        jwt_required
        )
from bson.objectid import ObjectId
from models.UserModel import UserModel
from utilities.Database import mongo
from utilities.WebApplicationClient import client
from utilities.TokenHelpers import revoke_token, add_token_to_database
from datetime import datetime
import requests

login_namespace = Namespace('login', description='Site login using Google Oauth2.')

login_namespace.model('RequestAuthUriModel',{ 
        'requestUri': fields.String
        })

login_namespace.model('AuthModel', {
        'access_token': fields.String,
        'refresh_token': fields.String
        })

login_namespace.model('AuthRefreshModel', {
        'access_token': fields.String
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
    @login_namespace.response(302, 'Redirect')
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
        
        return redirect(url_for('login_login_validate', id_token=token_response.json()['id_token']))

@login_namespace.route('/validate')
class loginValidate(Resource):
    @login_namespace.response(200, 'Success', login_namespace.models['AuthModel'])
    @login_namespace.response(500, 'Internal Server Error')
    @login_namespace.doc(params={'id_token': 'Token retrieved from Google.'})
    def get(self):
        token = request.args.get('id_token')

        tokenValidateUrl = app.config['GOOGLE_TOKENINFO_URI'] + token
        
        tokenResponse = requests.get(tokenValidateUrl)
        
        if tokenResponse.json().get('error_description'):
            abort(make_response(jsonify(message=tokenResponse.json().get('error_description')), 500))
        
        if tokenResponse.json().get('email_verified'):
            userEmail = tokenResponse.json().get('email')
            picture = tokenResponse.json().get('picture')
            firstName = tokenResponse.json().get('given_name')
            lastName = tokenResponse.json().get('family_name')
        else:
            abort(make_response(jsonify(message='User email not available or not verified by Google.'), 500))
        
        storedUser = UserModel.load_user_by_email(userEmail)
    
        if not storedUser:
            mongo.db.users.insert_one({
                'userHandle': userEmail.split('@')[0], 
                'firstName': firstName,
                'lastName': lastName,
                'emailAddress': userEmail, 
                'picture': picture,
                'role': 1,
                'lastLoggedIn': datetime.utcnow()
                })
    
            storedUser = UserModel.load_user_by_email(userEmail)
        
        storedUser.lastLoggedIn = datetime.utcnow()
        
        updatedUser = storedUser.update_user()
        
        if updatedUser is None:
            abort(make_response(jsonify(message='Unable to update user.'), 500))
        
        access_token = create_access_token(
                identity={'tokenId': str(ObjectId()), 'id': updatedUser.id, 'role': updatedUser.role}, 
                fresh=True)
        refresh_token = create_refresh_token(identity={'tokenId': str(ObjectId()), 'id': updatedUser.id})
        
        add_token_to_database(access_token, app.config['JWT_IDENTITY_CLAIM'])
        add_token_to_database(refresh_token, app.config['JWT_IDENTITY_CLAIM'])
        
        return make_response(jsonify({ 'access_token': access_token, 
                                      'refresh_token': refresh_token }), 200)

@login_namespace.route('/refresh')
class LoginRefresh(Resource):
    @jwt_refresh_token_required
    @login_namespace.response(200, 'Success', login_namespace.models['AuthRefreshModel'])
    @login_namespace.response(500, 'Internal Server Error')
    def post(self):
        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity)
        
        if not current_user:
            abort(make_response(jsonify(message='Token is invalid.'), 401))
        
        new_access_token = create_access_token(
                identity={'tokenId': str(ObjectId()), 'id': current_user.id, 'role': current_user.role}, 
                fresh=False)
        
        add_token_to_database(new_access_token, app.config['JWT_IDENTITY_CLAIM'])
        
        return make_response(jsonify({ 'access_token': new_access_token}), 200)    
    
logout_namespace = Namespace('logout', description='Site logout.')

@logout_namespace.route('')
class Logout(Resource):
    @jwt_required
    @login_namespace.response(200, 'Success')
    @login_namespace.response(500, 'Internal Server Error')
    @login_namespace.response(401, 'Authentication Error')
    def get(self):
        identity = get_jwt_identity()
        revoke_token(identity['tokenId'])
        
        return make_response('', 200) 

def get_google_provider_cfg():
    return requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()
