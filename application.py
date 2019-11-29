# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 08:45:14 2019

@author: Jason
"""

import sys
import os
from flask import Flask
from flask_login import LoginManager
from models.User import User
from models.Database import mongo
from routes.Login import login_blueprint
from routes.Games import games_blueprint
from routes.Movies import movies_blueprint

sys.path.insert(0, '/models/')
sys.path.insert(1, '/routes/')
sys.path.insert(2, '/enums/')

application = app = Flask(__name__, template_folder='templates')

app.config["MONGO_URI"] = os.environ['MONGO_CONNECTION_STRING']
app.config["SECRET_KEY"] = os.environ['SECRET_KEY']

mongo.init_app(app)
    
login = LoginManager(app)

@app.route('/')
def index():
    return 'This is the index page'

@login.user_loader
def load_user(username):
    u = mongo.db.users.find_one({"username": username})
    if not u:
        return None
    return User(username=u['username'])

app.register_blueprint(login_blueprint)
app.register_blueprint(games_blueprint)
app.register_blueprint(movies_blueprint)

if __name__ == "__main__":
    app.run()