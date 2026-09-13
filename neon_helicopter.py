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

BASE_W, BASE_H = 900, 750
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("NEON HELICOPTER")
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
GRAVITY = 0.5
FLAP_FORCE = -8
MAX_FALL_SPEED = 12
GROUND_Y = HEIGHT - 60
SCROLL_SPEED = 4

# --- ذخیره ---
SAVE_FILE = "neon_heli_save.json"
settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'difficulty': 1.0,
    'screen_shake': True,
}
achievements = {
    'first_flap': {'name': 'FIRST FLAP', 'desc': 'Flap for the first time', 'unlocked': False, 'icon': '^'},
    'distance_100': {'name': 'ROOKIE', 'desc': 'Fly 100 meters', 'unlocked': False, 'icon': 'D100'},
    'distance_500': {'name': 'VETERAN', 'desc': 'Fly 500 meters', 'unlocked': False, 'icon': 'D500'},
    'distance_2000': {'name': 'LEGEND', 'desc': 'Fly 2000 meters', 'unlocked': False, 'icon': 'D2K'},
    'coin_10': {'name': 'COIN COLLECTOR', 'desc': 'Collect 10 coins', 'unlocked': False, 'icon': 'C10'},
    'coin_50': {'name': 'RICH', 'desc': 'Collect 50 coins', 'unlocked': False, 'icon': 'C50'},
    'coin_200': {'name': 'MILLIONAIRE', 'desc': 'Collect 200 coins', 'unlocked': False, 'icon': 'C200'},
    'checkpoint_1': {'name': 'CHECKPOINT!', 'desc': 'Reach first checkpoint', 'unlocked': False, 'icon': 'CP1'},
    'checkpoint_5': {'name': 'EXPLORER', 'desc': 'Reach 5 checkpoints', 'unlocked': False, 'icon': 'CP5'},
    'checkpoint_10': {'name': 'ADVENTURER', 'desc': 'Reach 10 checkpoints', 'unlocked': False, 'icon': 'CP10'},
    'shield_use': {'name': 'SHIELDED', 'desc': 'Use a shield', 'unlocked': False, 'icon': 'S'},
    'magnet_use': {'name': 'MAGNETIC', 'desc': 'Use a magnet', 'unlocked': False, 'icon': 'M'},
    'boss_kill': {'name': 'BOSS SLAYER', 'desc': 'Defeat the boss', 'unlocked': False, 'icon': 'B'},
    'night_flyer': {'name': 'NIGHT FLYER', 'desc': 'Survive through the night', 'unlocked': False, 'icon': 'N'},
    'perfect_100': {'name': 'PERFECT 100', 'desc': 'Reach 100m without a single hit', 'unlocked': False, 'icon': 'P'},
}
highscore = [0]
game_history = []
total_distance = [0]
total_coins = [0]
total_bosses = [0]


def load_save():
    global settings, achievements, highscore, game_history, total_distance, total_coins, total_bosses
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
            settings.update(data.get('settings', {}))
            for k, v in data.get('achievements', {}).items():
                if k in achievements:
                    achievements[k]['unlocked'] = v
            highscore[0] = data.get('highscore', 0)
            game_history = data.get('game_history', [])
            total_distance[0] = data.get('total_distance', 0)
            total_coins[0] = data.get('total_coins', 0)
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
                'total_distance': total_distance[0],
                'total_coins': total_coins[0],
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


