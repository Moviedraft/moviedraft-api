from utilities.Database import mongo
from bson.objectid import ObjectId
from utilities.DatetimeHelper import convert_to_utc
from models.MovieModel import MovieModel
import json

class BetModel():
    def __init__(self, user_id, bet):
        self.user_id = user_id
        self.bet = bet

class SideBetModel():
    def __init__(self, id, game_id, movie_id, prize_in_millions, close_date, bets, winner, current):
        self._id = id
        self.game_id = game_id
        self.movie_id = movie_id
        self.prize_in_millions = prize_in_millions
        self.close_date = close_date
        self.bets = bets
        self.winner = winner
        self.current = current

    def serialize(self):
        bets = [{'userId': bet.user_id, 'bet': bet.bet} for bet in self.bets]
        movie_title = getattr(MovieModel.load_movie_by_id(self.movie_id), 'title', None)

        return {
            'id': self._id,
            'gameId': self.game_id,
            'movieId': self.movie_id,
            'movieTitle': movie_title or '',
            'prizeInMillions': self.prize_in_millions,
            'closeDate': self.close_date,
            'bets': bets,
            'winner': self.winner
        }

    def update_side_bet(self):
        betModels = [BetModel(user_id=bet.user_id, bet=bet.bet) for bet in self.bets]
        jsonBets = json.dumps([bet.__dict__ for bet in betModels])

        result = mongo.db.sidebets.update_one({'_id': ObjectId(self._id)},
                                              {'$set':
                                                   dict(game_id=ObjectId(self.game_id),
                                                        movie_id=ObjectId(self.movie_id),
                                                        prize_in_millions=self.prize_in_millions,
                                                        close_date=convert_to_utc(self.close_date),
                                                        bets=json.loads(jsonBets),
                                                        winner=self.winner,
                                                        current=self.current)})

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
                                      winner='',
                                      current=True)

        result = mongo.db.sidebets.insert_one(side_bet_model.__dict__)

        if result.acknowledged:
            inserted_side_bet = cls.load_side_bet_by_id(str(result.inserted_id))
            return inserted_side_bet

        return None

    @classmethod
    def disable_previous_side_bet(cls, gameId):
        current_side_bet = cls.load_side_bet_by_game_id(gameId)

        if not current_side_bet:
            return None

        current_side_bet.current = False

        updated_side_bet = current_side_bet.update_side_bet()

        if not updated_side_bet:
            return None

        return updated_side_bet

    @classmethod
    def load_side_bet_by_id(cls, id):
        if not ObjectId.is_valid(id):
            return None
        queryDict = {'_id': ObjectId(id)}
        side_bet = cls.load_side_bet(queryDict)
        return side_bet

    @classmethod
    def load_side_bet_by_game_id(cls, game_id):
        if not ObjectId.is_valid(game_id):
            return None
        queryDict = {'game_id': ObjectId(game_id), 'current': True}
        side_bet = cls.load_side_bet(queryDict)
        return side_bet

    @classmethod
    def load_side_bet(cls, queryDict):
        side_bet = mongo.db.sidebets.find_one(queryDict)
        if not side_bet:
            return None

        bets = [BetModel(user_id=bet['user_id'], bet=bet['bet']) for bet in side_bet['bets']]

        return SideBetModel(id=str(side_bet['_id']),
                            game_id=str(side_bet['game_id']),
                            movie_id=str(side_bet['movie_id']),
                            prize_in_millions=side_bet['prize_in_millions'],
                            close_date=side_bet['close_date'],
                            bets=bets,
                            winner=side_bet['winner'],
                            current=side_bet['current'])

