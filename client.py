# file client.py 
# Alexandre Plante, Anton Claes
# CEG4188 Assignment #1
# october 8th, 2017
import socket
import sys
import utils
import thread
import signal

# required args : clientName IP Port
if len(sys.argv) != 4:
	print("Invalid number of args.\nUse : python client.py NAME IP PORT")
	quit()

# this handle connection errors. Quits upon error with adequate err. msg
try:
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((sys.argv[2], int(sys.argv[3])))
except socket.error:
	print(utils.CLIENT_CANNOT_CONNECT.format(sys.argv[2], sys.argv[3]))
	quit()

name = sys.argv[1]

# name is the first message. 
# ljust built-in padding function (left-justify)
s.send(name.ljust(200).encode())

# this allows to stop the 2 threads upon server disconnection
running = True

# this function's role is to receive the data, buffer it if needed and display it
# this function will be run in a separate thread to allow for data sending at the same
def receiverThread():
	global running
	while running:
		# handles the case were server closes the connection properly
		# does not handle the server quitting without closing socket
		try:	
			data = s.recv(200);
		except:
			print(utils.CLIENT_SERVER_DISCONNECTED.format(sys.argv[2], sys.argv[3]))
			s.close()
			running = False
			sys.exit(0)
		if data == "": # empty string : also proof of deconnection
			print(utils.CLIENT_SERVER_DISCONNECTED.format(sys.argv[2], sys.argv[3]))
			s.close()
			running = False			
			sys.exit(0)

		# buffering on the client side in case there was a spliting server (unlikely)
		while len(data) < 200:
			data += s.recv(200 - len(data))

		# wipes "[ME]" and prints received message at the same time
		print(utils.CLIENT_WIPE_ME + "\r" + data.decode().strip())
		# reset the terminal "[ME]" output
		print utils.CLIENT_MESSAGE_PREFIX,
		sys.stdout.flush()

# start receiving thread before we go for sending loop
thread.start_new_thread(receiverThread, ())

while running:
	# .strip() prevents a graphical bug (']' not wiped)
	text = raw_input(utils.CLIENT_MESSAGE_PREFIX).strip()

	if len(text) == 0: # discards empty messages (pressing enter without sending text)
		continue
	if text[0] != '/':
		# add client name now, this will allow for coherent padding
		text = "[" + name + '] ' + text
	text = text.ljust(200)[:200] # pad to a 200 char msg and cut excess text if message more than 200 char

	# handles case where server disconnects
	try:	
		s.send(text.encode())
	except socket.error:
		print(utils.CLIENT_SERVER_DISCONNECTED.format(sys.argv[2], sys.argv[3]))
		s.close()
		running = False

sys.exit(0)