def add_game_to_history(score, distance, duration, new_achs):
    entry = {
        'score': score,
        'distance': distance,
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
    sounds['flap'] = make_sound(400, 700, 0.08, 0.18, 'sine')
    sounds['coin'] = make_sound(1000, 1500, 0.1, 0.18, 'sine')
    sounds['hit'] = make_sound(300, 100, 0.2, 0.28, 'noise')
    sounds['powerup'] = make_sound(600, 1400, 0.3, 0.22, 'sine')
    sounds['checkpoint'] = make_sound(500, 1500, 0.5, 0.25, 'sine')
    sounds['boss_alert'] = make_sound(150, 500, 0.8, 0.28, 'saw')
    sounds['gameover'] = make_sound(500, 60, 1.2, 0.30, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['shield'] = make_sound(700, 1200, 0.2, 0.20, 'sine')

    bass = [82.4, 82.4, 73.4, 73.4, 65.4, 65.4, 82.4, 82.4]
    lead = [659, 784, 880, 784, 659, 587, 523, 587]
    music_sound[0] = make_music_loop(bass, lead, 0.22, 0.08)
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
#                    Helicopter
# ============================================================
class Helicopter:
    def __init__(self):
        self.x = 200
        self.y = HEIGHT // 2
        self.vy = 0
        self.radius = 22
        self.rotor_angle = 0
        self.alive = True
        self.has_shield = False
        self.magnet_timer = 0
        self.boost_timer = 0
        self.slowmo_timer = 0
        self.lives = 1
        self.hit_flash = 0

    def flap(self):
        self.vy = FLAP_FORCE

    def update(self):
        # گرانش
        gravity_mult = 1.0
        if self.slowmo_timer > 0:
            gravity_mult = 0.5

        self.vy += GRAVITY * gravity_mult
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED

        self.y += self.vy

        # محدودیت بالا
        if self.y < self.radius:
            self.y = self.radius
            self.vy = 0

        # محدودیت پایین
        if self.y > GROUND_Y - self.radius:
            self.y = GROUND_Y - self.radius
            self.vy = 0
            # اگه خیلی سریع خورده به زمین
            if self.vy > 8:
                self.alive = False

        # پره چرخان
        self.rotor_angle += 30

        # تایمرها
        if self.magnet_timer > 0:
            self.magnet_timer -= 1
        if self.boost_timer > 0:
            self.boost_timer -= 1
        if self.slowmo_timer > 0:
            self.slowmo_timer -= 1
        if self.hit_flash > 0:
            self.hit_flash -= 1

    def rect(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius),
                           self.radius * 2, self.radius * 2)

    def draw(self, surface):
        color = WHITE if self.hit_flash > 0 else NEON_CYAN

        # هاله
        for hr in range(3, 0, -1):
            glow_size = self.radius * 2 + hr * 10
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 50 - hr * 12),
                               (glow_size // 2, glow_size // 2), glow_size // 2)
            surface.blit(glow, (self.x - glow_size // 2, self.y - glow_size // 2))

        # بدنه
        body_rect = pygame.Rect(int(self.x - 25), int(self.y - 12), 50, 24)
        pygame.draw.rect(surface, (20, 50, 90), body_rect, border_radius=8)
        pygame.draw.rect(surface, color, body_rect, 3, border_radius=8)

        # کابین (شیشه)
        cockpit_rect = pygame.Rect(int(self.x + 8), int(self.y - 8), 15, 16)
        pygame.draw.rect(surface, (100, 180, 240), cockpit_rect, border_radius=4)
        pygame.draw.rect(surface, WHITE, cockpit_rect, 1, border_radius=4)

        # دم
        pygame.draw.line(surface, color,
                         (self.x - 25, self.y),
                         (self.x - 45, self.y), 6)
        pygame.draw.line(surface, WHITE,
                         (self.x - 25, self.y - 1),
                         (self.x - 45, self.y - 1), 2)

        # پره چرخان
        rotor_x = self.x
        rotor_y = self.y - 20
        rad = math.radians(self.rotor_angle)
        for i in range(2):
            angle = rad + i * math.pi
            ex = rotor_x + math.cos(angle) * 35
            ey = rotor_y + math.sin(angle) * 8
            ex2 = rotor_x + math.cos(angle + math.pi) * 35
            ey2 = rotor_y + math.sin(angle + math.pi) * 8
            pygame.draw.line(surface, color, (ex, ey), (ex2, ey2), 3)

        # مرکز پره
        pygame.draw.circle(surface, WHITE, (int(rotor_x), int(rotor_y)), 4)

        # موتور
        pygame.draw.circle(surface, NEON_ORANGE, (int(self.x - 15), int(self.y + 12)), 4)

        # چراغ‌های چشمک‌زن
        blink = (pygame.time.get_ticks() // 300) % 2
        light_color = NEON_RED if blink else (100, 20, 20)
        pygame.draw.circle(surface, light_color, (int(self.x), int(self.y - 12)), 3)

        # شیلد
        if self.has_shield:
            shield_alpha = 100 + int(math.sin(pygame.time.get_ticks() / 100) * 60)
            for hr in range(2):
                shield_surf = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
                pygame.draw.circle(shield_surf, (*NEON_GREEN, shield_alpha // (hr + 2)),
                                   (self.radius * 2, self.radius * 2), self.radius + 10 + hr * 3, 2)
                surface.blit(shield_surf, (self.x - self.radius * 2, self.y - self.radius * 2))

        # Magnet indicator
        if self.magnet_timer > 0:
            for hr in range(2):
                mag_surf = pygame.Surface((200, 200), pygame.SRCALPHA)
                pygame.draw.circle(mag_surf, (*NEON_MAGENTA, 50),
                                   (100, 100), 90 + int(math.sin(pygame.time.get_ticks() / 200) * 5), 2)
                surface.blit(mag_surf, (self.x - 100, self.y - 100))

        # Boost indicator
        if self.boost_timer > 0:
            for _ in range(3):
                trail_x = self.x - 30 - random.randint(0, 20)
                trail_y = self.y + random.randint(-10, 10)
                pygame.draw.circle(surface, NEON_ORANGE, (trail_x, trail_y), random.randint(2, 5))


# ============================================================
#                    Obstacle Types
# ============================================================
class Obstacle:
    def __init__(self, x, y, kind='pipe_top'):
        self.x = x
        self.y = y
        self.kind = kind
        self.w = 80
        self.h = 400
        self.passed = False
        self.alive = True
        self.anim_time = 0
        self.moving = False
        self.move_speed = 0
        self.move_range = 0
        self.base_y = y
        self.direction = 1
        self.rot = 0

    def update(self, speed_mult=1.0):
        self.x -= SCROLL_SPEED * speed_mult
        self.anim_time += 0.1

        if self.moving:
            self.y += self.move_speed * self.direction
            if abs(self.y - self.base_y) > self.move_range:
                self.direction = -self.direction

        if self.kind == 'spinner':
            self.rot += 3

        if self.x + self.w < -100:
            self.alive = False

    def rect(self):
        if self.kind == 'spinner':
            return pygame.Rect(int(self.x - 30), int(self.y - 30), 60, 60)
        return pygame.Rect(int(self.x), int(self.y), int(self.w), int(self.h))

    def draw(self, surface):
        if self.kind == 'pipe_top':
            self._draw_pipe(surface, is_top=True)
        elif self.kind == 'pipe_bottom':
            self._draw_pipe(surface, is_top=False)
        elif self.kind == 'laser':
            self._draw_laser(surface)
        elif self.kind == 'spinner':
            self._draw_spinner(surface)
        elif self.kind == 'wall':
            self._draw_wall(surface)

    def _draw_pipe(self, surface, is_top=True):
        rect = pygame.Rect(int(self.x), int(self.y), int(self.w), int(self.h))

        # هاله
        for hr in range(3, 0, -1):
            glow = pygame.Surface((rect.w + hr * 15, rect.h + hr * 15), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*NEON_PURPLE, 50 - hr * 12),
                             (0, 0, rect.w + hr * 15, rect.h + hr * 15), border_radius=8)
            surface.blit(glow, (rect.x - hr * 7, rect.y - hr * 7))

        # بدنه
        pygame.draw.rect(surface, (30, 15, 60), rect, border_radius=8)
        pygame.draw.rect(surface, NEON_PURPLE, rect, 3, border_radius=8)
        pygame.draw.rect(surface, WHITE, rect, 1, border_radius=8)

        # خطوط
        for i in range(0, int(self.h), 30):
            pygame.draw.line(surface, NEON_CYAN,
                             (rect.x + 5, rect.y + i + self.anim_time * 20 % 30),
                             (rect.right - 5, rect.y + i + self.anim_time * 20 % 30), 1)

        # نوک
        if is_top:
            tip_rect = pygame.Rect(int(self.x - 8), int(self.y + self.h - 25), int(self.w + 16), 25)
        else:
            tip_rect = pygame.Rect(int(self.x - 8), int(self.y), int(self.w + 16), 25)
        pygame.draw.rect(surface, (50, 25, 100), tip_rect, border_radius=6)
        pygame.draw.rect(surface, NEON_PURPLE, tip_rect, 3, border_radius=6)

    def _draw_laser(self, surface):
        # لیزر افقی
        rect = pygame.Rect(int(self.x), int(self.y), int(self.w), int(self.h))

        pulse = 1 + math.sin(self.anim_time * 5) * 0.2

        # هاله
        glow = pygame.Surface((rect.w + 30, rect.h + 30), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*NEON_RED, 100),
                         (0, 0, rect.w + 30, rect.h + 30), border_radius=4)
        surface.blit(glow, (rect.x - 15, rect.y - 15))

        # بدنه
        pygame.draw.rect(surface, (80, 10, 10), rect)
        pygame.draw.rect(surface, NEON_RED, rect, 3)

        # خط لیزر
        line_y = rect.centery
        for i in range(3):
            width = int(6 * pulse) - i * 2
            if width > 0:
                pygame.draw.line(surface, WHITE if i == 0 else NEON_RED,
                                 (rect.x, line_y), (rect.right, line_y), width)

    def _draw_spinner(self, surface):
        cx = self.x
        cy = self.y
        r = 30

        # هاله
        for hr in range(3, 0, -1):
            glow = pygame.Surface((r * 2 + hr * 15, r * 2 + hr * 15), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*NEON_ORANGE, 50 - hr * 12),
                               ((r * 2 + hr * 15) // 2, (r * 2 + hr * 15) // 2), r + hr * 7)
            surface.blit(glow, (cx - r - hr * 7, cy - r - hr * 7))

        # مرکز
        pygame.draw.circle(surface, (60, 30, 10), (int(cx), int(cy)), 10)
        pygame.draw.circle(surface, NEON_ORANGE, (int(cx), int(cy)), 10, 3)

        # پره‌های چرخان
        rad = math.radians(self.rot)
        for i in range(4):
            angle = rad + i * math.pi / 2
            ex = cx + math.cos(angle) * r
            ey = cy + math.sin(angle) * r
            pygame.draw.line(surface, NEON_ORANGE, (cx, cy), (ex, ey), 6)
            pygame.draw.circle(surface, WHITE, (int(ex), int(ey)), 4)

    def _draw_wall(self, surface):
        rect = pygame.Rect(int(self.x), int(self.y), int(self.w), int(self.h))

        for hr in range(3, 0, -1):
            glow = pygame.Surface((rect.w + hr * 15, rect.h + hr * 15), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*NEON_BLUE, 50 - hr * 12),
                             (0, 0, rect.w + hr * 15, rect.h + hr * 15), border_radius=8)
            surface.blit(glow, (rect.x - hr * 7, rect.y - hr * 7))

        pygame.draw.rect(surface, (15, 25, 60), rect, border_radius=8)
        pygame.draw.rect(surface, NEON_BLUE, rect, 3, border_radius=8)
        pygame.draw.rect(surface, WHITE, rect, 1, border_radius=8)

        # خطوط زیگزاگ
        for i in range(0, int(self.h), 40):
            y1 = rect.y + i
            y2 = rect.y + i + 20
            if y2 < rect.bottom:
                pygame.draw.line(surface, NEON_CYAN,
                                 (rect.x + 5, y1), (rect.right - 5, y2), 2)


# ============================================================
#                    Coin
# ============================================================
class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 15
        self.alive = True
        self.anim_time = 0
        self.pulse = 0

    def update(self, speed_mult=1.0):
        self.x -= SCROLL_SPEED * speed_mult
        self.anim_time += 0.15
        self.pulse += 0.1
        if self.x < -50:
            self.alive = False

    def rect(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius),
                           self.radius * 2, self.radius * 2)

    def draw(self, surface):
        r = self.radius + int(math.sin(self.pulse) * 2)

        # هاله
        for hr in range(3, 0, -1):
            glow_size = r * 2 + hr * 8
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*NEON_YELLOW, 60 - hr * 15),
                               (glow_size // 2, glow_size // 2), glow_size // 2)
            surface.blit(glow, (self.x - glow_size // 2, self.y - glow_size // 2))

        # بدنه سکه
        pygame.draw.circle(surface, (180, 140, 0), (int(self.x), int(self.y)), r)
        pygame.draw.circle(surface, NEON_YELLOW, (int(self.x), int(self.y)), r, 3)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), r, 1)

        # علامت دلار
        draw_text(surface, "$", 18, self.x, self.y - 10, WHITE, center=True, bold=True)


# ============================================================
#                    PowerUp
# ============================================================
class PowerUp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 20
        self.alive = True
        self.pulse = 0
        self.type = random.choices(
            ['shield', 'boost', 'slowmo', 'magnet', 'life'],
            weights=[3, 3, 2, 2, 1]
        )[0]

    def update(self, speed_mult=1.0):
        self.x -= SCROLL_SPEED * speed_mult
        self.pulse += 0.15
        if self.x < -50:
            self.alive = False

    def rect(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius),
                           self.radius * 2, self.radius * 2)

    def draw(self, surface):
        colors = {
            'shield': NEON_GREEN,
            'boost': NEON_ORANGE,
            'slowmo': NEON_BLUE,
            'magnet': NEON_MAGENTA,
            'life': NEON_RED,
        }
        icons = {
            'shield': 'S',
            'boost': 'B',
            'slowmo': 'W',
            'magnet': 'M',
            'life': '+',
        }
        color = colors[self.type]
        r = self.radius + int(math.sin(self.pulse) * 3)

        for hr in range(3, 0, -1):
            glow_size = r * 2 + hr * 10
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 60 - hr * 15),
                               (glow_size // 2, glow_size // 2), glow_size // 2)
            surface.blit(glow, (self.x - glow_size // 2, self.y - glow_size // 2))

        pygame.draw.circle(surface, (color[0] // 4, color[1] // 4, color[2] // 4),
                           (int(self.x), int(self.y)), r)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), r, 3)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), r, 1)

        draw_text(surface, icons[self.type], 18, self.x, self.y - 10, WHITE, center=True, bold=True)


