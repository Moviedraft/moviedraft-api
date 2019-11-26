# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 08:45:14 2019

@author: Jason
"""

import sys
from flask import Flask
from flask_login import LoginManager
from models.User import User
from models.Database import mongo
from routes.Login import login_blueprint
from routes.Game import game_blueprint

sys.path.insert(0, '/models/')
sys.path.insert(1, '/routes/')

application = app = Flask(__name__, template_folder='templates')

app.config["MONGO_URI"] = "mongodb+srv://JasonK58:e7g3Xy5WwPSD1k5H@cluster0-mxtug.gcp.mongodb.net/MovieDraft?retryWrites=true&w=majority"
app.config["SECRET_KEY"] = 'onehundredpercentsecret'

mongo.init_app(app)
    
login = LoginManager(app)

@app.route('/')
def index():
    return 'This is the index page'

@login.user_loader
def load_user(username):
    u = mongo.db.Users.find_one({"Username": username})
    if not u:
        return None
    return User(username=u['Username'])

app.register_blueprint(login_blueprint)
app.register_blueprint(game_blueprint)

if __name__ == "__main__":
    app.run()