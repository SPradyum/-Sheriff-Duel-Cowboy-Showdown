import pygame
import random
import sys
import time

pygame.init()

# -------------------- WINDOW & BASE CONFIG --------------------
WIDTH, HEIGHT = 950, 520
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🤠 Sheriff Duel - Cowboy Showdown")

FPS = 60
clock = pygame.time.Clock()

# -------------------- FONTS --------------------
FONT = pygame.font.SysFont("consolas", 34, bold=True)
SMALL = pygame.font.SysFont("consolas", 18)
MID = pygame.font.SysFont("consolas", 22)

# -------------------- COLORS --------------------
WHITE = (255, 255, 255)
RED = (230, 60, 60)
GREEN = (80, 230, 90)
GOLD = (255, 215, 0)
BLACK = (0, 0, 0)
BROWN = (139, 69, 19)
SAND = (235, 200, 120)
SKY_TOP = (90, 180, 255)
SKY_BOTTOM = (255, 230, 200)
CACTUS = (30, 140, 30)
SUN = (255, 240, 150)
BLOOD_RED = (170, 0, 0)

# -------------------- GAME STATE --------------------
score = 0
lives = 3
level = 1
game_state = "TITLE"  # TITLE, COUNTDOWN, DUEL, PLAYER_BULLET, ENEMY_BULLET, ROUND_END, GAME_OVER

# Sheriff & Bandit positions
SHERIFF_X = 120
SHERIFF_Y = HEIGHT - 150
BANDIT_X = WIDTH - 180
BANDIT_Y = HEIGHT - 150

# Bullets
player_bullet = None  # dict {x, y}
enemy_bullet = None   # dict {x, y}

# Timing
countdown_start = 0.0
countdown_number = 3
duel_start_time = 0.0
enemy_fire_delay = 0.0

# Enemy ready flag
enemy_ready = False
enemy_fired = False

# Effects
player_flash_time = 0.0
enemy_flash_time = 0.0
PLAYER_FLASH_DURATION = 0.12
ENEMY_FLASH_DURATION = 0.12

enemy_blood_timer = 0.0
player_blood_timer = 0.0

# Screen shake
shake_time_remaining = 0.0
shake_magnitude = 0

# Tumbleweed
tumbleweeds = []

# Messages & taunts
round_result = None  # "win", "lose", "early"
round_end_time = 0.0
TAUNT_TEXT = ""

WIN_TAUNTS = [
    "Nice shot, sheriff!",
    "You got him clean.",
    "Right between the eyes.",
]
LOSE_TAUNTS = [
    "Too slow, partner!",
    "He got you first.",
    "Blink and you’re dead.",
]
EARLY_TAUNTS = [
    "No cheatin’, cowboy.",
    "Shot too early.",
    "Wait for the draw!",
]

# Weapons (unlockable)
WEAPONS = [
    {"name": "Revolver", "bullet_speed": 11, "color": GOLD, "unlock_level": 1},
    {"name": "Shotgun",  "bullet_speed": 14, "color": (255, 210, 160), "unlock_level": 4},
    {"name": "Sniper",   "bullet_speed": 18, "color": (160, 235, 255), "unlock_level": 7},
]

# Try optional gunshot sound
try:
    GUNSHOT = pygame.mixer.Sound("gunshot.wav")
except Exception:
    GUNSHOT = None

# -------------------- HELPERS --------------------
def get_current_weapon():
    """Return weapon dict based on current level."""
    current = WEAPONS[0]
    for w in WEAPONS:
        if level >= w["unlock_level"]:
            current = w
    return current

def start_new_game():
    global score, lives, level, game_state, round_result, TAUNT_TEXT
    score = 0
    lives = 3
    level = 1
    round_result = None
    TAUNT_TEXT = ""
    start_new_round()
    game_state = "COUNTDOWN"

def start_new_round():
    global countdown_start, countdown_number, enemy_ready, enemy_fired
    global player_bullet, enemy_bullet, duel_start_time, enemy_fire_delay
    global round_result, TAUNT_TEXT, enemy_blood_timer, player_blood_timer

    countdown_start = time.time()
    countdown_number = 3
    enemy_ready = False
    enemy_fired = False
    player_bullet = None
    enemy_bullet = None
    enemy_blood_timer = 0.0
    player_blood_timer = 0.0
    round_result = None
    TAUNT_TEXT = ""

    # Enemy fire delay after DUEL begins
    enemy_fire_delay = random.uniform(0.5, 1.6)

def begin_duel():
    global game_state, duel_start_time, enemy_ready
    game_state = "DUEL"
    duel_start_time = time.time()
    enemy_ready = True

