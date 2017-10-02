import sys
import socket
import thread
import utils



#global variable storing the clients currently connected to the server
clients = {}
# global variable storing the channels for the server
channels = {}

class Client:
	def __init__(self, csock, addr, name):
		self.csock = csock
		self.addr = addr
		self.name = name
		self.channel = None
	def sendMessage(self, message):
		# this sends the given message to the current client
		self.csock.send(message)


class Channel:
	def __init__(self, name):
		self.name = name
		self.clients = {} # no clients at first
	def addClient(self, client):
		print("Adding client " + client.name + " to channel")
		# broadcast the joins of clients
		self.broadcast(utils.SERVER_CLIENT_JOINED_CHANNEL.format(client.name).ljust(utils.MESSAGE_LENGTH))
		self.clients[client.name] = client
	def logOut(self, client):
		#log out only if logged in (prevents inaccurate loggout messages)
		if client.name in self.clients.keys():
			# broadcast the leaving of the client
			self.broadcast(utils.SERVER_CLIENT_LEFT_CHANNEL.format(client.name).ljust(utils.MESSAGE_LENGTH))
			# This will log clients out of the channel based on name only
			# Clients with duplicate names will be logged out at the same time
			self.clients.pop(client.name, None)

	def broadcast(self, message):
		# this broadcasts the given message to all clients logged into the channel
		for c in self.clients:
			clients[c].sendMessage(message)

if len(sys.argv) != 2:
	print("Invalid number of arguments\nUse : python2.7 server.py PORT")
	quit()

# function that will be run in one thread per client
def clientThread(client):
	global channels
	global clients
	# loop that waits for client to send messages
	while True:
		# receive client data (max utils.MESSAGE_LENGTH chars). Do not perform length check as this will be done
		# on client side, and ctrl messages may be shorter
		ctrl = client.csock.recv(utils.MESSAGE_LENGTH).decode()
		if len(ctrl) == 0:	# discard empty messages
			continue

		if ctrl[0] == '/':	# control message
			# test control type
			print("ctrl = " + ctrl)
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
				client.csock.send(chList.encode())

			elif ctrl[:len("/join")] == "/join":
				# check for channel availability
				chName = ctrl[len("/join "):]
				if chName.strip() == "":
					# no name channel
					print("No channel name given")
					client.csock.send(utils.SERVER_JOIN_REQUIRES_ARGUMENT.ljust(utils.MESSAGE_LENGTH))
				else:
					print("chName = " + chName)
					if chName in channels.keys():
						print("Logging " + client.name + " in " + chName)
						# Log out of all channels
						logOutAll(client)
						# log in
						channels[chName].addClient(client)
					else:
						#reply with an error message
						client.csock.send(utils.SERVER_NO_CHANNEL_EXISTS.format(chName).ljust(utils.MESSAGE_LENGTH))
						print("Channel does not exist")


			elif ctrl[:len("/create")] == "/create":
				# create new channel, if no name provided reply with error message
				if ctrl[len("/create"):].strip() == "": # no channel name
					client.csock.send(utils.SERVER_CREATE_REQUIRES_ARGUMENT.ljust(utils.MESSAGE_LENGTH))
					print("Unable to create : invalid name")
				else:
					# create corresponding channel
					#assuming there is a space between "/create" and channel name
					chName = ctrl[len("/create "):]
					# check for already existing key
					if chName in channels.keys():
						client.csock.send(utils.SERVER_CHANNEL_EXISTS.format(chName).ljust(utils.MESSAGE_LENGTH))
						print("Channel already exists")
					else:
						print("Creating channel " + chName)
						channels[chName] = Channel(chName)
						#immediately add client to channel
						logOutAll(client)
						channels[chName].addClient(client)

			else:
				# send back invalid control message message
				print("Invalid ctrl message")
				client.csock.send(utils.SERVER_INVALID_CONTROL_MESSAGE.format(ctrl).ljust(utils.MESSAGE_LENGTH))

		else: # normal message to be broadcasted to the channel
			# broadcast the message to all in the channel	
			# find the channel client is logged in
			logged = False
			for e in channels:
				if client.name in channels[e].clients:
					channels[e].broadcast(ctrl)
					logged = True # check if logged in a channel
			if not logged:
				print("Discarding data from non logged client " + client.name)
				client.csock.send(utils.SERVER_CLIENT_NOT_IN_CHANNEL.ljust(utils.MESSAGE_LENGTH))

#debug
def printChannels():
	for k in channels.keys():
		print k + " : ",
		if len(channels[k].clients.keys()) != 0:
			print(reduce(lambda a, b: a + "," + b, channels[k].clients.keys()))
		else:
			print

# log out of all channels, either when joining or when creating
def logOutAll(user):
	# this will log all users with same name out of all channels
	for e in channels:
		channels[e].logOut(user)




# actually start the server's listenning 

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind(('localhost', int(sys.argv[1])))

s.listen(10)

while True:
	csock, caddr = s.accept()
	# receive first message to get client name
	name = csock.recv(utils.MESSAGE_LENGTH)
	print("Client " + name + " connected.")
	# add client to current client list
	clients[name] = Client(csock, caddr, name)
	# start a thread for clients incomming messages
	thread.start_new_thread(clientThread, (clients[name],))

