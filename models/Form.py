# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 14:35:27 2019

@author: Jason
"""

from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired

class LoginForm(Form):
    """Login form to access writing and settings pages"""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])