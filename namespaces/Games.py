# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 20:16:39 2019

@author: Jason
"""

from flask import abort, make_response, jsonify, render_template
from flask import current_app as app
from flask_restplus import Namespace, Resource, fields, reqparse
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
from email.utils import parseaddr
from utilities.Database import mongo
from utilities.Mailer import Emailer
from utilities.Executor import executor
from utilities.DatetimeHelper import convert_to_utc
from models.GameModel import GameModel
from models.RuleModel import RuleModel
from models.MovieModel import MovieModel
from models.MovieBidModel import MovieBidModel
from models.UserModel import UserModel
from models.UserGameModel import UserGameModel
from namespaces.Movies import movies_namespace
from namespaces.Rules import rules_namespace
from decorators.RoleAccessDecorator import requires_admin
import arrow

games_namespace = Namespace('games', description='Draft league game data.')

gamePayload = games_namespace.model('GamePayload', {
        'gameName': fields.String,
        'startDate': fields.DateTime(dt_format=u'%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'endDate': fields.DateTime(dt_format=u'%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'auctionDate': fields.DateTime(dt_format=u'%Y-%m-%dT%H:%M:%S.%f+00:00'),
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
        'startDate': fields.DateTime(dt_format=u'%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'endDate': fields.DateTime(dt_format=u'%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'auctionDate': fields.DateTime(dt_format=u'%Y-%m-%dT%H:%M:%S.%f+00:00'),
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
    @games_namespace.expect(gamePayload)
    @games_namespace.response(200, 'Success', games_namespace.models['GamePostResponse'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(400, 'Bad Request')
    @games_namespace.response(409, 'Conflict')
    @games_namespace.response(500, 'Internal Server Error')
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('gameName', required=True)
        parser.add_argument('startDate', type=lambda x: arrow.get(x), required=True)
        parser.add_argument('endDate', type=lambda x: arrow.get(x), required=True)
        parser.add_argument('auctionDate', type=lambda x: arrow.get(x), required=True)
        parser.add_argument('playerBuyIn', type=int, required=True)
        parser.add_argument('dollarSpendingCap', type=int, required=True)
        parser.add_argument('playerIds', type=list, location='json', required=True)
        parser.add_argument('movies', type=list, location='json', required=True)
        parser.add_argument('auctionItemsExpireInSeconds', type=int, required=True)
        parser.add_argument('rules', type=list, location='json', required=True)
        args = parser.parse_args()
        
        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity['id'])
        
        if not GameModel.load_game_by_name(args['gameName']) == None:
            abort(make_response(jsonify(message='Game name: \'{}\' already exists.'.format(args['gameName'])), 409))
        
        gameId = ObjectId()
        UtcStartDate = convert_to_utc(args['startDate'])
        UtcEndDate = convert_to_utc(args['endDate'])
        UtcAuctionDate = convert_to_utc(args['auctionDate'])
        
        rulesArray = []
        rulesJson = args['rules']
        for rule in rulesJson:
            ruleModel = RuleModel(ruleName=rule['ruleName'], rules=rule['rules'])
            rulesArray.append(ruleModel.__dict__)
        
        filteredPlayers = [value for value in args['playerIds'] if value != current_user.id 
                           and value.lower() != current_user.email.lower()
                           and '@' in parseaddr(value)[1]]

        playerIds = []
        recipientDict = {}
        for email in filteredPlayers:   
            player = UserModel.load_user_by_email(email)
            if player:
                playerIds.append(player.id)
                recipientName = player.firstName
                recipientDict[email] = recipientName
            else:
                playerIds.append(email.lower())
                recipientName = email.split('@')[0]
                recipientDict[email] = recipientName

        for movieId in args['movies']:
            if not MovieModel.load_movie_by_id(movieId):
                abort(make_response(jsonify(message='MovieId: \'{}\' could not be found.'.format(movieId)), 404))
            MovieBidModel.create_empty_bid(gameId, movieId, UtcAuctionDate)
            
        game = GameModel(
                id=gameId,
                gameName=args['gameName'],
                gameNameLowerCase=args['gameName'].lower(),
                startDate=UtcStartDate,
                endDate=UtcEndDate,
                auctionDate=UtcAuctionDate,
                playerBuyIn=args['playerBuyIn'],
                dollarSpendingCap=args['dollarSpendingCap'],
                movies=args['movies'],
                auctionItemsExpireInSeconds=args['auctionItemsExpireInSeconds'],
                rules=rulesArray,
                commissionerId=current_user.id,
                playerIds=playerIds
                )

        result = mongo.db.games.insert_one(game.__dict__)
        
        commissioneruUserGame = UserGameModel.create_userGameModel(gameId, current_user.id, game.gameName)
        if not commissioneruUserGame:
            abort(make_response(jsonify(message='Unable to associate commissionerId \'{}\' with game: \'{}\'.'
                                                .format(current_user.id, game.gameName)), 500))
        
        for playerId in playerIds:
            if ObjectId.is_valid(playerId):
                userGame = UserGameModel.create_userGameModel(gameId, player.id, args['gameName'])
                if not userGame:
                    abort(make_response(jsonify(message='Unable to associate userId \'{}\' with game: \'{}\'.'
                                                .format(playerId, game.gameName)), 500))
                    
        for email in filteredPlayers:
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
                movieModel = MovieModel.load_movie_by_id(movieId)
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
            MovieBidModel.delete_movie_bids_by_game_id(game._id)
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
        parser.add_argument('startDate', type=lambda x: arrow.get(x), required=True)
        parser.add_argument('endDate', type=lambda x: arrow.get(x), required=True)
        parser.add_argument('auctionDate', type=lambda x: arrow.get(x), required=True)
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
        oldgameNameLowerCase = existingGame.gameNameLowerCase
        
        if not existingGame:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))
            
        if existingGame.commissionerId != current_user.id:
            abort(make_response(jsonify(message='You are not authorized to access this resource.'), 403))
        
        if args['gameName'].lower() != oldgameNameLowerCase:
            gameWithRequestedNewName = GameModel.load_game_by_name(args['gameName'])
            if gameWithRequestedNewName:
                abort(make_response(jsonify(message='Game name: \'{}\' already exists.'
                                            .format(args['gameName'])), 409))
        
        args['startDate'] = convert_to_utc(args['startDate'])
        args['endDate'] = convert_to_utc(args['endDate'])
        args['auctionDate'] = convert_to_utc(args['auctionDate'])
        
        filteredPlayerIds = [value for value in args['playerIds'] if value != current_user.id 
                             and value.lower() != current_user.email.lower()]
        playerIds = []
        for value in filteredPlayerIds:
            sendMail = False
            player = UserModel.load_user_by_id(value)
            if player:
                playerIds.append(player.id)
                if player.id not in existingGame.playerIds:
                    recipientName = player.firstName
                    email = player.email
                    sendMail = True
            elif '@' in parseaddr(value)[1]:
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
                                                gameName=args['gameName']))
        
        playersToDelete = set(existingGame.playerIds).difference(set(playerIds))
        for playerId in playersToDelete:
            UserGameModel.delete_user_games_by_game_id_and_user_id(gameId, playerId)
        
        playersToAdd = set(playerIds).difference(set(existingGame.playerIds))
        for playerId in playersToAdd:
            UserGameModel.create_userGameModel(gameId, playerId, existingGame.gameName)
            
        args['playerIds'] = playerIds
        print(playerIds)
        
        movieIds = []
        for value in args['movies'] or []:
            movie = mongo.db.movies.find_one({'_id': ObjectId(value)}, {'_id':1})
            if movie:
                movieIds.append(str(movie['_id']))
        args['movies'] = movieIds
        
        moviesToDelete = set(existingGame.movies).difference(set(movieIds))
        for movieId in moviesToDelete:
            MovieBidModel.delete_movie_bids_by_game_id_and_movie_id(gameId, movieId)
        
        moviesToAdd = set(movieIds).difference(set(existingGame.movies))
        for movieId in moviesToAdd:
            MovieBidModel.create_empty_bid(gameId, movieId, existingGame.auctionDate)

        for key, value in args.items():
            setattr(existingGame, key, value)
            if key.lower() == 'gamename':
                setattr(existingGame, 'gameNameLowerCase', value.lower())
                
        ruleArray = []
        for value in args['rules'] or []:
            existingRule = mongo.db.rules.find_one({'ruleName': value['ruleName']}, {'_id':1})
            if existingRule:
                ruleArray.append(value)
        args['rules'] = ruleArray
        
        updatedGame = existingGame.update_game()
        
        movieBids = MovieBidModel.load_bids_by_gameId(gameId)
        for movieBid in movieBids:
            movieBid.auctionExpiry = updatedGame.auctionDate
            movieBid.update_bid()
        
        if oldgameNameLowerCase != updatedGame.gameNameLowerCase:
            userGames = UserGameModel.load_user_game_by_game_id(updatedGame._id)
            for userGame in userGames:
                userGame.gameName = updatedGame.gameName
                updatedUserGame = userGame.update_userGameModel()
                if not updatedUserGame:
                    abort(make_response(jsonify('Game could not be updated for gameId: \'{}\' and userId: \'{}\'.'
                                                .format(userGame.game_id, userGame.user_id)), 500))
        
        return make_response(updatedGame.__dict__, 200)