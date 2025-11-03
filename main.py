import pgzrun
import os
import re
from collections import defaultdict
from platformer import *
import time
import math

TILE_SIZE = 32
ROWS = 30
COLS = 20

WIDTH = TILE_SIZE * ROWS
HEIGHT = TILE_SIZE * COLS
TITLE = "mini madness"
CREDIT_SCROLL_Y = HEIGHT

DEATH_COUNT = 0

GAME_STATE = "menu"
lobby_image = Actor("lobby")
lobby_image.pos = (WIDTH // 2, HEIGHT // 2)

LOGO = Actor("logo")
LOGO.pos = (WIDTH // 2, HEIGHT // 3)

start_button = Actor("start_button")
start_button.pos = (WIDTH // 2, HEIGHT // 1.5)
start_scale = 1.0
target_scale = 1.0
scale_speed = 10
click_anim = False
click_timer = 0

Current_Stage = 1

DATA_PATH = "data"

Stage_List = {}
Bg_List = {}
Door_List = {}
FakePart_List = defaultdict(list)
Spike_List = defaultdict(list)
Spring_List = defaultdict(list)
Super_spring_List = defaultdict(list)
Star_List = defaultdict(list)

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
    elif "._Star" in filename:
        Star_List[stage_num].append(full_path)

FakePart_List = dict(FakePart_List)
Spike_List = dict(Spike_List)
Spring_List = dict(Spring_List)
Super_spring_List = dict(Super_spring_List)
Star_List = dict(Star_List)

# store which triggers have already spawned their objects to avoid repeated spawns
trigger_spawned = {}

def load_stage(stage_num):
    global platforms, backgrounds, doors, fake_parts, spike_parts, Current_Stage, spring_parts, super_spring_parts
    global spring_timers, spring_active, remove_spring, removed_spring, spawned, spike_active, spike_timers, Star_parts
    global FakePart_Drop, Spike_Drop, spike_index, active_spikes, drop_started, drop_start_time
    Current_Stage = stage_num
    platforms = build(Stage_List[stage_num], TILE_SIZE)
    backgrounds = build(Bg_List[stage_num], TILE_SIZE)
    doors = build(Door_List[stage_num], TILE_SIZE)
    fake_parts = []
    spike_parts = []
    spring_parts = []
    super_spring_parts = []
    Star_parts = []
    spring_timers = []
    spike_timers = []
    spring_active = False
    removed_spring = False
    spike_active = False
    spawned = False
    FakePart_Drop = False
    Spike_Drop = False
    drop_started = False
    drop_start_time = 0
    spike_index = 30
    active_spikes = []

    # reset stage-specific trigger flags
    # remove any previous stage's keys
    keys_to_remove = [k for k in trigger_spawned.keys() if k[0] == stage_num]
    for k in keys_to_remove:
        trigger_spawned.pop(k, None)

    if Current_Stage == 3:
        # preload a spring to remove later
        part_file = Spring_List[Current_Stage][1]
        remove_spring = build(part_file, TILE_SIZE)
        spring_parts.extend(remove_spring)

    if stage_num in FakePart_List:
        for part_file in FakePart_List[stage_num]:
            fake_parts.extend(build(part_file, TILE_SIZE))
    if stage_num in Spike_List:
        for part_file in Spike_List[stage_num]:
            spike_parts.extend(build(part_file, TILE_SIZE))
    if stage_num in Star_List:
        for part_file in Star_List[stage_num]:
            Star_parts.extend(build(part_file, TILE_SIZE))

    if Current_Stage == 5:
        player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 1.25)
    else:
        player.bottomleft = (0, 0)
    player.velocity_x = 5

# -- spawn spring
def spawn_spring(file_path, lifetime=3):
    new_springs = build(file_path, TILE_SIZE)
    spring_parts.extend(new_springs)
    spring_timers.append((time.time(), file_path, lifetime, new_springs))

# -- click anim
def on_mouse_move(pos):
    global target_scale
    if GAME_STATE == "menu":
        if start_button.collidepoint(pos):
            target_scale = 1.1
        else:
            target_scale = 1.0

def on_mouse_down(pos):
    global GAME_STATE, click_anim, target_scale
    if GAME_STATE == "menu" and start_button.collidepoint(pos):
        click_anim = True
        target_scale = 0.9

def on_mouse_up(pos):
    global GAME_STATE
    if GAME_STATE == "menu" and start_button.collidepoint(pos):
        GAME_STATE = "playing"

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

def draw_ending():
    screen.clear()
    screen.fill("black")

    credit_lines = [
        "THANK YOU FOR PLAYING!",
        "",
        "Mini Madness",
        "Created by: YourNameHere",
        "",
        "Special Thanks:",
        "- Everyone who played the game",
        "- Friends & Family",
        "",
        "See you next adventure!"
    ]
    y = CREDIT_SCROLL_Y
    for line in credit_lines:
        screen.draw.text(
            line,
            center=(WIDTH // 2, y),
            fontsize=40,
            color="white"
        )
        y += 60


# --- draw ---
def draw():
    screen.clear()
    if GAME_STATE == "menu":
        lobby_image.draw()
        if os.path.exists("images/logo.png"):
            LOGO.draw()
            scaled_img = pygame.transform.rotozoom(images.logo, 0, 2)
            rect = scaled_img.get_rect(center=LOGO.pos)
            screen.surface.blit(scaled_img, rect)
        else:
            screen.draw.text("Mini Madness", center=(WIDTH // 2, HEIGHT // 3), fontsize=80, color="white")

        scaled_img = pygame.transform.rotozoom(images.start_button, 0, start_scale)
        rect = scaled_img.get_rect(center=start_button.pos)
        screen.surface.blit(scaled_img, rect)
        return  # จบที่เมนูเลย ไม่ต้องวาดฉากอื่น


    # --- ฉากจบ (End Credit) ---
    if GAME_STATE == "ending":
        screen.fill("black")
        credit_lines = [
            "THANK YOU FOR PLAYING!",
            "",
            "Mini Madness",
            "Created by: Kuy",
            "",
            "Special Thanks:",
            "- Everyone who played the game",
            "- Friends & Family",
            "",
            "See you next adventure!"
        ]

        y = CREDIT_SCROLL_Y
        for line in credit_lines:
            screen.draw.text(
                line,
                center=(WIDTH // 2, y),
                fontsize=40,
                color="white"
            )
            y += 60
        return


    # --- เกมหลัก (playing) ---
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
    for Star in Star_parts:
        Star.draw()

    screen.draw.text(
        f"Deaths: {DEATH_COUNT}",
        (WIDTH - 150, 10),
        color="white",
        fontsize=30,
    )

    player.draw()

# --- update ---
def update(dt):
    global Current_Stage, spring_parts, spring_active, removed_spring, DEATH_COUNT, spawned, spring_velocity
    global spike_active, Star_parts, FakePart_Drop
    global Spike_Drop, drop_started, drop_start_time, spike_index, active_spikes
    global GAME_STATE, start_scale, click_anim, click_timer, target_scale, CREDIT_SCROLL_Y

    start_scale += (target_scale - start_scale) * dt * scale_speed

    if click_anim:
        click_timer += dt * 10
        target_scale = 1.0 + 0.1 * math.sin(click_timer * 3.5) * math.exp(-click_timer)
        if click_timer > 2:
            click_anim = False
            click_timer = 0
            target_scale = 1.0
    if GAME_STATE == "menu":
        return
    
    if GAME_STATE == "ending":
        CREDIT_SCROLL_Y -= 100 * dt
        if CREDIT_SCROLL_Y < -1000:
            CREDIT_SCROLL_Y = HEIGHT
            GAME_STATE = "menu"
            Current_Stage = 1
        return
    
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
        # set sprite only when it actually changes
        if player.sprite != knight_walk:
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
        if player.sprite != knight_walk:
            player.sprite = knight_walk
        player.flip_h = False
        if player.collidelist(platforms) != -1:
            obj = platforms[player.collidelist(platforms)]
            player.x = obj.x - (obj.width / 2 + player.width / 2)
        if player.collidelist(fake_parts) != -1:
            obj = fake_parts[player.collidelist(fake_parts)]
            player.x = obj.x - (obj.width / 2 + player.width / 2)
    else:
        # when not moving horizontally, ensure idle sprite
        if player.sprite != knight_stand:
            player.sprite = knight_stand

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
    # if player.collidelist(spike_parts) != -1:
    #     DEATH_COUNT += 1
    #     load_stage(Current_Stage)

    # ชนStar
    if player.collidelist(Star_parts) != -1:
        DEATH_COUNT += 1
        load_stage(Current_Stage)

    # ชนspring
    if player.collidelist(spring_parts) != -1:
        player.velocity_y = spring_velocity
    if player.collidelist(super_spring_parts) != -1:
        player.velocity_y = Super_spring_velocity

    # ตกขอบ
    if player.y >= HEIGHT:
        DEATH_COUNT += 1
        load_stage(Current_Stage)

    # เปลี่ยนด่าน
    if player.collidelist(doors) != -1:
        next_stage = Current_Stage + 1
        if next_stage in Stage_List:
            load_stage(next_stage)
        else:
            GAME_STATE = "ending"
            CREDIT_SCROLL_Y = HEIGHT

    # กับดัก
    if Current_Stage == 1:
        if not spawned:
            player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 1.3)
            spawned = True
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
        if not spawned:
            player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 1.4)
            spawned = True
        key0 = (Current_Stage, "spring", 0)
        if player.x >= 45 and player.y >= 480 and not trigger_spawned.get(key0, False):
            part_file = Spring_List[Current_Stage][0]
            spring_parts.extend(build(part_file, TILE_SIZE))
            trigger_spawned[key0] = True

        key1 = (Current_Stage, "spring", 1)
        key1s = (Current_Stage, "superspring", 0)
        if player.x >= 544 and player.y >= 480 and not trigger_spawned.get(key1, False):
            part_file = Spring_List[Current_Stage][1]
            spring_parts.extend(build(part_file, TILE_SIZE))
            trigger_spawned[key1] = True
        if player.x >= 544 and player.y >= 480 and not trigger_spawned.get(key1s, False):
            part_file = Super_spring_List[Current_Stage][0]
            super_spring_parts.extend(build(part_file, TILE_SIZE))
            trigger_spawned[key1s] = True

        if player.x >= 385:
            for i in range(3,6):
                spike_parts[i].x = 1000
        if player.x >= 672:
            spike_parts[3].x = 688
        if player.x >= 768:
            fake_parts[0].x = 720
            fake_parts[1].x = 880

    if Current_Stage == 3:
        if not spawned:
            player.bottomleft = (0, 95)
            spawned = True
        fake_parts[22].x = 1000
        if player.y >= 352:
            for i in range(8):
                fake_parts[i].x = 80
            key2 = (Current_Stage, "spring", 0)
            if not trigger_spawned.get(key2, False):
                part_file = Spring_List[Current_Stage][0]
                spring_parts.extend(build(part_file, TILE_SIZE))
                trigger_spawned[key2] = True
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
            player.bottomleft = (0, (HEIGHT - TILE_SIZE) / 1.7)
            spawned = True
            if len(spike_parts) > 10:
                spike_parts[9].x = 1000
                spike_parts[10].x = 1000
            key3 = (Current_Stage, "spring", 1)
            if not trigger_spawned.get(key3, False):
                part_file = Spring_List[Current_Stage][1]
                spring_parts.extend(build(part_file, TILE_SIZE))
                trigger_spawned[key3] = True
            key4 = (Current_Stage, "spring", 2)
            if not trigger_spawned.get(key4, False):
                part_file = Spring_List[Current_Stage][2]
                spring_parts.extend(build(part_file, TILE_SIZE))
                trigger_spawned[key4] = True
            key5 = (Current_Stage, "superspring", 0)
            if not trigger_spawned.get(key5, False):
                part_file = Super_spring_List[Current_Stage][0]
                super_spring_parts.extend(build(part_file, TILE_SIZE))
                trigger_spawned[key5] = True
            spring_velocity = -15

        key6 = (Current_Stage, "spring", 0)
        if player.y > 384 and not trigger_spawned.get(key6, False):
            if len(spike_parts) > 3:
                spike_parts[3].x = 1000
            part_file = Spring_List[Current_Stage][0]
            spring_parts.extend(build(part_file, TILE_SIZE))
            trigger_spawned[key6] = True

        if player.y > 480:
            spring_velocity = -20
            if len(spike_parts) > 10:
                spike_parts[9].x = 368
                spike_parts[10].x = 400
        if player.x < 608 and player.y < 192:
            Spike_Drop = True
            FakePart_Drop = True
        if FakePart_Drop:
            if player.x < 416:
                for i in range(6):
                    fake_parts[i].y += 10
        if Spike_Drop and not drop_started:
            drop_started = True
            drop_start_time = current_time
            spike_index = 28
            active_spikes = []
        if drop_started:
            if spike_index >= 12 and current_time - drop_start_time >= (28 - spike_index) * 0.13:
                active_spikes.append(spike_index)
                spike_index -= 1
            for i in active_spikes:
                if i == 20 or i == 21:
                    continue
                spike_parts[i].y += 5
                if spike_parts[i].y >= 1000:
                    spike_parts[i].y = 1000
            if spike_index < 12 and all(spike_parts[i].y >= 1000 for i in active_spikes):
                drop_started = False
                Spike_Drop = False

# --- key events ---
def on_key_down(key):
    if key == keys.SPACE and not player.jumping:
        player.velocity_y = jump_velocity
        player.jumping = True

def on_key_up(key):
    if key in (keys.A, keys.D):
        if player.sprite != knight_stand:
            player.sprite = knight_stand

pgzrun.go()
