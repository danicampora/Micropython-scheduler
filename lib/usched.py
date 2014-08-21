# Microthreads for the micropython board. 20th Aug 2014
# Author: Peter Hinch
# V1.0 21st Aug 2014

# 14th Aug unused pin argument removed from Waitfor constructor
# 12th Aug: Waitfor.triggered returns a measure of priority, with scheduler scheduling the highest priority thread
# and sending the result to the yield statement
# New implementation. Uses microsecond counter more effectively. Supports waiting on interrupt.

import pyb
import micropython
micropython.alloc_emergency_exception_buf(100)

# *************************************************** TIMER ACCESS **************************************************

# Timing is based on a free running uS counter
# Utility functions enable access to the counter which produce correct results if timer rolls over

TIMERPERIOD = 0x3fffffff                                    # 17.89 minutes 1073 secs
MAXTIME     = 0x1fffffff                                    # 536 seconds maximum timeout

micros = pyb.Timer(2, prescaler=83, period=TIMERPERIOD)     # Initialise and start the global counter

class TimerException(Exception) : pass

def microsWhen(timediff):                                   # Expected value of counter in a given no. of uS
    if timediff >= MAXTIME:
        raise TimerException()
    return (micros.counter() + timediff) & TIMERPERIOD

def microsSince(oldtime):                                   # No of uS since timer held this value
    return (micros.counter() - oldtime) & TIMERPERIOD

def after(trigtime):                                        # If current time is after the specified value return
    res = ((micros.counter() - trigtime) & TIMERPERIOD)     # the no. of uS after. Otherwise return zero
    if res >= MAXTIME:
        res = 0
    return res
                                                            # @micropython.native causes crash: can't find reason
def seconds(S):                                             # Utility functions to convert to integer microseconds
    return int(1000000*S)

def millisecs(mS):
    return int(1000*mS)

# *********************************** WAITFOR CLASS: TRIGGER FOR THREAD EXECUTION ***********************************

# This is a base class. User threads should use only classes derived from this.
# Threads submit control by yielding a Waitfor object. This conveys information to the scheduler as to when the thread
# should be rescheduled. The scheduler stores this on the task list and polls its triggered method to determine if the
# thread is ready to run. Can wait on a time, an interrupt, a poll function, or not at all: reschedule ASAP running
# other such threads in round-robin fashion. A timeout may be applied when blocking on an interrupt or a poll.
# A poll function will be called every time the scheduler determines which thread to run, so should execute quickly.
# It should return None unless the thread is to run, in which case it should return an integer which will be passed
# back to the thread

# The triggered method returns a "priority" tuple of three integers indicating priority or None. The latter indicates
# that the thread is not ready for execution. The value (0,0,0) indicates a round-robin reschedule.
# The tuple holds: 
# (number of interrupts missed, pollfunc return value, uS after timeout or zero if it's a round-robin thread)
# This design allows priorities to be sorted in natural order. The scheduler sends this tuple to the thread which
# yielded the Waitfor object.
# Time in uS must not exceed MAXTIME (536 secs) and an exception will be raised if a longer time is specified. Threads
# can readily implement longer delays with successive yields in a loop.
# If a thread wishes to run again ASAP it yields a Roundrobin instance. In the absence of timed-out or higher priority
# threads, threads yielding these will run in round-robin fashion with minimal delay.

class Waitfor(object):
    def __init__(self):
        self.uS         = 0                                 # Current value of timeout in uS
        self.timeout    = microsWhen(0)                     # End value of microsecond counter when TO has elapsed
        self.forever    = False                             # "infinite" time delay flag
        self.irq        = None                              # Interrupt vector no
        self.pollfunc   = None                              # Function to be called if we're polling
        self.pollfunc_args = ()                             # Arguments for the above
        self.customcallback = None                          # Optional custom interrupt handler
        self.interruptcount = 0                             # Set by handler, tested by triggered()
        self.roundrobin = False                             # If true reschedule ASAP

    def triggered(self):                                    # Polled by scheduler. Returns a priority tuple or None if not ready
        if self.irq:                                        # Waiting on an interrupt
            self.irq.disable()                              # Potential concurrency issue here (????)
            numints = self.interruptcount                   # Number of missed interrupts
            if numints:                                     # Waiting on an interrupt and it's occurred
                self.interruptcount = 0                     # Clear down the counter
            self.irq.enable()
            if numints:
                return (numints, 0, 0)
        if self.pollfunc:                                   # Optional function for the scheduler to poll
            res = self.pollfunc(*self.pollfunc_args)        # something other than an interrupt
            if res is not None:
                return (0, res, 0)
        if not self.forever:                                # Check for timeout
            if self.roundrobin:
                return (0,0,0)                              # Priority value of round robin thread
            res = after(self.timeout)                       # uS after, or zero if not yet timed out in which case we return None
            if res:                                         # Note: can never return (0,0,0) here!
                return (0, 0, res)                          # Nonzero means it's timed out
        return None                                         # Not ready for execution

    def _ussetdelay(self,uS = None):                        # Reset the timer by default to its last value
        if uS:                                              # If a value was passed, update it
            self.uS = uS
        self.timeout = microsWhen(self.uS)                  # Target timer value
        return self

    def setdelay(self, secs = None):                        # Method used by derived classes to alter timer values
        if secs is None:                                    # Set to infinity
            self.forever = True
            return self
        else:                                               # Update saved delay and calculate a new end time
            self.forever = False
            return self._ussetdelay(seconds(secs))

    def __call__(self):                                     # Convenience function allows user to yield an updated
        if self.uS:                                         # waitfor object
            return self._ussetdelay()
        return self

    def intcallback(self, irqno):                           # Runs in interrupt's context.
        if self.customcallback:
            self.customcallback(irqno)
        self.interruptcount += 1                            # Increments count to enable trigger to operate

