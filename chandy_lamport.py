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

class chandy_lamport:

	initialization_status = False
	snapshot_history_list = []
	channel_state = {}
	MARKER_MESSAGE_CHANNEL_STATE = {}
	MARKER_MESSAGE_BALANCE = {}

        ##############################
        # Initialize objects
        def initialize( self,socket_pool_param, bank_param):
                SOCKET_POOL = socket_pool_param
                BANK = bank_param
                self.initialization_status = True


        ##############################
        # I am the one initailizing snapshot because controller asked me to.
        def initSnapshot ( self, snapshot_num ):

                self.BANK.money_transfer_status = False

                time.sleep(2)

                # first record initial state
                self.snapshot_history_list.append(snapshot_num)
                self.MARKER_MESSAGE_BALANCE[snapshot_num] = self.BANK.Account_Balance
                for item in self.BANK.all_branches:
                        # start recording on incomming channels
                        self.MARKER_MESSAGE_CHANNEL_STATE[ snapshot_num , item.name ] = (True , 0 )

                # send marker's to all branch's
                thread = Thread(target = self.SendMarkers,args=(snapshot_num,))
                thread.daemon = True
                thread.start()


        #############################
        # Send Marker's to all branches
        def SendMarkers ( self, snapshot_num ):

                self.BANK.money_transfer_status = False
                # for loop to send marker message to all branches
                for item in self.BANK.all_branches:

                        NextIp = item.ip
                        NextPort = item.port
                        NextBranch = item.name

                        marker_msg = bank_pb2.Marker()
                        marker_msg.snapshot_id = int(snapshot_num)

                        pb_msg = bank_pb2.BranchMessage()
                        pb_msg.marker.CopyFrom(marker_msg)
                        encoded = pb_msg.SerializeToString()

                        SOCKET_POOL.send_message_Protobuf(NextIp, NextPort, encoded)

                self.BANK.money_transfer_status = True


        ###############################################
        # Handle receive marker message
        def ReceiveMarker(self, snapshot_num, ReceivingBranch):

                self.BANK.money_transfer_status = False

                if snapshot_num not in self.snapshot_history_list:
                        ## first marker messsage to me

                        self.snapshot_history_list.append(snapshot_num)

                        # first record my own state
                        self.MARKER_MESSAGE_BALANCE[snapshot_num] = BALANCE

                        for item in self.BANK.all_branches:
                                # start recording on other channels
                                self.MARKER_MESSAGE_CHANNEL_STATE[ snapshot_num , item.name ] = (True , 0 )

                        # mark the channel from which marker message was received as empty
                        self.MARKER_MESSAGE_CHANNEL_STATE[ snapshot_num , ReceivingBranch ] = (False , 0 )

                        # send markers to all branches
                        self.SendMarkers(snapshot_num)
                else:
                        # not the first marker message

                        # mark all messages received on this channel state
                        amount = self.MARKER_MESSAGE_CHANNEL_STATE[snapshot_num , ReceivingBranch ][1]

                        # stop recording on channel's
                        self.MARKER_MESSAGE_CHANNEL_STATE[snapshot_num , ReceivingBranch ] = (False , amount )

                self.BANK.money_transfer_status = True


        ##########################################
        # controller calling to retrive a snapshot
        def return_snapshot(self,snapshot_num):

                # pack the message to be sent to controller '

                return_snapshot_msg = bank_pb2.ReturnSnapshot.LocalSnapshot()
                return_snapshot_msg.snapshot_id = int(snapshot_num)
                return_snapshot_msg.balance = int(self.MARKER_MESSAGE_BALANCE[snapshot_num])

                for item in self.BANK.all_branches:
                        amount = self.MARKER_MESSAGE_CHANNEL_STATE[snapshot_num , item.name ][1]

			# Critical section, BANK.Account_Balance accessed by multiple threads
			with BANK.critical_section_lock:
				BANK.Account_Balance = BANK.Account_Balance + amount 

                        return_snapshot_msg.channel_state.append(int(amount))


                pb_msg1 = bank_pb2.ReturnSnapshot()
                pb_msg1.local_snapshot.CopyFrom(return_snapshot_msg)

                pb_msg = bank_pb2.BranchMessage()
                pb_msg.return_snapshot.CopyFrom(pb_msg1)
                encoded = pb_msg.SerializeToString()

                return encoded

	
