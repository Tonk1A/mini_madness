import pgzrun
import os
import re
from collections import defaultdict
from platformer import *

TILE_SIZE = 32
ROWS = 30
COLS = 20

WIDTH = TILE_SIZE * ROWS
HEIGHT = TILE_SIZE * COLS
TITLE = "mini madness"

Current_Stage = 2

DATA_PATH = "data"

Stage_List = {}
Bg_List = {}
Door_List = {}
FakePart_List = defaultdict(list)
Spike_List = defaultdict(list)
Spring_List = defaultdict(list)

for filename in os.listdir(DATA_PATH):
    if not filename.endswith(".csv"):
        continue

    match = re.search(r"Stage_(\d+)", filename)
    if not match:
        continue
    stage_num = int(match.group(1))

    full_path = os.path.join(DATA_PATH, filename)

    if "._Platformer" in filename:
        Stage_List[stage_num] = full_path
    elif "._Bg" in filename:
        Bg_List[stage_num] = full_path
    elif "._Door" in filename:
        Door_List[stage_num] = full_path
    elif "._FakePart" in filename:
        FakePart_List[stage_num].append(full_path)
    elif "._Spike" in filename:
        Spike_List[stage_num].append(full_path)
    elif "._Spring" in filename:
        Spring_List[stage_num].append(full_path)
        
FakePart_List = dict(FakePart_List)
Spike_List = dict(Spike_List)
Spring_List = dict(Spring_List)

def load_stage(stage_num):
    global platforms, backgrounds, doors, fake_parts, spike_parts, spring_parts, Current_Stage
    Current_Stage = stage_num
    platforms = build(Stage_List[stage_num], TILE_SIZE)
    backgrounds = build(Bg_List[stage_num], TILE_SIZE)
    doors = build(Door_List[stage_num], TILE_SIZE)
    fake_parts = []
    spike_parts = []
    spring_parts = []
    if stage_num in FakePart_List:
        for part_file in FakePart_List[stage_num]:
            fake_parts.extend(build(part_file, TILE_SIZE))
    if stage_num in Spike_List:
        for part_file in Spike_List[stage_num]:
            spike_parts.extend(build(part_file, TILE_SIZE))
    if stage_num in Spring_List:
        for part_file in Spring_List[stage_num]:
            spring_parts.extend(build(part_file, TILE_SIZE))
    player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 2)

# --- sprite ---
color_key = (0, 0, 0)
knight_stand = Sprite("hero-idle-sheet.png", 24, 24, 0, 2, 4, color_key)
knight_walk = Sprite("hero-walk-sheet.png", 24, 24, 0, 6, 12, color_key)

# --- player Actor ---
player = SpriteActor(knight_stand)
player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 2)
player.velocity_x = 5
player.velocity_y = 0
player.jumping = False
player.alive = True
player.scale = 1.5
gravity = 1
jump_velocity = -14
spring_velocity = -20

# --- โหลด Current Stage ---
load_stage(Current_Stage)

# --- draw ---
def draw():
    screen.clear()
    screen.fill("Black")
    for bg in backgrounds:
        bg.draw()
    for platform in platforms:
        platform.draw()
    for door in doors:
        door.draw()
    for fake in fake_parts:
        fake.draw()
    for spike in spike_parts:
        spike.draw()
    for spring in spring_parts:
        spring.draw()
    player.draw()

# --- update ---
def update():
    global Current_Stage

    # การเคลื่อนไหวซ้าย-ขวา
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

    # ชนspike
    if player.collidelist(spike_parts) != -1:
        player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 2)
        load_stage(Current_Stage)

    # ชนspring
    if player.collidelist(spring_parts) != -1:
        player.velocity_y = spring_velocity

    # ตกขอบ
    if player.y >= HEIGHT:
        player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 2)
        player.alive = False
        load_stage(Current_Stage)

    # เปลี่ยนด่าน
    if player.collidelist(doors) != -1:
        next_stage = Current_Stage + 1
        if next_stage in Stage_List:
            load_stage(next_stage)
        else:
            player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 2)
            
    # กับดัก
    if Current_Stage == 1:
        if player.x >= 185:
            for i in range(15):
                fake_parts[i].y += 10
        if player.x >= 832:
            for i in range(15,45):
                fake_parts[i].y += 10
        if player.x >= 336:
            spike_parts[0].x = 400
            spike_parts[1].x = 432
    if Current_Stage == 2:
         if player.x >= 384:
            for i in range(3,6):
                spike_parts[i].x = 1000

# --- key events ---
def on_key_down(key):
    if key == keys.SPACE and not player.jumping:
        player.velocity_y = jump_velocity
        player.jumping = True

def on_key_up(key):
    if key in (keys.A, keys.D):
        player.sprite = knight_stand

pgzrun.go()
