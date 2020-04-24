#!/usr/bin/env python

# Sensor configuration...
SensorName = ["Kitchen"]
SensorType = ['LM75','x','x','x']
# 'T1w' = One-Wire Temperature Sensor 
# 'LM75' = LM75 I2C Temperature Sensor
# 'TPin' = Analogue Thermistor
# 'LDRPin' = Analogue Light Dependant Resistor
SensorLoc = ['0','x','x','x']
HighWarning = [125,125,125,125]
HighReset = [0,0,0,0]
LowWarning = [-25,-25,-25,-25]
LowReset = [0,0,0,0]
DomoticzIDX = ['x', 'x', 'x', 'x'] # Use 'x' to disable logging to Domoticz for each sensor

ActiveSensors = len(SensorName)

MeasurementInterval = 5

# Identify which sensor (if any) should be displayed to the local display
DisplaySensor1 = 0 # Set to -1 to disable display

