import pygame
import random
import math
import array
import threading
import json
import sys
from datetime import datetime

# --- تنظیمات اولیه ---
pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    AUDIO_OK = True
except:
    AUDIO_OK = False

BASE_W, BASE_H = 900, 950
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("NEON TOWER STACK")
game_surface = pygame.Surface((BASE_W, BASE_H))

clock = pygame.time.Clock()
FPS = 60

# --- رنگ‌ها ---
BLACK = (0, 0, 4)
DARK_BG = (5, 3, 20)
WHITE = (255, 255, 255)
NEON_BLUE = (50, 150, 255)
NEON_CYAN = (0, 230, 255)
NEON_PURPLE = (170, 60, 255)
NEON_PINK = (255, 60, 180)
NEON_RED = (255, 50, 50)
NEON_ORANGE = (255, 160, 30)
NEON_YELLOW = (255, 230, 0)
NEON_GREEN = (50, 255, 120)
NEON_MAGENTA = (255, 0, 200)

# پالت رنگ برای بلوک‌ها
TOWER_COLORS = [
    NEON_CYAN, NEON_PINK, NEON_PURPLE, NEON_GREEN, NEON_YELLOW,
    NEON_ORANGE, NEON_BLUE, NEON_MAGENTA, NEON_RED, (100, 200, 255),
    (255, 100, 200), (150, 255, 100), (255, 200, 100), (200, 100, 255),
]

# --- فیزیک ---
BLOCK_HEIGHT = 45
BASE_BLOCK_WIDTH = 300
MIN_BLOCK_WIDTH = 30
GROUND_Y = HEIGHT - 80

# --- ذخیره ---
SAVE_FILE = "neon_tower_save.json"
settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'difficulty': 1.0,
    'screen_shake': True,
}
achievements = {
    'first_block': {'name': 'FIRST BLOCK', 'desc': 'Place your first block', 'unlocked': False, 'icon': '1'},
    'height_10': {'name': 'ROOKIE', 'desc': 'Reach 10 meters', 'unlocked': False, 'icon': 'H10'},
    'height_25': {'name': 'VETERAN', 'desc': 'Reach 25 meters', 'unlocked': False, 'icon': 'H25'},
    'height_50': {'name': 'MASTER', 'desc': 'Reach 50 meters', 'unlocked': False, 'icon': 'H50'},
    'height_100': {'name': 'LEGEND', 'desc': 'Reach 100 meters', 'unlocked': False, 'icon': 'H100'},
    'height_200': {'name': 'GRANDMASTER', 'desc': 'Reach 200 meters', 'unlocked': False, 'icon': 'H200'},
    'perfect_1': {'name': 'PERFECT!', 'desc': 'Place a perfect block', 'unlocked': False, 'icon': 'P1'},
    'perfect_5': {'name': 'PRECISE', 'desc': '5 perfect blocks', 'unlocked': False, 'icon': 'P5'},
    'perfect_10': {'name': 'SNIPER', 'desc': '10 perfect blocks', 'unlocked': False, 'icon': 'P10'},
    'perfect_25': {'name': 'PERFECTIONIST', 'desc': '25 perfect blocks', 'unlocked': False, 'icon': 'P25'},
    'combo_5': {'name': 'COMBO KING', 'desc': '5x combo', 'unlocked': False, 'icon': 'C5'},
    'combo_10': {'name': 'COMBO GOD', 'desc': '10x combo', 'unlocked': False, 'icon': 'C10'},
    'score_1000': {'name': 'SCORER', 'desc': 'Score 1000 points', 'unlocked': False, 'icon': '$1K'},
    'score_5000': {'name': 'ACE', 'desc': 'Score 5000 points', 'unlocked': False, 'icon': '$5K'},
    'no_mistake': {'name': 'FLAWLESS', 'desc': 'Reach 50m without missing', 'unlocked': False, 'icon': 'F'},
}
highscore = [0]
game_history = []
total_blocks = [0]
total_perfect = [0]
max_height = [0]


def load_save():
    global settings, achievements, highscore, game_history, total_blocks, total_perfect, max_height
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
            settings.update(data.get('settings', {}))
            for k, v in data.get('achievements', {}).items():
                if k in achievements:
                    achievements[k]['unlocked'] = v
            highscore[0] = data.get('highscore', 0)
            game_history = data.get('game_history', [])
            total_blocks[0] = data.get('total_blocks', 0)
            total_perfect[0] = data.get('total_perfect', 0)
            max_height[0] = data.get('max_height', 0)
    except:
        pass