def trigger_screen_shake(duration=0.25, magnitude=8):
    global shake_time_remaining, shake_magnitude
    shake_time_remaining = duration
    shake_magnitude = magnitude

def end_round(result):
    """result in {'win','lose','early'}"""
    global round_result, round_end_time, game_state, TAUNT_TEXT, score, lives, level

    round_result = result
    round_end_time = time.time()
    game_state = "ROUND_END"

    if result == "win":
        score += 10
        level += 1
        TAUNT_TEXT = random.choice(WIN_TAUNTS)
        trigger_screen_shake(0.25, 6)
    elif result == "lose":
        lives -= 1
        TAUNT_TEXT = random.choice(LOSE_TAUNTS)
        trigger_screen_shake(0.25, 9)
    elif result == "early":
        lives -= 1
        score = max(0, score - 5)
        TAUNT_TEXT = random.choice(EARLY_TAUNTS)
        trigger_screen_shake(0.25, 7)

def update_round_end():
    """Handle transition after ROUND_END."""
    global game_state
    now = time.time()
    if now - round_end_time >= 1.2:
        if lives <= 0:
            game_state = "GAME_OVER"
        else:
            start_new_round()
            game_state = "COUNTDOWN"

def init_tumbleweeds():
    global tumbleweeds
    tumbleweeds = []
    for _ in range(4):
        x = random.randint(0, WIDTH)
        y = HEIGHT // 2 + random.randint(60, 120)
        speed = random.uniform(1.5, 3.0)
        size = random.randint(14, 24)
        tumbleweeds.append({"x": x, "y": y, "speed": speed, "size": size})

