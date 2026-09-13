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
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    AUDIO_OK = True
except:
    AUDIO_OK = False

BASE_W, BASE_H = 900, 900
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("NEON PAC-MAN")
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

# رنگ ارواح
GHOST_RED = (255, 50, 50)
GHOST_PINK = (255, 100, 180)
GHOST_CYAN = (100, 200, 255)
GHOST_ORANGE = (255, 180, 50)
GHOST_SCARED = (50, 50, 200)
GHOST_FLASH = (255, 255, 255)

# --- ابعاد Maze ---
CELL_SIZE = 30
COLS = 21
ROWS = 23
MAZE_W = COLS * CELL_SIZE
MAZE_H = ROWS * CELL_SIZE
MAZE_X = (WIDTH - MAZE_W) // 2
MAZE_Y = (HEIGHT - MAZE_H) // 2 + 20

# --- Maze Layout ---
# 0 = خالی (path), 1 = دیوار, 2 = pellet, 3 = power pellet
# 4 = در خونه ارواح
MAZE = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,2,2,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2,2,1],
    [1,3,2,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2,3,1],
    [1,2,2,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2,2,1],
    [1,2,2,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2,2,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
    [1,1,1,1,1,1,1,1,1,1,4,1,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
    [1,1,1,1,1,1,1,1,1,2,2,2,1,1,1,1,1,1,1,1,1],
    [1,2,2,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2,2,1],
    [1,2,2,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2,2,1],
    [1,3,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,3,1],
    [1,2,2,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2,2,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

# --- ذخیره ---
SAVE_FILE = "neon_pacman_save.json"
settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'difficulty': 1.0,
    'screen_shake': True,
}
achievements = {
    'first_pellet': {'name': 'FIRST BITE', 'desc': 'Eat your first pellet', 'unlocked': False, 'icon': '.'},
    'pellet_100': {'name': 'ROOKIE', 'desc': 'Eat 100 pellets', 'unlocked': False, 'icon': '..'},
    'pellet_500': {'name': 'VETERAN', 'desc': 'Eat 500 pellets', 'unlocked': False, 'icon': '...'},
    'pellet_2000': {'name': 'LEGEND', 'desc': 'Eat 2000 pellets', 'unlocked': False, 'icon': '....'},
    'first_ghost': {'name': 'GHOST BUSTER', 'desc': 'Eat your first ghost', 'unlocked': False, 'icon': 'G'},
    'ghost_10': {'name': 'HUNTER', 'desc': 'Eat 10 ghosts', 'unlocked': False, 'icon': 'GG'},
    'ghost_50': {'name': 'SLAYER', 'desc': 'Eat 50 ghosts', 'unlocked': False, 'icon': 'GGG'},
    'ghost_100': {'name': 'EXTERMINATOR', 'desc': 'Eat 100 ghosts', 'unlocked': False, 'icon': 'GGGG'},
    'level_2': {'name': 'EXPLORER', 'desc': 'Reach level 2', 'unlocked': False, 'icon': 'L2'},
    'level_5': {'name': 'ADVENTURER', 'desc': 'Reach level 5', 'unlocked': False, 'icon': 'L5'},
    'level_10': {'name': 'MASTER', 'desc': 'Reach level 10', 'unlocked': False, 'icon': 'L10'},
    'score_5000': {'name': 'SCORER', 'desc': 'Score 5000 points', 'unlocked': False, 'icon': '$5K'},
    'score_20000': {'name': 'ACE', 'desc': 'Score 20000 points', 'unlocked': False, 'icon': '$20K'},
    'combo_4': {'name': 'COMBO KING', 'desc': 'Eat 4 ghosts in one power', 'unlocked': False, 'icon': 'C4'},
    'fruit_10': {'name': 'FRUIT LOVER', 'desc': 'Eat 10 fruits', 'unlocked': False, 'icon': 'F'},
}
highscore = [0]
game_history = []
total_pellets = [0]
total_ghosts = [0]
total_fruits = [0]


def load_save():
    global settings, achievements, highscore, game_history, total_pellets, total_ghosts, total_fruits
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
            settings.update(data.get('settings', {}))
            for k, v in data.get('achievements', {}).items():
                if k in achievements:
                    achievements[k]['unlocked'] = v
            highscore[0] = data.get('highscore', 0)
            game_history = data.get('game_history', [])
            total_pellets[0] = data.get('total_pellets', 0)
            total_ghosts[0] = data.get('total_ghosts', 0)
            total_fruits[0] = data.get('total_fruits', 0)
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
                'total_pellets': total_pellets[0],
                'total_ghosts': total_ghosts[0],
                'total_fruits': total_fruits[0],
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


def add_game_to_history(score, level, duration, new_achs):
    entry = {
        'score': score,
        'level': level,
        'duration': duration,
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
    sounds['chomp'] = make_sound(400, 300, 0.06, 0.12, 'square')
    sounds['power'] = make_sound(200, 600, 0.2, 0.22, 'sine')
    sounds['eat_ghost'] = make_sound(800, 1600, 0.4, 0.28, 'sine')
    sounds['eat_fruit'] = make_sound(600, 1500, 0.3, 0.25, 'sine')
    sounds['death'] = make_sound(600, 100, 0.8, 0.30, 'saw')
    sounds['levelup'] = make_sound(400, 1500, 0.6, 0.25, 'sine')
    sounds['gameover'] = make_sound(500, 60, 1.5, 0.30, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['ghost_move'] = make_sound(150, 200, 0.1, 0.08, 'square')

    bass = [73.4, 73.4, 82.4, 82.4, 65.4, 65.4, 73.4, 73.4]
    lead = [523, 587, 659, 587, 523, 494, 440, 494]
    music_sound[0] = make_music_loop(bass, lead, 0.25, 0.10)
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

    def spawn(self, x, y, color, speed_mult=1.0, size_mult=1.0, life_mult=1.0, gravity=0.1):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 6) * speed_mult
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = int(random.randint(20, 40) * life_mult)
        self.max_life = self.life
        self.color = color
        self.size = random.randint(2, 5) * size_mult
        self.gravity = gravity
        self.active = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
        self.vy += self.gravity
        self.life -= 1
        if self.life <= 0:
            self.active = False

    def draw(self, surface):
        if self.life > 0:
            alpha = self.life / self.max_life
            size = max(1, int(self.size * alpha))
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), size)


def spawn_particles(x, y, color, count, speed_mult=1.0, size_mult=1.0, life_mult=1.0, gravity=0.1):
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
#                    Game State
# ============================================================
class GameState:
    def __init__(self):
        self.maze = [row[:] for row in MAZE]
        self.pellets_left = sum(1 for row in self.maze for c in row if c == 2 or c == 3)
        self.power_timer = 0
        self.ghost_combo = 0
        self.level = 1
        self.score = 0
        self.arcade_timer = 0


# ============================================================
#                    Pac-Man
# ============================================================
class PacMan:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.radius = CELL_SIZE * 0.4
        self.speed = 3.0
        self.dx = 0
        self.dy = 0
        self.next_dx = 0
        self.next_dy = 0
        self.mouth_angle = 0
        self.anim_timer = 0
        self.alive = True
        self.death_anim = 0
        self.moving = False

    def grid_pos(self):
        return (int(self.x), int(self.y))

    def is_wall(self, gx, gy, maze):
        if gx < 0 or gx >= COLS or gy < 0 or gy >= ROWS:
            return True
        return maze[gy][gx] == 1

    def can_move(self, dx, dy, maze):
        if dx == 0 and dy == 0:
            return False
        # موقعیت جدید
        new_gx = self.x + dx * self.speed
        new_gy = self.y + dy * self.speed
        # چک خونه‌ی جدید
        cx = int(round(new_gx))
        cy = int(round(new_gy))
        if self.is_wall(cx, cy, maze):
            return False
        return True

    def update(self, maze, keys, power_mode):
        if not self.alive:
            self.death_anim += 1
            return

        # ورودی
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.next_dx = -1
            self.next_dy = 0
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.next_dx = 1
            self.next_dy = 0
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            self.next_dx = 0
            self.next_dy = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.next_dx = 0
            self.next_dy = 1

        # سرعت بر اساس power mode
        self.speed = 3.2 if power_mode else 3.0

        # تلاش برای حرکت در جهت بعدی
        if self.next_dx != 0 or self.next_dy != 0:
            if self.can_move(self.next_dx, self.next_dy, maze):
                self.dx = self.next_dx
                self.dy = self.next_dy

        # حرکت در جهت فعلی
        if self.can_move(self.dx, self.dy, maze):
            self.x += self.dx * self.speed
            self.y += self.dy * self.speed
            self.moving = True
        else:
            # اسنپ به مرکز خونه
            self.moving = False

        # انیمیشن دهان
        if self.moving:
            self.anim_timer += 0.3
            self.mouth_angle = abs(math.sin(self.anim_timer)) * 40
        else:
            self.mouth_angle = 20

        # Wrap tunnel (ردیف وسط)
        if self.x < -0.5:
            self.x = COLS - 0.5
        elif self.x > COLS - 0.5:
            self.x = -0.5

    def reset_position(self):
        self.x = self.start_x
        self.y = self.start_y
        self.dx = 0
        self.dy = 0
        self.next_dx = 0
        self.next_dy = 0
        self.alive = True
        self.death_anim = 0

    def pixel_pos(self):
        return (MAZE_X + self.x * CELL_SIZE + CELL_SIZE / 2,
                MAZE_Y + self.y * CELL_SIZE + CELL_SIZE / 2)

    def draw(self, surface):
        px, py = self.pixel_pos()

        if not self.alive:
            # انیمیشن مرگ - کوچک شدن
            r = max(0, self.radius - self.death_anim * 0.5)
            if r > 0:
                pygame.draw.circle(surface, NEON_YELLOW, (int(px), int(py)), int(r))
            return

        # زاویه بر اساس جهت
        base_angle = 0
        if self.dx > 0:
            base_angle = 0
        elif self.dx < 0:
            base_angle = 180
        elif self.dy < 0:
            base_angle = 90
        elif self.dy > 0:
            base_angle = 270

        # رسم Pac-Man (دایره با مثلث بریده)
        mouth = self.mouth_angle
        if self.dx == 0 and self.dy == 0:
            mouth = 20

        # محاسبه نقاط
        start_angle = math.radians(base_angle + mouth)
        end_angle = math.radians(base_angle + 360 - mouth)

        # هاله
        for r in range(3, 0, -1):
            glow_size = self.radius * 2 + r * 8
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*NEON_YELLOW, 50 - r * 15),
                               (glow_size // 2, glow_size // 2), glow_size // 2)
            surface.blit(glow, (px - glow_size // 2, py - glow_size // 2))

        # بدنه
        points = [(px, py)]
        steps = 20
        for i in range(steps + 1):
            a = start_angle + (end_angle - start_angle) * i / steps
            x = px + math.cos(a) * self.radius
            y = py + math.sin(a) * self.radius
            points.append((x, y))
        points.append((px, py))

        pygame.draw.polygon(surface, NEON_YELLOW, points)
        pygame.draw.polygon(surface, WHITE, points, 2)

        # چشم
        eye_offset = 6
        eye_x = px + math.cos(math.radians(base_angle + 90)) * 0
        # ساده: چشم رو در جهت حرکت بذار
        if self.dx > 0:
            eye_x, eye_y = px + 4, py - 5
        elif self.dx < 0:
            eye_x, eye_y = px - 4, py - 5
        elif self.dy < 0:
            eye_x, eye_y = px + 3, py - 5
        elif self.dy > 0:
            eye_x, eye_y = px + 3, py + 3
        else:
            eye_x, eye_y = px + 3, py - 5

        pygame.draw.circle(surface, WHITE, (int(eye_x), int(eye_y)), 3)
        pygame.draw.circle(surface, BLACK, (int(eye_x), int(eye_y)), 1.5)


# ============================================================
#                    Ghost
# ============================================================
class Ghost:
    def __init__(self, x, y, kind='blinky'):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.kind = kind
        self.speed = 2.8
        self.dx = 0
        self.dy = -1
        self.alive = True
        self.scared = False
        self.eaten = False  # برمی‌گرده به خونه
        self.anim_timer = 0

        colors = {
            'blinky': GHOST_RED,
            'pinky': GHOST_PINK,
            'inky': GHOST_CYAN,
            'clyde': GHOST_ORANGE,
        }
        self.color = colors[kind]

    def grid_pos(self):
        return (int(self.x), int(self.y))

    def is_wall(self, gx, gy, maze):
        if gx < 0 or gx >= COLS or gy < 0 or gy >= ROWS:
            return True
        return maze[gy][gx] == 1

    def can_move(self, dx, dy, maze):
        if dx == 0 and dy == 0:
            return False
        new_gx = self.x + dx * self.speed
        new_gy = self.y + dy * self.speed
        cx = int(round(new_gx))
        cy = int(round(new_gy))
        if self.is_wall(cx, cy, maze):
            return False
        return True

    def get_target(self, pacman, blinky_pos, clyde_pos):
        px, py = pacman.x, pacman.y

        if self.kind == 'blinky':
            # مستقیم تعقیب
            return (px, py)
        elif self.kind == 'pinky':
            # 4 خونه جلوتر
            return (px + pacman.dx * 4, py + pacman.dy * 4)
        elif self.kind == 'inky':
            # رفتار پیچیده: بر اساس بلینکی
            bx, by = blinky_pos
            # نقطه 2 خونه جلوتر
            target_x = px + pacman.dx * 2
            target_y = py + pacman.dy * 2
            # آینه نسبت به بلینکی
            return (target_x * 2 - bx, target_y * 2 - by)
        elif self.kind == 'clyde':
            # اگه دور، تعقیب کن؛ اگه نزدیک، فرار
            dist = math.hypot(px - self.x, py - self.y)
            if dist > 8:
                return (px, py)
            else:
                return (1, ROWS - 2)

    def update(self, maze, pacman, blinky_pos, clyde_pos, power_mode):
        if not self.alive:
            return

        # اگه خورده شده، به خونه برگرده
        if self.eaten:
            # مستقیم به مرکز
            target_x = COLS // 2
            target_y = 10
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)
            if dist < 0.3:
                self.eaten = False
                self.scared = False
                self.x = target_x
                self.y = target_y
                return
            self.x += dx / dist * self.speed
            self.y += dy / dist * self.speed
            return

        self.anim_timer += 0.1
        self.speed = 2.8 if not power_mode else 2.2

        # انتخاب مسیر
        # سر هر خونه، تصمیم می‌گیره
        cx, cy = int(round(self.x)), int(round(self.y))
        if abs(self.x - cx) < 0.1 and abs(self.y - cy) < 0.1:
            # می‌تونه تصمیم بگیره
            target = self.get_target(pacman, blinky_pos, clyde_pos)
            possible = []
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                # معکوس نرو
                if dx == -self.dx and dy == -self.dy:
                    continue
                if not self.is_wall(cx + dx, cy + dy, maze):
                    # فاصله به هدف
                    tx, ty = target
                    dist = (cx + dx - tx) ** 2 + (cy + dy - ty) ** 2
                    possible.append((dist, dx, dy))
            if possible:
                possible.sort()
                # با یه کم رندوم
                if len(possible) > 1 and random.random() < 0.15:
                    chosen = random.choice(possible[:2])
                else:
                    chosen = possible[0]
                self.dx = chosen[1]
                self.dy = chosen[2]

        # حرکت
        if self.can_move(self.dx, self.dy, maze):
            self.x += self.dx * self.speed
            self.y += self.dy * self.speed

        # Wrap
        if self.x < -0.5:
            self.x = COLS - 0.5
        elif self.x > COLS - 0.5:
            self.x = -0.5

    def reset(self):
        self.x = self.start_x
        self.y = self.start_y
        self.dx = 0
        self.dy = -1
        self.eaten = False
        self.scared = False

    def pixel_pos(self):
        return (MAZE_X + self.x * CELL_SIZE + CELL_SIZE / 2,
                MAZE_Y + self.y * CELL_SIZE + CELL_SIZE / 2)

    def draw(self, surface, power_mode):
        if not self.alive:
            return

        px, py = self.pixel_pos()
        r = CELL_SIZE * 0.4

        # رنگ
        if self.eaten:
            color = (100, 100, 100)
        elif self.scared:
            # چشمک سفید/آبی
            if power_mode and (pygame.time.get_ticks() // 200) % 2 == 0:
                color = WHITE
            else:
                color = GHOST_SCARED
        else:
            color = self.color

        # هاله
        for hr in range(3, 0, -1):
            glow_size = r * 2 + hr * 8
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 50 - hr * 15),
                               (glow_size // 2, glow_size // 2), glow_size // 2)
            surface.blit(glow, (px - glow_size // 2, py - glow_size // 2))

        # بدنه روح (شبیه به نیم‌دایره با پای چین‌دار)
        # نیم‌دایره بالا
        pygame.draw.circle(surface, color, (int(px), int(py - 2)), int(r))
        # مستطیل پایین
        bottom_rect = pygame.Rect(int(px - r), int(py - 2), int(r * 2), int(r))
        pygame.draw.rect(surface, color, bottom_rect)
        # چین‌های پایین
        wave_y = py - 2 + r
        wave_amp = 4
        wave_count = 4
        # ساده‌سازی: مثلث‌های کوچک
        for i in range(wave_count):
            x1 = px - r + (i * 2 * r / wave_count)
            x2 = px - r + ((i + 1) * 2 * r / wave_count)
            xm = (x1 + x2) / 2
            pygame.draw.polygon(surface, color, [
                (x1, wave_y),
                (xm, wave_y + wave_amp),
                (x2, wave_y),
            ])

        # حاشیه
        pygame.draw.circle(surface, WHITE, (int(px), int(py - 2)), int(r), 2)

        # چشم‌ها
        eye_offset = r * 0.3
        eye_y = py - 4
        if self.scared:
            # چشم‌های ترسیده
            for ex in [px - eye_offset, px + eye_offset]:
                pygame.draw.circle(surface, WHITE, (int(ex), int(eye_y)), 4)
                pygame.draw.circle(surface, color, (int(ex), int(eye_y)), 2)
        else:
            # چشم‌های عادی
            for ex in [px - eye_offset, px + eye_offset]:
                pygame.draw.circle(surface, WHITE, (int(ex), int(eye_y)), 5)
                # مردمک در جهت حرکت
                pupil_x = ex + self.dx * 2
                pupil_y = eye_y + self.dy * 2
                pygame.draw.circle(surface, BLACK, (int(pupil_x), int(pupil_y)), 2.5)


# ============================================================
#                    Fruit
# ============================================================
class Fruit:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.life = 600  # 10 ثانیه
        self.pulse = 0
        # میوه‌های مختلف
        self.kind = random.choice(['cherry', 'strawberry', 'orange', 'apple', 'melon'])
        self.score_value = {
            'cherry': 100,
            'strawberry': 300,
            'orange': 500,
            'apple': 700,
            'melon': 1000,
        }[self.kind]

    def update(self):
        self.life -= 1
        self.pulse += 0.15

    def pixel_pos(self):
        return (MAZE_X + self.x * CELL_SIZE + CELL_SIZE / 2,
                MAZE_Y + self.y * CELL_SIZE + CELL_SIZE / 2)

    def draw(self, surface):
        px, py = self.pixel_pos()
        r = CELL_SIZE * 0.35 + math.sin(self.pulse) * 2

        colors = {
            'cherry': NEON_RED,
            'strawberry': NEON_PINK,
            'orange': NEON_ORANGE,
            'apple': NEON_GREEN,
            'melon': NEON_YELLOW,
        }
        color = colors[self.kind]

        # هاله
        for hr in range(3, 0, -1):
            glow_size = int(r * 2 + hr * 8)
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 50 - hr * 15),
                               (glow_size // 2, glow_size // 2), glow_size // 2)
            surface.blit(glow, (px - glow_size // 2, py - glow_size // 2))

        # بدنه
        pygame.draw.circle(surface, color, (int(px), int(py)), int(r))
        pygame.draw.circle(surface, WHITE, (int(px), int(py)), int(r), 2)

        # برگ
        pygame.draw.polygon(surface, NEON_GREEN, [
            (px, py - r),
            (px + 6, py - r - 6),
            (px + 2, py - r - 2),
        ])


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
def draw_maze(surface, maze, power_mode, power_timer):
    # هاله‌ی دیوارها
    for y in range(ROWS):
        for x in range(COLS):
            if maze[y][x] == 1:
                px = MAZE_X + x * CELL_SIZE
                py = MAZE_Y + y * CELL_SIZE
                # هاله
                glow = pygame.Surface((CELL_SIZE + 20, CELL_SIZE + 20), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*NEON_BLUE, 50), (0, 0, CELL_SIZE + 20, CELL_SIZE + 20),
                                 border_radius=6)
                surface.blit(glow, (px - 10, py - 10))
                # بدنه
                rect = pygame.Rect(px, py, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(surface, (10, 20, 60), rect)
                pygame.draw.rect(surface, NEON_BLUE, rect, 2)
                # درخشش لبه
                pygame.draw.line(surface, NEON_CYAN, (rect.x, rect.y),
                                 (rect.right, rect.y), 2)

    # Pellet‌ها
    for y in range(ROWS):
        for x in range(COLS):
            cell = maze[y][x]
            px = MAZE_X + x * CELL_SIZE + CELL_SIZE / 2
            py = MAZE_Y + y * CELL_SIZE + CELL_SIZE / 2

            if cell == 2:
                # Pellet عادی
                pygame.draw.circle(surface, NEON_YELLOW, (int(px), int(py)), 3)
                pygame.draw.circle(surface, WHITE, (int(px), int(py)), 3, 1)
            elif cell == 3:
                # Power Pellet
                pulse = 1 + math.sin(pygame.time.get_ticks() / 200) * 0.3
                r = int(8 * pulse)
                # هاله
                for hr in range(3, 0, -1):
                    glow_size = r * 2 + hr * 6
                    glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                    pygame.draw.circle(glow, (*NEON_PINK, 80 - hr * 20),
                                       (glow_size // 2, glow_size // 2), glow_size // 2)
                    surface.blit(glow, (px - glow_size // 2, py - glow_size // 2))
                pygame.draw.circle(surface, NEON_PINK, (int(px), int(py)), r)
                pygame.draw.circle(surface, WHITE, (int(px), int(py)), r, 2)


# ============================================================
#                    Menu
# ============================================================
def show_menu():
    menu_time = 0
    btn_start = Button(WIDTH // 2, HEIGHT // 2 + 30, 320, 55, "START GAME", NEON_YELLOW, NEON_GREEN, 28)
    btn_history = Button(WIDTH // 2, HEIGHT // 2 + 95, 320, 45, "HISTORY", NEON_BLUE, NEON_CYAN, 22)
    btn_settings = Button(WIDTH // 2, HEIGHT // 2 + 150, 320, 45, "SETTINGS", NEON_PURPLE, NEON_PINK, 22)
    btn_achievements = Button(WIDTH // 2, HEIGHT // 2 + 205, 320, 45, "ACHIEVEMENTS", NEON_YELLOW, NEON_ORANGE, 22)
    btn_quit = Button(WIDTH // 2, HEIGHT // 2 + 260, 320, 42, "QUIT", NEON_RED, NEON_ORANGE, 20)
    btn_fullscreen = Button(WIDTH - 40, 30, 40, 40, "[]", NEON_PURPLE, NEON_CYAN, 20)

    while True:
        game_surface.fill(DARK_BG)
        t = pygame.time.get_ticks() / 1000
        menu_time += 1
        mouse_pos = get_game_mouse_pos()

        # آسمان گرادیان
        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            game_surface.blit(s, (0, y))

        # Maze کوچیک تزئینی - Pac-Man و 4 روح شناور
        for _ in range(3):
            px = random.randint(50, WIDTH - 50)
            py = random.randint(50, HEIGHT - 50)

        # Pac-Man تزئینی
        pac_x = 200 + math.sin(t) * 100
        pac_y = 400 + math.cos(t * 1.3) * 50
        # هاله
        for hr in range(3, 0, -1):
            glow_size = 40 + hr * 8
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*NEON_YELLOW, 50 - hr * 15),
                               (glow_size // 2, glow_size // 2), glow_size // 2)
            game_surface.blit(glow, (pac_x - glow_size // 2, pac_y - glow_size // 2))
        # Pac-Man
        mouth = abs(math.sin(t * 5)) * 40
        points = [(pac_x, pac_y)]
        for i in range(21):
            a = math.radians(mouth + (360 - 2 * mouth) * i / 20)
            points.append((pac_x + math.cos(a) * 20, pac_y + math.sin(a) * 20))
        pygame.draw.polygon(game_surface, NEON_YELLOW, points)
        pygame.draw.polygon(game_surface, WHITE, points, 2)

        # 4 روح تزئینی
        ghost_data = [
            (GHOST_RED, WIDTH - 200 + math.sin(t * 1.1) * 50, 380),
            (GHOST_PINK, WIDTH - 260 + math.cos(t * 1.2) * 50, 420),
            (GHOST_CYAN, WIDTH - 140 + math.sin(t * 1.3) * 50, 420),
            (GHOST_ORANGE, WIDTH - 200 + math.cos(t * 1.4) * 50, 460),
        ]
        for color, gx, gy in ghost_data:
            # هاله
            for hr in range(3, 0, -1):
                glow_size = 30 + hr * 8
                glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*color, 50 - hr * 15),
                                   (glow_size // 2, glow_size // 2), glow_size // 2)
                game_surface.blit(glow, (gx - glow_size // 2, gy - glow_size // 2))
            # بدنه
            r = 15
            pygame.draw.circle(game_surface, color, (int(gx), int(gy - 2)), r)
            rect = pygame.Rect(int(gx - r), int(gy - 2), r * 2, r)
            pygame.draw.rect(game_surface, color, rect)
            for i in range(4):
                x1 = gx - r + (i * 2 * r / 4)
                x2 = gx - r + ((i + 1) * 2 * r / 4)
                xm = (x1 + x2) / 2
                pygame.draw.polygon(game_surface, color, [
                    (x1, gy - 2 + r),
                    (xm, gy - 2 + r + 4),
                    (x2, gy - 2 + r),
                ])
            # چشم
            for ex in [gx - 5, gx + 5]:
                pygame.draw.circle(game_surface, WHITE, (int(ex), int(gy - 4)), 4)
                pygame.draw.circle(game_surface, BLACK, (int(ex), int(gy - 4)), 2)

        # عنوان
        title_y = 150 + math.sin(t * 2) * 8
        draw_text(game_surface, "NEON", 72, WIDTH // 2 - 100, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "PAC-MAN", 72, WIDTH // 2 + 130, title_y, NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, "EAT  /  CHASE  /  SURVIVE", 20, WIDTH // 2, title_y + 65,
                  (200, 200, 220), center=True)

        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 22, WIDTH // 2, title_y + 115,
                      NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, f"PELLETS: {total_pellets[0]}   GHOSTS: {total_ghosts[0]}   FRUITS: {total_fruits[0]}",
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
    slider_diff = Slider(WIDTH // 2, 380, 400, 12, (settings['difficulty'] - 0.5) / 1.0, 0, 1, "AI Difficulty")
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
                total_pellets[0] = 0
                total_ghosts[0] = 0
                total_fruits[0] = 0
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
            draw_text(game_surface, a['icon'], 14, cx + 35, y_pos + card_h // 2, icon_color, center=True)
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
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                toggle_fullscreen()
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
                elif score >= 20000:
                    rank_color, rank = NEON_YELLOW, "A"
                elif score >= 10000:
                    rank_color, rank = NEON_GREEN, "B"
                elif score >= 5000:
                    rank_color, rank = NEON_CYAN, "C"
                else:
                    rank_color, rank = (150, 150, 180), "D"
                pygame.draw.rect(game_surface, (15, 8, 30), (ix, iy, iw, item_h - 8), border_radius=6)
                pygame.draw.rect(game_surface, rank_color, (ix, iy, iw, item_h - 8), 2, border_radius=6)
                draw_text(game_surface, rank, 36, ix + 35, iy + (item_h - 8) // 2, rank_color, center=True, glow=True)
                draw_text(game_surface, f"SCORE: {score}", 20, ix + 70, iy + 6, WHITE)
                draw_text(game_surface, f"LEVEL: {entry.get('level', 1)}   TIME: {entry.get('duration', 0)}s",
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
    gs = GameState()

    # Pac-Man در موقعیت شروع (وسط پایین)
    pacman = PacMan(COLS // 2, 17)

    # ارواح
    ghosts = [
        Ghost(COLS // 2 - 2, 10, 'blinky'),
        Ghost(COLS // 2, 10, 'pinky'),
        Ghost(COLS // 2 + 2, 10, 'inky'),
        Ghost(COLS // 2 + 4, 10, 'clyde'),
    ]

    # میوه
    fruits = []
    fruit_spawn_timer = 0

    # افکت‌ها
    screen_shake = 0
    flash = 0
    game_over = False
    paused = False
    final_score = 0
    final_level = 1
    new_achs = []
    notifications = []
    go_anim = 0
    game_saved = False
    total_frames = 0
    death_timer = 0
    level_banner_timer = 120

    # کمبو
    combo = 0

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
        add_game_to_history(gs.score, gs.level, total_frames // FPS, new_achs)

    def reset_level():
        gs.maze = [row[:] for row in MAZE]
        gs.pellets_left = sum(1 for row in gs.maze for c in row if c == 2 or c == 3)
        gs.power_timer = 0
        gs.ghost_combo = 0
        pacman.reset_position()
        for g in ghosts:
            g.reset()
        fruits.clear()

    def next_level():
        nonlocal level_banner_timer
        gs.level += 1
        if gs.level >= 2: try_unlock('level_2')
        if gs.level >= 5: try_unlock('level_5')
        if gs.level >= 10: try_unlock('level_10')
        play_sound('levelup')
        level_banner_timer = 120
        reset_level()
        # سرعت ارواح با level
        for g in ghosts:
            g.speed = 2.8 + (gs.level - 1) * 0.15

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
            keys = pygame.key.get_pressed()

            # آپدیت Pac-Man
            power_mode = gs.power_timer > 0
            if pacman.alive:
                pacman.update(gs.maze, keys, power_mode)

                # خوردن pellet
                gx = int(round(pacman.x))
                gy = int(round(pacman.y))
                if 0 <= gx < COLS and 0 <= gy < ROWS:
                    cell = gs.maze[gy][gx]
                    if cell == 2 or cell == 3:
                        gs.maze[gy][gx] = 0
                        gs.pellets_left -= 1
                        pacman_px, pacman_py = pacman.pixel_pos()
                        if cell == 2:
                            gs.score += 10
                            total_pellets[0] += 1
                            play_sound('chomp')
                            spawn_particles(pacman_px, pacman_py, NEON_YELLOW, 3, 0.8, 0.6, 0.5)
                            if total_pellets[0] >= 1: try_unlock('first_pellet')
                            if total_pellets[0] >= 100: try_unlock('pellet_100')
                            if total_pellets[0] >= 500: try_unlock('pellet_500')
                            if total_pellets[0] >= 2000: try_unlock('pellet_2000')
                        else:  # Power pellet
                            gs.score += 50
                            total_pellets[0] += 1
                            gs.power_timer = 420  # 7 ثانیه
                            gs.ghost_combo = 0
                            play_sound('power')
                            if settings['screen_shake']:
                                screen_shake = 15
                            flash = 100
                            for _ in range(30):
                                spawn_particles(pacman_px, pacman_py, NEON_PINK, 1, 1.5, 1.2, 1.2)
                            # همه ارواح scared بشن
                            for g in ghosts:
                                if not g.eaten:
                                    g.scared = True

                        if gs.score >= 5000: try_unlock('score_5000')
                        if gs.score >= 20000: try_unlock('score_20000')

            # تایمر power
            if gs.power_timer > 0:
                gs.power_timer -= 1
                if gs.power_timer == 0:
                    for g in ghosts:
                        g.scared = False
                    gs.ghost_combo = 0

            # آپدیت ارواح
            if pacman.alive:
                blinky_pos = (ghosts[0].x, ghosts[0].y)
                clyde_pos = (ghosts[3].x, ghosts[3].y)
                for g in ghosts:
                    g.update(gs.maze, pacman, blinky_pos, clyde_pos, power_mode)

                    # برخورد با Pac-Man
                    if not g.eaten:
                        dist = math.hypot(g.x - pacman.x, g.y - pacman.y)
                        if dist < 0.7:
                            if g.scared:
                                # خوردن روح
                                g.eaten = True
                                g.scared = False
                                gs.ghost_combo += 1
                                combo = gs.ghost_combo
                                points = 200 * (2 ** (gs.ghost_combo - 1))
                                gs.score += points
                                total_ghosts[0] += 1
                                play_sound('eat_ghost')
                                if settings['screen_shake']:
                                    screen_shake = 20
                                flash = 150
                                gx_px, gy_px = g.pixel_pos()
                                for _ in range(40):
                                    spawn_particles(gx_px, gy_px, g.color, 1, 1.8, 1.3, 1.3)
                                if total_ghosts[0] >= 1: try_unlock('first_ghost')
                                if total_ghosts[0] >= 10: try_unlock('ghost_10')
                                if total_ghosts[0] >= 50: try_unlock('ghost_50')
                                if total_ghosts[0] >= 100: try_unlock('ghost_100')
                                if gs.ghost_combo >= 4: try_unlock('combo_4')
                            else:
                                # مرگ Pac-Man
                                pacman.alive = False
                                death_timer = 90
                                play_sound('death')
                                if settings['screen_shake']:
                                    screen_shake = 30
                                flash = 200

            # انیمیشن مرگ
            if not pacman.alive:
                death_timer -= 1
                if death_timer <= 0:
                    # ریست
                    pacman.reset_position()
                    for g in ghosts:
                        g.reset()
                    gs.power_timer = 0
                    gs.ghost_combo = 0

            # اسپاون میوه
            fruit_spawn_timer += 1
            if fruit_spawn_timer > FPS * 15:
                fruit_spawn_timer = 0
                if len(fruits) < 2:
                    # موقعیت مرکز
                    fruits.append(Fruit(COLS // 2, 14))

            # آپدیت میوه‌ها
            for f in fruits[:]:
                f.update()
                if f.life <= 0:
                    fruits.remove(f)
                    continue
                # خوردن
                if abs(f.x - pacman.x) < 0.6 and abs(f.y - pacman.y) < 0.6:
                    gs.score += f.score_value
                    total_fruits[0] += 1
                    play_sound('eat_fruit')
                    fx, fy = f.pixel_pos()
                    for _ in range(25):
                        spawn_particles(fx, fy, NEON_GREEN, 1, 1.5, 1.2, 1.2)
                    if total_fruits[0] >= 10:
                        try_unlock('fruit_10')
                    fruits.remove(f)

            # چک تموم شدن
            if gs.pellets_left <= 0:
                next_level()

            # آپدیت ذرات
            for p in active_particles[:]:
                p.update()
                if not p.active:
                    active_particles.remove(p)

            # افکت‌ها
            if screen_shake > 0:
                screen_shake -= 1
            if flash > 0:
                flash -= 8
            if level_banner_timer > 0:
                level_banner_timer -= 1

        # ============================================================
        #                    رسم
        # ============================================================
        game_surface.fill(DARK_BG)
        offset_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        offset_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0

        play_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            play_layer.blit(s, (0, y))

        # Maze
        power_mode = gs.power_timer > 0
        draw_maze(play_layer, gs.maze, power_mode, gs.power_timer)

        # میوه‌ها
        for f in fruits:
            f.draw(play_layer)

        # ارواح
        for g in ghosts:
            g.draw(play_layer, power_mode)

        # Pac-Man
        if pacman.alive or pacman.death_anim < 60:
            pacman.draw(play_layer)

        # ذرات
        for p in active_particles:
            p.draw(play_layer)

        if flash > 0:
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 200, 100, flash))
            play_layer.blit(fs, (0, 0))

        game_surface.blit(play_layer, (offset_x, offset_y))

        # ============================================================
        #                    HUD
        # ============================================================
        draw_text(game_surface, "NEON", 22, 25, 15, WHITE)
        draw_text(game_surface, "PAC-MAN", 22, 25 + get_font(22).size("NEON ")[0], 15, NEON_YELLOW, glow=True)
        draw_text(game_surface, "MOVE: Arrows or WASD | P: Pause | F11: Fullscreen",
                  11, 25, 45, (180, 200, 220))

        draw_text(game_surface, "SCORE", 14, WIDTH - 25, 12, NEON_CYAN)
        draw_text(game_surface, f"{gs.score}", 26, WIDTH - 25, 30, WHITE, glow=True)
        draw_text(game_surface, f"LEVEL: {gs.level}", 16, WIDTH - 25, 62, NEON_GREEN)
        draw_text(game_surface, f"PELLETS: {gs.pellets_left}", 14, WIDTH - 25, 84, NEON_YELLOW)

        # Combo
        if combo > 1 and gs.power_timer > 0:
            combo_color = NEON_GREEN if combo < 3 else NEON_YELLOW if combo < 4 else NEON_PINK
            scale = 1 + math.sin(t * 10) * 0.1
            draw_text(game_surface, f"x{combo} GHOST COMBO", int(28 * scale), WIDTH // 2, HEIGHT // 2 - 100,
                      combo_color, center=True, glow=True)

        # Power mode indicator
        if gs.power_timer > 0:
            power_alpha = min(255, gs.power_timer * 3)
            bar_w = 200
            bar_x = WIDTH // 2 - bar_w // 2
            bar_y = HEIGHT - 30
            pygame.draw.rect(game_surface, (40, 10, 40), (bar_x, bar_y, bar_w, 10))
            ratio = gs.power_timer / 420
            pygame.draw.rect(game_surface, NEON_PINK, (bar_x, bar_y, bar_w * ratio, 10))
            pygame.draw.rect(game_surface, WHITE, (bar_x, bar_y, bar_w, 10), 2)
            draw_text(game_surface, "POWER MODE!", 14, WIDTH // 2, bar_y - 20,
                      NEON_PINK, center=True, glow=True)

        # Banner
        if level_banner_timer > 0:
            size = 60 + int(math.sin(t * 10) * 5)
            draw_text(game_surface, f"LEVEL {gs.level}", size, WIDTH // 2, HEIGHT // 2 - 50,
                      NEON_CYAN, center=True, glow=True)
            draw_text(game_surface, "GET READY!", 30, WIDTH // 2, HEIGHT // 2 + 20,
                      WHITE, center=True)

        # Notifications
        for i, notif in enumerate(notifications):
            ny = 100 + i * 60
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
            box_w = 540
            box_h = 400
            box_x = WIDTH // 2 - box_w // 2
            box_y = HEIGHT // 2 - box_h // 2
            pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h))
            pygame.draw.rect(game_surface, NEON_PINK, (box_x, box_y, box_w, box_h), 3)
            pygame.draw.rect(game_surface, NEON_CYAN, (box_x + 5, box_y + 5, box_w - 10, box_h - 10), 1)
            draw_text(game_surface, "GAME OVER", 60, WIDTH // 2, box_y + 55,
                      NEON_RED, center=True, glow=True)
            draw_text(game_surface, f"SCORE: {final_score if final_score else gs.score}", 32,
                      WIDTH // 2, box_y + 120, WHITE, center=True)
            draw_text(game_surface, f"LEVEL: {gs.level}   GHOSTS: {total_ghosts[0]}",
                      16, WIDTH // 2, box_y + 160, NEON_CYAN, center=True)
            hs = highscore[0]
            if gs.score >= hs and gs.score > 0:
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