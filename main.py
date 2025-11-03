import pgzrun
import os
import re
from collections import defaultdict
from platformer import *
import time

TILE_SIZE = 32
ROWS = 30
COLS = 20

WIDTH = TILE_SIZE * ROWS
HEIGHT = TILE_SIZE * COLS
TITLE = "mini madness"

DEATH_COUNT = 0

Current_Stage = 5

DATA_PATH = "data"

Stage_List = {}
Bg_List = {}
Door_List = {}
FakePart_List = defaultdict(list)
Spike_List = defaultdict(list)
Spring_List = defaultdict(list)
Super_spring_List = defaultdict(list)

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
    elif "._SuperSpring" in filename:
        Super_spring_List[stage_num].append(full_path)

FakePart_List = dict(FakePart_List)
Spike_List = dict(Spike_List)
Spring_List = dict(Spring_List)
Super_spring_List = dict(Super_spring_List)

def load_stage(stage_num):
    global platforms, backgrounds, doors, fake_parts, spike_parts, Current_Stage, spring_parts, super_spring_parts
    global spring_timers, spring_active, remove_spring, removed_spring, spawned
    Current_Stage = stage_num
    platforms = build(Stage_List[stage_num], TILE_SIZE)
    backgrounds = build(Bg_List[stage_num], TILE_SIZE)
    doors = build(Door_List[stage_num], TILE_SIZE)
    fake_parts = []
    spike_parts = []
    spring_parts = []
    super_spring_parts = []
    spring_timers = []
    spring_active = False
    removed_spring = False
    spawned = False
    if Current_Stage == 3:
        part_file = Spring_List[Current_Stage][1]
        remove_spring = build(part_file, TILE_SIZE)
        spring_parts.extend(remove_spring)
    if stage_num in FakePart_List:
        for part_file in FakePart_List[stage_num]:
            fake_parts.extend(build(part_file, TILE_SIZE))
    if stage_num in Spike_List:
        for part_file in Spike_List[stage_num]:
            spike_parts.extend(build(part_file, TILE_SIZE))
    if Current_Stage == 5:
        player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 1.25)
    else:
        player.bottomleft = (0, 0)

# -- spawn spring
def spawn_spring(file_path, lifetime=3):
    new_springs = build(file_path, TILE_SIZE)
    spring_parts.extend(new_springs)
    spring_timers.append((time.time(), file_path, lifetime, new_springs))


# --- sprite ---
color_key = (0, 0, 0)
knight_stand = Sprite("hero-idle-sheet.png", 24, 24, 0, 2, 4, color_key)
knight_walk = Sprite("hero-walk-sheet.png", 24, 24, 0, 6, 12, color_key)

# --- player Actor ---
player = SpriteActor(knight_stand)
player.bottomleft = (0, 0)
player.velocity_x = 5
player.velocity_y = 0
player.jumping = False
player.scale = 1.5
gravity = 1
jump_velocity = -14
spring_velocity = -20
Super_spring_velocity = -30
Block_direction = 1
Block_speed = 1

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
    for Super_spring in super_spring_parts:
        Super_spring.draw()
    screen.draw.text(
    f"Deaths: {DEATH_COUNT}",
    (WIDTH - 150, 10),
    color="white",
    fontsize=30,
    )
    player.draw()

