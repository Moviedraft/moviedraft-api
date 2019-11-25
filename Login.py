# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 13:45:07 2019

@author: Jason
"""

from flask import Blueprint, request, render_template
from flask_login import current_user, login_user, logout_user, login_required
from User import User
from Database import mongo
from Form import LoginForm

login_blueprint = Blueprint('Login', __name__)

@login_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        print('got past the validate check')
        user = mongo.db.Users.find_one({'Username': form.username.data})
        if user and User.validate_login(user['Password'], form.password.data):
          userObject = User(username=user['Username'])
          login_user(userObject)
          return 'You are logged in!'
        else:
           return 'Your password is wrong!'
    return render_template('Login.html', title='Login', form=form)

@login_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return 'You are logged out!'
    #return redirect(url_for('/'))
    
@login_blueprint.route('/home')
@login_required
def home():
    return 'The current user is ' + current_user.username