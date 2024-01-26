## How to run Flask Web Application on EC2 Instance
1. Start a Ubuntu Server EC2 Instance (AWS Linux not supported by Kinesis)
2. Install prerequisites `Website/requirements.txt`
3. Add credentials into the `~/.aws/credentials` file
4. Create 2 IOT Things in AWS (for publisher and subscriber)
5. Place their certificates in the Website/certs folder
  * certs/rootca.pem 
  * certs/pub/private.key.pem     (publisher thing's key)
  * certs/pub/certificate.pem.crt (publisher thing's key)
  * certs/sub/private.key.pem     (subscriber thing's key)
  * certs/sub/certificate.pem.crt (subscriber thing's key)
6. Add the IOT endpoint into `Website/app/__init__.py` and `Website/app/home/routes.py` 
7. Change directory to the `Website/` folder
8. Run `run.py` with python3

## How to run application on Raspberry Pi
1. Install Debian 10 version of Raspian OS (required for Kinesis Video Streaming)
2. Build from source the following [product](https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp)
3. Install python3 prerequisites from `Application/requirements.txt` file
4. Add credentials into the `~/.aws/credentials` file
5. Place their certificates in the `Application/certs` folder
  * certs/rootca.pem
  * certs/pub/private.key.pem     (publisher thing's key)
  * certs/pub/certificate.pem.crt (publisher thing's key)
  * certs/sub/private.key.pem     (subscriber thing's key)
  * certs/sub/certificate.pem.crt (subscriber thing's key)
6. Add the IOT endpoint into `modules/alert_system.py` and `main.py` files (host="<endpoint>")
7. Create a new file `credentials_file` with aws credentials in the format: 
    `CREDENTIALS <access_key> <expiry_datetime> <secret_key> <token>`
8. Change directory to the `Application/` folder
9. Run `main.py` with python3
10. Setup another Raspberry Pi with a camera installed
11. Run `camera_rekognition.py` with python3 on the Raspberry Pi
