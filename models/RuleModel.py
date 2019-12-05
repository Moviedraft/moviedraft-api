# -*- coding: utf-8 -*-
"""
Created on Thu Dec  5 13:04:11 2019

@author: Jason
"""

from models.Database import mongo

class RuleModel():
    def __init__(self, ruleName, rules):
        self.ruleName = ruleName
        self.rules = rules
        
    def load_rule(ruleName):
        rule = mongo.db.rules.find_one({'ruleName': ruleName})
        if not rule:
            return None
        return RuleModel(
                ruleName=rule['ruleName'],
                rules=rule['ruleName'],
                )