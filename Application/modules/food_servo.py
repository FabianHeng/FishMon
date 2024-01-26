import RPi.GPIO as gpio
#import mysql.connector
import time
from datetime import datetime
import threading
import logging

from modules.alert_system import addAlertsToDB

SERVO_PIN = 16

foodDispenseTimes = 0


def dispenseFood(num=None, client=None, userdata=None, message=None):
    if num:
        for c in range(0,num):
            gpio.output(SERVO_PIN, gpio.HIGH)
            time.sleep(0.5)
            gpio.output(SERVO_PIN, gpio.LOW)
            logging.debug("dispenseFood ran | count: {}".format(c))
            time.sleep(10)
    else:
        gpio.output(SERVO_PIN, gpio.HIGH)
        time.sleep(0.5)
        gpio.output(SERVO_PIN, gpio.LOW)
        addAlertsToDB([{"desc":"Food Dispenser Triggered by User", "type":"General"}])
        time.sleep(10)


def addAlertsToDB(alerts):
    global table
    print("add alerts to db")
    #d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # ADD DYNAMODB HERE, ALERTS TABLE
    for a in alerts:
        logging.info("FOR A IN ALERTS: ".format(a))
        d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        response = table.put_item(
            Item={
                'deviceid': 'raspberrypi',
                'details': a.get('desc'),
                'type': a.get('type'),
                'date': d
            }
        )
    logging.info("end of alert add")
    

def fixedTimeFoodDispense():
    global foodDispenseTimes
    fed = False
    logging.info("started food dispenser")
    while True:
        d = datetime.now().strftime('%H')
        if d == 10 and fed == False: # 10am feeding time
            dispenseFood(num=foodDispenseTimes)
            addAlertsToDB([{"desc":"Fishes Fed for {} number of times".format(foodDispenseTimes), "type":"General"}])
            fed = True
        else:
            fed = False
        time.sleep(3600) # 1h sleep

def debug():
    global foodDispenseTimes
    logging.debug("started food dispenser")
    while True:
        logging.debug("food dispenser - ran")
        dispenseFood(foodDispenseTimes)
        addAlertsToDB([{"desc":"Fishes Fed for {} number of times".format(foodDispenseTimes), "type":"General"}])
        time.sleep(10) # 1h sleep

def startup(boto_sess):
    global table
    dynamodb = boto_sess.resource('dynamodb')
    table = dynamodb.Table('alerts')
    gpio.setmode(gpio.BCM)
    gpio.setup(SERVO_PIN, gpio.OUT)
    t = threading.Thread(target=fixedTimeFoodDispense, name='t_feeder')
    t.daemon = True
    t.start()
