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
    def apply_rules(cls, moviesPurchased, rules, playerBids):
        totalGross = 0
        grossCapRule = next((rule for rule in rules if rule['ruleName'] == 'grossCap'), None)
        valueMultiplierRule = next((rule for rule in rules if rule['ruleName'] == 'valueMultiplier'), None)

        for movie in moviesPurchased:
            if not grossCapRule and not valueMultiplierRule:
                totalGross += movie.domesticGross
                continue

            purchase_price = next(bid.bid for bid in playerBids if bid.movie_id == movie.id)

            adjustedGross = cls.apply_gross_cap(movie.domesticGross,
                                                grossCapRule['rules']['capValue'],
                                                grossCapRule['rules']['centsOnDollar']) \
                if grossCapRule \
                else movie.domesticGross

            valueMultiplierTotal = cls.apply_value_multiplier_rule(adjustedGross,
                                                                   purchase_price,
                                                                   valueMultiplierRule['rules']['lowerThreshold'],
                                                                   valueMultiplierRule['rules']['upperThreshold']) \
                if valueMultiplierRule \
                else 0

            totalGross += adjustedGross + valueMultiplierTotal

        return totalGross

    @classmethod
    def apply_gross_cap(cls, gross_total, cap_value, cents_on_dollar):
        if gross_total > cap_value:
            total_to_manipulate = gross_total - cap_value

            return round(total_to_manipulate * cents_on_dollar) + cap_value

        return gross_total

    @classmethod
    def apply_value_multiplier_rule(cls, gross_total, purchase_price, lower_threshold, upper_threshold):
        value = cls.calculate_movie_value(gross_total, purchase_price)
        value_multiplier = cls.calculate_value_multiplier(value, lower_threshold, upper_threshold)

        return value * value_multiplier

    @classmethod
    def calculate_movie_value(cls, gross_total, purchase_price):
        return round(gross_total / purchase_price)

    @classmethod
    def calculate_value_multiplier(cls, value, lower_threshold, upper_threshold):
        if value >= upper_threshold:
            return 3
        if upper_threshold > value >= lower_threshold:
            return 2
        return 1

    def load_rule(ruleName):
        rule = mongo.db.rules.find_one({'ruleName': ruleName})
        if not rule:
            return None
        return RuleModel(
                ruleName=rule['ruleName'],
                rules=rule['ruleName'],
                )