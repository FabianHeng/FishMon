# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import jsonify, render_template, redirect, request, url_for, session
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)

from app import login_manager, boto_sess, sess
from app.base import blueprint
from app.base.forms import LoginForm, CreateAccountForm
from app.base.models import User
from app.base.util import verify_pass, hash_pass

import boto3
from boto3.dynamodb.conditions import Key, Attr

@blueprint.route('/')
def route_default():
    print("default")
    return redirect(url_for('base_blueprint.login'))

## Login & Registration

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    global boto_sess
    print("login")
    login_form = LoginForm(request.form)
    if not current_user:
        return render_template( 'accounts/login.html', form=login_form)
    
    if 'login' in request.form:
        
        # read form data
        username = request.form['username']
        password = request.form['password']
        print(username)

        # Locate user
        if boto_sess:
            print("boto exists")
            dynamodb = boto_sess.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.Table('users') 
            response = table.query(KeyConditionExpression=Key('username').eq(username))
            
            if response:
                items = response['Items']
                if not items == None or not items == []: 
                    # Check the password
                    if username==items[0]['username'] and verify_pass( password, items[0]['password']):
                        user = User(username=username, email=items[0]['email'])
                        login_user(user)
                        session['username'] = username
                        return redirect(url_for('base_blueprint.route_default'))

                    # Something (user or pass) is not ok
                    return render_template( 'accounts/login.html', msg='Wrong user or password', form=login_form)
                    
    if current_user and (not current_user.is_authenticated):
        return render_template( 'accounts/login.html', form=login_form)
    
    return redirect(url_for('home_blueprint.index'))

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    global boto_sess
    login_form = LoginForm(request.form)
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username  = request.form['username']
        email     = request.form['email'   ]

        if boto_sess:
            dynamodb = boto_sess.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.Table('users') 
            response = table.query(KeyConditionExpression=Key('username').eq(username))
            # Check usename exists
            if response:
                items = response['Items']
                if (not items == None) and (not items == []):
                    if username == items[0]['username']:
                        return render_template( 'accounts/register.html', 
                                                msg='Username already registered',
                                                success=False,
                                                form=create_account_form)

                    # Check email exists
                    if email == items[0]['email']:
                        return render_template( 'accounts/register.html', 
                                                msg='Email already registered', 
                                                success=False,
                                                form=create_account_form)

                # items = [] if user non existent
                else:
                    response = table.put_item(
                    Item = {
                            'username': username,
                            'email': email,
                            'password': hash_pass(password)
                        }
                    )

                    return render_template( 'accounts/register.html', 
                                            msg='User created please <a href="/login">login</a>', 
                                            success=True,
                                            form=create_account_form)

    else:
        return render_template( 'accounts/register.html', form=create_account_form)

@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('base_blueprint.login'))

@blueprint.route('/shutdown')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'


## Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('page-403.html'), 403

@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('page-403.html'), 403

@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('page-404.html'), 404

@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('page-500.html'), 500
