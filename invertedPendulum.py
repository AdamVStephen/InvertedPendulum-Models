#!/usr/bin/env python3
#
"""
Python models of the UCLA Edukit rotary inverted pendulum
and the associated STM32 embedded rotary encoder/motor 
sensor and actuator systems.
"""

import pdb

from struct import pack, unpack

class L6474:
    """
    Attributes of the L6474 motor controller
    c.f. L6474_Init_t
    Augmented with other motor information for pretty printing.
    """
    def __init__(self):
        self.instance = 1
        self.max_acceleration = self.max_deceleration = self.max_speed = 131071


class CommandInterpreter:
    """
    This class handles command packets (TX)
    *        byte 0: requested command ID
    *        byte 1: device ID
    *        bytes 2-9: command parameters
    """
    # commandID: ["Description", pack format]
    command_encoding = {
        17 : ["GoTo Location", 10, 'BBI4b'],
        22 : ["Set Acceleration", 10, 'BBI4b'],
        252 : ["Reset.  No parameters", 10, 'BB7b'],
        253 : ["Read Status. No parameters", 10,  'BB7b' ],
        254 : ["Apply acceleration", 10, 'BBff']
    }
    
    def __init__(self):
        pass

    def handle_command(self, commandID):
        if commandID:
            pass

CMDERR_OK = 0
CMDERR_INVALID_COMMAND = 1
CMDERR_INVALID_DEVICE = 2

class ResponseInterpreter:
    """
 * @brief Response (13 bytes) has the following structure:
 *        byte 0: command ID
 *        byte 1: device ID
 *        byte 2: error code (0 == OK)
 *        bytes 3-6: command return values
 *        or
 *        bytes 3-12: status

 To distinguish which type of response has been sent we use the size
 """
    response_decoding = {
        # commandID: ["Description", size, format]
        252 : ["Reset", 7, 'bbb?bbb'],  # Single bool ret = BSP_MotorControl_SoftStop() trailing packet data for no reason
        253 : ["Read status", 13, 'bbbbbiI'],
        254 : ["Apply acceleration", 0, ''] # No response is sent
    }



from collections import namedtuple

class SerialFrame:
    """
    Base class for describing serial protocols
    """
    format = "!b"
    fields = [
        ('demo_byte', 0),
        ]

    def __init__(self):
       (field_names, default_values) = zip(*self.fields)
       self.Record = namedtuple('Record', ' '.join(field_names), defaults = default_values)
       self.record = self.Record()

    def unpack(self, data):
        self.record = self.record._make(unpack(self.format, data))

    def pack(self, *args):
        if len(args) != len(self.format) - 1:
            raise RuntimeError(f'{len(args)} arguments provided, {len(self.format) -1} arguments required')

        self.data = pack(self.format, *args) 

        self.unpack(self.data)
    
    def __repr__(self):
        r = []
        r.append(f'{self.__class__.__name__} with format {self.format}')
        for field in self.record._fields:
            r.append("%s : %d" % (field, self.record.__getattribute__(field)))
        return '\n'.join(r)


class CommandFrame(SerialFrame):
    """
    CommandFrame according to RokHari control implementation
    Commands may have varying number of command parameters

    No table of consistency is provided - the decoder in
    the STM32 code provides the lookup.

    The decoder deals with unpacking 1,2,4 byte structures
    and serializing to C types.

    In this python support tool, we implement the deserialization
    for the commands used in the MARTe2 control application.

    TODO: code review - check if the UCLA project and L6474 driver
    provide any mapping on commandID to API.

    DeviceID comes from L6474 design which can multiplex  boards.

    Command frame layout:
 *        byte 0: command ID
 *        byte 1: device ID
 *        byte 2-9: command parameters 
    
    """
 
    format = "!bbQ"
    fields = [
            ('commandID', 0),
            ('deviceID', 0),
            ('params', 0),
            ]

    def __init__(self, param_spec = None):
        # Option to customise the class on the fly
        # param_spec must be a list of (field, format, default_value)
        if param_spec is not None:
            format = format[0:2]
            for (field_name, field_format, field_default) in param_spec:
                format += field_format
                self.fields.append((field_name, field_default))
        super().__init__()

    def pack(self, commandID, deviceID, errorCode, responseSize, motorState, motorPos, encoderPos):
        """Repeat the field order to give better function signature"""
        self.data = pack(self.format, commandID, deviceID, errorCode, responseSize,
                            motorState, motorPos, encoderPos)
        self.unpack(self.data)

class CommandResponseFrame(SerialFrame):
    """
    ReponseFrame according to RokHari control implementation

 * @brief Response (13 bytes) has the following structure:
 *        byte 0: command ID
 *        byte 1: device ID
 *        byte 2: error code (0 == OK)
 *        bytes 3-6: command return values : depend on command
 *        or
 *        bytes 3-12: status : always the same

    Which response is received can be determined by frame size (7 or 13)

    This class is for the 13 byte CommandResponse
   """
 
    format = "!bbbbbiI"
    fields = [
            ('commandID', 0),
            ('deviceID', 0),
            ('errorCode', 0),
            ('responseSize', 13),
            ('motorState', 0),
            ('motorPos', 0),
            ('encoderPos', 0)
            ]

    def pack(self, commandID, deviceID, errorCode, responseSize, motorState, motorPos, encoderPos):
        """Repeat the field order to give better function signature"""
        self.data = pack(self.format, commandID, deviceID, errorCode, responseSize,
                            motorState, motorPos, encoderPos)
        self.unpack(self.data)


