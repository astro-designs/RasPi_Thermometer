#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
from datetime import datetime
import os
import sys
import math
import urllib
import urllib2
import requests

# IFTTT Key definition
# Save your IFTTT key to key.py
# or just define IFTTT_KEY somewhere inside this file
# example key.py:
# IFTTT_KEY = "randomstringofcharacters..."
from key import IFTTT_KEY

print("""RasPi 'analoguePi' TempLogger
By Mark Cantrill @AstroDesignsLtd
Monitors & logs temperature using a Thermistors resistance to control the discharge of a capacitor.
The time taken to discharge the capacitor is used to determine the resistance of the thermistor and the temperature is then derived from the resistance measurement.
So all you need is a Thermistor and a 10uF capacitor - no ADC is required!

Press Ctrl+C to exit.
""")


# How it works...

# Circuit:
# Connect a Thermistor between the chosen I/O pin and GND
# Connect a capacitor between the choses I/O pin and GND (across the Thermistor)

# Program function
# 1) Set I/O pin to output
# 2) Set I/O pin output to True (3.3V)
# 2a) Capacitor starts to charge up
# 3) Wait for a time to ensure capacitor is fully charged
# 4) Record system time (t1)
# 5) Set the pin to input
# 5a) Capacitor starts to discharge through the Thermistor which is wired across the capacitor. 
# 6) Wait until the I/O pin returns an input False
# 7) Record the system time. (t2)
# 8) Determine the time taken to discharge the capacitor (t2 - t1)
# 9) Calculate the resistance of the thermistor
# 10) Calculate the temperature of the thermistor
# 11) Repeat measurement a number of times and determine the average

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

# Set the GPIO modes
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define the sensors available...
LogTitles = ["HW Out", "HW Immersion", "HW Heating", "HW Thermostat"]
Temperature = [0,0,0,0]
TPins = [27, 15, 19, 20]
LowWarning = [0,0,0,0]
LowReset = [5,5,5,5]
DomoticzIDX = ['7', '11', '10', '9'] # Use 'x' to disable logging to Domoticz for each sensor
ActiveSensors = len(LogTitles)

LowWarningIssued = [False, False, False, False]

# Default parameters
NumReadings = 5
Interval = 5.0
NumAverages = 3
T_InitialCharge = 1.5
T_Pause = 0.5
T_Timeout = 3
Duration = [0,0,0,0]
SummedDuration = [0,0,0,0]
AverageDuration = [0,0,0,0]
Resistance = [0,0,0,0]
Temperature = [0,0,0,0]

############################################################
# GPIOpin Temperature Reader...

# Define GPIO pin to drive LED that flashes when reading is taken
# Set to 0 if there's no LED fitted
pinTestLED = 3

# Setup GPIO
for pin in TPins:
	GPIO.setup(pin, GPIO.OUT)
	GPIO.output(pin, False)

if pinTestLED > 0:
	GPIO.setup(pinTestLED, GPIO.OUT)
	GPIO.output(pinTestLED, False)


# Define some constants
V_Charge = 3.28
V_Threshold = V_Charge - 1.13
Capacitance = 0.0000104 # 10uF
T_Offset = -0.0005
LogFileName = "TLog"

# Thermistor constants for Steinhart-Hart equation
Thermistor_A = 0.001125308852122
Thermistor_B = 0.000234711863267
Thermistor_C = 0.000000085663516

