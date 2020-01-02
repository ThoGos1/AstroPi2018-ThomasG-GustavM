import logging
import logzero
from logzero import logger
from sense_hat import SenseHat
import ephem
from picamera import PiCamera
import datetime
from time import sleep
import random
import os
from PIL import Image
from PIL.ExifTags import TAGS

dir_path = os.path.dirname(os.path.realpath(__file__))

# Connect to the Sense Hat

sh = SenseHat()

# define some colours - keep brightness low

g = [0,50,0]
o = [0,0,0]

# define a simple image
img1 = [
    g,g,g,g,g,g,g,g,
    o,g,o,o,o,o,g,o,
    o,o,g,o,o,g,o,o,
    o,o,o,g,g,o,o,o,
    o,o,o,g,g,o,o,o,
    o,o,g,g,g,g,o,o,
    o,g,g,g,g,g,g,o,
    g,g,g,g,g,g,g,g,
]

# Set a logfile name
logzero.logfile(dir_path+"/data01.csv")

# Set a custom formatter
formatter = logging.Formatter('%(name)s - %(asctime)-15s - %(levelname)s: %(message)s');
logzero.formatter(formatter)

# Latest TLE data for ISS location
name = "ISS (ZARYA)"
l1 = "1 25544U 98067A   19032.30987313  .00001170  00000-0  25693-4 0  9997"
l2 = "2 25544  51.6429 316.9782 0004973 340.0425 166.5613 15.53214053154148"
iss = ephem.readtle(name, l1, l2)

# Set up camera
cam = PiCamera()
cam.resolution = (1296,972)

# function to write lat/long to EXIF data for photographs
def get_latlon():
    """
    A function to write lat/long to EXIF data for photographs
    """
    iss.compute() # Get the lat/long values from ephem
    long_value = [float(i) for i in str(iss.sublong).split(":")]
    if long_value[0] < 0:
        long_value[0] = abs(long_value[0])
        cam.exif_tags['GPS.GPSLongitudeRef'] = "W"
    else:
        cam.exif_tags['GPS.GPSLongitudeRef'] = "E"
    cam.exif_tags['GPS.GPSLongitude'] = '%d/1,%d/1,%d/10' % (long_value[0], long_value[1], long_value[2]*10)
    lat_value = [float(i) for i in str(iss.sublat).split(":")]
    if lat_value[0] < 0:
        lat_value[0] = abs(lat_value[0])
        cam.exif_tags['GPS.GPSLatitudeRef'] = "S"
    else:
        cam.exif_tags['GPS.GPSLatitudeRef'] = "N"
    cam.exif_tags['GPS.GPSLatitude'] = '%d/1,%d/1,%d/10' % (lat_value[0], lat_value[1], lat_value[2]*10)
    return(str(lat_value), str(long_value))

# define a function to update the LED matrix
def active_status():
    """
    A function to update the LED matrix regularly
    to show that the experiment is progressing
    """
    # a list with all possible rotation values
    orientation = [0,90,270,180]
    # pick one at random
    rot = random.choice(orientation)
    # set the rotation
    sh.set_rotation(rot)


# create a datetime variable to store the start time
start_time = datetime.datetime.now()
# create a datetime variable to store the current time
# (these will be almost the same at the start)
now_time = datetime.datetime.now()
# run a loop for 2 minutes
photo_counter = 1
sh.set_pixels(img1)
while (now_time < start_time + datetime.timedelta(minutes=1)):
    try:
        # Read some data from the Sense Hat, rounded to 4 decimal places
        temperature = round(sh.get_temperature(),4)
        humidity = round(sh.get_humidity(),4)


        # get latitude and longitude
        lat, lon = get_latlon()
        # Save the data to the file
        logger.info("%s,%s,%s,%s,%s", photo_counter,humidity, temperature, lat, lon )
        # use zfill to pad the integer value used in filename to 3 digits (e.g. 001, 002...)
        cam.capture(dir_path+"/photo_"+ str(photo_counter).zfill(3)+".jpg")
        (a,b)=Image.open(dir_path+"/photo_"+ str(photo_counter).zfill(3)+".jpg")._getexif()[37379] #BrightnessValue from exif data read from captured image
        if(a>9):  #Only if brightnessValue indicates daytime will the image be kept otherwise the image is overwritten with a new one - economizes memory use
            photo_counter+=1
        active_status()
        sleep(0.5)
        active_status()
        sleep(0.5)
        # update the current time
        now_time = datetime.datetime.now()
    except Exception as e:
        logger.error("An error occurred: " + str(e))

