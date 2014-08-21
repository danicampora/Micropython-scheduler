Micropython-scheduler
=====================

V1.0 21st August 2014

A set of libraries for writing threaded code on the MicroPython board.

There are three libraries
usched.py The scheduler
switch.py Support for debounced switches. Uses usched.
lcdthread.py Support for LCD displays using the Hitachi HD44780 controller chip. Uses usched.

Test/demonstration programs
ledflash.py Flashes the onboard LED's asynchronously
roundrobin.py Demonstrates round-robin schedulting.
irqtest.py Demonstrates a thread which blocks on an interrupt.
subthread.py Illustrates dynamic creation and deletion of threads.
lcdtest.py Demonstrates output to an attached LCD display.
polltest.py A thread which blocks on a user defined polling function

