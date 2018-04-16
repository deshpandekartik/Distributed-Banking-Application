#!/usr/bin/env python

import glob
import sys
import os
import hashlib
import logging
import socket  
import shutil
import struct
from random import randint
from struct import unpack
from struct import pack
import random
import time

sys.path.append('/home/vchaska1/protobuf/protobuf-3.5.1/python')
# Protobuf module for marshalling and unmarshalling messages
import bank_pb2


from socket_pool import socket_pool

logging.basicConfig(level=logging.DEBUG)


class Controller:
	# INIT BRANCH
	list = []
	FILENAME = None
	TOTAL_BALANCE = 0
	snapshot_num = 1
	socket_obj = socket_pool()

        def __init__(self,total_balance, filename):
                self.log = {}
                self.TOTAL_BALANCE = total_balance
		self.FILENAME = filename
		self.socket_obj.initialize("Controller")

	###############################
	# Initialize all branches , pass them an initial amount and a list of all branches
	def initbranch(self):

		try:
			num_of_branches = sum(1 for line in open(self.FILENAME))
		except:
			print "EXCEPTION ! Error opening input file"
			sys.exit(0)

		if num_of_branches < 2 :
			print "EXCEPTION ! Input file should contain at least 2 branches"
			sys.exit(0)

		try:
			balance = int ( self.TOTAL_BALANCE ) / int ( num_of_branches )
		except:
			print "EXCEPTION ! Input file expty"
			sys.exit(0)
		
		with open(self.FILENAME, 'rU') as f:
			for line in f:
				branchname,ipaddress,portnumber = line.split(" ")

				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				HOST, PORT = ipaddress, int(portnumber)

	
				init_branch_msg = bank_pb2.InitBranch()
				init_branch_msg.balance = int(balance)

				with open(self.FILENAME, 'rU') as f:
					for line in f:
						branchname1,ipaddress1,portnumber1 = line.split(" ")
						pb_branch = init_branch_msg.all_branches.add()
						pb_branch.name = branchname1
						pb_branch.ip = ipaddress1
						pb_branch.port = int(portnumber1)
	
						branchUpdateMessage = bank_pb2.InitBranch.Branch()
						branchUpdateMessage.name = branchname
						branchUpdateMessage.ip = ipaddress
						branchUpdateMessage.port = int(portnumber)	
						

				pb_msg = bank_pb2.BranchMessage()
				pb_msg.init_branch.CopyFrom(init_branch_msg)
				encoded = pb_msg.SerializeToString()

				self.socket_obj.send_message_Protobuf(HOST , PORT, encoded)

                pb_message = bank_pb2.BranchMessage()
                pb_message.ParseFromString(encoded)
		self.list = pb_message.init_branch.all_branches
	
		list1 = []
                for item in self.list:
              		list1.append(item)
	
		self.list = list1

	##############################
	# Initiate a snapshot
	def StartSnapShot(self):
                
		while 1:
                        self.SendInitSnapshotMessage()
                        time.sleep(20)
                        self.SendRetriveSnapshotMessage(self.snapshot_num)
			time.sleep(4)
                        self.snapshot_num = self.snapshot_num + 1


	def SendInitSnapshotMessage(self):

		# randomly select a branch to initate a snapshot
		RandomBranch = random.choice(self.list)

		NextIp = RandomBranch.ip
               	NextPort = RandomBranch.port
              	NextBranch = RandomBranch.name

		init_snapshot_msg = bank_pb2.InitSnapshot()
             	init_snapshot_msg.snapshot_id = int(self.snapshot_num)

             	pb_msg = bank_pb2.BranchMessage()
         	pb_msg.init_snapshot.CopyFrom(init_snapshot_msg)
           	encoded = pb_msg.SerializeToString()

		ip = NextIp
             	port_num = NextPort
            	message = encoded

		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	               	sock.connect((ip, int(port_num)))
	             	x = pack('>I', len(message))
	            	sock.sendall(x)
	             	sock.sendall(message)
	             	header = sock.recv(4)
			sock.close()
		except:
			print "EXCEPTION ! Socket exception in SendInitSnapshotMessage"
			sys.exit(0)



	def SendRetriveSnapshotMessage(self, snapshot_num):
		total = 0
		print "---------------------------------------"
		print "snapshot_id:" + str(snapshot_num)

		flag = 0
		for item in self.list:
			NextIp = item.ip
	                NextPort = item.port
        	        NextBranch = item.name

	                retrive_snapshot_msg = bank_pb2.RetrieveSnapshot()
	                retrive_snapshot_msg.snapshot_id = int(snapshot_num)

        	        pb_msg = bank_pb2.BranchMessage()
                	pb_msg.retrieve_snapshot.CopyFrom(retrive_snapshot_msg)
                	encoded = pb_msg.SerializeToString()

			ip = NextIp
			port_num = NextPort
			message = encoded

			try:
		                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	        	        sock.connect((ip, int(port_num)))
	        	        x = pack('>I', len(message))
	        	        sock.sendall(x)
	        	        sock.sendall(message)
				header = sock.recv(4)

				while header == "removethios":
					sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					sock.connect((ip, int(port_num)))
					x = pack('>I', len(message))
					sock.sendall(x)
					sock.sendall(message)
					header = sock.recv(4)

				message_length, = unpack('>I', header)
				message = sock.recv(message_length)
				pb_message = bank_pb2.BranchMessage()
				pb_message.ParseFromString(message)		
				sock.close()
			except:
				print "EXCEPTION ! Socket exception in SendRetriveSnapshotMessage"
				sys.exit(0)

			list123 = []
			for item1 in self.list:
				if item1.name != NextBranch:
					list123.append(item1)


			channel_state = ""
			for item , chanstat in zip(list123, pb_message.return_snapshot.local_snapshot.channel_state) :
				if int(chanstat) != 0 :
					flag = 1

				channel_state = channel_state + str(item.name) + " -> " + str(NextBranch) + " : " + str(chanstat) + " "
				total = total + int(chanstat)

			branchname = NextBranch
			print branchname + " : " + str(pb_message.return_snapshot.local_snapshot.balance) + " , " + channel_state

			total = total + pb_message.return_snapshot.local_snapshot.balance

		print "Total Balance " + str(total)

if __name__ == '__main__':
	if len(sys.argv) != 3:
	        print "Invalid Parameters: <Total Balanace> <branches.txt>"
	        sys.exit(0)
	else:
	        totalbalance = sys.argv[1]
	        filename = sys.argv[2]


	handler = Controller(totalbalance,filename)
	handler.initbranch()
	time.sleep(3)
	handler.StartSnapShot()
