#!/usr/bin/env python

import logging
import time
from datetime import datetime
import LM75
import sys
import urllib
import urllib2
import requests
from microdotphat import write_string, set_decimal, clear, show
import os
import subprocess
from gpiozero import CPUTemperature

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

import argparse

parser = argparse.ArgumentParser(description='Simple Domoticz data logger')

parser.add_argument('-ip', action='store', dest='IP_Address', default='192.168.1.32',
                    help='IP Address of Domoticz server (e.g. 192.168.1.32)')

parser.add_argument('-port', action='store', dest='port', default='8085',
                    help='Domoticz listening port (e.g. 8085')

parser.add_argument('-NumReadings', action='store', dest='NumReadings', default=0,
                    help='Number of readings to log')

parser.add_argument('-LogInterval', action='store', dest='LogInterval', default=30,
                    help='Log interval in seconds (e.g. 30)')

parser.add_argument('-NumAverages', action='store', dest='NumAverages', default=1,
                    help='Number of readings to average')

parser.add_argument('-DisplayInterval', action='store', dest='DisplayInterval', default=10,
                    help='Display interval in seconds (e.g. 30)')

arguments = parser.parse_args()

# Read arguments...
IP_Address = arguments.IP_Address
port = arguments.port
NumReadings = int(arguments.NumReadings)
LogInterval = int(arguments.LogInterval)
NumAverages = int(arguments.NumAverages)
DisplayInterval = int(arguments.DisplayInterval)

# Setup Log to file function
timestr = 'logs/' + time.strftime("%B-%dth--%I-%M-%S%p") + '.log'
logger = logging.getLogger('myapp')
hdlr = logging.FileHandler(timestr)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)

# Miscelaneous definitions
GET_THROTTLED_CMD = 'vcgencmd get_throttled'
throttle_uv = 0
throttle_uv_level = 0
throttle_readings = 0
throttle_uv_num = 0

print("""RasPi Multi-Function Data Monitor / Logger
By Mark Cantrill @AstroDesignsLtd
Measure and logs temperature from external DS18B20 1-wire temperature sensor or LM75
Logs the data to Domoticz server
Optionally displays data on a MicroDot pHAT
Can optionally issues a warning to IFTTT 

Press Ctrl+C to exit.
""")

logger.info('Starting Logger...')

# Define function to log data to Domoticz server...
def LogToDomoticz(idx, SensorVal):
	url = 'http://' + IP_Address + ':' + port + '/json.htm?type=command&param=udevice&nvalue=0&idx='+idx+'&svalue='+str(SensorVal)
	try:
		request = urllib2.Request(url)
		response = urllib2.urlopen(request)
		print('Logged ' + str(SensorVal) + ' to Domoticz ID ' + idx)
	except urllib2.HTTPError, e:
		logger.info(e.code)
		print e.code;
	except urllib2.URLError, e:
		logger.info(e.args)
		print e.args;


# Define a function to monitor the throttle status...
def ThrottleMonitor():
	global throttle_readings, throttle_uv_num, throttle_uv, throttle_uv_level
	throttle_output = subprocess.check_output(GET_THROTTLED_CMD, shell=True)
	throttle_status = int(throttle_output.split('=')[1], 0)
	throttle_readings = throttle_readings + 1
	if throttle_status & 1:
		throttle_uv = 1
		throttle_uv_num = throttle_uv_num + 1
		throttle_uv_level = round(100 * (throttle_uv_num / throttle_readings),0)
	else:
		throttle_uv = 0
		throttle_uv_num = max(0, throttle_uv_num - 1)
		throttle_uv_level = round(100 * (throttle_uv_num / throttle_readings),0)


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

def read_temp_CPU():
	measurement = CPUTemperature()
	return measurement

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

    # Format temperature data
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        measurement = float(temp_string) / 1000.0
        measurement = round(measurement,1)
        return measurement

def read_temp_LM75(SensorID):
	clear()
	temp_raw = sensor.getTemp()
	if temp_raw > 128:
		measurement = temp_raw - 256
	else:
		measurement = temp_raw
	return measurement

def read_temp_TPin(SensorID):
	measurement = 22.2
	return measurement

def read_Trig(SensorID):
	measurement = 100
	return measurement

def read_throttle(Mode = 0):
	if Mode == 0: # Check status of under-voltage detection
		measurement = throttle_uv

	elif Mode == 1: # Check level of throttle
		measurement = throttle_uv_level

	else: # Any unsupported mode...
		measurement = -999

	return measurement


def read_temp(SensorID):
	measurement = -999

	if SensorType[SensorID] == 'CPU_Temp':
		cpu = read_temp_CPU()
		measurement = cpu.temperature

	if SensorType[SensorID] == 'T1w':
		measurement = read_temp_T1w(SensorID)

	if SensorType[SensorID] == 'LM75':
		measurement = read_temp_LM75(SensorID)

	if SensorType[SensorID] == 'TPin':
		measurement = read_temp_TPin(SensorID)

	if SensorType[SensorID] == 'Throttle_Level':
		measurement = read_throttle(1)

	if SensorType[SensorID] == 'Throttle_Status':
		measurement = read_throttle(0)

	return measurement


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

# TrigN config...
if 'TrigN' in SensorType:
	print("Using Negative-Edge trigger on pin")
	
	
# Update LogTitlesString with description of all sensors...
logTitleString = ""
for x in range(0, ActiveSensors):
	logTitleString = logTitleString + LogTitles[x] + ";"
print (logTitleString)

############################################################
# Main program loop
try:
	
	print("Number of Readings: ", NumReadings)
	print("Number of Averages: ", NumAverages)
	print("Measurement Interval: ", MeasurementInterval)
	print("Log Interval: ", LogInterval)
	print("Display Interval: ", DisplayInterval)
	print("Temperature data logger running...")

	# Set first LogTime
	NextLogTime = time.time() + LogInterval
	
	# Set first DisplayTime
	NextDisplayTime = time.time() + DisplayInterval
	
	# Set first MeasurementTime
	NextMeasurementTime = time.time()
	
	# First reading...
	Reading = 0
	
	while Reading < NumReadings or NumReadings < 1:
		TimeNow = time.time()
		
		# Pause between measurements
		while TimeNow < NextMeasurementTime:
			# Check CPU throttle status while waiting...
			print ("Reading throttle...")
			ThrottleMonitor()
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
					logger.info('Low temperature warning')
					# Issue Warning via IFTTT...
					#r = requests.post('https://maker.ifttt.com/trigger/Water_low_temp/with/key/' + IFTTT_KEY, params={"value1":"none","value2":"none","value3":"none"})
					LowWarningIssued[x] = True
			if Temperature[x] > LowReset[x]:
				LowWarningIssued[x] = False
			# Check for high warning
			if Temperature[x] > HighWarning[x]:
				if HighWarningIssued[x] == False:
					logger.info('High temperature warning')
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
	
	logger.info('Logging completed.')
	
# If you press CTRL+C, cleanup and stop
except KeyboardInterrupt:
	logger.info('Keyboard Interrupt (ctrl-c) detected - exiting program loop')
	print("Keyboard Interrupt (ctrl-c) detected - exiting program loop")

finally:
	logger.info('Closing data logger')
	print("Closing data logger")

	
	
	
	
	
	
