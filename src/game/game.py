import cocos

import entity.player
import equipment


game = None
layer = None


def start():
    global game
    global layer

    #Setup the game
    layer = cocos.layer.Layer()
    game = Game()

    player = entity.player.Player()
    player.weapon = equipment.BowWeapon(player)

    enemy = entity.BasicEnemy()

    game.spawn(enemy)

    #Setup controls
    import interface.controls  # TODO: Add init functions for modules so late import isnt needed
    c = interface.controls.init()
    layer.add(c)

    game.spawn(player)
    game.set_player(player.eid)
    layer.schedule(game.update)

    return layer


class Game():
    """Game state

    Handles both game state and in-game world state

    """

    def __init__(self):
        self.entities = {}
        self.controlled_player = None
        self.tick = 0

    def update(self, t):
        #Update position then velocity
        self.tick += t
        for i in self.entities.values():
            self.update_entity(i, t)

    def update_entity(self, ent, t):
        ent.update(t)

    def get_entity(self, eid):
        return self.entities.get(eid)

    def get_player(self):
        return self.get_entity(self.controlled_player)

    def set_player(self, eid):
        self.controlled_player = eid

    def spawn(self, e):
        if not hasattr(e, "eid"):
            e.eid = len(self.entities) + 1
        self.entities[e.eid] = e

        if e.attached_to:
            anchor = self.get_entity(e.attached_to)
            anchor.sprite.add(e.sprite)
        else:
            print "added: ", e.sprite
            layer.add(e.sprite)

    def despawn(self, e):
        if e.sprite:
            print "Want to remove: ", e.sprite
            layer.remove(e.sprite)
