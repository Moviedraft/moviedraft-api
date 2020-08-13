from utilities.Database import mongo
from bson.objectid import ObjectId
from utilities.DatetimeHelper import convert_to_utc

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
        self.current=current

    def serialize(self):
        bets = [{'userId': bet.user_id, 'bet': bet.bet} for bet in self.bets]

        return {
            'id': self._id,
            'movieId': self.movie_id,
            'prizeInMillions': self.prize_in_millions,
            'closeDate': self.close_date,
            'bets': bets,
            'winner': self.winner
        }

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

