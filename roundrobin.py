# roundrobin.py Runs three threads in round robin fashion. Stops after a duration via a timeout thread.
# Author: Peter Hinch
# V1.02 6th Sep 2014

import pyb
from usched import Sched, Roundrobin, wait

# Run on MicroPython board bare hardware
# THREADS:

def stop(fTim, objSch):                                     # Stop the scheduler after fTim seconds
    yield from wait(fTim)
    objSch.stop()

def robin(text):
    wf = Roundrobin()
    while True:
        print(text)
        yield wf()

# USER TEST PROGRAM

def test(duration = 0):
    objSched = Sched()
    objSched.add_thread(robin("Thread 1"))
    objSched.add_thread(robin("Thread 2"))
    objSched.add_thread(robin("Thread 3"))
    if duration:
        objSched.add_thread(stop(duration, objSched))       # Kill after a period
    objSched.run()

test(5)

