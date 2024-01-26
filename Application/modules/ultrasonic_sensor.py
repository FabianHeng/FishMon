#!/usr/bin/env python3

import RPi.GPIO as gpio
import sys
import time
#import mysql.connector
from datetime import datetime
import traceback

import random

base_dist = 13.7    # DEPENDS ON CONTAINER
recorded = False

foodWarnThreshold = 0

# define GPIO pins
TRIG = 20
ECHO = 21

def getFoodLeft():
    """
    exit_count = 0
    while True:
        try:
            gpio.output(TRIG, True)
            time.sleep(0.00001)
            gpio.output(TRIG, False)
 
            while gpio.input(ECHO)==0:
                pulse_start = time.time()

            while gpio.input(ECHO)==1:
                pulse_end = time.time()
            
            print("ultrasonic: done")
            break
        except:
            exit_count += 1
            if exit_count > 15:
                break
            print(traceback.format_exc())
            print("ultrasonic: retry")

    # calculate distance of sensor from surface
    pulse_duration = pulse_end - pulse_start
    dist = pulse_duration * 17150
    dist = round(dist, 2)
    
    # calculate percentage of food left in container
    percentage = round(((base_dist-dist) / base_dist) * 100)
    #print(percentage)
    """
    percentage = random.randrange(0,100)
    if percentage <= 0:
        return 0
    else:
        return percentage 

def startup():
    try:
        """
        gpio.setmode(gpio.BCM)
        gpio.setup(TRIG, gpio.OUT)
        gpio.setup(ECHO, gpio.IN)
        gpio.output(TRIG, False)
        """
        print("ultrasonic startup")
    except:
        print(traceback.format_exc())
        

