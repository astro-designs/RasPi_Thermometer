#!/usr/bin/env python

import datetime
import time
import LM75

from microdotphat import write_string, set_decimal, clear, show


print("""Thermal

Displays the temperature measured from external LM75 temperature sensor

Press Ctrl+C to exit.
""")

delay = 1
sensor = LM75.LM75()

clear()
temp_raw = sensor.getTemp()
temp = temp_raw
if temp > 128:
    temp = temp - 256

max_temp = temp
min_temp = temp

disp = 0

try:
	while True:
	    clear()
	    temp_raw = sensor.getTemp()
	    temp = temp_raw
	    if temp > 128:
	        temp = temp - 256
	    print temp

	    if temp > max_temp:
	        max_temp = temp
	    if temp < min_temp:
	        min_temp = temp
	        
	    disp = disp + 1
	    if disp > 9:
	       disp = 0
	       
	    if disp == 8: # Display Min
	       write_string( "%.1f" % min_temp + "cL", kerning=False)
	    elif disp == 9: # Display Max
	       write_string( "%.1f" % max_temp + "cH", kerning=False)
	    else:
	       write_string( "%.1f" % temp + "c ", kerning=False)

	    show()
	    time.sleep(delay)

# If you press CTRL+C, cleanup and stop
except KeyboardInterrupt:
	    write_string( "Exit", kerning=False)
	    show()
