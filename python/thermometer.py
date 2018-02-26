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

while True:
    clear()
    temp_raw = sensor.getTemp()
    temp = temp_raw
    if temp > 128:
        temp = temp - 256
    print temp
    write_string( "%.1f" % temp + " c", kerning=False)
    show()
    time.sleep(delay)
