# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 20:16:39 2019

@author: Jason
"""

from flask import Blueprint, request, abort, make_response, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import json
from models.Database import mongo
from models.GameModel import GameModel
from models.User import User

games_blueprint = Blueprint('Games', __name__)

@games_blueprint.route('/games', methods=['POST'])
@login_required
def create_game():
    currentUserId = User.get_user_id(current_user.username)
    try:
        jsonDump = json.dumps(request.json)
        jsonData = json.loads(jsonDump)
        game = GameModel(
                gameName=jsonData['gameName'],
                gameNameLowerCase=jsonData['gameName'].lower(),
                startDate=datetime.strptime(jsonData['startDate'], '%Y-%m-%d'),
                endDate=datetime.strptime(jsonData['endDate'], '%Y-%m-%d'),
                playerBuyIn=jsonData['playerBuyIn'],
                dollarSpendingCap=jsonData['dollarSpendingCap'],
                movies=jsonData['movies'],
                rules=jsonData['rules'],
                commissionerId=currentUserId
                )
    except:
        abort(make_response(jsonify(message='Request is not valid JSON.'), 500))
    
    if not GameModel.load_game(game.gameName.lower()) == None:
        abort(make_response(jsonify(message='Game name: \'{}\' already exists.'.format(game.gameName)), 409))
        
    result = mongo.db.games.insert_one(game.__dict__)

    return str(result.inserted_id), 200

@games_blueprint.route('/games/<gameName>', methods=['GET'])
@login_required
def get_game(gameName):
    game = GameModel.load_game(gameName.lower())
    if game:
        return game.__dict__, 200
    abort(make_response(jsonify(message='Game name: \'{}\' could not be found.'.format(gameName)), 404))

@games_blueprint.route('/games/<gameName>', methods=['DELETE'])
@login_required
def delete_game(gameName):
    game = GameModel.load_game(gameName.lower())
    if game:
        try:
            mongo.db.games.delete_one({'gameName': game.gameName})
            return '', 200
        except:
            abort(make_response(jsonify('Game name: \'{}\' could not be deleted'.format(gameName)), 500))
    abort(make_response(jsonify(message='Game name: \'{}\' could not be found.'.format(gameName)), 404))