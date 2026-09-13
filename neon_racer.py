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
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
    AUDIO_OK = True
except:
    AUDIO_OK = False

BASE_W, BASE_H = 900, 750
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("PYTHON NEON RACER")
game_surface = pygame.Surface((BASE_W, BASE_H))

clock = pygame.time.Clock()
FPS = 60

# --- رنگ‌ها ---
BLACK = (0, 0, 4)
DARK_BG = (2, 4, 14)
WHITE = (255, 255, 255)
NEON_BLUE = (50, 150, 255)
NEON_CYAN = (0, 230, 255)
NEON_PURPLE = (170, 60, 255)
NEON_PINK = (255, 60, 180)
NEON_RED = (255, 50, 50)
NEON_ORANGE = (255, 160, 30)
NEON_YELLOW = (255, 230, 0)
NEON_GREEN = (50, 255, 120)

SAVE_FILE = "neon_racer_save.json"

settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'difficulty': 1.0,
    'screen_shake': True,
}

achievements = {
    'first_dodge': {'name': 'FIRST DODGE', 'desc': 'Dodge your first car', 'unlocked': False, 'icon': '>'},
    'speed_500': {'name': 'SPEED DEMON', 'desc': 'Reach speed 500', 'unlocked': False, 'icon': '>>'},
    'speed_1000': {'name': 'SONIC', 'desc': 'Reach speed 1000', 'unlocked': False, 'icon': '>>>'},
    'score_1000': {'name': 'ROOKIE', 'desc': 'Score 1000 points', 'unlocked': False, 'icon': '*'},
    'score_5000': {'name': 'VETERAN', 'desc': 'Score 5000 points', 'unlocked': False, 'icon': '**'},
    'score_10000': {'name': 'LEGEND', 'desc': 'Score 10000 points', 'unlocked': False, 'icon': '***'},
    'boost_5': {'name': 'TURBO', 'desc': 'Collect 5 boosts in one run', 'unlocked': False, 'icon': 'B'},
    'survive_1min': {'name': 'SURVIVOR', 'desc': 'Survive 1 minute', 'unlocked': False, 'icon': 'T'},
    'survive_3min': {'name': 'ENDURANCE', 'desc': 'Survive 3 minutes', 'unlocked': False, 'icon': 'TT'},
    'tunnel_master': {'name': 'TUNNEL MASTER', 'desc': 'Pass 3 tunnels', 'unlocked': False, 'icon': 'U'},
    'boss_dodge': {'name': 'BOSS DODGE', 'desc': 'Dodge a boss truck', 'unlocked': False, 'icon': 'K'},
    'obstacle_10': {'name': 'OBSTACLE KILLER', 'desc': 'Pass 10 obstacles', 'unlocked': False, 'icon': 'X'},
}

highscore = [0]
game_history = []
total_tunnels = [0]
total_bosses_dodged = [0]


def load_save():
    global settings, achievements, highscore, game_history, total_tunnels, total_bosses_dodged
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
            settings.update(data.get('settings', {}))
            for k, v in data.get('achievements', {}).items():
                if k in achievements:
                    achievements[k]['unlocked'] = v
            highscore[0] = data.get('highscore', 0)
            game_history = data.get('game_history', [])
            total_tunnels[0] = data.get('total_tunnels', 0)
            total_bosses_dodged[0] = data.get('total_bosses_dodged', 0)
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
                'total_tunnels': total_tunnels[0],
                'total_bosses_dodged': total_bosses_dodged[0],
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


