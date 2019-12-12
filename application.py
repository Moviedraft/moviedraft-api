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
from routes.Movies import movies_namespace
from routes.Login import login_blueprint
from routes.Games import games_blueprint
from routes.Rules import rules_blueprint

sys.path.insert(0, '/models/')
sys.path.insert(1, '/routes/')
sys.path.insert(2, '/enums/')

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

app.register_blueprint(login_blueprint)
app.register_blueprint(games_blueprint)
app.register_blueprint(rules_blueprint)

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=int(app.config['SESSION_TIMEOUT_MINUTES']))

if __name__ == '__main__':
    app.run()