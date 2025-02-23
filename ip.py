#!/usr/bin/env python3
#
"""
Python models of the UCLA Edukit rotary inverted pendulum
and the associated STM32 embedded rotary encoder/motor 
sensor and actuator systems
"""

from invertedPendulum import CommandFrame, ResponseFrame

class ActiveStatusMonitor:
    """
    An object to monitor the status of the system actively
    """
    def __init__(self):
        cmd = CommandFrame(253,1,0,)

def main():
    cf = CommandFrame()

if __name__ == '__main__':
    main()