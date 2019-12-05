# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 13:59:36 2019

@author: Jason
"""
from enum import Enum

class MovieReleaseType(Enum): 
    wide = 1
    limited = 2
    
    @classmethod
    def has_value(cls, value):
        return value.lower() in cls._member_names_ 