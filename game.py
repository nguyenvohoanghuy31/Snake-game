import pygame
import random
import sys
import os
import math
import argparse

try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except Exception:
    pass
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        try:
            import codecs
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
            sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
        except Exception:
            pass



pygame.init()
try:
    pygame.mixer.init()
except Exception as e:
    print("Warning: Could not initialize mixer:", e)


COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_TONGUE = (255, 0, 0)
COLOR_SHADOW = (0, 0, 0, 100)
SHADOW_OFFSET = 6
COLOR_BG_LIGHT = (142, 204, 57)
COLOR_BG_DARK = (124, 184, 46)
COLOR_SCORE_TEXT = (40, 40, 40)
COLOR_SNAKE = (76, 119, 219)
COLOR_SNAKE_EYE = (255, 255, 255)
COLOR_FOOD_APPLE = (223, 75, 61)
COLOR_FOOD_GOLDEN = (239, 187, 83)
COLOR_GAME_OVER = (200, 0, 0)
COLOR_BUTTON_PLAY = (76, 119, 219)
COLOR_BUTTON_OTHER = (130, 130, 130)
COLOR_GLASS_BG = (255, 255, 255, 40)
COLOR_GLASS_BORDER = (255, 255, 255, 90)
COLOR_GLASS_TEXT = (255, 255, 255, 240)

COLOR_OUTLINE_DARK = (20, 20, 20)
COLOR_OUTLINE_LIGHT = (230, 230, 230)

COLOR_STEM = (139, 69, 19) # Màu nâu
COLOR_LEAF = (0, 150, 0)   # Màu xanh lá

BLOCK_SIZE = 40
GRID_WIDTH = 32
GRID_HEIGHT = 18
INFO_BAR_HEIGHT = 80
INFO_BAR_GRID_HEIGHT = INFO_BAR_HEIGHT // BLOCK_SIZE
GAME_WIDTH = GRID_WIDTH * BLOCK_SIZE
GAME_HEIGHT = GRID_HEIGHT * BLOCK_SIZE
DEFAULT_WINDOW_WIDTH = 1280
DEFAULT_WINDOW_HEIGHT = 720
SNAKE_CORNER_RADIUS = 12
TARGET_FPS = 120
BASE_SPEED = 10

