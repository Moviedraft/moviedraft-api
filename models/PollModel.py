# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 11:12:31 2020

@author: Jason
"""

from utilities.Database import mongo
from utilities.DatetimeHelper import get_most_recent_day
from enums.DaysOfWeek import DaysOfWeek
from bson.objectid import ObjectId
import json
import arrow

class ChoiceModel():
    def __init__(self, displayText, votes):
        self.displayText = displayText
        self.votes = votes

class PollModel():
    def __init__(self, id, gameId, question, choices, current, voters):
        self._id = id
        self.gameId = gameId
        self.question = question
        self.choices = choices
        self.current = current
        self.voters = voters
    
    def serialize(self):
        choices = [{'displayText': choice.displayText, 'votes': choice.votes} for choice in self.choices]
        voters = [str(voter) for voter in self.voters]

        return {
                'id': self._id,
                'gameId': self.gameId,
                'question': self.question,
                'choices': choices,
                'current': self.current,
                'voters': voters
                }
    
    def update_poll(self):
        choiceModels = [ChoiceModel(displayText=choice.displayText, votes=choice.votes) for choice in self.choices]
        jsonChoices = json.dumps([choice.__dict__ for choice in choiceModels])
        
        result = mongo.db.polls.update_one({'_id': ObjectId(self._id)}, 
                                           {'$set': {'gameId': ObjectId(self.gameId),
                                                     'question': self.question,
                                                     'choices': json.loads(jsonChoices),
                                                     'current': self.current,
                                                     'voters': self.voters}})
        
        if result.modified_count == 1:
            return self.load_poll_by_id(self._id)
        
        return None
    
    def update_vote(self, displayText, vote, user_id):
        if not ObjectId.is_valid(user_id):
            return None

        self.voters.append(ObjectId(user_id))

        result = mongo.db.polls.update_one({'_id': ObjectId(self._id), 'choices.displayText': displayText}, 
                                           { '$set': { 'choices.$.votes': vote, 'voters': self.voters }})
        
        if result.modified_count == 1:
            return self.load_poll_by_id(self._id)
        
        return None
    
    @classmethod
    def create_poll(cls, gameId, question, choices):
        choiceModels = [ChoiceModel(displayText=choice, votes=0) for choice in choices]
        jsonChoices = json.dumps([choice.__dict__ for choice in choiceModels])
        
        pollModel = PollModel(id=ObjectId(), 
                              gameId=ObjectId(gameId), 
                              question=question, 
                              choices=json.loads(jsonChoices), 
                              current=True,
                              voters=[])

        result = mongo.db.polls.insert_one(pollModel.__dict__)

        if result.acknowledged:
            insertedPoll = cls.load_poll_by_id(str(result.inserted_id))
            return insertedPoll
        
        return None
    
    @classmethod
    def disable_previous_poll(cls, gameId):
        currentPoll = cls.load_poll_by_gameId(gameId)
        
        if not currentPoll:
            return None

        currentPoll.current = False

        updatedPoll = currentPoll.update_poll()
        
        if not updatedPoll:
            return None
        
        return updatedPoll
        
    @classmethod
    def load_poll_by_id(cls, id):
        if not ObjectId.is_valid(id):
            return None
        queryDict = {'_id': ObjectId(id)}
        poll = cls.load_poll(queryDict)
        return poll
        
    @classmethod
    def load_poll_by_gameId(cls, gameId):
        if not ObjectId.is_valid(gameId):
            return None
        queryDict = {'gameId': ObjectId(gameId), 'current': True}
        poll = cls.load_poll(queryDict)
        return poll
    
    @classmethod
    def load_poll(cls, queryDict):
        weekendEnding = get_most_recent_day(DaysOfWeek.Monday.value)
        recent_monday_id = ObjectId.from_datetime(arrow.get(weekendEnding))
        poll = mongo.db.polls.find_one({'$and': [{'_id': {'$gte': recent_monday_id}}, queryDict]})
        
        if not poll:
            return None
        
        choices = [ChoiceModel(displayText=choice['displayText'], votes=choice['votes']) for choice in poll['choices']]
        
        return PollModel(id = str(poll['_id']),
                         gameId = str(poll['gameId']),
                         question = poll['question'],
                         choices = choices,
                         current = poll['current'],
                         voters=poll['voters'])
    
        