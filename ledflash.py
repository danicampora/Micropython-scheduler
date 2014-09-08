# ledflash.py Demo/test program for MicroPython scheduler
# Author: Peter Hinch
# V1.1 6th Sep 2014
# Flashes the onboard LED's each at a different rate. Stops after ten seconds.

import pyb
from usched import Sched, wait

# Run on MicroPython board bare hardware
# THREADS:
def stop(fTim, objSch):                                     # Stop the scheduler after fTim seconds
    yield from wait(fTim)
    objSch.stop()

def toggle(objLED, time):
    while True:
        yield from wait(time)
        objLED.toggle()
    
# USER TEST FUNCTION

def test(duration = 0):
    if duration:
        print("Flash LED's for {:3d} seconds".format(duration))
    leds = [pyb.LED(x) for x in range(1,5)]                 # Initialise all four on board LED's
    objSched = Sched()                                      # Instantiate the scheduler
    for x in range(4):                                      # Create a thread instance for each LED
        objSched.add_thread(toggle(leds[x], 0.2 + x/2))
    if duration:
        objSched.add_thread(stop(duration, objSched))       # Commit suicide after specified no. of seconds
    objSched.run()                                          # Run it!

test(10)