# --- Canvas and Screen ---
game_canvas = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
shadow_canvas = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
screen = pygame.display.set_mode((DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption('Snake Game (720p Sharp)')
clock = pygame.time.Clock()
HIGHSCORE_FILE = "highscore.txt"

# Global variables
ASSETS = {}
PULSE_COUNTER = 0
fullscreen = False
EFFECT_LIST = []
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- FONTS ---
PREFERRED_SYSFONTS = ["dejavusans", "noto sans", "segoeui", "tahoma", "arial"]
CUSTOM_FONT_FILENAME = "font.ttf"

def find_system_font():
    for name in PREFERRED_SYSFONTS:
        path = pygame.font.match_font(name, bold=False, italic=False)
        if path:
            return path
    return None

def get_font_obj(size):
    custom_font_path = os.path.join(SCRIPT_DIR, CUSTOM_FONT_FILENAME)
    if os.path.exists(custom_font_path):
        try:
            return pygame.font.Font(custom_font_path, size)
        except Exception as e:
            print(f"Lỗi tải font tùy chỉnh '{CUSTOM_FONT_FILENAME}': {e}")

    sys_font_path = find_system_font()
    if sys_font_path:
        try:
            return pygame.font.Font(sys_font_path, size)
        except Exception:
            pass

    return pygame.font.Font(None, size)

font_title = get_font_obj(120)
font_button = get_font_obj(45)
font_info = get_font_obj(35)
font_score = get_font_obj(32)
font_game_over = get_font_obj(150)
font_pause = get_font_obj(100)

# --- ASSET LOADING ---
def load_assets():
    global sound_eat, sound_game_over, ASSETS
    ASSETS = {}
    ASSET_DIR = os.path.join(SCRIPT_DIR, "assets")

    def try_load_image(fname, size=None, key=None):
        if key is None:
            key = os.path.splitext(fname)[0]
        path = os.path.join(ASSET_DIR, fname)
        if not os.path.exists(path):
            ASSETS[key] = None; return None
        try:
            img = pygame.image.load(path).convert_alpha()
            if size:
                img = pygame.transform.smoothscale(img, size)
            ASSETS[key] = img
            return img
        except Exception:
            ASSETS[key] = None; return None



    def try_load_sound(fname):
        path = os.path.join(ASSET_DIR, fname)
        if not os.path.exists(path):
            return None
        try:
            s = pygame.mixer.Sound(path)
            s.set_volume(0.5)
            return s
        except Exception:
            return None

    def try_load_music(fname):
        path = os.path.join(ASSET_DIR, fname)
        if not os.path.exists(path):
            print(f"Warning: Music file not found: {fname}")
            return False
        try:
            pygame.mixer.music.load(path)
            return True
        except Exception as e:
            print(f"Warning: Could not load music '{fname}'. Error: {e}")
            return False

    try_load_image("apple.png", size=None, key="apple")
    try_load_image("golden_apple.png", size=None, key="golden_apple")
    try_load_image("background_lose.png", size=(GAME_WIDTH, GAME_HEIGHT), key="background_lose")
    sound_eat_temp = try_load_sound("an_moi.wav")
    sound_game_over_temp = try_load_sound("thua_game.wav")
    

    sound_eat = sound_eat_temp if sound_eat_temp else DummySound()
    sound_game_over = sound_game_over_temp if sound_game_over_temp else DummySound()
    
    try_load_music("background_music.mp3")

# --- Helper ---
def lerp(a, b, t):
    return a + (b - a) * t

# --- DRAWING FUNCTIONS ---
def draw_checkerboard_bg():
    game_canvas.fill(COLOR_BG_LIGHT)
    for y in range(INFO_BAR_GRID_HEIGHT, GRID_HEIGHT):
        for x in range(0, GRID_WIDTH):
            if (x + y) % 2 == 0:
                pygame.draw.rect(game_canvas, COLOR_BG_DARK,
                                 (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
    info_bar_rect = pygame.Rect(0, 0, GAME_WIDTH, INFO_BAR_HEIGHT)
    pygame.draw.rect(game_canvas, COLOR_BG_LIGHT, info_bar_rect,
                     border_bottom_left_radius=20, border_bottom_right_radius=20)

def draw_to_screen(canvas_to_draw):
    global screen
    screen_size = screen.get_size()
    if screen_size[0] == 0 or screen_size[1] == 0:
        return
    if screen_size != (GAME_WIDTH, GAME_HEIGHT):
        scaled_canvas = pygame.transform.smoothscale(canvas_to_draw, screen_size)
        screen.blit(scaled_canvas, (0, 0))
    else:
        screen.blit(canvas_to_draw, (0, 0))
    pygame.display.flip()

def toggle_fullscreen():
    global fullscreen, screen
    fullscreen = not fullscreen
    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT), pygame.RESIZABLE)

def play_flash_effect():
    flash_surf = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
    flash_surf.fill(COLOR_WHITE)
    game_canvas.blit(flash_surf, (0, 0))
    draw_to_screen(game_canvas)
    pygame.time.wait(75)

def draw_text_with_outline(surface, text_str, font, pos, text_color, outline_color, outline_px=2):
    text_surface = font.render(text_str, True, text_color)
    outline_surface = font.render(text_str, True, outline_color)
    x, y = pos
    outline_positions = [
        (x - outline_px, y - outline_px), (x + outline_px, y - outline_px),
        (x - outline_px, y + outline_px), (x + outline_px, y + outline_px),
        (x - outline_px, y), (x + outline_px, y),
        (x, y - outline_px), (x, y + outline_px),
    ]
    for outline_pos in outline_positions:
        surface.blit(outline_surface, outline_pos)
    surface.blit(text_surface, pos)

def draw_button(text, x, y, width, height, bg_color, text_color):
    button_rect = pygame.Rect(x, y, width, height)
    mouse_x, mouse_y = pygame.mouse.get_pos()
    win_w, win_h = screen.get_size()
    if win_w == 0 or win_h == 0:
        canvas_x, canvas_y = -1, -1
    else:
        canvas_x = mouse_x * (GAME_WIDTH / win_w)
        canvas_y = mouse_y * (GAME_HEIGHT / win_h)
    is_hovered = button_rect.collidepoint((canvas_x, canvas_y))
    current_color = bg_color
    if is_hovered:
        current_color = (min(255, bg_color[0] + 20), min(255, bg_color[1] + 20), min(255, bg_color[2] + 20))
    pygame.draw.rect(game_canvas, current_color, button_rect, border_radius=10)

    text_obj = font_button.render(text, True, text_color)
    text_pos = (x + (width - text_obj.get_width()) / 2, y + (height - text_obj.get_height()) / 2)
    draw_text_with_outline(game_canvas, text, font_button, text_pos,
                           text_color, COLOR_OUTLINE_DARK, 2)
    return button_rect

def _draw_snake_internal(surface, visual_body, color, radius, direction, tongue=False):
    if not visual_body:
        return
    for pos in visual_body:
        body_rect = pygame.Rect(pos[0], pos[1], BLOCK_SIZE, BLOCK_SIZE)
        pygame.draw.rect(surface, color, body_rect, border_radius=radius)
    if len(visual_body) > 0:
        head_pos = visual_body[0]
        head_rect = pygame.Rect(head_pos[0], head_pos[1], BLOCK_SIZE, BLOCK_SIZE)
        pygame.draw.rect(surface, color, head_rect, border_radius=radius)
        if tongue:
            eye_size = max(3, BLOCK_SIZE // 6)
            pupil_size = max(1, BLOCK_SIZE // 15)
            eye_offset = BLOCK_SIZE // 4
            center_x = head_pos[0] + BLOCK_SIZE // 2
            center_y = head_pos[1] + BLOCK_SIZE // 2
            if direction == 'UP':
                eye1_pos = (center_x - eye_offset, center_y - eye_offset)
                eye2_pos = (center_x + eye_offset, center_y - eye_offset)
            elif direction == 'DOWN':
                eye1_pos = (center_x - eye_offset, center_y + eye_offset)
                eye2_pos = (center_x + eye_offset, center_y + eye_offset)
            elif direction == 'LEFT':
                eye1_pos = (center_x - eye_offset, center_y - eye_offset)
                eye2_pos = (center_x - eye_offset, center_y + eye_offset)
            else:  # RIGHT
                eye1_pos = (center_x + eye_offset, center_y - eye_offset)
                eye2_pos = (center_x + eye_offset, center_y + eye_offset)
            pygame.draw.circle(surface, COLOR_SNAKE_EYE, eye1_pos, eye_size)
            pygame.draw.circle(surface, COLOR_SNAKE_EYE, eye2_pos, eye_size)
            pygame.draw.circle(surface, COLOR_BLACK, eye1_pos, pupil_size)
            pygame.draw.circle(surface, COLOR_BLACK, eye2_pos, pupil_size)
            if PULSE_COUNTER % 100 < 8:
                tongue_length = BLOCK_SIZE // 2
                tongue_width = max(2, BLOCK_SIZE // 10)
                tongue_rect = None
                if direction == 'UP':
                    tongue_rect = pygame.Rect(center_x - tongue_width // 2, head_pos[1] - tongue_length, tongue_width, tongue_length)
                elif direction == 'DOWN':
                    tongue_rect = pygame.Rect(center_x - tongue_width // 2, head_pos[1] + BLOCK_SIZE, tongue_width, tongue_length)
                elif direction == 'LEFT':
                    tongue_rect = pygame.Rect(head_pos[0] - tongue_length, center_y - tongue_width // 2, tongue_length, tongue_width)
                elif direction == 'RIGHT':
                    tongue_rect = pygame.Rect(head_pos[0] + BLOCK_SIZE, center_y - tongue_width // 2, tongue_length, tongue_width)
                if tongue_rect:
                    pygame.draw.rect(surface, COLOR_TONGUE, tongue_rect, border_radius=2)

def draw_snake_smooth(snake_body, prev_snake_body, t, direction):
    global shadow_canvas
    visual_body = []
    play_height = GAME_HEIGHT - INFO_BAR_HEIGHT

    for i in range(len(snake_body)):
        current_grid_pos = snake_body[i]
        prev_grid_pos = prev_snake_body[i]

        vis_x = lerp(prev_grid_pos[0], current_grid_pos[0], t)
        if abs(current_grid_pos[0] - prev_grid_pos[0]) > GAME_WIDTH / 2:
            if current_grid_pos[0] > prev_grid_pos[0]:
                vis_x = lerp(prev_grid_pos[0] - GAME_WIDTH, current_grid_pos[0], t) % GAME_WIDTH
            else:
                vis_x = lerp(prev_grid_pos[0] + GAME_WIDTH, current_grid_pos[0], t) % GAME_WIDTH

        vis_y = lerp(prev_grid_pos[1], current_grid_pos[1], t)

        visual_body.append((vis_x, vis_y))

    shadow_canvas.fill((0, 0, 0, 0))
    _draw_snake_internal(shadow_canvas, visual_body, COLOR_SHADOW, SNAKE_CORNER_RADIUS, direction, tongue=False)
    game_canvas.blit(shadow_canvas, (SHADOW_OFFSET, SHADOW_OFFSET))
    _draw_snake_internal(game_canvas, visual_body, COLOR_SNAKE, SNAKE_CORNER_RADIUS, direction, tongue=True)

def draw_food(food_pos, sprite_key):
    global PULSE_COUNTER
    if not food_pos:
        return
    draw_x, draw_y = food_pos[0], food_pos[1]
    sprite = ASSETS.get(sprite_key)

    if sprite:
           scale_factor = 1.8
           scaled_size = int(BLOCK_SIZE * scale_factor)
           sprite_scaled = pygame.transform.smoothscale(sprite, (scaled_size, scaled_size))
           offset = (scaled_size - BLOCK_SIZE) // 2
           game_canvas.blit(sprite_scaled, (draw_x - offset, draw_y - offset))
           return

    color = COLOR_FOOD_APPLE
    if sprite_key == 'golden_apple':
        color = COLOR_FOOD_GOLDEN
        pulse_amplitude = 0.1
        scale_factor = 1 + abs(math.sin(PULSE_COUNTER * 0.15)) * pulse_amplitude
        apple_radius = int(BLOCK_SIZE * 0.4 * scale_factor)
    else:
        apple_radius = int(BLOCK_SIZE * 0.4)

    shadow_radius = apple_radius
    shadow_center_x = draw_x + BLOCK_SIZE // 2 + SHADOW_OFFSET
    shadow_center_y = draw_y + BLOCK_SIZE // 2 + SHADOW_OFFSET + 2

    shadow_surf = pygame.Surface(game_canvas.get_size(), pygame.SRCALPHA)
    pygame.draw.circle(shadow_surf, COLOR_SHADOW, (shadow_center_x, shadow_center_y), shadow_radius)
    game_canvas.blit(shadow_surf, (0,0))

    apple_center_x = draw_x + BLOCK_SIZE // 2
    apple_center_y = draw_y + BLOCK_SIZE // 2 + 2

    pygame.draw.circle(game_canvas, color, (apple_center_x, apple_center_y), apple_radius)

    stem_width = max(3, int(BLOCK_SIZE * 0.1))
    stem_height = max(5, int(BLOCK_SIZE * 0.2))
    stem_x = apple_center_x - stem_width // 2
    stem_y = apple_center_y - apple_radius - stem_height + 2
    stem_rect = pygame.Rect(stem_x, stem_y, stem_width, stem_height)
    pygame.draw.rect(game_canvas, COLOR_STEM, stem_rect)

    leaf_width = max(8, int(BLOCK_SIZE * 0.3))
    leaf_height = max(5, int(BLOCK_SIZE * 0.2))
    leaf_x = apple_center_x - leaf_width - 2
    leaf_y = apple_center_y - apple_radius
    leaf_rect = pygame.Rect(leaf_x, leaf_y, leaf_width, leaf_height)
    pygame.draw.ellipse(game_canvas, COLOR_LEAF, leaf_rect)

def draw_effects():
    global EFFECT_LIST
    for i in range(len(EFFECT_LIST) - 1, -1, -1):
        effect = EFFECT_LIST[i]
        effect['timer'] -= 1
        if effect['timer'] <= 0:
            EFFECT_LIST.pop(i)
            continue
        if effect['type'] == 'sparkle':
            MAX_FRAMES_SPARKLE = 10
            progress = (MAX_FRAMES_SPARKLE - effect['timer']) / MAX_FRAMES_SPARKLE
            radius = int(progress * BLOCK_SIZE * 0.8)
            alpha = int((1.0 - progress) * 200)
            if alpha > 0 and radius > 0:
                center_x = effect['pos'][0] + BLOCK_SIZE // 2
                center_y = effect['pos'][1] + BLOCK_SIZE // 2
                glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 255, 100, alpha), (radius, radius), radius)
                game_canvas.blit(glow_surf, (center_x - radius, center_y - radius))

def display_score(score, high_score):
    BAR_HEIGHT = INFO_BAR_HEIGHT - 20
    BAR_RADIUS = 15
    BAR_PADDING_X = 20
    BAR_WIDTH = GAME_WIDTH - (BAR_PADDING_X * 2)
    bar_x = BAR_PADDING_X
    bar_y = (INFO_BAR_HEIGHT - BAR_HEIGHT) // 2
    score_bar_rect = pygame.Rect(bar_x, bar_y, BAR_WIDTH, BAR_HEIGHT)

    glass_surf = pygame.Surface(score_bar_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(glass_surf, COLOR_GLASS_BG, glass_surf.get_rect(), border_radius=BAR_RADIUS)
    pygame.draw.rect(glass_surf, COLOR_GLASS_BORDER, glass_surf.get_rect(), width=2, border_radius=BAR_RADIUS)
    game_canvas.blit(glass_surf, score_bar_rect.topleft)

    score_text_obj = font_score.render(f"Score: {score}", True, COLOR_SCORE_TEXT)
    high_score_text_obj = font_score.render(f"High: {high_score}", True, COLOR_SCORE_TEXT)

    score_text_x = bar_x + 30
    score_text_y = bar_y + (BAR_HEIGHT - score_text_obj.get_height()) // 2

    high_score_text_x = bar_x + BAR_WIDTH - high_score_text_obj.get_width() - 30
    high_score_text_y = bar_y + (BAR_HEIGHT - high_score_text_obj.get_height()) // 2

    draw_text_with_outline(game_canvas, f"Score: {score}", font_score,
                          (score_text_x, score_text_y),
                          COLOR_SCORE_TEXT, COLOR_OUTLINE_LIGHT, 2)

    draw_text_with_outline(game_canvas, f"High: {high_score}", font_score,
                          (high_score_text_x, high_score_text_y),
                          COLOR_SCORE_TEXT, COLOR_OUTLINE_LIGHT, 2)

def load_high_score():
    try:
        with open(os.path.join(SCRIPT_DIR, HIGHSCORE_FILE), "r", encoding="utf-8") as f:
            return int(f.read())
    except (FileNotFoundError, ValueError):
        return 0

def save_high_score(score):
    try:
        with open(os.path.join(SCRIPT_DIR, HIGHSCORE_FILE), "w", encoding="utf-8") as f:
            f.write(str(score))
    except Exception as e:
        print("Warning: Could not save high score. Error:", e)

def pause_game():
    global screen
    paused = True
    overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    game_canvas.blit(overlay, (0, 0))

    pause_text_obj = font_pause.render("PAUSED", True, COLOR_WHITE)
    pause_pos = (GAME_WIDTH / 2 - pause_text_obj.get_width() / 2, GAME_HEIGHT / 2 - pause_text_obj.get_height() / 2)
    draw_text_with_outline(game_canvas, "PAUSED", font_pause,
                           pause_pos, COLOR_WHITE, COLOR_OUTLINE_DARK, 3)

    info_text_obj = font_info.render("Press 'P' to continue", True, COLOR_WHITE)
    info_pos = (GAME_WIDTH / 2 - info_text_obj.get_width() / 2, GAME_HEIGHT / 2 + 100)
    draw_text_with_outline(game_canvas, "Press 'P' to continue", font_info,
                           info_pos, COLOR_WHITE, COLOR_OUTLINE_DARK, 2)

    draw_to_screen(game_canvas)

    while paused:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = False
                if event.key == pygame.K_F11:
                    toggle_fullscreen()
                    game_canvas.blit(overlay, (0, 0))
                    draw_text_with_outline(game_canvas, "PAUSED", font_pause,
                                           pause_pos, COLOR_WHITE, COLOR_OUTLINE_DARK, 3)
                    draw_text_with_outline(game_canvas, "Press 'P' to continue", font_info,
                                           info_pos, COLOR_WHITE, COLOR_OUTLINE_DARK, 2)
                    draw_to_screen(game_canvas)
            elif event.type == pygame.VIDEORESIZE:
                game_canvas.blit(overlay, (0, 0))
                draw_text_with_outline(game_canvas, "PAUSED", font_pause,
                                        pause_pos, COLOR_WHITE, COLOR_OUTLINE_DARK, 3)
                draw_text_with_outline(game_canvas, "Press 'P' to continue", font_info,
                                        info_pos, COLOR_WHITE, COLOR_OUTLINE_DARK, 2)
                draw_to_screen(game_canvas)
        clock.tick(15)

def game_loop(high_score, wrap_mode):
    global PULSE_COUNTER, EFFECT_LIST, screen
    snake_pos = [120, INFO_BAR_HEIGHT]
    snake_body = [[120, INFO_BAR_HEIGHT], [80, INFO_BAR_HEIGHT], [40, INFO_BAR_HEIGHT]]
    prev_snake_body = list(snake_body)
    direction = 'RIGHT'
    change_to = direction

    def spawn_food():
        while True:
            new_pos = [random.randrange(0, GRID_WIDTH) * BLOCK_SIZE,
                       random.randrange(INFO_BAR_GRID_HEIGHT, GRID_HEIGHT) * BLOCK_SIZE]
            if new_pos not in snake_body:
                return new_pos

    food_pos = spawn_food()
    golden_apple_pos = None
    golden_apple_timer = 0
    GOLDEN_APPLE_LIFESPAN = 150
    score = 0
    current_speed = BASE_SPEED
    logic_timer = 0.0

    while True:
        dt = clock.tick(TARGET_FPS) / 1000.0
        logic_timer += dt
        PULSE_COUNTER += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    toggle_fullscreen()
                if event.key == pygame.K_p:
                    pause_game()
                if event.key == pygame.K_UP and direction != 'DOWN':
                    change_to = 'UP'
                if event.key == pygame.K_DOWN and direction != 'UP':
                    change_to = 'DOWN'
                if event.key == pygame.K_LEFT and direction != 'RIGHT':
                    change_to = 'LEFT'
                if event.key == pygame.K_RIGHT and direction != 'LEFT':
                    change_to = 'RIGHT'
            elif event.type == pygame.VIDEORESIZE:
                pass

        time_per_step = 1.0 / current_speed
        while logic_timer >= time_per_step:
            logic_timer -= time_per_step
            prev_snake_body = list(snake_body)
            direction = change_to

            if direction == 'UP':
                snake_pos[1] -= BLOCK_SIZE
            if direction == 'DOWN':
                snake_pos[1] += BLOCK_SIZE
            if direction == 'LEFT':
                snake_pos[0] -= BLOCK_SIZE
            if direction == 'RIGHT':
                snake_pos[0] += BLOCK_SIZE

            if (snake_pos[0] < 0 or snake_pos[0] >= GAME_WIDTH or
                snake_pos[1] < INFO_BAR_HEIGHT or snake_pos[1] >= GAME_HEIGHT):
                sound_game_over.play()
                play_flash_effect()
                pygame.time.wait(500)
                return score

            snake_body.insert(0, list(snake_pos))
            ate_something = False
            eat_pos = None

            if snake_pos[0] == food_pos[0] and snake_pos[1] == food_pos[1]:
                ate_something = True
                eat_pos = list(food_pos)
                score += 10
                sound_eat.play()
                if score % 50 == 0:
                    current_speed += 1
                food_pos = spawn_food()

            if golden_apple_pos and snake_pos[0] == golden_apple_pos[0] and snake_pos[1] == golden_apple_pos[1]:
                ate_something = True
                eat_pos = list(golden_apple_pos)
                score += 50
                sound_eat.play()
                golden_apple_pos = None
                golden_apple_timer = 0

            if not ate_something:
                snake_body.pop()
            else:
                if prev_snake_body:
                    prev_snake_body.append(prev_snake_body[-1])
                if eat_pos:
                    EFFECT_LIST.append({'type': 'sparkle', 'pos': eat_pos, 'timer': 10})

                if wrap_mode:
                    snake_body.reverse()
                    snake_pos[:] = snake_body[0]

                    if direction == 'UP': direction = 'DOWN'
                    elif direction == 'DOWN': direction = 'UP'
                    elif direction == 'LEFT': direction = 'RIGHT'
                    elif direction == 'RIGHT': direction = 'LEFT'

                    change_to = direction

            if golden_apple_pos:
                golden_apple_timer -= 1
                if golden_apple_timer <= 0:
                    golden_apple_pos = None
            elif random.randrange(0, 400) == 1:
                golden_apple_pos = spawn_food()
                golden_apple_timer = GOLDEN_APPLE_LIFESPAN

            for block in snake_body[1:]:
                if snake_pos[0] == block[0] and snake_pos[1] == block[1]:
                    sound_game_over.play()
                    play_flash_effect()
                    pygame.time.wait(500)
                    return score

        # DRAW
        t = logic_timer / time_per_step if time_per_step > 0 else 1.0
        draw_checkerboard_bg()
        draw_food(food_pos, 'apple')
        draw_food(golden_apple_pos, 'golden_apple')
        if len(prev_snake_body) == len(snake_body):
            draw_snake_smooth(snake_body, prev_snake_body, t, direction)
        else:
            draw_snake_smooth(snake_body, snake_body, 1.0, direction)
        draw_effects()
        display_score(score, high_score)
        draw_to_screen(game_canvas)

def game_over_screen(score, high_score):
    global screen

    lose_text_obj = font_game_over.render("LOSE", True, COLOR_GAME_OVER)
    lose_pos = (GAME_WIDTH / 2 - lose_text_obj.get_width() / 2, GAME_HEIGHT * 0.1)

    score_text_obj = font_button.render(f"Your Score: {score}", True, COLOR_SCORE_TEXT)
    score_pos = (GAME_WIDTH / 2 - score_text_obj.get_width() / 2, GAME_HEIGHT * 0.35)

    high_score_text_obj = font_button.render(f"High Score: {high_score}", True, COLOR_SCORE_TEXT)
    high_score_pos = (GAME_WIDTH / 2 - high_score_text_obj.get_width() / 2, GAME_HEIGHT * 0.45)

    btn_w = 500
    btn_h = 70
    btn_spacing = 30
    btn_x = (GAME_WIDTH - btn_w) / 2
    btn_y_start = GAME_HEIGHT * 0.6
    
    btn_play_again = pygame.Rect(btn_x, btn_y_start, btn_w, btn_h)
    btn_high_scores = pygame.Rect(btn_x, btn_y_start + btn_h + btn_spacing, btn_w, btn_h)
    btn_home = pygame.Rect(btn_x, btn_y_start + 2 * (btn_h + btn_spacing), btn_w, btn_h)
    
    while True:
        clicked = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    clicked = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    toggle_fullscreen() # Cho phép F11

        lose_bg_img = ASSETS.get("background_lose")
        if lose_bg_img:
            game_canvas.blit(lose_bg_img, (0, 0))
        else:
            draw_checkerboard_bg() 

        draw_text_with_outline(game_canvas, "LOSE", font_game_over,
                               lose_pos, COLOR_GAME_OVER, COLOR_OUTLINE_DARK, 4)
        
        draw_text_with_outline(game_canvas, f"Your Score: {score}", font_button,
                               score_pos, COLOR_SCORE_TEXT, COLOR_OUTLINE_LIGHT, 2)
        draw_text_with_outline(game_canvas, f"High Score: {high_score}", font_button,
                               high_score_pos, COLOR_SCORE_TEXT, COLOR_OUTLINE_LIGHT, 2)
        draw_button("Play Again", btn_play_again.x, btn_play_again.y, btn_play_again.w, btn_play_again.h,
                    COLOR_BUTTON_PLAY, COLOR_WHITE)
        draw_button("High Scores", btn_high_scores.x, btn_high_scores.y, btn_high_scores.w, btn_high_scores.h,
                    COLOR_BUTTON_OTHER, COLOR_WHITE)
        draw_button("Home", btn_home.x, btn_home.y, btn_home.w, btn_home.h,
                    COLOR_BUTTON_OTHER, COLOR_WHITE)

        draw_to_screen(game_canvas)


        if clicked:

            mouse_x, mouse_y = pygame.mouse.get_pos()
            win_w, win_h = screen.get_size()
            if win_w == 0 or win_h == 0: continue
            
            canvas_x = mouse_x * (GAME_WIDTH / win_w)
            canvas_y = mouse_y * (GAME_HEIGHT / win_h)
            
            if btn_play_again.collidepoint((canvas_x, canvas_y)):
                return "PLAY_AGAIN" 
                
            if btn_high_scores.collidepoint((canvas_x, canvas_y)):
                return "HIGH_SCORES" 
                
            if btn_home.collidepoint((canvas_x, canvas_y)):
                pygame.quit() 
                sys.exit()

        clock.tick(60)

def high_score_screen(high_score):
    global screen
    
    title_text_obj = font_title.render("High Score", True, COLOR_SCORE_TEXT)
    title_pos = (GAME_WIDTH / 2 - title_text_obj.get_width() / 2, GAME_HEIGHT * 0.2)
    
    score_text_obj = font_game_over.render(f"{high_score}", True, COLOR_FOOD_GOLDEN)
    score_pos = (GAME_WIDTH / 2 - score_text_obj.get_width() / 2, GAME_HEIGHT * 0.4)

    btn_w = 300
    btn_h = 70
    btn_x = (GAME_WIDTH - btn_w) / 2
    btn_y = GAME_HEIGHT * 0.75
    btn_back_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

    while True:
        clicked = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    clicked = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    toggle_fullscreen()

        # --- Vẽ ---
        draw_checkerboard_bg()
        
        # Vẽ tiêu đề
        draw_text_with_outline(game_canvas, "High Score", font_title,
                               title_pos, COLOR_SCORE_TEXT, COLOR_OUTLINE_LIGHT, 3)
        
        # Vẽ điểm số
        draw_text_with_outline(game_canvas, f"{high_score}", font_game_over,
                               score_pos, COLOR_FOOD_GOLDEN, COLOR_OUTLINE_DARK, 4)
        
        # Vẽ nút "Back"
        draw_button("Back", btn_back_rect.x, btn_back_rect.y, btn_back_rect.w, btn_back_rect.h,
                    COLOR_BUTTON_OTHER, COLOR_WHITE)
        
        draw_to_screen(game_canvas)

        # --- Xử lý Click ---
        if clicked:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            win_w, win_h = screen.get_size()
            if win_w == 0 or win_h == 0: continue
            
            canvas_x = mouse_x * (GAME_WIDTH / win_w)
            canvas_y = mouse_y * (GAME_HEIGHT / win_h)

            if btn_back_rect.collidepoint((canvas_x, canvas_y)):
                return "GAME_OVER" # Quay lại màn hình thua

        clock.tick(60)

def main():
    parser = argparse.ArgumentParser(description='Snake Game (Pygame instance)')
    parser.add_argument('--wrap', action='store_true', help='Enable special mode')
    args = parser.parse_args()

    wrap_mode = args.wrap

    load_assets()
    
    try:
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(loops=-1)
    except Exception as e:
        print(f"Warning: Không thể phát nhạc nền. Error: {e}")
        
    high_score = load_high_score()
    
    game_state = "PLAYING" # Bắt đầu game luôn
    final_score = 0

    while True: # Vòng lặp chính của toàn bộ ứng dụng
        
        if game_state == "PLAYING":
            # Chạy game
            final_score = game_loop(high_score, wrap_mode)
            
            # Cập nhật high score nếu cần
            if final_score > high_score:
                high_score = final_score
                save_high_score(high_score)
                
            # Tự động chuyển trạng thái
            game_state = "GAME_OVER" 

        elif game_state == "GAME_OVER":
            # Hiển thị màn hình thua và lấy lựa chọn
            # Hàm này sẽ chạy 1 vòng lặp riêng cho đến khi có click
            next_action = game_over_screen(final_score, high_score)
            
            if next_action == "PLAY_AGAIN":
                game_state = "PLAYING" # Quay lại chơi
            elif next_action == "HIGH_SCORES":
                game_state = "HIGH_SCORES" # Đi tới màn hình điểm
            # (Nút "Home" đã tự xử lý exit)

        elif game_state == "HIGH_SCORES":
            # Hiển thị màn hình điểm cao
            # Hàm này cũng chạy 1 vòng lặp riêng
            next_action = high_score_screen(high_score)
            
            if next_action == "GAME_OVER":
                game_state = "GAME_OVER" # Quay lại màn hình thua


# (Đảm bảo dòng này vẫn ở cuối cùng)
if __name__ == '__main__':
    main()