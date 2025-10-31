import pgzrun
from platfomer import *

TILE_SIZE = 32
ROWS = 30
COLS = 20

WIDTH = TILE_SIZE * ROWS
HEIGHT = TILE_SIZE * COLS
TITLE = "mini madness"

# map
platforms = build("Stage_01._Platformer.csv", TILE_SIZE)
blackgrounds = build("Stage_01._Background2.csv", TILE_SIZE)
doors = build("Stage_01._Door.csv", TILE_SIZE)

# sprite
color_key = (0, 0, 0)
knight_stand = Sprite("hero-idle-sheet.png", 24, 24, 0, 2, 4, color_key)
knight_walk = Sprite("hero-walk-sheet.png", 24, 24, 0, 6, 12, color_key)

# player Actor
player = SpriteActor(knight_stand)
player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 1.3)
player.velocity_x = 3
player.velocity_y = 0
player.jumping = False
player.scale = 2
gravity = 1
jump_velocity = -12

def draw():
    screen.clear()
    screen.fill("Black")
    for platform in platforms:
        platform.draw()
    for backgound in blackgrounds:
        backgound.draw()
    for door in doors:
        door.draw()

    player.draw()

def update():
    if keyboard.A and player.midleft[0] > 0:
        player.x -= player.velocity_x
        player.sprite = knight_walk
        player.flip_h = True
        if player.collidelist(platforms) != -1:
            object = platforms[player.collidelist(platforms)]
            player.x = object.x + (object.width / 2 + player.width / 2)

    elif keyboard.D and player.midright[0] < WIDTH:
        player.x += player.velocity_x
        player.sprite = knight_walk
        player.flip_h = False
        if player.collidelist(platforms) != -1:
            object = platforms[player.collidelist(platforms)]
            player.x = object.x - (object.width / 2 + player.width / 2)

    player.y += player.velocity_y
    player.velocity_y += gravity

    if player.collidelist(platforms) != -1:
        object = platforms[player.collidelist(platforms)]
        if player.velocity_y >= 0:
            player.y = object.y - (object.height / 2 + player.height / 2)
            player.jumping = False
        else:
            player.y = object.y + (object.height / 2 + player.height / 2)
            player.jumping = False
        player.velocity_y = 0

    if player.y >= 650:
        player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 1.3)

    # if player.collidelist(doors) != -1:


def on_key_down(key):
    if key == key.SPACE and not player.jumping:
        player.velocity_y = jump_velocity
        player.jumping = True

def on_key_up(key):
    if key == keys.A or key == keys.D:
        player.sprite = knight_stand

pgzrun.go()