# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
from flask_migrate import Migrate
from os import environ
from sys import exit
from decouple import config
import threading
import logging
import traceback
import boto3

"""
import RPi.GPIO as gpio

import app.sensors_code.temp_sensor as s_temp
import app.sensors_code.ultrasonic_sensor as s_ultrasonic
import app.sensors_code.water_level_sensor as s_water
import app.sensors_code.alert_system as alert_sys
import app.sensors_code.camera as s_cam
import app.sensors_code.food_servo as f_servo
"""
import app.modules.camera as s_cam
from config import config_dict
from app import create_app, boto_sess

s_cam.camThreadLock = threading.Lock()
#print("run.py threadLock type" + str(type(s_cam.camThreadLock)))

# WARNING: Don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False)
#print(DEBUG + " DEBUG VALUE")

# The configuration
get_config_mode = 'Debug' if DEBUG else 'Production'

try:
    
    # Load the configuration using the default values 
    app_config = config_dict[get_config_mode.capitalize()]

except KeyError:
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

app = create_app( app_config ) 
Migrate(app)

if __name__ == "__main__":
    print("run.py")
    logging.basicConfig(level=logging.INFO, format='%(threadName)s %(message)s')
    """
    s_temp.startup()
    s_ultrasonic.startup()
    s_water.startup()
    f_servo.startup()
    alert_sys.startup()
    """
    if boto_sess:
        print("123")
    app.run(host='0.0.0.0', debug=False, threaded=True, use_reloader=False)
try:
    pass
    #s_cam.shutdown()
except:
    print(traceback.format_exc())
#s_temp.f.close()
#s_temp.temp_cnx.close()
#gpio.cleanup()
#print("closed f and cleaned gpio")
exit(0)
