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
from models.BidModel import BidModel
from models.UserModel import UserModel
from models.UserGameModel import UserGameModel
from models.PlayerModel import PlayerModel
from models.WeekendBoxOfficeModel import WeekendBoxOfficeModel
from models.PollModel import PollModel
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

PollPatchPayload = games_namespace.model('PollPatchPayload', {
        'vote': fields.String
        })

PollPostPayload = games_namespace.model('PollPostPayload', {
        'question': fields.String,
        'choices': fields.List(fields.String)
        })

games_namespace.model('GamePostResponse', {
        'id': fields.String
        })

gamePatch = games_namespace.model('gamePatch',{
        'auctionComplete': fields.Boolean
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
        'playerIds': fields.List(fields.String),
        'auctionComplete': fields.Boolean
        })

games_namespace.model('Player', {
        'id': fields.String,
        'userHandle': fields.String,
        'totalSpent': fields.Integer,
        'totalGross': fields.Integer,
        'moviesPurchasedTitles': fields.List(fields.String),
        'value': fields.Integer
        })


games_namespace.model('Players', {
        'players': fields.List(fields.Nested(games_namespace.models['Player']))
        })

games_namespace.model('WeekendBoxOfficeMovie', {
        'id': fields.String,
        'title': fields.String,
        'weekendGross': fields.Integer,
        'totalGross': fields.Integer,
        'owner': fields.String,
        'purchasePrice': fields.Integer,
        'openingWeekend': fields.Boolean
        })

games_namespace.model('WeekendBoxOffice', {
        'weekendBoxOffice': fields.List(fields.Nested(games_namespace.models['WeekendBoxOfficeMovie']))
        })

games_namespace.model('PollChoice', {
        'displayText': fields.String,
        'votes': fields.Integer
        })

games_namespace.model('Poll', {
        'id': fields.String,
        'gameId': fields.String,
        'question': fields.String,
        'choices': fields.List(fields.Nested(games_namespace.models['PollChoice']))
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
            BidModel.create_empty_bid(gameId, movieId, UtcAuctionDate, args['dollarSpendingCap'])
            
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
                playerIds=playerIds,
                auctionComplete=False
                )

        result = mongo.db.games.insert_one(game.__dict__)
        
        commissioneruUserGame = UserGameModel.create_userGameModel(current_user.id, gameId, current_user.id, game.gameName, True)
        if not commissioneruUserGame:
            abort(make_response(jsonify(message='Unable to associate commissionerId \'{}\' with game: \'{}\'.'
                                                .format(current_user.id, game.gameName)), 500))
        
        for playerId in playerIds:
            userGame = UserGameModel.create_userGameModel(current_user.id, gameId, playerId, args['gameName'])
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
        
        if not game:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))

        movies = []
        for movieId in game.movies:
            movieModel = MovieModel.load_movie_by_id(movieId)
            movies.append(movieModel.__dict__)          
            game.movies = movies

        playerIds = []
        for id in game.playerIds:
            player = UserModel.load_user_by_id(id)
            if player:
                playerIds.append(player.email)
        
        game.playerIds = playerIds
            
        return make_response(jsonify(game.__dict__), 200)

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
            BidModel.delete_bids_by_game_id(game._id)
            try:
                mongo.db.games.delete_one({'gameName': game.gameName})
                return make_response('', 200)
            except:
                abort(make_response(jsonify('Game ID: \'{}\' could not be deleted'.format(gameId)), 500))
                
        abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))
    
    @jwt_required
    @games_namespace.expect(gamePatch)
    @games_namespace.response(200, 'Success', games_namespace.models['Game'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def patch(self, gameId):
        parser = reqparse.RequestParser()
        parser.add_argument('auctionComplete', type=bool, required=False)
        args = parser.parse_args()
        
        existingGame = GameModel.load_game_by_id(gameId)
        
        if not existingGame:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))
        
        for key, value in args.items():
            setattr(existingGame, key, value)
            
        updatedGame = existingGame.update_game()
        
        return make_response(updatedGame.__dict__, 200)

        
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
        parser.add_argument('auctionComplete', type=bool, required=True)
        args = parser.parse_args()
        
        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity['id'])
        
        existingGame = GameModel.load_game_by_id(gameId)
        
        if not existingGame:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))
            
        if existingGame.commissionerId != current_user.id:
            abort(make_response(jsonify(message='You are not authorized to access this resource.'), 403))
        
        if arrow.utcnow() > arrow.get(existingGame.auctionDate):
            abort(make_response(jsonify(message='Game ID: \'{}\' cannot be edited after the auction date: \'{}\''
                                        .format(existingGame._id, existingGame.auctionDate)), 403))
        
        oldgameNameLowerCase = existingGame.gameNameLowerCase
        
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
            player = UserModel.load_user_by_email(value) or UserModel.load_user_by_id(value)
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
            UserGameModel.create_userGameModel(current_user.id, gameId, playerId, existingGame.gameName)
            
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
            BidModel.delete_bids_by_game_id_and_movie_id(gameId, movieId)
        
        moviesToAdd = set(movieIds).difference(set(existingGame.movies))
        for movieId in moviesToAdd:
            BidModel.create_empty_bid(gameId, movieId, existingGame.auctionDate, args['dollarSpendingCap'])

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
        
        movieBids = BidModel.load_bids_by_gameId(gameId)
        for movieBid in movieBids:
            movieBid.auctionExpiry = convert_to_utc(args['auctionDate'])
            movieBid.dollarSpendingCap = args['dollarSpendingCap']
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

