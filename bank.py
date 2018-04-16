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

logging.basicConfig(level=logging.DEBUG)

class bank:
	initialization_status = False
	money_transfer_status = False
	Account_Balance = 0
	all_branches = []
	critical_section_lock = Lock()
	BRANCH_NAME = ""
	
	##############################
	# Initialize objects
	def initialize( self,socket_pool_param, Marker_param,name):
		SOCKET_POOL = socket_pool_param
		CHANDY_MARKER = Marker_param
		self.initialization_status = True
		BRANCH_NAME = name


        ##############################
        # Controller asked me to initialize branch with an ammount
        def initBranch (self, balance_param, branch_list):

		for item in branch_list:
                        if item.name != self.BRANCH_NAME:
                                self.all_branches.append(item)

                self.Account_Balance = balance_param
                print "Branch Initialized ---"

                # start sending money to other branches ( as a daemon )
                thread = Thread(target = self.TransferMoney)
                thread.daemon = True
                thread.start()


	############################
        # Running as a daemon to transfer money to other branches at different intrevals
        def TransferMoney(self):
        	while 1:
        		if self.money_transfer_status == True:

                                RandomBranch = random.choice(self.all_branches)

                               	NextIp = RandomBranch.ip
                            	NextPort = RandomBranch.port
                            	NextBranch = RandomBranch.name

                             	amount = (int) ((random.randint(1,4) * self.Account_Balance) /100)

                           	transfer_money_msg = bank_pb2.Transfer()
                              	transfer_money_msg.money = int(amount)
                            	pb_msg = bank_pb2.BranchMessage()
                            	pb_msg.transfer.CopyFrom(transfer_money_msg)
                           	encoded = pb_msg.SerializeToString()

                           	server_response = self.SOCKET_POOL.send_message_Protobuf(NextIp, NextPort, encoded)

                         	# Critical section, self.Account_Balance accessed by multiple threads
                         	with self.critical_section_lock:
                        		self.Account_Balance = self.Account_Balance - amount
                             	time.sleep(random.randint(1,5))
	
        ################################
        # Receive money from other branches
        def ReceiveMoney ( self, receivedmoney, ReceivingBranch ):

                if len(self.CHANDY_MARKER.snapshot_history_list) > 0 :
                        snapshot_num = self.CHANDY_MARKER.snapshot_history_list[-1]

                        # check if incomming message needs to be recorded
                        if self.CHANDY_MARKER.MARKER_MESSAGE_CHANNEL_STATE[ snapshot_num , ReceivingBranch ][0] == True and self.CHANDY_MARKER.MARKER_MESSAGE_BALANCE != 0:
	
				# Critical section, self.Account_Balance accessed by multiple threads
				with self.critical_section_lock:
                                       self.Account_Balance = self.Account_Balance + int(self.CHANDY_MARKER.MARKER_MESSAGE_CHANNEL_STATE[ snapshot_num , ReceivingBranch ][1])
                                self.CHANDY_MARKER.MARKER_MESSAGE_CHANNEL_STATE[snapshot_num , ReceivingBranch ] = (True , receivedmoney )
			else:
			
		                #print "-----------------------------------------------"
        		        #print "Recorded Balance " + str(MARKER_MESSAGE_self.Account_Balance)
                		#print self.MARKER_MESSAGE_CHANNEL_STATE
                		#print "Now balance " + str(self.Account_Balance) + " status " + str(money_transfer_status)
        	       	 	#print "-----------------------------------------------"
	
        	        	# Critical section, self.Account_Balance accessed by multiple threads
        		        with self.critical_section_lock:
                 		       self.Account_Balance = self.Account_Balance + receivedmoney
