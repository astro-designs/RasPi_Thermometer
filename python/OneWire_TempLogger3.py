#!/usr/bin/env python

import time
from datetime import datetime
import LM75
import sys
import urllib
import urllib2
import requests
from microdotphat import write_string, set_decimal, clear, show
import os

# Import sensor configurations
import sensors

# Note - enable 1-wire interface using raspi-config
# Note - Once enabled, run (once):

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

# Define function to log data to Domoticz server...
def LogToDomoticz(idx, SensorVal):
	url = 'http://192.168.1.32:8085/json.htm?type=command&param=udevice&nvalue=0&idx='+idx+'&svalue='+str(SensorVal)
	try:
		request = urllib2.Request(url)
		response = urllib2.urlopen(request)
		print('Logged to Domoticz ' + idx)
	except urllib2.HTTPError, e:
		print e.code; time.sleep(60)
	except urllib2.URLError, e:
		print e.args; time.sleep(60)	

# Define function to log data...
def LogTemp(NextLogTime, logTitleString, logString, SensorVal):
	TimeNow = time.time()
	if TimeNow > NextLogTime:
		NextLogTime = NextLogTime + LogInterval
		# Log to webhook...
		#print("Logging Temperature to webhook...")
		#r = requests.post('https://maker.ifttt.com/trigger/RasPi_LogTemp/with/key/'+IFTTT_KEY, params={"value1":logTitleString,"value2":logString,"value3":"none"})
		
		print("Logging to Domoticz...")
		for x in range(0, ActiveSensors):
			if DomoticzIDX[x] != 'x':
				LogToDomoticz(DomoticzIDX[x], SensorVal[x])
		
	return NextLogTime
	
# Define function to display temperature on MicroDot Phat...
def DisplayTemp(NextDisplayTime, SensorVal, unitstr):
	TimeNow = time.time()
	if TimeNow > NextDisplayTime:
		NextDisplayTime = NextDisplayTime + DisplayInterval
		print("Displaying Temperature on MicroDot Phat...")
		write_string( "%.1f" % SensorVal + unitstr, kerning=False)
		show()

	return NextDisplayTime

# Define function to read one-wire temperature sensors...
def read_temp_T1w(SensorID):
    # Read one-wire device
    device_file = base_dir + SensorLoc[SensorID] + '/w1_slave'
    f = open(device_file, 'r')
    lines = f.readlines()

    # Extract temperature data
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = f.readlines()
    f.close()
	
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_c = round(temp_c,1)
        return temp_c

def read_temp_LM75(SensorID):
	clear()
	temp_raw = sensor.getTemp()
	if temp_raw > 128:
		temp_c = temp_raw - 256
	else:
		temp_c = temp_raw
	return temp_c

def read_temp_TPin(SensorID):
	temp = 22.2
	return temp_c
	
def read_temp(SensorID):
	if SensorType[SensorID] == 'T1w':
		temp_c = read_temp_T1w(SensorID)
	
	if SensorType[SensorID] == 'LM75':
		temp_c = read_temp_LM75(SensorID)
		
	if SensorType[SensorID] == 'TPin':
		temp_c = read_temp_TPin(SensorID)
	
	return temp_c
	
# Sensor configuration...
LogTitles = sensors.SensorName
SensorType = sensors.SensorType
SensorLoc = sensors.SensorLoc
TPins = sensors.SensorLoc
HighWarning = sensors.HighWarning
HighReset = sensors.HighReset
LowWarning = sensors.LowWarning
LowReset = sensors.LowReset
DomoticzIDX = sensors.DomoticzIDX
ActiveSensors = sensors.ActiveSensors
DisplaySensor1 = sensors.DisplaySensor1
MeasurementInterval = sensors.MeasurementInterval

Temperature = [0,0,0,0]
LowWarningIssued = [False, False, False, False]

# Default parameters
NumReadings = 0 # Set to 0 to log continuously
LogInterval = 30 # Set to 0 to disable logging
NumAverages = 1
DisplayInterval = 10 # Set to 0 to disable display

# 1-wire config...
if 'T1w' in SensorType:
	print("Using 1-Wire Temperature Sensor(s)")
	os.system('modprobe w1-gpio')
	os.system('modprobe w1-therm')
	base_dir = '/sys/bus/w1/devices/'

# LM75 config...
if 'LM75' in SensorType:
	print("Using LM75 Temperature Sensor(s)")
	sensor = LM75.LM75()

# Update LogTitlesString with description of all sensors...
logTitleString = ""
for x in range(0, ActiveSensors):
	logTitleString = logTitleString + LogTitles[x] + ";"
print (logTitleString)

############################################################
# Main program loop
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
	
	Reading = 0
	NextMeasurementTime = time.time()
	while Reading < NumReadings or NumReadings < 1:
		TimeNow = time.time()

		# Pause between measurements
		while TimeNow < NextMeasurementTime:
			time.sleep(0.2)
			TimeNow = time.time()

		NextMeasurementTime = NextMeasurementTime + MeasurementInterval

		# Reset average measurements
		for x in range(0, ActiveSensors):
			Temperature[x] = 0.0

		# Measurement loop
		for i in range (0, NumAverages):
			for x in range(0, ActiveSensors):
				Temperature[x] = Temperature[x] + read_temp(x)

		# Calculate average
		for x in range(0, ActiveSensors):
			Temperature[x] = Temperature[x] / NumAverages

		# Check for warnings...
		for x in range(0, ActiveSensors):
			# Check for low warning
			if Temperature[x] < LowWarning[x]:
				if LowWarningIssued[x] == False:
					# Issue Warning via IFTTT...
					#r = requests.post('https://maker.ifttt.com/trigger/Water_low_temp/with/key/' + IFTTT_KEY, params={"value1":"none","value2":"none","value3":"none"})
					LowWarningIssued[x] = True
			if Temperature[x] > LowReset[x]:
				LowWarningIssued[x] = False
			# Check for high warning
			if Temperature[x] > HighWarning[x]:
				if HighWarningIssued[x] == False:
					# Issue Warning via IFTTT...
					#r = requests.post('https://maker.ifttt.com/trigger/Water_low_temp/with/key/' + IFTTT_KEY, params={"value1":"none","value2":"none","value3":"none"})
					HighWarningIssued[x] = True
			if Temperature[x] < HighReset[x]:
				HighWarningIssued[x] = False

		# update logString with current temperature(s)
		logTime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(TimeNow))
		logString = logTime + ";" + str(Reading) + ";"
		for x in range(0, ActiveSensors):
			logString = logString + str(Temperature[x]) + ";"

		# Print the result
		print(logString)
		
		# Write to log...
		if LogInterval > 0:
			NextLogTime = LogTemp(NextLogTime, logTitleString, logString, Temperature)
		
		# Write to display...
		if DisplayInterval > 0 and DisplaySensor1 >= 0:
			NextDisplayTime = DisplayTemp(NextDisplayTime, Temperature[DisplaySensor1], "c ")
		
		# NumReadings countdown...
		if Reading < NumReadings:
			Reading = Reading + 1
		
# If you press CTRL+C, cleanup and stop
except KeyboardInterrupt:
	print("Keyboard Interrupt (ctrl-c) - exiting program loop")

finally:
	print("Closing data logger")

	
	
	
	
	
	