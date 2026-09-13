import pygame
import random
import math
import array
import threading
import json
import sys
from datetime import datetime
from collections import deque

# --- تنظیمات اولیه ---
pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
    AUDIO_OK = True
except:
    AUDIO_OK = False

BASE_W, BASE_H = 900, 780
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("NEON TETRIS")
game_surface = pygame.Surface((BASE_W, BASE_H))

clock = pygame.time.Clock()
FPS = 60

# --- ابعاد بازی ---
CELL_SIZE = 30
COLS = 10
ROWS = 20
BOARD_W = COLS * CELL_SIZE
BOARD_H = ROWS * CELL_SIZE
BOARD_X = (WIDTH - BOARD_W) // 2
BOARD_Y = (HEIGHT - BOARD_H) // 2 + 20

# پنل‌های کناری
PANEL_W = 150
HOLD_X = BOARD_X - PANEL_W - 20
HOLD_Y = BOARD_Y + 40
NEXT_X = BOARD_X + BOARD_W + 20
NEXT_Y = BOARD_Y + 40

# --- رنگ‌ها ---
BLACK = (0, 0, 4)
DARK_BG = (3, 5, 15)
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

# قطعات Tetris
# I, O, T, S, Z, J, L
PIECES = {
    'I': {
        'color': NEON_CYAN,
        'rotations': [
            [(0, 0), (1, 0), (2, 0), (3, 0)],
            [(0, 0), (0, 1), (0, 2), (0, 3)],
            [(0, 0), (1, 0), (2, 0), (3, 0)],
            [(0, 0), (0, 1), (0, 2), (0, 3)],
        ],
        'kick_wall': True,
    },
    'O': {
        'color': NEON_YELLOW,
        'rotations': [
            [(0, 0), (1, 0), (0, 1), (1, 1)],
        ] * 4,
        'kick_wall': False,
    },
    'T': {
        'color': NEON_PURPLE,
        'rotations': [
            [(1, 0), (0, 1), (1, 1), (2, 1)],
            [(1, 0), (1, 1), (2, 1), (1, 2)],
            [(0, 1), (1, 1), (2, 1), (1, 2)],
            [(1, 0), (0, 1), (1, 1), (1, 2)],
        ],
        'kick_wall': True,
    },
    'S': {
        'color': NEON_GREEN,
        'rotations': [
            [(1, 0), (2, 0), (0, 1), (1, 1)],
            [(0, 0), (0, 1), (1, 1), (1, 2)],
            [(1, 0), (2, 0), (0, 1), (1, 1)],
            [(0, 0), (0, 1), (1, 1), (1, 2)],
        ],
        'kick_wall': True,
    },
    'Z': {
        'color': NEON_RED,
        'rotations': [
            [(0, 0), (1, 0), (1, 1), (2, 1)],
            [(1, 0), (0, 1), (1, 1), (0, 2)],
            [(0, 0), (1, 0), (1, 1), (2, 1)],
            [(1, 0), (0, 1), (1, 1), (0, 2)],
        ],
        'kick_wall': True,
    },
    'J': {
        'color': NEON_BLUE,
        'rotations': [
            [(0, 0), (0, 1), (1, 1), (2, 1)],
            [(1, 0), (2, 0), (1, 1), (1, 2)],
            [(0, 1), (1, 1), (2, 1), (2, 2)],
            [(1, 0), (1, 1), (0, 2), (1, 2)],
        ],
        'kick_wall': True,
    },
    'L': {
        'color': NEON_ORANGE,
        'rotations': [
            [(2, 0), (0, 1), (1, 1), (2, 1)],
            [(1, 0), (1, 1), (1, 2), (2, 2)],
            [(0, 1), (1, 1), (2, 1), (0, 2)],
            [(0, 0), (1, 0), (1, 1), (1, 2)],
        ],
        'kick_wall': True,
    },
}

PIECE_KEYS = list(PIECES.keys())

