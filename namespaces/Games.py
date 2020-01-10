# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 20:16:39 2019

@author: Jason
"""

from flask import request, abort, make_response, jsonify, render_template
from flask import current_app as app
from flask_login import login_required, current_user
from flask_restplus import Namespace, Resource, fields
from datetime import datetime
from bson.objectid import ObjectId
import json
from models.Database import mongo
from models.GameModel import GameModel
from models.RuleModel import RuleModel
from models.MovieModel import MovieModel
from models.User import User
from models.Mailer import Emailer
from models.Executor import executor
from namespaces.Movies import movies_namespace
from namespaces.Rules import rules_namespace
from decorators.RoleAccessDecorator import requires_role
from enums.Role import Role

games_namespace = Namespace('games', description='Draft league game data.')

games_namespace.model('GamePayload', {
        'gameName': fields.String,
        'startDate': fields.String,
        'endDate': fields.String,
        'playerBuyIn': fields.Integer,
        'dollarSpendingCap': fields.Integer,
        'playerEmails': fields.List(fields.String),
        'movies': fields.List(fields.String),
        'rules': fields.Nested(rules_namespace.models['Rules'])
        })

games_namespace.model('GamePostResponse', {
        'id': fields.String
        })

games_namespace.model('Game', {
        'gameName': fields.String,
        'startDate': fields.String,
        'endDate': fields.String,
        'playerBuyIn': fields.Integer,
        'dollarSpendingCap': fields.Integer,
        'movies': fields.List(fields.Nested(movies_namespace.models['MovieModelFields'])),
        'rules': fields.List(fields.Nested(rules_namespace.models['Rules'])),
        'commissionerId': fields.String,
        'playerIds': fields.List(fields.String)
        })

@games_namespace.route('')
class CreateGames(Resource):
    @login_required
    @requires_role(Role.user.value)
    @games_namespace.expect(games_namespace.models['GamePayload'])
    @games_namespace.response(200, 'Success', games_namespace.models['GamePostResponse'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(400, 'Bad Request')
    @games_namespace.response(409, 'Conflict')
    @games_namespace.response(500, 'Internal Server Error')
    def post(self):
        currentUserId = User.get_user_id(current_user.username)

        jsonDump = json.dumps(request.get_json(force=True))
        jsonData = json.loads(jsonDump)
        rulesArray = []
        rulesJson = jsonData['rules']
        for rule in rulesJson:
            ruleModel = RuleModel(ruleName=rule['ruleName'], rules=rule['rules'])
            rulesArray.append(ruleModel.__dict__)
        
        playerIds = []
        playerEmailsJson = jsonData['playerEmails']
        for email in playerEmailsJson:   
            player = mongo.db.users.find_one({'emailAddress': email}, {'_id':1, 'firstName':1})
            if player:
                playerIds.append(str(player['_id']))
                recipientName = player['firstName']
            else:
                playerIds.append(email)
                recipientName = email.split('@')[0]

            executor.submit(Emailer.send_email, 
                                 'Invitation to Moviedraft', 
                                 app.config['MAIL_USERNAME'], 
                                 [email],
                                 None,
                                 render_template('InviteToGame.html', recipientName=recipientName, user=current_user))
            
            game = GameModel(
                    gameName=jsonData['gameName'],
                    gameNameLowerCase=jsonData['gameName'].lower(),
                    startDate=datetime.strptime(jsonData['startDate'], '%Y-%m-%d'),
                    endDate=datetime.strptime(jsonData['endDate'], '%Y-%m-%d'),
                    playerBuyIn=jsonData['playerBuyIn'],
                    dollarSpendingCap=jsonData['dollarSpendingCap'],
                    movies=jsonData['movies'],
                    rules=rulesArray,
                    commissionerId=currentUserId,
                    playerIds=playerIds
                    )

        if not GameModel.load_game(game.gameName.lower()) == None:
            abort(make_response(jsonify(message='Game name: \'{}\' already exists.'.format(game.gameName)), 409))
        
        result = mongo.db.games.insert_one(game.__dict__)
        
        return make_response(jsonify(id=str(result.inserted_id)), 200)
    
@games_namespace.route('/<string:gameName>')
class Game(Resource):
    @login_required
    @requires_role(Role.user.value)
    @games_namespace.response(200, 'Success', games_namespace.models['Game'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def get(self, gameName):
        game = GameModel.load_game(gameName.lower())
    
        if game:
            movies = []
            for movieId in game.movies:
                movieResult = mongo.db.movies.find_one({'_id': ObjectId(movieId)})
                movieModel = MovieModel(id=movieResult['_id'],
                                        releaseDate=movieResult['releaseDate'],
                                        title=movieResult['title'],
                                        releaseType=movieResult['releaseType'],
                                        distributor=movieResult['distributor'],
                                        lastUpdated=movieResult['lastUpdated'])
                movies.append(movieModel.__dict__)          
                game.movies = movies
            
            commissionerId = game.commissionerId
            game.commissionerId = str(commissionerId)
            
            playerIds = []
            for id in game.playerIds:
                if ObjectId.is_valid(id):
                    player = mongo.db.users.find_one({'_id': ObjectId(id)}, {'_id':1})
                    if player:
                        playerIds.append(str(player['_id']))
            game.playerIds = playerIds
            
            return make_response(jsonify(game.__dict__), 200)
    
        abort(make_response(jsonify(message='Game name: \'{}\' could not be found.'.format(gameName)), 404))

    @login_required
    @requires_role(Role.admin.value)
    @games_namespace.response(200, 'Success')
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def delete(self, gameName):
        game = GameModel.load_game(gameName.lower())
        if game:
            try:
                mongo.db.games.delete_one({'gameName': game.gameName})
                return make_response('', 200)
            except:
                abort(make_response(jsonify('Game name: \'{}\' could not be deleted'.format(gameName)), 500))
        abort(make_response(jsonify(message='Game name: \'{}\' could not be found.'.format(gameName)), 404))