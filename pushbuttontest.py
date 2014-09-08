# pushbuttontest.py Demonstrates the pushbutton library
# Author: Peter Hinch
# V1.02 6th Sep 2014

from usched import Sched, wait
from pushbutton import Pushbutton, descriptor

def stop(fTim, objSch):                                     # Stop the scheduler after fTim seconds
    yield from wait(fTim)
    objSch.stop()

def x5print(*args):
    print("X5 released " +args[0])                          # Demo of argument passing

def x6print(*args):
    print("X6 pressed " + args[0])

def yellowlong(*args):
    print(args[0] +" yellow")

def yellowdbl(*args):
    print(args[0] +" yellow")

def test(duration = 0):                                   # responds to switches
    if duration:
        print("Tests pushbuttons for {:5d} seconds".format(duration))
    else:
        print("Tests pushbuttons")
    objSched = Sched()
    Pushbutton(objSched, 'X5', descriptor, 
        false_func = x5print, false_func_args = ("Red",))   # X5 triggers on open
    Pushbutton(objSched, 'X6', descriptor, 
        true_func = x6print, true_func_args = ("Yellow",),
        long_func = yellowlong, long_func_args = ("Long press",),
        double_func = yellowdbl, double_func_args = ("Double click",)) # X6 triggers on close
    if duration:
        objSched.add_thread(stop(duration, objSched))
    objSched.run()

test(20)

