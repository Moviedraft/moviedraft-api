# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 13:59:36 2019

@author: Jason
"""
from enum import Enum

class MovieReleaseType(Enum): 
    Wide = 1
    Limited = 2
    All = 3
    
    @classmethod
    def has_value(cls, value):
        return value in cls._member_names_ 