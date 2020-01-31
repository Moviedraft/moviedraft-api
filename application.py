# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 08:45:14 2019

@author: Jason
"""

import sys
import os
from flask import Flask, request, make_response
from flask.sessions import SecureCookieSessionInterface
from flask_cors import CORS
from utilities.Database import mongo
from utilities.WebApplicationClient import client
from utilities.RestApi import restApi
from utilities.Mailer import mail
from utilities.Executor import executor
from utilities.JWTManager import jwt
from namespaces.Movies import movies_namespace
from namespaces.Authentication import login_namespace
from namespaces.Authentication import logout_namespace
from namespaces.Games import games_namespace
from namespaces.Rules import rules_namespace
from namespaces.Users import users_namespace

sys.path.insert(0, '/models/')
sys.path.insert(1, '/namespaces/')
sys.path.insert(2, '/enums/')
sys.path.insert(2, '/decorators/')
sys.path.insert(3, '/utilities/')

application = app = Flask(__name__)

app.config['MONGO_URI'] = os.environ['MONGO_CONNECTION_STRING']
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['GOOGLE_CLIENT_ID'] = os.environ['GOOGLE_CLIENT_ID']
app.config['GOOGLE_CLIENT_SECRET'] = os.environ['GOOGLE_CLIENT_SECRET']
app.config['GOOGLE_DISCOVERY_URL'] = os.environ['GOOGLE_DISCOVERY_URL']
app.config['WHITELIST_ORIGINS'] = os.environ['WHITELIST_ORIGINS']
app.config['MAIL_SERVER'] = os.environ['MAIL_SERVER']
app.config['MAIL_PORT'] = os.environ['MAIL_PORT']
app.config['MAIL_USE_SSL'] = os.environ['MAIL_USE_SSL']
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
app.config['GOOGLE_TOKENINFO_URI'] = os.environ['GOOGLE_TOKENINFO_URI']
app.config['JWT_ALGORITHM'] = os.environ['JWT_ALGORITHM']
app.config['JWT_EXP_DELTA_MINUTES'] = os.environ['JWT_EXP_DELTA_MINUTES']

mongo.init_app(app)
restApi.init_app(app)
mail.init_app(app)
executor.init_app(app)
jwt.init_app(app)
CORS(app, supports_credentials=True, resources={r"/*": {'origins': [app.config['WHITELIST_ORIGINS'].split(';')]}})

client.client_id = app.config['GOOGLE_CLIENT_ID']

session_serializer = SecureCookieSessionInterface().get_signing_serializer(app)

restApi.add_namespace(movies_namespace)
restApi.add_namespace(login_namespace)
restApi.add_namespace(logout_namespace)
restApi.add_namespace(games_namespace)
restApi.add_namespace(rules_namespace)
restApi.add_namespace(users_namespace)

@app.before_request
def before_request():
    whiteListOrigins = app.config['WHITELIST_ORIGINS'].split(';')
    if request.method == "OPTIONS":
        response = make_response()
        if request.headers['Origin'] in whiteListOrigins:
            response.headers.add("Access-Control-Allow-Origin", request.headers['Origin'])
        response.headers.add('Access-Control-Allow-Headers', 'Authorization')
        response.headers.add('Access-Control-Allow-Methods', '*')
        return response
    
@app.after_request
def after_request(response):
    response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains; preload'
    response.headers['Access-Control-Expose-Headers'] = 'Authorization'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization'
    
    return response

if __name__ == '__main__':
    app.run()