# --- update ---
def update():
    global Current_Stage, spring_parts, spring_active, removed_spring, DEATH_COUNT, spawned

    current_time = time.time()
    for timer in list(spring_timers):
        start, file_path, lifetime, parts = timer
        if current_time - start >= lifetime:
            for s in parts:
                if s in spring_parts:
                    spring_parts.remove(s)
            spring_timers.remove(timer)

    # การเคลื่อนไหวซ้าย-ขวา
    if keyboard.A and player.midleft[0] > 0:
        player.x -= player.velocity_x
        player.sprite = knight_walk
        player.flip_h = True
        if player.collidelist(platforms) != -1:
            obj = platforms[player.collidelist(platforms)]
            player.x = obj.x + (obj.width / 2 + player.width / 2)
        if player.collidelist(fake_parts) != -1:
            obj = fake_parts[player.collidelist(fake_parts)]
            player.x = obj.x + (obj.width / 2 + player.width / 2)
    elif keyboard.D and player.midright[0] < WIDTH:
        player.x += player.velocity_x
        player.sprite = knight_walk
        player.flip_h = False
        if player.collidelist(platforms) != -1:
            obj = platforms[player.collidelist(platforms)]
            player.x = obj.x - (obj.width / 2 + player.width / 2)
        if player.collidelist(fake_parts) != -1:
            obj = fake_parts[player.collidelist(fake_parts)]
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

    # ชนfake_part
    if player.collidelist(fake_parts) != -1:
        obj = fake_parts[player.collidelist(fake_parts)]
        if player.velocity_y >= 0:
            player.y = obj.y - (obj.height / 2 + player.height / 2)
            player.jumping = False
        else:
            player.y = obj.y + (obj.height / 2 + player.height / 2)
        player.velocity_y = 0

    # ชนspike
    if player.collidelist(spike_parts) != -1:
        DEATH_COUNT += 1
        if Current_Stage == 5:
            player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 1.25)
        else:
            player.bottomleft = (0, 0)
        load_stage(Current_Stage)

    # ชนspring
    if player.collidelist(spring_parts) != -1:
        player.velocity_y = spring_velocity
    if player.collidelist(super_spring_parts) != -1:
        player.velocity_y = Super_spring_velocity

    # ตกขอบ
    if player.y >= HEIGHT:
        DEATH_COUNT += 1
        if Current_Stage == 5:
            player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 1.25)
        else:
            player.bottomleft = (0, 0)
        load_stage(Current_Stage)

    # เปลี่ยนด่าน
    if player.collidelist(doors) != -1:
        next_stage = Current_Stage + 1
        if next_stage in Stage_List:
            load_stage(next_stage)
        else:
            if Current_Stage == 5:
                player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 1.25)
            else:
                player.bottomleft = (0, 0)

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
        if player.x >= 45 and player.y >= 480:
            part_file = Spring_List[Current_Stage][0]
            spring_parts.extend(build(part_file, TILE_SIZE))
        if player.x >= 544 and player.y >= 480:
            part_file = Spring_List[Current_Stage][1]
            spring_parts.extend(build(part_file, TILE_SIZE))
            part_file = Super_spring_List[Current_Stage][0]
            super_spring_parts.extend(build(part_file, TILE_SIZE))
        if player.x >= 385:
            for i in range(3,6):
                spike_parts[i].x = 1000
        if player.x >= 672:
            spike_parts[3].x = 688
        if player.x >= 768:
            fake_parts[0].x = 720
            fake_parts[1].x = 880
    if Current_Stage == 3:
        fake_parts[22].x = 1000
        if player.y >= 352:
            for i in range(8):
                fake_parts[i].x = 80
            part_file = Spring_List[Current_Stage][0]
            spring_parts.extend(build(part_file, TILE_SIZE))
        if player.x >= 350:
            fake_parts[22].x = 368
            if not removed_spring:
                part_file = Spring_List[Current_Stage][2]
                spring_parts.extend(build(part_file, TILE_SIZE))
                for s in remove_spring:
                    if s in spring_parts:
                        spring_parts.remove(s)
                    removed_spring = True
            for i in range(8,22):
                fake_parts[i].x = 1000
        if not spring_active and player.x >= 500:
            part_file = Spring_List[Current_Stage][3]
            spawn_spring(part_file, lifetime=3)
            spring_active = True
        global Block_direction
        fake_parts[23].x += Block_speed * Block_direction
        if fake_parts[23].x >= 784:
            Block_direction = -1
        elif fake_parts[23].x <= 688:
            Block_direction = 1
        if player.x >= 896:
            for i in range(24,52):
                fake_parts[i].y += 10
    if Current_Stage == 5:
        if not spawned:
            player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 1.25)
            spawned = True

# --- key events ---
def on_key_down(key):
    if key == keys.SPACE and not player.jumping:
        player.velocity_y = jump_velocity
        player.jumping = True

def on_key_up(key):
    if key in (keys.A, keys.D):
        player.sprite = knight_stand

pgzrun.go()
