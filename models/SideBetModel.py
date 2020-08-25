from utilities.Database import mongo
from bson.objectid import ObjectId
from utilities.DatetimeHelper import convert_to_utc
from models.MovieModel import MovieModel
from models.UserModel import UserModel
from enums.SideBetStatus import SideBetStatus
from pymongo.errors import WriteError
import json

class BetModel():
    def __init__(self, user_id, bet):
        self.user_id = user_id
        self.bet = bet

class SideBetModel():
    def __init__(self, id, game_id, movie_id, prize_in_millions, close_date, bets, winner, status):
        self._id = id
        self.game_id = game_id
        self.movie_id = movie_id
        self.prize_in_millions = prize_in_millions
        self.close_date = close_date
        self.bets = bets
        self.winner = winner
        self.status = status

    def serialize(self):
        bets = [{'userHandle': getattr(UserModel.load_user_by_id(bet.user_id), 'userHandle', None) or '', 'bet': bet.bet} for bet in self.bets]
        winner = getattr(UserModel.load_user_by_id(self.winner), 'userHandle', None)
        movie_title = getattr(MovieModel.load_movie_by_id(self.movie_id), 'title', None)

        return {
            'id': self._id,
            'gameId': self.game_id,
            'movieId': self.movie_id,
            'movieTitle': movie_title or '',
            'prizeInMillions': self.prize_in_millions,
            'closeDate': self.close_date,
            'bets': bets,
            'winner': winner,
            'status': SideBetStatus(self.status).name
        }

    def update_side_bet(self):
        betModels = [BetModel(user_id=bet.user_id, bet=bet.bet) for bet in self.bets]
        jsonBets = json.dumps([bet.__dict__ for bet in betModels])
        winner = ObjectId(self.winner) if ObjectId.is_valid(self.winner) else None

        result = mongo.db.sidebets.update_one({'_id': ObjectId(self._id)},
                                              {'$set':
                                                   dict(game_id=ObjectId(self.game_id),
                                                        movie_id=ObjectId(self.movie_id),
                                                        prize_in_millions=self.prize_in_millions,
                                                        close_date=convert_to_utc(self.close_date),
                                                        bets=json.loads(jsonBets),
                                                        winner=winner,
                                                        status=self.status)})

        if result.modified_count == 1:
            return self.load_side_bet_by_id(self._id)

        return None

    @classmethod
    def create_side_bet(cls, game_id, movie_id, prize_in_millions, close_date):
        side_bet_model = SideBetModel(id=ObjectId(),
                                      game_id=ObjectId(game_id),
                                      movie_id=ObjectId(movie_id),
                                      prize_in_millions=prize_in_millions,
                                      close_date=convert_to_utc(close_date),
                                      bets=[],
                                      winner=None,
                                      status=SideBetStatus.current.value)

        result = mongo.db.sidebets.insert_one(side_bet_model.__dict__)

        if result.acknowledged:
            inserted_side_bet = cls.load_side_bet_by_id(str(result.inserted_id))
            return inserted_side_bet

        return None

    @classmethod
    def change_side_bet_status(cls, gameId, old_status, new_status):
        side_bets = cls.load_side_bet_by_game_id_and_status(gameId, old_status)

        for side_bet in side_bets:
            side_bet.status = new_status
            updated_side_bet = side_bet.update_side_bet()

            if not updated_side_bet:
                raise WriteError('Unable to update side bet status.')

    @classmethod
    def load_side_bet_by_id(cls, id):
        if not ObjectId.is_valid(id):
            return None
        queryDict = {'_id': ObjectId(id)}
        side_bets = cls.load_side_bets(queryDict)
        return side_bets[0]

    @classmethod
    def load_side_bet_by_game_id(cls, game_id):
        if not ObjectId.is_valid(game_id):
            return None
        queryDict = {'game_id': ObjectId(game_id), 'status': SideBetStatus.current.value}
        side_bets = cls.load_side_bets(queryDict)
        return side_bets[0]

    @classmethod
    def load_side_bet_by_game_id_and_status(cls, game_id, status):
        if not ObjectId.is_valid(game_id):
            return None
        queryDict = {'game_id': ObjectId(game_id), 'status': status}
        side_bets = cls.load_side_bets(queryDict)
        return side_bets

    @classmethod
    def load_side_bets(cls, queryDict):
        db_side_bets = mongo.db.sidebets.find(queryDict)
        side_bets = []
        for side_bet in db_side_bets:
            bets = [BetModel(user_id=bet['user_id'], bet=bet['bet']) for bet in side_bet['bets']]

            side_bet_model = SideBetModel(id=str(side_bet['_id']),
                                          game_id=str(side_bet['game_id']),
                                          movie_id=str(side_bet['movie_id']),
                                          prize_in_millions=side_bet['prize_in_millions'],
                                          close_date=side_bet['close_date'],
                                          bets=bets,
                                          winner=str(side_bet['winner']),
                                          status=side_bet['status'])
            side_bets.append(side_bet_model)

        return side_bets