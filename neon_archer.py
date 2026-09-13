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

BASE_W, BASE_H = 1100, 700
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("NEON ARCHER")
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

# --- فیزیک ---
GRAVITY_ARROW = 0.25
GROUND_Y = HEIGHT - 100

# --- ذخیره ---
SAVE_FILE = "neon_archer_save.json"
settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'difficulty': 1.0,
    'wind_enabled': True,
    'show_trajectory': True,
    'screen_shake': True,
}
achievements = {
    'first_shot': {'name': 'FIRST SHOT', 'desc': 'Fire your first arrow', 'unlocked': False, 'icon': '>'},
    'first_kill': {'name': 'FIRST BLOOD', 'desc': 'Kill your first enemy', 'unlocked': False, 'icon': '*'},
    'kill_10': {'name': 'ROOKIE', 'desc': 'Kill 10 enemies', 'unlocked': False, 'icon': '**'},
    'kill_50': {'name': 'VETERAN', 'desc': 'Kill 50 enemies', 'unlocked': False, 'icon': '***'},
    'kill_100': {'name': 'LEGEND', 'desc': 'Kill 100 enemies', 'unlocked': False, 'icon': '****'},
    'headshot_1': {'name': 'HEADSHOT!', 'desc': 'Get a headshot', 'unlocked': False, 'icon': 'H'},
    'headshot_10': {'name': 'MARKSMAN', 'desc': 'Get 10 headshots', 'unlocked': False, 'icon': 'HH'},
    'headshot_30': {'name': 'SNIPER', 'desc': 'Get 30 headshots', 'unlocked': False, 'icon': 'HHH'},
    'wave_5': {'name': 'SURVIVOR', 'desc': 'Reach wave 5', 'unlocked': False, 'icon': 'W5'},
    'wave_10': {'name': 'DEFENDER', 'desc': 'Reach wave 10', 'unlocked': False, 'icon': 'W10'},
    'wave_15': {'name': 'CHAMPION', 'desc': 'Reach wave 15', 'unlocked': False, 'icon': 'W15'},
    'combo_5': {'name': 'COMBO KING', 'desc': 'Reach 5x combo', 'unlocked': False, 'icon': 'C5'},
    'combo_10': {'name': 'COMBO GOD', 'desc': 'Reach 10x combo', 'unlocked': False, 'icon': 'C10'},
    'fire_arrow': {'name': 'PYROMANIAC', 'desc': 'Use fire arrows', 'unlocked': False, 'icon': 'F'},
    'explosive': {'name': 'BOOM!', 'desc': 'Use explosive arrows', 'unlocked': False, 'icon': 'B'},
}
highscore = [0]
game_history = []
total_kills = [0]
total_headshots = [0]
total_waves = [0]


