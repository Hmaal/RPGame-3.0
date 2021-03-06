import socket
import json
import logging

from game.game import game  # Yeeeaaah.... Time to figure out python packages!
from multiplayer import json_decode, jsonEncoder
import interface.controls
import entity
import events


logger = logging.getLogger("client")

server = None
old_data = ""
packet_id = 0 

packet_hooks = {}  # Function callbacks
entity_ticks = {}  # Last tick we recieved updates for entities

# Init handlers
class ClientHandler(object):

    def on_attack(self, attacker, weapon, old_entity):
        old_eid = old_entity.eid
        if game.is_controlled(old_entity):
            def reply_callback(eid):
                game.local_entities[old_eid] = None
                new_entity = game.get_entity(eid)
                if new_entity: # Might happen if a packet is lost
                    # TODO: Some trouble here (i.e if packet is lost)
                    new_entity.sprite.kill()
                    new_entity.sprite = old_entity.sprite
                else:
                    old_entity.eid = eid
                    game.entities[eid] = old_entity

            packet_id = send("spawn_entity", old_entity)
            packet_hooks[packet_id] = reply_callback

events.handler.push_handlers(ClientHandler())

def recieve():
    """Check for data from server"""
    raw_data = True
    while raw_data:
        try:
            raw_data = server.recv(1024)
        except socket.error as e:
            raw_data = False
            if e.errno == 10035:
                pass
        else:
            handle_data(raw_data)


def send(command, data, callback=None):
    """Send data to the server"""
    global packet_id
    pid = packet_id +1
    packet_id = pid
    msg = {
        "packet_id": pid,
        "command": command,
        "data": data,
        "tick": game.tick
    }
    msg = json.dumps(msg, cls=jsonEncoder)

    if callback:
        packet_hooks[pid] = callback
    
    logging.info("Sending msg: " + msg)
    server.send(msg)

    return packet_id


def handle_data(raw_data):
    #print "[CLIENT] Recieved data, json: ", raw_data
    logger.info("Recieved data from server: %s", raw_data)
    data = json.loads(raw_data, object_hook = json_decode)

    if data["command"] == "update":
        #Time to update an entity
        tick = data["tick"]

        entity = data["data"]
        eid = entity.eid

        #check for tick
        if not tick in entity_ticks.keys():  # First time we recieve a tick
            entity_ticks[eid] = tick
        elif tick < entity_ticks[eid]:  # The new update is old! lets disregard it
            return
        else:
            entity_ticks[eid] = tick

        e = game.get_entity(eid)

        # If it has the key, this entity has already existed at a point so we should ignore this
        if not e:
            game.spawn(entity, force=True)
            #e.from_json(entity)
        else:
            if e.eid == game.get_player(): # TODO: This shouldnt even be sent from the server
                pass
            else:
                e.update_from(entity) # TODO: This is kinda weird.
                tick = max(0, game.tick - tick) / 100.0
                #e.update(tick)

    elif data["command"] == "set_control":
        d = data["data"]
        eid = d["eid"]
        game.set_player(eid)

    elif data["command"] == "set_tick":
        d = data["data"]
        tick = d["tick"]
        game.tick = tick
    elif data["command"] == "set_player":
        d = data["data"]
        player = d["player"]
        game.set_player_id(player)
    elif data["command"] == "set_tick":
        d = data["data"]
        tick = d["tick"]
        game.tick = tick
    elif data["command"] == "accept_attack":
        d = data["data"]
        packet_id = d["packet_reference"]
        eid = d["eid"]
        packet_hooks[packet_id](eid)    

    else:
        assert(False, "We recieved a command but have no idea what to do with it")


def update(t):
    recieve()

    #Check if we need to send an update of our controls
    state = interface.controls.get_state()
    if state["updated"]:
        player = game.get_player()
        position = None
        if player:
            position = player.position
        data = {"state":state, "tick":game.tick, "position":position}
        send("update_controls", data)
        state["updated"] = False

#init_handlers()