# SRS Wall Kick Tables
KICKS_JLSTZ = {
    (0, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (1, 0): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (1, 2): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (2, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (2, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (3, 2): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (3, 0): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (0, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
}

KICKS_I = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
}

# --- ذخیره ---
SAVE_FILE = "neon_tetris_save.json"

settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'start_level': 1,
    'ghost_piece': True,
    'screen_shake': True,
}

achievements = {
    'first_line': {'name': 'FIRST CLEAR', 'desc': 'Clear your first line', 'unlocked': False, 'icon': '|'},
    'lines_10': {'name': 'ROOKIE', 'desc': 'Clear 10 lines', 'unlocked': False, 'icon': '||'},
    'lines_50': {'name': 'VETERAN', 'desc': 'Clear 50 lines', 'unlocked': False, 'icon': '|||'},
    'lines_100': {'name': 'LEGEND', 'desc': 'Clear 100 lines', 'unlocked': False, 'icon': '||||'},
    'tetris': {'name': 'TETRIS!', 'desc': 'Clear 4 lines at once', 'unlocked': False, 'icon': 'T4'},
    'tetris_x2': {'name': 'BACK-TO-BACK', 'desc': 'Two Tetrises in a row', 'unlocked': False, 'icon': 'T8'},
    'score_1000': {'name': 'BEGINNER', 'desc': 'Score 1000 points', 'unlocked': False, 'icon': '*'},
    'score_5000': {'name': 'INTERMEDIATE', 'desc': 'Score 5000 points', 'unlocked': False, 'icon': '**'},
    'score_10000': {'name': 'EXPERT', 'desc': 'Score 10000 points', 'unlocked': False, 'icon': '***'},
    'score_50000': {'name': 'GRANDMASTER', 'desc': 'Score 50000 points', 'unlocked': False, 'icon': '****'},
    'level_5': {'name': 'SPEED UP', 'desc': 'Reach level 5', 'unlocked': False, 'icon': 'L5'},
    'level_10': {'name': 'FAST FINGERS', 'desc': 'Reach level 10', 'unlocked': False, 'icon': 'L10'},
    'level_15': {'name': 'SONIC SPEED', 'desc': 'Reach level 15', 'unlocked': False, 'icon': 'L15'},
    'hold_used': {'name': 'STRATEGIST', 'desc': 'Use hold for the first time', 'unlocked': False, 'icon': 'H'},
    'combo_5': {'name': 'COMBO KING', 'desc': 'Reach combo 5', 'unlocked': False, 'icon': 'C5'},
}

highscore = [0]
game_history = []


def load_save():
    global settings, achievements, highscore, game_history
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
            settings.update(data.get('settings', {}))
            for k, v in data.get('achievements', {}).items():
                if k in achievements:
                    achievements[k]['unlocked'] = v
            highscore[0] = data.get('highscore', 0)
            game_history = data.get('game_history', [])
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


def add_game_to_history(score, lines, level, duration, mode, new_achs):
    entry = {
        'score': score,
        'lines': lines,
        'level': level,
        'duration': duration,
        'mode': mode,
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


def make_tetris_music(vol=0.3):
    """موسیقی معروف Korobeiniki با کد procedural"""
    if not AUDIO_OK:
        return None
    sr = 44100
    # نت‌های اصلی (Korobeiniki - Tetris Theme)
    # E5, B4, C5, D5, C5, B4, A4, A4, C5, E5, D5, C5, B4, B4, C5, D5, E5, C5, A4, A4
    notes = [
        659.25, 493.88, 523.25, 587.33, 523.25, 493.88, 440.00, 440.00,
        523.25, 659.25, 587.33, 523.25, 493.88, 493.88, 523.25, 587.33,
        659.25, 523.25, 440.00, 440.00, 0, 587.33, 698.46, 880.00, 783.99,
        698.46, 659.25, 523.25, 659.25, 587.33, 523.25, 493.88, 493.88,
        523.25, 587.33, 659.25, 523.25, 440.00, 440.00, 0
    ]
    # مدت هر نت (بر اساس الگوی اصلی)
    durations = [
        0.25, 0.125, 0.125, 0.25, 0.125, 0.125, 0.25, 0.125,
        0.125, 0.25, 0.125, 0.125, 0.25, 0.125, 0.125, 0.25,
        0.125, 0.125, 0.25, 0.125, 0.125, 0.25, 0.125, 0.125,
        0.25, 0.125, 0.125, 0.25, 0.125, 0.125, 0.25, 0.125,
        0.125, 0.25, 0.125, 0.125, 0.25, 0.125, 0.125
    ]

    buf = array.array('h')
    for note, dur in zip(notes, durations):
        n = int(sr * dur)
        for i in range(n):
            t = i / sr
            if note == 0:
                val = 0
            else:
                # صدای square wave (شبیه موسیقی 8-bit)
                val = (1.0 if math.sin(2 * math.pi * note * t) > 0 else -1.0) * 0.5
                # هارمونیک
                val += math.sin(2 * math.pi * note * 2 * t) * 0.1
                # آرپژ زیر
                val += (1.0 if math.sin(2 * math.pi * note * 0.5 * t) > 0 else -1.0) * 0.15

            env = 1.0
            if i < n * 0.02:
                env = i / (n * 0.02)
            elif i > n * 0.9:
                env = 1.0 - (i - n * 0.9) / (n * 0.1)
            val *= env * vol
            buf.append(int(max(-1, min(1, val)) * 32767))

    try:
        return pygame.mixer.Sound(buffer=buf)
    except:
        return None


def build_sounds():
    sounds['move'] = make_sound(400, 500, 0.03, 0.10, 'square')
    sounds['rotate'] = make_sound(600, 800, 0.05, 0.12, 'square')
    sounds['drop'] = make_sound(300, 100, 0.1, 0.20, 'square')
    sounds['line'] = make_sound(800, 1400, 0.2, 0.22, 'sine')
    sounds['tetris'] = make_sound(600, 1800, 0.4, 0.30, 'sine')
    sounds['levelup'] = make_sound(500, 1500, 0.5, 0.25, 'sine')
    sounds['hold'] = make_sound(700, 1000, 0.1, 0.15, 'sine')
    sounds['gameover'] = make_sound(500, 60, 1.5, 0.30, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['combo'] = make_sound(1200, 1800, 0.15, 0.15, 'sine')

    music_sound[0] = make_tetris_music(0.15)
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
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'size', 'active')

    def __init__(self):
        self.active = False

    def spawn(self, x, y, color, speed_mult=1.0, size_mult=1.0, life_mult=1.0):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 6) * speed_mult
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 2  # به سمت بالا
        self.life = int(random.randint(20, 45) * life_mult)
        self.max_life = self.life
        self.color = color
        self.size = random.randint(2, 5) * size_mult
        self.active = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
        self.vy += 0.3
        self.life -= 1
        if self.life <= 0:
            self.active = False

    def draw(self, surface):
        if self.life > 0:
            alpha = self.life / self.max_life
            size = max(1, int(self.size * alpha))
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), size)


def spawn_particles(x, y, color, count, speed_mult=1.0, size_mult=1.0, life_mult=1.0):
    for _ in range(int(count)):
        p = None
        for pp in particle_pool:
            if not pp.active:
                p = pp
                break
        if p is None:
            p = Particle()
            particle_pool.append(p)
        p.spawn(x, y, color, speed_mult, size_mult, life_mult)
        active_particles.append(p)


# ============================================================
#                    منطق Tetris
# ============================================================
class Tetromino:
    def __init__(self, kind):
        self.kind = kind
        self.color = PIECES[kind]['color']
        self.rotation = 0
        self.x = 0
        self.y = 0

    def get_cells(self, rotation=None):
        if rotation is None:
            rotation = self.rotation
        return PIECES[self.kind]['rotations'][rotation % 4]

    def get_absolute_cells(self, rotation=None, x=None, y=None):
        if rotation is None:
            rotation = self.rotation
        if x is None:
            x = self.x
        if y is None:
            y = self.y
        return [(cx + x, cy + y) for cx, cy in self.get_cells(rotation)]


class Board:
    def __init__(self):
        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.clearing_lines = []  # خطوط در حال انفجار
        self.clear_timer = 0

    def reset(self):
        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]

    def is_valid_position(self, cells):
        for x, y in cells:
            if x < 0 or x >= COLS or y >= ROWS:
                return False
            if y < 0:
                continue
            if self.grid[y][x] is not None:
                return False
        return True

    def lock_piece(self, piece):
        for x, y in piece.get_absolute_cells():
            if 0 <= y < ROWS and 0 <= x < COLS:
                self.grid[y][x] = piece.color

    def check_full_lines(self):
        full = []
        for y in range(ROWS):
            if all(cell is not None for cell in self.grid[y]):
                full.append(y)
        return full

    def clear_lines(self, lines):
        """حذف خطوط و برگرداندن تعداد"""
        if not lines:
            return 0
        # حذف خطوط
        for y in sorted(lines, reverse=True):
            del self.grid[y]
            self.grid.insert(0, [None for _ in range(COLS)])
        return len(lines)

    def get_drop_position(self, piece):
        """محل نهایی فرود قطعه (Ghost)"""
        drop_y = piece.y
        while True:
            test_cells = piece.get_absolute_cells(x=piece.x, y=drop_y + 1)
            if not self.is_valid_position(test_cells):
                break
            drop_y += 1
        return drop_y


