import pygame
import random
import math
import array
import threading
import json
import os
import sys
from datetime import datetime

# --- تنظیمات اولیه ---
pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
    AUDIO_OK = True
except:
    AUDIO_OK = False

BASE_W, BASE_H = 900, 650
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("NEON SPACE SHOOTER — ULTIMATE")
game_surface = pygame.Surface((BASE_W, BASE_H))

clock = pygame.time.Clock()
FPS = 60

# --- رنگ‌ها ---
BLACK = (3, 3, 12)
WHITE = (255, 255, 255)
NEON_PURPLE = (180, 60, 255)
NEON_PINK = (255, 40, 150)
NEON_RED = (255, 50, 50)
NEON_BLUE = (60, 160, 255)
NEON_CYAN = (0, 255, 255)
NEON_YELLOW = (255, 230, 0)
NEON_GREEN = (50, 255, 120)
NEON_ORANGE = (255, 140, 0)
NEON_MAGENTA = (255, 0, 200)

# --- فایل ذخیره ---
SAVE_FILE = "neon_save.json"

settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'difficulty': 1.0,
    'screen_shake': True,
}

achievements = {
    'first_blood': {'name': 'FIRST BLOOD', 'desc': 'Destroy your first meteor', 'unlocked': False, 'icon': '*'},
    'combo_5': {'name': 'COMBO MASTER', 'desc': 'Reach a 5x combo', 'unlocked': False, 'icon': 'F'},
    'combo_10': {'name': 'COMBO LEGEND', 'desc': 'Reach a 10x combo', 'unlocked': False, 'icon': 'Z'},
    'score_500': {'name': 'ROOKIE', 'desc': 'Score 500 points', 'unlocked': False, 'icon': '*'},
    'score_2000': {'name': 'VETERAN', 'desc': 'Score 2000 points', 'unlocked': False, 'icon': '**'},
    'score_5000': {'name': 'LEGEND', 'desc': 'Score 5000 points', 'unlocked': False, 'icon': '***'},
    'boss_kill': {'name': 'BOSS SLAYER', 'desc': 'Defeat your first boss', 'unlocked': False, 'icon': '@'},
    'boss_3': {'name': 'BOSS HUNTER', 'desc': 'Defeat 3 bosses', 'unlocked': False, 'icon': 'O'},
    'survive_2min': {'name': 'SURVIVOR', 'desc': 'Survive for 2 minutes', 'unlocked': False, 'icon': 'T'},
}

highscore = [0]
boss_kills = [0]
game_history = []  # لیست بازی‌های قبلی

# --- ذخیره/بارگذاری ---
def load_save():
    global settings, achievements, highscore, boss_kills, game_history
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
            settings.update(data.get('settings', {}))
            for k, v in data.get('achievements', {}).items():
                if k in achievements:
                    achievements[k]['unlocked'] = v
            highscore[0] = data.get('highscore', 0)
            boss_kills[0] = data.get('boss_kills', 0)
            game_history = data.get('game_history', [])
    except:
        pass

def save_game_async():
    def worker():
        try:
            data = {
                'settings': settings,
                'achievements': {k: v['unlocked'] for k, v in achievements.items()},
                'highscore': highscore[0],
                'boss_kills': boss_kills[0],
                'game_history': game_history[-50:],  # فقط 50 تای آخر
            }
            with open(SAVE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass
    threading.Thread(target=worker, daemon=True).start()

load_save()

def add_game_to_history(score, bosses, duration_sec, level_reached, new_achievements):
    """اضافه کردن یه بازی به تاریخچه"""
    entry = {
        'score': score,
        'bosses': bosses,
        'duration': duration_sec,
        'level': level_reached,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'achievements': new_achievements,  # لیست دستاوردهای جدید این بازی
    }
    game_history.append(entry)
    save_game_async()

def unlock_achievement(key):
    if key in achievements and not achievements[key]['unlocked']:
        achievements[key]['unlocked'] = True
        save_game_async()
        return True
    return False

# --- Font Cache ---
FONT_CACHE = {}
def get_font(size, bold=True):
    key = (size, bold)
    if key not in FONT_CACHE:
        FONT_CACHE[key] = pygame.font.SysFont("consolas", size, bold=bold)
    return FONT_CACHE[key]

# --- صدا ---
sounds = {}
music_sound = [None]
sound_ready = threading.Event()

def make_sound(freq_start, freq_end, duration, volume=0.3, wave='sine'):
    if not AUDIO_OK:
        return None
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = array.array('h')
    for i in range(n_samples):
        t = i / sample_rate
        freq = freq_start + (freq_end - freq_start) * (i / n_samples)
        if wave == 'sine':
            val = math.sin(2 * math.pi * freq * t)
        elif wave == 'square':
            val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
        elif wave == 'noise':
            val = random.uniform(-1, 1)
        elif wave == 'saw':
            val = 2 * (freq * t - math.floor(freq * t + 0.5))
        else:
            val = math.sin(2 * math.pi * freq * t)
        env = 1.0 - (i / n_samples)
        val *= env * volume
        buf.append(int(val * 32767))
    try:
        return pygame.mixer.Sound(buffer=buf)
    except:
        return None

def make_music_loop(notes, note_duration, volume=0.3, waveform='sine'):
    if not AUDIO_OK:
        return None
    sample_rate = 44100
    buf = array.array('h')
    for note in notes:
        if note == 0:
            n_samples = int(sample_rate * note_duration)
            buf.extend([0] * n_samples)
            continue
        n_samples = int(sample_rate * note_duration)
        for i in range(n_samples):
            t = i / sample_rate
            if waveform == 'sine':
                val = math.sin(2 * math.pi * note * t)
            elif waveform == 'saw':
                val = 2 * (note * t - math.floor(note * t + 0.5))
            elif waveform == 'triangle':
                val = 2 * abs(2 * (note * t - math.floor(note * t + 0.5))) - 1
            else:
                val = math.sin(2 * math.pi * note * t)
            val += math.sin(2 * math.pi * note * 2 * t) * 0.15
            val += math.sin(2 * math.pi * note * 0.5 * t) * 0.1
            env = 1.0
            if i < n_samples * 0.05:
                env = i / (n_samples * 0.05)
            elif i > n_samples * 0.85:
                env = 1.0 - (i - n_samples * 0.85) / (n_samples * 0.15)
            val *= env * volume
            buf.append(int(max(-1, min(1, val)) * 32767))
    try:
        return pygame.mixer.Sound(buffer=buf)
    except:
        return None

def build_sounds():
    sounds['shoot'] = make_sound(900, 1400, 0.07, 0.10, 'square')
    sounds['explosion'] = make_sound(400, 50, 0.3, 0.22, 'noise')
    sounds['big_explosion'] = make_sound(250, 30, 0.5, 0.30, 'noise')
    sounds['powerup'] = make_sound(500, 1400, 0.35, 0.18, 'sine')
    sounds['hit'] = make_sound(200, 60, 0.4, 0.28, 'noise')
    sounds['gameover'] = make_sound(500, 60, 1.2, 0.28, 'saw')
    sounds['combo'] = make_sound(1200, 1800, 0.15, 0.13, 'sine')
    sounds['laser'] = make_sound(2000, 400, 0.3, 0.20, 'saw')
    sounds['boss_alert'] = make_sound(150, 800, 0.8, 0.25, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['achievement'] = make_sound(600, 1600, 0.5, 0.20, 'sine')

    music_notes = [
        220, 261.63, 329.63, 392, 329.63, 261.63,
        220, 261.63, 329.63, 440, 392, 329.63,
        196, 246.94, 293.66, 392, 293.66, 246.94,
        220, 261.63, 329.63, 392, 329.63, 261.63,
    ]
    music = make_music_loop(music_notes, 0.22, 0.12, 'triangle')
    music_sound[0] = music
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
    if not sound_ready.is_set() or not music_sound[0]:
        return
    try:
        music_sound[0].set_volume(settings['music_volume'] * 0.4)
        music_sound[0].play(loops=-1)
    except:
        pass

def stop_music():
    if music_sound[0]:
        try:
            music_sound[0].stop()
        except:
            pass

def update_music_volume():
    if music_sound[0]:
        try:
            music_sound[0].set_volume(settings['music_volume'] * 0.4)
        except:
            pass

# --- ذرات ---
particle_pool = []
active_particles = []

class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'size', 'active', 'gravity')
    def __init__(self):
        self.active = False
        self.x = self.y = 0
        self.vx = self.vy = 0
        self.life = 0
        self.max_life = 1
        self.color = WHITE
        self.size = 2
        self.gravity = 0.05
    def spawn(self, x, y, color, speed_mult=1.0, size_mult=1.0, life_mult=1.0, gravity=0.05):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 6) * speed_mult
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = int(random.randint(20, 45) * life_mult)
        self.max_life = self.life
        self.color = color
        self.size = random.randint(2, 4) * size_mult
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

