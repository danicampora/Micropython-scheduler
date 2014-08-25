# pushbutton.py pushbutton library. Class offers press, release, long and double click callbacks
# Author: Peter Hinch
# V1.0 21st Aug 2014

import pyb
from usched import Sched, Timeout
from delay import Delay

# ************************************************ PUSHBUTTON CLASS *************************************************

# A Pushbutton instance is a debounced switch with characteristics suited to a physical button. Its state is defined
# as a boolean, True if the button is pressed, regardless of how the device is wired or whether it is normally open
# or normally closed. The class supports running callback functions on button press, button release, long presses
# or double clicks

# Function call syntax returns debounced logical state of the button, regardless of whether wired to ground or 3.3v

descriptor = dict()                                         # Defines a default pushbutton. User can change
descriptor['no'] = True                                     # Normally open switch
descriptor['grounded'] = True                               # Common is wired to ground
descriptor['pull'] = pyb.Pin.PULL_UP                        # on chip pullup enabled
descriptor['debounce'] = 0.02
descriptor['long_press_time'] = 1
descriptor['double_click_time'] = 0.4

class Pushbutton(object):
    def __init__(self, objSched, pinName, desc, 
            true_func = None, true_func_args = (),
            false_func = None, false_func_args = (),
            long_func = None, long_func_args = (),
            double_func = None, double_func_args =()):
        self.pin = pyb.Pin(pinName, pyb.Pin.IN, desc['pull']) # Initialise for input
        self.desc = desc                                    # Button descriptor
        self.objSched = objSched
        self.true_func = true_func
        self.true_func_args = true_func_args
        self.false_func = false_func
        self.false_func_args = false_func_args
        self.long_func = long_func
        self.long_func_args = long_func_args
        self.double_func = double_func
        self.double_func_args = double_func_args
        self.sense = not desc['no']^desc['grounded']        # Conversion from electrical to logical value
        self.buttonstate = self.rawstate()                  # Initial state
        objSched.add_thread(self.buttoncheck())             # Thread runs forever

    def rawstate(self):                                     # Current non-debounced logical button state
        return bool(self.pin.value() ^ self.sense)          # True == pressed

    def __call__(self):
        return self.buttonstate                             # Current debounced state of switch (True = pressed)

    def buttoncheck(self):                                  # Generator object: thread which tests and debounces
        wf = Timeout(self.desc['debounce'])
        state_id = 0
        if self.long_func:
            longdelay = Delay(self.objSched, self.long_func, self.long_func_args)
        if self.double_func:
            doubledelay = Delay(self.objSched)
        while True:
            state = self.rawstate()
            if state != self.buttonstate:                   # State has changed: act on it now.
                self.buttonstate = state
                if state:                                   # Button has been pressed
                    if self.long_func and not longdelay.running():
                        longdelay.trigger(self.desc['long_press_time']) # Start long press delay
                    if self.double_func:
                        if doubledelay.running():
                            self.double_func(*self.double_func_args)
                        else:                               # First click: start doubleclick timer
                            doubledelay.trigger(self.desc['double_click_time'])
                    if self.true_func:
                        self.true_func(*self.true_func_args)
                else:                                       # Button release
                    if self.long_func and longdelay.running():
                        longdelay.stop()                    # Avoid interpreting a second click as a long push
                    if self.false_func:
                        self.false_func(*self.false_func_args)
            yield wf()                                      # Ignore further state changes until switch has settled

