# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 20:16:39 2019

@author: Jason
"""

from flask import request, abort, make_response, jsonify, render_template, session
from flask import current_app as app
from flask_login import login_required, current_user
from flask_restplus import Namespace, Resource, fields, reqparse
from datetime import datetime
from bson.objectid import ObjectId
import json
from utilities.Database import mongo
from utilities.Mailer import Emailer
from utilities.Executor import executor
from models.GameModel import GameModel
from models.RuleModel import RuleModel
from models.MovieModel import MovieModel
from models.UserModel import UserModel
from namespaces.Movies import movies_namespace
from namespaces.Rules import rules_namespace
from decorators.RoleAccessDecorator import requires_admin
from enums.Role import Role

games_namespace = Namespace('games', description='Draft league game data.')

gamePayload = games_namespace.model('GamePayload', {
        'gameName': fields.String,
        'startDate': fields.String,
        'endDate': fields.String,
        'playerBuyIn': fields.Integer,
        'dollarSpendingCap': fields.Integer,
        'playerIds': fields.List(fields.String),
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
    @games_namespace.expect(games_namespace.models['GamePayload'])
    @games_namespace.response(200, 'Success', games_namespace.models['GamePostResponse'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(400, 'Bad Request')
    @games_namespace.response(409, 'Conflict')
    @games_namespace.response(500, 'Internal Server Error')
    def post(self):
        jsonDump = json.dumps(request.get_json(force=True))
        jsonData = json.loads(jsonDump)
        rulesArray = []
        rulesJson = jsonData['rules']
        for rule in rulesJson:
            ruleModel = RuleModel(ruleName=rule['ruleName'], rules=rule['rules'])
            rulesArray.append(ruleModel.__dict__)
        
        playerIds = []
        recipientDict = {}
        playerEmailsJson = jsonData['playerEmails']
        for email in playerEmailsJson:   
            player = UserModel.load_user_by_email(email)
            if player:
                playerIds.append(player.id)
                recipientName = player.firstName
                recipientDict[email] = recipientName
            else:
                playerIds.append(email.lower())
                recipientName = email.split('@')[0]
                recipientDict[email] = recipientName

            game = GameModel(
                    gameName=jsonData['gameName'],
                    gameNameLowerCase=jsonData['gameName'].lower(),
                    startDate=datetime.strptime(jsonData['startDate'], '%Y-%m-%d'),
                    endDate=datetime.strptime(jsonData['endDate'], '%Y-%m-%d'),
                    playerBuyIn=jsonData['playerBuyIn'],
                    dollarSpendingCap=jsonData['dollarSpendingCap'],
                    movies=jsonData['movies'],
                    rules=rulesArray,
                    commissionerId=session['user_id'],
                    playerIds=playerIds
                    )

        if not GameModel.load_game(game.gameNameLowerCase) == None:
            abort(make_response(jsonify(message='Game name: \'{}\' already exists.'.format(game.gameName)), 409))
        
        result = mongo.db.games.insert_one(game.__dict__)
        
        for email in playerEmailsJson:
            executor.submit(Emailer.send_email, 
                                 'Invitation to Moviedraft', 
                                 app.config['MAIL_USERNAME'], 
                                 [email],
                                 None,
                                 render_template('InviteToGame.html', 
                                                 recipientName=recipientDict[email], 
                                                 user=current_user,
                                                 gameName=game.gameName))
            
        return make_response(jsonify(id=str(result.inserted_id)), 200)
    
@games_namespace.route('/<string:gameName>')
class Game(Resource):
    @login_required
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
    @requires_admin
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
    
    @login_required
    @games_namespace.expect(gamePayload)
    @games_namespace.response(200, 'Success', games_namespace.models['Game'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(403, 'Forbidden')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def put(self, gameName):
        parser = reqparse.RequestParser()
        parser.add_argument('gameName', required=True)
        parser.add_argument('startDate', type=lambda x: datetime.strptime(x,'%Y-%m-%d'), required=True)
        parser.add_argument('endDate', type=lambda x: datetime.strptime(x,'%Y-%m-%d'), required=True)
        parser.add_argument('playerBuyIn', type=int, required=True)
        parser.add_argument('dollarSpendingCap', type=int, required=True)
        parser.add_argument('playerIds', type=list, location='json', required=True)
        parser.add_argument('movies', type=list, location='json', required=True)
        parser.add_argument('rules', type=list, location='json', required=True)
        args = parser.parse_args()
        
        existingGame = GameModel.load_game(gameName.lower())
        
        if not existingGame:
            abort(make_response(jsonify(message='Game name: \'{}\' could not be found.'.format(gameName)), 404))
            
        if existingGame.commissionerId != current_user.id:
            abort(make_response(jsonify(message='You are not authorized to access this resource.'), 403))
        
        playerIds = []
        for value in args['playerIds'] or []:
            sendMail = False
            player = UserModel.load_user_by_id(value)
            if player:
                playerIds.append(player.id)
                if player.id not in existingGame.playerIds:
                    recipientName = player.firstName
                    email = player.email
                    sendMail = True
            else:
                playerIds.append(value)
                recipientName = value.split('@')[0]
                email = value
                sendMail = True
            
            if sendMail:
                executor.submit(Emailer.send_email,
                                'Invitation to Moviedraft', 
                                app.config['MAIL_USERNAME'], 
                                [email],
                                None,
                                render_template('InviteToGame.html', 
                                                recipientName=recipientName, 
                                                user=current_user,
                                                gameName=existingGame.gameName))
            
        args['playerIds'] = playerIds
        
        movieIds = []
        for value in args['movies'] or []:
            movie = mongo.db.movies.find_one({'_id': ObjectId(value)}, {'_id':1})
            if movie:
                movieIds.append(str(movie['_id']))
        args['movies'] = movieIds

        for key, value in args.items():
            setattr(existingGame, key, value or getattr(existingGame, key))
            if key.lower() == 'gamename':
                setattr(existingGame, 'gameNameLowerCase', value.lower())
                
        ruleArray = []
        for value in args['rules'] or []:
            existingRule = mongo.db.rules.find_one({'ruleName': value['ruleName']}, {'_id':1})
            if existingRule:
                ruleArray.append(value)
        args['rules'] = ruleArray
        
        mongo.db.games.replace_one({'gameName': gameName}, existingGame.__dict__)
        updatedGame = GameModel.load_game(existingGame.gameNameLowerCase)
        
        return make_response(updatedGame.__dict__, 200)
    
    