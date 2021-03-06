# file server.py 
# Alexandre Plante, 7908179, Anton Claes, 0300042110
# CEG4188 Assignment #1
# october 8th, 2017 
import sys
import socket
import thread
import utils
import signal

#global variable storing the clients currently connected to the server
clients = {}
# global variable storing the channels for the server
channels = {}

# allows to give a unique ID to each client
# this way two clients can have the same name
conn_number = 0

class Client:
	def __init__(self, csock, addr, name):
		global conn_number
		self.csock = csock
		self.addr = addr
		self.name = name
		self.channel = None
		self.id = conn_number
		conn_number += 1
	def sendMessage(self, message):
		# this sends the given message to the current client
		try:
			self.csock.send(message)
		except:
			print("Unable to send message to : " + self.name)
			logOutAll(self)


class Channel:
	def __init__(self, name):
		self.name = name
		self.clients = {} # no clients at first
	def addClient(self, client):
		print("Adding client " + client.name + " to channel")
		# broadcast the joins of clients
		self.broadcast(utils.SERVER_CLIENT_JOINED_CHANNEL.format(client.name).ljust(utils.MESSAGE_LENGTH), client)
		self.clients[client.id] = client
	def logOut(self, client):
		#log out only if logged in (prevents inaccurate loggout messages)
		if client.id in self.clients.keys():
			# broadcast the leaving of the client
			self.broadcast(utils.SERVER_CLIENT_LEFT_CHANNEL.format(client.name).ljust(utils.MESSAGE_LENGTH), client)
			# This will log clients out of the channel based on name only
			# Clients with duplicate names will be logged out at the same time
			self.clients.pop(client.id, None)

	def broadcast(self, message, srcClient):
		# this broadcasts the given message to all clients logged into the channel
		# do not forward to sender client
		# this can throw an exception if logging out while broadcasting
		try:
			for c in self.clients:
				if self.clients[c] is not srcClient:
					self.clients[c].sendMessage(message)
		except:
			pass
			
if len(sys.argv) != 2:
	print("Invalid number of arguments\nUse : python2.7 server.py PORT")
	quit()

# functions that allows for message buffering, returns only after
# having received 200 characters
def bufferMessage(socket):
	msg = ""
	while len(msg) < 200:
		tmp = socket.recv(utils.MESSAGE_LENGTH - len(msg)).decode()
		# empty recv means client disconnected 
		# "forward emptyness" to allow for disconection detection
		if tmp == "":
			return ""
		else:
			msg += tmp
	return msg

# function that will be run in one thread per client
def clientThread(client):
	global channels
	global clients
	running = True
	# loop that waits for client to send messages
	while True:
		# receive client data (max utils.MESSAGE_LENGTH chars). Do not perform length check as this will be done
		# on client side, and ctrl messages may be shorter
		ctrl = bufferMessage(client.csock)
		if ctrl == "": # empty message, client disconnected
			logOutAll(client)
			running = False
			client.csock.close()
			break

		if ctrl[0] == '/':	# control message
			ctrl = ctrl.strip() # get rid of the padding for the control messages
			# test control type
			# print("ctrl = " + ctrl)
			if ctrl[:len("/join")] == "/list":
				# return a message containing a list of channels
				# must be utils.MESSAGE_LENGTH char aligned like every message
				if len(channels) != 0:
					chList = reduce(lambda a, b: a + "\n" + b, channels.keys())
					printChannels()
				else:
					chList = " "

				# add padding spaces until chList is utils.MESSAGE_LENGTH characters aligned
				while len(chList)%utils.MESSAGE_LENGTH != 0:
					chList += " "
				# send the result
				client.sendMessage(chList.encode())

			elif ctrl[:len("/join")] == "/join":
				# check for channel availability
				chName = ctrl[len("/join "):]
				if chName.strip() == "":
					# no name channel
					# print("No channel name given")
					client.sendMessage(utils.SERVER_JOIN_REQUIRES_ARGUMENT.ljust(utils.MESSAGE_LENGTH))
				else:
					# print("chName = " + chName)
					if chName in channels.keys():
						# Log out of all channels
						logOutAll(client)
						# log in
						channels[chName].addClient(client)
					else:
						#reply with an error message
						client.sendMessage(utils.SERVER_NO_CHANNEL_EXISTS.format(chName).ljust(utils.MESSAGE_LENGTH))
						# print("Channel does not exist")


			elif ctrl[:len("/create")] == "/create":
				# create new channel, if no name provided reply with error message
				if ctrl[len("/create"):].strip() == "": # no channel name
					client.sendMessage(utils.SERVER_CREATE_REQUIRES_ARGUMENT.ljust(utils.MESSAGE_LENGTH))
					# print("Unable to create : invalid name")
				else:
					# create corresponding channel
					#assuming there is a space between "/create" and channel name
					chName = ctrl[len("/create "):]
					# check for already existing key
					if chName in channels.keys():
						client.sendMessage(utils.SERVER_CHANNEL_EXISTS.format(chName).ljust(utils.MESSAGE_LENGTH))
						# print("Channel already exists")
					else:
						# print("Creating channel " + chName)
						channels[chName] = Channel(chName)
						#immediately add client to channel
						logOutAll(client)
						channels[chName].addClient(client)

			else:
				# send back invalid control message message
				# print("Invalid ctrl message")
				client.sendMessage(utils.SERVER_INVALID_CONTROL_MESSAGE.format(ctrl).ljust(utils.MESSAGE_LENGTH))

		else: # normal message to be broadcasted to the channel
			# broadcast the message to all in the channel	
			# find the channel client is logged in
			logged = False
			for e in channels:
				if client.id in channels[e].clients:
					channels[e].broadcast(ctrl, client)
					logged = True # check if logged in a channel
			if not logged:
				print("Discarding data from non logged client " + client.name + ":", client.id)
				client.sendMessage(utils.SERVER_CLIENT_NOT_IN_CHANNEL.ljust(utils.MESSAGE_LENGTH))

#debug
def printChannels():
	for k in channels.keys():
		print k + " : ",
		if len(channels[k].clients.keys()) != 0:
			print(reduce(lambda a, b: str(a) + "," + str(b), channels[k].clients.keys()))
		else:
			print

# log out of all channels, either when joining or when creating
def logOutAll(user):
	# this will log all users with same name out of all channels	
	for e in channels:
		channels[e].logOut(user)


# disconnects all clients 
def disconnectAll():
	for e in clients:
		clients[e].csock.close()
	s.close()

# actually start the server's listenning 

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# for fast debug, allow reuse of port during TIME_WAIT
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

s.bind(('localhost', int(sys.argv[1])))

# max 10 connections between 2 accepts()
s.listen(10)

while True:
	try:
		csock, caddr = s.accept()
	except: 
		# exceptions caused here are due to system signals (SIGINT)
		# probably the server being quit
		# must properly disconnect all clients
		disconnectAll()
		quit()


	# receive first message to get client name
	name = bufferMessage(csock).strip()
	print("Client " + name + " connected.")
	# add client to current client list
	newClient = Client(csock, caddr, name)
	clients[conn_number] = newClient
	# start a thread for clients incomming messages
	thread.start_new_thread(clientThread, (newClient,))

