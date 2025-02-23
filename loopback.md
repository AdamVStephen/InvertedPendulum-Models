```
111
#!/usr/bin/env python
# -*- coding: utf-8 -*-

#import the PySerial library and sleep from the time library
import serial
from time import sleep, time

# declare to variables, holding the com port we wish to talk to and the speed
port = '/dev/ttyAMA0'
baud = 9600
lastime = 0
timeout = 30 # 30 seconds timeout

# open a serial connection using the variables above
ser = serial.Serial(port=port, baudrate=baud)
ser.timeout(1)  # set the read time out to 1 second
# wait for a moment before doing anything else
sleep(0.2)


while true:
    char = ser.read()
    if char == 'a':
        llapmsg = 'a'
        while len(llapmsg) < 12:
            llapmsg += ser.read()
        if llapmsg == 'a--D02LOW---':
            print("ALARM!!!!!!!")
             ser.write('a--D13HIGH--')
        elif llapmsg == 'a--SOMETHING':
            # do something else with mesage 
            pass
    else:
        # char was not start of a message or the read timed out
        # do something else
        if (time() - lasttime) > timeout:
            lattime = time()
            # say send a periodic message 
            ser.write('a--HELLO----')
            print("Sent hello")
            
```
