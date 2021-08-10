#!/usr/bin/python3
"""
DC29 Human Badge Fuzzer
Used to help level up badges and get to the next part of the puzzle

To run:
    plug in the badge, make sure in USB mode. 
    Find the serial port the badge is attached to run:
        dmesg | grep tty
    Make sure your user can access port:
        sudo chmod a+rw /dev/ttyACM0
    Run program with:
        python3 badgefuzz.py - /dev/ttyACM[??] -n [number of max signals]

"""

import argparse
from serial import Serial 
import random
from time import sleep
import re

# gloabals
chars = 'ABSCEF0123456789'
hashReg = re.compile('[A-F\d]{32}')
sigReg = re.compile('.*Shared the Signal: (\d+)')

# wrapper for serial write
def serialWrite(s, msg):
    s.write(msg.encode())
    sleep(0.1)
    s.flush()
    
# wrapper for serial read
def serialRead(s):
    result = b''
    char = b' '
    while char:
        char = s.read()
        sleep(0.01)
        result += char
        
    if 'ENTER' in result.decode():
        serialWrite(s,'\r\n')
        result += serialRead(s).encode()
        
    # try to clean up stop characters
    result = result.decode()
    result = result.replace('\x00','')
    return result

# create spoofed response string
def makeResponse(request):
    result = ''.join(random.choices(chars,k=2))
    result += request[2:4]
    result += ''.join(random.choices(chars,k=4))
    result += request[8:10]
    result += ''.join(random.choices(chars,k=6))
    result += request[16:21] + '3'
    result += ''.join(random.choices(chars,k=10))
    
    return result


if __name__ == '__main__':
    # command line arguments accepted
    parser = argparse.ArgumentParser(description='fuzz the DC29 badge')
    parser.add_argument('-s', action='store', dest='ttyport', type=str, default='/dev/ttyACM0', help='serial port')
    parser.add_argument('-n', action='store', dest='numSignals', type=int, default=20, help='number of max signals')
    args = parser.parse_args()

    with Serial(args.ttyport, 115200, timeout=5) as s:
        sleep(1)
        state = 0
        signalCount = 0
        while signalCount < args.numSignals:
            
            # Get menu - this can take some time.
            if state == 0:
                # menu reguarly fails to show without prompting
                # this hack is safe enough.
                # script will work without getting menu, just a nice-to-have
                serialWrite(s, '\r\n') 
                resp = serialRead(s)
                print(resp)
                match = sigReg.search(resp)
                if match:
                    signalCount = int(match[1])
                    if signalCount > args.numSignals:
                        break
                state = 1
            
            # Get request string 
            # only need to run this once
            if state == 1:
                serialWrite(s,'4')
                resp = serialRead(s)
                print(resp)
                if hashReg.search(resp):
                    request = hashReg.search(resp)[0]
                    state = 2
            
            # Get response
            if state == 2:                
                serialWrite(s,'5')
                resp = serialRead(s)
                print(resp)                
                response = makeResponse(request) + '\r\n'
                serialWrite(s,response)
                resp = serialRead(s)
                print(resp)
                match = sigReg.search(resp)
                if match:
                    signalCount = int(match[1])
                state = 2
