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
def CreateGame():
    try:
        jsonDump = json.dumps(request.json)
        jsonData = json.loads(jsonDump)
        game = GameModel(
                GameName=jsonData['GameName'], 
                DollarSpendingCap=jsonData['DollarSpendingCap']
                )
    except:
        return "Request is not valid JSON.", 400

    try:
        if not GameModel.load_game(game.GameName):
            result = mongo.db.Games.insert_one(game.__dict__)
        else:
            return "Game with that name already exists.", 409
    except:
        return "Game insert operation failed.", 500
    
    return str(result.inserted_id), 200

@game_blueprint.route('/game/<gamename>', methods=['GET'])
@login_required
def GetGame(gamename):
    game = GameModel.load_game(gamename)
    if game:
        return game.__dict__, 200
    return "Game name: \'{}\' could not be found.".format(gamename), 404

@game_blueprint.route('/game/<gamename>', methods=['DELETE'])
@login_required
def DeleteGame(gamename):
    game = GameModel.load_game(gamename)
    if game:
        try:
            mongo.db.Games.delete_one({'GameName': game.GameName})
            return "", 200
        except:
            return "Game name: \'{}\' could not be deleted".format(gamename), 500