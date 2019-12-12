# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 10:47:51 2019

@author: Jason
"""

from flask_restplus import Api

description = ('Moviedraft game API '
                       '<style>.models {display: none !important} '
                       '.download-contents {display: none !important} '
                       '.try-out {display: none !important}</style>')

restApi = Api(
        title='Moviedraft', 
        doc='/swagger', 
        version='1.0', 
        description=description
        )