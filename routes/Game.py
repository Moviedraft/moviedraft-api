# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 20:16:39 2019

@author: Jason
"""

from flask import Blueprint, request
from flask_login import login_required
import json
from models.Database import mongo
from models.GameModel import GameModel

game_blueprint = Blueprint('Game', __name__)

@game_blueprint.route('/game', methods=['POST'])
@login_required
def create_game():
    try:
        jsonDump = json.dumps(request.json)
        jsonData = json.loads(jsonDump)
        game = GameModel(
                gameName=jsonData['gameName'], 
                dollarSpendingCap=jsonData['dollarSpendingCap']
                )
    except:
        return "Request is not valid JSON.", 400

    try:
        if not GameModel.load_game(game.gameName):
            result = mongo.db.games.insert_one(game.__dict__)
        else:
            return "Game with that name already exists.", 409
    except:
        return "Game insert operation failed.", 500
    
    return str(result.inserted_id), 200

@game_blueprint.route('/game/<gameName>', methods=['GET'])
@login_required
def get_game(gameName):
    game = GameModel.load_game(gameName)
    if game:
        return game.__dict__, 200
    return "Game name: \'{}\' could not be found.".format(gameName), 404

@game_blueprint.route('/game/<gameName>', methods=['DELETE'])
@login_required
def delete_game(gameName):
    game = GameModel.load_game(gameName)
    if game:
        try:
            mongo.db.games.delete_one({'gameName': game.gameName})
            return "", 200
        except:
            return "Game name: \'{}\' could not be deleted".format(gameName), 500