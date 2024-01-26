# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
from   decouple import config

class Config(object):

    basedir    = os.path.abspath(os.path.dirname(__file__))

    # Set up the App SECRET_KEY
    SECRET_KEY = config('SECRET_KEY', default='S#perS3crEt_007')
    SESSION_TYPE = 'filesystem'

    # This will create a file in <app> FOLDER
    #SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')
    DEBUG = False

    # Security
    SESSION_COOKIE_HTTPONLY  = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

    """
    # PostgreSQL database
    SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(
        config( 'DB_ENGINE'   , default='postgresql'    ),
        config( 'DB_USERNAME' , default='appseed'       ),
        config( 'DB_PASS'     , default='pass'          ),
        config( 'DB_HOST'     , default='localhost'     ),
        config( 'DB_PORT'     , default=5432            ),
        config( 'DB_NAME'     , default='appseed-flask' )
    )
    print(SQLALCHEMY_DATABASE_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    """

class ProductionConfig(Config):
    DEBUG = False

    SECRET_KEY = config('SECRET_KEY', default='S#perS3crEt_007')

    # Security
    SESSION_COOKIE_HTTPONLY  = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

    """
    # PostgreSQL database
    SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(
        config( 'DB_ENGINE'   , default='postgresql'    ),
        config( 'DB_USERNAME' , default='appseed'       ),
        config( 'DB_PASS'     , default='pass'          ),
        config( 'DB_HOST'     , default='localhost'     ),
        config( 'DB_PORT'     , default=5432            ),
        config( 'DB_NAME'     , default='appseed-flask' )
    )
    print(SQLALCHEMY_DATABASE_URI)
    """

class DebugConfig(Config):
    DEBUG = True

# Load all possible configurations
config_dict = {
    'Production': ProductionConfig,
    'Debug'     : DebugConfig
}
