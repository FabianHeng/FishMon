import boto3
import botocore
from picamera import PiCamera
from time import sleep
import json
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

# Set the filename and bucket name
BUCKET = 'rekognition-blutangclan' # replace with your own unique bucket name
location = {'LocationConstraint': 'us-east-1'}
file_path = "/home/pi/Desktop"
file_name = "pic.jpg"

# Custom MQTT message callback
def customCallback(client, userdata, message):
	print("Received a new message: ")
	print(message.payload)
	print("from topic: ")
	print(message.topic)
	print("--------------\n\n")

host = ""
rootCAPath = "certs/rootca.pem"

pub_certificatePath = "certs/pub/certificate.pem.crt"
pub_privateKeyPath = "certs/pub/private.pem.key"

sub_certificatePath = "certs/sub/certificate.pem.crt"
sub_privateKeyPath = "certs/sub/private.pem.key"

my_rpi_sub = AWSIoTMQTTClient("")
my_rpi_sub.configureEndpoint(host, 8883)
my_rpi_sub.configureCredentials(rootCAPath, sub_privateKeyPath, sub_certificatePath)

my_rpi_sub.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
my_rpi_sub.configureDrainingFrequency(2)  # Draining: 2 Hz
my_rpi_sub.configureConnectDisconnectTimeout(10)  # 10 sec
my_rpi_sub.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
my_rpi_sub.connect()
my_rpi_sub.subscribe("sensors/rekognition", 1, customCallback)
sleep(2)

my_rpi_pub = AWSIoTMQTTClient("")
my_rpi_pub.configureEndpoint(host, 8883)
my_rpi_pub.configureCredentials(rootCAPath, pub_privateKeyPath, pub_certificatePath)

my_rpi_pub.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
my_rpi_pub.configureDrainingFrequency(2)  # Draining: 2 Hz
my_rpi_pub.configureConnectDisconnectTimeout(10)  # 10 sec
my_rpi_pub.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
my_rpi_pub.connect()

def takePhoto(file_path,file_name):
    with PiCamera() as camera:
        #camera.resolution = (1024, 768)
        full_path = file_path + "/" + file_name
        camera.capture(full_path)
        sleep(1)

def uploadToS3(file_path,file_name, bucket_name,location):
    s3 = boto3.resource('s3') # Create an S3 resource
    exists = True

    try:
        s3.meta.client.head_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            exists = False

    if exists == False:
        s3.create_bucket(Bucket=bucket_name,CreateBucketConfiguration=location)
    
    # Upload the file
    full_path = file_path + "/" + file_name
    s3.Object(bucket_name, file_name).put(Body=open(full_path, 'rb'))
    print("File uploaded")


def detect_labels(bucket, key, max_labels=10, min_confidence=90, region="us-east-1"):
	rekognition = boto3.client("rekognition", region)
	response = rekognition.detect_labels(
		Image={
			"S3Object": {
				"Bucket": bucket,
				"Name": key,
			}
		},
		MaxLabels=max_labels,
		MinConfidence=min_confidence,
	)
	print("Detected labels for " + key)
	print("")
	return response['Labels']

while True:
    takePhoto(file_path, file_name)
    uploadToS3(file_path,file_name, BUCKET,location)

    fishBreed = []
    confidence = []

    for label in detect_labels(BUCKET, file_name):
        for parent in label['Parents']:
            if (parent['Name'] == "Fish"):
                print ("Label: " + label['Name'])
                print ("Confidence: " + str(label['Confidence']))
                print ("----------")
                fishBreed.append(str(label['Name']))
                confidence.append(round(label['Confidence']))

    if (fishBreed):
        msg = "Don't know what your fishes' breeds are? By running thorugh AI, we will help you determine what type of fish you have! The breed(s) of your fish: " + fishBreed[0] + " (" + str(confidence[0]) + "%) "
        for i in range(1, len(fishBreed)):
            msg += "/ " + fishBreed[i] + " (" + str(confidence[i]) + "%) "
    else:
        msg = "Don't know what your fishes' breeds are? By running thorugh AI, we will help you determine what type of fish you have! Cannot determine the breed of your fish, please try again."
    
    my_rpi_pub.publish("sensors/rekognition", msg, 1)
    sleep(5)

