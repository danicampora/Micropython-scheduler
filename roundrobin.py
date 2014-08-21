# roundrobin.py Runs three threads in round robin fashion. Stops after a duration via a timeout thread.
# Author: Peter Hinch
# V1.0 21st Aug 2014

import pyb
from usched import Sched, Roundrobin, Timeout

# Run on MicroPython board bare hardware
# THREADS:

def stop(fTim, objSch):                                     # Stop the scheduler after fTim seconds
    yield Timeout(fTim)
    objSch.stop()

def robin(text):
    wf = Roundrobin()
    while True:
        print(text)
        yield wf()

# USER TEST PROGRAM

def robin_test(duration = 0):
    objSched = Sched()
    objSched.add_thread(robin("Thread 1"))
    objSched.add_thread(robin("Thread 2"))
    objSched.add_thread(robin("Thread 3"))
    if duration:
        objSched.add_thread(stop(duration, objSched))       # Kill after a period
    objSched.run()

robin_test(5)

