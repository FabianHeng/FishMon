# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
from flask import Flask, url_for, session
from flask_session import Session
from flask_login import LoginManager
#from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from logging import basicConfig, DEBUG, getLogger, StreamHandler
from os import path
import boto3

import AWSIoTPythonSDK
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

login_manager = LoginManager()
boto_sess = None
rpi_pub = None
sess = None

def register_extensions(app):
    #db.init_app(app)
    #sess.init_app(app)
    login_manager.init_app(app)
    

def register_blueprints(app):
    for module_name in ('base', 'home'):
        module = import_module('app.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)

"""
def configure_database(app):

    @app.before_first_request
    def initialize_database():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()
"""

def create_app(config):
    global boto_sess, sess, rpi_pub, rpi_sub
    app = Flask(__name__, static_folder='base/static')
    
    rpiHost = ""
    rootCAPath = "certs/rootca.pem"

    pub_certificatePath = "certs/pub/certificate.pem.crt"
    pub_privateKeyPath = "certs/pub/private.pem.key"
    
    boto_sess = boto3.Session(profile_name='default', region_name='us-east-1') # REQUIRES CHANGE FOR PRODUCTION
    #print(type(boto_sess))
    
    rpi_pub = AWSIoTMQTTClient("")
    rpi_pub.configureEndpoint(rpiHost, 8883)
    rpi_pub.configureCredentials(rootCAPath, pub_privateKeyPath, pub_certificatePath)
    
    rpi_pub.configureOfflinePublishQueueing(-1)          # Infinite offline Publish queueing
    rpi_pub.configureDrainingFrequency(2)                # Draining: 2 Hz
    rpi_pub.configureConnectDisconnectTimeout(10)        # 10 sec
    rpi_pub.configureMQTTOperationTimeout(5)             # 5 sec
    rpi_pub.connect()
    
    app.config.from_object(config)
    sess = Session()
    sess.init_app(app)
    register_extensions(app)
    register_blueprints(app)
    #configure_database(app)
    return app