def save_async():
    def worker():
        try:
            data = {
                'settings': settings,
                'achievements': {k: v['unlocked'] for k, v in achievements.items()},
                'highscore': highscore[0],
                'game_history': game_history[-50:],
                'total_blocks': total_blocks[0],
                'total_perfect': total_perfect[0],
                'max_height': max_height[0],
            }
            with open(SAVE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass
    threading.Thread(target=worker, daemon=True).start()


load_save()


def unlock_achievement(key):
    if key in achievements and not achievements[key]['unlocked']:
        achievements[key]['unlocked'] = True
        save_async()
        return True
    return False


def add_game_to_history(score, height, perfects, blocks, new_achs):
    entry = {
        'score': score,
        'height': height,
        'perfects': perfects,
        'blocks': blocks,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'achievements': new_achs,
    }
    game_history.append(entry)
    save_async()


# --- Font Cache ---
FONT_CACHE = {}


def get_font(size, bold=True, italic=False):
    key = (size, bold, italic)
    if key not in FONT_CACHE:
        FONT_CACHE[key] = pygame.font.SysFont("consolas", size, bold=bold, italic=italic)
    return FONT_CACHE[key]


def draw_text(surface, text, size, x, y, color, center=False, bold=True, italic=False, glow=False):
    font = get_font(size, bold, italic)
    surf = font.render(text, True, color)
    if glow:
        glow_surf = font.render(text, True, color)
        glow_surf.set_alpha(80)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            if center:
                rect = glow_surf.get_rect(center=(x + dx, y + dy))
                surface.blit(glow_surf, rect)
            else:
                surface.blit(glow_surf, (x + dx, y + dy))
    if center:
        rect = surf.get_rect(center=(x, y))
        surface.blit(surf, rect)
    else:
        surface.blit(surf, (x, y))


# --- صدا ---
sounds = {}
music_sound = [None]
sound_ready = threading.Event()


def make_sound(fs, fe, dur, vol=0.3, wave='sine'):
    if not AUDIO_OK:
        return None
    sr = 44100
    n = int(sr * dur)
    buf = array.array('h')
    for i in range(n):
        t = i / sr
        f = fs + (fe - fs) * (i / n)
        if wave == 'sine':
            val = math.sin(2 * math.pi * f * t)
        elif wave == 'square':
            val = 1.0 if math.sin(2 * math.pi * f * t) > 0 else -1.0
        elif wave == 'noise':
            val = random.uniform(-1, 1)
        elif wave == 'saw':
            val = 2 * (f * t - math.floor(f * t + 0.5))
        else:
            val = math.sin(2 * math.pi * f * t)
        env = 1.0 - (i / n)
        val *= env * vol
        buf.append(int(val * 32767))
    try:
        return pygame.mixer.Sound(buffer=buf)
    except:
        return None


def make_music_loop(bass_notes, lead_notes, note_dur, vol=0.3):
    if not AUDIO_OK:
        return None
    sr = 44100
    buf = array.array('h')
    n_notes = max(len(bass_notes), len(lead_notes))
    for idx in range(n_notes):
        n = int(sr * note_dur)
        bass = bass_notes[idx % len(bass_notes)] if bass_notes else 0
        lead = lead_notes[idx % len(lead_notes)] if lead_notes else 0
        for i in range(n):
            t = i / sr
            val = 0
            if bass > 0:
                val += (1.0 if math.sin(2 * math.pi * bass * t) > 0 else -1.0) * 0.22
            if lead > 0:
                val += 2 * (lead * t - math.floor(lead * t + 0.5)) * 0.12
                val += math.sin(2 * math.pi * lead * 2 * t) * 0.07
            if i < sr * 0.05 and idx % 2 == 0:
                val += math.sin(2 * math.pi * 60 * t * (1 - i / (sr * 0.05))) * 0.35
            if idx % 2 == 1 and i > n * 0.5:
                val += random.uniform(-0.08, 0.08)
            env = 1.0
            if i < n * 0.05:
                env = i / (n * 0.05)
            elif i > n * 0.85:
                env = 1.0 - (i - n * 0.85) / (n * 0.15)
            val *= env * vol
            buf.append(int(max(-1, min(1, val)) * 32767))
    try:
        return pygame.mixer.Sound(buffer=buf)
    except:
        return None


def build_sounds():
    sounds['place'] = make_sound(400, 600, 0.1, 0.20, 'square')
    sounds['perfect'] = make_sound(800, 1600, 0.3, 0.28, 'sine')
    sounds['cut'] = make_sound(500, 200, 0.15, 0.15, 'noise')
    sounds['gameover'] = make_sound(500, 60, 1.5, 0.30, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['combo'] = make_sound(1000, 2000, 0.2, 0.22, 'sine')
    sounds['levelup'] = make_sound(500, 1500, 0.5, 0.25, 'sine')

    bass = [65.4, 65.4, 73.4, 73.4, 82.4, 82.4, 73.4, 73.4]
    lead = [523, 587, 659, 587, 523, 494, 440, 494]
    music_sound[0] = make_music_loop(bass, lead, 0.3, 0.08)
    sound_ready.set()


threading.Thread(target=build_sounds, daemon=True).start()


def play_sound(name):
    if sound_ready.is_set() and name in sounds and sounds[name]:
        try:
            sounds[name].set_volume(settings['sfx_volume'])
            sounds[name].play()
        except:
            pass


def start_music():
    if sound_ready.is_set() and music_sound[0]:
        try:
            music_sound[0].set_volume(settings['music_volume'] * 0.5)
            music_sound[0].play(loops=-1)
        except:
            pass


def stop_music():
    if music_sound[0]:
        try:
            music_sound[0].stop()
        except:
            pass


# --- ذرات ---
particle_pool = []
active_particles = []


class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'size', 'active', 'gravity')

    def __init__(self):
        self.active = False

    def spawn(self, x, y, color, speed_mult=1.0, size_mult=1.0, life_mult=1.0, gravity=0.3):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 6) * speed_mult
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 2  # رو به بالا
        self.life = int(random.randint(20, 40) * life_mult)
        self.max_life = self.life
        self.color = color
        self.size = random.randint(2, 5) * size_mult
        self.gravity = gravity
        self.active = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.96
        self.vy *= 0.96
        self.vy += self.gravity
        self.life -= 1
        if self.life <= 0:
            self.active = False

    def draw(self, surface):
        if self.life > 0:
            alpha = self.life / self.max_life
            size = max(1, int(self.size * alpha))
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), size)


def spawn_particles(x, y, color, count, speed_mult=1.0, size_mult=1.0, life_mult=1.0, gravity=0.3):
    for _ in range(int(count)):
        p = None
        for pp in particle_pool:
            if not pp.active:
                p = pp
                break
        if p is None:
            p = Particle()
            particle_pool.append(p)
        p.spawn(x, y, color, speed_mult, size_mult, life_mult, gravity)
        active_particles.append(p)


