# main.py file to add everything together, start and shutdown stuff

import modules.temp_sensor as s_temp
import modules.ultrasonic_sensor as s_ultrasonic
import modules.water_level_sensor as s_water
import modules.food_servo as f_servo
import modules.alert_system as alert_sys

import RPi.GPIO as gpio

import AWSIoTPythonSDK
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

import boto3
import json
import traceback
import sys
import datetime

camRunning = False
boto_sess = None

host = ""
rootCAPath = "certs/rootca.pem"

sub_certificatePath = "certs/sub/certificate.pem.crt"
sub_privateKeyPath = "certs/sub/private.pem.key"

pub_certificatePath = "certs/pub/certificate.pem.crt"
pub_privateKeyPath = "certs/pub/private.pem.key"

rpi_pub = None
rpi_sub = None

# call this to get and send requested sensor data
def sendRequestedData(client, userdata, message):
    global rpi_pub
    print("run sendRequestedData"+str(message))
    try:
        req = str(json.loads(message.payload).get("req"))
        d = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #print(req)
        if req == "food":
            # return food
            data = {"value": s_ultrasonic.getFoodLeft(), "date": d}
            rpi_pub.publish('sensors/food', json.dumps(data), 1)
        elif req == "water":
            # return water
            data = {"value": s_water.getState(), "date": d}
            rpi_pub.publish('sensors/water', json.dumps(data), 1)
        else:
            # pass
            pass
        print(str(data))
    except:
        print(traceback.format_exc())
    
# call this to update the settings
def updateSettings(client, userdata, message):
    try:
        topic = (message.topic)[9:]
        data = (json.loads(message.payload)).get('message')
        print(str(type(data)))
        print(str(data))
        
        if topic == 'food':
            # GET MQTT SETTING CHANGES HERE
            f_servo.foodDispenseTimes = data.get("foodCountInput")
            s_ultrasonic.foodWarnThreshold = data.get("foodWarnInput")                
            print("set food")                
        elif topic == 'temp':
            # GET MQTT SETTING CHANGES HERE
            s_temp.minTempThreshold = data.get('minTempInput')
            s_temp.maxTempThreshold = data.get('maxTempInput')
                
            print("set temperature")
        elif topic == 'alert':
            # GET MQTT SETTING CHANGES HERE
            #print(data)
            alert_sys.owner_hp = data.get('twilioHP')
            #print(alert_sys.owner_hp)
            #print(json.loads(data))
            print("set alert")
        else:
            #print(data)
            pass
    except:
        print(traceback.format_exc())
        



# start of program
if __name__ == "__main__":
    try:
        # start everything
        rpi_sub = AWSIoTMQTTClient("")
        rpi_sub.configureEndpoint(host, 8883)
        rpi_sub.configureCredentials(rootCAPath, sub_privateKeyPath, sub_certificatePath)

        rpi_sub.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        rpi_sub.configureDrainingFrequency(2)  # Draining: 2 Hz
        rpi_sub.configureConnectDisconnectTimeout(10)  # 10 sec
        rpi_sub.configureMQTTOperationTimeout(10)  # 10 sec
        
        rpi_sub.connect()

        rpi_pub = AWSIoTMQTTClient("")
        rpi_pub.configureEndpoint(host, 8883)
        rpi_pub.configureCredentials(rootCAPath, pub_privateKeyPath, pub_certificatePath)

        rpi_pub.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        rpi_pub.configureDrainingFrequency(2)  # Draining: 2 Hz
        rpi_pub.configureConnectDisconnectTimeout(10)  # 10 sec
        rpi_pub.configureMQTTOperationTimeout(10)  # 10 sec
        
        rpi_pub.connect()

        boto_sess = boto3.Session(region_name='us-east-1')
        if boto_sess:
            alert_sys.startup(boto_sess)
            s_temp.startup(boto_sess)
            s_ultrasonic.startup()
            s_water.startup()
            f_servo.startup(boto_sess)
        else:
            print('boto_sess null...')
            raise KeyboardInterrupt
    except:
        print(traceback.format_exc())
        sys.exit()
        
    try:
        # all started, continue to listen for mqtt stuff
        rpi_sub.subscribe("sensors/requests", 1, sendRequestedData)      # request data
        rpi_sub.subscribe("sensors/dispend", 1, f_servo.dispenseFood)    # manual food dispense
        rpi_sub.subscribe("settings/#", 1, updateSettings)               # settings changes
    except:
        print(traceback.format_exc())
        gpio.cleanup()
        sys.exit()
    
    # keep running...
    try:
        while True:
            continue
    except:
        gpio.cleanup()
        print("exit")
    
    """
    MQTT HERE...
    
    SUBSCRIBE FOR:
        - SETTINGS CHANGES              -> CALL: updateSettings( set=<name of setting>, data=<data of setting> )
        - DISPENSE FOOD BUTTON PRESS    -> CALL: f_servo.dispenseFood(1)
        - DATA TO SEND                  -> CALL: sendRequestedData( data_type=<food or water> )
        
    PUBLISH:
        ? TEMPERATURE DATA              -> CALL: s_temp.pollRealtimeData(),    returns float(?) or ""   [called by sendRequestedData]
        - FOOD LEVEL DATA               -> CALL: s_ultrasonic.getFoodLeft(),   returns int              [called by sendRequestedData]
        - WATER LEVEL DATA              -> CALL: s_water.getState(),           returns boolean          [called by sendRequestedData]
    """
