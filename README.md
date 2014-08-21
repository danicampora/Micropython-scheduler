Micropython-scheduler
=====================

V1.0 21st August 2014

A set of libraries for writing threaded code on the MicroPython board.

There are three libraries
 1. usched.py The scheduler
 2. switch.py Support for debounced switches. Uses usched.
 3. lcdthread.py Support for LCD displays using the Hitachi HD44780 controller chip. Uses usched.

Test/demonstration programs
 1. ledflash.py Flashes the onboard LED's asynchronously
 2. roundrobin.py Demonstrates round-robin schedulting.
 3. irqtest.py Demonstrates a thread which blocks on an interrupt.
 4. subthread.py Illustrates dynamic creation and deletion of threads.
 5. lcdtest.py Demonstrates output to an attached LCD display.
 6. polltest.py A thread which blocks on a user defined polling function

