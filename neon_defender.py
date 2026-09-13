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

BASE_W, BASE_H = 1200, 750
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("NEON DEFENDER")
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

# --- ابعاد ---
GRID_SIZE = 50
GRID_COLS = 22
GRID_ROWS = 13
GRID_W = GRID_COLS * GRID_SIZE
GRID_H = GRID_ROWS * GRID_SIZE
GRID_X = (WIDTH - GRID_W) // 2
GRID_Y = 100

# --- ذخیره ---
SAVE_FILE = "neon_defender_save.json"
settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'difficulty': 1.0,
    'screen_shake': True,
    'auto_wave': False,
}
achievements = {
    'first_kill': {'name': 'FIRST BLOOD', 'desc': 'Kill your first enemy', 'unlocked': False, 'icon': '*'},
    'kill_10': {'name': 'ROOKIE', 'desc': 'Kill 10 enemies', 'unlocked': False, 'icon': '**'},
    'kill_100': {'name': 'VETERAN', 'desc': 'Kill 100 enemies', 'unlocked': False, 'icon': '***'},
    'kill_500': {'name': 'LEGEND', 'desc': 'Kill 500 enemies', 'unlocked': False, 'icon': '****'},
    'wave_5': {'name': 'EXPLORER', 'desc': 'Reach wave 5', 'unlocked': False, 'icon': 'W5'},
    'wave_10': {'name': 'DEFENDER', 'desc': 'Reach wave 10', 'unlocked': False, 'icon': 'W10'},
    'wave_20': {'name': 'CHAMPION', 'desc': 'Reach wave 20', 'unlocked': False, 'icon': 'W20'},
    'money_1000': {'name': 'RICH', 'desc': 'Earn 1000 money', 'unlocked': False, 'icon': '$'},
    'money_5000': {'name': 'MILLIONAIRE', 'desc': 'Earn 5000 money', 'unlocked': False, 'icon': '$$'},
    'all_towers': {'name': 'ARCHITECT', 'desc': 'Build all 5 tower types', 'unlocked': False, 'icon': '5T'},
    'upgrade_max': {'name': 'MAXED OUT', 'desc': 'Fully upgrade a tower', 'unlocked': False, 'icon': 'U3'},
    'boss_kill': {'name': 'BOSS SLAYER', 'desc': 'Kill a boss', 'unlocked': False, 'icon': 'B'},
    'no_leak': {'name': 'FLAWLESS', 'desc': 'Complete a wave without losing HP', 'unlocked': False, 'icon': 'P'},
    'combo_20': {'name': 'COMBO KING', 'desc': 'Kill 20 enemies in a row', 'unlocked': False, 'icon': 'C20'},
    'score_50000': {'name': 'GRANDMASTER', 'desc': 'Score 50000', 'unlocked': False, 'icon': 'GM'},
}
highscore = [0]
game_history = []
total_kills = [0]
total_waves = [0]
total_bosses = [0]


def load_save():
    global settings, achievements, highscore, game_history, total_kills, total_waves, total_bosses
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
            settings.update(data.get('settings', {}))
            for k, v in data.get('achievements', {}).items():
                if k in achievements:
                    achievements[k]['unlocked'] = v
            highscore[0] = data.get('highscore', 0)
            game_history = data.get('game_history', [])
            total_kills[0] = data.get('total_kills', 0)
            total_waves[0] = data.get('total_waves', 0)
            total_bosses[0] = data.get('total_bosses', 0)
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
                'total_kills': total_kills[0],
                'total_waves': total_waves[0],
                'total_bosses': total_bosses[0],
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


