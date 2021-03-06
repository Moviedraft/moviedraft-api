# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 20:16:39 2019

@author: Jason
"""

from flask import request, abort, make_response, jsonify, render_template
from flask import current_app as app
from flask_restplus import Namespace, Resource, fields, reqparse
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
from email.utils import parseaddr
from utilities.Mailer import Emailer
from utilities.Executor import executor
from utilities.DatetimeHelper import convert_to_utc, get_current_time, string_format_date, get_most_recent_day
from models.GameModel import GameModel
from models.RuleModel import RuleModel
from models.MovieModel import MovieModel
from models.BidModel import BidModel
from models.UserModel import UserModel
from models.UserGameModel import UserGameModel
from models.PlayerModel import PlayerModel
from models.WeekendBoxOfficeModel import WeekendBoxOfficeModel
from models.PollModel import PollModel
from models.SideBetModel import SideBetModel
from models.SideBetModel import BetModel
from models.FlavorTextModel import FlavorTextModel
from enums.SideBetStatus import SideBetStatus
from enums.DaysOfWeek import DaysOfWeek
from namespaces.Movies import movies_namespace
from namespaces.Rules import rules_namespace
from pymongo.errors import WriteError
import arrow

games_namespace = Namespace('games', description='Draft league game data.')

gamePayload = games_namespace.model('GamePayload', {
        'gameName': fields.String,
        'startDate': fields.DateTime(dt_format=u'%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'endDate': fields.DateTime(dt_format=u'%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'auctionDate': fields.DateTime(dt_format=u'%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'dollarSpendingCap': fields.Integer,
        'minimumBid': fields.Integer,
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

FlavorTextPostPayload = games_namespace.model('FlavorTextPostPayload', {
        'type': fields.String,
        'text': fields.String
        })

FlavorTextPatchPayload = games_namespace.model('FlavorTextPatchPayload', {
        'text': fields.String
        })

SideBetPostPayload = games_namespace.model('SideBetPostPayload', {
        'movieId': fields.String,
        'prizeInMillions': fields.Integer,
        'closeDate': fields.DateTime(dt_format=u'%Y-%m-%dT%H:%M:%S.%f+00:00')
        })

SideBetPatchPayload = games_namespace.model('SideBetPatchPayload', {
        'bet': fields.Integer
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
        'dollarSpendingCap': fields.Integer,
        'minimumBid': fields.Integer,
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
        'value': fields.Integer,
        'bonusInMillions': fields.Integer
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
        'choices': fields.List(fields.Nested(games_namespace.models['PollChoice'])),
        'voters': fields.List(fields.String)
        })

games_namespace.model('Bet', {
    'userHandle': fields.String,
    'bet': fields.Integer
})

games_namespace.model('SideBet', { 'id': fields.String,
                                   'gameId': fields.String,
                                   'movieId': fields.String,
                                   'movieTitle': fields.String,
                                   'prizeInMillions': fields.Integer,
                                   'closeDate': fields.DateTime(dt_format=u'%Y-%m-%dT%H:%M:%S.%f+00:00'),
                                   'bets': fields.List(fields.Nested(games_namespace.models['Bet'])),
                                   'weekendGross': fields.Integer,
                                   'winner': fields.String,
                                   'status': fields.String
                                   })

games_namespace.model('FlavorText', {
        'id': fields.String,
        'gameId': fields.String,
        'type': fields.String,
        'text': fields.String
        })

games_namespace.model('CurrentTime', {
        'time': fields.String
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
        parser.add_argument('dollarSpendingCap', type=int, required=True)
        parser.add_argument('minimumBid', type=int, required=True)
        parser.add_argument('playerIds', type=list, location='json', required=True)
        parser.add_argument('movies', type=list, location='json', required=True)
        parser.add_argument('auctionItemsExpireInSeconds', type=int, required=True)
        parser.add_argument('rules', type=list, location='json', required=True)
        args = parser.parse_args()
        
        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity['id'])

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
                dollarSpendingCap=args['dollarSpendingCap'],
                minimumBid=args['minimumBid'],
                movies=args['movies'],
                auctionItemsExpireInSeconds=args['auctionItemsExpireInSeconds'],
                rules=rulesArray,
                commissionerId=current_user.id,
                playerIds=playerIds,
                auctionComplete=False
                )

        createdGame = game.create_game()
        
        commissioneruUserGame = UserGameModel.create_userGameModel(current_user.id, gameId, current_user.id, game.gameName, game.auctionDate, True)
        if not commissioneruUserGame:
            abort(make_response(jsonify(message='Unable to associate commissionerId \'{}\' with game: \'{}\'.'
                                                .format(current_user.id, game.gameName)), 500))
        
        for playerId in playerIds:
            userGame = UserGameModel.create_userGameModel(current_user.id, gameId, playerId, args['gameName'], game.auctionDate)
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
            
        return make_response(jsonify(id=str(createdGame._id)), 200)
    
@games_namespace.route('/<string:gameId>')
class Game(Resource):
    @jwt_required
    @games_namespace.response(200, 'Success', games_namespace.models['Game'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(403, 'Forbidden')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def get(self, gameId):
        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity['id'])

        game = GameModel.load_game_by_id(gameId)
        
        if not game:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))

        if current_user.id not in game.playerIds and current_user.id != game.commissionerId:
            abort(make_response(jsonify(message='You are not authorized to access this resource.'), 403))

        movies = []
        for movieId in game.movies:
            movieModel = MovieModel.load_movie_by_id(movieId)
            if arrow.get(game.startDate).date() \
                    <= arrow.get(movieModel.releaseDate).date()  \
                    <= arrow.get(game.endDate).date():
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
    @games_namespace.response(200, 'Success')
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(403, 'Forbidden')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def delete(self, gameId):
        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity['id'])

        game = GameModel.load_game_by_id(gameId)

        if not game:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))

        if current_user.id != game.commissionerId:
            abort(make_response(jsonify(message='You are not authorized to access this resource. '
                                                'Game admin privilege required.'), 403))

        UserGameModel.delete_user_games_by_game_id(game._id)
        BidModel.delete_bids_by_game_id(game._id)
        deleted = GameModel.delete_game_by_id(game._id)

        if deleted:
            return make_response(jsonify(message='Successfully deleted GameId: \'{}\'.'.format(gameId)), 200)

        abort(make_response(jsonify('Game ID: \'{}\' could not be deleted'.format(gameId)), 500))
                

    
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
        parser.add_argument('dollarSpendingCap', type=int, required=True)
        parser.add_argument('minimumBid', type=int, required=True)
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
            UserGameModel.create_userGameModel(current_user.id, gameId, playerId, existingGame.gameName, existingGame.auctionDate)
            
        args['playerIds'] = playerIds
        
        movieIds = []
        for id in args['movies'] or []:
            movie = MovieModel.load_movie_by_id(id)
            if movie:
                movieIds.append(str(movie.id))
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
        for rule in args['rules'] or []:
            existingRule = RuleModel.load_rule(rule)
            if existingRule:
                ruleArray.append(rule)
        args['rules'] = ruleArray
        
        updatedGame = existingGame.update_game()
        
        movieBids = BidModel.load_bids_by_gameId(gameId)
        for movieBid in movieBids:
            movieBid.auctionExpiry = convert_to_utc(args['auctionDate'])
            movieBid.dollarSpendingCap = args['dollarSpendingCap']
            movieBid.update_bid()
        
        userGames = UserGameModel.load_user_game_by_game_id(updatedGame._id)
        for userGame in [userGame for userGame in userGames
                         if userGame.gameName != updatedGame.gameName
                         or arrow.get(userGame.auctionDate) != arrow.get(updatedGame.auctionDate)]:
            userGame.gameName = updatedGame.gameName
            userGame.auctionDate = convert_to_utc(updatedGame.auctionDate)
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
        
        commissioner = PlayerModel.loadPlayer(game._id, game.commissionerId, gameBids, game.rules)
        players.append(commissioner)

        for id in game.playerIds:
            player = PlayerModel.loadPlayer(game._id, id, gameBids, game.rules)
            if player:
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

        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity['id'])

        game = GameModel.load_game_by_id(gameId)
        
        if not game:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))
        
        if current_user.id not in game.playerIds and current_user.id != game.commissionerId:
            abort(make_response(jsonify(message='You are not authorized to access this resource.'), 403))

        poll = PollModel.load_poll_by_gameId(gameId)
        updatedPoll = None
        
        if not poll:
            abort(make_response(jsonify(message='Poll could not be found for game ID: \'{}\'.'.format(gameId)), 404))

        if ObjectId(current_user.id) in poll.voters:
            abort(make_response(jsonify(message='user ID: \'{}\' has already voted in poll.'.format(current_user.id)), 400))

        if args['vote']:
            choiceToUpdate = next((x for x in poll.choices if x.displayText == args['vote']), None)
        
            if not choiceToUpdate:
                abort(make_response(jsonify(message='Poll choice: \'{}\' is not valid.'.format(args['vote'])), 400))
            
            updatedPoll = poll.update_vote(choiceToUpdate.displayText, choiceToUpdate.votes + 1, current_user.id)
        
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

@games_namespace.route('/<string:game_id>/sidebet')
class SideBet(Resource):
    @jwt_required
    @games_namespace.response(200, 'Success', games_namespace.models['SideBet'])
    @games_namespace.response(400, 'Bad Request')
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(403, 'Forbidden')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    @games_namespace.doc(params={'status': 'current, previous'})
    def get(self, game_id):
        status = request.args.get('status')

        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity['id'])

        game = GameModel.load_game_by_id(game_id)

        if not game:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(game_id)), 404))

        if current_user.id not in game.playerIds and current_user.id != game.commissionerId:
            abort(make_response(jsonify(message='You are not authorized to access this resource.'), 403))

        if not SideBetStatus.has_value(status):
            abort(make_response(jsonify(message='\'{}\' is not a valid query parameter value for \'status\''
                                        .format(status)), 400))

        side_bet = next(iter(SideBetModel.load_side_bet_by_game_id_and_status(game_id, SideBetStatus[status].value)), None)

        if not side_bet:
            abort(make_response(jsonify(message='\'{}\' side bet could not be found for game ID: \'{}\'.'
                                        .format(status, game_id)), 404))

        if side_bet.status == SideBetStatus.current.value and not any(bet.user_id == current_user.id for bet in side_bet.bets):
            side_bet.bets = []

        return make_response(jsonify(sideBet=side_bet.serialize()), 200)

    @jwt_required
    @games_namespace.expect(SideBetPostPayload)
    @games_namespace.response(200, 'Success', games_namespace.models['SideBet'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(403, 'Forbidden')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def post(self, game_id):
        parser = reqparse.RequestParser()
        parser.add_argument('movieId', required=True)
        parser.add_argument('prizeInMillions', type=int, required=True)
        parser.add_argument('closeDate', type=lambda x: arrow.get(x), required=True)
        args = parser.parse_args()

        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity['id'])

        game = GameModel.load_game_by_id(game_id)

        if not game:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(game_id)), 404))

        if current_user.id != game.commissionerId:
            abort(make_response(jsonify(message='You are not authorized to access this resource.'), 403))

        try:
            current_side_bet = SideBetModel.load_side_bet_by_game_id_and_status(game._id, SideBetStatus.current.value)[0]
        except IndexError:
            current_side_bet = None

        if current_side_bet:
            if arrow.utcnow() <= arrow.get(current_side_bet.close_date):
                current_side_bet.movie_id = ObjectId(args['movieId'])
                current_side_bet.prize_in_millions = args['prizeInMillions']
                current_side_bet.close_date = convert_to_utc(args['closeDate'])
                side_bet = current_side_bet.update_side_bet()
            else:
                try:
                    SideBetModel.change_side_bet_status(game_id, SideBetStatus.previous.value, SideBetStatus.old.value)
                    SideBetModel.change_side_bet_status(game_id, SideBetStatus.current.value, SideBetStatus.previous.value)
                    side_bet = SideBetModel.create_side_bet(game_id, args['movieId'], args['prizeInMillions'], args['closeDate'])
                except WriteError:
                    abort(make_response(
                        jsonify(
                            message='Previous side bet statuses for gameId: \'{}\' could not be changed'.format(game_id)),
                        500))
        else:
            side_bet = SideBetModel.create_side_bet(game_id, args['movieId'], args['prizeInMillions'], args['closeDate'])

        if not side_bet:
            abort(make_response(jsonify(message='Side bet could not be created.'), 500))

        return make_response(jsonify(sideBet=side_bet.serialize()), 200)

    @jwt_required
    @games_namespace.expect(SideBetPatchPayload)
    @games_namespace.response(200, 'Success', games_namespace.models['SideBet'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(403, 'Forbidden')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def patch(self, game_id):
        parser = reqparse.RequestParser()
        parser.add_argument('bet', type=int, required=True)
        args = parser.parse_args()

        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity['id'])

        game = GameModel.load_game_by_id(game_id)

        if not game:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(game_id)), 404))

        if current_user.id not in game.playerIds and current_user.id != game.commissionerId:
            abort(make_response(jsonify(message='You are not authorized to access this resource.'), 403))

        side_bet = next(iter(SideBetModel.load_side_bet_by_game_id_and_status(game_id, SideBetStatus.current.value)), None)

        if not side_bet:
            abort(make_response(jsonify(message='Side bet for gameID: \'{}\' could not be found.'.format(game_id)), 404))

        if any(bet.user_id == current_user.id for bet in side_bet.bets):
            abort(make_response(jsonify(message='User: \'{}\' has already placed a bid for this side bet.'.format(current_user.userHandle)), 403))

        if arrow.utcnow() > arrow.get(side_bet.close_date):
            abort(make_response(jsonify(
                message='The close date for this side bet has passed. Close date was: \'{}\''.format(string_format_date(side_bet.close_date))), 403))

        side_bet.bets.append(BetModel(current_user.id, args['bet']))
        updated_side_bet = side_bet.update_side_bet()

        if not updated_side_bet:
            abort(make_response(jsonify(message='Side bet could not be updated.'), 500))

        return make_response(jsonify(sideBet=updated_side_bet.serialize()), 200)

@games_namespace.route('/<string:gameId>/flavortext/<string:type>')
class FlavorText(Resource):
    @jwt_required
    @games_namespace.response(200, 'Success', games_namespace.models['FlavorText'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(403, 'Forbidden')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def get(self, gameId, type):
        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity['id'])

        game = GameModel.load_game_by_id(gameId)

        if not game:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))

        if current_user.id not in game.playerIds and current_user.id != game.commissionerId:
            abort(make_response(jsonify(message='You are not authorized to access this resource.'), 403))

        flavor_text = FlavorTextModel.load_flavor_text_by_game_id_and_type(gameId, type)

        if not flavor_text:
            abort(make_response(jsonify(message='Flavor text could not be found for game ID: \'{}\' type: \'{}\'.'
                                        .format(gameId, type)), 404))

        return make_response(jsonify(flavorText=flavor_text.serialize()), 200)

    @jwt_required
    @games_namespace.expect(FlavorTextPatchPayload)
    @games_namespace.response(200, 'Success', games_namespace.models['FlavorText'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(403, 'Forbidden')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def patch(self, gameId, type):
        parser = reqparse.RequestParser()
        parser.add_argument('text', required=True)
        args = parser.parse_args()

        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity['id'])

        game = GameModel.load_game_by_id(gameId)

        if not game:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))

        if current_user.id != game.commissionerId:
            abort(make_response(jsonify(message='You are not authorized to access this resource.'), 403))

        flavor_text = FlavorTextModel.load_flavor_text_by_game_id_and_type(gameId, type)

        if not flavor_text:
            abort(make_response(jsonify(message='Flavor text could not be created.'), 500))

        flavor_text.text = args['text']
        updated_flavor_text = flavor_text.update_flavor_text()

        if not updated_flavor_text:
            abort(make_response(jsonify(message='Unable to update flavor text.'), 500))

        return make_response(jsonify(flavorText=flavor_text.__dict__), 200)

@games_namespace.route('/<string:gameId>/flavortext')
class PostFlavorText(Resource):
    @jwt_required
    @games_namespace.expect(FlavorTextPostPayload)
    @games_namespace.response(200, 'Success', games_namespace.models['FlavorText'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(403, 'Forbidden')
    @games_namespace.response(404, 'Not Found')
    @games_namespace.response(500, 'Internal Server Error')
    def post(self, gameId):
        parser = reqparse.RequestParser()
        parser.add_argument('type', required=True)
        parser.add_argument('text', required=True)
        args = parser.parse_args()

        userIdentity = get_jwt_identity()
        current_user = UserModel.load_user_by_id(userIdentity['id'])

        game = GameModel.load_game_by_id(gameId)

        if not game:
            abort(make_response(jsonify(message='Game ID: \'{}\' could not be found.'.format(gameId)), 404))

        if current_user.id != game.commissionerId:
            abort(make_response(jsonify(message='You are not authorized to access this resource.'), 403))

        flavor_text = FlavorTextModel.create_flavor_text(gameId, args['type'], args['text'])

        if not flavor_text:
            abort(make_response(jsonify(message='Flavor text could not be created.'), 500))

        return make_response(jsonify(flavorText=flavor_text.__dict__), 200)

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

@games_namespace.route('/time')
class CurrentTime(Resource):
    @jwt_required
    @games_namespace.response(200, 'Success', games_namespace.models['CurrentTime'])
    @games_namespace.response(401, 'Authentication Error')
    @games_namespace.response(500, 'Internal Server Error')
    def get(self):
        current_time = get_current_time()

        return make_response((jsonify(time=current_time)), 200)