# lcdtest.py Demo/test program for MicroPython scheduler with attached LCD display
# Author: Peter Hinch
# V1.0 21st Aug 2014
# Display must use the Hitachi HD44780 controller. This demo assumes a 16*2 character unit.

import pyb
from usched import Sched, Timeout
from usched import micros                                   # For microsecond display
from lcdthread import LCD, PINLIST                          # Library supporting Hitachi LCD module

# HARDWARE
# Micropython board with LCD attached using the 4-wire data interface. See lcdthread.py for the
# default pinout. If yours is wired differently, declare a pinlist as per the details in lcdthread
# and instantiate the LCD using that list.

# THREADS:

def stop(fTim, objSch):                                     # Stop the scheduler after fTim seconds
    yield Timeout(fTim)
    objSch.stop()


def lcd_thread(mylcd):
    mylcd[0] = "MicroPython"
    while True:
        mylcd[1] = "{:10d}uS".format(micros.counter())
        yield Timeout(1)

# USER TEST PROGRAM
# Runs forever unless you pass a number of seconds

def lcdtest(duration = 0):
    print("Test LCD display for {:3d} seconds".format(duration))
    objSched = Sched()
    lcd0 = LCD(PINLIST, objSched, cols = 16)
    objSched.add_thread(lcd_thread(lcd0))
    if duration:
        objSched.add_thread(stop(duration, objSched))
    objSched.run()

lcdtest(20)

