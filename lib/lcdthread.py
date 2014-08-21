# LCD class for Micropython and scheduler.
# Author Peter Hinch.
# V1.0 21 Aug 2014

# Assumes an LCD with standard Hitachi HD44780 controller chip wired using four data lines
# Code has only been tested on two line LCD displays

# My code is based on this program written for the Raspberry Pi
# http://www.raspberrypi-spy.co.uk/2012/07/16x2-lcd-module-control-using-python/
# HD44780 LCD Test Script for
# Raspberry Pi
#
# Author : Matt Hawkins
# Site   : http://www.raspberrypi-spy.co.uk
# 
# Date   : 26/07/2012

import pyb
from usched import Timeout, Roundrobin

# **************************************************** LCD DRIVER ***************************************************

"""
Pin correspondence of default pinlist. This is supplied as an example
Name LCD connector Board
Rs    4   1 red    Y1
E     6   2        Y2
D7   14   3        Y3
D6   13   4        Y4
D5   12   5        Y5
D4   11   6        Y6
"""

# *********************************** GLOBAL CONSTANTS: MICROPYTHON PIN NUMBERS *************************************

# Supply as board pin numbers as a tuple Rs, E, D4, D5, D6, D7

PINLIST = ('Y1','Y2','Y6','Y5','Y4','Y3')

# **************************************************** LCD CLASS ****************************************************
# Initstring:
# 0x33, 0x32: See flowchart P24 send 3,3,3,2
# 0x28: Function set DL = 1 (4 bit) N = 1 (2 lines) F = 0 (5*8 bit font)
# 0x0C: Display on/off: D = 1 display on C, B = 0 cursor off, blink off
# 0x06: Entry mode set: ID = 1 increment S = 0 display shift??
# 0x01: Clear display, set DDRAM address = 0
# Original code had timing delays of 50uS. Testing with the Pi indicates that time.sleep() can't issue delays shorter
# than about 250uS. There also seems to be an error in the original code in that the datasheet specifies a delay of
# >4.1mS after the first 3 is sent. To simplify I've imposed a delay of 5mS after each initialisation pulse: the time to
# initialise is hardly critical. The original code worked, but I'm happier with something that complies with the spec.

# Threaded version:
# No point in having a message queue: people's eyes aren't that quick. Just display the most recent data for each line.
# Assigning changed data to the LCD object sets a "dirty" flag for that line. The LCD's runlcd thread then updates the
# hardware and clears the flag

# Note that the lcd_nybble method uses explicit delays rather than yields. This is for two reasons.
# The delays are short in the context of general runtimes and minimum likely yield delays, so won't
# significantly impact performance. Secondly, using yield produced perceptibly slow updates to the display text.

class LCD(object):                                          # LCD objects appear as read/write lists
    INITSTRING = (0x33, 0x32, 0x28, 0x0C, 0x06, 0x01)
    LCD_LINES = (0x80, 0xC0)                                # LCD RAM address for the 1st and 2nd line (0 and 40H)
    CHR = True
    CMD = False
    E_PULSE = 50                                            # Timing constants in uS
    E_DELAY = 50
    def __init__(self, pinlist, scheduler, cols, rows = 2): # Init with pin nos for enable, rs, D4, D5, D6, D7
        self.initialising = True
        self.LCD_E = pyb.Pin(pinlist[1], pyb.Pin.OUT_PP)    # Create and initialise the hardware pins
        self.LCD_RS = pyb.Pin(pinlist[0], pyb.Pin.OUT_PP)
        self.datapins = [pyb.Pin(pin_name, pyb.Pin.OUT_PP) for pin_name in pinlist[2:]]
        self.cols = cols
        self.rows = rows
        self.lines = [""]*self.rows
        self.dirty = [False]*self.rows
        for thisbyte in LCD.INITSTRING:
            self.lcd_byte(thisbyte, LCD.CMD)
            self.initialising = False                       # Long delay after first byte only
        scheduler.add_thread(runlcd(self))

    def lcd_nybble(self, bits):                             # send the LS 4 bits
        for pin in self.datapins:
            pin.value(bits & 0x01)
            bits >>= 1
        pyb.udelay(LCD.E_DELAY)    
        self.LCD_E.value(True)                              # Toggle the enable pin
        pyb.udelay(LCD.E_PULSE)
        self.LCD_E.value(False)
        if self.initialising:
            pyb.delay(5)
        else:
            pyb.udelay(LCD.E_DELAY)      

    def lcd_byte(self, bits, mode):                         # Send byte to data pins: bits = data
        self.LCD_RS.value(mode)                             # mode = True  for character, False for command
        self.lcd_nybble(bits >>4)                           # send high bits
        self.lcd_nybble(bits)                               # then low ones

    def __setitem__(self, line, message):                   # Send string to display line 0 or 1
                                                            # Strip or pad to width of display. Should use "{0:{1}.{1}}".format("rats", 20)
        message = "%-*.*s" % (self.cols,self.cols,message)  # but micropython doesn't work with computed format field sizes
        if message != self.lines[line]:                     # Only update LCD if data has changed
            self.lines[line] = message                      # Update stored line
            self.dirty[line] = True                         # Flag its non-correspondence with the LCD device

    def __getitem__(self, line):
        return self.lines[line]

def runlcd(thislcd):                                        # Periodically check for changed text and update LCD if so
    wf = Timeout(0.02)
    rr = Roundrobin()
    while(True):
        for row in range(thislcd.rows):
            if thislcd.dirty[row]:
                msg = thislcd[row]
                thislcd.lcd_byte(LCD.LCD_LINES[row], LCD.CMD)
                for thisbyte in msg:
                    thislcd.lcd_byte(ord(thisbyte), LCD.CHR)
                    yield rr                                # Reshedule ASAP
                thislcd.dirty[row] = False
        yield wf()                                          # Give other threads a look-in


