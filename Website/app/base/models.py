# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_login import UserMixin
#from sqlalchemy import Binary, Column, Integer, String

from app import login_manager, boto_sess

import boto3
from boto3.dynamodb.conditions import Key, Attr
import traceback


class User(UserMixin):
    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            setattr(self, property, value)
        #super().__init__()
        #self.table = self.dynamodb.Table('users')

    def get(username):
        user = None
        dynamodb = boto_sess.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('users')
        response = table.query(KeyConditionExpression=Key('username').eq(username))
        if response:
            items = response['Items']
            if (not items == None) and (not items == []):
                # Check the password
                if username==items[0]['username']:
                    user = User(username=username, email=items[0]['email'])
        return user if user else None

    def get_id(self):
        return self.username

@login_manager.user_loader
def user_loader(username):
    try:
        user = User.get(username=username)
    except:
        print(traceback.format_exc())
        user = None
    return user