def load_save():
    global settings, achievements, highscore, game_history, total_kills, total_headshots, total_waves
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
            total_headshots[0] = data.get('total_headshots', 0)
            total_waves[0] = data.get('total_waves', 0)
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
                'total_headshots': total_headshots[0],
                'total_waves': total_waves[0],
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
    sounds['bow_draw'] = make_sound(200, 400, 0.3, 0.12, 'saw')
    sounds['shoot'] = make_sound(800, 400, 0.15, 0.18, 'saw')
    sounds['hit'] = make_sound(400, 100, 0.1, 0.20, 'square')
    sounds['kill'] = make_sound(600, 200, 0.25, 0.25, 'saw')
    sounds['headshot'] = make_sound(1200, 2000, 0.3, 0.30, 'sine')
    sounds['explode'] = make_sound(300, 50, 0.5, 0.35, 'noise')
    sounds['wave_start'] = make_sound(400, 800, 0.4, 0.25, 'sine')
    sounds['wave_clear'] = make_sound(600, 1500, 0.6, 0.28, 'sine')
    sounds['damage'] = make_sound(200, 60, 0.3, 0.28, 'noise')
    sounds['gameover'] = make_sound(500, 60, 1.2, 0.30, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['buy'] = make_sound(800, 1500, 0.3, 0.22, 'sine')
    sounds['boss'] = make_sound(150, 400, 1.0, 0.28, 'saw')

    bass = [82.4, 82.4, 73.4, 73.4, 65.4, 65.4, 82.4, 82.4]
    lead = [659, 784, 880, 784, 659, 587, 523, 587]
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

    def spawn(self, x, y, color, speed_mult=1.0, size_mult=1.0, life_mult=1.0, gravity=0.3):
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
#                    تیر
# ============================================================
class Arrow:
    def __init__(self, x, y, vx, vy, arrow_type='normal', owner='player'):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.arrow_type = arrow_type
        self.owner = owner
        self.life = 240
        self.angle = math.degrees(math.atan2(vy, vx))
        self.trail = []
        self.stuck = False
        self.stuck_timer = 0

        if arrow_type == 'normal':
            self.color = NEON_YELLOW
            self.damage = 25
        elif arrow_type == 'fire':
            self.color = NEON_ORANGE
            self.damage = 40
        elif arrow_type == 'ice':
            self.color = NEON_CYAN
            self.damage = 20
        elif arrow_type == 'explosive':
            self.color = NEON_RED
            self.damage = 30
        else:
            self.color = NEON_YELLOW
            self.damage = 25

    def update(self, wind=0):
        if self.stuck:
            self.stuck_timer += 1
            if self.stuck_timer > 120:
                self.life = 0
            return

        self.trail.append((self.x, self.y))
        if len(self.trail) > 10:
            self.trail.pop(0)

        self.vy += GRAVITY_ARROW
        self.vx += wind * 0.01
        self.x += self.vx
        self.y += self.vy
        self.angle = math.degrees(math.atan2(self.vy, self.vx))
        self.life -= 1

        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.stuck = True
            if self.arrow_type == 'explosive':
                self.explode()

    def explode(self):
        self.life = 0
        play_sound('explode')
        for _ in range(40):
            spawn_particles(self.x, self.y, NEON_ORANGE, 1, 2.5, 2.0, 1.5)
        for _ in range(20):
            spawn_particles(self.x, self.y, NEON_YELLOW, 1, 1.5, 1.5, 1.2)

    def draw(self, surface):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / len(self.trail) * 0.5
            r = max(1, int(3 * alpha))
            c = tuple(int(c1 * alpha) for c1 in self.color)
            pygame.draw.circle(surface, c, (int(tx), int(ty)), r)

        rad = math.radians(self.angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        length = 20

        tip_x = self.x + cos_a * length
        tip_y = self.y + sin_a * length
        tail_x = self.x - cos_a * length * 0.3
        tail_y = self.y - sin_a * length * 0.3

        for r in range(3, 0, -1):
            pygame.draw.line(surface, (*self.color, 40),
                             (tail_x, tail_y), (tip_x, tip_y), 4 + r * 2)

        pygame.draw.line(surface, self.color, (tail_x, tail_y), (tip_x, tip_y), 3)
        pygame.draw.line(surface, WHITE, (tail_x, tail_y), (tip_x, tip_y), 1)
        pygame.draw.circle(surface, WHITE, (int(tip_x), int(tip_y)), 3)

        perp = rad + math.pi / 2
        for side in [-1, 1]:
            fx = tail_x + math.cos(perp) * 5 * side
            fy = tail_y + math.sin(perp) * 5 * side
            pygame.draw.line(surface, self.color, (tail_x, tail_y), (fx, fy), 2)


# ============================================================
#                    دشمنان
# ============================================================
class Enemy:
    def __init__(self, x, y, kind='soldier', wave=1):
        self.x = x
        self.y = y
        self.kind = kind
        self.vx = 0
        self.vy = 0
        self.hit_flash = 0
        self.anim_time = 0
        self.alive = True
        self.frozen = 0

        if kind == 'soldier':
            self.w = 30
            self.h = 55
            self.hp = 30 + wave * 5
            self.max_hp = self.hp
            self.speed = 1.5 + wave * 0.1
            self.color = NEON_RED
            self.score_value = 100
        elif kind == 'archer':
            self.w = 28
            self.h = 50
            self.hp = 25 + wave * 4
            self.max_hp = self.hp
            self.speed = 1.0 + wave * 0.08
            self.color = NEON_PURPLE
            self.score_value = 150
            self.shoot_timer = random.randint(60, 120)
            self.shoot_interval = 120
        elif kind == 'ninja':
            self.w = 26
            self.h = 48
            self.hp = 20 + wave * 4
            self.max_hp = self.hp
            self.speed = 2.5 + wave * 0.15
            self.color = NEON_MAGENTA
            self.score_value = 200
        elif kind == 'brute':
            self.w = 45
            self.h = 75
            self.hp = 80 + wave * 10
            self.max_hp = self.hp
            self.speed = 1.0 + wave * 0.05
            self.color = NEON_ORANGE
            self.score_value = 300
        elif kind == 'boss':
            self.w = 70
            self.h = 120
            self.hp = 300 + wave * 20
            self.max_hp = self.hp
            self.speed = 0.8
            self.color = NEON_PINK
            self.score_value = 1000
            self.shoot_timer = 60
            self.shoot_interval = 90

        self.update_headshot()

    def update_headshot(self):
        if self.kind == 'boss':
            self.headshot_zone = pygame.Rect(int(self.x - 20), int(self.y - self.h), 40, 30)
        elif self.kind == 'brute':
            self.headshot_zone = pygame.Rect(int(self.x - 15), int(self.y - self.h), 30, 22)
        else:
            self.headshot_zone = pygame.Rect(int(self.x - 10), int(self.y - self.h), 20, 18)

    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h), self.w, self.h)

    def update(self, player_x, wind=0):
        if not self.alive:
            return None

        self.anim_time += 1
        if self.hit_flash > 0:
            self.hit_flash -= 1

        if self.frozen > 0:
            self.frozen -= 1
            self.update_headshot()
            return None

        dx = player_x - self.x
        dist = abs(dx)

        if self.kind in ['soldier', 'ninja', 'brute']:
            # راه رفتن به سمت بازیکن
            direction = 1 if dx > 0 else -1
            self.x += self.speed * direction * 2.5
        elif self.kind == 'archer':
            # کماندار: اگه دور، نزدیک شو؛ اگه نزدیک، دور شو
            if dist > 350:
                self.x += self.speed * (1 if dx > 0 else -1) * 2
            elif dist < 200:
                self.x -= self.speed * (1 if dx > 0 else -1) * 2
            self.shoot_timer += 1
            if self.shoot_timer >= self.shoot_interval:
                self.shoot_timer = 0
                self.update_headshot()
                return 'shoot'
        elif self.kind == 'boss':
            if dist > 200:
                self.x += self.speed * (1 if dx > 0 else -1) * 2
            self.shoot_timer += 1
            if self.shoot_timer >= self.shoot_interval:
                self.shoot_timer = 0
                self.update_headshot()
                return 'shoot'

        self.update_headshot()
        return None

    def take_damage(self, amount, is_headshot=False):
        if is_headshot:
            amount *= 2
        self.hp -= amount
        self.hit_flash = 8
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def freeze(self, duration=180):
        self.frozen = duration

    def draw(self, surface):
        if not self.alive:
            return

        color = WHITE if self.hit_flash > 0 else self.color
        if self.frozen > 0:
            color = NEON_CYAN

        for r in range(3, 0, -1):
            glow = pygame.Surface((self.w * 4, self.h * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*color, 30 - r * 8),
                                (self.w * 2 - r * 5, self.h - r * 5,
                                 self.w + r * 10, self.h + r * 10))
            surface.blit(glow, (self.x - self.w * 2, self.y - self.h * 2 + 20))

        body_rect = pygame.Rect(int(self.x - self.w // 2), int(self.y - self.h + 20),
                                self.w, self.h - 20)
        darker = (color[0] // 3, color[1] // 3, color[2] // 3)
        pygame.draw.rect(surface, darker, body_rect, border_radius=6)
        pygame.draw.rect(surface, color, body_rect, 3, border_radius=6)

        head_size = int(self.w * 0.6)
        head_rect = pygame.Rect(int(self.x - head_size // 2), int(self.y - self.h),
                                head_size, head_size)
        pygame.draw.rect(surface, darker, head_rect, border_radius=5)
        pygame.draw.rect(surface, color, head_rect, 3, border_radius=5)

        eye_color = NEON_YELLOW if self.kind != 'ninja' else NEON_RED
        pygame.draw.circle(surface, eye_color, (int(self.x), int(self.y - self.h + head_size // 2)), 4)
        pygame.draw.circle(surface, WHITE, (int(self.x - 1), int(self.y - self.h + head_size // 2 - 1)), 2)

        if self.kind == 'archer':
            pygame.draw.arc(surface, color, (self.x + 10, self.y - 40, 25, 30),
                            -math.pi / 2, math.pi / 2, 3)
        elif self.kind in ['soldier', 'ninja']:
            pygame.draw.line(surface, (150, 150, 180),
                             (self.x + self.w // 2, self.y - self.h // 2),
                             (self.x + self.w // 2 + 20, self.y - self.h // 2 - 10), 3)
        elif self.kind == 'boss':
            pygame.draw.line(surface, color,
                             (self.x - 30, self.y - self.h + 40),
                             (self.x + 30, self.y - self.h + 40), 5)

        if self.kind in ['brute', 'boss']:
            bar_w = self.w * 1.5
            bar_x = self.x - bar_w / 2
            bar_y = self.y - self.h - 15
            pygame.draw.rect(surface, (40, 10, 10), (bar_x, bar_y, bar_w, 6))
            ratio = self.hp / self.max_hp
            pygame.draw.rect(surface, NEON_RED, (bar_x, bar_y, bar_w * ratio, 6))
            pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, 6), 1)

        if self.frozen > 0:
            draw_text(surface, "*", 16, self.x, self.y - self.h - 25, NEON_CYAN, center=True)


# ============================================================
#                    کماندار (Player)
# ============================================================
class Archer:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = 35
        self.h = 65
        self.angle = 0
        self.power = 0
        self.is_drawing = False
        self.cooldown = 0
        self.anim_time = 0
        self.current_arrow = 'normal'
        self.vx = 0  # برای انیمیشن راه رفتن
        self.walk_phase = 0

    def update(self, mouse_pos, mouse_pressed, keys):
        # ============ حرکت با کلیدها ============
        move_speed = 5
        is_walking = False

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= move_speed
            is_walking = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += move_speed
            is_walking = True

        # محدودیت صفحه
        self.x = max(50, min(WIDTH - 50, self.x))

        # انیمیشن راه رفتن
        if is_walking:
            self.walk_phase += 0.3
        else:
            self.walk_phase = 0

        # ============ نشانه‌گیری ============
        mx, my = mouse_pos
        dx = mx - (self.x + 20)
        dy = my - (self.y - self.h / 2)
        self.angle = math.degrees(math.atan2(dy, dx))

        # ============ کشیدن کمان ============
        if mouse_pressed and self.cooldown == 0:
            self.is_drawing = True
            self.power = min(100, self.power + 4)
        elif not mouse_pressed and self.is_drawing:
            self.is_drawing = False
            arrow = self.shoot()
            self.power = 0
            self.cooldown = 15
            return arrow
        else:
            if not mouse_pressed:
                self.power = 0

        if self.cooldown > 0:
            self.cooldown -= 1

        self.anim_time += 1
        return None

    def shoot(self):
        play_sound('shoot')
        rad = math.radians(self.angle)
        start_x = self.x + 30 + math.cos(rad) * 20
        start_y = self.y - self.h / 2 + math.sin(rad) * 20

        speed = 5 + self.power * 0.18

        vx = math.cos(rad) * speed
        vy = math.sin(rad) * speed

        if self.current_arrow == 'triple':
            arrows = []
            for offset in [-10, 0, 10]:
                a = rad + math.radians(offset)
                arrows.append(Arrow(start_x, start_y,
                                    math.cos(a) * speed, math.sin(a) * speed,
                                    'normal', 'player'))
            return arrows
        else:
            return [Arrow(start_x, start_y, vx, vy, self.current_arrow, 'player')]

    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h), self.w, self.h)

    def draw(self, surface):
        # هاله
        for r in range(3, 0, -1):
            glow = pygame.Surface((self.w * 4, self.h * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*NEON_GREEN, 40 - r * 10),
                                (self.w * 2 - r * 5, self.h - r * 5,
                                 self.w + r * 10, self.h + r * 10))
            surface.blit(glow, (self.x - self.w * 2, self.y - self.h * 2 + 20))

        # انیمیشن راه رفتن
        leg_swing = math.sin(self.walk_phase) * 4 if self.walk_phase > 0 else 0

        # پاها
        pygame.draw.line(surface, NEON_GREEN,
                         (self.x - 5, self.y - 15),
                         (self.x - 5 + leg_swing, self.y), 4)
        pygame.draw.line(surface, NEON_GREEN,
                         (self.x + 5, self.y - 15),
                         (self.x + 5 - leg_swing, self.y), 4)

        # بدن
        body_rect = pygame.Rect(int(self.x - 12), int(self.y - self.h + 20), 24, self.h - 25)
        pygame.draw.rect(surface, (10, 50, 30), body_rect, border_radius=5)
        pygame.draw.rect(surface, NEON_GREEN, body_rect, 2, border_radius=5)

        # سر
        head_rect = pygame.Rect(int(self.x - 10), int(self.y - self.h), 20, 20)
        pygame.draw.rect(surface, (10, 50, 30), head_rect, border_radius=5)
        pygame.draw.rect(surface, NEON_GREEN, head_rect, 2, border_radius=5)

        # چشم جهت‌دار
        rad = math.radians(self.angle)
        eye_x = self.x + math.cos(rad) * 5
        eye_y = self.y - self.h + 10 + math.sin(rad) * 3
        pygame.draw.circle(surface, NEON_YELLOW, (int(eye_x), int(eye_y)), 3)
        pygame.draw.circle(surface, WHITE, (int(eye_x - 1), int(eye_y - 1)), 1)

        # کمان
        bow_rad = math.radians(self.angle)
        bow_x = self.x + math.cos(bow_rad) * 25
        bow_y = self.y - self.h / 2 + math.sin(bow_rad) * 25

        bow_size = 35
        perp = bow_rad + math.pi / 2
        p1x = bow_x + math.cos(perp) * bow_size / 2
        p1y = bow_y + math.sin(perp) * bow_size / 2
        p2x = bow_x - math.cos(perp) * bow_size / 2
        p2y = bow_y - math.sin(perp) * bow_size / 2

        for r in range(3, 0, -1):
            pygame.draw.line(surface, (*NEON_YELLOW, 60 - r * 15),
                             (p1x, p1y), (bow_x, bow_y), 3 + r)
            pygame.draw.line(surface, (*NEON_YELLOW, 60 - r * 15),
                             (bow_x, bow_y), (p2x, p2y), 3 + r)

        pygame.draw.line(surface, NEON_YELLOW, (p1x, p1y), (bow_x, bow_y), 3)
        pygame.draw.line(surface, NEON_YELLOW, (bow_x, bow_y), (p2x, p2y), 3)
        pygame.draw.line(surface, WHITE, (p1x, p1y), (bow_x, bow_y), 1)
        pygame.draw.line(surface, WHITE, (bow_x, bow_y), (p2x, p2y), 1)

        # رشته کمان
        if self.is_drawing:
            pull = self.power * 0.3
            string_x = bow_x - math.cos(bow_rad) * pull
            string_y = bow_y - math.sin(bow_rad) * pull
            pygame.draw.line(surface, WHITE, (p1x, p1y), (string_x, string_y), 2)
            pygame.draw.line(surface, WHITE, (string_x, string_y), (p2x, p2y), 2)
        else:
            pygame.draw.line(surface, WHITE, (p1x, p1y), (p2x, p2y), 2)

        # تیر آماده
        if self.is_drawing:
            arrow_start_x = bow_x
            arrow_start_y = bow_y
            arrow_end_x = bow_x + math.cos(bow_rad) * 25
            arrow_end_y = bow_y + math.sin(bow_rad) * 25
            pygame.draw.line(surface, NEON_YELLOW,
                             (arrow_start_x, arrow_start_y),
                             (arrow_end_x, arrow_end_y), 3)

        # نوار قدرت
        if self.is_drawing:
            bar_w = 60
            bar_h = 8
            bar_x = self.x - bar_w / 2
            bar_y = self.y - self.h - 30
            pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            if self.power < 33:
                power_color = NEON_GREEN
            elif self.power < 66:
                power_color = NEON_YELLOW
            else:
                power_color = NEON_RED
            pygame.draw.rect(surface, power_color,
                             (bar_x, bar_y, bar_w * (self.power / 100), bar_h),
                             border_radius=4)
            pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)


# ============================================================
#                    PowerUp
# ============================================================
class PowerUp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = random.choices(
            ['health', 'fire', 'ice', 'explosive', 'triple', 'money'],
            weights=[3, 3, 2, 2, 2, 4]
        )[0]
        self.radius = 18
        self.pulse = 0
        self.life = 600
        self.vy = 0

    def update(self):
        self.pulse += 0.15
        self.life -= 1
        self.vy += 0.3
        self.y += self.vy
        if self.y > GROUND_Y - 20:
            self.y = GROUND_Y - 20
            self.vy = -self.vy * 0.5

    def draw(self, surface):
        colors_pu = {
            'health': NEON_GREEN,
            'fire': NEON_ORANGE,
            'ice': NEON_CYAN,
            'explosive': NEON_RED,
            'triple': NEON_YELLOW,
            'money': (255, 215, 0),
        }
        icons = {
            'health': '+',
            'fire': 'F',
            'ice': 'I',
            'explosive': 'B',
            'triple': '3',
            'money': '$',
        }
        color = colors_pu[self.type]
        r = self.radius + int(math.sin(self.pulse) * 3)

        for i in range(3, 0, -1):
            glow = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 50 - i * 12), (r * 2, r * 2), r * 1.5)
            surface.blit(glow, (self.x - r * 2, self.y - r * 2))

        pygame.draw.circle(surface, (color[0] // 3, color[1] // 3, color[2] // 3),
                           (int(self.x), int(self.y)), r)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), r, 2)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), r, 1)

        draw_text(surface, icons[self.type], 22, self.x, self.y - 12, WHITE, center=True, bold=True)


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
def build_archer_bg():
    layers = []
    surf1 = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(HEIGHT):
        t = y / HEIGHT
        c = (int(10 + 30 * t), int(5 + 20 * t), int(30 + 50 * t))
        pygame.draw.line(surf1, c, (0, y), (WIDTH, y))
    for _ in range(120):
        x, y = random.randint(0, WIDTH), random.randint(0, HEIGHT // 2)
        b = random.randint(100, 200)
        pygame.draw.circle(surf1, (b, b, b + 50), (x, y), random.choice([1, 1, 2]))
    layers.append({'surf': surf1, 'speed': 0.05})

    surf2 = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(surf2, (200, 150, 220, 200), (900, 150), 70)
    pygame.draw.circle(surf2, (220, 180, 240, 255), (900, 150), 65)
    pygame.draw.circle(surf2, (180, 140, 210, 255), (900, 150), 60)
    for _ in range(10):
        mx = 900 + random.randint(-40, 40)
        my = 150 + random.randint(-40, 40)
        pygame.draw.circle(surf2, (150, 110, 180, 200), (mx, my), random.randint(3, 8))
    for i in range(15):
        bx = i * 80 - 100
        bh = random.randint(80, 180)
        by = GROUND_Y - 50 - bh
        pts = [
            (bx, GROUND_Y - 50),
            (bx + 40, by),
            (bx + 80, GROUND_Y - 50),
        ]
        pygame.draw.polygon(surf2, (20, 15, 50), pts)
    layers.append({'surf': surf2, 'speed': 0.15})

    surf3 = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(20):
        bx = i * 60 - 50
        bh = random.randint(60, 150)
        by = GROUND_Y - bh
        pygame.draw.rect(surf3, (8, 5, 25), (bx, by, 50, bh))
        for _ in range(random.randint(3, 8)):
            wx = bx + random.randint(5, 45)
            wy = by + random.randint(10, bh - 15)
            color = random.choice([NEON_CYAN, NEON_PINK, NEON_PURPLE])
            pygame.draw.rect(surf3, color, (wx, wy, 4, 5))
    layers.append({'surf': surf3, 'speed': 0.3})

    return layers


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

    menu_layers = build_archer_bg()

    while True:
        game_surface.fill(DARK_BG)
        t = pygame.time.get_ticks() / 1000
        menu_time += 1
        mouse_pos = get_game_mouse_pos()

        for layer in menu_layers:
            game_surface.blit(layer['surf'], (0, 0))

        pygame.draw.rect(game_surface, (10, 20, 15), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.line(game_surface, NEON_GREEN, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)

        title_y = 130 + math.sin(t * 2) * 8
        draw_text(game_surface, "NEON", 72, WIDTH // 2 - 100, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "ARCHER", 72, WIDTH // 2 + 120, title_y, NEON_GREEN, center=True, glow=True)
        draw_text(game_surface, "AIM  /  SHOOT  /  SURVIVE", 20, WIDTH // 2, title_y + 65,
                  (200, 200, 220), center=True)

        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 22, WIDTH // 2, title_y + 115,
                      NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, f"KILLS: {total_kills[0]}   HEADSHOTS: {total_headshots[0]}   WAVES: {total_waves[0]}",
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
    btn_wind = Button(WIDTH // 2, 450, 280, 50,
                      f"WIND: {'ON' if settings['wind_enabled'] else 'OFF'}",
                      NEON_GREEN if settings['wind_enabled'] else (100, 100, 100), NEON_CYAN, 22)
    btn_traj = Button(WIDTH // 2, 510, 280, 50,
                      f"TRAJECTORY: {'ON' if settings['show_trajectory'] else 'OFF'}",
                      NEON_GREEN if settings['show_trajectory'] else (100, 100, 100), NEON_CYAN, 22)
    btn_reset = Button(WIDTH // 2 - 130, 580, 220, 50, "RESET SAVE", NEON_RED, NEON_ORANGE, 20)
    btn_back = Button(WIDTH // 2 + 130, 580, 220, 50, "BACK", NEON_CYAN, NEON_GREEN, 22)

    while True:
        game_surface.fill(DARK_BG)
        mouse_pos = get_game_mouse_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((15, 5, 35, alpha))
            game_surface.blit(s, (0, y))
        for _ in range(80):
            pygame.draw.circle(game_surface, (80, 100, 150),
                               (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 1)

        box_w, box_h = 700, 640
        box_x = WIDTH // 2 - box_w // 2
        box_y = HEIGHT // 2 - box_h // 2 + 20
        pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h), border_radius=12)
        pygame.draw.rect(game_surface, NEON_PURPLE, (box_x, box_y, box_w, box_h), 3, border_radius=12)

        draw_text(game_surface, "SETTINGS", 48, WIDTH // 2, 60, NEON_CYAN, center=True, glow=True)

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
        draw_text(game_surface, diff_label, 20, WIDTH // 2, 400, diff_color, center=True)

        btn_wind.update(mouse_pos)
        btn_wind.text = f"WIND: {'ON' if settings['wind_enabled'] else 'OFF'}"
        btn_wind.color = NEON_GREEN if settings['wind_enabled'] else (100, 100, 100)
        btn_wind.draw(game_surface)

        btn_traj.update(mouse_pos)
        btn_traj.text = f"TRAJECTORY: {'ON' if settings['show_trajectory'] else 'OFF'}"
        btn_traj.color = NEON_GREEN if settings['show_trajectory'] else (100, 100, 100)
        btn_traj.draw(game_surface)

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
            if btn_wind.is_clicked(event):
                settings['wind_enabled'] = not settings['wind_enabled']
                save_async()
            if btn_traj.is_clicked(event):
                settings['show_trajectory'] = not settings['show_trajectory']
                save_async()
            if btn_reset.is_clicked(event):
                settings['sfx_volume'] = 0.7
                settings['music_volume'] = 0.5
                settings['difficulty'] = 1.0
                settings['wind_enabled'] = True
                settings['show_trajectory'] = True
                settings['screen_shake'] = True
                for k in achievements:
                    achievements[k]['unlocked'] = False
                highscore[0] = 0
                game_history.clear()
                total_kills[0] = 0
                total_headshots[0] = 0
                total_waves[0] = 0
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
            s.fill((15, 5, 35, alpha))
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
            s.fill((15, 5, 35, alpha))
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
                if score >= 30000:
                    rank_color, rank = NEON_PINK, "S"
                elif score >= 15000:
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
    archer = Archer(200, GROUND_Y)
    arrows = []
    enemy_arrows = []
    enemies = []
    powerups = []

    score = 0
    display_score = 0
    kills = 0
    headshots = 0
    max_combo = 0
    combo = 0
    combo_timer = 0
    total_frames = 0
    wave = 1
    wave_kills_needed = 5
    wave_kills = 0
    wave_banner_timer = 120
    enemies_to_spawn = 0
    spawn_timer = 0
    money = 0

    wind = 0
    wind_change_timer = 0

    screen_shake = 0
    flash = 0
    game_over = False
    paused = False
    final_score = 0
    final_wave = 1
    new_achs = []
    notifications = []
    go_anim = 0
    game_saved = False
    hit_marker_timer = 0
    hit_marker_pos = (0, 0)
    hit_marker_headshot = False

    btn_resume = Button(WIDTH // 2, HEIGHT // 2 + 20, 300, 60, "RESUME", NEON_GREEN, NEON_CYAN, 28)
    btn_pause_menu = Button(WIDTH // 2, HEIGHT // 2 + 100, 300, 55, "MAIN MENU", NEON_RED, NEON_ORANGE, 24)
    btn_restart = Button(WIDTH // 2, HEIGHT // 2 + 70, 300, 60, "RESTART", NEON_CYAN, NEON_GREEN, 28)
    btn_menu = Button(WIDTH // 2, HEIGHT // 2 + 145, 300, 55, "MAIN MENU", NEON_YELLOW, NEON_ORANGE, 24)

    active_particles.clear()
    for p in particle_pool:
        p.active = False

    bg_layers = build_archer_bg()

    start_music()

    def try_unlock(key):
        if unlock_achievement(key):
            new_achs.append(achievements[key]['name'])
            notifications.append({'ach': achievements[key], 'timer': 180})
            return True
        return False

    def save_current():
        add_game_to_history(score, wave, total_frames // FPS, new_achs)

    def spawn_wave():
        nonlocal enemies_to_spawn, wave_kills_needed
        count = 3 + wave
        enemies_to_spawn = count
        wave_kills_needed = count

    def spawn_enemy():
        ex = WIDTH + random.uniform(30, 150)
        choices = ['soldier'] * 5 + ['archer'] * 3 + ['ninja'] * 2
        if wave >= 3:
            choices += ['brute'] * 2
        if wave >= 5 and wave % 5 == 0:
            kind = 'boss'
        else:
            kind = random.choice(choices)
        enemies.append(Enemy(ex, GROUND_Y, kind, wave))

    spawn_wave()

    running = True
    while running:
        clock.tick(FPS)
        t = pygame.time.get_ticks() / 1000
        mouse_pos = get_game_mouse_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        if settings['wind_enabled']:
            wind_change_timer += 1
            if wind_change_timer > 180:
                wind_change_timer = 0
                wind = random.uniform(-3, 3)
        else:
            wind = 0

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
                if not paused and not game_over:
                    if event.key == pygame.K_1:
                        archer.current_arrow = 'normal'
                    if event.key == pygame.K_2:
                        archer.current_arrow = 'fire'
                        try_unlock('fire_arrow')
                    if event.key == pygame.K_3:
                        archer.current_arrow = 'ice'
                    if event.key == pygame.K_4:
                        archer.current_arrow = 'explosive'
                        try_unlock('explosive')
                    if event.key == pygame.K_5:
                        archer.current_arrow = 'triple'

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

        if hit_marker_timer > 0:
            hit_marker_timer -= 1

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

            if display_score < score:
                display_score += max(1, (score - display_score) // 5)
                if display_score > score:
                    display_score = score

            if combo_timer > 0:
                combo_timer -= 1
                if combo_timer == 0:
                    combo = 0

            # آپدیت کماندار
            keys = pygame.key.get_pressed()
            result = archer.update(mouse_pos, mouse_pressed, keys)
            if result:
                if isinstance(result, list):
                    for a in result:
                        arrows.append(a)
                else:
                    arrows.append(result)
                try_unlock('first_shot')

            # آپدیت تیرها
            for a in arrows[:]:
                a.update(wind if settings['wind_enabled'] else 0)
                if a.life <= 0:
                    if a in arrows:
                        arrows.remove(a)
                    continue
                if a.stuck:
                    continue
                hit = False
                for e in enemies[:]:
                    if not e.alive:
                        continue
                    is_headshot = e.headshot_zone.colliderect(pygame.Rect(int(a.x - 5), int(a.y - 5), 10, 10))
                    if e.rect().colliderect(pygame.Rect(int(a.x - 5), int(a.y - 5), 10, 10)) or is_headshot:
                        if e.take_damage(a.damage, is_headshot):
                            kills += 1
                            total_kills[0] += 1
                            wave_kills += 1
                            combo += 1
                            combo_timer = 120
                            max_combo = max(max_combo, combo)
                            combo_mult = 1 + (combo - 1) * 0.15
                            points = int(e.score_value * combo_mult)
                            if is_headshot:
                                headshots += 1
                                total_headshots[0] += 1
                                points *= 2
                                hit_marker_headshot = True
                                play_sound('headshot')
                            else:
                                hit_marker_headshot = False
                                play_sound('kill')
                            score += points
                            money += points // 10
                            hit_marker_timer = 20
                            hit_marker_pos = (e.x, e.y - e.h / 2)
                            for _ in range(30):
                                spawn_particles(e.x, e.y - e.h / 2, e.color, 1, 2.0, 1.5, 1.5)
                            if settings['screen_shake']:
                                screen_shake = 8
                            enemies.remove(e)
                            if kills >= 1: try_unlock('first_kill')
                            if kills >= 10: try_unlock('kill_10')
                            if kills >= 50: try_unlock('kill_50')
                            if kills >= 100: try_unlock('kill_100')
                            if headshots >= 1: try_unlock('headshot_1')
                            if headshots >= 10: try_unlock('headshot_10')
                            if headshots >= 30: try_unlock('headshot_30')
                            if combo >= 5: try_unlock('combo_5')
                            if combo >= 10: try_unlock('combo_10')
                            if random.random() < 0.15:
                                powerups.append(PowerUp(e.x, e.y - 50))
                        else:
                            play_sound('hit')
                            hit_marker_timer = 10
                            hit_marker_headshot = is_headshot
                            hit_marker_pos = (a.x, a.y)
                            for _ in range(8):
                                spawn_particles(a.x, a.y, NEON_YELLOW, 1, 1.5, 1.0, 1.0)

                        if a.arrow_type == 'explosive':
                            a.explode()
                            for other in enemies[:]:
                                if other == e:
                                    continue
                                if math.hypot(other.x - a.x, other.y - other.h / 2 - a.y) < 80:
                                    if other.take_damage(40):
                                        kills += 1
                                        total_kills[0] += 1
                                        wave_kills += 1
                                        score += other.score_value
                                        enemies.remove(other)
                                        for _ in range(20):
                                            spawn_particles(other.x, other.y - other.h / 2, NEON_ORANGE, 1, 1.5, 1.2, 1.2)
                        elif a.arrow_type == 'ice':
                            e.freeze(120)

                        if a in arrows:
                            arrows.remove(a)
                        hit = True
                        break
                if hit:
                    continue

            # آپدیت دشمن‌ها
            for e in enemies[:]:
                action = e.update(archer.x, wind if settings['wind_enabled'] else 0)
                if action == 'shoot':
                    dx = archer.x - e.x
                    dy = archer.y - e.y + 25
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        speed = 7
                        vx = dx / dist * speed
                        vy = dy / dist * speed
                        enemy_arrows.append(Arrow(e.x, e.y - 25, vx, vy, 'normal', 'enemy'))
                        play_sound('shoot')

                if e.rect().colliderect(archer.rect()):
                    if settings['screen_shake']:
                        screen_shake = 20
                    flash = 200
                    game_over = True
                    final_score = score
                    final_wave = wave
                    highscore[0] = max(highscore[0], score)
                    save_current()
                    game_saved = True
                    play_sound('gameover')
                    go_anim = 0

            for a in enemy_arrows[:]:
                a.update(0)
                if a.life <= 0:
                    enemy_arrows.remove(a)
                    continue
                if a.stuck:
                    continue
                if a.owner == 'enemy':
                    if archer.rect().colliderect(pygame.Rect(int(a.x - 5), int(a.y - 5), 10, 10)):
                        if settings['screen_shake']:
                            screen_shake = 15
                        flash = 150
                        game_over = True
                        final_score = score
                        final_wave = wave
                        highscore[0] = max(highscore[0], score)
                        save_current()
                        game_saved = True
                        play_sound('gameover')
                        go_anim = 0
                        enemy_arrows.remove(a)

            for p in powerups[:]:
                p.update()
                if p.life <= 0:
                    powerups.remove(p)
                    continue
                if math.hypot(p.x - archer.x, p.y - (archer.y - archer.h / 2)) < 40:
                    if p.type == 'health':
                        score += 100
                    elif p.type == 'fire':
                        archer.current_arrow = 'fire'
                        try_unlock('fire_arrow')
                    elif p.type == 'ice':
                        archer.current_arrow = 'ice'
                    elif p.type == 'explosive':
                        archer.current_arrow = 'explosive'
                        try_unlock('explosive')
                    elif p.type == 'triple':
                        archer.current_arrow = 'triple'
                    elif p.type == 'money':
                        money += 100
                        score += 200
                    play_sound('buy')
                    for _ in range(20):
                        spawn_particles(p.x, p.y, NEON_GREEN, 1, 1.5)
                    powerups.remove(p)

            if enemies_to_spawn > 0:
                spawn_timer += 1
                if spawn_timer >= max(30, 90 - wave * 5):
                    spawn_timer = 0
                    enemies_to_spawn -= 1
                    spawn_enemy()

            if wave_kills >= wave_kills_needed and enemies_to_spawn <= 0 and len(enemies) == 0:
                wave += 1
                total_waves[0] += 1
                play_sound('wave_clear')
                wave_banner_timer = 120
                spawn_wave()
                if wave >= 5: try_unlock('wave_5')
                if wave >= 10: try_unlock('wave_10')
                if wave >= 15: try_unlock('wave_15')
                money += 50
                score += 500

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

        for layer in bg_layers:
            play_layer.blit(layer['surf'], (0, 0))

        pygame.draw.rect(play_layer, (10, 20, 15), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.line(play_layer, NEON_GREEN, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)

        # نشانگر محدوده حرکت کماندار
        pygame.draw.line(play_layer, (50, 100, 80), (50, GROUND_Y + 5), (50, GROUND_Y + 15), 2)
        pygame.draw.line(play_layer, (50, 100, 80), (WIDTH - 50, GROUND_Y + 5), (WIDTH - 50, GROUND_Y + 15), 2)

        if settings['show_trajectory'] and archer.is_drawing:
            rad = math.radians(archer.angle)
            start_x = archer.x + 30 + math.cos(rad) * 20
            start_y = archer.y - archer.h / 2 + math.sin(rad) * 20
            speed = 5 + archer.power * 0.18
            vx = math.cos(rad) * speed
            vy = math.sin(rad) * speed
            tx, ty = start_x, start_y
            for i in range(60):
                tx += vx
                ty += vy
                vy += GRAVITY_ARROW
                if settings['wind_enabled']:
                    vx += wind * 0.01
                if ty > GROUND_Y or tx > WIDTH or tx < 0:
                    break
                if i % 3 == 0:
                    alpha = max(30, 200 - i * 3)
                    dot = pygame.Surface((4, 4), pygame.SRCALPHA)
                    pygame.draw.circle(dot, (*NEON_YELLOW, alpha), (2, 2), 2)
                    play_layer.blit(dot, (tx - 2, ty - 2))

        for p in powerups:
            p.draw(play_layer)
        for e in enemies:
            e.draw(play_layer)
        for a in arrows:
            a.draw(play_layer)
        for a in enemy_arrows:
            a.draw(play_layer)
        for p in active_particles:
            p.draw(play_layer)

        archer.draw(play_layer)

        if hit_marker_timer > 0:
            alpha = min(255, hit_marker_timer * 12)
            mx, my = hit_marker_pos
            color = NEON_RED if hit_marker_headshot else NEON_YELLOW
            size = 12
            for angle in [0, 90, 180, 270]:
                a_rad = math.radians(angle)
                x1 = mx + math.cos(a_rad) * size
                y1 = my + math.sin(a_rad) * size
                x2 = mx + math.cos(a_rad) * (size + 8)
                y2 = my + math.sin(a_rad) * (size + 8)
                line_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(line_surf, (*color, alpha), (x1, y1), (x2, y2), 3)
                play_layer.blit(line_surf, (0, 0))
            if hit_marker_headshot:
                draw_text(play_layer, "HEADSHOT!", 20, mx, my - 30, NEON_RED, center=True, glow=True)

        if settings['wind_enabled'] and abs(wind) > 0.5:
            wind_dir = 1 if wind > 0 else -1
            wind_speed = abs(wind)
            wind_text = "WIND: " + ("→" if wind_dir > 0 else "←") * int(wind_speed)
            draw_text(play_layer, wind_text, 18, WIDTH // 2, HEIGHT - 40, NEON_CYAN, center=True, glow=True)

        if flash > 0:
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 200, 100, flash))
            play_layer.blit(fs, (0, 0))

        game_surface.blit(play_layer, (offset_x, offset_y))

        # ============================================================
        #                    HUD
        # ============================================================
        hud_panel = pygame.Surface((WIDTH, 90), pygame.SRCALPHA)
        for y in range(90):
            alpha = int(180 * (1 - y / 90))
            pygame.draw.line(hud_panel, (5, 10, 25, alpha), (0, y), (WIDTH, y))
        game_surface.blit(hud_panel, (0, 0))
        pygame.draw.line(game_surface, NEON_CYAN, (0, 90), (WIDTH, 90), 1)

        draw_text(game_surface, "NEON", 22, 25, 15, WHITE)
        draw_text(game_surface, "ARCHER", 22, 25 + get_font(22).size("NEON ")[0], 15, NEON_GREEN, glow=True)
        draw_text(game_surface, "MOVE: A/D or Arrows | AIM: Mouse | DRAW: Hold Click | 1-5: Arrow",
                  11, 25, 45, (180, 200, 220))

        draw_text(game_surface, "SCORE", 14, WIDTH - 25, 12, NEON_CYAN)
        draw_text(game_surface, f"{display_score}", 26, WIDTH - 25, 30, WHITE, glow=True)
        draw_text(game_surface, f"WAVE: {wave}", 16, WIDTH - 25, 62, NEON_GREEN)
        draw_text(game_surface, f"KILLS: {kills}", 14, WIDTH - 25, 84, NEON_YELLOW)

        arrow_names = {'normal': 'Normal', 'fire': 'Fire', 'ice': 'Ice',
                       'explosive': 'Boom', 'triple': '3x'}
        arrow_colors = {'normal': NEON_YELLOW, 'fire': NEON_ORANGE, 'ice': NEON_CYAN,
                        'explosive': NEON_RED, 'triple': NEON_MAGENTA}
        draw_text(game_surface, f"ARROW: {arrow_names[archer.current_arrow]}",
                  14, WIDTH // 2, 15, arrow_colors[archer.current_arrow], center=True, glow=True)
        draw_text(game_surface, f"HEADSHOTS: {headshots}   MONEY: ${money}",
                  12, WIDTH // 2, 40, NEON_YELLOW, center=True)

        remaining = len(enemies) + enemies_to_spawn
        draw_text(game_surface, f"ENEMIES: {remaining}",
                  14, WIDTH // 2, 65, NEON_RED, center=True)

        if combo > 1:
            combo_color = NEON_GREEN if combo < 5 else NEON_YELLOW if combo < 10 else NEON_PINK
            scale = 1 + math.sin(t * 10) * 0.1
            draw_text(game_surface, f"x{combo} COMBO", int(28 * scale), WIDTH // 2, HEIGHT // 2 - 150,
                      combo_color, center=True, glow=True)

        if wave_banner_timer > 0:
            size = 60 + int(math.sin(t * 10) * 5)
            draw_text(game_surface, f"WAVE {wave}", size, WIDTH // 2, HEIGHT // 2 - 50,
                      NEON_CYAN, center=True, glow=True)
            if wave % 5 == 0:
                draw_text(game_surface, "BOSS WAVE!", 30, WIDTH // 2, HEIGHT // 2 + 20,
                          NEON_RED, center=True, glow=True)
            else:
                draw_text(game_surface, "GET READY!", 30, WIDTH // 2, HEIGHT // 2 + 20,
                          WHITE, center=True)

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
            draw_text(game_surface, "GAME OVER", 60, WIDTH // 2, box_y + 55,
                      NEON_RED, center=True, glow=True)
            draw_text(game_surface, f"SCORE: {final_score if final_score else score}", 32,
                      WIDTH // 2, box_y + 120, WHITE, center=True)
            draw_text(game_surface, f"WAVE: {wave}   KILLS: {kills}   HEADSHOTS: {headshots}",
                      16, WIDTH // 2, box_y + 160, NEON_CYAN, center=True)
            hs = highscore[0]
            if score >= hs and score > 0:
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