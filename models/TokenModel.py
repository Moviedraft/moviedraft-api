# -*- coding: utf-8 -*-
"""
Created on Thu Feb 13 12:35:59 2020

@author: Jason
"""

from bson.objectid import ObjectId
from utilities.Database import mongo

class TokenModel():
    def __init__(self, _id, jti, token_type, user_identity, revoked, expires):
        self._id = _id
        self.jti = jti
        self.token_type = token_type
        self.user_identity = user_identity
        self.revoked = revoked
        self.expires = expires
    
    @classmethod
    def load_token_by_id(cls, id):
        if not ObjectId.is_valid(id):
            return None
        queryDict = {'_id': ObjectId(id)}
        token = cls.load_token(queryDict) 
        
        return token
        
    @classmethod
    def load_token(cls, queryDict):
        token = mongo.db.tokens.find_one(queryDict)
        
        if not token:
            return None
        
        return TokenModel(_id = str(token['_id']),
                jti = token['jti'],
                token_type = token['token_type'],
                user_identity = token['user_identity'],
                revoked = token['revoked'],
                expires = token['expires'])
    
    def update_token(self):
        result = mongo.db.tokens.update_one({'_id': ObjectId(self._id)}, 
                                            { '$set': {'jti': self.jti,
                                             'token_type': self.token_type,
                                             'user_identity': self.user_identity,
                                             'revoked': self.revoked,
                                             'expires': self.expires
                                            }})
        if result.modified_count == 1:
            return self.load_token({'_id': ObjectId(self._id)})
        
        return None