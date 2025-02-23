#!/usr/bin/env python3
#
"""
Python models of the UCLA Edukit rotary inverted pendulum
and the associated STM32 embedded rotary encoder/motor 
sensor and actuator systems
"""
import pdb
import serial
import sys

from struct import calcsize
from time import sleep, time
from invertedPendulum import CommandFrame, CommandResponseFrame, StatusResponseFrame

def unhexlify(s):
    s = re.sub(r"[^0-9a-fA-F]", "", s)
    return binascii.unhexlify(s)

def hexlify(s):
    return " ".join(bytes([c]).hex().upper() for c in s)

class SerialPort:
    def __init__(self, port = '/dev/ttyUSB0', baud = 230400, verbose = False):
        self.port = port
        #self.baud = 9600
        #self.baud = 115200
        self.baud = baud
        self.timeout = 10
        self.ser = serial.Serial(port = self.port, baudrate = self.baud)
        #pdb.set_trace()
        self.ser.timeout = 1
        self.iterations = 5
        self.verbose = verbose
        sleep(0.2)

    def write(self, bytes):
        txb = self.ser.write(bytes)
        self.ser.flush()
        # TODO: apply logging, not print
        if self.verbose:
            tx_bytes = hexlify(bytes)
            print(f"TX {txb:03d} {tx_bytes:<60}")
        return txb
    
    def read(self, rxsize):
        rxb = 0
        rxbuf = bytearray()
        while rxb < rxsize and self.ser.inWaiting() > 0:
            rxbuf.extend(self.ser.read(1))
            rxb+=1
        if self.verbose:
            print(f"RX {rxb:03d} {hexlify(rxbuf):<60}")
        return rxbuf

    def echo_test(self):
        iterations = self.iterations
        ipsm = InvPendStatusMonitor()
        buf = bytearray()
        out = ipsm.reset_cmd.data
        while iterations > 0:
            txb = self.ser.write(out)
            self.ser.flush()
            print(f"TX : sent {txb} bytes")
            sleep(0.01)
            #pdb.set_trace()d
            while self.ser.inWaiting() > 0:
                buf.extend(self.ser.read(1))
            if len(buf) > 0:
                print("Sent    : %s" % hexlify(out))
                print("Received: %s" % hexlify(buf))
            else:
                print(f"No data received {iterations}\n")
            iterations-=1


class SerialTransmitter:
    def __self__(init):
        pass


class SerialReceiver:
    def __self__(init):
        pass

class MockEdukitSTM32:
    """
    An object to model the behaviour of the EdukitSTM32 
    """
    def __init__(self, port = '/dev/ttyUSB2', baud = 230400, verbose = False):
        self.serial_port = SerialPort(port, baud)
        self.verbose = verbose
        self.status_response = StatusResponseFrame()
        self.command = CommandFrame()

    def handle_commands(self):
        loops = 0
        handled = 0
        while True:
            loops+=1
            expected_bytes = calcsize(self.command.format)
            rx_data = self.serial_port.read(expected_bytes)
            commandID = None
#            pdb.set_trace()
            if len(rx_data) != expected_bytes:
                log_msg=f"Mock : {len(rx_data)} data != {expected_bytes}: sleep(1) {loops:<10d}"
                sleep(1)
            else:
                self.command.unpack(rx_data)
                commandID = self.command.record.commandID
                handled+=1
                log_msg=f"Mock : command {commandID}: sleep(1) {handled}/{loops:<10d}"
            if self.verbose: print(log_msg)
            if commandID is not None:
                if commandID == 252:
                    # reset command : no response
                    pass
                elif commandID == 253:
                    # status command : create and send status
                    self.status_response.pack(commandID, 1, 0, 13, 10, 20, 30)
                    self.transceive(self.status_response)
                    pass
                elif commandID == 254:
                    # apply acceleration command : no response
                    pass
                else:
                    # Other command
                    pass

    def status(self):
        status_response = StatusResponseFrame()
        data = self.transceive(self.status_cmd, status_response)

    def transceive(self, cmd, response_frame = None):
        """
        Send a command and read back the response.
        This will not work in echo mode as we require a real response.
        """
        txb = self.serial_port.write(cmd.data)
        if self.verbose: print(f"sent response of {txb} bytes {len(cmd.data)}")
        if response_frame is None: return None
        rx_data = self.serial_port.read(calcsize(response_frame.format))
        response_frame.pack(rx_data)
        return rx_data
   
    def __repr__(self):
        r = []
        r.append("%s" % self.reset_cmd)
        r.append("%s" % self.reset_cmd.data)
        return '\n'.join(r)