# ============================================================
#                    Block
# ============================================================
class Block:
    def __init__(self, x, y, width, color):
        self.x = x  # موقعیت چپ
        self.y = y  # موقعیت بالا
        self.width = width
        self.height = BLOCK_HEIGHT
        self.color = color

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(self.width), self.height)

    def draw(self, surface):
        rect = self.get_rect()

        # هاله
        for hr in range(3, 0, -1):
            glow = pygame.Surface((rect.w + hr * 10, rect.h + hr * 10), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*self.color, 60 - hr * 15),
                             (0, 0, rect.w + hr * 10, rect.h + hr * 10), border_radius=6)
            surface.blit(glow, (rect.x - hr * 5, rect.y - hr * 5))

        # بدنه
        pygame.draw.rect(surface, (self.color[0] // 4, self.color[1] // 4, self.color[2] // 4),
                         rect, border_radius=6)
        pygame.draw.rect(surface, self.color, rect, 3, border_radius=6)
        pygame.draw.rect(surface, WHITE, rect, 1, border_radius=6)

        # خط درخشان بالا
        pygame.draw.line(surface, WHITE,
                         (rect.x + 5, rect.y + 3),
                         (rect.right - 5, rect.y + 3), 2)


# ============================================================
#                    Moving Block
# ============================================================
class MovingBlock(Block):
    def __init__(self, y, width, color, direction=1, speed=5):
        # از سمت چپ یا راست شروع می‌کنه
        if direction == 1:
            x = -width
        else:
            x = WIDTH
        super().__init__(x, y, width, color)
        self.direction = direction
        self.speed = speed

    def update(self, speed_mult=1.0):
        self.x += self.speed * self.direction * speed_mult

    def is_out_of_bounds(self):
        return self.x > WIDTH or self.x + self.width < 0


# ============================================================
#                    Button & Slider
# ============================================================
class Button:
    def __init__(self, x, y, w, h, text, color, hover_color=None, text_size=28):
        self.rect = pygame.Rect(x - w // 2, y - h // 2, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color if hover_color else color
        self.text_size = text_size
        self.hovered = False
        self.click_anim = 0
        self.pulse = random.uniform(0, math.pi * 2)

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        if self.click_anim > 0:
            self.click_anim -= 1
        self.pulse += 0.08

    def draw(self, surface):
        scale = 1.0
        if self.click_anim > 0:
            scale = 1.0 - (self.click_anim / 10) * 0.1
        elif self.hovered:
            scale = 1.0 + math.sin(self.pulse) * 0.02
        w = int(self.rect.width * scale)
        h = int(self.rect.height * scale)
        rx = self.rect.centerx - w // 2
        ry = self.rect.centery - h // 2
        color = self.hover_color if self.hovered else self.color

        if self.hovered:
            glow = pygame.Surface((w + 60, h + 60), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*color, 60), (30, 30, w, h), border_radius=8)
            surface.blit(glow, (rx - 30, ry - 30))

        pygame.draw.rect(surface, (10, 5, 25), (rx, ry, w, h), border_radius=8)
        pygame.draw.rect(surface, color, (rx, ry, w, h), 3, border_radius=8)
        pygame.draw.rect(surface, WHITE, (rx + 4, ry + 4, w - 8, h - 8), 1, border_radius=6)

        corner = 12
        for cx, cy in [(rx, ry), (rx + w - corner, ry), (rx, ry + h - corner), (rx + w - corner, ry + h - corner)]:
            pygame.draw.rect(surface, color, (cx, cy, corner, 3))
            pygame.draw.rect(surface, color, (cx, cy, 3, corner))

        text_color = WHITE if self.hovered else (230, 230, 230)
        draw_text(surface, self.text, self.text_size, self.rect.centerx, self.rect.centery,
                  text_color, center=True, glow=self.hovered)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.click_anim = 10
                play_sound('click')
                return True
        return False


class Slider:
    def __init__(self, x, y, w, h, value, min_v, max_v, label):
        self.rect = pygame.Rect(x - w // 2, y - h // 2, w, h)
        self.value = value
        self.min_v = min_v
        self.max_v = max_v
        self.label = label
        self.dragging = False
        self.hovered = False

    def update(self, mouse_pos, mouse_pressed):
        self.hovered = self.rect.collidepoint(mouse_pos) or self._knob_rect().collidepoint(mouse_pos)
        if mouse_pressed and (self.hovered or self.dragging):
            self.dragging = True
            rel_x = mouse_pos[0] - self.rect.x
            rel_x = max(0, min(self.rect.width, rel_x))
            ratio = rel_x / self.rect.width
            self.value = self.min_v + (self.max_v - self.min_v) * ratio
        if not mouse_pressed:
            self.dragging = False

    def _knob_rect(self):
        ratio = (self.value - self.min_v) / (self.max_v - self.min_v)
        kx = self.rect.x + int(self.rect.width * ratio)
        return pygame.Rect(kx - 10, self.rect.centery - 12, 20, 24)

    def draw(self, surface):
        pygame.draw.rect(surface, (30, 30, 40), self.rect, border_radius=4)
        ratio = (self.value - self.min_v) / (self.max_v - self.min_v)
        fill_w = int(self.rect.width * ratio)
        pygame.draw.rect(surface, NEON_CYAN, (self.rect.x, self.rect.y, fill_w, self.rect.height), border_radius=4)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=4)
        knob = self._knob_rect()
        color = NEON_GREEN if self.hovered else NEON_PINK
        pygame.draw.rect(surface, color, knob, border_radius=4)
        pygame.draw.rect(surface, WHITE, knob, 2, border_radius=4)
        draw_text(surface, self.label, 18, self.rect.x, self.rect.y - 30, WHITE)
        draw_text(surface, f"{int(self.value * 100)}%", 18, self.rect.right - 60, self.rect.y - 30, NEON_YELLOW)


# ============================================================
#                    Resize & Fullscreen
# ============================================================
screen_offset_x = [0]
screen_offset_y = [0]
screen_scale = [1.0]
is_fullscreen = [False]
windowed_size = [(BASE_W, BASE_H)]


def handle_resize(event):
    new_w, new_h = event.w, event.h
    scale = min(new_w / BASE_W, new_h / BASE_H)
    screen_scale[0] = scale
    screen_offset_x[0] = (new_w - BASE_W * scale) // 2
    screen_offset_y[0] = (new_h - BASE_H * scale) // 2


def toggle_fullscreen():
    global screen
    is_fullscreen[0] = not is_fullscreen[0]
    if is_fullscreen[0]:
        windowed_size[0] = screen.get_size()
        info = pygame.display.Info()
        screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.RESIZABLE)
    else:
        screen = pygame.display.set_mode(windowed_size[0], pygame.RESIZABLE)


def present():
    sw, sh = screen.get_size()
    scale = min(sw / BASE_W, sh / BASE_H)
    new_w = int(BASE_W * scale)
    new_h = int(BASE_H * scale)
    ox = (sw - new_w) // 2
    oy = (sh - new_h) // 2
    screen.fill((0, 0, 0))
    if scale == 1.0:
        screen.blit(game_surface, (ox, oy))
    else:
        scaled = pygame.transform.smoothscale(game_surface, (new_w, new_h))
        screen.blit(scaled, (ox, oy))
    screen_scale[0] = scale
    screen_offset_x[0] = ox
    screen_offset_y[0] = oy
    pygame.display.flip()


def get_game_mouse_pos():
    mx, my = pygame.mouse.get_pos()
    return ((mx - screen_offset_x[0]) / screen_scale[0],
            (my - screen_offset_y[0]) / screen_scale[0])


