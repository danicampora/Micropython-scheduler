# instrument.py Demo of instrumenting code via the usched module's timer functions
# Author: Peter Hinch
# V1.02 6 Sep 2014 now uses pyb.micros() and yield from wait
# V1.0 21st Aug 2014

import pyb
from usched import Sched, Roundrobin, wait, microsSince

# Run on MicroPython board bare hardware
# THREADS:

def stop(fTim, objSch):                                     # Stop the scheduler after fTim seconds
    yield from wait(fTim)
    objSch.stop()

def thr_instrument(objSch, lstResult):
    yield Roundrobin()                                      # Don't measure initialisation phase (README.md)
    while True:
        start = pyb.micros()                                # More typically we'd measure our own code
        yield Roundrobin()                                  # but here we're measuring yield delays
        lstResult[0] = max(lstResult[0], microsSince(start))
        lstResult[1] += 1

def robin(text):
    wf = Roundrobin()
    while True:
        print(text)
        yield wf()

# USER TEST PROGRAM

def test(duration = 0):
    objSched = Sched()
    objSched.add_thread(robin("Thread 1"))                  # Instantiate a few threads
    objSched.add_thread(robin("Thread 2"))
    objSched.add_thread(robin("Thread 3"))
    lstResult = [0, 0]
    objSched.add_thread(thr_instrument(objSched, lstResult))
    if duration:
        objSched.add_thread(stop(duration, objSched))           # Run for a period then stop
    objSched.run()
    print("Maximum delay was {:6.1f}mS".format(lstResult[0]/1000.0))
    print("Thread was executed {:3d} times in {:3d} seconds".format(lstResult[1], duration))

test(2)