# -------------------- DRAW FUNCTIONS --------------------
def draw_background(offset):
    ox, oy = offset
    # Sky gradient
    for i in range(HEIGHT//2):
        t = i / (HEIGHT//2)
        r = int(SKY_TOP[0] * (1 - t) + SKY_BOTTOM[0] * t)
        g = int(SKY_TOP[1] * (1 - t) + SKY_BOTTOM[1] * t)
        b = int(SKY_TOP[2] * (1 - t) + SKY_BOTTOM[2] * t)
        pygame.draw.rect(WIN, (r, g, b), (0 + ox, i + oy, WIDTH, 1))

    # Sun
    pygame.draw.circle(WIN, SUN, (WIDTH - 120 + ox, 90 + oy), 40)

    # Ground
    pygame.draw.rect(WIN, SAND, (0 + ox, HEIGHT//2 + oy, WIDTH, HEIGHT//2))

    # Cactus
    base_y = HEIGHT//2 + 60 + oy
    cx = WIDTH//2 + 120 + ox
    pygame.draw.rect(WIN, CACTUS, (cx, base_y - 80, 22, 80))
    pygame.draw.circle(WIN, CACTUS, (cx + 11, base_y - 90), 18)

def draw_tumbleweeds(offset):
    ox, oy = offset
    for t in tumbleweeds:
        pygame.draw.circle(WIN, (170, 120, 70),
                           (int(t["x"] + ox), int(t["y"] + oy)), t["size"], width=2)

def draw_sheriff(offset, flash=False, blood=False):
    ox, oy = offset
    x = SHERIFF_X + ox
    y = SHERIFF_Y + oy

    pygame.draw.rect(WIN, (222,190,140), (x, y - 60, 50, 55))  # Head
    pygame.draw.rect(WIN, (120, 50, 10), (x - 5, y - 50, 60, 10))  # Hat brim
    pygame.draw.rect(WIN, (150, 70, 20), (x + 5, y - 75, 40, 25))  # Hat top
    pygame.draw.rect(WIN, (160,80,30), (x, y, 50, 70))  # Body
    pygame.draw.circle(WIN, GOLD, (x+25, y+20), 10)  # Badge

    # Blood splat on sheriff
    if blood:
        pygame.draw.circle(WIN, BLOOD_RED, (x+10, y+10), 16)
        pygame.draw.circle(WIN, BLOOD_RED, (x+22, y+18), 10)

    # Gun flash
    if flash:
        pygame.draw.circle(WIN, GOLD, (x+60, y+10), 18)

def draw_bandit(offset, ready=False, blood=False, flash=False):
    ox, oy = offset
    x = BANDIT_X + ox
    y = BANDIT_Y + oy

    base_color = RED if ready else (140,140,140)

    pygame.draw.rect(WIN, (200,160,110), (x, y - 60, 50, 55)) # Head
    pygame.draw.rect(WIN, BROWN, (x - 5, y - 50, 60, 10))  # hat brim
    pygame.draw.rect(WIN, (100,40,10), (x+5, y - 75, 40, 25)) # hat top
    pygame.draw.rect(WIN, base_color, (x, y, 50, 70))

    # Blood splat
    if blood:
        pygame.draw.circle(WIN, BLOOD_RED, (x+10, y+10), 18)
        pygame.draw.circle(WIN, BLOOD_RED, (x, y+16), 10)

    # Gun flash
    if flash:
        pygame.draw.circle(WIN, GOLD, (x-10, y+10), 18)

def draw_ui(offset):
    ox, oy = offset
    hud = FONT.render(f"Score: {score}   Lives: {lives}   Level: {level}", True, WHITE)
    WIN.blit(hud, (20 + ox, 20 + oy))

    inst = SMALL.render("SPACE: Shoot   •   R: Restart   •   ESC: Quit", True, WHITE)
    WIN.blit(inst, (WIDTH//2 - inst.get_width()//2 + ox, HEIGHT - 32 + oy))

    # Weapon display
    current_weapon = get_current_weapon()
    weapon_text = MID.render(f"Weapon: {current_weapon['name']}", True, WHITE)
    WIN.blit(weapon_text, (20 + ox, 60 + oy))

    # Next weapon info
    next_weapon = None
    for w in WEAPONS:
        if w["unlock_level"] > level:
            next_weapon = w
            break
    if next_weapon:
        nxt = SMALL.render(
            f"Next: {next_weapon['name']} unlocks at Level {next_weapon['unlock_level']}",
            True, (230, 230, 200)
        )
        WIN.blit(nxt, (20 + ox, 86 + oy))

def draw_message_center(text, color, offset, dy=0):
    ox, oy = offset
    msg = FONT.render(text, True, color)
    WIN.blit(msg, (WIDTH//2 - msg.get_width()//2 + ox, HEIGHT//2 - 50 + oy + dy))

def draw_taunt(offset):
    if not TAUNT_TEXT:
        return
    ox, oy = offset
    t = SMALL.render(TAUNT_TEXT, True, (255, 240, 200))
    WIN.blit(t, (WIDTH//2 - t.get_width()//2 + ox, HEIGHT//2 + 8 + oy))

# -------------------- MAIN LOOP --------------------
def main():
    global game_state, countdown_number, countdown_start, enemy_ready, enemy_fired
    global player_bullet, enemy_bullet, duel_start_time, enemy_fire_delay
    global player_flash_time, enemy_flash_time
    global enemy_blood_timer, player_blood_timer
    global shake_time_remaining, shake_magnitude, lives

    init_tumbleweeds()
    running = True
    last_time = time.time()

    while running:
        dt_ms = clock.tick(FPS)
        dt = dt_ms / 1000.0
        now = time.time()

        # ------------- EVENTS -------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if event.key == pygame.K_r:
                    # Restart from scratch
                    start_new_game()
                    game_state = "COUNTDOWN"

                if event.key == pygame.K_SPACE:
                    # handle depending on state
                    if game_state == "TITLE":
                        start_new_game()
                        game_state = "COUNTDOWN"
                        countdown_start = now

                    elif game_state == "COUNTDOWN":
                        # early shot
                        if lives > 0:
                            end_round("early")

                    elif game_state == "DUEL":
                        # player shoots
                        if player_bullet is None:
                            if GUNSHOT:
                                GUNSHOT.play()
                            player_flash_time = now
                            w = get_current_weapon()
                            player_bullet = {"x": SHERIFF_X + 60, "y": SHERIFF_Y - 10, "speed": w["bullet_speed"], "color": w["color"]}
                            game_state = "PLAYER_BULLET"

        # ------------- UPDATE GAME LOGIC -------------
        # Countdown state
        if game_state == "COUNTDOWN":
            elapsed = now - countdown_start
            if elapsed < 1:
                countdown_number = 3
            elif elapsed < 2:
                countdown_number = 2
            elif elapsed < 3:
                countdown_number = 1
            elif elapsed < 3.5:
                countdown_number = "DRAW!"
            else:
                # Begin duel
                if not enemy_ready:
                    begin_duel()

        # Duel state: enemy AI
        if game_state == "DUEL":
            if not enemy_fired and (now - duel_start_time) >= enemy_fire_delay:
                # enemy fires
                enemy_fired = True
                if GUNSHOT:
                    GUNSHOT.play()
                enemy_flash_time = now
                enemy_bullet = {"x": BANDIT_X - 10, "y": BANDIT_Y - 10, "speed": 11, "color": RED}
                game_state = "ENEMY_BULLET"

        # Player bullet movement
        if player_bullet is not None:
            player_bullet["x"] += player_bullet["speed"]
            if player_bullet["x"] >= BANDIT_X - 10:
                # Hit bandit
                enemy_blood_timer = 0.4
                end_round("win")
                player_bullet = None

        # Enemy bullet movement
        if enemy_bullet is not None:
            enemy_bullet["x"] -= enemy_bullet["speed"]
            if enemy_bullet["x"] <= SHERIFF_X + 30:
                # Hit sheriff
                player_blood_timer = 0.4
                end_round("lose")
                enemy_bullet = None

        # Reduce timers
        if enemy_blood_timer > 0:
            enemy_blood_timer -= dt
            if enemy_blood_timer < 0:
                enemy_blood_timer = 0
        if player_blood_timer > 0:
            player_blood_timer -= dt
            if player_blood_timer < 0:
                player_blood_timer = 0

        # Screen shake timer
        if shake_time_remaining > 0:
            shake_time_remaining -= dt
            if shake_time_remaining < 0:
                shake_time_remaining = 0

        # Round end transitions
        if game_state == "ROUND_END":
            update_round_end()

        # Game over state
        if game_state == "GAME_OVER":
            # no auto restart, just wait for R or ESC
            pass

        # Tumbleweed update
        for t in tumbleweeds:
            t["x"] -= t["speed"]
            if t["x"] < -t["size"] * 2:
                t["x"] = WIDTH + random.randint(10, 200)
                t["y"] = HEIGHT//2 + random.randint(60, 120)
                t["speed"] = random.uniform(1.5, 3.0)
                t["size"] = random.randint(14, 24)

        # ------------- DRAW -------------
        # Screen shake offset
        if shake_time_remaining > 0:
            mag = shake_magnitude
            ox = random.randint(-mag, mag)
            oy = random.randint(-mag, mag)
        else:
            ox, oy = 0, 0
        offset = (ox, oy)

        draw_background(offset)
        draw_tumbleweeds(offset)

        # Determine flash/blood flags
        sheriff_flash = (now - player_flash_time) < PLAYER_FLASH_DURATION
        bandit_flash = (now - enemy_flash_time) < ENEMY_FLASH_DURATION
        sheriff_blood = (player_blood_timer > 0)
        bandit_blood = (enemy_blood_timer > 0)

        draw_sheriff(offset, flash=sheriff_flash, blood=sheriff_blood)
        draw_bandit(offset, ready=enemy_ready, blood=bandit_blood, flash=bandit_flash)

        # Draw bullets
        if player_bullet is not None:
            pygame.draw.circle(WIN, player_bullet["color"],
                               (int(player_bullet["x"] + ox), int(player_bullet["y"] + oy)), 7)

        if enemy_bullet is not None:
            pygame.draw.circle(WIN, enemy_bullet["color"],
                               (int(enemy_bullet["x"] + ox), int(enemy_bullet["y"] + oy)), 7)

        draw_ui(offset)

        # State messages
        if game_state == "TITLE":
            draw_message_center("Sheriff Duel - Cowboy Showdown", GOLD, offset, dy=-10)
            msg2 = SMALL.render("Press SPACE to start", True, WHITE)
            WIN.blit(msg2, (WIDTH//2 - msg2.get_width()//2 + ox, HEIGHT//2 + 20 + oy))

        elif game_state == "COUNTDOWN":
            if isinstance(countdown_number, int):
                draw_message_center(str(countdown_number), GOLD, offset)
            else:  # "DRAW!"
                draw_message_center("DRAW!", RED, offset)

        elif game_state in ("DUEL", "PLAYER_BULLET", "ENEMY_BULLET"):
            draw_message_center("DRAW!!! SHOOT!!", RED, offset)

        elif game_state == "ROUND_END":
            if round_result == "win":
                draw_message_center("You hit him!", GREEN, offset)
            elif round_result == "lose":
                draw_message_center("You got shot!", RED, offset)
            elif round_result == "early":
                draw_message_center("Shot too early!", RED, offset)
            draw_taunt(offset)

        elif game_state == "GAME_OVER":
            draw_message_center("GAME OVER", RED, offset, dy=-10)
            msg2 = SMALL.render("Press R to restart or ESC to quit", True, WHITE)
            WIN.blit(msg2, (WIDTH//2 - msg2.get_width()//2 + ox, HEIGHT//2 + 20 + oy))

        pygame.display.flip()

    pygame.quit()
    print("Final Score:", score)


if __name__ == "__main__":
    main()