class Roundrobin(Waitfor):                                  # Trivial subclasses of Waitfor. A thread yielding a Roundrobin
    def __init__(self):                                     # will be rescheduled as soon as priority threads have been serviced
        super().__init__()
        self.roundrobin = True

class Timeout(Waitfor):                                     # A thread yielding a Timeout instance will pause for at least that period
    def __init__(self, tim):                                # Time is in seconds
        super().__init__()
        self.setdelay(tim)

# ************************************************ INTERRUPT HANDLING ***********************************************

# The aim here is to enable a thread to block pending receipt of an interrupt. An optional timeout may be applied.
# A thread wishing to do this must create a Pinblock instance with optional timeout and callback function
# wf = Pinblock(mypin, pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_NONE, mycallback)
# The custom callback function (if provided) receives the irq number as its only argument
class Pinblock(Waitfor):                                    # Block on an interrupt from a pin subject to optional timeout
    def __init__(self, pin, mode, pull, customcallback = None, timeout = None):
        super().__init__()
        self.customcallback = customcallback
        if timeout is None:
            self.forever = True
        else:
            self.setdelay(timeout)
        self.irq = pyb.ExtInt(pin, mode, pull, self.intcallback)

class Poller(Waitfor):
    def __init__(self, pollfunc, pollfunc_args = (), timeout = None):
        super().__init__()
        self.pollfunc   = pollfunc
        self.pollfunc_args = pollfunc_args
        if timeout is None:
            self.forever = True
        else:
            self.setdelay(timeout)

# ************************************************* SCHEDULER CLASS *************************************************

class Sched(object):
    def __init__(self):
        self.lstThread = []                                 # Entries contain [Waitfor object, function]
        self.bStop = False

    def stop(self):                                         # Kill the run method
        self.bStop = True

    def add_thread(self, func):                             # Thread list contains [Waitfor object, generator]
        try:                                                # Run thread to first yield to acquire a Waitfor instance
            self.lstThread.append([func.send(None), func])  # and put the resultant thread onto the threadlist
        except StopIteration:                               # Shouldn't happen on 1st call: implies thread lacks a yield statement
            print("Stop iteration error")                   # best to tell user.

    def run(self):                                          # Run scheduler but trap ^C for testing
        try:
            self._runthreads()
        except OSError as v:                                # Doesn't recognise EnvironmentError or VCPInterrupt!
            print(v)
            print("Interrupted")

    def _runthreads(self):                                  # Only returns if the stop method is used or all threads terminate
        while len(self.lstThread) and not self.bStop:       # Run until last thread terminates or the scheduler is stopped
            self.lstThread = [thread for thread in self.lstThread if thread[1] is not None] # Remove threads flagged for deletion
            lstPriority = []                                # List threads which are ready to run
            lstRoundRobin = []                              # Low priority round robin threads
            for idx, thread in enumerate(self.lstThread):   # Put each pending thread on priority or round robin list
                priority = thread[0].triggered()            # (interrupt count, poll func value, uS overdue) or None
                if priority is not None:                    # Ignore threads waiting on events or time
                    if priority == (0,0,0) :                # (0,0,0) indicates round robin
                        lstRoundRobin.append(idx)
                    else:                                   # Thread is ready to run
                        lstPriority.append((priority, idx)) # List threads ready to run
            lstPriority.sort()                              # Lowest priority will be first in list

            while True:                                     # Until there are no round robin threads left
                while len(lstPriority):                     # Execute high priority threads first
                    priority, idx = lstPriority.pop(-1)     # Get highest priority thread. Thread:
                    thread = self.lstThread[idx]            # thread[0] is the current waitfor instance, thread[1] is the code
                    try:                                    # Run thread, send (interrupt count, poll func value, uS overdue)
                        thread[0] = thread[1].send(priority)  # Thread yields a Waitfor object: store it for subsequent testing
                    except StopIteration:                   # The thread has terminated:
                        self.lstThread[idx][1] = None       # Flag thread for removal

                if len(lstRoundRobin) == 0:                 # There are no round robins pending. Quit the loop to rebuild new
                    break                                   # lists of threads
                idx = lstRoundRobin.pop()                   # Run an arbitrary round robin thread and remove from pending list
                thread = self.lstThread[idx]
                try:                                        # Run thread, send (0,0,0) because it's a round robin
                    thread[0] = thread[1].send((0,0,0))     # Thread yields a Waitfor object: store it
                except StopIteration:                       # The thread has terminated:
                    self.lstThread[idx][1] = None           # Flag thread for removal
                                                            # Rebuild priority list: time has elapsed and events may have occurred!
                for idx, thread in enumerate(self.lstThread): # check and handle priority threads
                    priority = thread[0].triggered()        # (interrupt count, poll func value, uS overdue) or None
                                                            # Ignore pending threads, those scheduled for deletion and round robins
                    if priority is not None and priority != (0,0,0) and thread[1] is not None:
                         lstPriority.append((priority, idx)) # Just list threads wanting to run
                lstPriority.sort()