@games_namespace.route('/<string:gameId>/players')
class GamePlayerRankings(Resource):
    @jwt_required
    @games_namespace.response(200, 'Success', games_namespace.models['Players'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def get(self, gameId):
        game = GameModel.load_game_by_id(gameId)
        
        if not game:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))
        
        gameBids = BidModel.load_bids_by_gameId(gameId)
        
        if not gameBids:
            abort(make_response(jsonify(message='Bids for Game ID: \'{}\' could not be found.'.format(gameId)), 404))
            
        players = []
        
        commissioner = PlayerModel.loadPlayer(game.commissionerId, gameBids)
        players.append(commissioner)
        
        for id in game.playerIds:
            player = PlayerModel.loadPlayer(id, gameBids)
            playerJoined = UserGameModel.load_user_game_by_game_id_and_user_id(game._id, player.id).joined
            if playerJoined:
                players.append(player)
            
        return make_response(jsonify(players=[player.serialize() for player in players]), 200)

@games_namespace.route('/<string:gameId>/weekend')
class WeekendBoxOffice(Resource):
    @jwt_required
    @games_namespace.response(200, 'Success', games_namespace.models['WeekendBoxOffice'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def get(self, gameId):
        game = GameModel.load_game_by_id(gameId)
        
        if not game:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))
        
        weekendBoxOffice = WeekendBoxOfficeModel.load_weekend_box_office(gameId)
        
        return make_response(jsonify(weekendBoxOffice=[movie.serialize() for movie in weekendBoxOffice]), 200)

@games_namespace.route('/<string:gameId>/poll')
class Poll(Resource):
    @jwt_required
    @games_namespace.response(200, 'Success', games_namespace.models['Poll'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def get(self, gameId):
        game = GameModel.load_game_by_id(gameId)
        
        if not game:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))
        
        poll = PollModel.load_poll_by_gameId(gameId)
        
        if not poll:
            abort(make_response(jsonify(message='Poll could not be found for game ID: \'{}\'.'.format(gameId)), 404))
        
        return make_response(jsonify(poll.serialize()), 200)
    
    @jwt_required
    @games_namespace.expect(PollPatchPayload)
    @games_namespace.response(200, 'Success', games_namespace.models['Poll'])
    @games_namespace.response(400, 'Bad Request')
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def patch(self, gameId):
        parser = reqparse.RequestParser()
        parser.add_argument('vote', required=True)
        args = parser.parse_args()
        
        game = GameModel.load_game_by_id(gameId)
        
        if not game:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))
        
        poll = PollModel.load_poll_by_gameId(gameId)
        updatedPoll = None
        
        if not poll:
            abort(make_response(jsonify(message='Poll could not be found for game ID: \'{}\'.'.format(gameId)), 404))
        
        if args['vote']:
            choiceToUpdate = next((x for x in poll.choices if x.displayText == args['vote']), None)
        
            if not choiceToUpdate:
                abort(make_response(jsonify(message='Poll choice: \'{}\' is not valid.'.format(args['vote'])), 400))
            
            updatedPoll = poll.update_vote(choiceToUpdate.displayText, choiceToUpdate.votes + 1)
        
        responsePoll = updatedPoll or poll
        
        return make_response(jsonify(responsePoll.serialize()), 200)
    
    @jwt_required
    @games_namespace.expect(PollPostPayload)
    @games_namespace.response(200, 'Success', games_namespace.models['Poll'])
    @games_namespace.response(400, 'Bad Request')
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(403, 'Forbidden')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def post(self, gameId):
        parser = reqparse.RequestParser()
        parser.add_argument('question', required=True)
        parser.add_argument('choices', type=list, location='json', required=True)
        args = parser.parse_args()
        
        game = GameModel.load_game_by_id(gameId)
        
        if not game:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))
        
        userIdentity = get_jwt_identity()
        currentUser = UserModel.load_user_by_id(userIdentity['id'])
        
        if currentUser.id != game.commissionerId:
            abort(make_response(jsonify(message='User ID: \'{}\' is not authorized to access this resource.'
                                        .format(currentUser.id)), 403))
            
        PollModel.disable_previous_poll(gameId)

        newPoll = PollModel.create_poll(gameId, args['question'], args['choices'])
        
        if not newPoll:
            abort(make_response(jsonify(message='Unable to create poll.'.format(gameId)), 500))

        return make_response(jsonify(newPoll.serialize()), 200)
    
@games_namespace.route('/<string:gameId>/join')
class JoinGame(Resource):
    @jwt_required
    @games_namespace.response(200, 'Success')
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(403, 'Forbidden')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def post(self, gameId):
        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity['id'])
        
        game = GameModel.load_game_by_id(gameId)
        userGame = UserGameModel.load_user_game_by_game_id_and_user_id(gameId, current_user.id)
        
        if not game:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))
        
        if not userGame:
            abort(make_response(jsonify(message='User-Game association could not be found ' + 
                                        'for game ID: \'{}\' and user ID \'{}\'.'
                                        .format(gameId, current_user.id)), 404))
        
        if current_user.id not in game.playerIds:
            abort(make_response(jsonify(message='User ID: \'{}\' has not been added to game ID: \'{}\'.'
                                        .format(current_user.id, gameId)), 403))

        userGame.joined = True
        if not userGame.update_userGameModel():
            abort(make_response(jsonify(message='User-Game association could not be created ' + 
                                        'for game ID: \'{}\' and user ID \'{}\'.'
                                        .format(gameId, current_user.id)), 500))
        
        return make_response(jsonify(message='Successfully joined game: \'{}\''.format(game.gameName)), 200)