import socket
import json

from game.game import game #Yeeeaaah.... Time to figure out python packages!

server = None

def join():
	global server

	server = socket.socket()
	server.connect(("localhost",30035))
	server.setblocking(0)

def recieve():
	"""Check for data from server"""

	try:
		raw_data = server.recv(1024)
	except socket.error as e:
	    if e.errno == 10035:
	        pass
	else:
		if raw_data:
			#first handle command splitting
			while raw_data:
				l, data = raw_data.split("|", 1) #Only split the first |
				l = int(l)
				raw_data = data[l:] #continue processing the rest of the data
				if len(raw_data) < l:
					pass #TODO: Handle too much data at once
				else:
					handle_data(data[:l]) #handle the recieved command

def send(command, data):
	"""Send data to the server"""
	print "[CLIENT] Sending data: Command: '%s' Data: '%s'"%(command,data)
	d = json.dumps({"command":command, "data":data})
	msg = str(len(d)) + "|" + d
	server.send(msg)


def handle_data(raw_data):
	print "[CLIENT] Recieved data, json: ", raw_data
	data = json.loads(raw_data)

	if data["command"] == "update":
		#Time to update an entity
		d = data["data"]
		eid = d["eid"]
		entity = game.get_entity(eid)
		for k,v in d.items():
			if isinstance(v, dict): #The value is an object and must be constructed
				if v["type"] == "Vector2":
					args = v["args"]
					import cocos.euclid
					v = cocos.euclid.Vector2(args[0],args[1])
				else:
					print "[WARNING] Client recieved undefined data type" #Should ignore it most likely
					continue
			setattr(entity, k, v) #YOLO

	elif data["command"] == "spawn":
		e = data["data"]
		t = e["type"]
		game.spawn(t)

def update(t):
	recieve()

