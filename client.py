import socket
import sys
import utils
import thread

if len(sys.argv) != 4:
	print("Invalid number of args.\nUse : python client.py NAME IP PORT")
	quit()


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((sys.argv[2], int(sys.argv[3])))

name = sys.argv[1]

s.send(name.encode())

# this function's role is to receive the data, buffer it if needed and display it
# this function will be run in a separate thread to allow for data sending at the same
# time
def receiverThread():
	while True:
		data = s.recv(200);
		while len(data) < 200:
			data += s.recv(200 - len(data))
			# now we have for sure a 200 char piece of data
		print(utils.CLIENT_WIPE_ME + "\r" + data.decode().strip())
		# reset the terminal 'ME' output
		print utils.CLIENT_MESSAGE_PREFIX,
		sys.stdout.flush()

# start receiving thread before we go for sending loop
thread.start_new_thread(receiverThread, ())

while True:
	text = raw_input(utils.CLIENT_MESSAGE_PREFIX)
	# do not pad ctrl data as it will be interpreted by the server
	if text[0] != '/':
		# add client name now, this will allow for coherent padding
		text = '[' + name + ']' + text
		while len(text) < 200:
			text += ' '
	s.send(text.encode())

s.close()