# ============================================================
#                    Boss
# ============================================================
class Boss:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = 120
        self.h = 120
        self.hp = 5
        self.max_hp = 5
        self.alive = True
        self.anim_time = 0
        self.hit_flash = 0
        self.shoot_timer = 0
        self.bullets = []
        self.direction = -1

    def update(self, speed_mult=1.0):
        self.anim_time += 0.1

        # حرکت
        self.y += math.sin(self.anim_time * 2) * 2

        # نزدیک شدن به بازیکن
        self.x -= SCROLL_SPEED * 0.5 * speed_mult

        if self.hit_flash > 0:
            self.hit_flash -= 1

        # شلیک
        self.shoot_timer += 1
        if self.shoot_timer > 90:
            self.shoot_timer = 0
            # شلیک به سمت بازیکن
            self.bullets.append(BossBullet(self.x, self.y))

        # آپدیت گلوله‌ها
        for b in self.bullets[:]:
            b.update()
            if not b.alive:
                self.bullets.remove(b)

        if self.x < -200:
            self.alive = False

    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h / 2), self.w, self.h)

    def take_damage(self):
        self.hp -= 1
        self.hit_flash = 10
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surface):
        color = WHITE if self.hit_flash > 0 else NEON_RED

        # هاله
        for hr in range(4, 0, -1):
            glow = pygame.Surface((self.w + hr * 20, self.h + hr * 20), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*color, 50 - hr * 10),
                                (0, 0, self.w + hr * 20, self.h + hr * 20))
            surface.blit(glow, (self.x - self.w / 2 - hr * 10, self.y - self.h / 2 - hr * 10))

        # بدنه اصلی (هلیکوپتر جنگی)
        body_rect = pygame.Rect(int(self.x - 50), int(self.y - 30), 100, 60)
        pygame.draw.rect(surface, (60, 10, 20), body_rect, border_radius=10)
        pygame.draw.rect(surface, color, body_rect, 4, border_radius=10)

        # چرخاننده‌های اصلی
        rad = math.radians(self.anim_time * 100)
        for i in range(2):
            angle = rad + i * math.pi
            ex = self.x + math.cos(angle) * 60
            ey = self.y - 40 + math.sin(angle) * 10
            ex2 = self.x - math.cos(angle) * 60
            ey2 = self.y - 40 - math.sin(angle) * 10
            pygame.draw.line(surface, color, (ex, ey), (ex2, ey2), 5)

        # چرخاننده دم
        for i in range(3):
            angle = rad + i * 2 * math.pi / 3
            ex = self.x + 70 + math.cos(angle) * 15
            ey = self.y + 15 + math.sin(angle) * 15
            pygame.draw.line(surface, NEON_ORANGE, (self.x + 70, self.y + 15), (ex, ey), 3)

        # چشم‌های جنگی
        pygame.draw.circle(surface, NEON_RED, (int(self.x - 20), int(self.y)), 8)
        pygame.draw.circle(surface, WHITE, (int(self.x - 20), int(self.y)), 4)

        # نوار HP
        bar_w = 100
        bar_h = 8
        bar_x = self.x - bar_w / 2
        bar_y = self.y - self.h / 2 - 20
        pygame.draw.rect(surface, (40, 10, 10), (bar_x, bar_y, bar_w, bar_h))
        ratio = self.hp / self.max_hp
        pygame.draw.rect(surface, NEON_RED, (bar_x, bar_y, bar_w * ratio, bar_h))
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, bar_h), 2)

        # گلوله‌ها
        for b in self.bullets:
            b.draw(surface)


class BossBullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = -4
        self.vy = random.uniform(-1, 1)
        self.radius = 8
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.x < -50:
            self.alive = False

    def rect(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius),
                           self.radius * 2, self.radius * 2)

    def draw(self, surface):
        # هاله
        for hr in range(3, 0, -1):
            glow_size = self.radius * 2 + hr * 6
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*NEON_MAGENTA, 80 - hr * 20),
                               (glow_size // 2, glow_size // 2), glow_size // 2)
            surface.blit(glow, (self.x - glow_size // 2, self.y - glow_size // 2))

        pygame.draw.circle(surface, NEON_MAGENTA, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 2)


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
_bg_cache = None
_bg_time = 0
def build_sky_bg(day_phase=0):
    """day_phase: 0=روز, 1=غروب, 2=شب"""
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    if day_phase == 0:  # روز
        colors = [(80, 180, 255), (150, 220, 255), (200, 240, 255)]
    elif day_phase == 1:  # غروب
        colors = [(255, 100, 80), (255, 150, 100), (255, 200, 150)]
    else:  # شب
        colors = [(10, 10, 30), (20, 20, 50), (30, 30, 70)]

    for y in range(HEIGHT):
        t = y / HEIGHT
        c1, c2 = colors[0], colors[-1]
        # interp
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (WIDTH, y))

    # خورشید یا ماه
    if day_phase == 0 or day_phase == 1:
        sun_x = WIDTH - 200
        sun_y = 150
        # خورشید نئونی
        for hr in range(5, 0, -1):
            glow = pygame.Surface((200 + hr * 15, 200 + hr * 15), pygame.SRCALPHA)
            color = NEON_YELLOW if day_phase == 0 else NEON_ORANGE
            pygame.draw.circle(glow, (*color, 60 - hr * 10),
                               ((200 + hr * 15) // 2, (200 + hr * 15) // 2), 80 + hr * 7)
            surf.blit(glow, (sun_x - 80 - hr * 7, sun_y - 80 - hr * 7))
        pygame.draw.circle(surf, WHITE, (sun_x, sun_y), 60)
        pygame.draw.circle(surf, NEON_YELLOW, (sun_x, sun_y), 55)
    else:
        # ماه
        moon_x = WIDTH - 200
        moon_y = 150
        for hr in range(5, 0, -1):
            glow = pygame.Surface((200 + hr * 15, 200 + hr * 15), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*NEON_CYAN, 60 - hr * 10),
                               ((200 + hr * 15) // 2, (200 + hr * 15) // 2), 70 + hr * 7)
            surf.blit(glow, (moon_x - 70 - hr * 7, moon_y - 70 - hr * 7))
        pygame.draw.circle(surf, WHITE, (moon_x, moon_y), 55)
        pygame.draw.circle(surf, (220, 220, 240), (moon_x, moon_y), 50)
        # دهانه‌ها
        for _ in range(5):
            cx = moon_x + random.randint(-30, 30)
            cy = moon_y + random.randint(-30, 30)
            pygame.draw.circle(surf, (180, 180, 200), (cx, cy), random.randint(3, 6))

    return surf


_bg_cache = {}
def get_sky_bg(phase):
    if phase not in _bg_cache:
        _bg_cache[phase] = build_sky_bg(phase)
    return _bg_cache[phase]


def draw_clouds(surface, scroll_offset):
    """ابرهای پارالاکس"""
    cloud_positions = [
        (0, 100, 1.0),
        (200, 150, 0.8),
        (400, 80, 1.2),
        (600, 200, 0.9),
        (800, 120, 1.1),
        (1000, 170, 1.0),
    ]
    for base_x, base_y, speed in cloud_positions:
        x = (base_x - scroll_offset * speed) % (WIDTH + 200) - 100
        y = base_y
        # ابر نئونی
        for hr in range(3, 0, -1):
            glow = pygame.Surface((200 + hr * 15, 80 + hr * 15), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*WHITE, 30 - hr * 8),
                                (0, 0, 200 + hr * 15, 80 + hr * 15))
            surface.blit(glow, (x - hr * 7, y - hr * 7))
        pygame.draw.ellipse(surface, (60, 80, 120), (x, y, 200, 80))
        pygame.draw.ellipse(surface, (100, 130, 180), (x + 30, y + 15, 140, 50))
        pygame.draw.ellipse(surface, (80, 100, 150), (x + 80, y + 5, 100, 40))


def draw_mountains(surface, scroll_offset):
    """کوه‌های پارالاکس"""
    base_y = GROUND_Y - 100
    for i in range(15):
        x = i * 150 - (scroll_offset * 0.3) % 150
        height = 100 + (i % 3) * 40
        pts = [
            (x, base_y + 50),
            (x + 75, base_y - height),
            (x + 150, base_y + 50),
        ]
        # هاله
        for hr in range(3, 0, -1):
            glow = pygame.Surface((160 + hr * 15, 160 + hr * 15), pygame.SRCALPHA)
            pygame.draw.polygon(glow, (*NEON_PURPLE, 30 - hr * 8),
                                [(15, 75), (80, 0), (145, 75)])
            surface.blit(glow, (x - hr * 7, base_y - height - hr * 7))
        pygame.draw.polygon(surface, (30, 15, 50), pts)
        pygame.draw.polygon(surface, NEON_PURPLE, pts, 2)
        # برف روی قله
        tip_pts = [
            (x + 65, base_y - height + 15),
            (x + 75, base_y - height),
            (x + 85, base_y - height + 15),
        ]
        pygame.draw.polygon(surface, WHITE, tip_pts)


def draw_ground(surface, scroll_offset):
    """زمین با حرکت"""
    # گرادیان زمین
    for y in range(GROUND_Y, HEIGHT):
        t = (y - GROUND_Y) / (HEIGHT - GROUND_Y)
        c = (int(20 + 30 * t), int(15 + 20 * t), int(30 + 40 * t))
        pygame.draw.line(surface, c, (0, y), (WIDTH, y))

    # خط بالای زمین
    pygame.draw.line(surface, NEON_GREEN, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)

    # علامت‌های حرکت
    for i in range(20):
        x = (i * 60 - scroll_offset) % (WIDTH + 60)
        y = GROUND_Y + 15 + (i % 2) * 10
        pygame.draw.line(surface, NEON_GREEN, (x, y), (x + 30, y), 2)


# ============================================================
#                    Menu
# ============================================================
def show_menu():
    menu_time = 0
    btn_start = Button(WIDTH // 2, HEIGHT // 2 + 30, 320, 55, "START FLIGHT", NEON_CYAN, NEON_GREEN, 28)
    btn_history = Button(WIDTH // 2, HEIGHT // 2 + 95, 320, 45, "HISTORY", NEON_BLUE, NEON_CYAN, 22)
    btn_settings = Button(WIDTH // 2, HEIGHT // 2 + 150, 320, 45, "SETTINGS", NEON_PURPLE, NEON_PINK, 22)
    btn_achievements = Button(WIDTH // 2, HEIGHT // 2 + 205, 320, 45, "ACHIEVEMENTS", NEON_YELLOW, NEON_ORANGE, 22)
    btn_quit = Button(WIDTH // 2, HEIGHT // 2 + 260, 320, 42, "QUIT", NEON_RED, NEON_ORANGE, 20)
    btn_fullscreen = Button(WIDTH - 40, 30, 40, 40, "[]", NEON_PURPLE, NEON_CYAN, 20)

    # هلیکوپتر تزئینی
    demo_heli = Helicopter()

    while True:
        game_surface.fill(DARK_BG)
        t = pygame.time.get_ticks() / 1000
        menu_time += 1
        mouse_pos = get_game_mouse_pos()

        # آسمان
        phase = int((t / 20) % 3)
        game_surface.blit(get_sky_bg(phase), (0, 0))

        # ابرها
        draw_clouds(game_surface, t * 50)
        draw_mountains(game_surface, t * 50)
        draw_ground(game_surface, t * 50)

        # هلیکوپتر تزئینی
        demo_heli.y = HEIGHT // 2 + math.sin(t * 2) * 30
        demo_heli.rotor_angle = (t * 1000) % 360
        demo_heli.draw(game_surface)

        # عنوان
        title_y = 130 + math.sin(t * 2) * 8
        draw_text(game_surface, "NEON", 72, WIDTH // 2 - 100, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "HELICOPTER", 72, WIDTH // 2 + 130, title_y, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, "FLAP  /  DODGE  /  SURVIVE", 20, WIDTH // 2, title_y + 65,
                  (200, 200, 220), center=True)

        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 22, WIDTH // 2, title_y + 115,
                      NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, f"DISTANCE: {total_distance[0]}m   COINS: {total_coins[0]}",
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
                total_distance[0] = 0
                total_coins[0] = 0
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

        draw_text(game_surface, "FLIGHT HISTORY", 46, WIDTH // 2, 35, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, f"Total flights: {len(game_history)}", 16, WIDTH // 2, 72, NEON_YELLOW, center=True)

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
                if score >= 2000:
                    rank_color, rank = NEON_PINK, "S"
                elif score >= 1000:
                    rank_color, rank = NEON_YELLOW, "A"
                elif score >= 500:
                    rank_color, rank = NEON_GREEN, "B"
                elif score >= 200:
                    rank_color, rank = NEON_CYAN, "C"
                else:
                    rank_color, rank = (150, 150, 180), "D"
                pygame.draw.rect(game_surface, (15, 8, 30), (ix, iy, iw, item_h - 8), border_radius=6)
                pygame.draw.rect(game_surface, rank_color, (ix, iy, iw, item_h - 8), 2, border_radius=6)
                draw_text(game_surface, rank, 36, ix + 35, iy + (item_h - 8) // 2, rank_color, center=True, glow=True)
                draw_text(game_surface, f"SCORE: {score}", 20, ix + 70, iy + 6, WHITE)
                draw_text(game_surface, f"DIST: {entry.get('distance', 0)}m   TIME: {entry.get('duration', 0)}s",
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
            draw_text(game_surface, "No flights yet", 28, WIDTH // 2, HEIGHT // 2, (150, 150, 180), center=True)

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
    heli = Helicopter()
    obstacles = []
    coins = []
    powerups = []
    boss = None
    boss_bullets = []

    # آمار
    score = 0
    display_score = 0
    distance = 0
    coins_collected = 0
    max_combo = 0
    combo = 0
    total_frames = 0

    # دیفیولتی
    base_speed = 4.0
    speed_mult = 1.0
    spawn_timer = 0
    coin_spawn_timer = 0
    powerup_spawn_timer = 0

    # Checkpoint
    next_checkpoint = 500  # هر 500 متر
    checkpoints_reached = 0

    # Boss
    next_boss = 5  # هر 5 checkpoint
    boss_active = False

    # روز/شب
    day_phase = 0
    day_timer = 0

    # حالت
    game_over = False
    paused = False
    final_score = 0
    final_distance = 0
    hit_something = False
    perfect_run = True

    # افکت‌ها
    screen_shake = 0
    flash = 0
    new_achs = []
    notifications = []
    go_anim = 0
    game_saved = False
    checkpoint_banner = 0

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
        add_game_to_history(score, distance, total_frames // FPS, new_achs)

    def spawn_obstacle():
        # انواع موانع با شانس
        kinds = ['pipe', 'pipe', 'pipe', 'laser', 'spinner', 'wall']
        kind = random.choice(kinds)

        if kind == 'pipe':
            gap = 250 - int(distance / 100) * 10
            gap = max(150, gap)
            top_h = random.randint(100, HEIGHT - gap - 200)
            obstacles.append(Obstacle(WIDTH + 50, 0, 'pipe_top'))
            obstacles[-1].h = top_h
            obstacles.append(Obstacle(WIDTH + 50, top_h + gap, 'pipe_bottom'))
            obstacles[-1].h = HEIGHT - top_h - gap - 60
        elif kind == 'laser':
            y = random.randint(200, HEIGHT - 200)
            obstacles.append(Obstacle(WIDTH + 50, y, 'laser'))
            obstacles[-1].h = 20
        elif kind == 'spinner':
            y = random.randint(200, HEIGHT - 200)
            obstacles.append(Obstacle(WIDTH + 50, y, 'spinner'))
            obstacles[-1].moving = True
            obstacles[-1].move_speed = 1
            obstacles[-1].move_range = 80
            obstacles[-1].base_y = y
        elif kind == 'wall':
            h = random.randint(100, 200)
            y = random.randint(200, HEIGHT - h - 100)
            obstacles.append(Obstacle(WIDTH + 50, y, 'wall'))
            obstacles[-1].h = h

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
                    heli.flap()
                    try_unlock('first_flap')
                    play_sound('flap')
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
                    heli.flap()
                    try_unlock('first_flap')
                    play_sound('flap')

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

            # سرعت افزایش با فاصله
            speed_mult = 1.0 + distance / 2000
            speed_mult *= settings['difficulty']

            # آپدیت هلیکوپتر
            heli.update()

            # آپدیت روز/شب
            day_timer += 1
            if day_timer > FPS * 20:
                day_timer = 0
                day_phase = (day_phase + 1) % 3

            # فاصله
            distance += SCROLL_SPEED * speed_mult / FPS * 10
            total_distance[0] += SCROLL_SPEED * speed_mult / FPS * 10

            # اسپاون موانع
            spawn_timer += 1
            spawn_interval = max(60, 100 - int(distance / 100))
            if spawn_timer > spawn_interval / speed_mult:
                spawn_timer = 0
                spawn_obstacle()

            # اسپاون سکه
            coin_spawn_timer += 1
            if coin_spawn_timer > 40:
                coin_spawn_timer = 0
                if random.random() < 0.5:
                    coins.append(Coin(WIDTH + 50, random.randint(150, HEIGHT - 150)))

            # اسپاون Power-up
            powerup_spawn_timer += 1
            if powerup_spawn_timer > 300:
                powerup_spawn_timer = 0
                if random.random() < 0.4:
                    powerups.append(PowerUp(WIDTH + 50, random.randint(150, HEIGHT - 150)))

            # آپدیت موانع
            for obs in obstacles[:]:
                obs.update(speed_mult)
                if not obs.alive:
                    obstacles.remove(obs)
                    continue

                # برخورد
                if heli.rect().colliderect(obs.rect()):
                    if heli.has_shield:
                        heli.has_shield = False
                        obs.alive = False
                        obstacles.remove(obs)
                        play_sound('shield')
                        flash = 150
                        for _ in range(30):
                            spawn_particles(heli.x, heli.y, NEON_GREEN, 1, 1.5, 1.2, 1.2)
                    else:
                        heli.alive = False
                        game_over = True
                        final_score = score
                        final_distance = int(distance)
                        highscore[0] = max(highscore[0], score)
                        hit_something = True
                        play_sound('hit')
                        if settings['screen_shake']:
                            screen_shake = 25
                        flash = 200
                        for _ in range(40):
                            spawn_particles(heli.x, heli.y, NEON_RED, 1, 2.0, 1.5, 1.5)
                        save_current()
                        game_saved = True
                        play_sound('gameover')
                        go_anim = 0

                # رد شدن (امتیاز)
                if not obs.passed and obs.x + obs.w < heli.x:
                    obs.passed = True
                    score += 5
                    combo += 1
                    max_combo = max(max_combo, combo)

            # آپدیت سکه‌ها
            for c in coins[:]:
                c.update(speed_mult)
                if not c.alive:
                    coins.remove(c)
                    continue

                # Magnet
                if heli.magnet_timer > 0:
                    dx = heli.x - c.x
                    dy = heli.y - c.y
                    dist = math.hypot(dx, dy)
                    if dist < 250:
                        c.x += dx / dist * 8
                        c.y += dy / dist * 8

                # برخورد
                if heli.rect().colliderect(c.rect()):
                    coins_collected += 1
                    total_coins[0] += 1
                    score += 10
                    play_sound('coin')
                    for _ in range(10):
                        spawn_particles(c.x, c.y, NEON_YELLOW, 1, 1.5, 1.0, 0.8)
                    coins.remove(c)
                    if coins_collected >= 10: try_unlock('coin_10')
                    if coins_collected >= 50: try_unlock('coin_50')
                    if coins_collected >= 200: try_unlock('coin_200')

            # آپدیت Power-up
            for p in powerups[:]:
                p.update(speed_mult)
                if not p.alive:
                    powerups.remove(p)
                    continue

                if heli.rect().colliderect(p.rect()):
                    if p.type == 'shield':
                        heli.has_shield = True
                        try_unlock('shield_use')
                    elif p.type == 'boost':
                        heli.boost_timer = 300
                    elif p.type == 'slowmo':
                        heli.slowmo_timer = 300
                    elif p.type == 'magnet':
                        heli.magnet_timer = 300
                        try_unlock('magnet_use')
                    elif p.type == 'life':
                        heli.lives += 1
                    play_sound('powerup')
                    for _ in range(20):
                        spawn_particles(p.x, p.y, NEON_GREEN, 1, 1.5)
                    powerups.remove(p)

            # Boss
            if not boss_active and checkpoints_reached >= next_boss:
                boss = Boss(WIDTH + 100, HEIGHT // 2)
                boss_active = True
                play_sound('boss_alert')
                flash = 100
                if settings['screen_shake']:
                    screen_shake = 20

            if boss and boss.alive:
                boss.update(speed_mult)

                # برخورد
                if heli.rect().colliderect(boss.rect()):
                    if heli.has_shield:
                        heli.has_shield = False
                    else:
                        heli.alive = False
                        game_over = True
                        final_score = score
                        final_distance = int(distance)
                        highscore[0] = max(highscore[0], score)
                        play_sound('hit')
                        if settings['screen_shake']:
                            screen_shake = 30
                        flash = 200
                        save_current()
                        game_saved = True
                        play_sound('gameover')
                        go_anim = 0

                # گلوله‌های باس
                for b in boss.bullets[:]:
                    if heli.rect().colliderect(b.rect()):
                        boss.bullets.remove(b)
                        if heli.has_shield:
                            heli.has_shield = False
                        else:
                            heli.alive = False
                            game_over = True
                            final_score = score
                            final_distance = int(distance)
                            highscore[0] = max(highscore[0], score)
                            save_current()
                            game_saved = True
                            play_sound('gameover')
                            go_anim = 0

                if not boss.alive:
                    # باس کشته شد
                    score += 1000
                    total_bosses[0] += 1
                    try_unlock('boss_kill')
                    boss = None
                    boss_active = False
                    next_boss += 5
                    play_sound('checkpoint')
                    for _ in range(50):
                        spawn_particles(WIDTH // 2, HEIGHT // 2, NEON_RED, 1, 2.5, 2.0, 2.0)

            # Checkpoint
            if distance >= next_checkpoint:
                checkpoints_reached += 1
                next_checkpoint += 500
                score += 100
                checkpoint_banner = 90
                play_sound('checkpoint')
                if checkpoints_reached >= 1: try_unlock('checkpoint_1')
                if checkpoints_reached >= 5: try_unlock('checkpoint_5')
                if checkpoints_reached >= 10: try_unlock('checkpoint_10')

            # دستاوردها
            if distance >= 100 and perfect_run: try_unlock('perfect_100')
            if distance >= 100: try_unlock('distance_100')
            if distance >= 500: try_unlock('distance_500')
            if distance >= 2000: try_unlock('distance_2000')
            if day_phase == 2 and distance > 500: try_unlock('night_flyer')

            # ذرات
            for p in active_particles[:]:
                p.update()
                if not p.active:
                    active_particles.remove(p)

            if screen_shake > 0:
                screen_shake -= 1
            if flash > 0:
                flash -= 8
            if checkpoint_banner > 0:
                checkpoint_banner -= 1

        # ============================================================
        #                    رسم
        # ============================================================
        game_surface.fill(DARK_BG)
        offset_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        offset_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0

        play_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # آسمان
        play_layer.blit(get_sky_bg(day_phase), (0, 0))

        # ابرها و کوه‌ها
        draw_clouds(play_layer, distance * 8)
        draw_mountains(play_layer, distance * 4)

        # موانع
        for obs in obstacles:
            obs.draw(play_layer)

        # سکه‌ها
        for c in coins:
            c.draw(play_layer)

        # Power-upها
        for p in powerups:
            p.draw(play_layer)

        # Boss
        if boss and boss.alive:
            boss.draw(play_layer)

        # زمین
        draw_ground(play_layer, distance * 10)

        # هلیکوپتر
        if heli.alive:
            heli.draw(play_layer)

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
        hud_panel = pygame.Surface((WIDTH, 70), pygame.SRCALPHA)
        for y in range(70):
            alpha = int(180 * (1 - y / 70))
            pygame.draw.line(hud_panel, (5, 10, 25, alpha), (0, y), (WIDTH, y))
        game_surface.blit(hud_panel, (0, 0))
        pygame.draw.line(game_surface, NEON_CYAN, (0, 70), (WIDTH, 70), 1)

        # عنوان
        draw_text(game_surface, "NEON HELICOPTER", 20, 25, 10, NEON_CYAN, glow=True)
        draw_text(game_surface, f"DIST: {int(distance)}m   CP: {checkpoints_reached}",
                  12, 25, 38, NEON_YELLOW)

        # Score
        draw_text(game_surface, "SCORE", 14, WIDTH - 25, 10, NEON_CYAN)
        draw_text(game_surface, f"{display_score}", 26, WIDTH - 25, 28, WHITE, glow=True)

        # Coins
        draw_text(game_surface, f"$ {coins_collected}", 20, WIDTH // 2, 30,
                  NEON_YELLOW, center=True, glow=True)

        # قدرت‌ها
        y_pos = 80
        if heli.has_shield:
            draw_text(game_surface, "SHIELD ACTIVE", 14, 25, y_pos, NEON_GREEN)
            y_pos += 20
        if heli.boost_timer > 0:
            draw_text(game_surface, f"BOOST {heli.boost_timer // FPS + 1}s", 14, 25, y_pos, NEON_ORANGE)
            y_pos += 20
        if heli.slowmo_timer > 0:
            draw_text(game_surface, f"SLOWMO {heli.slowmo_timer // FPS + 1}s", 14, 25, y_pos, NEON_BLUE)
            y_pos += 20
        if heli.magnet_timer > 0:
            draw_text(game_surface, f"MAGNET {heli.magnet_timer // FPS + 1}s", 14, 25, y_pos, NEON_MAGENTA)

        # Checkpoint banner
        if checkpoint_banner > 0:
            pulse = 1 + math.sin(t * 15) * 0.1
            draw_text(game_surface, f"CHECKPOINT {checkpoints_reached}!", int(60 * pulse),
                      WIDTH // 2, HEIGHT // 2 - 50, NEON_GREEN, center=True, glow=True)

        # راهنما
        if total_frames < 200:
            draw_text(game_surface, "SPACE or CLICK to flap!", 20, WIDTH // 2, HEIGHT - 100,
                      NEON_CYAN, center=True, glow=True)

        # Notifications
        for i, notif in enumerate(notifications):
            ny = 80 + i * 55
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
            draw_text(game_surface, "CRASHED!", 60, WIDTH // 2, box_y + 55,
                      NEON_RED, center=True, glow=True)
            draw_text(game_surface, f"SCORE: {final_score}", 32,
                      WIDTH // 2, box_y + 120, WHITE, center=True)
            draw_text(game_surface, f"DISTANCE: {final_distance}m   COINS: {coins_collected}",
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