def spawn_particles(x, y, color, count, speed_mult=1.0, size_mult=1.0, life_mult=1.0, gravity=0.05):
    count = int(count)
    for _ in range(count):
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

# --- ستاره ---
class Star:
    __slots__ = ('x', 'y', 'speed', 'size', 'color', 'layer')
    def __init__(self):
        self.layer = random.randint(0, 2)
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        speeds = [0.3, 0.8, 1.8]
        sizes = [1, 1, 2]
        colors = [(120, 120, 180), (200, 200, 255), WHITE]
        self.speed = speeds[self.layer] * random.uniform(0.8, 1.2)
        self.size = sizes[self.layer]
        self.color = colors[self.layer]
    def update(self, speed_mult=1.0):
        self.y += self.speed * speed_mult
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(0, WIDTH)
    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)

# --- Meteor ---
class Meteor:
    def __init__(self, speed_mult=1.0, size_type=None, x=None):
        self.x = x if x else random.randint(60, WIDTH - 60)
        self.y = -60
        if size_type is None:
            size_type = random.choices(['small', 'medium', 'large'], weights=[5, 3, 1])[0]
        self.size_type = size_type
        if size_type == 'small':
            self.size = random.randint(18, 26)
            self.hp = 1
            self.score_value = 10
            self.color = NEON_RED
        elif size_type == 'medium':
            self.size = random.randint(30, 40)
            self.hp = 2
            self.score_value = 25
            self.color = NEON_ORANGE
        else:
            self.size = random.randint(45, 58)
            self.hp = 4
            self.score_value = 60
            self.color = NEON_PINK
        self.max_hp = self.hp
        self.speed = random.uniform(2, 4.5) * speed_mult
        if size_type == 'large':
            self.speed *= 0.7
        self.rotation = random.uniform(0, math.pi)
        self.rot_speed = random.uniform(-0.05, 0.05)
        self.shape_seed = random.randint(0, 1000)
        self._points = None
        self._last_rot = -999
    def get_points(self):
        if self._points is None or abs(self.rotation - self._last_rot) > 0.05:
            pts = []
            n = 7
            for i in range(n):
                angle = (2 * math.pi / n) * i
                noise = math.sin(self.shape_seed + i * 3.7) * 0.2
                r = self.size * (0.85 + noise)
                pts.append((math.cos(angle) * r, math.sin(angle) * r))
            self._points = pts
            self._last_rot = self.rotation
        cos_r = math.cos(self.rotation)
        sin_r = math.sin(self.rotation)
        return [(self.x + px * cos_r - py * sin_r,
                 self.y + px * sin_r + py * cos_r) for px, py in self._points]
    def update(self, speed_mult=1.0):
        self.y += self.speed * speed_mult
        self.rotation += self.rot_speed
    def draw(self, surface):
        pts = self.get_points()
        pygame.draw.polygon(surface, (self.color[0] // 4, self.color[1] // 4, self.color[2] // 4), pts)
        pygame.draw.polygon(surface, self.color, pts, 2)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), max(2, self.size // 6))
        if self.max_hp > 1 and self.hp < self.max_hp:
            bar_w = self.size * 1.5
            bar_x = self.x - bar_w / 2
            bar_y = self.y - self.size - 12
            pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_w, 4))
            ratio = self.hp / self.max_hp
            pygame.draw.rect(surface, self.color, (bar_x, bar_y, bar_w * ratio, 4))

# --- Boss ---
class Boss:
    def __init__(self, level, spawn_count):
        self.x = WIDTH // 2
        self.y = -120
        self.target_y = 120
        self.level = level
        self.spawn_count = spawn_count
        self.size = 70 + spawn_count * 8
        base_hp = 50 + level * 30
        self.max_hp = int(base_hp * (1 + spawn_count * 0.6))
        self.hp = self.max_hp
        self.speed = (1.5 + level * 0.3) * (1 + spawn_count * 0.15)
        self.direction = 1
        self.shoot_timer = 0
        self.shoot_interval = max(25, 80 - level * 5 - spawn_count * 8)
        self.bullets = []
        self.entering = True
    def update(self, player):
        if self.entering:
            self.y += 2
            if self.y >= self.target_y:
                self.y = self.target_y
                self.entering = False
            return
        self.x += self.speed * self.direction
        if self.x > WIDTH - 100:
            self.direction = -1
        elif self.x < 100:
            self.direction = 1
        self.shoot_timer += 1
        if self.shoot_timer > self.shoot_interval:
            self.shoot_timer = 0
            if self.spawn_count >= 2:
                for offset in [-0.3, 0, 0.3]:
                    dx = player.x - self.x
                    dy = player.y - self.y
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        vx = dx / dist * 5
                        vy = dy / dist * 5
                        cos_o = math.cos(offset)
                        sin_o = math.sin(offset)
                        rvx = vx * cos_o - vy * sin_o
                        rvy = vx * sin_o + vy * cos_o
                        self.bullets.append(BossBullet(self.x, self.y + 40, rvx, rvy))
            else:
                dx = player.x - self.x
                dy = player.y - self.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    vx = dx / dist * 5
                    vy = dy / dist * 5
                    self.bullets.append(BossBullet(self.x, self.y + 40, vx, vy))
        for b in self.bullets[:]:
            b.update()
            if b.y > HEIGHT + 20 or b.y < -20 or b.x < -20 or b.x > WIDTH + 20:
                self.bullets.remove(b)
    def draw(self, surface):
        colors = [NEON_MAGENTA, NEON_ORANGE, NEON_RED, NEON_PURPLE, (255, 0, 100)]
        main_color = colors[self.spawn_count % len(colors)]
        glow = pygame.Surface((340, 340), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*main_color, 50), (170, 170), 150)
        surface.blit(glow, (self.x - 170, self.y - 170))
        n = 8 if self.spawn_count >= 1 else 6
        pts = []
        for i in range(n):
            angle = math.pi / 6 + i * (2 * math.pi / n)
            pts.append((self.x + math.cos(angle) * self.size,
                        self.y + math.sin(angle) * self.size * 0.7))
        pygame.draw.polygon(surface, (60, 10, 40), pts)
        pygame.draw.polygon(surface, main_color, pts, 3)
        pygame.draw.polygon(surface, WHITE, pts, 1)
        core_glow = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(core_glow, (*main_color, 180), (50, 50), 35)
        surface.blit(core_glow, (self.x - 50, self.y - 50))
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 18)
        pygame.draw.circle(surface, main_color, (int(self.x), int(self.y)), 25, 2)
        eye_blink = (pygame.time.get_ticks() // 2000) % 2
        if not eye_blink:
            pygame.draw.circle(surface, NEON_RED, (int(self.x - 22), int(self.y - 10)), 6)
            pygame.draw.circle(surface, NEON_RED, (int(self.x + 22), int(self.y - 10)), 6)
        for b in self.bullets:
            b.draw(surface)

class BossBullet:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = 8
    def update(self):
        self.x += self.vx
        self.y += self.vy
    def draw(self, surface):
        glow = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 0, 150, 150), (15, 15), 12)
        surface.blit(glow, (self.x - 15, self.y - 15))
        pygame.draw.circle(surface, NEON_MAGENTA, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 3)