try:

	if len(sys.argv) > 1:
		NumReadings = int(sys.argv[1])

	if len(sys.argv) > 2:
		Interval = float(sys.argv[2])

	if len(sys.argv) > 3:
		NumAverages = int(sys.argv[3])

	if NumReadings < 1:
		NumReadings = 9999
	
	#print NumReadings
	#print Interval
	#print NumAverages
	print("Temperature data logger running...")

	i = datetime.now()
	now = i.strftime('%Y%m%d-%H%M%S')
	LogFileName = LogFileName + "_" + now + '.csv'

	f = open(LogFileName, "a")

	BeginTime = time.time()
	logTime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(BeginTime))
	logString = logTime + ", " + "Logging Started"
	print(logString)
	logString = logString + "\r\n"
	f.write(logString)

	# Close the log file to ensure last reading is saved safely. (Helps to minimise loss of data if power fails)
	f.close()

	# Create LogTitlesString
	logTitleString = ""
	for x in range(0, ActiveSensors):
		logTitleString = logTitleString + LogTitles[x] + ";"
	print (logTitleString)
	
	for Reading in range (0, NumReadings):

		# Open file to append the next set of measurements...
		f = open(LogFileName, "a")
		
		# Reset time measurements
		for x in range(0, ActiveSensors):
			SummedDuration[x] = 0.0

		# Measurement loop
		for i in range (0, NumAverages):

			for pin in range(0, ActiveSensors):
				# Change the pin mode to output
				GPIO.setup(TPins[pin], GPIO.OUT)
				# Charge capacitor...
				GPIO.output(TPins[pin], True)

			if pinTestLED > 0:
				GPIO.output(pinTestLED, True)

			time.sleep (T_InitialCharge)

			#Start timer
			Timeout = False
			StartTime = time.time()
			
			# Change the pin mode to input
			for pin in range(0, ActiveSensors):
				GPIO.setup(TPins[pin], GPIO.IN)

			StopTime = time.time()
			MaxDuration = StopTime - StartTime
			# Wait for all measurements to be captured
			MeasurementsComplete = 0
			while MeasurementsComplete < ActiveSensors and MaxDuration < T_Timeout:
				MeasurementsComplete = 0
				StopTime = time.time()
				for x in range (0, ActiveSensors):
					if GPIO.input(TPins[x]) == 1:
						# Calculate fall time
						Duration[x] = StopTime - StartTime
					else:
						MeasurementsComplete = MeasurementsComplete + 1
				MaxDuration = StopTime - StartTime
			if pinTestLED > 0:
				GPIO.output(pinTestLED, False)
			if MaxDuration > T_Timeout:
				Timeout = True
				
			# Add result to any previous results
			for x in range(0, ActiveSensors):
				SummedDuration[x] = SummedDuration[x] + Duration[x]

		for x in range(0, ActiveSensors):
			# Calculate average
			AverageDuration[x] = SummedDuration[x] / NumAverages
			#print ("Discharge time: ", AverageDuration[x])

			Resistance[x] = -(AverageDuration[x] + T_Offset) / (Capacitance * math.log(1-V_Threshold/V_Charge))
			#Resistance[x] = round(Resistance[x],1)
			#print("Resistance: ", Resistance[x])

			Temperature[x] = 1.0/(Thermistor_A+(Thermistor_B*math.log(Resistance[x])) +(Thermistor_C*pow(math.log(Resistance[x]),3)))
			Temperature[x] = round(Temperature[x],3)
			Temperature[x] = Temperature[x] - 273.15

		logTime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(StartTime))

		if Timeout == False:
			# Log to file & print the result
			logString = logTime + ";" + str(Reading) + ";"
			for x in range(0, ActiveSensors):
				logString = logString + str(Temperature[x]) + ";"
				if Temperature[x] < LowWarning[x]:
					if LowWarningIssued[x] == False:
						#print ("Low Warning Issues: ", x)
						# Issue Warning
						r = requests.post('https://maker.ifttt.com/trigger/Water_low_temp/with/key/' + IFTTT_KEY, params={"value1":"none","value2":"none","value3":"none"})
						#print (r)
						LowWarningIssued[x] = True
				if Temperature[x] > LowReset[x]:
					LowWarningIssued[x] = False
			
				
				
				# Log to Domoticz...
				if DomoticzIDX[x] != 'x':
					LogToDomoticz(DomoticzIDX[x], Temperature[x])

			# Log to webhook...
			r = requests.post('https://maker.ifttt.com/trigger/RasPi_LogTemp/with/key/' + IFTTT_KEY, params={"value1":logTitleString,"value2":logString,"value3":"none"})

			# Print the result
			print(logString)
			# Log to file...
			logString = logString + "\r\n"
			f.write(logString)

		else:
			# Timeout - Modify the log data to indicate timeout has occured
			# Note - at the moment this modifies all sensor data but it should eventually only modify the ones that suffer a timeout
			logString = logTime + ", " + str(Reading)
			for x in range(0, ActiveSensors):
				logString = logString + ", " + "Timeout - check connections"

			# Print the result
			print(logString)
			# Log to file...
			logString = logString + "\r\n"
			f.write(logString)

		IntervalTime = time.time() - BeginTime
		while (IntervalTime < (Interval * (Reading+1))):
			IntervalTime = time.time() - BeginTime
		
		# Close the log file to ensure last reading is saved safely. (Helps to minimise loss of data if power fails)
		f.close()

	f = open(LogFileName, "a")
	f.write("Logging Finished" + "\r\n")
	f.close()

# If you press CTRL+C, cleanup and stop
except KeyboardInterrupt:
	print("Keyboard Interrupt (ctrl-c) - exiting program loop")
	f.close()

finally:
	print("Closing data logger")
	GPIO.cleanup()