class StatusResponseFrame(SerialFrame):
    """
    ReponseFrame according to RokHari control implementation

 * @brief Response (13 bytes) has the following structure:
 *        byte 0: command ID
 *        byte 1: device ID
 *        byte 2: error code (0 == OK)
 *        bytes 3-6: command return values
 *        or
 *        bytes 3-12: status

    Which response is received can be determined by frame size (7 or 13)

    This class is for the status response frame
   """
    format = "!bbbbbiI"
    fields = [
            ('commandID', 0),
            ('deviceID', 0),
            ('errorCode', 0),
            ('responseSize', 13),
            ('motorState', 0),
            ('motorPos', 0),
            ('encoderPos', 0)
            ]

    def pack(self, commandID, deviceID, errorCode, responseSize, motorState, motorPos, encoderPos):
        """Repeat the field order to give better function signature"""
        self.data = pack(self.format, commandID, deviceID, errorCode, responseSize,
                            motorState, motorPos, encoderPos)
        self.unpack(self.data)

 class DataFrame(SerialFrame):
    """
    DataFrame model from RokHari control implementation
     Status response data layout:
 *        byte 0: command ID
 *        byte 1: device ID
 *        byte 2: error code (0 == OK)
 *        byte 3: total response size (13)
 *        byte 4: motorState_t
 *        bytes 5-8: motor position (int32_t)
 *        bytes 9-12: encoder position (uint32_t)
    """
 
    format = "!bbbbbiI"
    fields = [
            ('commandID', 0),
            ('deviceID', 0),
            ('errorCode', 0),
            ('responseSize', 13),
            ('motorState', 0),
            ('motorPos', 0),
            ('encoderPos', 0)
            ]

    def pack(self, commandID, deviceID, errorCode, responseSize, motorState, motorPos, encoderPos):
        """Repeat the field order to give better function signature"""
        self.data = pack(self.format, commandID, deviceID, errorCode, responseSize,
                            motorState, motorPos, encoderPos)
        self.unpack(self.data)
 
     
class DataFrame0:
    """
    DataFrame model from RokHari control implementation
     Status response data layout:
 *        byte 0: command ID
 *        byte 1: device ID
 *        byte 2: error code (0 == OK)
 *        byte 3: total response size (13)
 *        byte 4: motorState_t
 *        bytes 5-8: motor position (int32_t)
 *        bytes 9-12: encoder position (uint32_t)
    """
    format = "!bbbbbiI"
    def __init__(self):
        self.fields = [
            ('commandID', 0),
            ('deviceID', 0),
            ('errorCode', 0),
            ('responseSize', 13),
            ('motorState', 0),
            ('motorPos', 0),
            ('encoderPos', 0)
            ]
        (field_names, default_values) = zip(*self.fields)
        self.Record = namedtuple('Record', ' '.join(field_names), defaults = default_values)
        self.record = self.Record()

    def unpack(self, data):
        self.record = self.record._make(unpack(self.format, data))

    def pack(self, commandID, deviceID, errorCode, responseSize, motorState, motorPos, encoderPos):

        self.data = pack(self.format, commandID, deviceID, errorCode, responseSize,
                            motorState, motorPos, encoderPos)

        self.unpack(self.data)
    
    def __repr__(self):
        r = []
        r.append(f'{self.__class__.__name__} with format {self.format}')
        for field in self.record._fields:
            r.append("%s : %d" % (field, self.record.__getattribute__(field)))
        return '\n'.join(r)

dataFrameTestData = {}


def ut_SerialFrame():
    sf = SerialFrame()
    try:
        sf.pack(1,2)
    except RuntimeError:
        print("Overpacking serial frame exception detected")
    try:
        sf.pack(127)
    except RuntimeError:
        print("Fault : this should work")
    else:
        print(sf)

def ut_DataFrame0():
    df = DataFrame0()
    df.pack(1,2,0,13,10,11,100)
    print(df)
    data = pack(DataFrame.format, 10, 20, 0, 13, 20, 22, 200)
    dg = DataFrame0()
    dg.unpack(data)
    print(dg)

def ut_DataFrame():
    df = DataFrame()
    df.pack(1,2,0,13,10,11,100)
    print(df)
    data = pack(DataFrame.format, 10, 20, 0, 13, 20, 22, 200)
    dg = DataFrame()
    dg.unpack(data)
    print(dg)

class MockEdukitSTM32:
    def __init__(self):
        pass

class MockEdukitMARTe2:
    def __init__(self):
        pass



def main():
    ut_DataFrame0()
    ut_SerialFrame()
    ut_DataFrame()

if __name__ == '__main__':
    main()
