# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 13:45:07 2019

@author: Jason
"""

from flask import Blueprint, request, redirect, url_for, abort, make_response, jsonify
from flask import current_app as app
from flask_login import current_user, login_user, logout_user, login_required
from models.User import User
from models.Database import mongo
from models.WebApplicationClient import client
import json
import requests

login_blueprint = Blueprint('Login', __name__)

@login_blueprint.route('/')
def index():
    if current_user.is_authenticated:
        return ('<p>Hello, {}! You\'re logged in! Email: {}</p>'
            '<div><p>Google Profile Picture:</p>'
            '<img src="{}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'.format(
            current_user.name, current_user.email, current_user.profilePic))
    else:
        return '<a class="button" href="/login">Google Login</a>'

@login_blueprint.route('/login')
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"]
    )
    return redirect(request_uri)

@login_blueprint.route("/login/callback")
def callback():
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
        users_email = userinfo_response.json()['email']
        picture = userinfo_response.json()['picture']
        users_name = userinfo_response.json()['given_name']
    else:
        return abort(make_response(jsonify(message='User email not available or not verified by Google.'), 500))
    
    user = User(username=users_email, name=users_name, email=users_email, profilePic=picture)
    
    storedUser = mongo.db.users.find_one({'emailAddress': user.email})
    if not storedUser:
        mongo.db.users.insert_one({
                'username': user.email, 
                'name': user.name, 
                'emailAddress': user.email, 
                'picture': user.profilePic
                })
    
    login_user(user)
    
    return redirect(url_for("Login.index"))

@login_blueprint.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("Login.index"))

def get_google_provider_cfg():
    return requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()
