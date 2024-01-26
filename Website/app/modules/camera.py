# -*- encoding: utf-8 -*-

import cv2
import threading
import logging
import datetime
import time
import io

import imageio
import boto3
import pika
import traceback

camThread = None
camThreadLock = None
outputFrame = None
boto_sess = None

class CameraThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        global boto_sess 
        super(CameraThread, self).__init__(*args, **kwargs) 
        self._stop = threading.Event()
        kvs_client = boto_sess.client('kinesisvideo')
        kvs_endpoint = kvs_client.get_data_endpoint(
            StreamARN='arn:aws:kinesisvideo:us-east-1:607151056550:stream/iot-stream/1613563896139',
            APIName='GET_MEDIA'
        )
        endpoint_url = kvs_endpoint['DataEndpoint']
        # Get video fragment from KVS
        self.media_client = boto_sess.client('kinesis-video-media', endpoint_url=endpoint_url)

    # function using _stop function 
    def stop(self): 
        self._stop.set()
  
    def stopped(self): 
        return self._stop.isSet() 
    
    def get_fragment(self):
        # start_time = timeit.default_timer()
        fragment = self.media_client.get_media(StreamARN='arn:aws:kinesisvideo:us-east-1:607151056550:stream/iot-stream/1613563896139', StartSelector={'StartSelectorType': 'NOW'})
        print(f'Downloading one chunk took: {timeit.default_timer() - start_time}')
        print('Fragment downloaded')
        return fragment
    
    def read_chunk(self, fragment):
        chunk = fragment['Payload'].read(1024*8*8)
        print("Chunk read")
        return chunk
    
    def get_frame(self, chunk):
        try:
            #print("CHUNK TYPE: " + str(type(chunk)))
            #print("CHUNK TYPE: " + str(type(io.BytesIO(chunk))))
            fragment = imageio.get_reader(io.BytesIO(chunk)) #, 'ffmpeg')
            
            for num , im in enumerate(fragment):
                print(num)
                if num % 30 == 0:
                    sts = 0
                    print("Frame captured")
                    break
            print("Returning result")
            return im, sts
            # print(f'Finish one chunk took: {timeit.default_timer() - start_time}')
        except:
            print("Broken fragment received")
            print(traceback.format_exc())
            sts = 1
            return None, sts

    
    def run(self): 
        global outputFrame, camThreadLock
        logging.debug("detectMotion started")
        try:
            counter = 0
            while True:
                print("WHILE TRUE LOOP COUNTER FOR RUN" + str(counter)) 
                #start_time = timeit.default_timer()
                fragment = self.get_fragment()
                chunk = self.read_chunk(fragment)
                im, sts = self.get_frame(chunk)
                if sts != 0:
                    time.sleep(0.25)
                    continue
                #print(f'Time between fragment download and frame processing: {timeit.default_timer() - start_time}')
                
                # acquire the lock, set the output frame, and release the
                # lock
                with camThreadLock:
                    outputFrame = im
        except:
            logging.debug(traceback.format_exc())
            logging.debug("exit thread")
            #camThreadLock.release()

def generate():
    # grab global references to the output frame and lock variables
    global outputFrame, camThreadLock
    # loop over frames from the output stream
    logging.debug("while true generate section")
    while True:
        # wait until the lock is acquired
        with camThreadLock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if outputFrame is None:
                continue
            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
            # ensure the frame was successfully encoded
            if not flag:
                continue
        # yield the output frame in the byte format
        yield str(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

def startup(bs):
    global camThread, camThreadLock, boto_sess
    print("start camera stuff")
    """
    kvs_client = boto3.client('kinesisvideo')
    kvs_endpoint = kvs_client.get_data_endpoint(
        StreamARN='',
        APIName='GET_MEDIA'
    )
    endpoint_url = kvs_endpoint['DataEndpoint']
    # Get video fragment from KVS
    media_client = boto3.client('kinesis-video-media', endpoint_url=endpoint_url)
    """
    time.sleep(2)
    print(type(bs))
    boto_sess = bs
    camThread = CameraThread()
    camThread.daemon = True
    camThread.start()
    print('Camera Thread started')


def shutdown():
    global camThread, camThreadLock
    print("Stop camera stuff")
    time.sleep(2)
    camThread.stop()
    camThread.join()
    print('Camera Thread stopped')