def add_game_to_history(score, speed, duration, new_achs):
    entry = {
        'score': score,
        'speed': speed,
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
                val += (1.0 if math.sin(2 * math.pi * bass * t) > 0 else -1.0) * 0.25
            if lead > 0:
                val += 2 * (lead * t - math.floor(lead * t + 0.5)) * 0.15
                val += math.sin(2 * math.pi * lead * 2 * t) * 0.08
            if i < sr * 0.05 and idx % 2 == 0:
                val += math.sin(2 * math.pi * 60 * t * (1 - i / (sr * 0.05))) * 0.4
            if idx % 2 == 1 and i > n * 0.5:
                val += random.uniform(-0.1, 0.1)
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
    sounds['pass'] = make_sound(800, 1200, 0.15, 0.15, 'sine')
    sounds['boost'] = make_sound(400, 1200, 0.4, 0.20, 'sine')
    sounds['crash'] = make_sound(300, 50, 0.6, 0.35, 'noise')
    sounds['gameover'] = make_sound(500, 60, 1.5, 0.3, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['tunnel'] = make_sound(200, 600, 0.8, 0.2, 'saw')
    sounds['boss_warn'] = make_sound(150, 400, 1.0, 0.25, 'saw')
    bass = [55, 55, 65.4, 65.4, 49, 49, 55, 55]
    lead = [440, 523, 659, 523, 440, 392, 349, 392]
    music_sound[0] = make_music_loop(bass, lead, 0.18, 0.12)
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
        speed = random.uniform(1, 5) * speed_mult
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = int(random.randint(20, 40) * life_mult)
        self.max_life = self.life
        self.color = color
        self.size = random.randint(2, 4) * size_mult
        self.active = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
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
#                    ماشین بازیکن
# ============================================================
class PlayerCar:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = 64
        self.h = 115
        self.target_x = x
        self.lean = 0

    def move_to(self, tx):
        self.target_x = tx

    def update(self):
        dx = self.target_x - self.x
        self.x += dx * 0.18
        self.lean = max(-1, min(1, dx / 30))

    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2 + 6), int(self.y - self.h / 2 + 4),
                           self.w - 12, self.h - 8)

    def draw(self, surface):
        cx, cy = self.x, self.y
        w, h = self.w, self.h
        lean = self.lean

        # هاله نئونی زیر ماشین
        for r in range(3, 0, -1):
            glow = pygame.Surface((int(w + 40 * r), int(h + 40 * r)), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (40, 120, 255, 25), (0, 0, w + 40 * r, h + 40 * r))
            surface.blit(glow, (cx - (w + 40 * r) / 2, cy - (h + 40 * r) / 2))

        # سایه زیر
        shadow = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 180), (10, 20, w, h - 20))
        surface.blit(shadow, (cx - (w + 20) / 2, cy - (h + 20) / 2 + 10))

        # چرخ‌ها
        for wx in [cx - w / 2 - 4, cx + w / 2 - 8]:
            pygame.draw.rect(surface, (8, 8, 15), (wx, cy + h / 4, 12, 24), border_radius=3)
            pygame.draw.rect(surface, (35, 35, 50), (wx + 2, cy + h / 4 + 3, 8, 18), border_radius=2)
        for wx in [cx - w / 2 - 4, cx + w / 2 - 8]:
            pygame.draw.rect(surface, (8, 8, 15), (wx, cy - h / 3, 12, 22), border_radius=3)

        # بدنه سه‌لایه
        body_outer = [
            (cx - lean * 3, cy - h / 2),
            (cx - w / 2 + 14 - lean * 4, cy - h / 2 + 16),
            (cx - w / 2 - 2 - lean * 5, cy - h / 4),
            (cx - w / 2 - 2 - lean * 5, cy + h / 3),
            (cx - w / 2 + 10 - lean * 4, cy + h / 2),
            (cx + w / 2 - 10 - lean * 4, cy + h / 2),
            (cx + w / 2 + 2 - lean * 5, cy + h / 3),
            (cx + w / 2 + 2 - lean * 5, cy - h / 4),
            (cx + w / 2 - 14 - lean * 4, cy - h / 2 + 16),
        ]
        pygame.draw.polygon(surface, (10, 30, 80), body_outer)

        body_mid = [
            (cx - lean * 2, cy - h / 2 + 5),
            (cx - w / 2 + 16 - lean * 3, cy - h / 2 + 20),
            (cx - w / 2 + 2 - lean * 4, cy - h / 4 + 2),
            (cx - w / 2 + 2 - lean * 4, cy + h / 3 - 2),
            (cx - w / 2 + 12 - lean * 3, cy + h / 2 - 4),
            (cx + w / 2 - 12 - lean * 3, cy + h / 2 - 4),
            (cx + w / 2 - 2 - lean * 4, cy + h / 3 - 2),
            (cx + w / 2 - 2 - lean * 4, cy - h / 4 + 2),
            (cx + w / 2 - 16 - lean * 3, cy - h / 2 + 20),
        ]
        pygame.draw.polygon(surface, (20, 100, 220), body_mid)

        body_light = [
            (cx - lean * 2, cy - h / 2 + 10),
            (cx - w / 2 + 20 - lean * 2, cy - h / 2 + 24),
            (cx - w / 2 + 10 - lean * 3, cy - h / 4 + 6),
            (cx - w / 2 + 10 - lean * 3, cy + h / 3 - 8),
            (cx - w / 2 + 16 - lean * 2, cy + h / 2 - 8),
            (cx + w / 2 - 16 - lean * 2, cy + h / 2 - 8),
            (cx + w / 2 - 10 - lean * 3, cy + h / 3 - 8),
            (cx + w / 2 - 10 - lean * 3, cy - h / 4 + 6),
            (cx + w / 2 - 20 - lean * 2, cy - h / 2 + 24),
        ]
        pygame.draw.polygon(surface, (60, 160, 255), body_light, 2)

        # کابین
        roof = [
            (cx - lean * 1, cy - h / 4 + 2),
            (cx - w / 2 + 16 - lean * 2, cy - h / 8),
            (cx - w / 2 + 18 - lean * 2, cy + h / 6),
            (cx + w / 2 - 18 - lean * 2, cy + h / 6),
            (cx + w / 2 - 16 - lean * 2, cy - h / 8),
        ]
        pygame.draw.polygon(surface, (6, 12, 25), roof)
        pygame.draw.polygon(surface, (30, 80, 150), roof, 2)

        # شیشه عقب
        rear_glass = [
            (cx - w / 2 + 20 - lean * 2, cy + h / 6 - 2),
            (cx + w / 2 - 20 - lean * 2, cy + h / 6 - 2),
            (cx + w / 2 - 22 - lean * 2, cy + h / 4 - 8),
            (cx - w / 2 + 22 - lean * 2, cy + h / 4 - 8),
        ]
        pygame.draw.polygon(surface, (100, 180, 240), rear_glass)

        # شیشه جلو
        front_glass = [
            (cx - w / 2 + 20 - lean * 2, cy - h / 6),
            (cx + w / 2 - 20 - lean * 2, cy - h / 6),
            (cx + w / 2 - 22 - lean * 2, cy - h / 3 + 2),
            (cx - w / 2 + 22 - lean * 2, cy - h / 3 + 2),
        ]
        pygame.draw.polygon(surface, (60, 130, 200), front_glass)

        # اسپویلر
        spoiler_y = cy + h / 2 - 4
        pygame.draw.line(surface, (40, 120, 220),
                         (cx - w / 2 + 8, spoiler_y), (cx + w / 2 - 8, spoiler_y), 5)
        pygame.draw.line(surface, (100, 180, 255),
                         (cx - w / 2 + 8, spoiler_y - 1), (cx + w / 2 - 8, spoiler_y - 1), 1)

        # چراغ‌های عقب قرمز
        light_y = cy + h / 2 - 12
        for lx in [cx - w / 2 + 14, cx + w / 2 - 14]:
            for r in [24, 16, 10, 5]:
                alpha = int(200 * (1 - r / 30))
                glow_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 50, 50, alpha), (r, r), r)
                surface.blit(glow_surf, (lx - r, light_y - r))
            pygame.draw.circle(surface, (255, 100, 100), (int(lx), int(light_y)), 5)
            pygame.draw.circle(surface, (255, 240, 240), (int(lx), int(light_y)), 2)

        # چراغ جلو آبی
        head_y = cy - h / 2 + 5
        for lx in [cx - 12, cx + 12]:
            glow_surf = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (100, 220, 255, 200), (18, 18), 14)
            surface.blit(glow_surf, (lx - 18, head_y - 18))
            pygame.draw.circle(surface, (200, 240, 255), (int(lx), int(head_y)), 4)


