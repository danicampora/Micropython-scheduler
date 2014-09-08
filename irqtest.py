# irqtest.py Demonstrates, with minimal hardware, the use of the scheduler in responding to pin interrupts
# Author: Peter Hinch
# V1.02 6th Sep 2014

# Also demonstrates the debounced switch library (which is threaded)

# A thread sets up initial conditions and blocks pending an interrupt. When it occurs the following things happen
# 1. The scheduler's default callback function runs recording the fact that the event has happened.
# 2. The user's callback runs. This is still in the interrupt handler's context: Micropython rules apply
# 3. (Later) the thread wakes up. It receives a count of the number of interrupts which have occurred while it
# was blocked.

# This demo runs one thread as an oscillator pulsing (via a link) an input pin. The callback function toggles
# an lED and pulses an output pin. The blocking thread toggles another LED and prints a message.
# The optional pushbuttons print a message when operated.

import pyb
from usched import Sched, Poller, Timeout, Pinblock, wait
from switch import Switch                                   # Library supporting debounced switches

# HARDWARE 
# MicroPython board with pin X7 linked to pin X8
# Optionally provide two pushbuttons wired to be capable of grounding X5 and X6 respectively
# The interrupt handler pulses pin Y10 to enable timings to be measured, notably minimum pulse duration
# and latency

# THREADS:

def stop(fTim, objSch):                                     # Stop the scheduler after fTim seconds
    yield from wait(fTim)
    objSch.stop()

def oscillator(freq_hz = 1):                                # Toggles X7 forever.
     outpin = pyb.Pin(pyb.Pin.board.X7, pyb.Pin.OUT_PP)     # Push pull output pin on X7
     wf = Timeout(1/(2*freq_hz))
     while True:
        outpin.low()
        yield wf()                                          # Duration will be imprecise owing to contention
        outpin.high()
        yield wf()

class Irq_handler(object):                                  # Using an object to demonstrate communication between
    def __init__(self, lstLed, testpin):                    # the interrupt handler and its thread
        self.lstLed = lstLed
        self.testpin = testpin

    def callback(self, irqno):                              # BEWARE: runs in interrupt's context. MicroPython rules apply
        self.testpin.high()                                 # along with normal concurrency caveats
        self.testpin.low()                                  # Pulse of 6.8uS on Y10
        self.lstLed[1].toggle()

def irqtest_thread():                                       # Thread blocks on an interrupt.
    lstLeds = [pyb.LED(x) for x in range(1,5)]              # Initialise all four on board LED's
    testpin = pyb.Pin(pyb.Pin.board.Y10, pyb.Pin.OUT_PP)    # Pin Y10 pulsed when handler runs
    mypin = pyb.Pin.board.X8                                # X8 used for interrupt request
    han = Irq_handler(lstLeds, testpin)
    wf = Pinblock(mypin, pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_NONE, han.callback) # Blocking interrupt handler
    count = 0
    while True:
        result = (yield wf())                               # Wait for the interrupt
        lstLeds[0].toggle()                                 # Toggle LED
        print("Interrupt recieved ", result)

def x5print(*args):
    print("X5 released " +args[0])                          # Demo of argument passing

def x6print(*args):
    print("X6 pressed " + args[0])

# USER TEST PROGRAM
# Runs forever unless you pass a number of seconds
def test(duration = 0):                                     # Runs oscillator, counts interrupts, responds to switches
    if duration:
        print("Test interrupt on pin X8 for {:3d} seconds".format(duration))
    objSched = Sched()                                      # Requires jumper between pins X7 and X8
    objSched.add_thread(oscillator(1))                      # 1Hz
    objSched.add_thread(irqtest_thread())
    Switch(objSched, 'X5', open_func = x5print, open_func_args = ("Red",)) # X5 triggers on open
    Switch(objSched, 'X6', x6print, ("Yellow",))            # X6 triggers on close
    if duration:
        objSched.add_thread(stop(duration, objSched))
    objSched.run()

test(30)

