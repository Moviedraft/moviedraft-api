# -*- coding: utf-8 -*-
"""
Created on Tue Jan  7 12:11:08 2020

@author: Jason
"""

from functools import wraps
from flask import make_response, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from enums.Role import Role

def requires_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except:
            return make_response(jsonify(message='Token is invalid.'), 401)
        identity = get_jwt_identity()
        if identity['role'] != Role.admin.value:
            return make_response(jsonify(message='You are not authorized to view this resource.'), 403)
        return fn(*args, **kwargs)
    return wrapper

        