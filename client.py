import socket
import sys
import utils
import thread

if len(sys.argv) != 4:
	print("Invalid number of args.\nUse : python client.py NAME IP PORT")
	quit()

try:
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((sys.argv[2], int(sys.argv[3])))
except socket.error:
	print(utils.CLIENT_CANNOT_CONNECT.format(sys.argv[2], sys.argv[3]))
	quit()

name = sys.argv[1]

s.send(name.ljust(200).encode())

# this function's role is to receive the data, buffer it if needed and display it
# this function will be run in a separate thread to allow for data sending at the same
# time
def receiverThread():
	while True:
		try:	
			data = s.recv(200);
		except socket.error:
			print(utils.CLIENT_SERVER_DISCONNECTED.format(sys.argv[2], sys.argv[3]))
			s.close()
			quit()

		# buffering on the client side in case there was a spliting server (unlikely)
		while len(data) < 200:
			data += s.recv(200 - len(data))

		print(utils.CLIENT_WIPE_ME + "\r" + data.decode().strip())
		# reset the terminal 'ME' output
		print utils.CLIENT_MESSAGE_PREFIX,
		sys.stdout.flush()

# start receiving thread before we go for sending loop
thread.start_new_thread(receiverThread, ())

while True:
	text = raw_input(utils.CLIENT_MESSAGE_PREFIX)
	# do not pad ctrl data as it will be interpreted by the server
	if len(text) == 0: # discards empty messages
		continue
	if text[0] != '/':
		# add client name now, this will allow for coherent padding
		text = "[" + name + '] ' + text
	text = text.ljust(200) # pad to a 200 char msg

	try:	
		s.send(text.encode())
	except socket.error:
		print(utils.CLIENT_SERVER_DISCONNECTED.format(sys.argv[2], sys.argv[3]))
		s.close()
		quit()

s.close()