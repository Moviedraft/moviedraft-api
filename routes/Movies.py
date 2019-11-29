# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 13:42:32 2019

@author: Jason
"""

from flask import Blueprint, request, jsonify, abort, make_response
from flask_login import login_required
from models.Database import mongo
from models.MoviesModel import MoviesModel
from enums.MovieReleaseType import MovieReleaseType

movies_blueprint = Blueprint('Movies', __name__)

@movies_blueprint.route('/movies', methods=['GET'])
@login_required
def get_movies():
    movies = []
    releaseType = request.args.get('releaseType')
    
    if releaseType == MovieReleaseType.All.name:
        moviesResult = mongo.db.movies.find({})
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
    
    if releaseType:
        if MovieReleaseType.has_value(releaseType):
            moviesResult = mongo.db.movies.find({'releaseType': releaseType})
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
    
    return abort(make_response(jsonify(message='There was a problem retrieving the movies.'), 500))
