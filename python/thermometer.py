#!/usr/bin/env python

import datetime
import time
import LM75
import sys
import requests

from microdotphat import write_string, set_decimal, clear, show

# IFTTT Key definition
# Save your IFTTT key to key.py
# or just define IFTTT_KEY somewhere inside this file
# example key.py:
# IFTTT_KEY = "randomstringofcharacters..."
from key import IFTTT_KEY

print("""RasPi Temperature Sensor
By Mark Cantrill @AstroDesignsLtd
Displays the temperature measured from external LM75 temperature sensor
Using the Pimoroni Microdot Phat for the display device

Press Ctrl+C to exit.
""")

# Define the delay between each reading
delay = 1

# Define the sensors available...
ActiveSensors = 1
LogTitles = ["Kitchen"]
LowWarning = [15]
LowReset = [17]
LowWarningIssued = [False]
Temperature = [0]
NumReadings = 5

# Define log interval, the number of seconds between logs
LogInterval = 300

def LogTemp(NextLogTime, logTitleString, logString):
	print("Logging Temperature to webhook...")
	TimeNow = time.time()
	if TimeNow > NextLogTime:
		NextLogTime = NextLogTime + LogInterval
		# Log to webhook...
		print(logTitleString + logString)
		r = requests.post('https://maker.ifttt.com/trigger/RasPi_LogTemp/with/key/'+IFTTT_KEY, params={"value1":logTitleString,"value2":logString,"value3":"none"})
	return NextLogTime

	
def DisplayTemp(temp, unitstr):
	print("Displaying Temperature on MicroDot Phat...")
	write_string( "%.1f" % temp + unitstr, kerning=False)
	show()

# Initialisation...
sensor = LM75.LM75()

clear()
temp_raw = sensor.getTemp()
temp = temp_raw
if temp > 128:
    temp = temp - 256

max_temp = temp
min_temp = temp

disp = 0

# Update LogTitlesString with description of all sensors...
logTitleString = ""
for x in range(0, ActiveSensors):
	logTitleString = logTitleString + LogTitles[x] + ";"
print (logTitleString)

# Set first LogTime
NextLogTime = time.time() + LogInterval

try:

	#r = requests.post('https://maker.ifttt.com/trigger/RasPi_Reboot/with/key/bPMigJxx44GrgeZkjHFu7m', params={"value1":"none","value2":"none","value3":"none"})
	#print ("Sending reboot message")
	#print (r)
	
	if len(sys.argv) > 1:
		NumReadings = int(sys.argv[1])

	if len(sys.argv) > 2:
		Interval = float(sys.argv[2])

	if len(sys.argv) > 3:
		NumAverages = int(sys.argv[3])

	if NumReadings < 1:
		NumReadings = 9999	

	while True:
		TimeNow = time.time()
		clear()
		temp_raw = sensor.getTemp()
		Temperature[0] = temp_raw
		if Temperature[0] > 128:
			Temperature[0] = Temperature[0] - 256

		if Temperature[0] > max_temp:
			max_temp = Temperature[0]
		if Temperature[0] < min_temp:
			min_temp = Temperature[0]
		
		# Just print things...
		print(Temperature[0])
		
		# update logString with current temperature(s)
		logTime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(TimeNow))
		logString = logTime + ";" + str(0) + ";" + str(Temperature[0]) + ";"

		# Check to see if a new log is due to be sent and write to log if it's time...
		NextLogTime = LogTemp(NextLogTime, logTitleString, logString)
		
		disp = disp + 1
		if disp > 9:
			disp = 0
	       
		if disp == 8: # Display lowest recorded temperature
			DisplayTemp(min_temp, "cL")
		elif disp == 9: # Display highest recorded temperature
			DisplayTemp(max_temp, "cH")
		else: # Display current temperature
			DisplayTemp(Temperature[0], "c ")

		time.sleep(delay)

# If you press CTRL+C, cleanup and stop
except KeyboardInterrupt:
	write_string( "Exit", kerning=False)
	show()