# ============================================================
#                    پس‌زمینه
# ============================================================
_bg_cache = {}
def build_bg(time_phase=0):
    """time_phase: 0=شب, 1=سپیده, 2=روز, 3=غروب"""
    if time_phase in _bg_cache:
        return _bg_cache[time_phase]

    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    if time_phase == 0:  # شب
        colors = [(5, 5, 20), (15, 10, 35), (25, 15, 50)]
    elif time_phase == 1:  # سپیده
        colors = [(30, 20, 50), (80, 40, 80), (200, 100, 100)]
    elif time_phase == 2:  # روز
        colors = [(100, 150, 255), (150, 200, 255), (200, 230, 255)]
    else:  # غروب
        colors = [(50, 20, 50), (150, 60, 80), (255, 150, 80)]

    for y in range(HEIGHT):
        t = y / HEIGHT
        if t < 0.5:
            t2 = t * 2
            c1, c2 = colors[0], colors[1]
        else:
            t2 = (t - 0.5) * 2
            c1, c2 = colors[1], colors[2]
        r = int(c1[0] + (c2[0] - c1[0]) * t2)
        g = int(c1[1] + (c2[1] - c1[1]) * t2)
        b = int(c1[2] + (c2[2] - c1[2]) * t2)
        pygame.draw.line(surf, (r, g, b), (0, y), (WIDTH, y))

    # ستاره‌ها برای شب
    if time_phase == 0 or time_phase == 1:
        for _ in range(80):
            x, y = random.randint(0, WIDTH), random.randint(0, HEIGHT // 2)
            b = random.randint(100, 220)
            pygame.draw.circle(surf, (b, b, min(255, b + 40)), (x, y), random.choice([1, 1, 2]))

    # ساختمان‌های نئونی
    for i in range(20):
        bx = i * 50 - 25
        bh = random.randint(80, 250)
        by = HEIGHT - bh
        color_choice = random.choice([NEON_CYAN, NEON_PINK, NEON_PURPLE, NEON_BLUE])
        # بدنه
        pygame.draw.rect(surf, (10, 10, 25), (bx, by, 45, bh))
        pygame.draw.rect(surf, color_choice, (bx, by, 45, bh), 2)
        # پنجره‌ها
        for wy in range(by + 10, HEIGHT - 10, 15):
            for wx in range(bx + 5, bx + 40, 10):
                if random.random() < 0.5:
                    pygame.draw.rect(surf, color_choice, (wx, wy, 4, 5))

    _bg_cache[time_phase] = surf
    return surf


# ============================================================
#                    Menu
# ============================================================
def show_menu():
    menu_time = 0
    btn_start = Button(WIDTH // 2, HEIGHT // 2 + 30, 320, 55, "START BUILDING", NEON_CYAN, NEON_GREEN, 26)
    btn_history = Button(WIDTH // 2, HEIGHT // 2 + 95, 320, 45, "HISTORY", NEON_BLUE, NEON_CYAN, 22)
    btn_settings = Button(WIDTH // 2, HEIGHT // 2 + 150, 320, 45, "SETTINGS", NEON_PURPLE, NEON_PINK, 22)
    btn_achievements = Button(WIDTH // 2, HEIGHT // 2 + 205, 320, 45, "ACHIEVEMENTS", NEON_YELLOW, NEON_ORANGE, 22)
    btn_quit = Button(WIDTH // 2, HEIGHT // 2 + 260, 320, 42, "QUIT", NEON_RED, NEON_ORANGE, 20)
    btn_fullscreen = Button(WIDTH - 40, 30, 40, 40, "[]", NEON_PURPLE, NEON_CYAN, 20)

    # بلوک‌های تزئینی
    demo_blocks = []
    for i in range(10):
        demo_blocks.append({
            'x': random.randint(50, WIDTH - 150),
            'y': random.randint(0, HEIGHT),
            'w': random.randint(60, 150),
            'color': random.choice(TOWER_COLORS),
            'vy': random.uniform(0.5, 1.5),
        })

    while True:
        game_surface.fill(DARK_BG)
        t = pygame.time.get_ticks() / 1000
        menu_time += 1
        mouse_pos = get_game_mouse_pos()

        # پس‌زمینه
        bg = build_bg(0)
        game_surface.blit(bg, (0, 0))

        # بلوک‌های تزئینی
        for db in demo_blocks:
            db['y'] += db['vy']
            if db['y'] > HEIGHT:
                db['y'] = -60
                db['x'] = random.randint(50, WIDTH - 150)
                db['color'] = random.choice(TOWER_COLORS)
            rect = pygame.Rect(db['x'], db['y'], db['w'], 40)
            for hr in range(3, 0, -1):
                glow = pygame.Surface((rect.w + hr * 10, rect.h + hr * 10), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*db['color'], 40 - hr * 10),
                                 (0, 0, rect.w + hr * 10, rect.h + hr * 10), border_radius=6)
                game_surface.blit(glow, (rect.x - hr * 5, rect.y - hr * 5))
            pygame.draw.rect(game_surface, (db['color'][0] // 4, db['color'][1] // 4, db['color'][2] // 4),
                             rect, border_radius=6)
            pygame.draw.rect(game_surface, db['color'], rect, 3, border_radius=6)

        # عنوان
        title_y = 150 + math.sin(t * 2) * 8
        draw_text(game_surface, "NEON", 72, WIDTH // 2 - 100, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "TOWER", 72, WIDTH // 2 + 100, title_y, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, "STACK  /  BUILD  /  SURVIVE", 20, WIDTH // 2, title_y + 65,
                  (200, 200, 220), center=True)

        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 22, WIDTH // 2, title_y + 115,
                      NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, f"BLOCKS: {total_blocks[0]}   PERFECT: {total_perfect[0]}   MAX: {max_height[0]}m",
                  14, WIDTH // 2, title_y + 145, NEON_PINK, center=True)

        for b in [btn_start, btn_history, btn_settings, btn_achievements, btn_quit, btn_fullscreen]:
            b.update(mouse_pos)
            b.draw(game_surface)

        present()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                toggle_fullscreen()
            if btn_fullscreen.is_clicked(event):
                toggle_fullscreen()
            if btn_start.is_clicked(event):
                return 'start'
            if btn_history.is_clicked(event):
                show_history()
            if btn_settings.is_clicked(event):
                show_settings()
            if btn_achievements.is_clicked(event):
                show_achievements()
            if btn_quit.is_clicked(event):
                return 'quit'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return 'start'
                if event.key == pygame.K_ESCAPE:
                    return 'quit'
        clock.tick(FPS)


# ============================================================
#                    Settings
# ============================================================
def show_settings():
    global settings
    slider_sfx = Slider(WIDTH // 2, 200, 400, 12, settings['sfx_volume'], 0, 1, "SFX Volume")
    slider_music = Slider(WIDTH // 2, 290, 400, 12, settings['music_volume'], 0, 1, "Music Volume")
    slider_diff = Slider(WIDTH // 2, 380, 400, 12, (settings['difficulty'] - 0.5) / 1.0, 0, 1, "Difficulty")
    btn_shake = Button(WIDTH // 2, 470, 280, 55,
                       f"SHAKE: {'ON' if settings['screen_shake'] else 'OFF'}",
                       NEON_GREEN if settings['screen_shake'] else (100, 100, 100), NEON_CYAN, 22)
    btn_reset = Button(WIDTH // 2 - 130, 560, 220, 50, "RESET SAVE", NEON_RED, NEON_ORANGE, 20)
    btn_back = Button(WIDTH // 2 + 130, 560, 220, 50, "BACK", NEON_CYAN, NEON_GREEN, 22)

    while True:
        game_surface.fill(DARK_BG)
        mouse_pos = get_game_mouse_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            game_surface.blit(s, (0, y))
        for _ in range(80):
            pygame.draw.circle(game_surface, (80, 100, 150),
                               (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 1)

        box_w = 700
        box_h = 640
        box_x = WIDTH // 2 - box_w // 2
        box_y = HEIGHT // 2 - box_h // 2 + 20
        pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h), border_radius=12)
        pygame.draw.rect(game_surface, NEON_PURPLE, (box_x, box_y, box_w, box_h), 3, border_radius=12)

        draw_text(game_surface, "SETTINGS", 48, WIDTH // 2, 80, NEON_CYAN, center=True, glow=True)

        slider_sfx.update(mouse_pos, mouse_pressed)
        slider_music.update(mouse_pos, mouse_pressed)
        slider_diff.update(mouse_pos, mouse_pressed)
        settings['sfx_volume'] = slider_sfx.value
        settings['music_volume'] = slider_music.value
        settings['difficulty'] = 0.5 + slider_diff.value * 1.0
        if music_sound[0]:
            try:
                music_sound[0].set_volume(settings['music_volume'] * 0.5)
            except:
                pass

        slider_sfx.draw(game_surface)
        slider_music.draw(game_surface)
        slider_diff.draw(game_surface)

        diff_val = settings['difficulty']
        if diff_val < 0.8:
            diff_label, diff_color = "EASY", NEON_GREEN
        elif diff_val < 1.2:
            diff_label, diff_color = "NORMAL", NEON_CYAN
        else:
            diff_label, diff_color = "HARD", NEON_RED
        draw_text(game_surface, diff_label, 20, WIDTH // 2, 410, diff_color, center=True)

        btn_shake.update(mouse_pos)
        btn_shake.text = f"SHAKE: {'ON' if settings['screen_shake'] else 'OFF'}"
        btn_shake.color = NEON_GREEN if settings['screen_shake'] else (100, 100, 100)
        btn_reset.update(mouse_pos)
        btn_back.update(mouse_pos)
        btn_shake.draw(game_surface)
        btn_reset.draw(game_surface)
        btn_back.draw(game_surface)
        present()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                toggle_fullscreen()
            if btn_shake.is_clicked(event):
                settings['screen_shake'] = not settings['screen_shake']
                save_async()
            if btn_reset.is_clicked(event):
                settings['sfx_volume'] = 0.7
                settings['music_volume'] = 0.5
                settings['difficulty'] = 1.0
                settings['screen_shake'] = True
                for k in achievements:
                    achievements[k]['unlocked'] = False
                highscore[0] = 0
                game_history.clear()
                total_blocks[0] = 0
                total_perfect[0] = 0
                max_height[0] = 0
                save_async()
                slider_sfx.value = 0.7
                slider_music.value = 0.5
                slider_diff.value = 0.5
            if btn_back.is_clicked(event):
                save_async()
                return
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_b):
                save_async()
                return
        clock.tick(FPS)


# ============================================================
#                    Achievements & History
# ============================================================
def show_achievements():
    btn_back = Button(WIDTH // 2, HEIGHT - 55, 240, 55, "BACK", NEON_CYAN, NEON_GREEN, 26)
    while True:
        game_surface.fill(DARK_BG)
        mouse_pos = get_game_mouse_pos()

        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            game_surface.blit(s, (0, y))
        for _ in range(80):
            pygame.draw.circle(game_surface, (80, 100, 150),
                               (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 1)

        draw_text(game_surface, "ACHIEVEMENTS", 50, WIDTH // 2, 40, NEON_YELLOW, center=True, glow=True)
        unlocked_count = sum(1 for a in achievements.values() if a['unlocked'])
        draw_text(game_surface, f"{unlocked_count} / {len(achievements)}", 22, WIDTH // 2, 78, NEON_CYAN, center=True)

        y_pos = 110
        card_w = 720
        card_h = 38
        for key, a in achievements.items():
            cx = WIDTH // 2 - card_w // 2
            color = NEON_GREEN if a['unlocked'] else (60, 60, 80)
            pygame.draw.rect(game_surface, (10, 5, 25), (cx, y_pos, card_w, card_h), border_radius=8)
            pygame.draw.rect(game_surface, color, (cx, y_pos, card_w, card_h), 2, border_radius=8)
            icon_color = NEON_YELLOW if a['unlocked'] else (80, 80, 80)
            draw_text(game_surface, a['icon'], 12, cx + 35, y_pos + card_h // 2, icon_color, center=True)
            name_color = NEON_YELLOW if a['unlocked'] else (120, 120, 120)
            draw_text(game_surface, a['name'], 15, cx + 70, y_pos + 5, name_color)
            draw_text(game_surface, a['desc'], 11, cx + 70, y_pos + 22, (150, 150, 180))
            status = "[OK]" if a['unlocked'] else "[--]"
            sc = NEON_GREEN if a['unlocked'] else (100, 100, 100)
            draw_text(game_surface, status, 13, cx + card_w - 50, y_pos + card_h // 2, sc, center=True)
            y_pos += card_h + 3

        btn_back.update(mouse_pos)
        btn_back.draw(game_surface)
        present()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                toggle_fullscreen()
            if btn_back.is_clicked(event):
                return
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_b):
                return
        clock.tick(FPS)


def show_history():
    btn_back = Button(WIDTH // 2 - 160, HEIGHT - 40, 220, 50, "BACK", NEON_CYAN, NEON_GREEN, 24)
    btn_clear = Button(WIDTH // 2 + 160, HEIGHT - 40, 220, 50, "CLEAR ALL", NEON_RED, NEON_ORANGE, 22)
    scroll_offset = [0]

    while True:
        game_surface.fill(DARK_BG)
        mouse_pos = get_game_mouse_pos()

        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            game_surface.blit(s, (0, y))
        for _ in range(80):
            pygame.draw.circle(game_surface, (80, 100, 150),
                               (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 1)

        draw_text(game_surface, "BUILD HISTORY", 46, WIDTH // 2, 35, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, f"Total buildings: {len(game_history)}", 16, WIDTH // 2, 72, NEON_YELLOW, center=True)

        if len(game_history) > 0:
            box_x, box_y = 60, 100
            box_w, box_h = WIDTH - 120, HEIGHT - 170
            pygame.draw.rect(game_surface, (5, 3, 15), (box_x, box_y, box_w, box_h), border_radius=8)
            pygame.draw.rect(game_surface, NEON_PURPLE, (box_x, box_y, box_w, box_h), 2, border_radius=8)
            item_h = 60
            rev = list(reversed(game_history))
            max_scroll = max(0, len(rev) * item_h - (box_h - 20))
            scroll_offset[0] = max(0, min(scroll_offset[0], max_scroll))
            clip_rect = pygame.Rect(box_x + 5, box_y + 5, box_w - 10, box_h - 10)
            old_clip = game_surface.get_clip()
            game_surface.set_clip(clip_rect)
            for i, entry in enumerate(rev):
                iy = box_y + 10 + i * item_h - scroll_offset[0]
                if iy + item_h < box_y or iy > box_y + box_h:
                    continue
                ix = box_x + 15
                iw = box_w - 30
                score = entry.get('score', 0)
                if score >= 5000:
                    rank_color, rank = NEON_PINK, "S"
                elif score >= 2000:
                    rank_color, rank = NEON_YELLOW, "A"
                elif score >= 1000:
                    rank_color, rank = NEON_GREEN, "B"
                elif score >= 500:
                    rank_color, rank = NEON_CYAN, "C"
                else:
                    rank_color, rank = (150, 150, 180), "D"
                pygame.draw.rect(game_surface, (15, 8, 30), (ix, iy, iw, item_h - 8), border_radius=6)
                pygame.draw.rect(game_surface, rank_color, (ix, iy, iw, item_h - 8), 2, border_radius=6)
                draw_text(game_surface, rank, 32, ix + 35, iy + (item_h - 8) // 2, rank_color, center=True, glow=True)
                draw_text(game_surface, f"SCORE: {score}", 20, ix + 70, iy + 6, WHITE)
                draw_text(game_surface, f"HEIGHT: {entry.get('height', 0)}m   BLOCKS: {entry.get('blocks', 0)}",
                          14, ix + 70, iy + 30, (180, 180, 200))
                draw_text(game_surface, entry.get('date', '?'), 12, ix + iw - 180, iy + 10, NEON_CYAN)
            game_surface.set_clip(old_clip)
            if max_scroll > 0:
                sb_x = box_x + box_w - 8
                sb_y = box_y + 10
                sb_h = box_h - 20
                pygame.draw.rect(game_surface, (30, 30, 40), (sb_x, sb_y, 4, sb_h))
                thumb_h = max(20, int(sb_h * (box_h - 20) / (len(rev) * item_h)))
                thumb_y = sb_y + int((sb_h - thumb_h) * (scroll_offset[0] / max_scroll))
                pygame.draw.rect(game_surface, NEON_CYAN, (sb_x, thumb_y, 4, thumb_h))
        else:
            draw_text(game_surface, "No buildings yet", 28, WIDTH // 2, HEIGHT // 2, (150, 150, 180), center=True)

        btn_back.update(mouse_pos)
        btn_back.draw(game_surface)
        if len(game_history) > 0:
            btn_clear.update(mouse_pos)
            btn_clear.draw(game_surface)
        present()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                toggle_fullscreen()
            if event.type == pygame.MOUSEWHEEL:
                scroll_offset[0] -= event.y * 40
            if btn_back.is_clicked(event):
                return
            if len(game_history) > 0 and btn_clear.is_clicked(event):
                game_history.clear()
                save_async()
                scroll_offset[0] = 0
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_b):
                    return
                if event.key == pygame.K_UP:
                    scroll_offset[0] -= 40
                if event.key == pygame.K_DOWN:
                    scroll_offset[0] += 40
        clock.tick(FPS)


# ============================================================
#                    بازی اصلی
# ============================================================
def play_game():
    # بلوک‌های ثابت
    placed_blocks = []
    # بلوک اولیه
    first_block = Block(WIDTH // 2 - BASE_BLOCK_WIDTH // 2, GROUND_Y, BASE_BLOCK_WIDTH, TOWER_COLORS[0])
    placed_blocks.append(first_block)

    # بلوک در حال حرکت
    current_block = None
    block_direction = 1
    block_speed = 5.0
    block_color_index = 1

    # امتیاز
    score = 0
    display_score = 0
    height = 0
    perfect_count = 0
    combo = 0
    max_combo = 0
    total_blocks_placed = 0
    total_frames = 0

    # دوربین
    camera_y_offset = 0
    target_camera_offset = 0

    # زمان
    day_phase = 0
    day_timer = 0

    # اسپاون بلوک بعدی
    def spawn_next_block():
        nonlocal current_block, block_direction, block_color_index
        if placed_blocks:
            top_block = placed_blocks[-1]
            y = top_block.y - BLOCK_HEIGHT
            width = top_block.width
        else:
            y = GROUND_Y
            width = BASE_BLOCK_WIDTH

        color = TOWER_COLORS[block_color_index % len(TOWER_COLORS)]
        block_color_index += 1

        direction = random.choice([1, -1])
        current_block = MovingBlock(y, width, color, direction, block_speed)

    spawn_next_block()

    # وضعیت
    game_over = False
    paused = False
    final_score = 0
    final_height = 0

    # افکت‌ها
    screen_shake = 0
    flash = 0
    new_achs = []
    notifications = []
    go_anim = 0
    game_saved = False
    perfect_banner = 0

    btn_resume = Button(WIDTH // 2, HEIGHT // 2 + 20, 300, 60, "RESUME", NEON_GREEN, NEON_CYAN, 28)
    btn_pause_menu = Button(WIDTH // 2, HEIGHT // 2 + 100, 300, 55, "MAIN MENU", NEON_RED, NEON_ORANGE, 24)
    btn_restart = Button(WIDTH // 2, HEIGHT // 2 + 70, 300, 60, "RESTART", NEON_CYAN, NEON_GREEN, 28)
    btn_menu = Button(WIDTH // 2, HEIGHT // 2 + 145, 300, 55, "MAIN MENU", NEON_YELLOW, NEON_ORANGE, 24)

    active_particles.clear()
    for p in particle_pool:
        p.active = False

    start_music()

    def try_unlock(key):
        if unlock_achievement(key):
            new_achs.append(achievements[key]['name'])
            notifications.append({'ach': achievements[key], 'timer': 180})
            return True
        return False

    def save_current():
        add_game_to_history(score, height, perfect_count, total_blocks_placed, new_achs)

    def place_block():
        """بلوک فعلی رو روی برج می‌ذاره"""
        nonlocal score, height, perfect_count, combo, max_combo, total_blocks_placed, current_block
        nonlocal block_speed, perfect_banner

        if current_block is None:
            return

        # بلوک قبلی
        prev_block = placed_blocks[-1] if placed_blocks else None

        if prev_block is None:
            return

        # محاسبه همپوشانی
        prev_left = prev_block.x
        prev_right = prev_block.x + prev_block.width
        curr_left = current_block.x
        curr_right = current_block.x + current_block.width

        overlap_left = max(prev_left, curr_left)
        overlap_right = min(prev_right, curr_right)
        overlap_width = overlap_right - overlap_left

        if overlap_width <= 0:
            # Miss - بلوک کامل افتاد
            current_block = None
            game_over_trigger()
            return

        # چک Perfect
        diff = abs(overlap_left - prev_left)
        is_perfect = diff < 5

        if is_perfect:
            overlap_left = prev_left
            overlap_width = prev_block.width
            perfect_count += 1
            combo += 1
            max_combo = max(max_combo, combo)
            perfect_banner = 60
            play_sound('perfect')
            if settings['screen_shake']:
                screen_shake = 8
            # ذرات
            cx = overlap_left + overlap_width / 2
            cy = current_block.y
            for _ in range(30):
                spawn_particles(cx, cy, NEON_YELLOW, 1, 2.0, 1.5, 1.5)
            if combo >= 5:
                play_sound('combo')

            # چک دستاوردها
            if perfect_count >= 1: try_unlock('perfect_1')
            if perfect_count >= 5: try_unlock('perfect_5')
            if perfect_count >= 10: try_unlock('perfect_10')
            if perfect_count >= 25: try_unlock('perfect_25')
            if combo >= 5: try_unlock('combo_5')
            if combo >= 10: try_unlock('combo_10')
        else:
            # نه perfect - بلوک رو کوچیک کن
            combo = 0

        # بلوک جدید
        new_block = Block(overlap_left, current_block.y, overlap_width, current_block.color)
        placed_blocks.append(new_block)

        # اگه بریده شد، بخش اضافی حذف می‌شه
        if overlap_width < current_block.width:
            play_sound('cut')
            # ذرات برای بخش حذف شده
            if curr_left < overlap_left:
                # بخش چپ حذف
                removed_x = curr_left
                for _ in range(15):
                    spawn_particles(removed_x, current_block.y + BLOCK_HEIGHT // 2,
                                    current_block.color, 1, 1.5, 1.0, 1.0)
            else:
                # بخش راست حذف
                removed_x = overlap_right
                for _ in range(15):
                    spawn_particles(removed_x, current_block.y + BLOCK_HEIGHT // 2,
                                    current_block.color, 1, 1.5, 1.0, 1.0)

        play_sound('place')
        total_blocks_placed += 1
        total_blocks[0] += 1

        # امتیاز
        points = 10
        if is_perfect:
            points = 50 * (1 + combo * 0.2)
        points = int(points)
        score += points

        # ارتفاع
        height = total_blocks_placed

        # سرعت بیشتر
        block_speed = min(15, 5.0 + total_blocks_placed * 0.1)
        block_speed *= settings['difficulty']

        # هدف جدید دوربین
        update_camera_target()

        # بلوک بعدی
        spawn_next_block()

        # چک دستاورد ارتفاع
        if height >= 10: try_unlock('height_10')
        if height >= 25: try_unlock('height_25')
        if height >= 50: try_unlock('height_50')
        if height >= 100: try_unlock('height_100')
        if height >= 200: try_unlock('height_200')
        if height >= 50 and perfect_count >= height - 1: try_unlock('no_mistake')
        if score >= 1000: try_unlock('score_1000')
        if score >= 5000: try_unlock('score_5000')
        try_unlock('first_block')

        # بلوک صفر شد؟
        if overlap_width < MIN_BLOCK_WIDTH:
            game_over_trigger()

    def game_over_trigger():
        nonlocal game_over, final_score, final_height
        game_over = True
        final_score = score
        final_height = height
        highscore[0] = max(highscore[0], score)
        max_height[0] = max(max_height[0], height)
        total_perfect[0] += perfect_count
        play_sound('gameover')
        if settings['screen_shake']:
            screen_shake = 25
        flash = 200

    def update_camera_target():
        nonlocal target_camera_offset
        if len(placed_blocks) > 8:
            # بالاترین بلوک
            top_y = placed_blocks[-1].y
            # می‌خوایم بالای برج توی 1/3 بالای صفحه باشه
            target_camera_offset = max(0, (HEIGHT - GROUND_Y) - (top_y - 200))

    running = True
    while running:
        clock.tick(FPS)
        t = pygame.time.get_ticks() / 1000
        mouse_pos = get_game_mouse_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_music()
                if not game_saved:
                    save_current()
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                toggle_fullscreen()

            if paused and not game_over:
                if btn_resume.is_clicked(event):
                    paused = False
                if btn_pause_menu.is_clicked(event):
                    stop_music()
                    if not game_saved:
                        save_current()
                        game_saved = True
                    return

            if game_over:
                if btn_restart.is_clicked(event):
                    stop_music()
                    play_game()
                    return
                if btn_menu.is_clicked(event):
                    stop_music()
                    return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over and not paused:
                    place_block()
                if event.key == pygame.K_p and not game_over:
                    paused = not paused
                if event.key == pygame.K_r and game_over:
                    stop_music()
                    play_game()
                    return
                if event.key == pygame.K_ESCAPE:
                    stop_music()
                    if not game_saved:
                        save_current()
                        game_saved = True
                    return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not game_over and not paused:
                    place_block()

        for notif in notifications[:]:
            notif['timer'] -= 1
            if notif['timer'] <= 0:
                notifications.remove(notif)

        if paused and not game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            game_surface.blit(overlay, (0, 0))
            box_w = 420
            box_h = 260
            box_x = WIDTH // 2 - box_w // 2
            box_y = HEIGHT // 2 - box_h // 2
            pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h))
            pygame.draw.rect(game_surface, NEON_CYAN, (box_x, box_y, box_w, box_h), 3)
            draw_text(game_surface, "PAUSED", 60, WIDTH // 2, box_y + 60, NEON_CYAN, center=True, glow=True)
            btn_resume.update(mouse_pos)
            btn_pause_menu.update(mouse_pos)
            btn_resume.draw(game_surface)
            btn_pause_menu.draw(game_surface)
            present()
            continue

        if not game_over:
            total_frames += 1

            if display_score < score:
                display_score += max(1, (score - display_score) // 5)
                if display_score > score:
                    display_score = score

            # آپدیت روز/شب
            day_timer += 1
            if day_timer > FPS * 15:
                day_timer = 0
                day_phase = (day_phase + 1) % 4

            # آپدیت بلوک
            if current_block:
                current_block.update()

                # اگه از صفحه خارج شد، از طرف دیگه بیاد
                if current_block.direction == 1 and current_block.x > WIDTH:
                    current_block.x = -current_block.width
                elif current_block.direction == -1 and current_block.x + current_block.width < 0:
                    current_block.x = WIDTH

            # دوربین
            camera_y_offset += (target_camera_offset - camera_y_offset) * 0.1

            # آپدیت ذرات
            for p in active_particles[:]:
                p.update()
                if not p.active:
                    active_particles.remove(p)

            if screen_shake > 0:
                screen_shake -= 1
            if flash > 0:
                flash -= 8
            if perfect_banner > 0:
                perfect_banner -= 1

        # ============================================================
        #                    رسم
        # ============================================================
        game_surface.fill(DARK_BG)
        offset_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        offset_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0

        play_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # پس‌زمینه
        bg = build_bg(day_phase)
        play_layer.blit(bg, (0, 0))

        # بلوک‌ها
        for block in placed_blocks:
            # موقعیت با دوربین
            draw_rect = block.get_rect().copy()
            draw_rect.y += camera_y_offset
            # هاله
            for hr in range(3, 0, -1):
                glow = pygame.Surface((draw_rect.w + hr * 10, draw_rect.h + hr * 10), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*block.color, 60 - hr * 15),
                                 (0, 0, draw_rect.w + hr * 10, draw_rect.h + hr * 10), border_radius=6)
                play_layer.blit(glow, (draw_rect.x - hr * 5, draw_rect.y - hr * 5))
            # بدنه
            pygame.draw.rect(play_layer, (block.color[0] // 4, block.color[1] // 4, block.color[2] // 4),
                             draw_rect, border_radius=6)
            pygame.draw.rect(play_layer, block.color, draw_rect, 3, border_radius=6)
            pygame.draw.rect(play_layer, WHITE, draw_rect, 1, border_radius=6)
            # خط درخشان بالا
            pygame.draw.line(play_layer, WHITE,
                             (draw_rect.x + 5, draw_rect.y + 3),
                             (draw_rect.right - 5, draw_rect.y + 3), 2)

        # بلوک فعلی
        if current_block:
            draw_rect = current_block.get_rect().copy()
            draw_rect.y += camera_y_offset
            # هاله
            for hr in range(3, 0, -1):
                glow = pygame.Surface((draw_rect.w + hr * 10, draw_rect.h + hr * 10), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*current_block.color, 80 - hr * 15),
                                 (0, 0, draw_rect.w + hr * 10, draw_rect.h + hr * 10), border_radius=6)
                play_layer.blit(glow, (draw_rect.x - hr * 5, draw_rect.y - hr * 5))
            # بدنه
            pygame.draw.rect(play_layer, (current_block.color[0] // 3, current_block.color[1] // 3, current_block.color[2] // 3),
                             draw_rect, border_radius=6)
            pygame.draw.rect(play_layer, current_block.color, draw_rect, 3, border_radius=6)
            pygame.draw.rect(play_layer, WHITE, draw_rect, 2, border_radius=6)
            # خط درخشان
            pygame.draw.line(play_layer, WHITE,
                             (draw_rect.x + 5, draw_rect.y + 3),
                             (draw_rect.right - 5, draw_rect.y + 3), 2)

            # خط راهنما
            prev_block = placed_blocks[-1] if placed_blocks else None
            if prev_block:
                guide_y = draw_rect.bottom
                # خط چین عمودی
                for i in range(0, int(draw_rect.h), 8):
                    pygame.draw.line(play_layer, (100, 100, 100),
                                     (draw_rect.x, draw_rect.y + i),
                                     (draw_rect.x, draw_rect.y + i + 4), 1)

        # ذرات
        for p in active_particles:
            p.draw(play_layer)

        # Flash
        if flash > 0:
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 200, 100, flash))
            play_layer.blit(fs, (0, 0))

        game_surface.blit(play_layer, (offset_x, offset_y))

        # ============================================================
        #                    HUD
        # ============================================================
        # نوار بالا
        hud_panel = pygame.Surface((WIDTH, 80), pygame.SRCALPHA)
        for y in range(80):
            alpha = int(180 * (1 - y / 80))
            pygame.draw.line(hud_panel, (5, 10, 25, alpha), (0, y), (WIDTH, y))
        game_surface.blit(hud_panel, (0, 0))
        pygame.draw.line(game_surface, NEON_CYAN, (0, 80), (WIDTH, 80), 1)

        # عنوان
        draw_text(game_surface, "NEON TOWER", 20, 25, 10, NEON_CYAN, glow=True)
        draw_text(game_surface, f"HEIGHT: {height}m", 16, 25, 38, NEON_YELLOW)
        draw_text(game_surface, f"BLOCKS: {total_blocks_placed}", 12, 25, 60, (200, 200, 220))

        # Score
        draw_text(game_surface, "SCORE", 14, WIDTH - 25, 10, NEON_CYAN)
        draw_text(game_surface, f"{display_score}", 26, WIDTH - 25, 28, WHITE, glow=True)
        draw_text(game_surface, f"PERFECT: {perfect_count}", 12, WIDTH - 25, 60, NEON_GREEN)

        # Combo
        if combo > 1:
            combo_color = NEON_GREEN if combo < 5 else NEON_YELLOW if combo < 10 else NEON_PINK
            scale = 1 + math.sin(t * 10) * 0.1
            draw_text(game_surface, f"x{combo} COMBO", int(24 * scale), WIDTH // 2, 30,
                      combo_color, center=True, glow=True)

        # Perfect banner
        if perfect_banner > 0:
            pulse = 1 + math.sin(t * 15) * 0.1
            draw_text(game_surface, "PERFECT!", int(50 * pulse), WIDTH // 2, HEIGHT // 2 - 100,
                      NEON_YELLOW, center=True, glow=True)

        # راهنما
        if total_frames < 200:
            draw_text(game_surface, "CLICK or SPACE to place block", 20,
                      WIDTH // 2, HEIGHT - 60, NEON_CYAN, center=True, glow=True)
            draw_text(game_surface, "Stack blocks precisely to build higher!", 14,
                      WIDTH // 2, HEIGHT - 30, (200, 200, 220), center=True)

        # Notifications
        for i, notif in enumerate(notifications):
            ny = 90 + i * 55
            alpha = min(255, notif['timer'] * 2)
            ach = notif['ach']
            notif_surf = pygame.Surface((340, 50), pygame.SRCALPHA)
            notif_surf.fill((10, 5, 25, min(220, alpha)))
            game_surface.blit(notif_surf, (WIDTH - 360, ny))
            pygame.draw.rect(game_surface, NEON_YELLOW, (WIDTH - 360, ny, 340, 50), 2)
            draw_text(game_surface, "ACHIEVEMENT!", 11, WIDTH - 345, ny + 4, NEON_YELLOW)
            draw_text(game_surface, ach['name'], 16, WIDTH - 345, ny + 22, WHITE, glow=True)

        # Game Over
        if game_over:
            go_anim += 1
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            game_surface.blit(overlay, (0, 0))
            box_w = 540
            box_h = 400
            box_x = WIDTH // 2 - box_w // 2
            box_y = HEIGHT // 2 - box_h // 2
            pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h))
            pygame.draw.rect(game_surface, NEON_PINK, (box_x, box_y, box_w, box_h), 3)
            pygame.draw.rect(game_surface, NEON_CYAN, (box_x + 5, box_y + 5, box_w - 10, box_h - 10), 1)
            draw_text(game_surface, "TOWER FALLEN!", 56, WIDTH // 2, box_y + 55,
                      NEON_RED, center=True, glow=True)
            draw_text(game_surface, f"HEIGHT: {final_height}m", 32,
                      WIDTH // 2, box_y + 120, NEON_YELLOW, center=True, glow=True)
            draw_text(game_surface, f"SCORE: {final_score}   PERFECT: {perfect_count}",
                      16, WIDTH // 2, box_y + 160, WHITE, center=True)
            hs = highscore[0]
            if final_score >= hs and final_score > 0:
                draw_text(game_surface, "* NEW HIGH SCORE! *", 22, WIDTH // 2, box_y + 195,
                          NEON_YELLOW, center=True, glow=True)
            else:
                draw_text(game_surface, f"HIGH SCORE: {hs}", 18, WIDTH // 2, box_y + 195,
                          NEON_YELLOW, center=True)
            if go_anim > 15:
                btn_restart.update(mouse_pos)
                btn_menu.update(mouse_pos)
                btn_restart.draw(game_surface)
                btn_menu.draw(game_surface)

        present()

    stop_music()


# ============================================================
#                    Main
# ============================================================
def main():
    while True:
        result = show_menu()
        if result == 'quit':
            break
        elif result == 'start':
            play_game()
    pygame.quit()


if __name__ == "__main__":
    main()