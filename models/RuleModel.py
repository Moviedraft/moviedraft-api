# -*- coding: utf-8 -*-
"""
Created on Thu Dec  5 13:04:11 2019

@author: Jason
"""

from utilities.Database import mongo

class RuleModel():
    def __init__(self, ruleName, rules):
        self.ruleName = ruleName
        self.rules = rules

    @classmethod
    def apply_gross_cap(cls, gross_total, cap_value, cents_on_dollar):
        if gross_total > cap_value:
            total_to_manipulate = gross_total - cap_value
            return round(total_to_manipulate * cents_on_dollar) + cap_value

        return gross_total
        
    def load_rule(ruleName):
        rule = mongo.db.rules.find_one({'ruleName': ruleName})
        if not rule:
            return None
        return RuleModel(
                ruleName=rule['ruleName'],
                rules=rule['ruleName'],
                )