# --- Bullet ---
class Bullet:
    __slots__ = ('x', 'y', 'vx', 'speed', 'radius', 'damage', 'trail')
    def __init__(self, x, y, vx=0, damage=1):
        self.x = x
        self.y = y
        self.vx = vx
        self.speed = -11
        self.radius = 3
        self.damage = damage
        self.trail = []
    def update(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 6:
            self.trail.pop(0)
        self.y += self.speed
        self.x += self.vx
    def draw(self, surface):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / len(self.trail)
            r = max(1, int(self.radius * alpha))
            c = (0, int(150 * alpha + 50), 255)
            pygame.draw.circle(surface, c, (int(tx), int(ty)), r)
        pygame.draw.circle(surface, NEON_CYAN, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 1)

class Laser:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 8
        self.life = 30
    def update(self):
        self.life -= 1
        self.y -= 15
    def draw(self, surface):
        alpha = self.life / 30
        glow = pygame.Surface((40, 60), pygame.SRCALPHA)
        pygame.draw.rect(glow, (255, 0, 255, int(150 * alpha)), (10, 0, 20, 60))
        surface.blit(glow, (self.x - 20, self.y - 30))
        pygame.draw.rect(surface, NEON_MAGENTA, (self.x - self.width // 2, self.y - 30, self.width, 60))
        pygame.draw.rect(surface, WHITE, (self.x - 2, self.y - 30, 4, 60))

# --- Player ---
class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 90
        self.speed = 7
        self.lives = 3
        self.score = 0
        self.display_score = 0
        self.bullets = []
        self.lasers = []
        self.shoot_cooldown = 0
        self.power_level = 1
        self.power_timer = 0
        self.invincible = 0
        self.shield = 0
        self.laser_timer = 0
        self.combo = 0
        self.combo_timer = 0
        self.max_combo = 0
        self.wing_phase = 0
        self.engine_timer = 0
    def move(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        self.x = max(35, min(WIDTH - 35, self.x))
    def shoot(self):
        if self.shoot_cooldown == 0:
            if self.power_level == 1:
                self.bullets.append(Bullet(self.x, self.y - 25))
            elif self.power_level == 2:
                self.bullets.append(Bullet(self.x - 12, self.y - 20))
                self.bullets.append(Bullet(self.x + 12, self.y - 20))
            elif self.power_level >= 3:
                self.bullets.append(Bullet(self.x, self.y - 30))
                self.bullets.append(Bullet(self.x - 18, self.y - 15, -0.8))
                self.bullets.append(Bullet(self.x + 18, self.y - 15, 0.8))
            self.shoot_cooldown = 10
            play_sound('shoot')
    def update(self):
        if self.display_score < self.score:
            diff = self.score - self.display_score
            self.display_score += max(1, diff // 8)
            if self.display_score > self.score:
                self.display_score = self.score
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.power_timer > 0:
            self.power_timer -= 1
            if self.power_timer == 0:
                self.power_level = 1
        if self.invincible > 0:
            self.invincible -= 1
        if self.shield > 0:
            self.shield -= 1
        if self.laser_timer > 0:
            self.laser_timer -= 1
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0:
                self.combo = 0
        self.wing_phase += 0.15
        self.engine_timer += 1
        if self.engine_timer > 2:
            self.engine_timer = 0
            for _ in range(2):
                p = None
                for pp in particle_pool:
                    if not pp.active:
                        p = pp
                        break
                if p is None:
                    p = Particle()
                    particle_pool.append(p)
                p.x = self.x + random.uniform(-4, 4)
                p.y = self.y + 22
                p.vx = random.uniform(-0.5, 0.5)
                p.vy = random.uniform(1.5, 3)
                p.life = random.randint(10, 20)
                p.max_life = p.life
                p.color = random.choice([NEON_CYAN, NEON_BLUE, (150, 200, 255)])
                p.size = random.randint(1, 3)
                p.gravity = 0
                p.active = True
                active_particles.append(p)
        for b in self.bullets[:]:
            b.update()
            if b.y < -20 or b.x < -20 or b.x > WIDTH + 20:
                self.bullets.remove(b)
        for l in self.lasers[:]:
            l.update()
            if l.life <= 0:
                self.lasers.remove(l)
    def draw(self, surface):
        if self.invincible > 0 and (self.invincible // 4) % 2 == 0:
            return
        if self.power_level == 1:
            body_color = NEON_PURPLE
            accent_color = NEON_PINK
            glow_color = (180, 60, 255)
        elif self.power_level == 2:
            body_color = NEON_CYAN
            accent_color = NEON_BLUE
            glow_color = (0, 255, 255)
        else:
            body_color = NEON_YELLOW
            accent_color = NEON_ORANGE
            glow_color = (255, 230, 0)
        glow = pygame.Surface((140, 140), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*glow_color, 50), (70, 70), 55)
        surface.blit(glow, (self.x - 70, self.y - 70))
        if self.shield > 0:
            shield_alpha = 100 + int(math.sin(pygame.time.get_ticks() / 100) * 60)
            shield_surf = pygame.Surface((140, 140), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (*NEON_GREEN, shield_alpha), (70, 70), 50, 3)
            pygame.draw.circle(shield_surf, (*NEON_GREEN, shield_alpha // 3), (70, 70), 55, 1)
            for i in range(6):
                a = pygame.time.get_ticks() / 500 + i * math.pi / 3
                px = 70 + math.cos(a) * 50
                py = 70 + math.sin(a) * 50
                pygame.draw.circle(shield_surf, (*NEON_GREEN, shield_alpha), (int(px), int(py)), 3)
            surface.blit(shield_surf, (self.x - 70, self.y - 70))
        flame_len = random.randint(14, 24)
        for i in range(4):
            color = (100 + i * 30, 150 - i * 20, 255)
            width = 5 - i
            pygame.draw.line(surface, color,
                             (self.x, self.y + 20),
                             (self.x + random.randint(-2, 2), self.y + 20 + flame_len - i * 4),
                             width)
        wing_offset = math.sin(self.wing_phase) * 2
        left_wing = [
            (self.x - 20, self.y + 5),
            (self.x - 38, self.y + 15 + wing_offset),
            (self.x - 34, self.y + 26 + wing_offset),
            (self.x - 22, self.y + 18),
        ]
        pygame.draw.polygon(surface, (20, 5, 40), left_wing)
        pygame.draw.polygon(surface, accent_color, left_wing, 2)
        pygame.draw.line(surface, body_color, (self.x - 24, self.y + 8),
                         (self.x - 32, self.y + 22 + wing_offset), 1)
        right_wing = [
            (self.x + 20, self.y + 5),
            (self.x + 38, self.y + 15 + wing_offset),
            (self.x + 34, self.y + 26 + wing_offset),
            (self.x + 22, self.y + 18),
        ]
        pygame.draw.polygon(surface, (20, 5, 40), right_wing)
        pygame.draw.polygon(surface, accent_color, right_wing, 2)
        pygame.draw.line(surface, body_color, (self.x + 24, self.y + 8),
                         (self.x + 32, self.y + 22 + wing_offset), 1)
        body_dark = [
            (self.x, self.y - 34),
            (self.x - 22, self.y + 16),
            (self.x + 22, self.y + 16),
            (self.x, self.y + 6),
        ]
        pygame.draw.polygon(surface, (15, 5, 30), body_dark)
        pygame.draw.polygon(surface, body_color, body_dark, 3)
        body_mid = [
            (self.x, self.y - 28),
            (self.x - 14, self.y + 10),
            (self.x + 14, self.y + 10),
            (self.x, self.y + 2),
        ]
        pygame.draw.polygon(surface, (30, 10, 55), body_mid)
        pygame.draw.polygon(surface, accent_color, body_mid, 2)
        pygame.draw.line(surface, body_color, (self.x, self.y - 32), (self.x, self.y + 4), 1)
        cockpit_glow = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(cockpit_glow, (*NEON_CYAN, 80), (12, 12), 10)
        surface.blit(cockpit_glow, (self.x - 12, self.y - 18))
        pygame.draw.circle(surface, NEON_CYAN, (int(self.x), int(self.y - 12)), 6)
        pygame.draw.circle(surface, (150, 240, 255), (int(self.x - 1), int(self.y - 13)), 3)
        pygame.draw.circle(surface, WHITE, (int(self.x - 2), int(self.y - 14)), 1)
        light_blink = (pygame.time.get_ticks() // 300) % 2
        light_color = NEON_RED if light_blink else (100, 20, 20)
        pygame.draw.circle(surface, light_color, (int(self.x - 18), int(self.y + 12)), 2)
        pygame.draw.circle(surface, light_color, (int(self.x + 18), int(self.y + 12)), 2)
        for b in self.bullets:
            b.draw(surface)
        for l in self.lasers:
            l.draw(surface)

# --- PowerUp ---
class PowerUp:
    def __init__(self):
        self.x = random.randint(60, WIDTH - 60)
        self.y = -30
        self.speed = 2.5
        self.type = random.choices(
            ['multi', 'life', 'shield', 'score', 'laser'],
            weights=[4, 2, 2, 3, 1]
        )[0]
        self.radius = 16
        self.pulse = random.uniform(0, math.pi * 2)
    def update(self):
        self.y += self.speed
        self.pulse += 0.15
    def draw(self, surface):
        colors = {
            'multi': NEON_CYAN,
            'life': NEON_PINK,
            'shield': NEON_GREEN,
            'score': NEON_YELLOW,
            'laser': NEON_MAGENTA,
        }
        color = colors[self.type]
        r = self.radius + int(math.sin(self.pulse) * 3)
        glow = pygame.Surface((r * 5, r * 5), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, 60), (r * 2 + r // 2, r * 2 + r // 2), r * 2)
        surface.blit(glow, (self.x - r * 2 - r // 2, self.y - r * 2 - r // 2))
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), r, 2)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), r - 4, 1)
        for i in range(6):
            angle = self.pulse * 2 + i * math.pi / 3
            px = self.x + math.cos(angle) * r
            py = self.y + math.sin(angle) * r
            pygame.draw.circle(surface, color, (int(px), int(py)), 2)
        if self.type == 'life':
            pts = [
                (self.x, self.y + 7),
                (self.x - 8, self.y - 4),
                (self.x - 3, self.y - 8),
                (self.x, self.y - 3),
                (self.x + 3, self.y - 8),
                (self.x + 8, self.y - 4),
            ]
            pygame.draw.polygon(surface, color, pts)
        elif self.type == 'multi':
            for dx in (-6, 0, 6):
                pygame.draw.line(surface, color,
                                 (self.x + dx, self.y - 7),
                                 (self.x + dx, self.y + 7), 3)
        elif self.type == 'shield':
            pts = [
                (self.x, self.y - 8),
                (self.x - 7, self.y - 4),
                (self.x - 6, self.y + 5),
                (self.x, self.y + 9),
                (self.x + 6, self.y + 5),
                (self.x + 7, self.y - 4),
            ]
            pygame.draw.polygon(surface, color, pts, 2)
        elif self.type == 'score':
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 6, 2)
            pygame.draw.line(surface, color, (self.x, self.y - 6), (self.x, self.y + 6), 2)
            pygame.draw.line(surface, color, (self.x - 6, self.y), (self.x + 6, self.y), 2)
        elif self.type == 'laser':
            pygame.draw.polygon(surface, color, [
                (self.x, self.y - 9),
                (self.x - 5, self.y + 3),
                (self.x + 5, self.y + 3),
            ])
            pygame.draw.line(surface, WHITE, (self.x, self.y - 6), (self.x, self.y + 2), 2)

# --- Button ---
class Button:
    def __init__(self, x, y, w, h, text, color, hover_color=None, text_size=32):
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
        corner_size = 12
        for cx, cy in [(rx, ry), (rx + w - corner_size, ry),
                       (rx, ry + h - corner_size), (rx + w - corner_size, ry + h - corner_size)]:
            pygame.draw.rect(surface, color, (cx, cy, corner_size, 3))
            pygame.draw.rect(surface, color, (cx, cy, 3, corner_size))
        text_color = WHITE if self.hovered else (230, 230, 230)
        draw_text(surface, self.text, self.text_size,
                  self.rect.centerx, self.rect.centery,
                  text_color, center=True, glow=self.hovered)
    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.click_anim = 10
                play_sound('click')
                return True
        return False

# --- Slider ---
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
        pygame.draw.rect(surface, NEON_CYAN,
                         (self.rect.x, self.rect.y, fill_w, self.rect.height),
                         border_radius=4)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=4)
        knob = self._knob_rect()
        color = NEON_GREEN if self.hovered else NEON_PINK
        pygame.draw.rect(surface, color, knob, border_radius=4)
        pygame.draw.rect(surface, WHITE, knob, 2, border_radius=4)
        draw_text(surface, self.label, 18, self.rect.x, self.rect.y - 30, WHITE)
        val_text = f"{int(self.value * 100)}%"
        draw_text(surface, val_text, 18, self.rect.right - 60, self.rect.y - 30, NEON_YELLOW)

# --- draw_text ---
def draw_text(surface, text, size, x, y, color, center=False, bold=True, glow=False):
    font = get_font(size, bold)
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

def draw_heart(surface, x, y, size=14, filled=True):
    color = NEON_PINK
    pts = [
        (x, y + size // 2),
        (x - size, y - size // 2),
        (x - size // 2, y - size),
        (x, y - size // 2),
        (x + size // 2, y - size),
        (x + size, y - size // 2),
    ]
    if filled:
        pygame.draw.polygon(surface, color, pts)
        pygame.draw.polygon(surface, (255, 150, 200), pts, 1)
    else:
        pygame.draw.polygon(surface, (80, 20, 50), pts, 2)

# --- Background ---
_bg_cache = {}
def build_background_cache(level=1):
    if level in _bg_cache:
        return
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    if level == 1:
        nebulas = [
            (WIDTH * 0.3, HEIGHT * 0.4, (60, 10, 120), 350),
            (WIDTH * 0.7, HEIGHT * 0.6, (120, 10, 70), 300),
            (WIDTH * 0.5, HEIGHT * 0.3, (10, 30, 110), 280),
        ]
    elif level == 2:
        nebulas = [
            (WIDTH * 0.3, HEIGHT * 0.4, (120, 60, 10), 350),
            (WIDTH * 0.7, HEIGHT * 0.6, (120, 10, 30), 300),
            (WIDTH * 0.5, HEIGHT * 0.3, (80, 40, 10), 280),
        ]
    elif level == 3:
        nebulas = [
            (WIDTH * 0.3, HEIGHT * 0.4, (10, 100, 60), 350),
            (WIDTH * 0.7, HEIGHT * 0.6, (10, 60, 120), 300),
            (WIDTH * 0.5, HEIGHT * 0.3, (80, 10, 100), 280),
        ]
    else:
        nebulas = [
            (WIDTH * 0.3, HEIGHT * 0.4, (120, 10, 100), 350),
            (WIDTH * 0.7, HEIGHT * 0.6, (30, 10, 120), 300),
            (WIDTH * 0.5, HEIGHT * 0.3, (100, 10, 60), 280),
        ]
    for (nx, ny, color, size) in nebulas:
        neb_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        for r in range(10, 0, -1):
            alpha = int(15 * (1 - r / 10))
            if alpha <= 0:
                continue
            radius = size * r // 10
            pygame.draw.circle(neb_surf, (*color, alpha), (size, size), radius)
        surf.blit(neb_surf, (nx - size, ny - size), special_flags=pygame.BLEND_ADD)
    cx, cy = -60, HEIGHT - 40
    for r in range(240, 180, -3):
        alpha = int((240 - r) * 1.0)
        pygame.draw.circle(surf, (min(60 + alpha, 130), 15, min(100 + alpha, 180)),
                           (cx, cy), r, 1)
    pygame.draw.circle(surf, (35, 8, 65), (cx, cy), 180)
    pygame.draw.circle(surf, NEON_PURPLE, (cx, cy), 180, 2)
    for i in range(3):
        y_offset = cy - 60 + i * 60
        pygame.draw.arc(surf, (80, 30, 140),
                        (cx - 170, y_offset - 30, 340, 60), 0, math.pi, 1)
    _bg_cache[level] = surf

for lvl in range(1, 5):
    build_background_cache(lvl)

def draw_background(surface, level):
    lvl = min(level, 4)
    if lvl in _bg_cache:
        surface.blit(_bg_cache[lvl], (0, 0))

# --- HUD ---
def draw_ui_top(surface, player, level, boss=None):
    bar_surf = pygame.Surface((WIDTH, 70), pygame.SRCALPHA)
    for y in range(70):
        alpha = min(255, int(220 * (1 - y / 70)) + 80)
        pygame.draw.line(bar_surf, (10, 5, 25, alpha), (0, y), (WIDTH, y))
    surface.blit(bar_surf, (0, 0))
    pygame.draw.line(surface, NEON_PURPLE, (0, 70), (WIDTH, 70), 2)
    pygame.draw.line(surface, NEON_PINK, (0, 72), (WIDTH, 72), 1)
    draw_text(surface, "SCORE", 16, 25, 12, NEON_CYAN)
    draw_text(surface, f"{player.display_score:06d}", 36, 25, 30, WHITE, glow=True)
    hs = highscore[0]
    draw_text(surface, "HIGH", 14, WIDTH // 2 - 60, 12, NEON_YELLOW)
    draw_text(surface, f"{max(hs, player.score):06d}", 22, WIDTH // 2 - 60, 30, NEON_YELLOW)
    draw_text(surface, f"LVL {level}", 18, WIDTH // 2 + 80, 12, NEON_GREEN)
    draw_text(surface, f"BOSS {boss_kills[0]}", 14, WIDTH // 2 + 80, 32, NEON_MAGENTA)
    if player.combo > 1:
        combo_color = NEON_GREEN if player.combo < 5 else NEON_YELLOW if player.combo < 10 else NEON_PINK
        scale = 1 + math.sin(pygame.time.get_ticks() / 100) * 0.1
        draw_text(surface, f"x{player.combo} COMBO", int(22 * scale), WIDTH // 2 + 180, 30,
                  combo_color, center=True, glow=True)
    draw_text(surface, "LIVES", 16, WIDTH - 260, 12, NEON_CYAN)
    for i in range(5):
        x = WIDTH - 250 + i * 42
        if i < player.lives:
            draw_heart(surface, x, 40, 13, filled=True)
        else:
            draw_heart(surface, x, 40, 13, filled=False)
    if boss and not boss.entering:
        bar_w = 600
        bar_x = WIDTH // 2 - bar_w // 2
        bar_y = 90
        pygame.draw.rect(surface, (40, 10, 30), (bar_x - 2, bar_y - 2, bar_w + 4, 24))
        pygame.draw.rect(surface, (60, 10, 40), (bar_x, bar_y, bar_w, 20))
        ratio = max(0, boss.hp / boss.max_hp)
        pygame.draw.rect(surface, NEON_MAGENTA, (bar_x, bar_y, int(bar_w * ratio), 20))
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, 20), 2)
        draw_text(surface, f"BOSS #{boss.spawn_count + 1}", 16, bar_x - 100, bar_y + 4, NEON_MAGENTA)
        draw_text(surface, f"{boss.hp}/{boss.max_hp}", 14, bar_x + bar_w + 10, bar_y + 4, WHITE)

def draw_active_powerups(surface, player):
    icon_x = 25
    icon_y = HEIGHT - 30
    if player.power_level > 1:
        ratio = player.power_timer / 480
        pygame.draw.rect(surface, (30, 30, 40), (icon_x - 5, icon_y - 12, 60, 24))
        pygame.draw.rect(surface, NEON_CYAN, (icon_x - 5, icon_y - 12, int(60 * ratio), 24), 1)
        for dx in (-6, 0, 6):
            pygame.draw.line(surface, NEON_CYAN,
                             (icon_x + 25 + dx, icon_y - 6),
                             (icon_x + 25 + dx, icon_y + 6), 2)
        icon_x += 75
    if player.shield > 0:
        ratio = player.shield / 480
        pygame.draw.rect(surface, (30, 30, 40), (icon_x - 5, icon_y - 12, 60, 24))
        pygame.draw.rect(surface, NEON_GREEN, (icon_x - 5, icon_y - 12, int(60 * ratio), 24), 1)
        pts = [
            (icon_x + 25, icon_y - 7),
            (icon_x + 20, icon_y - 3),
            (icon_x + 21, icon_y + 4),
            (icon_x + 25, icon_y + 8),
            (icon_x + 29, icon_y + 4),
            (icon_x + 30, icon_y - 3),
        ]
        pygame.draw.polygon(surface, NEON_GREEN, pts, 1)
        icon_x += 75
    if player.laser_timer > 0:
        ratio = player.laser_timer / 300
        pygame.draw.rect(surface, (30, 30, 40), (icon_x - 5, icon_y - 12, 60, 24))
        pygame.draw.rect(surface, NEON_MAGENTA, (icon_x - 5, icon_y - 12, int(60 * ratio), 24), 1)
        pygame.draw.polygon(surface, NEON_MAGENTA, [
            (icon_x + 25, icon_y - 9),
            (icon_x + 20, icon_y + 3),
            (icon_x + 30, icon_y + 3),
        ])

# --- Achievements Page ---
def show_achievements():
    btn_back = Button(WIDTH // 2, HEIGHT - 55, 240, 55,
                      "BACK", NEON_CYAN, NEON_GREEN, 26)
    while True:
        game_surface.fill(BLACK)
        mouse_pos = get_game_mouse_pos()

        draw_background(game_surface, 3)
        for _ in range(80):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            pygame.draw.circle(game_surface, WHITE, (x, y), 1)

        draw_text(game_surface, "ACHIEVEMENTS", 52, WIDTH // 2, 50,
                  NEON_YELLOW, center=True, glow=True)

        unlocked_count = sum(1 for a in achievements.values() if a['unlocked'])
        total = len(achievements)
        draw_text(game_surface, f"{unlocked_count} / {total}", 26, WIDTH // 2, 95,
                  NEON_CYAN, center=True)

        y_pos = 140
        card_w = 700
        card_h = 50
        for key, a in achievements.items():
            cx = WIDTH // 2 - card_w // 2
            cy = y_pos
            color = NEON_GREEN if a['unlocked'] else (60, 60, 80)
            pygame.draw.rect(game_surface, (10, 5, 25), (cx, cy, card_w, card_h), border_radius=8)
            pygame.draw.rect(game_surface, color, (cx, cy, card_w, card_h), 2, border_radius=8)
            icon_color = NEON_YELLOW if a['unlocked'] else (80, 80, 80)
            draw_text(game_surface, a['icon'], 26, cx + 35, cy + card_h // 2,
                      icon_color, center=True)
            name_color = NEON_YELLOW if a['unlocked'] else (120, 120, 120)
            draw_text(game_surface, a['name'], 20, cx + 70, cy + 6, name_color)
            draw_text(game_surface, a['desc'], 14, cx + 70, cy + 28, (150, 150, 180))
            if a['unlocked']:
                draw_text(game_surface, "[OK]", 16, cx + card_w - 50, cy + card_h // 2,
                          NEON_GREEN, center=True)
            else:
                draw_text(game_surface, "[--]", 16, cx + card_w - 50, cy + card_h // 2,
                          (100, 100, 100), center=True)
            y_pos += card_h + 6

        btn_back.update(mouse_pos)
        btn_back.draw(game_surface)

        present()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
            if btn_back.is_clicked(event):
                return True
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_b):
                return True
        clock.tick(FPS)

# --- History Page (جدید) ---
def show_history():
    btn_back = Button(WIDTH // 2 - 160, HEIGHT - 40, 220, 50,
                      "BACK", NEON_CYAN, NEON_GREEN, 24)
    btn_clear = Button(WIDTH // 2 + 160, HEIGHT - 40, 220, 50,
                       "CLEAR ALL", NEON_RED, NEON_ORANGE, 22)
    scroll_offset = [0]

    while True:
        game_surface.fill(BLACK)
        mouse_pos = get_game_mouse_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        draw_background(game_surface, 4)
        for _ in range(80):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            pygame.draw.circle(game_surface, WHITE, (x, y), 1)

        draw_text(game_surface, "GAME HISTORY", 48, WIDTH // 2, 35,
                  NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, f"Total games: {len(game_history)}", 18, WIDTH // 2, 75,
                  NEON_YELLOW, center=True)

        # اسکرول با wheel
        if len(game_history) > 0:
            # کادر اصلی
            box_x = 60
            box_y = 100
            box_w = WIDTH - 120
            box_h = HEIGHT - 170
            pygame.draw.rect(game_surface, (5, 3, 15), (box_x, box_y, box_w, box_h), border_radius=8)
            pygame.draw.rect(game_surface, NEON_PURPLE, (box_x, box_y, box_w, box_h), 2, border_radius=8)

            # نمایش آیتم‌ها از آخر به اول (جدیدترین بالا)
            item_h = 70
            reversed_history = list(reversed(game_history))

            max_scroll = max(0, len(reversed_history) * item_h - (box_h - 20))
            scroll_offset[0] = max(0, min(scroll_offset[0], max_scroll))

            # clip
            clip_rect = pygame.Rect(box_x + 5, box_y + 5, box_w - 10, box_h - 10)
            old_clip = game_surface.get_clip()
            game_surface.set_clip(clip_rect)

            for i, entry in enumerate(reversed_history):
                iy = box_y + 10 + i * item_h - scroll_offset[0]
                if iy + item_h < box_y or iy > box_y + box_h:
                    continue

                ix = box_x + 15
                iw = box_w - 30

                # رتبه‌بندی رنگ بر اساس امتیاز
                score = entry.get('score', 0)
                if score >= 5000:
                    rank_color = NEON_PINK
                    rank = "S"
                elif score >= 2000:
                    rank_color = NEON_YELLOW
                    rank = "A"
                elif score >= 1000:
                    rank_color = NEON_GREEN
                    rank = "B"
                elif score >= 500:
                    rank_color = NEON_CYAN
                    rank = "C"
                else:
                    rank_color = (150, 150, 180)
                    rank = "D"

                pygame.draw.rect(game_surface, (15, 8, 30), (ix, iy, iw, item_h - 8), border_radius=6)
                pygame.draw.rect(game_surface, rank_color, (ix, iy, iw, item_h - 8), 2, border_radius=6)

                # رتبه بزرگ
                draw_text(game_surface, rank, 36, ix + 35, iy + (item_h - 8) // 2,
                          rank_color, center=True, glow=True)

                # اطلاعات
                draw_text(game_surface, f"SCORE: {score}", 20, ix + 70, iy + 6, WHITE)
                draw_text(game_surface, f"BOSSES: {entry.get('bosses', 0)}   "
                                        f"LEVEL: {entry.get('level', 1)}   "
                                        f"TIME: {entry.get('duration', 0)}s",
                          14, ix + 70, iy + 30, (180, 180, 200))

                # تاریخ
                date_str = entry.get('date', '?')
                draw_text(game_surface, date_str, 14, ix + iw - 200, iy + 6, NEON_CYAN)

                # دستاوردهای این بازی
                new_achs = entry.get('achievements', [])
                if new_achs:
                    ach_str = " ".join(new_achs[:5])
                    if len(new_achs) > 5:
                        ach_str += f" +{len(new_achs) - 5}"
                    draw_text(game_surface, f"* {ach_str}", 12,
                              ix + iw - 200, iy + 30, NEON_YELLOW)

            game_surface.set_clip(old_clip)

            # scrollbar
            if max_scroll > 0:
                sb_x = box_x + box_w - 8
                sb_y = box_y + 10
                sb_h = box_h - 20
                pygame.draw.rect(game_surface, (30, 30, 40), (sb_x, sb_y, 4, sb_h))
                thumb_h = max(20, int(sb_h * (box_h - 20) / (len(reversed_history) * item_h)))
                thumb_y = sb_y + int((sb_h - thumb_h) * (scroll_offset[0] / max_scroll)) if max_scroll > 0 else sb_y
                pygame.draw.rect(game_surface, NEON_CYAN, (sb_x, thumb_y, 4, thumb_h))
        else:
            draw_text(game_surface, "No games played yet", 30, WIDTH // 2, HEIGHT // 2,
                      (150, 150, 180), center=True)
            draw_text(game_surface, "Start a game to see your history here!", 18,
                      WIDTH // 2, HEIGHT // 2 + 40, (100, 100, 130), center=True)

        btn_back.update(mouse_pos)
        btn_back.draw(game_surface)
        if len(game_history) > 0:
            btn_clear.update(mouse_pos)
            btn_clear.draw(game_surface)

        present()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
            if event.type == pygame.MOUSEWHEEL:
                scroll_offset[0] -= event.y * 40
            if btn_back.is_clicked(event):
                return True
            if len(game_history) > 0 and btn_clear.is_clicked(event):
                game_history.clear()
                save_game_async()
                scroll_offset[0] = 0
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_b):
                    return True
                if event.key == pygame.K_UP:
                    scroll_offset[0] -= 40
                if event.key == pygame.K_DOWN:
                    scroll_offset[0] += 40
        clock.tick(FPS)

# --- Settings Page ---
def show_settings():
    global settings

    slider_sfx = Slider(WIDTH // 2, 170, 400, 12, settings['sfx_volume'], 0, 1, "SFX Volume")
    slider_music = Slider(WIDTH // 2, 260, 400, 12, settings['music_volume'], 0, 1, "Music Volume")
    slider_diff = Slider(WIDTH // 2, 350, 400, 12, (settings['difficulty'] - 0.5) / 1.0, 0, 1,
                         "Difficulty")

    btn_shake = Button(WIDTH // 2, 440, 280, 55,
                       "SHAKE: ON" if settings['screen_shake'] else "SHAKE: OFF",
                       NEON_GREEN if settings['screen_shake'] else (100, 100, 100),
                       NEON_CYAN, 22)

    btn_reset = Button(WIDTH // 2 - 130, 520, 220, 50,
                       "RESET SAVE", NEON_RED, NEON_ORANGE, 20)
    btn_back = Button(WIDTH // 2 + 130, 520, 220, 50,
                      "BACK", NEON_CYAN, NEON_GREEN, 22)

    while True:
        game_surface.fill(BLACK)
        mouse_pos = get_game_mouse_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        draw_background(game_surface, 2)
        for _ in range(80):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            pygame.draw.circle(game_surface, WHITE, (x, y), 1)

        box_w, box_h = 700, 580
        box_x = WIDTH // 2 - box_w // 2
        box_y = HEIGHT // 2 - box_h // 2 + 20
        pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h), border_radius=12)
        pygame.draw.rect(game_surface, NEON_PURPLE, (box_x, box_y, box_w, box_h), 3, border_radius=12)
        pygame.draw.rect(game_surface, NEON_PINK, (box_x + 5, box_y + 5, box_w - 10, box_h - 10), 1, border_radius=10)

        draw_text(game_surface, "SETTINGS", 50, WIDTH // 2, 60,
                  NEON_CYAN, center=True, glow=True)

        slider_sfx.update(mouse_pos, mouse_pressed)
        slider_music.update(mouse_pos, mouse_pressed)
        slider_diff.update(mouse_pos, mouse_pressed)

        settings['sfx_volume'] = slider_sfx.value
        settings['music_volume'] = slider_music.value
        settings['difficulty'] = 0.5 + slider_diff.value * 1.0
        update_music_volume()

        slider_sfx.draw(game_surface)
        slider_music.draw(game_surface)
        slider_diff.draw(game_surface)

        diff_val = settings['difficulty']
        if diff_val < 0.8:
            diff_label = "EASY"
            diff_color = NEON_GREEN
        elif diff_val < 1.2:
            diff_label = "NORMAL"
            diff_color = NEON_CYAN
        else:
            diff_label = "HARD"
            diff_color = NEON_RED
        draw_text(game_surface, diff_label, 20, WIDTH // 2, 390, diff_color, center=True)

        btn_shake.update(mouse_pos)
        btn_shake.text = "SHAKE: ON" if settings['screen_shake'] else "SHAKE: OFF"
        btn_shake.color = NEON_GREEN if settings['screen_shake'] else (100, 100, 100)
        btn_reset.update(mouse_pos)
        btn_back.update(mouse_pos)
        btn_shake.draw(game_surface)
        btn_reset.draw(game_surface)
        btn_back.draw(game_surface)

        present()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
            if btn_shake.is_clicked(event):
                settings['screen_shake'] = not settings['screen_shake']
                save_game_async()
            if btn_reset.is_clicked(event):
                settings['sfx_volume'] = 0.7
                settings['music_volume'] = 0.5
                settings['difficulty'] = 1.0
                settings['screen_shake'] = True
                for k in achievements:
                    achievements[k]['unlocked'] = False
                highscore[0] = 0
                boss_kills[0] = 0
                game_history.clear()
                save_game_async()
                slider_sfx.value = 0.7
                slider_music.value = 0.5
                slider_diff.value = 0.5
            if btn_back.is_clicked(event):
                save_game_async()
                return True
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_b):
                save_game_async()
                return True
        clock.tick(FPS)

# --- Menu ---
def show_menu():
    menu_time = 0

    btn_start = Button(WIDTH // 2, HEIGHT // 2 + 20, 300, 48,
                       "START GAME", NEON_CYAN, NEON_GREEN, 24)
    btn_history = Button(WIDTH // 2, HEIGHT // 2 + 78, 300, 44,
                         "HISTORY", NEON_BLUE, NEON_CYAN, 22)
    btn_settings = Button(WIDTH // 2, HEIGHT // 2 + 132, 300, 44,
                          "SETTINGS", NEON_PURPLE, NEON_PINK, 22)
    btn_achievements = Button(WIDTH // 2, HEIGHT // 2 + 186, 300, 44,
                              "ACHIEVEMENTS", NEON_YELLOW, NEON_ORANGE, 22)
    btn_quit = Button(WIDTH // 2, HEIGHT // 2 + 240, 300, 42,
                      "QUIT", NEON_RED, NEON_ORANGE, 20)

    while True:
        game_surface.fill(BLACK)
        t = pygame.time.get_ticks() / 1000
        menu_time += 1
        mouse_pos = get_game_mouse_pos()

        draw_background(game_surface, 1)
        for _ in range(100):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            pygame.draw.circle(game_surface, WHITE, (x, y), 1)

        title_y = 60 + math.sin(t * 2) * 8
        for offset in range(8, 0, -2):
            alpha = 255 // (offset // 2 + 1)
            draw_text(game_surface, "NEON SPACE", 62, WIDTH // 2 + offset, title_y + offset,
                      (alpha // 3, 0, alpha), center=True)
        draw_text(game_surface, "NEON SPACE", 62, WIDTH // 2, title_y, NEON_PINK,
                  center=True, glow=True)

        for offset in range(8, 0, -2):
            alpha = 255 // (offset // 2 + 1)
            draw_text(game_surface, "SHOOTER", 62, WIDTH // 2 + offset, title_y + 58 + offset,
                      (0, alpha // 3, alpha), center=True)
        draw_text(game_surface, "SHOOTER", 62, WIDTH // 2, title_y + 58, NEON_CYAN,
                  center=True, glow=True)

        draw_text(game_surface, "ULTIMATE EDITION", 14, WIDTH // 2, title_y + 115,
                  (200, 200, 100), center=True, glow=True)

        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 20, WIDTH // 2, title_y + 155,
                      NEON_YELLOW, center=True)
        draw_text(game_surface, f"TOTAL GAMES: {len(game_history)}   BOSSES: {boss_kills[0]}",
                  14, WIDTH // 2, title_y + 180, NEON_MAGENTA, center=True)

        for b in [btn_start, btn_history, btn_settings, btn_achievements, btn_quit]:
            b.update(mouse_pos)
            b.draw(game_surface)

        draw_text(game_surface, "Arrows / A D to Move   |   SPACE to Shoot   |   P to Pause",
                  13, WIDTH // 2, HEIGHT - 25, (150, 150, 180), center=True)

        if menu_time % 4 == 0:
            p = None
            for pp in particle_pool:
                if not pp.active:
                    p = pp
                    break
            if p is None:
                p = Particle()
                particle_pool.append(p)
            p.spawn(random.randint(0, WIDTH), random.randint(0, HEIGHT),
                    random.choice([NEON_PINK, NEON_CYAN, NEON_PURPLE]),
                    0.5, 1, 2, gravity=-0.02)
            active_particles.append(p)
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

# --- Resize ---
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
    screen.fill(BLACK)
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
    scale = screen_scale[0]
    ox = screen_offset_x[0]
    oy = screen_offset_y[0]
    return ((mx - ox) / scale, (my - oy) / scale)

# --- Main ---
def main():
    while True:
        result = show_menu()
        if result == 'quit':
            break
        elif result == 'start':
            play_game()
    pygame.quit()

def play_game():
    global boss_kills

    player = Player()
    meteors = []
    powerups = []
    boss = None
    stars = [Star() for _ in range(150)]

    meteor_timer = 0
    powerup_timer = 0
    game_time_frames = 0
    screen_shake = 0
    flash_alpha = 0
    level = 1
    next_boss_score = 500
    boss_alert_timer = 0
    paused = False
    boss_spawn_count = 0
    bosses_this_game = 0

    # برای ذخیره در history
    new_achievements_this_game = []

    running = True
    game_over = False
    final_score = 0
    game_saved = False

    btn_resume = Button(WIDTH // 2, HEIGHT // 2 + 20, 300, 60,
                        "RESUME", NEON_GREEN, NEON_CYAN, 28)
    btn_quit_pause = Button(WIDTH // 2, HEIGHT // 2 + 100, 300, 55,
                            "MAIN MENU", NEON_RED, NEON_ORANGE, 24)

    btn_restart = Button(WIDTH // 2, HEIGHT // 2 + 70, 300, 60,
                         "RESTART", NEON_CYAN, NEON_GREEN, 28)
    btn_menu = Button(WIDTH // 2, HEIGHT // 2 + 145, 300, 55,
                      "MAIN MENU", NEON_YELLOW, NEON_ORANGE, 24)

    ach_notifications = []

    active_particles.clear()
    for p in particle_pool:
        p.active = False

    go_anim = 0

    start_music()

    # ثبت دستاورد به تاریخچه
    def try_unlock(key):
        if unlock_achievement(key):
            new_achievements_this_game.append(achievements[key]['name'])
            ach_notifications.append({'ach': achievements[key], 'timer': 180})
            return True
        return False

    while running:
        clock.tick(FPS)
        t = pygame.time.get_ticks() / 1000
        mouse_pos = get_game_mouse_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_music()
                # ذخیره اگه بازی تموم نشده
                if not game_saved:
                    save_current_game(player, bosses_this_game, game_time_frames,
                                      level, new_achievements_this_game)
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)

            if paused and not game_over:
                if btn_resume.is_clicked(event):
                    paused = False
                if btn_quit_pause.is_clicked(event):
                    stop_music()
                    if not game_saved:
                        save_current_game(player, bosses_this_game, game_time_frames,
                                          level, new_achievements_this_game)
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
                    player.shoot()
                if event.key == pygame.K_p and not game_over:
                    paused = not paused
                if event.key == pygame.K_r and game_over:
                    stop_music()
                    play_game()
                    return
                if event.key == pygame.K_ESCAPE:
                    stop_music()
                    if not game_saved:
                        save_current_game(player, bosses_this_game, game_time_frames,
                                          level, new_achievements_this_game)
                    return

        for notif in ach_notifications[:]:
            notif['timer'] -= 1
            if notif['timer'] <= 0:
                ach_notifications.remove(notif)

        if paused and not game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            game_surface.blit(overlay, (0, 0))
            box_w, box_h = 420, 260
            box_x = WIDTH // 2 - box_w // 2
            box_y = HEIGHT // 2 - box_h // 2
            pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h))
            pygame.draw.rect(game_surface, NEON_CYAN, (box_x, box_y, box_w, box_h), 3)
            pygame.draw.rect(game_surface, NEON_PURPLE, (box_x + 5, box_y + 5, box_w - 10, box_h - 10), 1)
            draw_text(game_surface, "PAUSED", 60, WIDTH // 2, box_y + 60,
                      NEON_CYAN, center=True, glow=True)
            btn_resume.update(mouse_pos)
            btn_quit_pause.update(mouse_pos)
            btn_resume.draw(game_surface)
            btn_quit_pause.draw(game_surface)
            present()
            continue

        if not game_over:
            game_time_frames += 1
            if game_time_frames >= FPS * 120:
                try_unlock('survive_2min')

            keys = pygame.key.get_pressed()
            player.move(keys)
            player.update()
            if keys[pygame.K_SPACE]:
                player.shoot()

            speed_mult = settings['difficulty'] * (1 + (level - 1) * 0.15)
            for s in stars:
                s.update(speed_mult)

            base_spawn = 50 - (level - 1) * 5
            base_spawn = max(12, base_spawn)
            spawn_rate = max(8, int(base_spawn / settings['difficulty']))
            meteor_timer += 1
            if meteor_timer > spawn_rate and boss is None:
                meteors.append(Meteor(speed_mult=(1 + (level - 1) * 0.2) * settings['difficulty']))
                meteor_timer = 0

            powerup_timer += 1
            if powerup_timer > 420:
                powerups.append(PowerUp())
                powerup_timer = 0

            if player.score >= next_boss_score and boss is None:
                boss = Boss(level, boss_spawn_count)
                boss_alert_timer = 120
                play_sound('boss_alert')
                next_boss_score += 500 + level * 200
                boss_spawn_count += 1

            if boss_alert_timer > 0:
                boss_alert_timer -= 1

            if boss:
                boss.update(player)
                if player.invincible == 0 and player.shield == 0:
                    for bb in boss.bullets[:]:
                        dist = math.hypot(bb.x - player.x, bb.y - player.y)
                        if dist < bb.radius + 20:
                            boss.bullets.remove(bb)
                            player.lives -= 1
                            player.invincible = 90
                            player.combo = 0
                            if settings['screen_shake']:
                                screen_shake = 15
                            flash_alpha = 120
                            play_sound('hit')
                            spawn_particles(bb.x, bb.y, NEON_RED, 20, 1.5)
                            if player.lives <= 0:
                                game_over = True
                                final_score = player.score
                                highscore[0] = max(highscore[0], player.score)
                                if player.score >= 500: try_unlock('score_500')
                                if player.score >= 2000: try_unlock('score_2000')
                                if player.score >= 5000: try_unlock('score_5000')
                                save_current_game(player, bosses_this_game, game_time_frames,
                                                  level, new_achievements_this_game)
                                game_saved = True
                                play_sound('gameover')
                                go_anim = 0
                for b in player.bullets[:]:
                    dist = math.hypot(b.x - boss.x, b.y - boss.y)
                    if dist < boss.size + b.radius:
                        if b in player.bullets:
                            player.bullets.remove(b)
                        boss.hp -= b.damage
                        spawn_particles(b.x, b.y, NEON_MAGENTA, 5, 0.8)
                        if boss.hp <= 0:
                            for _ in range(80):
                                spawn_particles(
                                    boss.x + random.randint(-60, 60),
                                    boss.y + random.randint(-40, 40),
                                    random.choice([NEON_MAGENTA, NEON_PINK, NEON_YELLOW]),
                                    count=2, speed_mult=1.5, size_mult=1.5, life_mult=1.5
                                )
                            if settings['screen_shake']:
                                screen_shake = 25
                            flash_alpha = 200
                            player.score += 300
                            boss_kills[0] += 1
                            bosses_this_game += 1
                            play_sound('big_explosion')
                            try_unlock('boss_kill')
                            if boss_kills[0] >= 3:
                                try_unlock('boss_3')
                            boss = None
                            level += 1
                            if level <= 4:
                                build_background_cache(level)
                            break
                for l in player.lasers[:]:
                    dist = math.hypot(l.x - boss.x, l.y - boss.y)
                    if dist < boss.size:
                        boss.hp -= 1
                        if boss.hp <= 0:
                            for _ in range(80):
                                spawn_particles(
                                    boss.x + random.randint(-60, 60),
                                    boss.y + random.randint(-40, 40),
                                    random.choice([NEON_MAGENTA, NEON_PINK, NEON_YELLOW]),
                                    count=2, speed_mult=1.5, size_mult=1.5, life_mult=1.5
                                )
                            if settings['screen_shake']:
                                screen_shake = 25
                            flash_alpha = 200
                            player.score += 300
                            boss_kills[0] += 1
                            bosses_this_game += 1
                            play_sound('big_explosion')
                            try_unlock('boss_kill')
                            if boss_kills[0] >= 3:
                                try_unlock('boss_3')
                            boss = None
                            level += 1
                            if level <= 4:
                                build_background_cache(level)
                            break

            for m in meteors[:]:
                m.update(speed_mult)
                if player.invincible == 0 and player.shield == 0:
                    dist = math.hypot(m.x - player.x, m.y - player.y)
                    if dist < m.size + 22:
                        meteors.remove(m)
                        player.lives -= 1
                        player.invincible = 90
                        player.combo = 0
                        if settings['screen_shake']:
                            screen_shake = 18
                        flash_alpha = 150
                        play_sound('hit')
                        spawn_particles(m.x, m.y, NEON_RED, 35, 1.8, 1.2, 1.2)
                        if player.lives <= 0:
                            game_over = True
                            final_score = player.score
                            highscore[0] = max(highscore[0], player.score)
                            if player.score >= 500: try_unlock('score_500')
                            if player.score >= 2000: try_unlock('score_2000')
                            if player.score >= 5000: try_unlock('score_5000')
                            save_current_game(player, bosses_this_game, game_time_frames,
                                              level, new_achievements_this_game)
                            game_saved = True
                            play_sound('gameover')
                            go_anim = 0
                elif player.shield > 0:
                    dist = math.hypot(m.x - player.x, m.y - player.y)
                    if dist < m.size + 30:
                        meteors.remove(m)
                        player.score += m.score_value
                        if settings['screen_shake']:
                            screen_shake = 8
                        spawn_particles(m.x, m.y, NEON_GREEN, 20, 1.5)
                        play_sound('explosion')
                if m.y > HEIGHT + 60:
                    meteors.remove(m)

            for b in player.bullets[:]:
                for m in meteors[:]:
                    dist = math.hypot(b.x - m.x, b.y - m.y)
                    if dist < m.size + b.radius:
                        if b in player.bullets:
                            player.bullets.remove(b)
                        m.hp -= b.damage
                        if m.hp <= 0:
                            if m in meteors:
                                meteors.remove(m)
                            player.combo += 1
                            player.combo_timer = 90
                            player.max_combo = max(player.max_combo, player.combo)
                            combo_mult = 1 + (player.combo - 1) * 0.1
                            gained = int(m.score_value * combo_mult)
                            player.score += gained
                            try_unlock('first_blood')
                            if player.max_combo >= 5:
                                try_unlock('combo_5')
                            if player.max_combo >= 10:
                                try_unlock('combo_10')
                            if m.size_type == 'large':
                                play_sound('big_explosion')
                                if settings['screen_shake']:
                                    screen_shake = 12
                                spawn_particles(m.x, m.y, NEON_PINK, 45, 2.0, 1.4, 1.3)
                                spawn_particles(m.x, m.y, NEON_YELLOW, 20, 1.5)
                            else:
                                play_sound('explosion')
                                spawn_particles(m.x, m.y, m.color, 22, 1.2)
                                spawn_particles(m.x, m.y, NEON_YELLOW, 8, 1.5)
                            if player.combo > 1:
                                play_sound('combo')
                        else:
                            spawn_particles(b.x, b.y, NEON_YELLOW, 6, 0.8)
                        break

            for l in player.lasers[:]:
                for m in meteors[:]:
                    dist = math.hypot(l.x - m.x, l.y - m.y)
                    if dist < m.size + l.width:
                        m.hp -= 1
                        if m.hp <= 0:
                            if m in meteors:
                                meteors.remove(m)
                            player.score += m.score_value
                            spawn_particles(m.x, m.y, NEON_MAGENTA, 30, 1.5)
                            play_sound('explosion')

            for p in powerups[:]:
                p.update()
                dist = math.hypot(p.x - player.x, p.y - player.y)
                if dist < p.radius + 25:
                    play_sound('powerup')
                    spawn_particles(p.x, p.y, NEON_GREEN, 20, 1.2)
                    if p.type == 'multi':
                        player.power_level = min(3, player.power_level + 1)
                        player.power_timer = 480
                    elif p.type == 'life':
                        player.lives = min(5, player.lives + 1)
                    elif p.type == 'shield':
                        player.shield = 480
                    elif p.type == 'score':
                        player.score += 150
                    elif p.type == 'laser':
                        player.laser_timer = 300
                        play_sound('laser')
                    powerups.remove(p)
                elif p.y > HEIGHT + 30:
                    powerups.remove(p)

            for part in active_particles[:]:
                part.update()
                if not part.active:
                    active_particles.remove(part)

            if screen_shake > 0:
                screen_shake -= 1
            if flash_alpha > 0:
                flash_alpha -= 8

        # --- رسم ---
        game_surface.fill(BLACK)
        draw_background(game_surface, min(level, 4))
        for s in stars:
            s.draw(game_surface)

        offset_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        offset_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0

        game_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for part in active_particles:
            part.draw(game_layer)
        for m in meteors:
            m.draw(game_layer)
        for p in powerups:
            p.draw(game_layer)
        if boss:
            boss.draw(game_layer)
        if not game_over:
            player.draw(game_layer)
        game_surface.blit(game_layer, (offset_x, offset_y))

        if flash_alpha > 0:
            flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((255, 50, 50, flash_alpha))
            game_surface.blit(flash_surf, (0, 0))

        if boss_alert_timer > 0:
            alpha = abs(math.sin(boss_alert_timer / 10)) * 200
            warn = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            warn.fill((255, 0, 100, int(alpha)))
            game_surface.blit(warn, (0, 0))
            draw_text(game_surface, "!! BOSS INCOMING !!", 60, WIDTH // 2, HEIGHT // 2,
                      WHITE, center=True, glow=True)

        draw_ui_top(game_surface, player, level, boss)
        draw_active_powerups(game_surface, player)

        for i, notif in enumerate(ach_notifications):
            ny = 130 + i * 70
            alpha = min(255, notif['timer'] * 2)
            ach = notif['ach']
            notif_surf = pygame.Surface((360, 60), pygame.SRCALPHA)
            notif_surf.fill((10, 5, 25, min(220, alpha)))
            game_surface.blit(notif_surf, (WIDTH - 380, ny))
            pygame.draw.rect(game_surface, NEON_YELLOW, (WIDTH - 380, ny, 360, 60), 2)
            draw_text(game_surface, "ACHIEVEMENT UNLOCKED!", 14, WIDTH - 360, ny + 5, NEON_YELLOW)
            draw_text(game_surface, ach['name'], 20, WIDTH - 360, ny + 25, WHITE, glow=True)

        if game_over:
            go_anim += 1
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            game_surface.blit(overlay, (0, 0))
            box_w, box_h = 520, 420
            box_x = WIDTH // 2 - box_w // 2
            box_y = HEIGHT // 2 - box_h // 2
            pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h))
            pygame.draw.rect(game_surface, NEON_PINK, (box_x, box_y, box_w, box_h), 3)
            pygame.draw.rect(game_surface, NEON_CYAN, (box_x + 5, box_y + 5, box_w - 10, box_h - 10), 1)
            draw_text(game_surface, "GAME OVER", 60, WIDTH // 2, box_y + 55,
                      NEON_RED, center=True, glow=True)
            draw_text(game_surface, f"SCORE: {final_score}", 34,
                      WIDTH // 2, box_y + 120, WHITE, center=True)
            hs = highscore[0]
            if final_score >= hs and final_score > 0:
                draw_text(game_surface, "* NEW HIGH SCORE! *", 24,
                          WIDTH // 2, box_y + 165, NEON_YELLOW, center=True, glow=True)
            else:
                draw_text(game_surface, f"HIGH SCORE: {hs}", 20,
                          WIDTH // 2, box_y + 165, NEON_YELLOW, center=True)

            # خلاصه
            draw_text(game_surface, f"BOSSES: {bosses_this_game}   "
                                    f"LEVEL: {level}   "
                                    f"TIME: {game_time_frames // FPS}s",
                      16, WIDTH // 2, box_y + 195, NEON_CYAN, center=True)
            if new_achievements_this_game:
                draw_text(game_surface, f"NEW: {len(new_achievements_this_game)} achievement(s)!",
                          16, WIDTH // 2, box_y + 220, NEON_YELLOW, center=True)

            if go_anim > 15:
                btn_restart.update(mouse_pos)
                btn_menu.update(mouse_pos)
                btn_restart.draw(game_surface)
                btn_menu.draw(game_surface)

        present()

    stop_music()

def save_current_game(player, bosses, frames, level_reached, new_achs):
    """ذخیره‌ی بازی در تاریخچه"""
    duration = frames // FPS
    add_game_to_history(player.score, bosses, duration, level_reached, new_achs)

if __name__ == "__main__":
    main()