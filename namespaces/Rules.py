# -*- coding: utf-8 -*-
"""
Created on Thu Dec  5 13:36:27 2019

@author: Jason
"""

from flask import Blueprint, jsonify
from flask_login import login_required
from models.Database import mongo
from models.RuleModel import RuleModel

rules_blueprint = Blueprint('Rules', __name__)

@rules_blueprint.route('/rules', methods=['GET'])
@login_required
def get_rules():
    rulesResponse = []
    rulesResult = mongo.db.rules.find({})
    for rule in rulesResult:
        ruleModel = RuleModel(ruleName=rule['ruleName'], rules=rule['rules'])
        rulesResponse.append(ruleModel.__dict__)
    return jsonify(rulesResponse), 200