# ============================================================
#                    Button
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


# ============================================================
#                    Slider
# ============================================================
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
#                    Resize
# ============================================================
screen_offset_x = [0]
screen_offset_y = [0]
screen_scale = [1.0]


def handle_resize(event):
    new_w, new_h = event.w, event.h
    scale = min(new_w / BASE_W, new_h / BASE_H)
    screen_scale[0] = scale
    screen_offset_x[0] = (new_w - BASE_W * scale) // 2
    screen_offset_y[0] = (new_h - BASE_H * scale) // 2


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
#                    رسم بلوک نئونی
# ============================================================
def draw_neon_block(surface, px, py, size, color, glow=True, alpha=255):
    """رسم یه بلوک نئونی زیبا"""
    rect = pygame.Rect(int(px + 1), int(py + 1), size - 2, size - 2)

    # هاله درخشان
    if glow and alpha == 255:
        for r in range(3, 0, -1):
            glow_size = size + r * 6
            glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*color, 50 - r * 12),
                             (0, 0, glow_size, glow_size), border_radius=8)
            surface.blit(glow_surf, (px - r * 3, py - r * 3))

    # بدنه اصلی
    if alpha == 255:
        pygame.draw.rect(surface, color, rect, border_radius=6)
    else:
        # برای ghost piece
        pygame.draw.rect(surface, color, rect, 2, border_radius=6)
        return

    # نوار روشن بالا
    top_rect = pygame.Rect(rect.x + 4, rect.y + 3, rect.w - 8, 3)
    lighter = (min(255, color[0] + 80), min(255, color[1] + 80), min(255, color[2] + 80))
    pygame.draw.rect(surface, lighter, top_rect, border_radius=2)

    # حاشیه سفید
    pygame.draw.rect(surface, WHITE, rect, 2, border_radius=6)

    # درخشش مرکزی
    pygame.draw.circle(surface, lighter, (rect.centerx - 4, rect.centery - 4), 3)


