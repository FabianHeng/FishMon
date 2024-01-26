# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
import json
from datetime import datetime
import traceback
import time

from app.home import blueprint
from flask import render_template, redirect, url_for, request, Response
from flask_login import login_required, current_user
from app import login_manager, boto_sess, rpi_pub
from jinja2 import TemplateNotFound

import boto3
from boto3.dynamodb.conditions import Key, Attr
import AWSIoTPythonSDK
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

import app.modules.camera as s_cam


rpiHost = ""
rootCAPath = "certs/rootca.pem"
sub_certificatePath = "certs/sub/certificate.pem.crt"
sub_privateKeyPath = "certs/sub/private.pem.key"

def getAlerts():
    print("alerts")
    # get latest 15 alerts
    
    dynamodb = boto_sess.resource('dynamodb')
    table = dynamodb.Table('alerts')
    response = table.query(
        KeyConditionExpression=Key('deviceid').eq('raspberrypi'),
        ScanIndexForward=False,
        Limit=15
    )
    
    data = None
    if response:
        data = response['Items']
        if not data == []:
            tmp = []
            for item in data:
                print(str(item))
                tmp.append({'desc':item.get("details"), 'type': item.get("type"), 'date': item.get("date")})
        else:
           tmp = None
    return tmp


@blueprint.route('/index')
@login_required
def index():
    print(type(boto_sess))
    #streamStop()

    alerts = getAlerts()
    return render_template('index.html', segment='index', alerts=alerts)
    
@blueprint.route('/stream')
@login_required
def stream():
    global boto_sess
    creds = {}
    if boto_sess:
        c = boto_sess.get_credentials()
        creds = {
            "access_key" : c.access_key, 
            "secret_key" : c.secret_key, 
            "token": c.token
        }
    print(creds)
    return render_template('stream.html', segment='stream', creds=creds)

@blueprint.route('/pastdata', methods=['GET'])
def pastData():
    
    dynamodb = boto_sess.resource('dynamodb')
    table = dynamodb.Table('alerts')
    response = table.query(
        KeyConditionExpression=Key('deviceid').eq('raspberrypi'),
        ScanIndexForward=False,
        Limit=15
    )
    
    ret = None
    if data:
        ret = []
        count = 0
        for entry in data:
            ret.append({"id": count, "date": entry.get("date"), "temperature":entry.get("temperature")})
            count += 1
    return render_template('pastdata.html', table_data=ret)


@blueprint.route('/<template>')
@login_required
def route_template(template):
    try:
        if not template.endswith( '.html' ):
            template += '.html'

        # Detect the current page
        segment = get_segment( request )

        # Serve the file (if exists) from app/templates/FILE.html
        return render_template( template, segment=segment )

    except TemplateNotFound:
        return render_template('page-404.html'), 404

    except:
        return render_template('page-500.html'), 500

# Helper - Extract current page name from request 
def get_segment( request ): 
    try:
        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment    

    except:
        return None  


rekognition_message = None
def rekognitionCallBack(client, userdata, message):
    global rekognition_message
    rekognition_message = str(message.payload)[2:-1]

def getLatestTemperature():
    global boto_sess
    dynamodb = boto_sess.resource('dynamodb')
    table = dynamodb.Table('sensor_temp')
    response = table.query(
        KeyConditionExpression=Key('deviceid').eq('raspberrypi'),
        ScanIndexForward=False,
        Limit=1
    )
    if response:
        print(response)
        items = response['Items']
        if items and items != []:
            return items[0].get("temperature")
    
    
## APIs
@blueprint.route('/api/getRekognition', methods=['GET'])
def getRekognition():
    global rekognition_message
    temp = AWSIoTMQTTClient("temp")
    temp.configureEndpoint(rpiHost, 8883)
    temp.configureCredentials(rootCAPath, sub_privateKeyPath, sub_certificatePath)

    temp.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
    temp.configureDrainingFrequency(2)  # Draining: 2 Hz
    temp.configureConnectDisconnectTimeout(10)  # 10 sec
    temp.configureMQTTOperationTimeout(5)  # 5 sec

    # Connect and subscribe to AWS IoT
    temp.connect()
    temp.subscribe("sensors/rekognition", 1, rekognitionCallBack)

    while (rekognition_message == None):
        time.sleep(1)
    temp.disconnect()

    return rekognition_data