def add_game_to_history(score, wave, duration, new_achs):
    entry = {
        'score': score,
        'wave': wave,
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
    sounds['build'] = make_sound(400, 800, 0.15, 0.20, 'sine')
    sounds['sell'] = make_sound(800, 400, 0.15, 0.18, 'sine')
    sounds['upgrade'] = make_sound(600, 1200, 0.25, 0.22, 'sine')
    sounds['shoot'] = make_sound(1200, 900, 0.04, 0.08, 'square')
    sounds['explode'] = make_sound(300, 50, 0.3, 0.25, 'noise')
    sounds['kill'] = make_sound(800, 400, 0.1, 0.15, 'square')
    sounds['wave_start'] = make_sound(300, 800, 0.5, 0.28, 'saw')
    sounds['wave_clear'] = make_sound(600, 1500, 0.6, 0.28, 'sine')
    sounds['damage'] = make_sound(200, 60, 0.4, 0.30, 'noise')
    sounds['gameover'] = make_sound(500, 60, 1.5, 0.30, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['boss'] = make_sound(150, 400, 1.0, 0.28, 'saw')

    bass = [73.4, 73.4, 82.4, 82.4, 65.4, 65.4, 73.4, 73.4]
    lead = [523, 587, 659, 587, 523, 494, 440, 494]
    music_sound[0] = make_music_loop(bass, lead, 0.22, 0.10)
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

    def spawn(self, x, y, color, speed_mult=1.0, size_mult=1.0, life_mult=1.0, gravity=0.15):
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


def spawn_particles(x, y, color, count, speed_mult=1.0, size_mult=1.0, life_mult=1.0, gravity=0.15):
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
#                    نقشه و مسیر
# ============================================================
# مسیر S-شکل از بالا به پایین
# هر سلول توی لیست path = مسیر دشمن
PATH_CELLS = [
    # از بالا وارد
    (2, 0), (2, 1), (2, 2), (2, 3),
    # راست
    (3, 3), (4, 3), (5, 3), (6, 3), (7, 3),
    # پایین
    (7, 4), (7, 5),
    # چپ
    (6, 5), (5, 5), (4, 5), (3, 5), (2, 5),
    # پایین
    (2, 6), (2, 7),
    # راست
    (3, 7), (4, 7), (5, 7), (6, 7), (7, 7), (8, 7), (9, 7), (10, 7),
    # پایین
    (10, 8), (10, 9),
    # چپ
    (9, 9), (8, 9), (7, 9), (6, 9), (5, 9), (4, 9), (3, 9),
    # پایین
    (3, 10), (3, 11), (3, 12),
    # راست به سمت Base
    (4, 12), (5, 12), (6, 12), (7, 12), (8, 12), (9, 12),
    (10, 12), (11, 12), (12, 12), (13, 12), (14, 12), (15, 12),
    (16, 12), (17, 12), (18, 12), (19, 12),
]

# مسیر دوم برای دشمن‌های پرنده (مستقیم)
PATH_CELLS_FLYER = [
    (2, 0), (4, 1), (6, 2), (8, 3), (10, 4),
    (12, 5), (14, 6), (16, 7), (18, 8), (19, 10),
    (18, 12),
]

PATH_SET = set(PATH_CELLS)
PATH_FLYER_SET = set(PATH_CELLS_FLYER)

# نقاط ساخت برج (کنار مسیر، نه روی اون)
BUILD_SLOTS = []
for gy in range(GRID_ROWS):
    for gx in range(GRID_COLS):
        if (gx, gy) not in PATH_SET and (gx, gy) not in PATH_FLYER_SET:
            # چک کن حداقل یک همسایه مسیر داشته باشه
            has_path_neighbor = False
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                if (gx + dx, gy + dy) in PATH_SET:
                    has_path_neighbor = True
                    break
            if has_path_neighbor:
                BUILD_SLOTS.append((gx, gy))

# --- انواع برج ---
TOWER_TYPES = {
    'gatling': {
        'name': 'GATLING',
        'color': NEON_ORANGE,
        'cost': 50,
        'damage': 8,
        'range': 120,
        'fire_rate': 8,
        'upgrade_cost': 60,
        'upgrade_damage': 6,
        'upgrade_range': 15,
        'icon': 'G',
        'desc': 'Fast fire rate',
    },
    'missile': {
        'name': 'MISSILE',
        'color': NEON_RED,
        'cost': 100,
        'damage': 40,
        'range': 160,
        'fire_rate': 60,
        'upgrade_cost': 120,
        'upgrade_damage': 25,
        'upgrade_range': 20,
        'icon': 'M',
        'desc': 'Splash damage',
        'splash': 60,
    },
    'tesla': {
        'name': 'TESLA',
        'color': NEON_CYAN,
        'cost': 150,
        'damage': 25,
        'range': 140,
        'fire_rate': 40,
        'upgrade_cost': 180,
        'upgrade_damage': 15,
        'upgrade_range': 20,
        'icon': 'T',
        'desc': 'Chain lightning',
        'chain': 3,
    },
    'slow': {
        'name': 'SLOW',
        'color': NEON_BLUE,
        'cost': 75,
        'damage': 5,
        'range': 130,
        'fire_rate': 30,
        'upgrade_cost': 90,
        'upgrade_damage': 3,
        'upgrade_range': 20,
        'icon': 'S',
        'desc': 'Slows enemies',
        'slow_amount': 0.5,
        'slow_duration': 90,
    },
    'laser': {
        'name': 'LASER',
        'color': NEON_PURPLE,
        'cost': 200,
        'damage': 60,
        'range': 180,
        'fire_rate': 50,
        'upgrade_cost': 220,
        'upgrade_damage': 40,
        'upgrade_range': 25,
        'icon': 'L',
        'desc': 'Pierce through',
        'pierce': True,
    },
}

# --- انواع دشمن ---
ENEMY_TYPES = {
    'grunt': {
        'name': 'GRUNT',
        'color': NEON_GREEN,
        'hp': 40,
        'speed': 1.0,
        'reward': 10,
        'damage': 1,
        'size': 12,
    },
    'runner': {
        'name': 'RUNNER',
        'color': NEON_YELLOW,
        'hp': 25,
        'speed': 2.2,
        'reward': 15,
        'damage': 1,
        'size': 10,
    },
    'brute': {
        'name': 'BRUTE',
        'color': NEON_RED,
        'hp': 150,
        'speed': 0.6,
        'reward': 25,
        'damage': 3,
        'size': 18,
    },
    'flyer': {
        'name': 'FLYER',
        'color': NEON_MAGENTA,
        'hp': 60,
        'speed': 1.5,
        'reward': 20,
        'damage': 2,
        'size': 14,
        'flying': True,
    },
    'boss': {
        'name': 'BOSS',
        'color': NEON_PINK,
        'hp': 800,
        'speed': 0.5,
        'reward': 200,
        'damage': 10,
        'size': 30,
    },
}


# ============================================================
#                    Towers
# ============================================================
class Tower:
    def __init__(self, gx, gy, tower_type):
        self.gx = gx
        self.gy = gy
        self.x = GRID_X + gx * GRID_SIZE + GRID_SIZE / 2
        self.y = GRID_Y + gy * GRID_SIZE + GRID_SIZE / 2
        self.tower_type = tower_type
        self.stats = TOWER_TYPES[tower_type].copy()
        self.level = 1
        self.max_level = 3
        self.cooldown = 0
        self.angle = 0
        self.target = None
        self.muzzle_flash = 0
        self.total_invested = self.stats['cost']

    def get_damage(self):
        return self.stats['damage'] + (self.level - 1) * self.stats['upgrade_damage']

    def get_range(self):
        return self.stats['range'] + (self.level - 1) * self.stats['upgrade_range']

    def get_fire_rate(self):
        base = self.stats['fire_rate']
        return max(3, base - (self.level - 1) * 3)

    def get_upgrade_cost(self):
        if self.level >= self.max_level:
            return None
        return int(self.stats['upgrade_cost'] * (1 + (self.level - 1) * 0.5))

    def sell_value(self):
        return int(self.total_invested * 0.7)

    def upgrade(self):
        if self.level >= self.max_level:
            return False
        cost = self.get_upgrade_cost()
        if cost is None:
            return False
        self.level += 1
        self.total_invested += cost
        return True

    def find_target(self, enemies):
        """پیدا کردن بهترین دشمن (نزدیک‌ترین به Base که توی برد باشه)"""
        best = None
        best_dist = -1
        for e in enemies:
            if not e.alive:
                continue
            dist = math.hypot(e.x - self.x, e.y - self.y)
            if dist <= self.get_range():
                # پیشرفته‌ترین دشمن = بیشترین مسیر رفته
                progress = e.path_index
                if progress > best_dist:
                    best_dist = progress
                    best = e
        return best

    def update(self, enemies, all_towers, projectiles):
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.muzzle_flash > 0:
            self.muzzle_flash -= 1

        self.target = self.find_target(enemies)
        if self.target:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            self.angle = math.degrees(math.atan2(dy, dx))

            if self.cooldown <= 0:
                self.shoot(enemies, projectiles)
                self.cooldown = self.get_fire_rate()

    def shoot(self, enemies, projectiles):
        if not self.target:
            return
        self.muzzle_flash = 5
        play_sound('shoot')

        if self.tower_type == 'gatling':
            # تیر سریع
            projectiles.append(Projectile(
                self.x, self.y, self.target,
                self.get_damage(), self.stats['color'],
                speed=15, type='bullet'
            ))

        elif self.tower_type == 'missile':
            # موشک انفجاری
            projectiles.append(Projectile(
                self.x, self.y, self.target,
                self.get_damage(), self.stats['color'],
                speed=8, type='missile',
                splash=self.stats.get('splash', 60)
            ))

        elif self.tower_type == 'tesla':
            # زنجیره برق
            chain_count = self.stats.get('chain', 3)
            # پیدا کردن دشمن‌های نزدیک
            targets = [self.target]
            for e in enemies:
                if e == self.target or not e.alive:
                    continue
                if len(targets) >= chain_count:
                    break
                dist = math.hypot(e.x - self.target.x, e.y - self.target.y)
                if dist < 100:
                    targets.append(e)

            for i, e in enumerate(targets):
                damage = self.get_damage() * (1 - i * 0.2)
                e.take_damage(damage)
                # افکت ذرات
                for _ in range(5):
                    spawn_particles(e.x, e.y, NEON_CYAN, 1, 1.5, 1.0, 0.8)

        elif self.tower_type == 'slow':
            # کند کردن
            self.target.slow_timer = self.stats.get('slow_duration', 90)
            self.target.slow_amount = self.stats.get('slow_amount', 0.5)
            self.target.take_damage(self.get_damage())
            for _ in range(5):
                spawn_particles(self.target.x, self.target.y, NEON_BLUE, 1, 1.0, 1.0, 0.5)

        elif self.tower_type == 'laser':
            # لیزر Pierce
            # همه دشمن‌های توی خط رو بزن
            rad = math.radians(self.angle)
            for e in enemies:
                if not e.alive:
                    continue
                dx = e.x - self.x
                dy = e.y - self.y
                dist = math.hypot(dx, dy)
                if dist > self.get_range():
                    continue
                # چک زاویه
                e_angle = math.degrees(math.atan2(dy, dx))
                angle_diff = abs((e_angle - self.angle + 180) % 360 - 180)
                if angle_diff < 15:
                    e.take_damage(self.get_damage())
                    for _ in range(5):
                        spawn_particles(e.x, e.y, NEON_PURPLE, 1, 1.5, 1.0, 0.8)

    def draw(self, surface, selected=False, hovering=False):
        color = self.stats['color']
        r = GRID_SIZE * 0.4

        # هاله
        if self.muzzle_flash > 0:
            for hr in range(3, 0, -1):
                glow = pygame.Surface((GRID_SIZE * 2, GRID_SIZE * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*WHITE, 100),
                                   (GRID_SIZE, GRID_SIZE), GRID_SIZE - hr * 4)
                surface.blit(glow, (self.x - GRID_SIZE, self.y - GRID_SIZE))

        for hr in range(3, 0, -1):
            glow_size = int(r * 2 + hr * 10)
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 40 - hr * 10),
                               (glow_size // 2, glow_size // 2), glow_size // 2)
            surface.blit(glow, (self.x - glow_size // 2, self.y - glow_size // 2))

        # پایه
        base_rect = pygame.Rect(int(self.x - r), int(self.y - r), int(r * 2), int(r * 2))
        pygame.draw.rect(surface, (color[0] // 4, color[1] // 4, color[2] // 4),
                         base_rect, border_radius=6)
        pygame.draw.rect(surface, color, base_rect, 3, border_radius=6)

        # تفنگ
        rad = math.radians(self.angle)
        gun_end_x = self.x + math.cos(rad) * r * 1.2
        gun_end_y = self.y + math.sin(rad) * r * 1.2
        pygame.draw.line(surface, color, (self.x, self.y), (gun_end_x, gun_end_y), 6)
        pygame.draw.circle(surface, WHITE, (int(gun_end_x), int(gun_end_y)), 3)

        # آیکون
        icon = self.stats.get('icon', '?')
        draw_text(surface, icon, 14, self.x, self.y - 8, WHITE, center=True, bold=True)

        # سطح
        if self.level > 1:
            for i in range(self.level - 1):
                pygame.draw.circle(surface, NEON_YELLOW,
                                   (int(self.x - 10 + i * 10), int(self.y + r + 6)), 3)

        # شعاع برد اگه انتخاب شده
        if selected:
            range_surf = pygame.Surface((self.get_range() * 2, self.get_range() * 2), pygame.SRCALPHA)
            pygame.draw.circle(range_surf, (*color, 30),
                               (self.get_range(), self.get_range()), self.get_range())
            pygame.draw.circle(range_surf, (*color, 80),
                               (self.get_range(), self.get_range()), self.get_range(), 2)
            surface.blit(range_surf, (self.x - self.get_range(), self.y - self.get_range()))


# ============================================================
#                    Projectile
# ============================================================
class Projectile:
    def __init__(self, x, y, target, damage, color, speed=10, type='bullet', splash=0):
        self.x = x
        self.y = y
        self.target = target
        self.damage = damage
        self.color = color
        self.speed = speed
        self.type = type
        self.splash = splash
        self.alive = True
        self.trail = []

    def update(self):
        if not self.target or not self.target.alive:
            self.alive = False
            return

        self.trail.append((self.x, self.y))
        if len(self.trail) > 6:
            self.trail.pop(0)

        # حرکت به سمت هدف
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)

        if dist < self.speed:
            # برخورد
            self.on_hit()
            self.alive = False
            return

        self.x += dx / dist * self.speed
        self.y += dy / dist * self.speed

    def on_hit(self):
        if self.type == 'missile':
            # انفجار
            play_sound('explode')
            # آسیب به دشمن اصلی
            if self.target and self.target.alive:
                self.target.take_damage(self.damage)
            # آسیب شعاعی
            for _ in range(30):
                spawn_particles(self.x, self.y, NEON_ORANGE, 1, 2.0, 1.5, 1.3)
        else:
            if self.target and self.target.alive:
                self.target.take_damage(self.damage)

    def draw(self, surface):
        # Trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / len(self.trail) * 0.7
            r = max(1, int(3 * alpha))
            c = tuple(int(c1 * alpha) for c1 in self.color)
            pygame.draw.circle(surface, c, (int(tx), int(ty)), r)

        # بدنه
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 4)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 2)


# ============================================================
#                    Enemy
# ============================================================
class Enemy:
    def __init__(self, enemy_type, wave_num):
        self.enemy_type = enemy_type
        self.stats = ENEMY_TYPES[enemy_type].copy()
        self.max_hp = self.stats['hp'] + wave_num * 5
        self.hp = self.max_hp
        self.speed = self.stats['speed']
        self.base_speed = self.speed
        self.reward = self.stats['reward']
        self.damage = self.stats['damage']
        self.color = self.stats['color']
        self.size = self.stats['size']
        self.flying = self.stats.get('flying', False)

        # انتخاب مسیر
        if self.flying:
            self.path = PATH_CELLS_FLYER
        else:
            self.path = PATH_CELLS

        self.path_index = 0
        self.x = GRID_X + self.path[0][0] * GRID_SIZE + GRID_SIZE / 2
        self.y = GRID_Y + self.path[0][1] * GRID_SIZE + GRID_SIZE / 2
        self.alive = True
        self.hit_flash = 0
        self.slow_timer = 0
        self.slow_amount = 1.0
        self.reached_end = False
        self.anim_time = 0

    def update(self):
        if not self.alive:
            return

        if self.hit_flash > 0:
            self.hit_flash -= 1
        if self.slow_timer > 0:
            self.slow_timer -= 1
        self.anim_time += 0.15

        # سرعت با slow
        speed_mult = self.slow_amount if self.slow_timer > 0 else 1.0
        actual_speed = self.speed * speed_mult

        # حرکت به سمت نقطه بعدی مسیر
        if self.path_index >= len(self.path) - 1:
            # به آخر رسید
            self.reached_end = True
            self.alive = False
            return

        target_gx, target_gy = self.path[self.path_index + 1]
        target_x = GRID_X + target_gx * GRID_SIZE + GRID_SIZE / 2
        target_y = GRID_Y + target_gy * GRID_SIZE + GRID_SIZE / 2

        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)

        if dist < actual_speed:
            self.x = target_x
            self.y = target_y
            self.path_index += 1
        else:
            self.x += dx / dist * actual_speed
            self.y += dy / dist * actual_speed

    def take_damage(self, amount):
        self.hp -= amount
        self.hit_flash = 5
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surface):
        if not self.alive:
            return

        color = WHITE if self.hit_flash > 0 else self.color

        # هاله
        for hr in range(3, 0, -1):
            glow_size = self.size * 2 + hr * 8
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 60 - hr * 15),
                               (glow_size // 2, glow_size // 2), glow_size // 2)
            surface.blit(glow, (self.x - glow_size // 2, self.y - glow_size // 2))

        # بدنه
        if self.flying:
            # پرنده - شکل لوزی
            pts = [
                (self.x, self.y - self.size),
                (self.x + self.size, self.y),
                (self.x, self.y + self.size),
                (self.x - self.size, self.y),
            ]
            pygame.draw.polygon(surface, color, pts)
            pygame.draw.polygon(surface, WHITE, pts, 2)
            # بال‌ها
            flap = math.sin(self.anim_time * 3) * 5
            pygame.draw.line(surface, color,
                             (self.x - self.size, self.y),
                             (self.x - self.size - 8, self.y - flap), 3)
            pygame.draw.line(surface, color,
                             (self.x + self.size, self.y),
                             (self.x + self.size + 8, self.y - flap), 3)
        else:
            # دشمن زمینی
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.size)
            pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.size, 2)
            # چشم‌ها
            eye_y = self.y - 3
            if self.hp > self.max_hp * 0.3:
                pygame.draw.circle(surface, WHITE, (int(self.x - 4), int(eye_y)), 2)
                pygame.draw.circle(surface, WHITE, (int(self.x + 4), int(eye_y)), 2)
            else:
                # چشم خسته
                pygame.draw.line(surface, WHITE, (self.x - 6, eye_y), (self.x - 2, eye_y), 1)
                pygame.draw.line(surface, WHITE, (self.x + 2, eye_y), (self.x + 6, eye_y), 1)

        # نوار HP
        bar_w = self.size * 2
        bar_h = 4
        bar_x = self.x - bar_w / 2
        bar_y = self.y - self.size - 10
        pygame.draw.rect(surface, (40, 10, 10), (bar_x, bar_y, bar_w, bar_h))
        ratio = self.hp / self.max_hp
        hp_color = NEON_GREEN if ratio > 0.5 else NEON_YELLOW if ratio > 0.25 else NEON_RED
        pygame.draw.rect(surface, hp_color, (bar_x, bar_y, bar_w * ratio, bar_h))
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, bar_h), 1)

        # آیکون slow
        if self.slow_timer > 0:
            pygame.draw.circle(surface, NEON_BLUE, (int(self.x), int(self.y - self.size - 18)), 4)


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
#                    Menu
# ============================================================
def show_menu():
    menu_time = 0
    btn_start = Button(WIDTH // 2, HEIGHT // 2 + 30, 320, 55, "START GAME", NEON_CYAN, NEON_GREEN, 28)
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

        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            game_surface.blit(s, (0, y))

        # ذرات تزئینی
        for _ in range(50):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            b = random.randint(50, 150)
            pygame.draw.circle(game_surface, (b, b, b + 40), (x, y), 1)

        # عنوان
        title_y = 130 + math.sin(t * 2) * 8
        draw_text(game_surface, "NEON", 72, WIDTH // 2 - 100, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "DEFENDER", 72, WIDTH // 2 + 130, title_y, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, "BUILD  /  DEFEND  /  SURVIVE", 20, WIDTH // 2, title_y + 65,
                  (200, 200, 220), center=True)

        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 22, WIDTH // 2, title_y + 115,
                      NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, f"KILLS: {total_kills[0]}   WAVES: {total_waves[0]}   BOSSES: {total_bosses[0]}",
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
    slider_sfx = Slider(WIDTH // 2, 180, 400, 12, settings['sfx_volume'], 0, 1, "SFX Volume")
    slider_music = Slider(WIDTH // 2, 270, 400, 12, settings['music_volume'], 0, 1, "Music Volume")
    slider_diff = Slider(WIDTH // 2, 360, 400, 12, (settings['difficulty'] - 0.5) / 1.0, 0, 1, "Difficulty")
    btn_auto = Button(WIDTH // 2, 450, 280, 55,
                      f"AUTO WAVE: {'ON' if settings['auto_wave'] else 'OFF'}",
                      NEON_GREEN if settings['auto_wave'] else (100, 100, 100), NEON_CYAN, 22)
    btn_shake = Button(WIDTH // 2, 515, 280, 55,
                       f"SHAKE: {'ON' if settings['screen_shake'] else 'OFF'}",
                       NEON_GREEN if settings['screen_shake'] else (100, 100, 100), NEON_CYAN, 22)
    btn_reset = Button(WIDTH // 2 - 130, 595, 220, 50, "RESET SAVE", NEON_RED, NEON_ORANGE, 20)
    btn_back = Button(WIDTH // 2 + 130, 595, 220, 50, "BACK", NEON_CYAN, NEON_GREEN, 22)

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
        box_h = 680
        box_x = WIDTH // 2 - box_w // 2
        box_y = HEIGHT // 2 - box_h // 2 + 20
        pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h), border_radius=12)
        pygame.draw.rect(game_surface, NEON_PURPLE, (box_x, box_y, box_w, box_h), 3, border_radius=12)

        draw_text(game_surface, "SETTINGS", 48, WIDTH // 2, 70, NEON_CYAN, center=True, glow=True)

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
        draw_text(game_surface, diff_label, 20, WIDTH // 2, 390, diff_color, center=True)

        btn_auto.update(mouse_pos)
        btn_auto.text = f"AUTO WAVE: {'ON' if settings['auto_wave'] else 'OFF'}"
        btn_auto.color = NEON_GREEN if settings['auto_wave'] else (100, 100, 100)
        btn_auto.draw(game_surface)

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
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                toggle_fullscreen()
            if btn_auto.is_clicked(event):
                settings['auto_wave'] = not settings['auto_wave']
                save_async()
            if btn_shake.is_clicked(event):
                settings['screen_shake'] = not settings['screen_shake']
                save_async()
            if btn_reset.is_clicked(event):
                settings['sfx_volume'] = 0.7
                settings['music_volume'] = 0.5
                settings['difficulty'] = 1.0
                settings['screen_shake'] = True
                settings['auto_wave'] = False
                for k in achievements:
                    achievements[k]['unlocked'] = False
                highscore[0] = 0
                game_history.clear()
                total_kills[0] = 0
                total_waves[0] = 0
                total_bosses[0] = 0
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
        card_h = 38
        for key, a in achievements.items():
            cx = WIDTH // 2 - card_w // 2
            color = NEON_GREEN if a['unlocked'] else (60, 60, 80)
            pygame.draw.rect(game_surface, (10, 5, 25), (cx, y_pos, card_w, card_h), border_radius=8)
            pygame.draw.rect(game_surface, color, (cx, y_pos, card_w, card_h), 2, border_radius=8)
            icon_color = NEON_YELLOW if a['unlocked'] else (80, 80, 80)
            draw_text(game_surface, a['icon'], 14, cx + 35, y_pos + card_h // 2, icon_color, center=True)
            name_color = NEON_YELLOW if a['unlocked'] else (120, 120, 120)
            draw_text(game_surface, a['name'], 15, cx + 70, y_pos + 5, name_color)
            draw_text(game_surface, a['desc'], 11, cx + 70, y_pos + 22, (150, 150, 180))
            status = "[OK]" if a['unlocked'] else "[--]"
            sc = NEON_GREEN if a['unlocked'] else (100, 100, 100)
            draw_text(game_surface, status, 13, cx + card_w - 50, y_pos + card_h // 2, sc, center=True)
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
                draw_text(game_surface, f"WAVE: {entry.get('wave', 1)}   TIME: {entry.get('duration', 0)}s",
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
    towers = []
    enemies = []
    projectiles = []

    money = 300
    score = 0
    display_score = 0
    base_hp = 20
    max_base_hp = 20
    wave = 0
    wave_active = False
    wave_banner_timer = 0
    enemies_to_spawn = deque()
    spawn_timer = 0
    spawn_interval = 40
    intermission_timer = 0
    in_intermission = False

    # انتخاب برج
    selected_type = None
    selected_tower = None
    placing = False
    mouse_tile = None

    # آمار
    total_frames = 0
    kills_this_wave = 0
    combo = 0
    combo_timer = 0
    max_combo = 0
    wave_no_leak = True
    built_types = set()

    # افکت‌ها
    screen_shake = 0
    flash = 0
    game_over = False
    paused = False
    final_score = 0
    final_wave = 0
    new_achs = []
    notifications = []
    go_anim = 0
    game_saved = False

    # دکمه‌ها
    btn_resume = Button(WIDTH // 2, HEIGHT // 2 + 20, 300, 60, "RESUME", NEON_GREEN, NEON_CYAN, 28)
    btn_pause_menu = Button(WIDTH // 2, HEIGHT // 2 + 100, 300, 55, "MAIN MENU", NEON_RED, NEON_ORANGE, 24)
    btn_restart = Button(WIDTH // 2, HEIGHT // 2 + 70, 300, 60, "RESTART", NEON_CYAN, NEON_GREEN, 28)
    btn_menu = Button(WIDTH // 2, HEIGHT // 2 + 145, 300, 55, "MAIN MENU", NEON_YELLOW, NEON_ORANGE, 24)
    btn_start_wave = Button(GRID_X + GRID_W // 2, GRID_Y + GRID_H + 60, 260, 55,
                            "START WAVE", NEON_GREEN, NEON_CYAN, 24)
    btn_sell = Button(GRID_X + 200, GRID_Y + GRID_H + 60, 200, 50,
                      "SELL", NEON_RED, NEON_ORANGE, 22)
    btn_upgrade = Button(GRID_X + 420, GRID_Y + GRID_H + 60, 200, 50,
                         "UPGRADE", NEON_YELLOW, NEON_GREEN, 22)

    # دکمه‌های برج
    tower_buttons = []
    bx = 20
    for t_type, t_data in TOWER_TYPES.items():
        btn = Button(bx + 60, 55, 110, 80, t_data['icon'], t_data['color'], WHITE, 32)
        tower_buttons.append((t_type, btn, t_data))
        bx += 120

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
        add_game_to_history(score, wave, total_frames // FPS, new_achs)

    def start_wave():
        nonlocal wave, wave_active, enemies_to_spawn, in_intermission, kills_this_wave, wave_no_leak
        wave += 1
        wave_active = True
        in_intermission = False
        kills_this_wave = 0
        wave_no_leak = True

        # تعداد دشمن‌ها بر اساس wave
        count = 5 + wave * 2
        # اگه مضرب 5 بود، باس اضافه کن
        is_boss_wave = (wave % 5 == 0)

        # ساخت لیست دشمن‌ها
        spawn_list = []
        for i in range(count):
            # انتخاب نوع
            choices = ['grunt'] * 5
            if wave >= 2:
                choices += ['runner'] * 3
            if wave >= 3:
                choices += ['brute'] * 2
            if wave >= 4:
                choices += ['flyer'] * 2
            spawn_list.append(random.choice(choices))

        if is_boss_wave:
            spawn_list.append('boss')
            play_sound('boss')
            flash = 100

        random.shuffle(spawn_list)
        enemies_to_spawn = deque(spawn_list)
        play_sound('wave_start')
        wave_banner_timer = 120

    def spawn_enemy():
        nonlocal enemies_to_spawn
        if not enemies_to_spawn:
            return
        e_type = enemies_to_spawn.popleft()
        enemies.append(Enemy(e_type, wave))

    def on_enemy_killed(enemy):
        nonlocal score, money, kills_this_wave, combo, combo_timer, max_combo
        combo += 1
        combo_timer = 120
        max_combo = max(max_combo, combo)

        # امتیاز و پول
        points = enemy.reward * (1 + combo * 0.05)
        score += int(points)
        money += enemy.reward
        kills_this_wave += 1
        total_kills[0] += 1

        if enemy.enemy_type == 'boss':
            total_bosses[0] += 1
            try_unlock('boss_kill')
            if settings['screen_shake']:
                screen_shake = 30
            flash = 200

        play_sound('kill')
        for _ in range(15):
            spawn_particles(enemy.x, enemy.y, enemy.color, 1, 1.5, 1.2, 1.0)

        if total_kills[0] >= 1: try_unlock('first_kill')
        if total_kills[0] >= 10: try_unlock('kill_10')
        if total_kills[0] >= 100: try_unlock('kill_100')
        if total_kills[0] >= 500: try_unlock('kill_500')
        if money >= 1000: try_unlock('money_1000')
        if money >= 5000: try_unlock('money_5000')
        if combo >= 20: try_unlock('combo_20')
        if score >= 50000: try_unlock('score_50000')

    running = True
    while running:
        clock.tick(FPS)
        t = pygame.time.get_ticks() / 1000
        mouse_pos = get_game_mouse_pos()

        # موقعیت ماوس توی grid
        mouse_gx = int((mouse_pos[0] - GRID_X) // GRID_SIZE)
        mouse_gy = int((mouse_pos[1] - GRID_Y) // GRID_SIZE)
        mouse_tile = (mouse_gx, mouse_gy)

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
                # کنسل انتخاب
                if event.key == pygame.K_x:
                    selected_type = None
                    selected_tower = None
                    placing = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if paused or game_over:
                    continue

                # چک کلیک روی دکمه برج
                clicked_tower_btn = False
                for t_type, btn, t_data in tower_buttons:
                    if btn.rect.collidepoint(mouse_pos):
                        if money >= t_data['cost']:
                            selected_type = t_type
                            selected_tower = None
                            placing = True
                        clicked_tower_btn = True
                        break

                if clicked_tower_btn:
                    continue

                # چک کلیک روی Start Wave
                if btn_start_wave.rect.collidepoint(mouse_pos) and not wave_active:
                    start_wave()
                    continue

                # چک کلیک روی Sell
                if selected_tower and btn_sell.rect.collidepoint(mouse_pos):
                    money += selected_tower.sell_value()
                    for _ in range(15):
                        spawn_particles(selected_tower.x, selected_tower.y, selected_tower.stats['color'], 1, 1.5)
                    towers.remove(selected_tower)
                    selected_tower = None
                    play_sound('sell')
                    continue

                # چک کلیک روی Upgrade
                if selected_tower and btn_upgrade.rect.collidepoint(mouse_pos):
                    cost = selected_tower.get_upgrade_cost()
                    if cost is not None and money >= cost:
                        money -= cost
                        selected_tower.upgrade()
                        play_sound('upgrade')
                        if selected_tower.level >= selected_tower.max_level:
                            try_unlock('upgrade_max')
                    continue

                # کلیک روی یه سلول
                if 0 <= mouse_gx < GRID_COLS and 0 <= mouse_gy < GRID_ROWS:
                    # چک کن روی برج موجوده
                    clicked_tower = None
                    for tower in towers:
                        if tower.gx == mouse_gx and tower.gy == mouse_gy:
                            clicked_tower = tower
                            break

                    if clicked_tower:
                        selected_tower = clicked_tower
                        selected_type = None
                        placing = False
                    elif placing and selected_type and (mouse_gx, mouse_gy) in BUILD_SLOTS:
                        # چک کن اینجا برج نیست
                        occupied = any(t.gx == mouse_gx and t.gy == mouse_gy for t in towers)
                        if not occupied:
                            cost = TOWER_TYPES[selected_type]['cost']
                            if money >= cost:
                                money -= cost
                                new_tower = Tower(mouse_gx, mouse_gy, selected_type)
                                towers.append(new_tower)
                                built_types.add(selected_type)
                                play_sound('build')
                                if len(built_types) >= 5:
                                    try_unlock('all_towers')
                                for _ in range(15):
                                    spawn_particles(new_tower.x, new_tower.y,
                                                    new_tower.stats['color'], 1, 1.5)
                                selected_type = None
                                placing = False
                    else:
                        selected_tower = None
                        if not placing:
                            selected_type = None

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

            if combo_timer > 0:
                combo_timer -= 1
                if combo_timer == 0:
                    combo = 0

            # اسپاون دشمن
            if wave_active and enemies_to_spawn:
                spawn_timer += 1
                if spawn_timer >= spawn_interval:
                    spawn_timer = 0
                    spawn_enemy()

            # آپدیت دشمن‌ها
            for e in enemies[:]:
                e.update()
                if not e.alive:
                    if e.reached_end:
                        base_hp -= e.damage
                        wave_no_leak = False
                        play_sound('damage')
                        if settings['screen_shake']:
                            screen_shake = 15
                        flash = 100
                        if base_hp <= 0:
                            game_over = True
                            final_score = score
                            final_wave = wave
                            highscore[0] = max(highscore[0], score)
                            save_current()
                            game_saved = True
                            play_sound('gameover')
                            go_anim = 0
                    else:
                        on_enemy_killed(e)
                    enemies.remove(e)

            # آپدیت برج‌ها
            for tower in towers:
                tower.update(enemies, towers, projectiles)

            # آپدیت پرتابه‌ها
            for p in projectiles[:]:
                p.update()
                if not p.alive:
                    projectiles.remove(p)

            # چک پایان wave
            if wave_active and not enemies_to_spawn and len(enemies) == 0:
                wave_active = False
                in_intermission = True
                intermission_timer = 180
                # پاداش پایان wave
                bonus = 50 + wave * 10
                money += bonus
                score += bonus
                play_sound('wave_clear')
                total_waves[0] += 1
                if wave_no_leak:
                    try_unlock('no_leak')
                if wave >= 5: try_unlock('wave_5')
                if wave >= 10: try_unlock('wave_10')
                if wave >= 20: try_unlock('wave_20')

            if in_intermission:
                intermission_timer -= 1
                if intermission_timer <= 0:
                    in_intermission = False
                    if settings['auto_wave']:
                        start_wave()

            # آپدیت ذرات
            for p in active_particles[:]:
                p.update()
                if not p.active:
                    active_particles.remove(p)

            if screen_shake > 0:
                screen_shake -= 1
            if flash > 0:
                flash -= 8
            if wave_banner_timer > 0:
                wave_banner_timer -= 1

        # ============================================================
        #                    رسم
        # ============================================================
        game_surface.fill(DARK_BG)
        offset_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        offset_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0

        play_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # پس‌زمینه
        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            play_layer.blit(s, (0, y))

        # Grid
        for gy in range(GRID_ROWS):
            for gx in range(GRID_COLS):
                px = GRID_X + gx * GRID_SIZE
                py = GRID_Y + gy * GRID_SIZE

                is_path = (gx, gy) in PATH_SET
                is_flyer_path = (gx, gy) in PATH_FLYER_SET
                is_slot = (gx, gy) in BUILD_SLOTS

                if is_path:
                    # مسیر اصلی
                    rect = pygame.Rect(px, py, GRID_SIZE, GRID_SIZE)
                    pygame.draw.rect(play_layer, (20, 30, 40), rect)
                    pygame.draw.rect(play_layer, NEON_CYAN, rect, 1)
                elif is_flyer_path:
                    # مسیر پرنده‌ها (نقطه‌چین)
                    rect = pygame.Rect(px, py, GRID_SIZE, GRID_SIZE)
                    pygame.draw.rect(play_layer, (25, 15, 40), rect)
                    for i in range(2, GRID_SIZE, 8):
                        pygame.draw.circle(play_layer, NEON_MAGENTA, (px + i, py + i), 2)
                elif is_slot:
                    # نقطه ساخت
                    rect = pygame.Rect(px + 4, py + 4, GRID_SIZE - 8, GRID_SIZE - 8)
                    # اگه برج هست، نذار
                    has_tower = any(t.gx == gx and t.gy == gy for t in towers)
                    if not has_tower:
                        pygame.draw.rect(play_layer, (40, 40, 60), rect, border_radius=6)
                        pygame.draw.rect(play_layer, (80, 80, 120), rect, 1, border_radius=6)

        # هاله دور مسیر
        for gx, gy in PATH_CELLS:
            px = GRID_X + gx * GRID_SIZE
            py = GRID_Y + gy * GRID_SIZE
            pygame.draw.rect(play_layer, (*NEON_CYAN, 30),
                             (px, py, GRID_SIZE, GRID_SIZE))

        # Preview برج
        if placing and selected_type and mouse_tile:
            gx, gy = mouse_tile
            if (gx, gy) in BUILD_SLOTS:
                occupied = any(t.gx == gx and t.gy == gy for t in towers)
                if not occupied:
                    px = GRID_X + gx * GRID_SIZE
                    py = GRID_Y + gy * GRID_SIZE
                    t_data = TOWER_TYPES[selected_type]
                    # برد
                    cx = px + GRID_SIZE / 2
                    cy = py + GRID_SIZE / 2
                    range_surf = pygame.Surface((t_data['range'] * 2, t_data['range'] * 2), pygame.SRCALPHA)
                    pygame.draw.circle(range_surf, (*t_data['color'], 30),
                                       (t_data['range'], t_data['range']), t_data['range'])
                    pygame.draw.circle(range_surf, (*t_data['color'], 80),
                                       (t_data['range'], t_data['range']), t_data['range'], 2)
                    play_layer.blit(range_surf, (cx - t_data['range'], cy - t_data['range']))
                    # خود برج
                    pygame.draw.rect(play_layer, (*t_data['color'], 100),
                                     (px + 4, py + 4, GRID_SIZE - 8, GRID_SIZE - 8), border_radius=6)
                    pygame.draw.rect(play_layer, t_data['color'],
                                     (px + 4, py + 4, GRID_SIZE - 8, GRID_SIZE - 8), 2, border_radius=6)
                    draw_text(play_layer, t_data['icon'], 20, cx, cy - 8, WHITE, center=True)

        # ارواح و برج‌ها
        for tower in towers:
            tower.draw(play_layer, selected=(tower == selected_tower))

        # پرتابه‌ها
        for p in projectiles:
            p.draw(play_layer)

        # دشمن‌ها
        for e in enemies:
            e.draw(play_layer)

        # ذرات
        for p in active_particles:
            p.draw(play_layer)

        # Base (پایین راست)
        base_px = GRID_X + 20 * GRID_SIZE + GRID_SIZE / 2
        base_py = GRID_Y + 12 * GRID_SIZE + GRID_SIZE / 2
        for hr in range(4, 0, -1):
            glow = pygame.Surface((120 + hr * 10, 120 + hr * 10), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*NEON_GREEN, 60 - hr * 10),
                               ((120 + hr * 10) // 2, (120 + hr * 10) // 2), (120 + hr * 10) // 2)
            play_layer.blit(glow, (base_px - (120 + hr * 10) // 2, base_py - (120 + hr * 10) // 2))
        pygame.draw.circle(play_layer, (20, 60, 30), (int(base_px), int(base_py)), 40)
        pygame.draw.circle(play_layer, NEON_GREEN, (int(base_px), int(base_py)), 40, 4)
        draw_text(play_layer, "BASE", 16, base_px, base_py - 8, WHITE, center=True, glow=True)

        # ورودی دشمن‌ها (بالا)
        start_px = GRID_X + 2 * GRID_SIZE + GRID_SIZE / 2
        start_py = GRID_Y - 10
        for hr in range(4, 0, -1):
            glow = pygame.Surface((80 + hr * 10, 40 + hr * 10), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*NEON_RED, 60 - hr * 10),
                                (0, 0, 80 + hr * 10, 40 + hr * 10))
            play_layer.blit(glow, (start_px - (80 + hr * 10) // 2, start_py - (40 + hr * 10) // 2))
        pygame.draw.ellipse(play_layer, NEON_RED, (start_px - 40, start_py - 15, 80, 30), 3)

        if flash > 0:
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 200, 100, flash))
            play_layer.blit(fs, (0, 0))

        game_surface.blit(play_layer, (offset_x, offset_y))

        # ============================================================
        #                    HUD
        # ============================================================
        # نوار بالا
        hud_panel = pygame.Surface((WIDTH, 100), pygame.SRCALPHA)
        for y in range(100):
            alpha = int(200 * (1 - y / 100))
            pygame.draw.line(hud_panel, (5, 10, 25, alpha), (0, y), (WIDTH, y))
        game_surface.blit(hud_panel, (0, 0))
        pygame.draw.line(game_surface, NEON_CYAN, (0, 100), (WIDTH, 100), 1)

        # عنوان
        draw_text(game_surface, "NEON DEFENDER", 22, 25, 15, NEON_CYAN, glow=True)
        draw_text(game_surface, f"WAVE {wave}", 18, 25, 45, NEON_YELLOW)
        draw_text(game_surface, f"KILLS: {total_kills[0]}", 14, 25, 70, NEON_PINK)

        # Money و Score
        draw_text(game_surface, "SCORE", 14, WIDTH - 25, 10, NEON_CYAN, center=False)
        draw_text(game_surface, f"{display_score}", 26, WIDTH - 25, 28, WHITE, glow=True)
        draw_text(game_surface, f"MONEY: ${money}", 18, WIDTH - 25, 60, NEON_GREEN, glow=True)

        # دکمه‌های برج
        for t_type, btn, t_data in tower_buttons:
            btn.update(mouse_pos)
            # رنگ اگه نتونی بخری
            if money < t_data['cost']:
                btn.color = (100, 100, 100)
            else:
                btn.color = t_data['color']
            # اگه انتخاب شده
            if selected_type == t_type:
                btn.color = WHITE
            btn.draw(game_surface)
            # قیمت
            cost_color = NEON_GREEN if money >= t_data['cost'] else NEON_RED
            draw_text(game_surface, f"${t_data['cost']}", 12, btn.rect.centerx, btn.rect.bottom + 3,
                      cost_color, center=True)

        # Base HP
        draw_text(game_surface, "BASE HP", 14, 25, GRID_Y + GRID_H + 20, NEON_CYAN)
        bar_w = 200
        bar_x = 25
        bar_y = GRID_Y + GRID_H + 45
        pygame.draw.rect(game_surface, (40, 10, 10), (bar_x, bar_y, bar_w, 20))
        ratio = base_hp / max_base_hp
        hp_color = NEON_GREEN if ratio > 0.5 else NEON_YELLOW if ratio > 0.25 else NEON_RED
        pygame.draw.rect(game_surface, hp_color, (bar_x, bar_y, bar_w * ratio, 20))
        pygame.draw.rect(game_surface, WHITE, (bar_x, bar_y, bar_w, 20), 2)
        draw_text(game_surface, f"{base_hp}/{max_base_hp}", 16, bar_x + bar_w // 2, bar_y + 2,
                  WHITE, center=True, glow=True)

        # دکمه Start Wave
        if not wave_active and not in_intermission:
            btn_start_wave.update(mouse_pos)
            btn_start_wave.draw(game_surface)
        elif in_intermission:
            draw_text(game_surface, f"NEXT WAVE IN {intermission_timer // 60 + 1}s", 18,
                      GRID_X + GRID_W // 2, GRID_Y + GRID_H + 60, NEON_YELLOW, center=True, glow=True)

        # پنل انتخاب برج
        if selected_tower:
            panel_x = WIDTH - 300
            panel_y = GRID_Y
            panel_w = 280
            panel_h = 250
            pygame.draw.rect(game_surface, (10, 5, 25), (panel_x, panel_y, panel_w, panel_h))
            pygame.draw.rect(game_surface, selected_tower.stats['color'],
                             (panel_x, panel_y, panel_w, panel_h), 3)
            draw_text(game_surface, selected_tower.stats['name'], 20,
                      panel_x + panel_w // 2, panel_y + 15, selected_tower.stats['color'],
                      center=True, glow=True)
            draw_text(game_surface, f"Level: {selected_tower.level}/{selected_tower.max_level}",
                      16, panel_x + 15, panel_y + 50, WHITE)
            draw_text(game_surface, f"Damage: {selected_tower.get_damage()}",
                      14, panel_x + 15, panel_y + 75, NEON_ORANGE)
            draw_text(game_surface, f"Range: {selected_tower.get_range()}",
                      14, panel_x + 15, panel_y + 95, NEON_CYAN)
            draw_text(game_surface, f"Fire Rate: {selected_tower.get_fire_rate()}f",
                      14, panel_x + 15, panel_y + 115, NEON_YELLOW)
            upgrade_cost = selected_tower.get_upgrade_cost()
            if upgrade_cost:
                btn_upgrade.update(mouse_pos)
                btn_upgrade.text = f"UPGRADE (${upgrade_cost})"
                btn_upgrade.color = NEON_GREEN if money >= upgrade_cost else (100, 100, 100)
                btn_upgrade.rect = pygame.Rect(panel_x + panel_w // 2, panel_y + 160, 220, 40)
                btn_upgrade.rect.center = (panel_x + panel_w // 2, panel_y + 160)
                btn_upgrade.text_size = 16
                btn_upgrade.draw(game_surface)
            else:
                draw_text(game_surface, "MAX LEVEL", 16, panel_x + panel_w // 2, panel_y + 160,
                          NEON_YELLOW, center=True)

            btn_sell.update(mouse_pos)
            btn_sell.text = f"SELL (${selected_tower.sell_value()})"
            btn_sell.rect = pygame.Rect(panel_x + panel_w // 2, panel_y + 210, 220, 40)
            btn_sell.rect.center = (panel_x + panel_w // 2, panel_y + 210)
            btn_sell.text_size = 16
            btn_sell.draw(game_surface)

        # Combo
        if combo > 1:
            combo_color = NEON_GREEN if combo < 10 else NEON_YELLOW if combo < 20 else NEON_PINK
            scale = 1 + math.sin(t * 10) * 0.1
            draw_text(game_surface, f"x{combo} COMBO", int(24 * scale), WIDTH // 2, 55,
                      combo_color, center=True, glow=True)

        # Banner
        if wave_banner_timer > 0:
            size = 60 + int(math.sin(t * 10) * 5)
            draw_text(game_surface, f"WAVE {wave}", size, WIDTH // 2, HEIGHT // 2 - 50,
                      NEON_CYAN, center=True, glow=True)
            if wave % 5 == 0:
                draw_text(game_surface, "BOSS WAVE!", 30, WIDTH // 2, HEIGHT // 2 + 20,
                          NEON_RED, center=True, glow=True)

        # Notifications
        for i, notif in enumerate(notifications):
            ny = 110 + i * 60
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
            draw_text(game_surface, f"SCORE: {final_score}", 32,
                      WIDTH // 2, box_y + 120, WHITE, center=True)
            draw_text(game_surface, f"WAVE: {final_wave}   KILLS: {total_kills[0]}",
                      16, WIDTH // 2, box_y + 160, NEON_CYAN, center=True)
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