# ============================================================
#                    Menu
# ============================================================
def show_menu():
    menu_time = 0
    btn_start = Button(WIDTH // 2, HEIGHT // 2 + 30, 320, 55, "START GAME", NEON_CYAN, NEON_GREEN, 28)
    btn_history = Button(WIDTH // 2, HEIGHT // 2 + 95, 320, 45, "HISTORY", NEON_BLUE, NEON_CYAN, 22)
    btn_settings = Button(WIDTH // 2, HEIGHT // 2 + 150, 320, 45, "SETTINGS", NEON_PURPLE, NEON_PINK, 22)
    btn_achievements = Button(WIDTH // 2, HEIGHT // 2 + 205, 320, 45, "ACHIEVEMENTS", NEON_YELLOW, NEON_ORANGE, 22)
    btn_quit = Button(WIDTH // 2, HEIGHT // 2 + 260, 320, 42, "QUIT", NEON_RED, NEON_ORANGE, 20)

    # قطعات تزئینی
    menu_pieces = []
    for _ in range(8):
        kind = random.choice(PIECE_KEYS)
        menu_pieces.append({
            'kind': kind,
            'x': random.uniform(0, WIDTH),
            'y': random.uniform(-200, HEIGHT),
            'rotation': random.randint(0, 3),
            'fall_speed': random.uniform(0.5, 2),
        })

    while True:
        game_surface.fill(BLACK)
        t = pygame.time.get_ticks() / 1000
        menu_time += 1
        mouse_pos = get_game_mouse_pos()

        # آسمان گرادیان
        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            game_surface.blit(s, (0, y))

        # ستاره‌ها
        for _ in range(80):
            pygame.draw.circle(game_surface, (80, 100, 150),
                               (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 1)

        # قطعات شناور
        for p in menu_pieces:
            p['y'] += p['fall_speed']
            if p['y'] > HEIGHT + 100:
                p['y'] = -100
                p['x'] = random.uniform(0, WIDTH)
                p['kind'] = random.choice(PIECE_KEYS)
            # رسم قطعه
            piece = PIECES[p['kind']]
            color = piece['color']
            cells = piece['rotations'][p['rotation']]
            for cx, cy in cells:
                px = p['x'] + cx * 25
                py = p['y'] + cy * 25
                draw_neon_block(game_surface, px, py, 25, color, glow=False)

        # عنوان
        title_y = 130 + math.sin(t * 2) * 8
        draw_text(game_surface, "NEON", 72, WIDTH // 2 - 100, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "TETRIS", 72, WIDTH // 2 + 120, title_y, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, "STACK  /  CLEAR  /  SURVIVE", 20, WIDTH // 2, title_y + 65, (200, 200, 220), center=True)

        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 22, WIDTH // 2, title_y + 115, NEON_YELLOW, center=True, glow=True)

        total_games = len(game_history)
        draw_text(game_surface, f"TOTAL GAMES: {total_games}", 14, WIDTH // 2, title_y + 145, NEON_PINK, center=True)

        # دکمه‌ها
        for b in [btn_start, btn_history, btn_settings, btn_achievements, btn_quit]:
            b.update(mouse_pos)
            b.draw(game_surface)

        # ذرات
        for p in active_particles[:]:
            p.update()
            p.draw(game_surface)
            if not p.active:
                active_particles.remove(p)

        present()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
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
#                    Mode Select
# ============================================================
def show_mode_select():
    btn_marathon = Button(WIDTH // 2, HEIGHT // 2 - 80, 400, 70,
                          "MARATHON", NEON_CYAN, NEON_GREEN, 30)
    btn_sprint = Button(WIDTH // 2, HEIGHT // 2 + 10, 400, 70,
                        "SPRINT (40 LINES)", NEON_YELLOW, NEON_ORANGE, 30)
    btn_ultra = Button(WIDTH // 2, HEIGHT // 2 + 100, 400, 70,
                       "ULTRA (2 MIN)", NEON_PINK, NEON_PURPLE, 30)
    btn_back = Button(WIDTH // 2, HEIGHT // 2 + 190, 300, 50,
                      "BACK", NEON_RED, NEON_ORANGE, 22)

    descriptions = {
        'marathon': ["Classic mode - play until you lose", "Levels increase every 10 lines"],
        'sprint': ["Clear 40 lines as fast as possible", "Timer counts up"],
        'ultra': ["Get the highest score in 2 minutes", "Timer counts down"],
    }

    while True:
        game_surface.fill(DARK_BG)
        t = pygame.time.get_ticks() / 1000
        mouse_pos = get_game_mouse_pos()

        # پس‌زمینه
        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            game_surface.blit(s, (0, y))

        for _ in range(80):
            pygame.draw.circle(game_surface, (80, 100, 150),
                               (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 1)

        draw_text(game_surface, "SELECT MODE", 50, WIDTH // 2, 100, NEON_CYAN, center=True, glow=True)

        for b in [btn_marathon, btn_sprint, btn_ultra, btn_back]:
            b.update(mouse_pos)
            b.draw(game_surface)

        # توضیحات
        modes = [
            (btn_marathon, descriptions['marathon']),
            (btn_sprint, descriptions['sprint']),
            (btn_ultra, descriptions['ultra']),
        ]
        for btn, descs in modes:
            if btn.hovered:
                for i, line in enumerate(descs):
                    draw_text(game_surface, line, 14, WIDTH // 2, btn.rect.bottom + 10 + i * 20,
                              (200, 200, 220), center=True)

        present()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
            if btn_marathon.is_clicked(event):
                return 'marathon'
            if btn_sprint.is_clicked(event):
                return 'sprint'
            if btn_ultra.is_clicked(event):
                return 'ultra'
            if btn_back.is_clicked(event):
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
        clock.tick(FPS)


# ============================================================
#                    Settings
# ============================================================
def show_settings():
    global settings
    slider_sfx = Slider(WIDTH // 2, 180, 400, 12, settings['sfx_volume'], 0, 1, "SFX Volume")
    slider_music = Slider(WIDTH // 2, 270, 400, 12, settings['music_volume'], 0, 1, "Music Volume")
    slider_level = Slider(WIDTH // 2, 360, 400, 12, (settings['start_level'] - 1) / 14, 0, 1, "Start Level")
    btn_ghost = Button(WIDTH // 2, 450, 280, 50,
                       f"GHOST: {'ON' if settings['ghost_piece'] else 'OFF'}",
                       NEON_GREEN if settings['ghost_piece'] else (100, 100, 100), NEON_CYAN, 22)
    btn_shake = Button(WIDTH // 2, 515, 280, 50,
                       f"SHAKE: {'ON' if settings['screen_shake'] else 'OFF'}",
                       NEON_GREEN if settings['screen_shake'] else (100, 100, 100), NEON_CYAN, 22)
    btn_reset = Button(WIDTH // 2 - 130, 590, 220, 50, "RESET SAVE", NEON_RED, NEON_ORANGE, 20)
    btn_back = Button(WIDTH // 2 + 130, 590, 220, 50, "BACK", NEON_CYAN, NEON_GREEN, 22)

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

        box_w, box_h = 700, 620
        box_x = WIDTH // 2 - box_w // 2
        box_y = HEIGHT // 2 - box_h // 2 + 20
        pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h), border_radius=12)
        pygame.draw.rect(game_surface, NEON_PURPLE, (box_x, box_y, box_w, box_h), 3, border_radius=12)

        draw_text(game_surface, "SETTINGS", 48, WIDTH // 2, 70, NEON_CYAN, center=True, glow=True)

        slider_sfx.update(mouse_pos, mouse_pressed)
        slider_music.update(mouse_pos, mouse_pressed)
        slider_level.update(mouse_pos, mouse_pressed)
        settings['sfx_volume'] = slider_sfx.value
        settings['music_volume'] = slider_music.value
        settings['start_level'] = 1 + int(slider_level.value * 14)
        if music_sound[0]:
            try:
                music_sound[0].set_volume(settings['music_volume'] * 0.5)
            except:
                pass

        slider_sfx.draw(game_surface)
        slider_music.draw(game_surface)
        slider_level.draw(game_surface)

        # نمایش سطح شروع
        draw_text(game_surface, f"Level {settings['start_level']}", 16, WIDTH // 2, 390,
                  NEON_YELLOW, center=True)

        btn_ghost.update(mouse_pos)
        btn_ghost.text = f"GHOST: {'ON' if settings['ghost_piece'] else 'OFF'}"
        btn_ghost.color = NEON_GREEN if settings['ghost_piece'] else (100, 100, 100)
        btn_ghost.draw(game_surface)

        btn_shake.update(mouse_pos)
        btn_shake.text = f"SHAKE: {'ON' if settings['screen_shake'] else 'OFF'}"
        btn_shake.color = NEON_GREEN if settings['screen_shake'] else (100, 100, 100)
        btn_shake.draw(game_surface)

        btn_reset.update(mouse_pos)
        btn_back.update(mouse_pos)
        btn_reset.draw(game_surface)
        btn_back.draw(game_surface)

        present()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
            if btn_ghost.is_clicked(event):
                settings['ghost_piece'] = not settings['ghost_piece']
                save_async()
            if btn_shake.is_clicked(event):
                settings['screen_shake'] = not settings['screen_shake']
                save_async()
            if btn_reset.is_clicked(event):
                settings['sfx_volume'] = 0.7
                settings['music_volume'] = 0.5
                settings['start_level'] = 1
                settings['ghost_piece'] = True
                settings['screen_shake'] = True
                for k in achievements:
                    achievements[k]['unlocked'] = False
                highscore[0] = 0
                game_history.clear()
                save_async()
                slider_sfx.value = 0.7
                slider_music.value = 0.5
                slider_level.value = 0
            if btn_back.is_clicked(event):
                save_async()
                return
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_b):
                save_async()
                return
        clock.tick(FPS)


# ============================================================
#                    Achievements
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
        card_h = 42
        for key, a in achievements.items():
            cx = WIDTH // 2 - card_w // 2
            color = NEON_GREEN if a['unlocked'] else (60, 60, 80)
            pygame.draw.rect(game_surface, (10, 5, 25), (cx, y_pos, card_w, card_h), border_radius=8)
            pygame.draw.rect(game_surface, color, (cx, y_pos, card_w, card_h), 2, border_radius=8)
            icon_color = NEON_YELLOW if a['unlocked'] else (80, 80, 80)
            draw_text(game_surface, a['icon'], 16, cx + 35, y_pos + card_h // 2, icon_color, center=True)
            name_color = NEON_YELLOW if a['unlocked'] else (120, 120, 120)
            draw_text(game_surface, a['name'], 16, cx + 70, y_pos + 5, name_color)
            draw_text(game_surface, a['desc'], 12, cx + 70, y_pos + 24, (150, 150, 180))
            status = "[OK]" if a['unlocked'] else "[--]"
            sc = NEON_GREEN if a['unlocked'] else (100, 100, 100)
            draw_text(game_surface, status, 14, cx + card_w - 50, y_pos + card_h // 2, sc, center=True)
            y_pos += card_h + 4

        btn_back.update(mouse_pos)
        btn_back.draw(game_surface)
        present()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
            if btn_back.is_clicked(event):
                return
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_b):
                return
        clock.tick(FPS)


# ============================================================
#                    History
# ============================================================
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

        draw_text(game_surface, "GAME HISTORY", 46, WIDTH // 2, 35, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, f"Total games: {len(game_history)}", 16, WIDTH // 2, 72, NEON_YELLOW, center=True)

        if len(game_history) > 0:
            box_x, box_y = 60, 100
            box_w, box_h = WIDTH - 120, HEIGHT - 170
            pygame.draw.rect(game_surface, (5, 3, 15), (box_x, box_y, box_w, box_h), border_radius=8)
            pygame.draw.rect(game_surface, NEON_PURPLE, (box_x, box_y, box_w, box_h), 2, border_radius=8)
            item_h = 70
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
                if score >= 50000:
                    rank_color, rank = NEON_PINK, "S"
                elif score >= 10000:
                    rank_color, rank = NEON_YELLOW, "A"
                elif score >= 5000:
                    rank_color, rank = NEON_GREEN, "B"
                elif score >= 1000:
                    rank_color, rank = NEON_CYAN, "C"
                else:
                    rank_color, rank = (150, 150, 180), "D"
                pygame.draw.rect(game_surface, (15, 8, 30), (ix, iy, iw, item_h - 8), border_radius=6)
                pygame.draw.rect(game_surface, rank_color, (ix, iy, iw, item_h - 8), 2, border_radius=6)
                draw_text(game_surface, rank, 36, ix + 35, iy + (item_h - 8) // 2, rank_color, center=True, glow=True)
                mode = entry.get('mode', 'marathon').upper()
                draw_text(game_surface, f"{mode}  SCORE: {score}", 20, ix + 70, iy + 6, WHITE)
                draw_text(game_surface, f"LINES: {entry.get('lines', 0)}   LEVEL: {entry.get('level', 1)}   TIME: {entry.get('duration', 0)}s",
                          14, ix + 70, iy + 30, (180, 180, 200))
                draw_text(game_surface, entry.get('date', '?'), 14, ix + iw - 200, iy + 6, NEON_CYAN)
                new_achs = entry.get('achievements', [])
                if new_achs:
                    ach_str = " ".join(new_achs[:4])
                    if len(new_achs) > 4:
                        ach_str += f" +{len(new_achs) - 4}"
                    draw_text(game_surface, f"* {ach_str}", 12, ix + iw - 200, iy + 30, NEON_YELLOW)
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
            draw_text(game_surface, "No games yet", 28, WIDTH // 2, HEIGHT // 2, (150, 150, 180), center=True)

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
def play_game(mode='marathon'):
    board = Board()

    # صف قطعات
    piece_queue = deque()
    for _ in range(5):
        piece_queue.append(Tetromino(random.choice(PIECE_KEYS)))

    # قطعه فعلی
    current_piece = None
    hold_piece = None
    can_hold = True

    # وضعیت بازی
    score = 0
    display_score = 0
    lines = 0
    level = settings['start_level']
    combo = 0
    max_combo = 0
    back_to_back = 0

    # تایمرها
    drop_timer = 0
    drop_interval = 0  # بر اساس level
    lock_delay = 0
    lock_delay_max = 30  # 0.5 ثانیه

    # کنترل DAS/ARR
    move_left_timer = 0
    move_right_timer = 0
    move_left_held = False
    move_right_held = False
    das_delay = 10
    arr_delay = 3
    das_charged = False

    soft_drop = False

    # افکت‌ها
    screen_shake = 0
    flash = 0
    line_flash = []  # خطوط در حال فلش
    line_flash_timer = 0
    screen_flash_alpha = 0
    combo_text_timer = 0
    combo_text = ""

    # زمان
    total_frames = 0
    elapsed_seconds = 0
    time_limit = None
    if mode == 'ultra':
        time_limit = 120  # 2 دقیقه

    # نتایج
    new_achs = []
    notifications = []
    game_over = False
    paused = False
    final_score = 0
    final_lines = 0
    final_level = 1

    game_saved = False
    go_anim = 0

    # دکمه‌ها
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
        add_game_to_history(score, lines, level, elapsed_seconds, mode, new_achs)

    def spawn_new_piece():
        nonlocal current_piece, can_hold
        if len(piece_queue) < 5:
            piece_queue.append(Tetromino(random.choice(PIECE_KEYS)))
        current_piece = piece_queue.popleft()
        # موقعیت شروع
        current_piece.x = COLS // 2 - 2
        current_piece.y = -1
        # چک برخورد اولیه
        if not board.is_valid_position(current_piece.get_absolute_cells()):
            # game over
            return False
        can_hold = True
        return True

    def get_drop_interval():
        # سرعت افت بر اساس level
        base = max(0.1, 1.0 - (level - 1) * 0.07)
        return max(2, int(base * FPS))

    def lock_current_piece():
        nonlocal current_piece, lines, level, score, combo, back_to_back, line_flash, line_flash_timer, screen_flash_alpha
        board.lock_piece(current_piece)
        # چک کردن خطوط پر
        full_lines = board.check_full_lines()
        if full_lines:
            n = len(full_lines)
            # محاسبه امتیاز
            base_scores = {1: 100, 2: 300, 3: 500, 4: 800}
            points = base_scores.get(n, 0) * level
            # combo
            if combo > 0:
                points += 50 * combo * level
            # back to back
            if n == 4:
                if back_to_back > 0:
                    points = int(points * 1.5)
                back_to_back += 1
            else:
                back_to_back = 0
            score += points
            combo += 1
            max_combo = max(max_combo, combo)

            # افکت‌ها
            play_sound('tetris' if n == 4 else 'line')
            if n == 4:
                if settings['screen_shake']:
                    screen_shake = 20
                screen_flash_alpha = 200
                # ذرات
                for y in full_lines:
                    for x in range(COLS):
                        px = BOARD_X + x * CELL_SIZE + CELL_SIZE // 2
                        py = BOARD_Y + y * CELL_SIZE + CELL_SIZE // 2
                        spawn_particles(px, py, board.grid[y][x] if board.grid[y][x] else WHITE,
                                        8, 1.5, 1.2, 1.3)
            else:
                if settings['screen_shake']:
                    screen_shake = 8

            # ذرات انفجار
            for y in full_lines:
                for x in range(COLS):
                    px = BOARD_X + x * CELL_SIZE + CELL_SIZE // 2
                    py = BOARD_Y + y * CELL_SIZE + CELL_SIZE // 2
                    color = board.grid[y][x] if board.grid[y][x] else NEON_CYAN
                    spawn_particles(px, py, color, 5, 1.2, 1.0, 1.2)

            # ذخیره برای فلش
            line_flash = full_lines[:]
            line_flash_timer = 15

            # حذف خطوط
            board.clear_lines(full_lines)
            lines += n

            # چک دستاوردها
            if lines >= 1:
                try_unlock('first_line')
            if lines >= 10:
                try_unlock('lines_10')
            if lines >= 50:
                try_unlock('lines_50')
            if lines >= 100:
                try_unlock('lines_100')
            if n == 4:
                try_unlock('tetris')
            if combo >= 5:
                try_unlock('combo_5')

            # نمایش combo
            if combo > 1:
                nonlocal combo_text_timer, combo_text
                combo_text = f"x{combo} COMBO"
                combo_text_timer = 60
                play_sound('combo')

            # افزایش level
            new_level = 1 + lines // 10
            if new_level > level:
                level = new_level
                play_sound('levelup')
                if level >= 5:
                    try_unlock('level_5')
                if level >= 10:
                    try_unlock('level_10')
                if level >= 15:
                    try_unlock('level_15')
        else:
            combo = 0

        # چک دستاورد امتیاز
        if score >= 1000:
            try_unlock('score_1000')
        if score >= 5000:
            try_unlock('score_5000')
        if score >= 10000:
            try_unlock('score_10000')
        if score >= 50000:
            try_unlock('score_50000')

        # چک باخت
        if not spawn_new_piece():
            return False
        return True

    # شروع
    if not spawn_new_piece():
        game_over = True

    drop_interval = get_drop_interval()

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
                    play_game(mode)
                    return
                if btn_menu.is_clicked(event):
                    stop_music()
                    return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p and not game_over:
                    paused = not paused
                if event.key == pygame.K_r and game_over:
                    stop_music()
                    play_game(mode)
                    return
                if event.key == pygame.K_ESCAPE:
                    stop_music()
                    if not game_saved:
                        save_current()
                        game_saved = True
                    return

                if not paused and not game_over and current_piece:
                    # Rotation
                    if event.key in (pygame.K_UP, pygame.K_x):
                        # چرخش ساعتگرد
                        old_rot = current_piece.rotation
                        new_rot = (old_rot + 1) % 4
                        kicks = KICKS_I if current_piece.kind == 'I' else KICKS_JLSTZ
                        kick_table = kicks.get((old_rot, new_rot), [(0, 0)])
                        for dx, dy in kick_table:
                            test_cells = current_piece.get_absolute_cells(rotation=new_rot,
                                                                          x=current_piece.x + dx,
                                                                          y=current_piece.y - dy)
                            if board.is_valid_position(test_cells):
                                current_piece.rotation = new_rot
                                current_piece.x += dx
                                current_piece.y -= dy
                                play_sound('rotate')
                                break
                    elif event.key == pygame.K_z:
                        # چرخش پادساعتگرد
                        old_rot = current_piece.rotation
                        new_rot = (old_rot - 1) % 4
                        kicks = KICKS_I if current_piece.kind == 'I' else KICKS_JLSTZ
                        kick_table = kicks.get((old_rot, new_rot), [(0, 0)])
                        for dx, dy in kick_table:
                            test_cells = current_piece.get_absolute_cells(rotation=new_rot,
                                                                          x=current_piece.x + dx,
                                                                          y=current_piece.y - dy)
                            if board.is_valid_position(test_cells):
                                current_piece.rotation = new_rot
                                current_piece.x += dx
                                current_piece.y -= dy
                                play_sound('rotate')
                                break
                    # Hold
                    elif event.key in (pygame.K_c, pygame.K_LSHIFT):
                        if can_hold:
                            if hold_piece is None:
                                hold_piece = current_piece
                                if not spawn_new_piece():
                                    pass
                            else:
                                temp = hold_piece
                                hold_piece = current_piece
                                current_piece = temp
                                current_piece.rotation = 0
                                current_piece.x = COLS // 2 - 2
                                current_piece.y = -1
                            can_hold = False
                            play_sound('hold')
                            try_unlock('hold_used')

            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    move_left_held = False
                    das_charged = False
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    move_right_held = False
                    das_charged = False

        for notif in notifications[:]:
            notif['timer'] -= 1
            if notif['timer'] <= 0:
                notifications.remove(notif)

        if paused and not game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            game_surface.blit(overlay, (0, 0))
            box_w, box_h = 420, 260
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
            elapsed_seconds = total_frames // FPS

            # چک time limit برای ultra
            if time_limit is not None:
                remaining = time_limit - elapsed_seconds
                if remaining <= 0:
                    game_over = True
                    final_score = score
                    final_lines = lines
                    final_level = level
                    highscore[0] = max(highscore[0], score)
                    save_current()
                    game_saved = True
                    play_sound('gameover')
                    go_anim = 0

            # آپدیت اسکور نمایشی
            if display_score < score:
                display_score += max(1, (score - display_score) // 5)
                if display_score > score:
                    display_score = score

            # آپدیت تایمرها
            if screen_shake > 0:
                screen_shake -= 1
            if flash > 0:
                flash -= 8
            if screen_flash_alpha > 0:
                screen_flash_alpha -= 12
            if line_flash_timer > 0:
                line_flash_timer -= 1
            if combo_text_timer > 0:
                combo_text_timer -= 1

            # ورودی held
            keys = pygame.key.get_pressed()
            if not paused and not game_over and current_piece:
                # حرکت چپ
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    if not move_left_held:
                        move_left_held = True
                        move_left_timer = 0
                        test_cells = current_piece.get_absolute_cells(x=current_piece.x - 1)
                        if board.is_valid_position(test_cells):
                            current_piece.x -= 1
                            play_sound('move')
                    else:
                        move_left_timer += 1
                        if move_left_timer >= das_delay:
                            if move_left_timer % arr_delay == 0:
                                test_cells = current_piece.get_absolute_cells(x=current_piece.x - 1)
                                if board.is_valid_position(test_cells):
                                    current_piece.x -= 1

                # حرکت راست
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    if not move_right_held:
                        move_right_held = True
                        move_right_timer = 0
                        test_cells = current_piece.get_absolute_cells(x=current_piece.x + 1)
                        if board.is_valid_position(test_cells):
                            current_piece.x += 1
                            play_sound('move')
                    else:
                        move_right_timer += 1
                        if move_right_timer >= das_delay:
                            if move_right_timer % arr_delay == 0:
                                test_cells = current_piece.get_absolute_cells(x=current_piece.x + 1)
                                if board.is_valid_position(test_cells):
                                    current_piece.x += 1

                # Soft drop
                if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    soft_drop = True
                    drop_timer = drop_interval  # سرعت افت
                    if total_frames % 2 == 0:
                        score += 1
                else:
                    soft_drop = False

                # Hard drop با Space
                # (این رو با keydown انجام میدیم)

            # Hard drop
            if not paused and not game_over and current_piece:
                if keys[pygame.K_SPACE]:
                    # hard drop
                    drop_y = board.get_drop_position(current_piece)
                    cells_dropped = drop_y - current_piece.y
                    if cells_dropped > 0:
                        current_piece.y = drop_y
                        score += cells_dropped * 2
                        play_sound('drop')
                        if settings['screen_shake']:
                            screen_shake = 6
                        # ذرات در محل قفل
                        for cx, cy in current_piece.get_absolute_cells():
                            if cy >= 0:
                                px = BOARD_X + cx * CELL_SIZE + CELL_SIZE // 2
                                py = BOARD_Y + cy * CELL_SIZE + CELL_SIZE // 2
                                spawn_particles(px, py, current_piece.color, 3, 1.2)
                        lock_current_piece()
                    continue

            # آپدیت افت خودکار
            if not paused and not game_over and current_piece:
                drop_timer += 1
                if drop_timer >= drop_interval:
                    drop_timer = 0
                    # چک کن می‌تونه بره پایین
                    test_cells = current_piece.get_absolute_cells(y=current_piece.y + 1)
                    if board.is_valid_position(test_cells):
                        current_piece.y += 1
                        lock_delay = 0
                    else:
                        # نمی‌تونه بره، lock delay شروع
                        lock_delay += 1
                        if lock_delay >= lock_delay_max:
                            lock_current_piece()
                            lock_delay = 0

                # اگه قطعه هنوز می‌تونه بره پایین ولی lock_delay داره
                if lock_delay > 0:
                    test_cells = current_piece.get_absolute_cells(y=current_piece.y + 1)
                    if board.is_valid_position(test_cells):
                        lock_delay = 0

            # آپدیت ذرات
            for p in active_particles[:]:
                p.update()
                if not p.active:
                    active_particles.remove(p)

        # ============================================================
        #                    رسم
        # ============================================================
        game_surface.fill(BLACK)
        offset_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        offset_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0

        play_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # پس‌زمینه
        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            play_layer.blit(s, (0, y))

        # ستاره‌ها
        for _ in range(50):
            pygame.draw.circle(play_layer, (60, 80, 130),
                               (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 1)

        # کادر Board
        board_rect = pygame.Rect(BOARD_X - 4, BOARD_Y - 4, BOARD_W + 8, BOARD_H + 8)
        pygame.draw.rect(play_layer, (5, 8, 20), board_rect, border_radius=8)
        pygame.draw.rect(play_layer, NEON_CYAN, board_rect, 2, border_radius=8)
        pygame.draw.rect(play_layer, NEON_PURPLE, board_rect.inflate(6, 6), 1, border_radius=10)

        # Grid
        for x in range(COLS + 1):
            px = BOARD_X + x * CELL_SIZE
            pygame.draw.line(play_layer, (20, 30, 50), (px, BOARD_Y), (px, BOARD_Y + BOARD_H), 1)
        for y in range(ROWS + 1):
            py = BOARD_Y + y * CELL_SIZE
            pygame.draw.line(play_layer, (20, 30, 50), (BOARD_X, py), (BOARD_X + BOARD_W, py), 1)

        # بلوک‌های موجود
        for y in range(ROWS):
            for x in range(COLS):
                if board.grid[y][x] is not None:
                    px = BOARD_X + x * CELL_SIZE
                    py = BOARD_Y + y * CELL_SIZE
                    # فلش اگه توی خط فلش داره
                    color = board.grid[y][x]
                    if line_flash_timer > 0 and y in line_flash:
                        # فلش سفید
                        blend = line_flash_timer / 15
                        color = (
                            min(255, int(color[0] + (255 - color[0]) * blend)),
                            min(255, int(color[1] + (255 - color[1]) * blend)),
                            min(255, int(color[2] + (255 - color[2]) * blend)),
                        )
                    draw_neon_block(play_layer, px, py, CELL_SIZE, color)

        # Ghost piece
        if settings['ghost_piece'] and current_piece and not game_over:
            drop_y = board.get_drop_position(current_piece)
            ghost_cells = current_piece.get_absolute_cells(y=drop_y)
            for cx, cy in ghost_cells:
                if cy >= 0:
                    px = BOARD_X + cx * CELL_SIZE
                    py = BOARD_Y + cy * CELL_SIZE
                    draw_neon_block(play_layer, px, py, CELL_SIZE, current_piece.color, glow=False, alpha=100)

        # قطعه فعلی
        if current_piece and not game_over:
            for cx, cy in current_piece.get_absolute_cells():
                if cy >= 0:
                    px = BOARD_X + cx * CELL_SIZE
                    py = BOARD_Y + cy * CELL_SIZE
                    draw_neon_block(play_layer, px, py, CELL_SIZE, current_piece.color)

        # ذرات
        for p in active_particles:
            p.draw(play_layer)

        # فلش کل صفحه
        if screen_flash_alpha > 0:
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 255, 255, screen_flash_alpha))
            play_layer.blit(fs, (0, 0))

        if flash > 0:
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 200, 100, flash))
            play_layer.blit(fs, (0, 0))

        game_surface.blit(play_layer, (offset_x, offset_y))

        # ============================================================
        #                    HUD
        # ============================================================
        # عنوان
        draw_text(game_surface, "NEON", 20, 25, 15, WHITE)
        draw_text(game_surface, "TETRIS", 20, 25 + get_font(20).size("NEON ")[0], 15, NEON_CYAN, glow=True)

        mode_text = mode.upper()
        draw_text(game_surface, f"MODE: {mode_text}", 12, 25, 42, (180, 200, 220))

        # SCORE
        draw_text(game_surface, "SCORE", 14, WIDTH - 25, 12, NEON_CYAN)
        draw_text(game_surface, f"{display_score}", 26, WIDTH - 25, 30, WHITE, glow=True)

        # LEVEL و LINES
        draw_text(game_surface, f"LEVEL: {level}", 16, WIDTH - 25, 62, NEON_GREEN)
        draw_text(game_surface, f"LINES: {lines}", 14, WIDTH - 25, 84, NEON_YELLOW)

        # Hold panel
        hold_rect = pygame.Rect(HOLD_X, HOLD_Y, PANEL_W, 100)
        pygame.draw.rect(game_surface, (5, 8, 20), hold_rect, border_radius=8)
        pygame.draw.rect(game_surface, NEON_PURPLE if can_hold else (80, 40, 100), hold_rect, 2, border_radius=8)
        draw_text(game_surface, "HOLD", 14, hold_rect.centerx, hold_rect.y + 15, NEON_PURPLE, center=True)

        if hold_piece:
            cells = hold_piece.get_cells()
            # مرکز کردن قطعه
            min_cx = min(c[0] for c in cells)
            max_cx = max(c[0] for c in cells)
            min_cy = min(c[1] for c in cells)
            max_cy = max(c[1] for c in cells)
            pw = (max_cx - min_cx + 1) * 22
            ph = (max_cy - min_cy + 1) * 22
            start_x = hold_rect.centerx - pw // 2
            start_y = hold_rect.centery - ph // 2 + 10
            for cx, cy in cells:
                px = start_x + (cx - min_cx) * 22
                py = start_y + (cy - min_cy) * 22
                draw_neon_block(game_surface, px, py, 22, hold_piece.color, glow=False)

        # Next panel
        next_rect = pygame.Rect(NEXT_X, NEXT_Y, PANEL_W, 320)
        pygame.draw.rect(game_surface, (5, 8, 20), next_rect, border_radius=8)
        pygame.draw.rect(game_surface, NEON_CYAN, next_rect, 2, border_radius=8)
        draw_text(game_surface, "NEXT", 14, next_rect.centerx, next_rect.y + 15, NEON_CYAN, center=True)

        # نمایش 4 قطعه بعدی
        for i, piece in enumerate(list(piece_queue)[:4]):
            cells = piece.get_cells()
            min_cx = min(c[0] for c in cells)
            max_cx = max(c[0] for c in cells)
            min_cy = min(c[1] for c in cells)
            max_cy = max(c[1] for c in cells)
            pw = (max_cx - min_cx + 1) * 20
            ph = (max_cy - min_cy + 1) * 20
            start_x = next_rect.centerx - pw // 2
            start_y = next_rect.y + 40 + i * 70
            for cx, cy in cells:
                px = start_x + (cx - min_cx) * 20
                py = start_y + (cy - min_cy) * 20
                draw_neon_block(game_surface, px, py, 20, piece.color, glow=False)

        # COMBO text وسط
        if combo_text_timer > 0:
            alpha = min(255, combo_text_timer * 6)
            size = 40 + int(math.sin(t * 15) * 5)
            draw_text(game_surface, combo_text, size, WIDTH // 2, BOARD_Y + BOARD_H // 2,
                      NEON_YELLOW, center=True, glow=True)

        # تایمر برای Ultra
        if time_limit is not None and not game_over:
            remaining = max(0, time_limit - elapsed_seconds)
            mins = remaining // 60
            secs = remaining % 60
            timer_color = NEON_GREEN if remaining > 30 else NEON_YELLOW if remaining > 10 else NEON_RED
            draw_text(game_surface, f"{mins:01d}:{secs:02d}", 30, WIDTH // 2, 80,
                      timer_color, center=True, glow=True)

        # Notifications
        for i, notif in enumerate(notifications):
            ny = 130 + i * 60
            alpha = min(255, notif['timer'] * 2)
            ach = notif['ach']
            notif_surf = pygame.Surface((340, 55), pygame.SRCALPHA)
            notif_surf.fill((10, 5, 25, min(220, alpha)))
            game_surface.blit(notif_surf, (WIDTH - 360, ny))
            pygame.draw.rect(game_surface, NEON_YELLOW, (WIDTH - 360, ny, 340, 55), 2)
            draw_text(game_surface, "ACHIEVEMENT UNLOCKED!", 12, WIDTH - 345, ny + 5, NEON_YELLOW)
            draw_text(game_surface, ach['name'], 18, WIDTH - 345, ny + 22, WHITE, glow=True)

        # Game Over
        if game_over:
            go_anim += 1
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            game_surface.blit(overlay, (0, 0))
            box_w, box_h = 540, 400
            box_x = WIDTH // 2 - box_w // 2
            box_y = HEIGHT // 2 - box_h // 2
            pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h))
            pygame.draw.rect(game_surface, NEON_PINK, (box_x, box_y, box_w, box_h), 3)
            pygame.draw.rect(game_surface, NEON_CYAN, (box_x + 5, box_y + 5, box_w - 10, box_h - 10), 1)

            if time_limit is not None and elapsed_seconds >= time_limit:
                draw_text(game_surface, "TIME'S UP!", 56, WIDTH // 2, box_y + 55,
                          NEON_YELLOW, center=True, glow=True)
            else:
                draw_text(game_surface, "GAME OVER", 60, WIDTH // 2, box_y + 55,
                          NEON_RED, center=True, glow=True)

            draw_text(game_surface, f"SCORE: {final_score}", 32, WIDTH // 2, box_y + 115,
                      WHITE, center=True)
            draw_text(game_surface, f"LINES: {final_lines}   LEVEL: {final_level}", 20,
                      WIDTH // 2, box_y + 155, NEON_CYAN, center=True)
            hs = highscore[0]
            if final_score >= hs and final_score > 0:
                draw_text(game_surface, "* NEW HIGH SCORE! *", 22, WIDTH // 2, box_y + 190,
                          NEON_YELLOW, center=True, glow=True)
            else:
                draw_text(game_surface, f"HIGH SCORE: {hs}", 18, WIDTH // 2, box_y + 190,
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
            mode = show_mode_select()
            if mode:
                play_game(mode)
    pygame.quit()


if __name__ == "__main__":
    main()