# ============================================================
#                    ماشین دشمن
# ============================================================
class EnemyCar:
    def __init__(self, x, y, color=None, speed=5):
        self.x = x
        self.y = y
        self.w = 64
        self.h = 115
        self.speed = speed
        self.color = color if color else random.choice([
            (200, 50, 80), (200, 100, 30), (100, 200, 80),
            (200, 200, 50), (150, 60, 200), (220, 60, 60)
        ])
        self.passed = False

    def update(self, world_speed):
        self.y += self.speed + world_speed * 0.3

    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2 + 6), int(self.y - self.h / 2 + 4),
                           self.w - 12, self.h - 8)

    def draw(self, surface):
        cx, cy = self.x, self.y
        w, h = self.w, self.h
        c = self.color

        for r in range(3, 0, -1):
            glow = pygame.Surface((w + 40 * r, h + 40 * r), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*c, 25), (0, 0, w + 40 * r, h + 40 * r))
            surface.blit(glow, (cx - (w + 40 * r) / 2, cy - (h + 40 * r) / 2))

        shadow = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 160), (10, 20, w, h - 20))
        surface.blit(shadow, (cx - (w + 20) / 2, cy - (h + 20) / 2 + 10))

        for wx in [cx - w / 2 - 4, cx + w / 2 - 8]:
            pygame.draw.rect(surface, (8, 8, 15), (wx, cy + h / 4, 12, 24), border_radius=3)
            pygame.draw.rect(surface, (8, 8, 15), (wx, cy - h / 3, 12, 22), border_radius=3)

        body = [
            (cx, cy - h / 2),
            (cx - w / 2 + 14, cy - h / 2 + 16),
            (cx - w / 2 - 2, cy - h / 4),
            (cx - w / 2 - 2, cy + h / 3),
            (cx - w / 2 + 10, cy + h / 2),
            (cx + w / 2 - 10, cy + h / 2),
            (cx + w / 2 + 2, cy + h / 3),
            (cx + w / 2 + 2, cy - h / 4),
            (cx + w / 2 - 14, cy - h / 2 + 16),
        ]
        dark_c = (c[0] // 3, c[1] // 3, c[2] // 3)
        pygame.draw.polygon(surface, dark_c, body)
        pygame.draw.polygon(surface, c, body, 2)

        lighter = (min(255, c[0] + 50), min(255, c[1] + 50), min(255, c[2] + 50))
        light_body = [
            (cx, cy - h / 2 + 10),
            (cx - w / 2 + 20, cy - h / 2 + 24),
            (cx - w / 2 + 10, cy - h / 4 + 6),
            (cx - w / 2 + 10, cy + h / 3 - 8),
            (cx - w / 2 + 16, cy + h / 2 - 8),
            (cx + w / 2 - 16, cy + h / 2 - 8),
            (cx + w / 2 - 10, cy + h / 3 - 8),
            (cx + w / 2 - 10, cy - h / 4 + 6),
            (cx + w / 2 - 20, cy - h / 2 + 24),
        ]
        pygame.draw.polygon(surface, lighter, light_body, 1)

        roof = [
            (cx, cy - h / 4),
            (cx - w / 2 + 16, cy - h / 8),
            (cx - w / 2 + 18, cy + h / 6),
            (cx + w / 2 - 18, cy + h / 6),
            (cx + w / 2 - 16, cy - h / 8),
        ]
        pygame.draw.polygon(surface, (20, 20, 30), roof)
        pygame.draw.polygon(surface, c, roof, 2)

        glass = [
            (cx - w / 2 + 20, cy + h / 6 - 2),
            (cx + w / 2 - 20, cy + h / 6 - 2),
            (cx + w / 2 - 22, cy + h / 4 - 8),
            (cx - w / 2 + 22, cy + h / 4 - 8),
        ]
        pygame.draw.polygon(surface, (80, 90, 120), glass)

        light_y = cy + h / 2 - 12
        for lx in [cx - w / 2 + 14, cx + w / 2 - 14]:
            glow_surf = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 80, 80, 150), (12, 12), 10)
            surface.blit(glow_surf, (lx - 12, light_y - 12))
            pygame.draw.circle(surface, (255, 120, 120), (int(lx), int(light_y)), 4)


# ============================================================
#                    کامیون باس
# ============================================================
class BossTruck:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = 130
        self.h = 220
        self.speed = 2
        self.passed = False

    def update(self, world_speed):
        self.y += self.speed + world_speed * 0.2

    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2 + 8), int(self.y - self.h / 2 + 8),
                           self.w - 16, self.h - 16)

    def draw(self, surface):
        cx, cy = self.x, self.y
        w, h = self.w, self.h

        for r in range(5, 0, -1):
            glow = pygame.Surface((w + 60 * r, h + 60 * r), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (255, 50, 50, 20), (0, 0, w + 60 * r, h + 60 * r))
            surface.blit(glow, (cx - (w + 60 * r) / 2, cy - (h + 60 * r) / 2))

        shadow = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 200), (10, 20, w, h - 20))
        surface.blit(shadow, (cx - (w + 20) / 2, cy - (h + 20) / 2 + 10))

        for wx, wy in [(cx - w / 2 - 6, cy - h / 3),
                       (cx - w / 2 - 6, cy),
                       (cx - w / 2 - 6, cy + h / 3),
                       (cx + w / 2 - 6, cy - h / 3),
                       (cx + w / 2 - 6, cy),
                       (cx + w / 2 - 6, cy + h / 3)]:
            pygame.draw.rect(surface, (5, 5, 10), (wx, wy, 16, 32), border_radius=4)
            pygame.draw.rect(surface, (40, 40, 50), (wx + 4, wy + 4, 8, 24), border_radius=3)

        body = pygame.Rect(int(cx - w / 2 + 5), int(cy - h / 2 + 5), w - 10, h - 10)
        pygame.draw.rect(surface, (60, 10, 10), body, border_radius=10)

        for y_off in [-h / 3, 0, h / 3]:
            line_rect = pygame.Rect(body.x + 5, int(body.centery + y_off - 4), body.w - 10, 8)
            pygame.draw.rect(surface, (255, 100, 50), line_rect)
            pygame.draw.rect(surface, (255, 200, 100), line_rect, 1)

        pygame.draw.rect(surface, NEON_RED, body, 3, border_radius=10)

        light_y = cy + h / 2 - 22
        for lx in [cx - w / 2 + 28, cx + w / 2 - 28]:
            for r in [28, 20, 14]:
                alpha = int(220 * (1 - r / 35))
                glow_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 30, 30, alpha), (r, r), r)
                surface.blit(glow_surf, (lx - r, light_y - r))
            pygame.draw.circle(surface, (255, 100, 100), (int(lx), int(light_y)), 8)
            pygame.draw.circle(surface, (255, 240, 240), (int(lx), int(light_y)), 3)

        warn_pts = [(cx, cy - h / 2 + 22), (cx - 18, cy - h / 2 + 50), (cx + 18, cy - h / 2 + 50)]
        pygame.draw.polygon(surface, NEON_YELLOW, warn_pts)
        pygame.draw.polygon(surface, WHITE, warn_pts, 2)
        draw_text(surface, "!", 22, cx, cy - h / 2 + 36, BLACK, center=True)


