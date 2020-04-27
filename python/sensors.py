#!/usr/bin/env python

# Sensor configuration...
SensorName = ["Temperature Probe", "CPU Temperature", "CPU Throttle", "CPU Throttle %"]
SensorType = ['T1w','CPU_Temp','Throttle_Status','Throttle_Level']
# 'Throttle_Status' = CPU Throttle status (Current throttle status)
# 'Throttle_Level' = CPU Throttle level (% time throttled)
# 'CPU_Temp' = CPU temperature
# 'T1w' = One-Wire Temperature Sensor 
# 'LM75' = LM75 I2C Temperature Sensor
# 'TPin' = Analogue Thermistor
# 'LDRPin' = Analogue Light Dependant Resistor
#SensorLoc = ['28-01191b9257fd','x','x','x']
SensorLoc = ['10-000801503137','x','x','x']
HighWarning = [125,125,125,125]
HighReset = [0,0,0,0]
LowWarning = [-25,-25,-25,-25]
LowReset = [0,0,0,0]
DomoticzIDX = ['8', 'x', 'x', 'x'] # Use 'x' to disable logging to Domoticz for each sensor

ActiveSensors = len(SensorName)

MeasurementInterval = 5

# Identify which sensor (if any) should be displayed to the local display
DisplaySensor1 = -1 # Set to -1 to disable display

