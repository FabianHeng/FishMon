import os
import glob
import time
from datetime import datetime
#import mysql.connector
import traceback
import json

import logging
import threading

import random

device_file = ""

# global settings
minTempThreshold = 0
maxTempThreshold = 0

f = None
dynamodbTable = None

def read_temp_raw(file):
    lines = file.readlines()
    file.seek(0)
    return lines

def read_temp(file):
    lines = read_temp_raw(file)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw(file)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return round(temp_c, 2)


# start thread that polls temp sensor every 10s
def startup(boto_sess):
    global device_file, f, dynamodbTable
    
    #logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')
    
    # UNCOMMENT TO USE WITH SENSOR
    """
    
    # probe for temperature sensor
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')

    # finding sensor's file
    base_dir = '/sys/bus/w1/devices/'
    device_folder = glob.glob(base_dir + '28*')[0]
    device_file = device_folder + '/w1_slave'
    """
    
    if not device_file == None:
        #f = open(device_file, 'r')
        
        # ADD DYNAMODB TABLE??? HERE (INSTANTIATE ONCE, RUN MULTIPLE TIMES)
        dynamodb = boto_sess.resource('dynamodb')
        dynamodbTable = dynamodb.Table('sensor_temp')
        
        # start thread
        t = threading.Thread(target=getDataConstant, name='t_pollTemp') #, daemon=True)
        t.daemon = True
        t.start()

    else:
        print("error reading temperature")

# Poll data once, no db involved
def pollRealtimeData():
    import random, decimal
    global device_file
    """
    if device_file == "":
        return ""
    else:
        with open(device_file, 'r') as f:
            curr_temp = read_temp(f)
    #data = { "time": datetime.now().strftime('%H:%M:%S'), "temp": read_temp_dbg() }
    """
    curr_temp = float(decimal.Decimal(random.randrange(150, 5000))/100)
    return curr_temp
    
# constantly poll data, involves db
def getDataConstant():
    import random
    import decimal
    
    global f
    logging.info("Temp sensor thread started!")
    """
    if device_file == "":
        logging.debug("Temp sensor thread stopped")
        raise FileNotFoundError
    """
    
    # ADD DYNAMODB HERE, ADD INTO DB CURR TEMP & DATE
    while True:
        d = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        curr_temp = float(decimal.Decimal(random.randrange(150, 500))/100)
        
        response = dynamodbTable.put_item(
            Item={
                'deviceid': 'raspberrypi',
                'date': d,
                'temperature': str(curr_temp)
            }
        )
        logging.info("UPDATED DB FOR TEMP with {0}@{1}".format(curr_temp, d))
        
        #message = {'deviceid': 'raspberrypi', 'date': d, 'temperature': curr_temp}
        #my_rpi.publish('sensors/temp', json.dumps(message), 1)
        time.sleep(5)
    
    
    
    
