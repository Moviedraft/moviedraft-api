# -*- coding: utf-8 -*-
"""
Created on Thu Feb 13 12:33:56 2020

@author: Jason
"""

from flask import abort, make_response, jsonify
from flask_jwt_extended import decode_token
from datetime import datetime
from bson.objectid import ObjectId
from models.TokenModel import TokenModel
from utilities.Database import mongo

def add_token_to_database(encoded_token, identity_claim):
    decoded_token = decode_token(encoded_token)
    
    id = decoded_token['identity']['tokenId']
    jti = decoded_token['jti']
    token_type = decoded_token['type']
    user_identity = decoded_token[identity_claim]
    expires = datetime.fromtimestamp(decoded_token['exp'])
    revoked = False

    tokenModel = TokenModel(_id=ObjectId(id),
                            jti=jti,
                            token_type=token_type,
                            user_identity=user_identity,
                            expires=expires,
                            revoked=revoked)
    
    mongo.db.tokens.insert_one(tokenModel.__dict__)

def get_token_expiry(encoded_token):
    decoded_token = decode_token(encoded_token)
    expires = datetime.fromtimestamp(decoded_token['exp']).isoformat()
    return expires

def is_token_revoked(decoded_token):
    jti = decoded_token['jti']
    token = TokenModel.load_token({'jti': jti})
    
    if not token:
        return True
    
    return token.revoked

def revoke_token(token_id):
    tokenModel = TokenModel.load_token_by_id(token_id)
    
    if not tokenModel:
        abort(make_response(jsonify(message='Unable to find token {}'.format(token_id)), 404))
        
    tokenModel.revoked = True
    updatedToken = tokenModel.update_token()
    
    if not updatedToken:
        abort(make_response(jsonify(message='Unable to update token {}'.format(token_id)), 500))