class InvPendStatusMonitor:
    """
    An object to monitor the status of the system actively
    """
    def __init__(self, port = '/dev/ttyUSB0', baud = 230400):
        self.serial_port = SerialPort(port, baud)
        self.reset_cmd = CommandFrame()
        self.reset_cmd.pack(252, 1, 0)
        self.status_cmd = CommandFrame()
        self.status_cmd.pack(253, 1, 0)

    def reset(self):
        self.transceive(self.reset_cmd)

    def status(self):
        status_response = StatusResponseFrame()
        data = self.transceive(self.status_cmd, status_response)

    def transceive(self, cmd, response_frame = None):
        """
        Send a command and read back the response.
        This will not work in echo mode as we require a real response.
        """
        invalid_frames=0
        null_frames = 0
        txb = self.serial_port.write(cmd.data)
        if response_frame is None: return None
        rx_bytes = 0
        expected_bytes = calcsize(response_frame.format)
        while(rx_bytes == 0):
            rx_data = self.serial_port.read(expected_bytes)
            rx_bytes = len(rx_data)
            if rx_bytes == 0:
                null_frames+=1
                sleep(1)
                print(f"{null_frames} null frames {invalid_frames} invalid_frames")
            elif rx_bytes == expected_bytes:
                response_frame.unpack(rx_data)
                print(f"decoded frame {response_frame}")
            else:
                invalid_frames+=1
        return rx_data
   
    def __repr__(self):
        r = []
        r.append("%s" % self.reset_cmd)
        r.append("%s" % self.reset_cmd.data)
        return '\n'.join(r)

def ut():
    cfII = CommandFrame([('parA', 'I', 3.14), ('parB', 'i', 6.28)])
    print(cfII)

# Ref https://stackoverflow.com/questions/24440143/how-do-i-make-the-pyserial-loopback-work
def serialDataPump():
    ser = serial.serial_for_url('loop://', timeout=1)
    testCtr = 0;
    while True: 
        ser.write(bytes("Test\n", encoding='ascii'))
        time.sleep(1)
        testCtr += 1

def serialDataTestRcv():
    ser = serial.serial_for_url('loop://', timeout=1)
    while True: 
        line = ser.readline()
        sys.stdout.write('received' + str(line))

def testSerMain():
    thread1 = Thread(target = serialDataPump)
    thread2 = Thread(target = serialDataTestRcv)
    thread1.start()
    thread2.start()
    thread1.join()
    time.sleep(2)

def main_was():
   ipsm = InvPendStatusMonitor()
   print(ipsm) 
   usb0 = SerialPort(115200)
   usb0.echo_test()
    

def reset():
    ipsm = InvPendStatusMonitor('/dev/ttyUSB1', 115200)
    ipsm.reset()

def tx_status_request():
    ipsm = InvPendStatusMonitor('/dev/ttyUSB1', 115200)
    ipsm.status()

def mock():
    mock = MockEdukitSTM32('/dev/ttyUSB2', 115200, verbose=True)
    mock.handle_commands()


def fullMockTest():
    threadEdukit = Thread(target = mock32)
    threadMarte2 = Thread(target = tx_status_request)
    threadEdukit.start()
    threadMarte2.start()
    thread1.join()
    time.sleep(2)

def main_test():
    usb0 = SerialPort(115200)
    usb0.echo_test()

def main(args):    # TODO: refactor the CLI
    if len(args) == 0:
        main_test()
    role = args[0]
    if role == "status":
        tx_status_request()
    elif role == "reset":
        reset()
    elif role == "mock":
        mock()
    elif role == "full":
        fullMockTest()
    else:
        print(f"No such role: {role}")

if __name__ == '__main__':
    #print(len(sys.argv))
    main(sys.argv[1:])