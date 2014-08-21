# Switch class for Micropython and scheduler.
# Author: Peter Hinch
# V1.0 21st Aug 2014
# 8th Aug: supports arguments for switch callbacks

import pyb
from usched import Timeout

# ************************************************** SWITCH CLASS ***************************************************

# The purpose of the switch object is to work with event driven programming using the scheduler. The switch is polled:
# there is usually no merit in using interrupts for a manually operated switch, especially with a scheduler using
# cooperative multi threading.
# A switch object will call user supplied open and close callback functions when the switch is operated. Polling is
# done by running a thread which runs forever and is done in a way to ensure debouncing.
# The switch is presumed to be wired from the assigned pin to ground.

class Switch(object):
    DEBOUNCETIME = 0.02
    def __init__(self, objSched, pinName, close_func = None, close_func_args = (), open_func = None, open_func_args = ()):
        self.pin = pyb.Pin(pinName, pyb.Pin.IN, pyb.Pin.PULL_UP) # Initialise for input, switch to ground
        self.close_func = close_func
        self.close_func_args = close_func_args
        self.open_func = open_func
        self.open_func_args = open_func_args
        objSched.add_thread(switchcheck(self))              # Thread runs forever

    def __call__(self):
        return self.pin.value()                             # Return current state of switch (0 = pressed)

def switchcheck(myswitch):                                  # Generator object: thread which tests and debounces
    oldstate = myswitch()                                   # Get initial switch state
    wf = Timeout(Switch.DEBOUNCETIME)
    while True:
        state = myswitch()
        if state != oldstate:                               # State has changed: act on it now.
            if state == 0 and myswitch.close_func:
                myswitch.close_func(*myswitch.close_func_args)
            elif state == 1 and myswitch.open_func:
                myswitch.open_func(*myswitch.open_func_args)
            oldstate = state
        yield wf()                                          # Ignore further state changes until switch has settled

