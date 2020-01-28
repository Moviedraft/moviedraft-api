# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 08:45:14 2019

@author: Jason
"""

import sys
import os
from flask import Flask, session, request
from flask.sessions import SecureCookieSessionInterface
from flask_cors import CORS
from datetime import timedelta
from utilities.Database import mongo
from utilities.WebApplicationClient import client
from utilities.LoginManager import login
from utilities.RestApi import restApi
from utilities.Mailer import mail
from utilities.Executor import executor
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
app.config['SESSION_TIMEOUT_MINUTES'] = os.environ['SESSION_TIMEOUT_MINUTES']
app.config['SESSION_COOKIE_HTTPONLY'] = os.environ['SESSION_COOKIE_HTTPONLY']
app.config['SESSION_COOKIE_SAMESITE'] = os.environ['SESSION_COOKIE_SAMESITE']
app.config['SESSION_COOKIE_SECURE'] = os.environ['SESSION_COOKIE_SECURE']
app.config['WHITELIST_ORIGIN'] = os.environ['WHITELIST_ORIGIN']
app.config['MAIL_SERVER'] = os.environ['MAIL_SERVER']
app.config['MAIL_PORT'] = os.environ['MAIL_PORT']
app.config['MAIL_USE_SSL'] = os.environ['MAIL_USE_SSL']
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
app.config['GOOGLE_TOKENINFO_URI'] = os.environ['GOOGLE_TOKENINFO_URI']

mongo.init_app(app)
login.init_app(app)
restApi.init_app(app)
mail.init_app(app)
executor.init_app(app)
CORS(app, supports_credentials=True, resources={r"/*": {'origins': app.config['WHITELIST_ORIGIN']}})

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
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=int(app.config['SESSION_TIMEOUT_MINUTES']))
    
@app.after_request
def after_request(response):
    session_clone = dict(_fresh=session['_fresh'], 
                         _id=session['_id'], 
                         _permanent=session['_permanent'], 
                         user_id=session['user_id'])
    session_cookie_data = session_serializer.dumps(session_clone)
    
    response.headers['Authorization'] = session_cookie_data
    response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains; preload'
    
    return response

if __name__ == '__main__':
    app.run()