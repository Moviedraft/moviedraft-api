# -*- coding: utf-8 -*-
"""
Created on Tue Jan  7 12:11:08 2020

@author: Jason
"""

from functools import wraps
from flask import make_response, jsonify
from flask_login import current_user

def requires_role(requiredRole):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwds):
            if not current_user.allowed(requiredRole):
                return make_response(jsonify(message='You are not authorized to view this resource.'), 403)       
            return fn(*args, **kwds)
        return wrapper
    return decorator
