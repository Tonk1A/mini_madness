import pgzrun
from platformer import *

TILE_SIZE = 32
ROWS = 30
COLS = 20

WIDTH = TILE_SIZE * ROWS
HEIGHT = TILE_SIZE * COLS
TITLE = "mini madness"

Current_Stage = 1

Stage_List = {
    1: "Stage_01._Platformer.csv",
    2: "Stage_02._Platformer.csv"
}
Bg_List = {
    1: "Stage_01._Bg.csv",
    2: "Stage_02._Bg.csv"
}
Door_List = {
    1: "Stage_01._Door.csv",
    2: "Stage_02._Door.csv"
}

# load defualt
def load_stage(stage_num):
    global platforms, backgrounds, doors, Current_Stage
    Current_Stage = stage_num
    platforms = build(Stage_List[stage_num], TILE_SIZE)
    backgrounds = build(Bg_List[stage_num], TILE_SIZE)
    doors = build(Door_List[stage_num], TILE_SIZE)
    player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 1.3)

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

# โหลด Current Stage
load_stage(Current_Stage)

def draw():
    screen.clear()
    screen.fill("Black")
    for bg in backgrounds:
        bg.draw()
    for platform in platforms:
        platform.draw()
    for door in doors:
        door.draw()
    player.draw()

def update():
    global Current_Stage
    # การเคลื่อนไหว
    if keyboard.A and player.midleft[0] > 0:
        player.x -= player.velocity_x
        player.sprite = knight_walk
        player.flip_h = True
        if player.collidelist(platforms) != -1:
            obj = platforms[player.collidelist(platforms)]
            player.x = obj.x + (obj.width / 2 + player.width / 2)

    elif keyboard.D and player.midright[0] < WIDTH:
        player.x += player.velocity_x
        player.sprite = knight_walk
        player.flip_h = False
        if player.collidelist(platforms) != -1:
            obj = platforms[player.collidelist(platforms)]
            player.x = obj.x - (obj.width / 2 + player.width / 2)

    # แรงโน้มถ่วง
    player.y += player.velocity_y
    player.velocity_y += gravity

    # ชนพื้น
    if player.collidelist(platforms) != -1:
        obj = platforms[player.collidelist(platforms)]
        if player.velocity_y >= 0:
            player.y = obj.y - (obj.height / 2 + player.height / 2)
            player.jumping = False
        else:
            player.y = obj.y + (obj.height / 2 + player.height / 2)
        player.velocity_y = 0

    # ตกขอบ
    if player.y >= 650:
        player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 1.3)

    # เปลี่ยนด่าน
    if player.collidelist(doors) != -1:
        next_stage = Current_Stage + 1
        if next_stage in Stage_List:
            load_stage(next_stage)
        else:
            player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 1.3)

def on_key_down(key):
    if key == keys.SPACE and not player.jumping:
        player.velocity_y = jump_velocity
        player.jumping = True

def on_key_up(key):
    if (key == keys.A or key == keys.D):
        player.sprite = knight_stand

pgzrun.go()
