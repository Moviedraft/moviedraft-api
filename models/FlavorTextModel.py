from utilities.Database import mongo
from bson.objectid import ObjectId
from utilities.DatetimeHelper import get_most_recent_day
from enums.DaysOfWeek import DaysOfWeek
import arrow

class FlavorTextModel():
    def __init__(self, _id, game_id, type, text):
        self._id = _id
        self.game_id = game_id
        self.type = type
        self.text = text

    def serialize(self):
        return {
            'id': self._id,
            'gameId': self.game_id,
            'type': self.type,
            'text': self.text
        }

    def update_flavor_text(self):
        result = mongo.db.flavortext.update_one({'_id': ObjectId(self._id)},
                                               {'$set': {
                                                   'text': self.text
                                               }})
        if result.modified_count == 1:
            return self.load_flavor_text_by_id(self._id)

        return None

    @classmethod
    def create_flavor_text(cls, game_id, type, text):
        if not ObjectId.is_valid(game_id):
            return None

        flavorTextModel = FlavorTextModel(_id=ObjectId(),
                                          game_id=ObjectId(game_id),
                                          type=type,
                                          text=text,
                                         )

        result = mongo.db.flavortext.insert_one(flavorTextModel.__dict__)

        if result.acknowledged:
            inserted_flavor_text = cls.load_flavor_text_by_id(str(result.inserted_id))
            return inserted_flavor_text

        return None

    @classmethod
    def load_flavor_text_by_id(cls, id):
        if not ObjectId.is_valid(id):
            return None
        query_dict = {'_id': ObjectId(id)}
        flavor_text = cls.load_flavor_text(query_dict)
        return flavor_text

    @classmethod
    def load_flavor_text_by_game_id_and_type(cls, game_id, type):
        if not ObjectId.is_valid(game_id):
            return None
        query_dict = {'game_id': ObjectId(game_id), 'type': type}
        flavor_text = cls.load_flavor_text(query_dict)
        return flavor_text

    @classmethod
    def load_flavor_text(cls, queryDict):
        weekendEnding = get_most_recent_day(DaysOfWeek.Monday.value)
        recent_monday_id = ObjectId.from_datetime(arrow.get(weekendEnding))
        flavorText = mongo.db.flavortext.find_one({'$and': [{'_id': {'$gte': recent_monday_id}}, queryDict]})
        
        if not flavorText:
            return None
        return FlavorTextModel(_id=str(flavorText['_id']),
                               game_id=str(flavorText['game_id']),
                               type=flavorText['type'],
                               text=flavorText['text']
                               )
