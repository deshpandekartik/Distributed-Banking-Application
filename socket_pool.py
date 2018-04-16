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

# Protobuf module for marshalling and unmarshalling messages
import bank_pb2

class socket_pool:
	SOCKBUFFERSIZE = 10000
	initialization_status = False
	my_branch_name = None

	##############################
        # Initialize objects
        def initialize( self,branch_param):
                self.my_branch_name = branch_param
                self.initialization_status = True


	##############################
	# encoding and sending messages via sockets
	def send_message_Protobuf(self, ip, port_num, message):
		#try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect((ip, port_num))
			x = pack('>I', len(message))
			sock.sendall(x)
			sock.sendall(message)
			sock.sendall(self.my_branch_name)
			server_response = sock.recv(self.SOCKBUFFERSIZE)
			sock.close()
			if server_response == "" :
	                        # ERROR ! Empty response from server, probably the server did not want to send anything
	                        return None
			else:
				return server_response
		#except:
                        #print "EXCEPTION ! Socket exception in send_message_Protobuf"
                        #sys.exit(0)
