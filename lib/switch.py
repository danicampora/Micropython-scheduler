# Switch class for Micropython and scheduler.
# Author: Peter Hinch
# V1.02 26th Aug 2014 switchcheck thread is now a method
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
        self.switchstate = self.pin.value()                 # Get initial state
        objSched.add_thread(self.switchcheck())              # Thread runs forever

    def __call__(self):
        return self.switchstate                             # Return current state of switch (0 = pressed)

    def switchcheck(self):                                  # Generator object: thread which tests and debounces
        wf = Timeout(Switch.DEBOUNCETIME)
        while True:
            state = self.pin.value()
            if state != self.switchstate:                   # State has changed: act on it now.
                self.switchstate = state
                if state == 0 and self.close_func:
                    self.close_func(*self.close_func_args)
                elif state == 1 and self.open_func:
                    self.open_func(*self.open_func_args)
            yield wf()                                      # Ignore further state changes until switch has settled

