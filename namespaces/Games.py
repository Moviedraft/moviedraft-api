# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 20:16:39 2019

@author: Jason
"""

from flask import request, abort, make_response, jsonify, render_template
from flask import current_app as app
from flask_restplus import Namespace, Resource, fields, reqparse
from flask_jwt_extended import get_jwt_identity, jwt_required
from datetime import datetime
from bson.objectid import ObjectId
import json
from utilities.Database import mongo
from utilities.Mailer import Emailer
from utilities.Executor import executor
from models.GameModel import GameModel
from models.RuleModel import RuleModel
from models.MovieModel import MovieModel
from models.MovieBidModel import MovieBidModel
from models.UserModel import UserModel
from models.UserGameModel import UserGameModel
from namespaces.Movies import movies_namespace
from namespaces.Rules import rules_namespace
from decorators.RoleAccessDecorator import requires_admin

games_namespace = Namespace('games', description='Draft league game data.')

gamePayload = games_namespace.model('GamePayload', {
        'gameName': fields.String,
        'startDate': fields.String,
        'endDate': fields.String,
        'auctionDate': fields.String,
        'playerBuyIn': fields.Integer,
        'dollarSpendingCap': fields.Integer,
        'playerIds': fields.List(fields.String),
        'movies': fields.List(fields.String),
        'auctionItemsExpireInSeconds': fields.Integer,
        'rules': fields.Nested(rules_namespace.models['Rules'])
        })

games_namespace.model('GamePostResponse', {
        'id': fields.String
        })

games_namespace.model('Game', {
        'gameName': fields.String,
        'startDate': fields.String,
        'endDate': fields.String,
        'auctionDate': fields.String,
        'playerBuyIn': fields.Integer,
        'dollarSpendingCap': fields.Integer,
        'movies': fields.List(fields.Nested(movies_namespace.models['MovieModelFields'])),
        'auctionItemsExpireInSeconds': fields.Integer,
        'rules': fields.List(fields.Nested(rules_namespace.models['Rules'])),
        'commissionerId': fields.String,
        'playerIds': fields.List(fields.String)
        })

@games_namespace.route('')
class CreateGames(Resource):
    @jwt_required
    @games_namespace.expect(games_namespace.models['GamePayload'])
    @games_namespace.response(200, 'Success', games_namespace.models['GamePostResponse'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(400, 'Bad Request')
    @games_namespace.response(409, 'Conflict')
    @games_namespace.response(500, 'Internal Server Error')
    def post(self):
        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity['id'])
        
        jsonDump = json.dumps(request.get_json(force=True))
        jsonData = json.loads(jsonDump)
        
        if not GameModel.load_game_by_name(jsonData['gameName']) == None:
            abort(make_response(jsonify(message='Game name: \'{}\' already exists.'.format(jsonData['gameName'])), 409))
        
        gameId = ObjectId()
        
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
                
                userGame = UserGameModel.create_userGameModel(gameId, player.id, jsonData['gameName'])
                if not userGame:
                    abort(make_response(jsonify(message='Unable to associate user with game: \'{}\'.'
                                                .format(jsonData['gameName'])), 500))
                    
                recipientName = player.firstName
                recipientDict[email] = recipientName
            else:
                playerIds.append(email.lower())
                recipientName = email.split('@')[0]
                recipientDict[email] = recipientName
        
        for movieId in jsonData['movies']:
            if not MovieModel.load_movie_by_id(movieId):
                abort(make_response(jsonify(message='MovieId: \'{}\' could not be found.'.format(movieId)), 404))
            MovieBidModel.create_empty_bid(gameId, movieId, datetime.strptime(jsonData['auctionDate'], '%Y-%m-%d %H:%M:%S'))
            
        game = GameModel(
                id=gameId,
                gameName=jsonData['gameName'],
                gameNameLowerCase=jsonData['gameName'].lower(),
                startDate=datetime.strptime(jsonData['startDate'], '%Y-%m-%d'),
                endDate=datetime.strptime(jsonData['endDate'], '%Y-%m-%d'),
                auctionDate=datetime.strptime(jsonData['auctionDate'], '%Y-%m-%d %H:%M:%S'),
                playerBuyIn=jsonData['playerBuyIn'],
                dollarSpendingCap=jsonData['dollarSpendingCap'],
                movies=jsonData['movies'],
                auctionItemsExpireInSeconds=jsonData['auctionItemsExpireInSeconds'],
                rules=rulesArray,
                commissionerId=current_user.id,
                playerIds=playerIds
                )

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
    
@games_namespace.route('/<string:gameId>')
class Game(Resource):
    @jwt_required
    @games_namespace.response(200, 'Success', games_namespace.models['Game'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def get(self, gameId):
        game = GameModel.load_game_by_id(gameId)
    
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
    
        abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))

    @jwt_required
    @requires_admin
    @games_namespace.response(200, 'Success')
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def delete(self, gameId):
        game = GameModel.load_game_by_id(gameId)
        if game:
            UserGameModel.delete_user_games_by_game_id(game._id)
            try:
                mongo.db.games.delete_one({'gameName': game.gameName})
                return make_response('', 200)
            except:
                abort(make_response(jsonify('Game ID: \'{}\' could not be deleted'.format(gameId)), 500))
                
        abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))
    
    @jwt_required
    @games_namespace.expect(gamePayload)
    @games_namespace.response(200, 'Success', games_namespace.models['Game'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(403, 'Forbidden')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def put(self, gameId):
        parser = reqparse.RequestParser()
        parser.add_argument('gameName', required=True)
        parser.add_argument('startDate', type=lambda x: datetime.strptime(x,'%Y-%m-%d'), required=True)
        parser.add_argument('endDate', type=lambda x: datetime.strptime(x,'%Y-%m-%d'), required=True)
        parser.add_argument('auctionDate', type=lambda x: datetime.strptime(x,'%Y-%m-%d %H:%M:%S'), required=True)
        parser.add_argument('playerBuyIn', type=int, required=True)
        parser.add_argument('dollarSpendingCap', type=int, required=True)
        parser.add_argument('playerIds', type=list, location='json', required=True)
        parser.add_argument('movies', type=list, location='json', required=True)
        parser.add_argument('auctionItemsExpireInSeconds', type=int, required=True)
        parser.add_argument('rules', type=list, location='json', required=True)
        args = parser.parse_args()
        
        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity['id'])
        
        existingGame = GameModel.load_game_by_id(gameId)
        
        if not existingGame:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))
            
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
        
        updatedGame = existingGame.update_game()
        
        userGames = UserGameModel.load_user_game_by_game_id(updatedGame._id)
        for userGame in userGames:
            userGame.gameName = updatedGame.gameName
            updatedUserGame = userGame.update_userGameModel()
            if not updatedUserGame:
                abort(make_response(jsonify('Game could not be updated for gameId: \'{}\' and userId: \'{}\'.'
                                            .format(userGame.game_id, userGame.user_id)), 500))
        
        return make_response(updatedGame.__dict__, 200)