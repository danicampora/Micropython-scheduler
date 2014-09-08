# polltest.py Demonstrates the use of poll functions where a thread blocks pending the result of a callback function
# polled by the scheduler
# Author: Peter Hinch
# V1.02 6th Sep 2014

import pyb
from usched import Sched, Poller, wait

# Poll functions will be called by the scheduler each time it determines which task to run. The thread will be scheduled
# unless the poll function returns None. When scheduled the result of the poll function - which should be an integer -
# is returned to the thread.
# The intended use of poll functions is for servicing hardware which can't raise interrupts. In such a function
# the function would clear down the device before return so that (until the device again becomes ready) subsequent calls
# would return None. Pseudocode:
# my poll funtion()
#    if hardware is ready
#        service it so that subsequent test returns not ready
#        return an integer
#    return None

# This example polls the accelerometer with a timeout, only responding to changes which exceed a threshold.
# Also demonstrates returning data from a callback by using an object method as a callback function

# The poll function is a method of the Accelerometer class defined below. Using a class method enables the
# function to retain state between calls. In this example it determines the amount of change since the last
# update and returns None if the amount of change is below a threshold: this will cause the scheduler not to
# schedule the thread. If the amount of change exceeds the threshold the Accelerometer instance's data is
# updated and the function returns 1 causing the scheduler to resume the processing thread.


# Run on MicroPython board bare hardware
# THREADS:

def stop(fTim, objSch):                                     # Stop the scheduler after fTim seconds
    yield from wait(fTim)
    objSch.stop()

class Accelerometer(object):
    def __init__(self, accelhw):
        self.accelhw = accelhw
        self.coords = [accelhw.x(), accelhw.y(), accelhw.z()]

    def dsquared(self, xyz):                                # Return the square of the distance between this and a passed 
        return sum(map(lambda p, q : (p-q)**2, self.coords, xyz)) # acceleration vector

    def poll(self, threshold):                              # Device is noisy. Only update if change exceeds a threshold
        xyz = [self.accelhw.x(), self.accelhw.y(), self.accelhw.z()]
        if self.dsquared(xyz) > threshold*threshold:
            self.coords = xyz
            return 1                                        # Scheduler will run the handling thread
        return None                                         # Scheduler will pass on the handler
    @property                                               # Convenience properties: return x, y, z
    def x(self):
        return self.coords[0]
    @property
    def y(self):
        return self.coords[1]
    @property
    def z(self):
        return self.coords[2]

def accelthread():
    accelhw = pyb.Accel()                                   # Instantiate accelerometer hardware
    yield from wait(0.03)                                   # Allow accelerometer to settle
    accel = Accelerometer(accelhw)
    wf = Poller(accel.poll, (4,), 2)                        # Instantiate a Poller with 2 second timeout.
    while True:
        reason = (yield wf())
        if reason[1]:                                       # Value has changed
            print("Value x:{:3d} y:{:3d} z:{:3d}".format(accel.x, accel.y, accel.z))
        if reason[2]:
            print("Timeout waiting for accelerometer change")

# USER TEST PROGRAM

def test(duration = 0):
    if duration:
        print("Output accelerometer values for {:3d} seconds".format(duration))
    else:
        print("Output accelerometer values")
    objSched = Sched()
    objSched.add_thread(accelthread())
    if duration:
        objSched.add_thread(stop(duration, objSched))           # Run for a period then stop
    objSched.run()

test(30)

