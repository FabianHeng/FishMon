#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
#import mysql.connector
import RPi.GPIO as gpio
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_UP
import modules.temp_sensor as s_temp
import modules.ultrasonic_sensor as s_ultrasonic
import modules.water_level_sensor as s_water
import modules.food_servo as f_servo
#from twilio.rest import Client

import AWSIoTPythonSDK
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

import logging
import threading
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = None

GREEN = 23
RED = 24

t_alert = None

twilio_acc_sid = ""
twilio_auth_token = ""
client = None
twilio_hp = "" 
owner_hp = None

old_error = {}

rpiHost = ""
rootCAPath = "certs/rootca.pem"
pub_certificatePath = "certs/pub/certificate.pem.crt"
pub_privateKeyPath = "certs/pub/private.pem.key"

rpi_pub = None

def sendMessage(msg):
    global rpi_pub
    rpi_pub.publish("sensors/alerts", msg, 1)
    logging.info("alert: " + str(msg))

def setLed(isErr):
    if isErr:
        gpio.output(GREEN, gpio.LOW)
        gpio.output(RED, gpio.HIGH)
    else:
        gpio.output(GREEN, gpio.HIGH)
        gpio.output(RED, gpio.LOW)

def addAlertsToDB(alerts):
    global dynamodb
    
    table = dynamodb.Table('alerts')
    print("add alerts to db")
    #d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # ADD DYNAMODB HERE, ALERTS TABLE
    print("ALERTS ARE " + str(alerts))
    for a in alerts:
        print("FOR A IN ALERTS: " + str(a))
        d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        response = table.put_item(
            Item={
                'deviceid': 'raspberrypi',
                'details': a.get('desc'), 
                'type': a.get('type'),
                'date': d
            }
        )
        time.sleep(1)
    
    

def getStatusOfSensors():
    global old_error
    print("waiting for sensors to start...")
    time.sleep(30)
    while True:
        error_msgs = []
        error = {}
        message = ""
        temp = Decimal(s_temp.pollRealtimeData()).quantize(Decimal('.01'), rounding=ROUND_HALF_EVEN)
        food = Decimal(s_ultrasonic.getFoodLeft()).quantize(Decimal('.01'), rounding=ROUND_HALF_EVEN)
        water = s_water.getState()
       
        # temp check
        t_min = Decimal(s_temp.minTempThreshold).quantize(Decimal('.01'), rounding=ROUND_HALF_EVEN)
        t_max = Decimal(s_temp.maxTempThreshold).quantize(Decimal('1.'), rounding=ROUND_UP)
        
        print("temp {}".format(temp))
        if (temp < t_min) or (temp > t_max):
            #print("{0} < {1} < {2}".format(str(s_temp.minTempThreshold), str(type(temp)), str(type(t_min))))
            error_msgs.append({"desc": 'Water temperature of {}°C has exceeded threshold!\n'.format(temp), "type": "Warning"})
            error.update({'temp':True})
        
        # food check
        #f_min = Decimal(s_ultrasonic.foodWarnThreshold).quantize(Decimal('.01'), rounding=ROUND_HALF_EVEN)
        f_min = Decimal(s_ultrasonic.foodWarnThreshold).quantize(Decimal('1.'), rounding=ROUND_UP)
        
        print("food {}".format(food))
        if food < f_min:
            error_msgs.append({"desc": 'Food remaining is low!\n'.format(food), "type": "Warning"})
            error.update({'food':True})

        # water check
        print("water {}".format(water))
        if water == True:
            error_msgs.append({"desc": 'Water is low!\n', "type": "Warning"})
            error.update({'water':True})

        if (not error_msgs == []) and old_error != error:
            print("has error detected")
            #logging.info(error_msgs)
            # there is a problem with one or more of the tank env
            old_error = error
            print("=========DEBUG STUFF==========")
            #print(old_error)
            #print(error)
            #print(error_msgs)
            
            message += "FishMon Error Alerts:\n\n"
            for m in error_msgs:
                message += m.get('desc')
            #logging.info('errors: ' + message)
            sendMessage(message)
            
            #logging.info("HERE:::: ".format(error_msgs))
            addAlertsToDB(error_msgs)
            setLed(isErr=True)
        elif (not error_msgs == []) and old_error == error:
            logging.info('Error still the same, do nothing.')
            setLed(isErr=True)
        else:
            logging.info("no errors to report")
            old_error = {}
            setLed(isErr=False)
        time.sleep(15)

def startup(boto_sess):
    global dynamodb, rpi_pub
    # GET SETTINGS FROM DYNAMODB, settings[]
    settings = None
    
    logging.basicConfig(level=logging.INFO)

    dynamodb = boto_sess.resource('dynamodb')
    table = dynamodb.Table('settings')
    deviceid = 'raspberrypi'
    
    response = table.query(KeyConditionExpression=Key('deviceid').eq(deviceid))
    #print(response)
    items = response.get('Items')
    
    if items and (not items == []):
        # store db retrieved settings into application
        s_temp.minTempThreshold = int(items[0].get('minTempThreshold'))
        s_temp.maxTempThreshold = int(items[0].get('maxTempThreshold'))
        s_ultrasonic.foodWarnThreshold = int(items[0].get('foodWarnThreshold'))
        owner_hp = str(items[0].get('twilio_hp'))
        f_servo.foodDispenseTimes = int(items[0].get('foodDispenseTimes'))
        
        # setup LED Indicators
        gpio.setmode(gpio.BCM)
        gpio.setup(GREEN, gpio.OUT)
        gpio.setup(RED, gpio.OUT)
        
        # start mqtt client
        rpi_pub = AWSIoTMQTTClient("")
        rpi_pub.configureEndpoint(rpiHost, 8883)
        rpi_pub.configureCredentials(rootCAPath, pub_privateKeyPath, pub_certificatePath)

        rpi_pub.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        rpi_pub.configureDrainingFrequency(2)  # Draining: 2 Hz
        rpi_pub.configureConnectDisconnectTimeout(10)  # 10 sec
        rpi_pub.configureMQTTOperationTimeout(10)  # 10 sec

        rpi_pub.connect()
        
        # start threading for sensor polling and alerting
        t_alert = threading.Thread(target=getStatusOfSensors, name='t_pollAllSensors') #, daemon=Tr$
        t_alert.daemon = True
        t_alert.start()
