# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 08:45:14 2019

@author: Jason
"""

import sys
import os
from flask import Flask, session
from flask_cors import CORS
from datetime import timedelta
from models.Database import mongo
from models.WebApplicationClient import client
from models.LoginManager import login
from models.RestApi import restApi
from namespaces.Movies import movies_namespace
from namespaces.Authentication import login_namespace
from namespaces.Authentication import logout_namespace
from namespaces.Games import games_namespace
from namespaces.Rules import rules_namespace

sys.path.insert(0, '/models/')
sys.path.insert(1, '/namespaces/')
sys.path.insert(2, '/enums/')
sys.path.insert(2, '/decorators/')

application = app = Flask(__name__)

app.config['MONGO_URI'] = os.environ['MONGO_CONNECTION_STRING']
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['GOOGLE_CLIENT_ID'] = os.environ['GOOGLE_CLIENT_ID']
app.config['GOOGLE_CLIENT_SECRET'] = os.environ['GOOGLE_CLIENT_SECRET']
app.config['GOOGLE_DISCOVERY_URL'] = os.environ['GOOGLE_DISCOVERY_URL']
app.config['SESSION_TIMEOUT_MINUTES'] = os.environ['SESSION_TIMEOUT_MINUTES']

mongo.init_app(app)
login.init_app(app)
restApi.init_app(app)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:8000"}})

client.client_id = app.config['GOOGLE_CLIENT_ID']

restApi.add_namespace(movies_namespace)
restApi.add_namespace(login_namespace)
restApi.add_namespace(logout_namespace)
restApi.add_namespace(games_namespace)
restApi.add_namespace(rules_namespace)

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=int(app.config['SESSION_TIMEOUT_MINUTES']))

if __name__ == '__main__':
    app.run()