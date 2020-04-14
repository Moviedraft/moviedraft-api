# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 11:12:31 2020

@author: Jason
"""

from utilities.Database import mongo
from bson.objectid import ObjectId

class ChoicesModel():
    def __init__(self, choice):
        self.displayText = choice['displayText']
        self.votes = choice['votes']
        
class PollModel():
    def __init__(self, id, gameId, question, choices):
        self.id = id
        self.gameId = gameId
        self.question = question
        self.choices = choices
    
    def serialize(self):
        choices = [{'displayText': choice.displayText, 'votes': choice.votes} for choice in self.choices]
        
        return {
                'id': self.id,
                'gameId': self.gameId,
                'question': self.question,
                'choices': choices
                }
    
    def update_vote(self, displayText, vote):
        result = mongo.db.polls.update_one({'_id': ObjectId(self.id), 'choices.displayText': displayText}, 
                                           { '$set': { 'choices.$.votes': vote }})
        
        if result.modified_count == 1:
            return self.load_poll_by_id(self.id)
        
        return None

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
        queryDict = {'gameId': ObjectId(gameId)}
        poll = cls.load_poll(queryDict)
        return poll
    
    @classmethod
    def load_poll(cls, queryDict):
        poll = mongo.db.polls.find_one(queryDict)
        if not poll:
            return None
        
        choices = [ChoicesModel(choice) for choice in poll['choices']]
        
        return PollModel(id = str(poll['_id']),
                         gameId = str(poll['gameId']),
                         question = poll['question'],
                         choices = choices)
    