@blueprint.route('/api/getTempData', methods=['GET'])
def getTempData():
    print("getTempData")
    rekognition_message = None
    d = datetime.now().strftime("%H:%M:%S")
    curr_temp = getLatestTemperature()
    data = json.dumps({"time":d, "temperature":curr_temp})
    return data


food_data = None

def retrieveFoodDataCallback(client, userdata, message):
    global food_data
    try:
        print("+++++++++++++++++++++++++++++++++ FOOD RETURN: " + str(message.payload)[2:-1])
        food_data = json.loads(str(message.payload)[2:-1])
    except:
        print(traceback.format_exc())

@blueprint.route('/api/getFoodPercent', methods=['GET'])
def getFoodPercent():
    print("getFoodPercent")
    # food percentage is incorrect, retrieve again\
    global food_data, rpi_pub
    food_data = None
    
    temp = AWSIoTMQTTClient("")
    temp.configureEndpoint(rpiHost, 8883)
    temp.configureCredentials(rootCAPath, sub_privateKeyPath, sub_certificatePath)
    
    temp.configureOfflinePublishQueueing(-1)          # Infinite offline Publish queueing
    temp.configureDrainingFrequency(2)                # Draining: 2 Hz
    temp.configureConnectDisconnectTimeout(10)        # 10 sec
    temp.configureMQTTOperationTimeout(5)             # 5 sec
    temp.connect()
    
    temp.subscribe("sensors/food", 1, retrieveFoodDataCallback)
    
    req_data = {"req":"food"}
    
    rpi_pub.publish("sensors/requests", json.dumps(req_data), 1)
    
    while True:
        if food_data != None:
            food_percentage = food_data.get("value")
            if food_percentage >= 0:
                break
            else:
                food_data = None
                rpi_pub.publish("sensors/requests", json.dumps(req_data), 1)
        time.sleep(1)

    temp.disconnect()
    print("=====================================  FINAL FOOD RETURN "+ str(food_percentage))
    d = datetime.now().strftime("%H:%M:%S")
    data = json.dumps({"time":d, "value":str(food_percentage)+"%" })
    
    return data


water_state = None

def retrieveWaterDataCallback(client, userdata, message):
    global water_state
    try:
        print("+++++++++++++++++++++++++++++++++ WATER RETURN: " + str(str(message.payload)[2:-1]))
        water_state = json.loads(str(message.payload)[2:-1])
    except:
        print(traceback.format_exc())

@blueprint.route('/api/getWaterLevelStatus', methods=['GET'])
def getWaterLevelStatus():
    print("getWaterLevelStatus")
    global water_state, rpi_pub
    
    global rpiHost, rootCAPath, privateKeyPath, certificatePath, water_state
    temp = AWSIoTMQTTClient("")
    temp.configureEndpoint(rpiHost, 8883)
    #print(os.getcwd())
    temp.configureCredentials(rootCAPath, sub_privateKeyPath, sub_certificatePath)
    
    temp.configureOfflinePublishQueueing(-1)          # Infinite offline Publish queueing
    temp.configureDrainingFrequency(2)                # Draining: 2 Hz
    temp.configureConnectDisconnectTimeout(10)        # 10 sec
    temp.configureMQTTOperationTimeout(5)             # 5 sec
    temp.connect()
    
    temp.subscribe("sensors/water", 1, retrieveWaterDataCallback)
    
    req_data = {"req":"water"}
    rpi_pub.publish("sensors/requests", json.dumps(req_data), 1)
    
    water_state = None
    
    while True:
        if water_state != None:
            break
        time.sleep(1)
        
    temp.disconnect()    
    state = water_state.get("value")
    
    if state == False:
        print('OK!')
        status = 'OK'
    else:
        print('LOW!')
        status = 'Water LOW!'
    
    print("=====================================  FINAL WATER RETURN "+ status)

    d = datetime.now().strftime("%H:%M:%S")
    data = json.dumps({"time":d, "value":status})
    return data

