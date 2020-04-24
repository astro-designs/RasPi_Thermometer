#!/usr/bin/env python

import urllib
import urllib2
import argparse

parser = argparse.ArgumentParser(description='Simple Domoticz data logger')

parser.add_argument('-ip', action='store', dest='IP_Address', default='192.168.1.32',
                    help='IP Address (e.g. 192.168.1.32)')

parser.add_argument('-port', action='store', dest='port', default='8085',
                    help='Domoticz listening port (e.g. 8085')

parser.add_argument('-idx', action='store', dest='idx', default=0,
                    help='Domoticz idx (e.g. 8)')

parser.add_argument('-val', action='store', dest='SensorVal', default=0,
                    help='Value to log (e.g. 20.3)')

results = parser.parse_args()

IP_Address = results.IP_Address
port = results.port
idx = results.idx
SensorVal = results.SensorVal
	
# Define function to log data to Domoticz server...
def LogToDomoticz(idx, SensorVal):
	url = 'http://' + IP_Address + ':' + port + '/json.htm?type=command&param=udevice&nvalue=0&idx='+idx+'&svalue='+str(SensorVal)
	try:
		request = urllib2.Request(url)
		response = urllib2.urlopen(request)
		print('Logged ' + SensorVal + ' to Domoticz ID ' + idx)
	except urllib2.HTTPError, e:
		print e.code; #time.sleep(60)
	except urllib2.URLError, e:
		print e.args; #time.sleep(60)	

############################################################
# Main program loop

if idx > 0:
	LogToDomoticz(idx, SensorVal)
else:
	print("Missing or invalid idx")
