# ledflash.py Demo/test program for MicroPython scheduler
# Author: Peter Hinch
# V1.0 21st Aug 2014
# Flashes the onboard LED's each at a different rate. Stops after ten seconds.

import pyb
from usched import Sched, Timeout

# Run on MicroPython board bare hardware
# THREADS:
def stop(fTim, objSch):                                     # Stop the scheduler after fTim seconds
    yield Timeout(fTim)
    objSch.stop()

def toggle(objLED, time):
    while True:
        yield Timeout(time)
        objLED.toggle()
    
# USER TEST FUNCTION

def ledtest(duration = 0):
    print("Flash LED's for {:3d} seconds".format(duration))
    leds = [pyb.LED(x) for x in range(1,5)]                 # Initialise all four on board LED's
    objSched = Sched()                                      # Instantiate the scheduler
    for x in range(4):                                      # Create a thread instance for each LED
        objSched.add_thread(toggle(leds[x], 0.2 + x/2))
    if duration:
        objSched.add_thread(stop(duration, objSched))       # Commit suicide after specified no. of seconds
    objSched.run()                                          # Run it!

ledtest(10)