# ============================================================
#                    موانع
# ============================================================
class Obstacle:
    def __init__(self, x, y, kind='cone'):
        self.x = x
        self.y = y
        self.kind = kind
        self.passed = False
        if kind == 'cone':
            self.w = 32
            self.h = 44
            self.color = NEON_ORANGE
        elif kind == 'barrel':
            self.w = 48
            self.h = 58
            self.color = NEON_YELLOW
        elif kind == 'block':
            self.w = 52
            self.h = 44
            self.color = NEON_PURPLE
        else:
            self.w = 38
            self.h = 38
            self.color = NEON_RED

    def update(self, world_speed):
        self.y += world_speed * 0.8

    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h / 2), self.w, self.h)

    def draw(self, surface):
        cx, cy = self.x, self.y
        w, h = self.w, self.h
        for r in range(2, 0, -1):
            glow = pygame.Surface((w + 30 * r, h + 30 * r), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*self.color, 50), (0, 0, w + 30 * r, h + 30 * r))
            surface.blit(glow, (cx - (w + 30 * r) / 2, cy - (h + 30 * r) / 2))

        if self.kind == 'cone':
            pts = [(cx, cy - h / 2), (cx - w / 2, cy + h / 2), (cx + w / 2, cy + h / 2)]
            pygame.draw.polygon(surface, (100, 50, 0), pts)
            pygame.draw.polygon(surface, self.color, pts, 2)
            for i in range(3):
                y_off = -h / 3 + i * h / 4
                ratio = (y_off + h / 2) / h
                lw = w * ratio * 0.8
                pygame.draw.line(surface, WHITE, (cx - lw / 2, cy + y_off), (cx + lw / 2, cy + y_off), 2)
        elif self.kind == 'barrel':
            r = pygame.Rect(int(cx - w / 2), int(cy - h / 2), w, h)
            pygame.draw.rect(surface, (80, 60, 0), r, border_radius=4)
            pygame.draw.rect(surface, self.color, r, 3, border_radius=4)
            for i in range(3):
                y_line = r.y + r.h // 4 * (i + 1)
                pygame.draw.line(surface, (200, 180, 0), (r.x + 3, y_line), (r.right - 3, y_line), 2)
        elif self.kind == 'block':
            r = pygame.Rect(int(cx - w / 2), int(cy - h / 2), w, h)
            pygame.draw.rect(surface, (60, 20, 100), r, border_radius=4)
            pygame.draw.rect(surface, self.color, r, 3, border_radius=4)
            pygame.draw.line(surface, WHITE, (r.x + 8, r.y + 8), (r.right - 8, r.bottom - 8), 3)
            pygame.draw.line(surface, WHITE, (r.right - 8, r.y + 8), (r.x + 8, r.bottom - 8), 3)
        else:
            pygame.draw.circle(surface, (100, 40, 40), (int(cx), int(cy)), w // 2)
            pygame.draw.circle(surface, self.color, (int(cx), int(cy)), w // 2, 2)


# ============================================================
#                    تونل
# ============================================================
class Tunnel:
    def __init__(self, y):
        self.y = y
        self.h = 250
        self.active = True

    def update(self, world_speed):
        self.y += world_speed * 1.0

    def get_overlay_alpha(self, player_y):
        if not self.active:
            return 0
        top = self.y - self.h / 2
        bottom = self.y + self.h / 2
        if player_y < top or player_y > bottom:
            return 0
        progress = (player_y - top) / self.h
        if progress < 0.2:
            return int(180 * progress / 0.2)
        elif progress > 0.8:
            return int(180 * (1 - (progress - 0.8) / 0.2))
        else:
            return 180

    def draw(self, surface):
        if not self.active:
            return
        road_left = 200
        road_right = WIDTH - 200
        tunnel_rect_left = pygame.Rect(0, int(self.y - self.h / 2), road_left, self.h)
        tunnel_rect_right = pygame.Rect(road_right, int(self.y - self.h / 2), WIDTH - road_right, self.h)

        pygame.draw.rect(surface, (15, 5, 25), tunnel_rect_left)
        for i in range(5):
            x = 30 + i * 35
            pygame.draw.line(surface, NEON_PURPLE, (x, tunnel_rect_left.y),
                             (x, tunnel_rect_left.bottom), 2)
        pygame.draw.line(surface, NEON_PURPLE, (road_left, tunnel_rect_left.y),
                         (road_left, tunnel_rect_left.bottom), 4)

        pygame.draw.rect(surface, (15, 5, 25), tunnel_rect_right)
        for i in range(5):
            x = WIDTH - 30 - i * 35
            pygame.draw.line(surface, NEON_PURPLE, (x, tunnel_rect_right.y),
                             (x, tunnel_rect_right.bottom), 2)
        pygame.draw.line(surface, NEON_PURPLE, (road_right, tunnel_rect_right.y),
                         (road_right, tunnel_rect_right.bottom), 4)

        top_y = int(self.y - self.h / 2)
        if top_y > -50:
            top_rect = pygame.Rect(road_left, top_y - 30, road_right - road_left, 30)
            pygame.draw.rect(surface, (20, 10, 40), top_rect)
            pygame.draw.rect(surface, NEON_PURPLE, top_rect, 2)

        bot_y = int(self.y + self.h / 2)
        if bot_y < HEIGHT:
            bot_rect = pygame.Rect(road_left, bot_y, road_right - road_left, 20)
            pygame.draw.rect(surface, (20, 10, 40), bot_rect)
            pygame.draw.rect(surface, NEON_PURPLE, bot_rect, 2)


# ============================================================
#                    Speed Lines
# ============================================================
class SpeedLine:
    def __init__(self):
        self.reset(random_y=True)

    def reset(self, random_y=False):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(-HEIGHT, HEIGHT) if random_y else random.uniform(-200, 0)
        self.length = random.uniform(60, 200)
        self.speed = random.uniform(20, 35)
        self.color = random.choice([WHITE, (200, 230, 255), (150, 200, 255), NEON_CYAN])
        self.width = random.choice([1, 2, 2, 3])

    def update(self, world_speed):
        self.y += self.speed + world_speed * 0.6
        if self.y > HEIGHT + self.length:
            self.reset()

    def draw(self, surface):
        pygame.draw.line(surface, self.color, (self.x, self.y), (self.x, self.y - self.length), self.width)


# ============================================================
#                    Boost Pad
# ============================================================
class BoostPad:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = 58
        self.h = 48
        self.pulse = 0

    def update(self, world_speed):
        self.y += world_speed
        self.pulse += 0.2

    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h / 2), self.w, self.h)

    def draw(self, surface):
        pulse = math.sin(self.pulse) * 0.3 + 1
        for r in range(3, 0, -1):
            glow = pygame.Surface((int(self.w * 2 * pulse) + r * 20,
                                    int(self.h * 2 * pulse) + r * 20), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (255, 200, 0, 40), (0, 0, glow.get_width(), glow.get_height()))
            surface.blit(glow, (self.x - glow.get_width() / 2, self.y - glow.get_height() / 2))

        for i in range(3):
            yy = self.y + self.h / 2 - i * 12
            pts = [(self.x, yy - 8), (self.x - 12, yy + 2), (self.x + 12, yy + 2)]
            pygame.draw.polygon(surface, NEON_YELLOW, pts)
            pygame.draw.polygon(surface, WHITE, pts, 2)


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
#                    Menu
# ============================================================
def show_menu():
    menu_time = 0
    btn_start = Button(WIDTH // 2, HEIGHT // 2 + 30, 320, 55, "START RACE", NEON_CYAN, NEON_GREEN, 28)
    btn_history = Button(WIDTH // 2, HEIGHT // 2 + 95, 320, 45, "HISTORY", NEON_BLUE, NEON_CYAN, 22)
    btn_settings = Button(WIDTH // 2, HEIGHT // 2 + 150, 320, 45, "SETTINGS", NEON_PURPLE, NEON_PINK, 22)
    btn_achievements = Button(WIDTH // 2, HEIGHT // 2 + 205, 320, 45, "ACHIEVEMENTS", NEON_YELLOW, NEON_ORANGE, 22)
    btn_quit = Button(WIDTH // 2, HEIGHT // 2 + 260, 320, 42, "QUIT", NEON_RED, NEON_ORANGE, 20)
    menu_speed_lines = [SpeedLine() for _ in range(40)]

    while True:
        game_surface.fill(BLACK)
        t = pygame.time.get_ticks() / 1000
        menu_time += 1
        mouse_pos = get_game_mouse_pos()

        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            game_surface.blit(s, (0, y))

        for _ in range(100):
            pygame.draw.circle(game_surface, (100, 100, 150),
                               (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 1)

        for sl in menu_speed_lines:
            sl.update(3)
            sl.draw(game_surface)

        title_y = 130 + math.sin(t * 2) * 8
        draw_text(game_surface, "PYTHON", 72, WIDTH // 2, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "NEON RACER", 72, WIDTH // 2, title_y + 70, NEON_BLUE, center=True, glow=True)
        draw_text(game_surface, "DOOGE  /  BOOST  /  SURVIVE", 20, WIDTH // 2, title_y + 135, (200, 200, 220), center=True)

        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 22, WIDTH // 2, title_y + 185, NEON_YELLOW, center=True)
        draw_text(game_surface, f"TOTAL RACES: {len(game_history)}   TUNNELS: {total_tunnels[0]}",
                  14, WIDTH // 2, title_y + 210, NEON_PINK, center=True)

        for b in [btn_start, btn_history, btn_settings, btn_achievements, btn_quit]:
            b.update(mouse_pos)
            b.draw(game_surface)

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
#                    Settings
# ============================================================
def show_settings():
    global settings
    slider_sfx = Slider(WIDTH // 2, 180, 400, 12, settings['sfx_volume'], 0, 1, "SFX Volume")
    slider_music = Slider(WIDTH // 2, 270, 400, 12, settings['music_volume'], 0, 1, "Music Volume")
    slider_diff = Slider(WIDTH // 2, 360, 400, 12, (settings['difficulty'] - 0.5) / 1.0, 0, 1, "Difficulty")
    btn_shake = Button(WIDTH // 2, 450, 280, 55,
                       "SHAKE: ON" if settings['screen_shake'] else "SHAKE: OFF",
                       NEON_GREEN if settings['screen_shake'] else (100, 100, 100), NEON_CYAN, 22)
    btn_reset = Button(WIDTH // 2 - 130, 530, 220, 50, "RESET SAVE", NEON_RED, NEON_ORANGE, 20)
    btn_back = Button(WIDTH // 2 + 130, 530, 220, 50, "BACK", NEON_CYAN, NEON_GREEN, 22)

    while True:
        game_surface.fill(DARK_BG)
        mouse_pos = get_game_mouse_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        for _ in range(80):
            pygame.draw.circle(game_surface, (100, 100, 150),
                               (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 1)

        box_w, box_h = 700, 580
        box_x = WIDTH // 2 - box_w // 2
        box_y = HEIGHT // 2 - box_h // 2 + 20
        pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h), border_radius=12)
        pygame.draw.rect(game_surface, NEON_PURPLE, (box_x, box_y, box_w, box_h), 3, border_radius=12)
        draw_text(game_surface, "SETTINGS", 50, WIDTH // 2, 60, NEON_CYAN, center=True, glow=True)

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
                return
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
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
                total_tunnels[0] = 0
                total_bosses_dodged[0] = 0
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
        for _ in range(80):
            pygame.draw.circle(game_surface, (100, 100, 150),
                               (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 1)
        draw_text(game_surface, "ACHIEVEMENTS", 50, WIDTH // 2, 40, NEON_YELLOW, center=True, glow=True)
        unlocked_count = sum(1 for a in achievements.values() if a['unlocked'])
        draw_text(game_surface, f"{unlocked_count} / {len(achievements)}", 22, WIDTH // 2, 78, NEON_CYAN, center=True)

        y_pos = 115
        card_w = 720
        card_h = 42
        for key, a in achievements.items():
            cx = WIDTH // 2 - card_w // 2
            color = NEON_GREEN if a['unlocked'] else (60, 60, 80)
            pygame.draw.rect(game_surface, (10, 5, 25), (cx, y_pos, card_w, card_h), border_radius=8)
            pygame.draw.rect(game_surface, color, (cx, y_pos, card_w, card_h), 2, border_radius=8)
            icon_color = NEON_YELLOW if a['unlocked'] else (80, 80, 80)
            draw_text(game_surface, a['icon'], 20, cx + 35, y_pos + card_h // 2, icon_color, center=True)
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
        for _ in range(80):
            pygame.draw.circle(game_surface, (100, 100, 150),
                               (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 1)
        draw_text(game_surface, "RACE HISTORY", 46, WIDTH // 2, 35, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, f"Total races: {len(game_history)}", 16, WIDTH // 2, 72, NEON_YELLOW, center=True)

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
                if score >= 10000:
                    rank_color, rank = NEON_PINK, "S"
                elif score >= 5000:
                    rank_color, rank = NEON_YELLOW, "A"
                elif score >= 2000:
                    rank_color, rank = NEON_GREEN, "B"
                elif score >= 1000:
                    rank_color, rank = NEON_CYAN, "C"
                else:
                    rank_color, rank = (150, 150, 180), "D"
                pygame.draw.rect(game_surface, (15, 8, 30), (ix, iy, iw, item_h - 8), border_radius=6)
                pygame.draw.rect(game_surface, rank_color, (ix, iy, iw, item_h - 8), 2, border_radius=6)
                draw_text(game_surface, rank, 36, ix + 35, iy + (item_h - 8) // 2, rank_color, center=True, glow=True)
                draw_text(game_surface, f"SCORE: {score}", 20, ix + 70, iy + 6, WHITE)
                draw_text(game_surface, f"TOP SPEED: {entry.get('speed', 0)}   TIME: {entry.get('duration', 0)}s",
                          14, ix + 70, iy + 30, (180, 180, 200))
                draw_text(game_surface, entry.get('date', '?'), 14, ix + iw - 200, iy + 6, NEON_CYAN)
                new_achs = entry.get('achievements', [])
                if new_achs:
                    ach_str = " ".join(new_achs[:5])
                    if len(new_achs) > 5:
                        ach_str += f" +{len(new_achs) - 5}"
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
            draw_text(game_surface, "No races yet", 28, WIDTH // 2, HEIGHT // 2, (150, 150, 180), center=True)

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
def play_game():
    lane_centers = [
        WIDTH // 2 - 200,
        WIDTH // 2,
        WIDTH // 2 + 200,
    ]
    player = PlayerCar(lane_centers[1], HEIGHT - 130)
    current_lane = 1
    enemy_cars = []
    boost_pads = []
    obstacles = []
    tunnels = []
    boss_trucks = []
    speed_lines = [SpeedLine() for _ in range(60)]

    score = 0
    display_score = 0
    speed = 6
    base_speed = 6
    boost_multiplier = 1
    boost_timer = 0
    game_over = False
    paused = False
    final_score = 0
    total_frames = 0

    new_achs = []
    notifications = []
    go_anim = 0
    screen_shake = 0
    flash = 0
    spawn_timer = 0
    pad_timer = 0
    obstacle_timer = 0
    tunnel_timer = 0
    boss_timer = 0
    boost_banner_timer = 0

    highest_speed = 0
    bosses_dodged = 0
    obstacles_passed = 0
    tunnels_passed = 0
    current_tunnel = None

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
        add_game_to_history(score, highest_speed, total_frames // FPS, new_achs)

    game_saved = False
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
                    play_game()
                    return
                if btn_menu.is_clicked(event):
                    stop_music()
                    return

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    if not paused and not game_over and current_lane > 0:
                        current_lane -= 1
                        player.move_to(lane_centers[current_lane])
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    if not paused and not game_over and current_lane < 2:
                        current_lane += 1
                        player.move_to(lane_centers[current_lane])
                if event.key == pygame.K_SPACE and not game_over and not paused:
                    if boost_timer < 60:
                        boost_multiplier = min(3, boost_multiplier + 1) if boost_timer > 0 else 2
                        boost_timer = 90
                        boost_banner_timer = 60
                        play_sound('boost')
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
            speed = base_speed + total_frames / (FPS * 3)
            speed *= settings['difficulty']
            if boost_timer > 0:
                speed *= boost_multiplier
                boost_timer -= 1
                if boost_timer == 0:
                    boost_multiplier = 1

            if speed * 30 > highest_speed:
                highest_speed = int(speed * 30)
            if speed * 30 >= 500:
                try_unlock('speed_500')
            if speed * 30 >= 1000:
                try_unlock('speed_1000')
            if total_frames >= FPS * 60:
                try_unlock('survive_1min')
            if total_frames >= FPS * 180:
                try_unlock('survive_3min')

            if display_score < score:
                display_score += max(1, (score - display_score) // 5)
                if display_score > score:
                    display_score = score

            player.update()
            for sl in speed_lines:
                sl.update(speed)

            # اسپاون دشمن
            spawn_timer += 1
            spawn_interval = max(35, 80 - int(total_frames / 120))
            spawn_interval = int(spawn_interval / settings['difficulty'])
            if spawn_timer > spawn_interval:
                spawn_timer = 0
                available = [0, 1, 2]
                for c in enemy_cars + boss_trucks:
                    if -200 < c.y < 200:
                        for li, lx in enumerate(lane_centers):
                            if abs(c.x - lx) < 10 and li in available:
                                available.remove(li)
                if available:
                    lane_idx = random.choice(available)
                    x = lane_centers[lane_idx]
                    enemy = EnemyCar(x, -120, speed=random.uniform(2, 4))
                    enemy_cars.append(enemy)

            # اسپاون boost
            pad_timer += 1
            if pad_timer > 250:
                pad_timer = 0
                if random.random() < 0.6:
                    lane_idx = random.randint(0, 2)
                    x = lane_centers[lane_idx]
                    boost_pads.append(BoostPad(x, -60))

            # اسپاون مانع
            obstacle_timer += 1
            if obstacle_timer > 100:
                obstacle_timer = 0
                if random.random() < 0.7:
                    lane_idx = random.randint(0, 2)
                    x = lane_centers[lane_idx]
                    kind = random.choice(['cone', 'barrel', 'block', 'rock'])
                    obstacles.append(Obstacle(x, -60, kind))

            # اسپاون تونل
            tunnel_timer += 1
            if tunnel_timer > 600 and current_tunnel is None:
                tunnel_timer = 0
                if random.random() < 0.7:
                    new_tunnel = Tunnel(-300)
                    tunnels.append(new_tunnel)
                    current_tunnel = new_tunnel
                    play_sound('tunnel')
                    tunnels_passed += 1
                    total_tunnels[0] += 1
                    if tunnels_passed >= 3:
                        try_unlock('tunnel_master')

            # اسپاون باس
            boss_timer += 1
            if boss_timer > 900:
                boss_timer = 0
                if random.random() < 0.6 and not boss_trucks:
                    boss = BossTruck(lane_centers[random.randint(0, 2)], -250)
                    boss_trucks.append(boss)
                    play_sound('boss_warn')
                    flash = 80

            # آپدیت دشمن
            for car in enemy_cars[:]:
                car.update(speed)
                if not car.passed and car.y > player.y + 100:
                    car.passed = True
                    score += 50
                    play_sound('pass')
                    try_unlock('first_dodge')
                    for _ in range(8):
                        spawn_particles(car.x, car.y, NEON_CYAN, 1, 0.8, 0.8)
                if car.rect().colliderect(player.rect()):
                    game_over = True
                    final_score = score
                    highscore[0] = max(highscore[0], score)
                    if score >= 1000:
                        try_unlock('score_1000')
                    if score >= 5000:
                        try_unlock('score_5000')
                    if score >= 10000:
                        try_unlock('score_10000')
                    if settings['screen_shake']:
                        screen_shake = 30
                    flash = 200
                    play_sound('crash')
                    for _ in range(60):
                        spawn_particles(player.x, player.y,
                                        random.choice([NEON_RED, NEON_ORANGE, NEON_YELLOW]),
                                        1, 2.0, 1.5, 1.5)
                    save_current()
                    game_saved = True
                    play_sound('gameover')
                    go_anim = 0
                if car.y > HEIGHT + 100:
                    enemy_cars.remove(car)

            # موانع
            for obs in obstacles[:]:
                obs.update(speed)
                if not obs.passed and obs.y > player.y + 50:
                    obs.passed = True
                    obstacles_passed += 1
                    score += 20
                    if obstacles_passed >= 10:
                        try_unlock('obstacle_10')
                if obs.rect().colliderect(player.rect()):
                    game_over = True
                    final_score = score
                    highscore[0] = max(highscore[0], score)
                    if settings['screen_shake']:
                        screen_shake = 25
                    flash = 180
                    play_sound('crash')
                    for _ in range(40):
                        spawn_particles(obs.x, obs.y, obs.color, 1, 1.8, 1.3, 1.3)
                    save_current()
                    game_saved = True
                    play_sound('gameover')
                    go_anim = 0
                if obs.y > HEIGHT + 80:
                    obstacles.remove(obs)

            # باس
            for boss in boss_trucks[:]:
                boss.update(speed)
                if not boss.passed and boss.y > player.y + 150:
                    boss.passed = True
                    score += 500
                    bosses_dodged += 1
                    total_bosses_dodged[0] += 1
                    try_unlock('boss_dodge')
                    if settings['screen_shake']:
                        screen_shake = 15
                if boss.rect().colliderect(player.rect()):
                    game_over = True
                    final_score = score
                    highscore[0] = max(highscore[0], score)
                    if settings['screen_shake']:
                        screen_shake = 40
                    flash = 255
                    play_sound('crash')
                    for _ in range(80):
                        spawn_particles(player.x, player.y,
                                        random.choice([NEON_RED, NEON_ORANGE, NEON_YELLOW]),
                                        1, 2.5, 2.0, 2.0)
                    save_current()
                    game_saved = True
                    play_sound('gameover')
                    go_anim = 0
                if boss.y > HEIGHT + 200:
                    boss_trucks.remove(boss)
                    if boss == current_tunnel:
                        current_tunnel = None

            # تونل
            for tunnel in tunnels[:]:
                tunnel.update(speed)
                if tunnel.y > HEIGHT + 300:
                    tunnels.remove(tunnel)
                    if tunnel == current_tunnel:
                        current_tunnel = None

            # boost pad
            for pad in boost_pads[:]:
                pad.update(speed)
                if pad.rect().colliderect(player.rect()):
                    boost_multiplier = min(3, boost_multiplier + 1) if boost_timer > 0 else 2
                    boost_timer = 120
                    boost_banner_timer = 60
                    play_sound('boost')
                    score += 100
                    for _ in range(20):
                        spawn_particles(pad.x, pad.y, NEON_YELLOW, 1, 1.5)
                    boost_pads.remove(pad)
                elif pad.y > HEIGHT + 100:
                    boost_pads.remove(pad)

            # ذرات موتور بوست
            if boost_timer > 0:
                for _ in range(3):
                    spawn_particles(player.x + random.uniform(-15, 15), player.y + 50,
                                    random.choice([NEON_CYAN, NEON_BLUE, WHITE]),
                                    1, 1.2, 0.8, 0.5)

            score += int(speed * 0.5)

            for part in active_particles[:]:
                part.update()
                if not part.active:
                    active_particles.remove(part)

            if screen_shake > 0:
                screen_shake -= 1
            if flash > 0:
                flash -= 8
            if boost_banner_timer > 0:
                boost_banner_timer -= 1

        # ===== رسم =====
        game_surface.fill(BLACK)
        offset_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        offset_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0

        play_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # آسمان گرادیان
        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            play_layer.blit(s, (0, y))

        # ستاره‌ها
        for _ in range(60):
            pygame.draw.circle(play_layer, (100, 100, 150),
                               (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 1)

        # خطوط سرعت
        for sl in speed_lines:
            sl.draw(play_layer)

        # تونل‌ها
        for tunnel in tunnels:
            tunnel.draw(play_layer)

        # boost pads
        for pad in boost_pads:
            pad.draw(play_layer)

        # موانع
        for obs in obstacles:
            obs.draw(play_layer)

        # دشمن‌ها
        for car in enemy_cars:
            car.draw(play_layer)

        # باس‌ها
        for boss in boss_trucks:
            boss.draw(play_layer)

        # ذرات
        for part in active_particles:
            part.draw(play_layer)

        # بازیکن
        if not game_over:
            player.draw(play_layer)

        # overlay تونل
        tunnel_overlay_alpha = 0
        for tunnel in tunnels:
            a = tunnel.get_overlay_alpha(player.y)
            if a > tunnel_overlay_alpha:
                tunnel_overlay_alpha = a
        if tunnel_overlay_alpha > 0:
            dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dark.fill((0, 0, 0, tunnel_overlay_alpha))
            play_layer.blit(dark, (0, 0))

        # speed lines بوست
        if boost_timer > 0:
            for i in range(25):
                x1 = random.randint(0, 120)
                y1 = random.randint(0, HEIGHT)
                length = random.randint(40, 120)
                pygame.draw.line(play_layer, (120, 220, 255), (x1, y1), (x1, y1 - length), 2)
                x2 = WIDTH - x1
                pygame.draw.line(play_layer, (120, 220, 255), (x2, y1), (x2, y1 - length), 2)

        if flash > 0:
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 200, 100, flash))
            play_layer.blit(fs, (0, 0))

        game_surface.blit(play_layer, (offset_x, offset_y))

        # HUD
        hud_panel = pygame.Surface((WIDTH, 90), pygame.SRCALPHA)
        for y in range(90):
            alpha = int(180 * (1 - y / 90))
            pygame.draw.line(hud_panel, (5, 10, 25, alpha), (0, y), (WIDTH, y))
        game_surface.blit(hud_panel, (0, 0))
        pygame.draw.line(game_surface, NEON_CYAN, (0, 90), (WIDTH, 90), 1)

        draw_text(game_surface, "PYTHON", 30, 25, 15, WHITE)
        pw = get_font(30).size("PYTHON ")[0]
        draw_text(game_surface, "NEON RACER", 30, 25 + pw, 15, NEON_BLUE, glow=True)
        draw_text(game_surface, "DOOGE  /  BOOST  /  SURVIVE", 13, 25, 50, (180, 200, 220))

        draw_text(game_surface, "SCORE", 16, WIDTH - 25, 12, NEON_CYAN)
        draw_text(game_surface, f"{display_score}", 28, WIDTH - 25, 32, WHITE, glow=True)
        draw_text(game_surface, "SPEED", 16, WIDTH - 25, 62, NEON_CYAN)
        speed_color = NEON_CYAN if speed * 30 < 500 else NEON_YELLOW if speed * 30 < 1000 else NEON_PINK
        draw_text(game_surface, f"{int(speed * 30)}", 20, WIDTH - 25, 80, speed_color, glow=True)

        if current_tunnel is not None and not game_over:
            ty = current_tunnel.y - current_tunnel.h / 2
            if -100 < ty < 200:
                draw_text(game_surface, "! TUNNEL !", 30, WIDTH // 2, 200, NEON_PURPLE, center=True, glow=True)

        if boss_trucks and not game_over:
            for boss in boss_trucks:
                if -150 < boss.y < 200:
                    alpha = abs(math.sin(t * 6)) * 255
                    warn = pygame.Surface((WIDTH, 100), pygame.SRCALPHA)
                    warn.fill((255, 0, 0, int(alpha * 0.3)))
                    game_surface.blit(warn, (0, HEIGHT // 2 - 50))
                    draw_text(game_surface, "!! BOSS TRUCK !!", 50, WIDTH // 2, HEIGHT // 2,
                              NEON_RED, center=True, glow=True)
                    break

        if boost_banner_timer > 0:
            size = 78 + int(math.sin(t * 12) * 8)
            bx = WIDTH // 2
            by = 160
            draw_text(game_surface, f"BOOST x{boost_multiplier}", size, bx + 5, by + 5,
                      (0, 0, 0), center=True, italic=True)
            draw_text(game_surface, f"BOOST x{boost_multiplier}", size, bx, by,
                      WHITE, center=True, italic=True, glow=True)

        if boost_timer > 0:
            draw_text(game_surface, f"BOOST x{boost_multiplier}", 30, WIDTH - 40, HEIGHT - 90,
                      WHITE, center=True, italic=True, glow=True)

        for i, notif in enumerate(notifications):
            ny = 130 + i * 70
            alpha = min(255, notif['timer'] * 2)
            ach = notif['ach']
            notif_surf = pygame.Surface((360, 60), pygame.SRCALPHA)
            notif_surf.fill((10, 5, 25, min(220, alpha)))
            game_surface.blit(notif_surf, (WIDTH - 380, ny))
            pygame.draw.rect(game_surface, NEON_YELLOW, (WIDTH - 380, ny, 360, 60), 2)
            draw_text(game_surface, "ACHIEVEMENT UNLOCKED!", 13, WIDTH - 360, ny + 5, NEON_YELLOW)
            draw_text(game_surface, ach['name'], 20, WIDTH - 360, ny + 25, WHITE, glow=True)

        if game_over:
            go_anim += 1
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            game_surface.blit(overlay, (0, 0))
            box_w, box_h = 540, 420
            box_x = WIDTH // 2 - box_w // 2
            box_y = HEIGHT // 2 - box_h // 2
            pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h))
            pygame.draw.rect(game_surface, NEON_PINK, (box_x, box_y, box_w, box_h), 3)
            pygame.draw.rect(game_surface, NEON_CYAN, (box_x + 5, box_y + 5, box_w - 10, box_h - 10), 1)
            draw_text(game_surface, "CRASHED!", 60, WIDTH // 2, box_y + 55,
                      NEON_RED, center=True, glow=True)
            draw_text(game_surface, f"SCORE: {final_score}", 34, WIDTH // 2, box_y + 120,
                      WHITE, center=True)
            hs = highscore[0]
            if final_score >= hs and final_score > 0:
                draw_text(game_surface, "* NEW HIGH SCORE! *", 24, WIDTH // 2, box_y + 158,
                          NEON_YELLOW, center=True, glow=True)
            else:
                draw_text(game_surface, f"HIGH SCORE: {hs}", 20, WIDTH // 2, box_y + 158,
                          NEON_YELLOW, center=True)
            draw_text(game_surface, f"Tunnels: {tunnels_passed}   Bosses: {bosses_dodged}   Obstacles: {obstacles_passed}",
                      14, WIDTH // 2, box_y + 195, NEON_CYAN, center=True)
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