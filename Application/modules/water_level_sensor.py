#!/usr/bin/env python3
import time
import RPi.GPIO as gpio

IN_PIN = 25


def getState():
    #stat = gpio.input(IN_PIN)
    stat = True
    return stat
    

def startup():
    # set up in/out pins
    #gpio.setmode(gpio.BCM)
    # Set pin 11 as an output, and define servo1 as PWM pin
    #gpio.setup(IN_PIN, gpio.IN, pull_up_down=gpio.PUD_DOWN)
    print("start water level sensor")
