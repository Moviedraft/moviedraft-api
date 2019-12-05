# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 13:42:32 2019

@author: Jason
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from datetime import datetime
from models.Database import mongo
from models.MoviesModel import MoviesModel
from enums.MovieReleaseType import MovieReleaseType

movies_blueprint = Blueprint('Movies', __name__)

@movies_blueprint.route('/movies', methods=['GET'])
@login_required
def get_movies():
    movies = []
    releaseType = request.args.get('releaseType')
    startDate = request.args.get('startDate')
    endDate = request.args.get('endDate')
    
    if not startDate:
        startDate = datetime.min.isoformat().split('T', 1)[0]
    if not endDate:
        endDate = datetime.max.isoformat().split('T', 1)[0]
    
    releaseDateFilterCondition = { '$lte': datetime.strptime(endDate, '%Y-%m-%d'),
                                  '$gte': datetime.strptime(startDate, '%Y-%m-%d') }

    if releaseType:
        if MovieReleaseType.has_value(releaseType):
            moviesResult = mongo.db.movies.find({'releaseType': releaseType, 
                                                 'releaseDate': releaseDateFilterCondition}).sort("releaseDate", 1)
            for movie in moviesResult:
                movieModel = MoviesModel(
                    movie['_id'], 
                    movie['releaseDate'], 
                    movie['title'], 
                    movie['releaseType'], 
                    movie['distributor'], 
                    movie['url'], 
                    movie['lastUpdated'])
                movies.append(movieModel.__dict__)
        return jsonify(movies), 200
    else:
        moviesResult = mongo.db.movies.find({'releaseDate': releaseDateFilterCondition}).sort("releaseDate", 1) 
        for movie in moviesResult:
            movieModel = MoviesModel(
                    movie['_id'], 
                    movie['releaseDate'], 
                    movie['title'], 
                    movie['releaseType'], 
                    movie['distributor'], 
                    movie['url'], 
                    movie['lastUpdated'])
            movies.append(movieModel.__dict__)
        return jsonify(movies), 200
