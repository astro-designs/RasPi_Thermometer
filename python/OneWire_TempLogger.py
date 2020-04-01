#!/usr/bin/env python

import time
from datetime import datetime
#import LM75
import sys
import urllib
import urllib2
import requests
from microdotphat import write_string, set_decimal, clear, show
import os
import glob

# Note - enable 1-wire interface using raspi-config
# Note - Once enabled, run (once):
# sudo modprobe w1–gpio
# sudo modprobe w1-therm

# IFTTT Key definition
# Save your IFTTT key to key.py
# or just define IFTTT_KEY somewhere inside this file
# example key.py:
# IFTTT_KEY = "randomstringofcharacters..."
from key import IFTTT_KEY

print("""RasPi Temperature Sensor
By Mark Cantrill @AstroDesignsLtd
Measure and logs temperature from external DS18B20 1-wire temperature sensor
Logs the data to Domoticz server
Issues a warning to IFTTT 

Press Ctrl+C to exit.
""")

def LogToDomoticz(idx, SensorVal):
	url = 'http://192.168.1.32:8085/json.htm?type=command&param=udevice&nvalue=0&idx='+idx+'&svalue='+str(SensorVal)
	try:
		request = urllib2.Request(url)
		response = urllib2.urlopen(request)
		print("Logged to Domoticz")
	except urllib2.HTTPError, e:
		print e.code; time.sleep(60)
	except urllib2.URLError, e:
		print e.args; time.sleep(60)	

def LogTemp(NextLogTime, logTitleString, logString, SensorVal):
	TimeNow = time.time()
	if TimeNow > NextLogTime:
		NextLogTime = NextLogTime + LogInterval
		# Log to webhook...
		print("Logging Temperature to webhook...")
		r = requests.post('https://maker.ifttt.com/trigger/RasPi_LogTemp/with/key/'+IFTTT_KEY, params={"value1":logTitleString,"value2":logString,"value3":"none"})
		
		print("Logging Temperature to Domoticz...")
		LogToDomoticz(DomoticzIDX[0], SensorVal)
		
	return NextLogTime
	
def DisplayTemp(NextDisplayTime, SensorVal, unitstr):
	TimeNow = time.time()
	if TimeNow > NextDisplayTime:
		NextDisplayTime = NextDisplayTime + DisplayInterval
		print("Displaying Temperature on MicroDot Phat...")
		write_string( "%.1f" % SensorVal + unitstr, kerning=False)
		show()

	return NextDisplayTime

# 1-wire config...
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
 
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

def read_temp_1w():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines
 
def read_temp():
    lines = read_temp_1w()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_1w()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c

	
# Define the sensors available...
LogTitles = ["TemperatureProbe"]
Temperature = [0]
LowWarning = [15]
LowReset = [17]
LowWarningIssued = [False]
DomoticzIDX = ['31'] # Use 'x' to disable logging to Domoticz for each sensor
ActiveSensors = len(LogTitles)

# Default parameters
NumReadings = 99999
LogInterval = 5 # Set to 0 to disable logging
NumAverages = 1
DisplayInterval = 5 # Set to 0 to disable display
MeasurementPause = 1

############################################################
# LM75 Temperature Reader...

# Initialisation...
temp = read_temp()

max_temp = temp
min_temp = temp

disp = 0

# Update LogTitlesString with description of all sensors...
logTitleString = ""
for x in range(0, ActiveSensors):
	logTitleString = logTitleString + LogTitles[x] + ";"
print (logTitleString)

try:
	
	if len(sys.argv) > 1:
		NumReadings = int(sys.argv[1])

	if len(sys.argv) > 2:
		LogInterval = float(sys.argv[2])

	if len(sys.argv) > 3:
		NumAverages = int(sys.argv[3])

	if NumReadings < 1:
		NumReadings = 9999	

	#print("NumReadings: ", NumReadings)
	#print("LogInterval: ", LogInterval)
	#print("NumAverages: ", NumAverages)
	print("Temperature data logger running...")

	# Set first LogTime
	NextLogTime = time.time() + LogInterval
	NextDisplayTime = time.time() + DisplayInterval
	
	while True:
		TimeNow = time.time()
		Temperature[0] = read_temp()

		if Temperature[0] > max_temp:
			max_temp = Temperature[0]
		if Temperature[0] < min_temp:
			min_temp = Temperature[0]
		
		# Just print things...
		print(Temperature[0])
		
		# update logString with current temperature(s)
		logTime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(TimeNow))
		logString = logTime + ";" + str(0) + ";" + str(Temperature[0]) + ";"

		# Write to log...
		if LogInterval > 0:
			NextLogTime = LogTemp(NextLogTime, logTitleString, logString, Temperature[0])
		
		# Write to display...
		if DisplayInterval > 0:
			NextDisplayTime = DisplayTemp(NextDisplayTime, Temperature[0], "c ")
		
		# Optionally display a min / max reading...
		#disp = disp + 1
		#if disp > 9:
		#	disp = 0
	       
		#if disp == 8: # Display lowest recorded temperature
		#	DisplayTemp(min_temp, "cL")
		#elif disp == 9: # Display highest recorded temperature
		#	DisplayTemp(max_temp, "cH")
		#else: # Display current temperature
		#	DisplayTemp(Temperature[0], "c ")

		# Pause between measurements
		time.sleep(MeasurementPause)

# If you press CTRL+C, cleanup and stop
except KeyboardInterrupt:
	print("Keyboard Interrupt (ctrl-c) - exiting program loop")
	write_string( "Exit", kerning=False)
	show()

finally:
	print("Closing data logger")

	
	
	
	
	
	