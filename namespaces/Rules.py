# -*- coding: utf-8 -*-
"""
Created on Thu Dec  5 13:36:27 2019

@author: Jason
"""

from flask import jsonify, make_response
from flask_jwt_extended import jwt_required
from flask_restplus import Namespace, Resource, fields
from utilities.Database import mongo
from models.RuleModel import RuleModel
from decorators.RoleAccessDecorator import requires_admin

rules_namespace = Namespace('rules', description='Game rules.')

wildcard = fields.Wildcard(fields.Integer)

rules_namespace.model('Rules', {
        'ruleName': fields.String,
        'rules': wildcard
        })

@rules_namespace.route('')
class Rules(Resource):
    @jwt_required
    @requires_admin
    @rules_namespace.response(200, 'Success', rules_namespace.models['Rules'])
    @rules_namespace.response(401, 'Authentication Error')
    @rules_namespace.response(500, 'Internal Server Error')
    def get(self):
        rulesResponse = []
        rulesResult = mongo.db.rules.find({})
        for rule in rulesResult:
            ruleModel = RuleModel(ruleName=rule['ruleName'], rules=rule['rules'])
            rulesResponse.append(ruleModel.__dict__)
        return make_response(jsonify(rulesResponse), 200)