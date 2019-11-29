# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 14:53:49 2019

@author: Jason
"""

class MoviesModel():
    def __init__(self, id, releaseDate, title, releaseType, distributor, url, lastUpdated):
        self.id = str(id)
        self.releaseDate = releaseDate.isoformat()
        self.title = title
        self.releaseType = releaseType
        self.distributor = distributor
        self.url = url
        self.lastUpdated = lastUpdated.isoformat()