@blueprint.route('/api/runFeeder', methods=['GET'])
def runFeeder():
    global rpi_pub
    print("runFeeder")
    rpi_pub.publish("sensors/dispend", "run", 1)
    return "ran"

def updateSettingsMQTT(c, newSettings):
    global rpi_pub
    
    if c == 'f':
        rpi_pub.publish("settings/food", json.dumps(newSettings), 1)
    elif c == 't':
        rpi_pub.publish("settings/temp", json.dumps(newSettings), 1)
    elif c == 'a':
        rpi_pub.publish("settings/alert", json.dumps(newSettings), 1)
    else:
        pass
        
        
def updateSettingsDB(c, newSettings):
    print("Update settings")
    dynamodb = boto_sess.resource('dynamodb')
    table = dynamodb.Table('settings')
        
    if c == 'f':
        response = table.update_item(
            Key={'deviceid':'raspberrypi'},
            UpdateExpression="set foodDispenseTimes=:fdt, foodWarnThreshold=:fwt",
            ExpressionAttributeValues={':fdt': newSettings.get('foodCountInput'), ':fwt': newSettings.get('foodWarnInput') },
            ReturnValues="UPDATED_NEW"
        )
        print(response)
    elif c == 't':
        response = table.update_item(
            Key={'deviceid':'raspberrypi'},
            UpdateExpression="set minTempThreshold=:min, maxTempThreshold=:max",
            ExpressionAttributeValues={':min': newSettings.get('minTempInput'), ':max': newSettings.get('maxTempInput')},
            ReturnValues="UPDATED_NEW"
        )
        print(response)
    else:
        response = table.update_item(
            Key={'deviceid':'raspberrypi'},
            UpdateExpression="set twilio_hp=:thp",
            ExpressionAttributeValues={':thp': newSettings.get('twilioHP')},
            ReturnValues="UPDATED_NEW"
        )
        print(response)
    
@blueprint.route('/api/updateSettings/<set>', methods=['GET', 'POST'])
def updateSettings(set):
    if request.method == 'GET':
        print('get settings')
        # dynamodb get settings
        try:
            dynamodb = boto_sess.resource('dynamodb')
            table = dynamodb.Table('settings')
            deviceid = 'raspberrypi'
            
            response = table.query(KeyConditionExpression=Key('deviceid').eq(deviceid))
            items = response.get('Items')
            if items and (not items == []):
                settings = {
                    "minTempThreshold": items[0].get('minTempThreshold'), 
                    "maxTempThreshold": items[0].get('maxTempThreshold'), 
                    "foodWarnThreshold": items[0].get('foodWarnThreshold'),
                    "foodDispenseTimes": items[0].get('foodDispenseTimes'),
                    "twilio_hp": items[0].get('twilio_hp')
                }
            return json.dumps(settings)
            
        except:
            print(traceback.format_exc())
            return render_template('settings.html', error=True)
    else:
        print("form {0} | values {1}".format(str(request.form), str(request.values)))
        try:
            if set == 'food':
                
                newSettings = {
                    "foodCountInput": request.form.get("foodCountInput"), 
                    "foodWarnInput": request.form.get("foodWarnInput")
                }
                
                updateSettingsMQTT('f', newSettings)
                updateSettingsDB('f', newSettings)
                return render_template('settings.html', msg_f="Settings Changed!")
            elif set == 'temperature':
            
                newSettings = {
                    "minTempInput": request.form.get("minTempInput"), 
                    "maxTempInput": request.form.get("maxTempInput")
                }
                
                updateSettingsMQTT('t', newSettings)
                updateSettingsDB('t', newSettings)
                return render_template('settings.html', msg_t="Settings Changed!")
            elif set == 'alert':
                newSettings = {"twilioHP": request.form.get("twilioHP")}
                updateSettingsMQTT('a', newSettings)
                updateSettingsDB('a', newSettings)
                return render_template('settings.html', msg_a="Settings Changed!")
            else:
                pass
        except:
            print(traceback.format_exc())



