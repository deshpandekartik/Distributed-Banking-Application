#!/usr/bin/env python

import glob
import sys
import os
import hashlib
import logging
import socket   
import shutil
import random 
import SocketServer
from struct import unpack
from struct import pack
from threading import Thread
import time
from threading import Lock

sys.path.append('/home/vchaska1/protobuf/protobuf-3.5.1/python')
# Protobuf module for marshalling and unmarshalling messages
import bank_pb2

from bank import bank
from socket_pool import socket_pool
from chandy_lamport import chandy_lamport

logging.basicConfig(level=logging.DEBUG)

class Branch_Server(SocketServer.ThreadingTCPServer):
        def __init__(self, server_address, RequestHandlerClass,branch,host,port):
                SocketServer.ThreadingTCPServer.__init__(self,server_address,RequestHandlerClass)
                self.branchname = branch
                self.hostname = host
		self.portno = port


class BranchHandler(SocketServer.BaseRequestHandler):
	HOST = None
	PORT = None
	BRANCH_NAME =  None
	BANK_ob = bank()
	Socket_Pool_ob = socket_pool()
	Chandy_Lamport_ob = chandy_lamport()

	###########################
	# I am the one handling messages from different branches and controller
        def handle(self):
		self.BRANCH_NAME = self.server.branchname
                self.HOST = self.server.hostname
                self.PORT = self.server.portno

		self.BANK_ob.initialize(self.Socket_Pool_ob,self.Chandy_Lamport_ob,self.BRANCH_NAME)

               	self.Socket_Pool_ob.initialize(self.BRANCH_NAME)

              	self.Chandy_Lamport_ob.initialize(self.Socket_Pool_ob , self.BANK_ob)
		
                header = self.request.recv(4)
                message_length, = unpack('>I', header) #unpack always returns a tuple.

                message = self.request.recv(message_length)
                pb_message = bank_pb2.BranchMessage()
                pb_message.ParseFromString(message)
                print pb_message

                if pb_message.HasField("init_branch") :
			# INIT BRANCH MESSAGE
			balance = pb_message.init_branch.balance
                	list = pb_message.init_branch.all_branches
			self.BANK_ob.initBranch(balance, list)
		elif pb_message.HasField("transfer") : 
			# TRANSFER MONEY MESSAGE
			ReceivingBranch = self.request.recv(24)
			gotmoney = pb_message.transfer.money
			self.BANK_ob.ReceiveMoney(gotmoney, ReceivingBranch)
		elif pb_message.HasField("init_snapshot"):	
			# INIT SNAPSHOT MESSAGE
			snapshotnum = pb_message.init_snapshot.snapshot_id
			self.Chandy_Lamport_ob.initSnapshot(snapshotnum)
		elif pb_message.HasField("retrieve_snapshot"):
			# RETRIVE SNAPSHOT MESSAGE	
			snapshotnum = pb_message.retrieve_snapshot.snapshot_id
			snapshotmsg = self.Chandy_Lamport_ob.return_snapshot(snapshotnum)	
			message = snapshotmsg

			try:
		                x = pack('>I', len(message))
		                self.request.send(x)
		               	self.request.send(message)
			except:
				print "EXCEPTION ! Socket exception in handle. retrieve_snapshot message"
				sys.exit(0)

		elif pb_message.HasField("marker"):
			# MARKER MESSAGE
			snapshotnum = pb_message.marker.snapshot_id
			ReceivingBranch = self.request.recv(24)
			self.Chandy_Lamport_ob.ReceiveMarker(snapshotnum, ReceivingBranch)




if __name__ == '__main__':
        if len(sys.argv) != 3:
                print "Invalid Parameters: <Branch_Name> <Port>"
                sys.exit(0)
	else:
		branchName = sys.argv[1]
		PORT = sys.argv[2]
		HOST = socket.gethostbyname(socket.gethostname()) 

	print('Starting branch ' + branchName + ' on ' + str(HOST) + ':' + str(PORT) + '...')

	try:
		server = Branch_Server((HOST, int(PORT)), BranchHandler, branchName , HOST ,PORT)
		server.serve_forever()
	except:
		print "EXCEPTION ! Cannot connect to port."
		sys.exit(0)
