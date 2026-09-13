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

BASE_W, BASE_H = 1000, 700
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("NEON PONG")
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

# --- ابعاد زمین ---
FIELD_MARGIN = 40
FIELD_X = FIELD_MARGIN
FIELD_Y = FIELD_MARGIN
FIELD_W = WIDTH - FIELD_MARGIN * 2
FIELD_H = HEIGHT - FIELD_MARGIN * 2
FIELD_RIGHT = FIELD_X + FIELD_W
FIELD_BOTTOM = FIELD_Y + FIELD_H
CENTER_X = WIDTH // 2
CENTER_Y = HEIGHT // 2

# --- ذخیره ---
SAVE_FILE = "neon_pong_save.json"
settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'difficulty': 1.0,
    'screen_shake': True,
    'win_score': 7,
}
achievements = {
    'first_hit': {'name': 'FIRST HIT', 'desc': 'Hit the ball', 'unlocked': False, 'icon': '>'},
    'first_win': {'name': 'FIRST WIN', 'desc': 'Win your first match', 'unlocked': False, 'icon': 'W'},
    'win_5': {'name': 'CHAMPION', 'desc': 'Win 5 matches', 'unlocked': False, 'icon': 'W5'},
    'win_10': {'name': 'LEGEND', 'desc': 'Win 10 matches', 'unlocked': False, 'icon': 'W10'},
    'perfect': {'name': 'PERFECT', 'desc': 'Win without conceding a point', 'unlocked': False, 'icon': 'P'},
    'sweep': {'name': 'SWEEP', 'desc': 'Win 7-0', 'unlocked': False, 'icon': 'S7'},
    'rally_10': {'name': 'RALLY MASTER', 'desc': '10-hit rally', 'unlocked': False, 'icon': 'R10'},
    'rally_20': {'name': 'ENDURANCE', 'desc': '20-hit rally', 'unlocked': False, 'icon': 'R20'},
    'power_5': {'name': 'POWERED UP', 'desc': 'Collect 5 power-ups', 'unlocked': False, 'icon': 'P5'},
    'power_15': {'name': 'SUPERCHARGED', 'desc': 'Collect 15 power-ups', 'unlocked': False, 'icon': 'P15'},
    'speed_15': {'name': 'FAST BALL', 'desc': 'Ball reaches speed 15', 'unlocked': False, 'icon': 'F15'},
    'speed_20': {'name': 'SUPERSONIC', 'desc': 'Ball reaches speed 20', 'unlocked': False, 'icon': 'F20'},
    'multi_ball': {'name': 'MULTIBALL', 'desc': 'Activate multiball', 'unlocked': False, 'icon': 'M'},
    'beat_hard': {'name': 'BEAT HARD AI', 'desc': 'Beat hard AI', 'unlocked': False, 'icon': 'H'},
    'survive_2min': {'name': 'SURVIVOR', 'desc': 'Survive 2 minutes in a match', 'unlocked': False, 'icon': 'T'},
}
highscore = [0]
game_history = []
total_wins = [0]
total_rallies = [0]


def load_save():
    global settings, achievements, highscore, game_history, total_wins, total_rallies
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
            settings.update(data.get('settings', {}))
            for k, v in data.get('achievements', {}).items():
                if k in achievements:
                    achievements[k]['unlocked'] = v
            highscore[0] = data.get('highscore', 0)
            game_history = data.get('game_history', [])
            total_wins[0] = data.get('total_wins', 0)
            total_rallies[0] = data.get('total_rallies', 0)
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
                'total_wins': total_wins[0],
                'total_rallies': total_rallies[0],
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


def add_game_to_history(score, player_score, ai_score, duration, mode, new_achs):
    entry = {
        'score': score,
        'player_score': player_score,
        'ai_score': ai_score,
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
    sounds['paddle_hit'] = make_sound(600, 900, 0.08, 0.20, 'square')
    sounds['wall_hit'] = make_sound(400, 500, 0.06, 0.15, 'square')
    sounds['score'] = make_sound(800, 1500, 0.4, 0.25, 'sine')
    sounds['lose'] = make_sound(400, 100, 0.5, 0.30, 'saw')
    sounds['power'] = make_sound(600, 1600, 0.35, 0.22, 'sine')
    sounds['gameover'] = make_sound(500, 60, 1.5, 0.30, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['victory'] = make_sound(500, 1800, 0.8, 0.28, 'sine')
    sounds['countdown'] = make_sound(400, 400, 0.2, 0.20, 'square')

    bass = [73.4, 73.4, 65.4, 65.4, 82.4, 82.4, 73.4, 73.4]
    lead = [587, 698, 784, 698, 587, 523, 466, 523]
    music_sound[0] = make_music_loop(bass, lead, 0.2, 0.10)
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
#                    Paddle
# ============================================================
class Paddle:
    def __init__(self, x, y, is_player=True, color=NEON_CYAN):
        self.x = x
        self.y = y
        self.base_w = 15
        self.base_h = 100
        self.w = self.base_w
        self.h = self.base_h
        self.speed = 7
        self.is_player = is_player
        self.color = color
        self.vx = 0
        self.vy = 0
        self.big_timer = 0
        self.magnet_timer = 0
        self.hit_flash = 0
        self.ai_target_y = CENTER_Y
        self.ai_reaction = 0.15

    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h / 2),
                           self.w, self.h)

    def update(self, keys, mouse_y=None, use_mouse=True):
        # تایمرها
        if self.big_timer > 0:
            self.big_timer -= 1
            self.h = int(self.base_h * 1.6)
        else:
            self.h = self.base_h
        if self.magnet_timer > 0:
            self.magnet_timer -= 1
        if self.hit_flash > 0:
            self.hit_flash -= 1

        # ورودی
        old_y = self.y
        if self.is_player:
            if use_mouse and mouse_y is not None:
                # حرکت با ماوس
                target_y = mouse_y
                dy = target_y - self.y
                self.y += dy * 0.3
            else:
                # حرکت با کلید
                if keys[pygame.K_w] or keys[pygame.K_UP]:
                    self.y -= self.speed
                if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                    self.y += self.speed
        self.vy = self.y - old_y

        # محدودیت
        self.y = max(FIELD_Y + self.h / 2, min(FIELD_BOTTOM - self.h / 2, self.y))

    def ai_update(self, ball):
        # AI حریف
        target = ball.y
        # سخت‌تر = سریع‌تر و دقیق‌تر
        diff = settings['difficulty']
        if diff < 0.8:
            self.ai_reaction = 0.10
        elif diff < 1.2:
            self.ai_reaction = 0.15
        else:
            self.ai_reaction = 0.22

        # یه کم delay
        self.ai_target_y = target + random.uniform(-20, 20) * (1.5 - diff)
        dy = self.ai_target_y - self.y
        self.y += dy * self.ai_reaction
        self.y = max(FIELD_Y + self.h / 2, min(FIELD_BOTTOM - self.h / 2, self.y))

    def draw(self, surface):
        rect = self.rect()
        color = WHITE if self.hit_flash > 0 else self.color

        # هاله
        for r in range(3, 0, -1):
            glow = pygame.Surface((rect.w + 40 * r, rect.h + 40 * r), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*color, 40 - r * 10),
                             (0, 0, rect.w + 40 * r, rect.h + 40 * r),
                             border_radius=10)
            surface.blit(glow, (rect.x - 20 * r, rect.y - 20 * r))

        # بدنه
        pygame.draw.rect(surface, (color[0] // 4, color[1] // 4, color[2] // 4),
                         rect, border_radius=8)
        pygame.draw.rect(surface, color, rect, 3, border_radius=8)
        pygame.draw.rect(surface, WHITE, rect, 1, border_radius=8)

        # خط وسط
        mid_y = rect.centery
        pygame.draw.line(surface, WHITE, (rect.x + 4, mid_y), (rect.right - 4, mid_y), 1)

        # آیکون‌های حالت
        if self.big_timer > 0:
            draw_text(surface, "B", 12, rect.centerx, rect.top - 12, NEON_PURPLE, center=True)
        if self.magnet_timer > 0:
            draw_text(surface, "M", 12, rect.centerx, rect.top - 12, NEON_PINK, center=True)


# ============================================================
#                    Ball
# ============================================================
class Ball:
    def __init__(self, x, y, vx=0, vy=0, speed=6):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = 10
        self.base_speed = speed
        self.speed = speed
        self.trail = []
        self.stuck_to_paddle = None
        self.stuck_offset = 0
        self.color = NEON_YELLOW
        self.slow_timer = 0

    def update(self, slow_all=False):
        # آپدیت trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 12:
            self.trail.pop(0)

        if self.stuck_to_paddle:
            # توپ چسبیده
            p = self.stuck_to_paddle
            self.x = p.x + (self.w_offset if hasattr(self, 'w_offset') else
                            (p.w / 2 + self.radius + 5 if p.x < CENTER_X else -p.w / 2 - self.radius - 5))
            self.y = p.y + self.stuck_offset
            return

        # آپدیت موقعیت
        self.x += self.vx
        self.y += self.vy

        # برخورد با دیوارهای بالا و پایین
        if self.y - self.radius < FIELD_Y:
            self.y = FIELD_Y + self.radius
            self.vy = abs(self.vy)
            play_sound('wall_hit')
            spawn_particles(self.x, self.y, self.color, 5, 1.0, 0.8, 0.5)
        elif self.y + self.radius > FIELD_BOTTOM:
            self.y = FIELD_BOTTOM - self.radius
            self.vy = -abs(self.vy)
            play_sound('wall_hit')
            spawn_particles(self.x, self.y, self.color, 5, 1.0, 0.8, 0.5)

    def launch(self, direction=1):
        angle = random.uniform(-30, 30)
        rad = math.radians(angle)
        self.vx = math.cos(rad) * self.speed * direction
        self.vy = math.sin(rad) * self.speed
        self.stuck_to_paddle = None

    def rect(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius),
                           self.radius * 2, self.radius * 2)

    def draw(self, surface):
        # Trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / len(self.trail) * 0.6
            r = max(1, int(self.radius * alpha))
            color = (int(self.color[0] * alpha), int(self.color[1] * alpha), int(self.color[2] * alpha))
            pygame.draw.circle(surface, color, (int(tx), int(ty)), r)

        # هاله
        for r in range(3, 0, -1):
            glow_size = self.radius * 2 + r * 8
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*self.color, 80 - r * 20),
                               (glow_size // 2, glow_size // 2), glow_size // 2)
            surface.blit(glow, (self.x - glow_size // 2, self.y - glow_size // 2))

        # بدنه
        pygame.draw.circle(surface, (self.color[0] // 3, self.color[1] // 3, self.color[2] // 3),
                           (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius, 2)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 1)

        # درخشش وسط
        pygame.draw.circle(surface, WHITE, (int(self.x - 2), int(self.y - 2)), 3)


# ============================================================
#                    PowerUp
# ============================================================
class PowerUp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = random.choices(
            ['big_paddle', 'multi_ball', 'slow_ball', 'speed_ball', 'magnet'],
            weights=[3, 2, 2, 2, 2]
        )[0]
        self.radius = 18
        self.pulse = 0
        self.life = 600
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)

    def update(self):
        self.pulse += 0.15
        self.life -= 1
        self.x += self.vx
        self.y += self.vy
        # bounce
        if self.x - self.radius < FIELD_X or self.x + self.radius > FIELD_RIGHT:
            self.vx = -self.vx
        if self.y - self.radius < FIELD_Y or self.y + self.radius > FIELD_BOTTOM:
            self.vy = -self.vy

    def draw(self, surface):
        colors = {
            'big_paddle': NEON_PURPLE,
            'multi_ball': NEON_CYAN,
            'slow_ball': NEON_GREEN,
            'speed_ball': NEON_RED,
            'magnet': NEON_PINK,
        }
        icons = {
            'big_paddle': 'B',
            'multi_ball': '3',
            'slow_ball': 'S',
            'speed_ball': 'F',
            'magnet': 'M',
        }
        color = colors[self.type]
        r = self.radius + int(math.sin(self.pulse) * 3)

        # هاله
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
#                    Obstacle
# ============================================================
class Obstacle:
    def __init__(self, x, y, w, h, horizontal=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.horizontal = horizontal
        self.vx = random.uniform(-2, 2) if horizontal else 0
        self.vy = 0 if horizontal else random.uniform(-2, 2)
        self.base_rect = self.rect.copy()
        self.timer = 0

    def update(self):
        self.timer += 1
        self.rect.x += self.vx
        self.rect.y += self.vy
        # محدودیت‌ها
        if self.horizontal:
            if self.rect.x < FIELD_X or self.rect.right > FIELD_RIGHT:
                self.vx = -self.vx
                self.rect.x = max(FIELD_X, min(FIELD_RIGHT - self.rect.w, self.rect.x))
        else:
            if self.rect.y < FIELD_Y or self.rect.bottom > FIELD_BOTTOM:
                self.vy = -self.vy
                self.rect.y = max(FIELD_Y, min(FIELD_BOTTOM - self.rect.h, self.rect.y))

    def draw(self, surface):
        # هاله
        for r in range(3, 0, -1):
            glow = pygame.Surface((self.rect.w + 20 * r, self.rect.h + 20 * r), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*NEON_ORANGE, 30 - r * 8),
                             (0, 0, self.rect.w + 20 * r, self.rect.h + 20 * r),
                             border_radius=6)
            surface.blit(glow, (self.rect.x - 10 * r, self.rect.y - 10 * r))

        pygame.draw.rect(surface, (100, 50, 0), self.rect, border_radius=6)
        pygame.draw.rect(surface, NEON_ORANGE, self.rect, 3, border_radius=6)
        pygame.draw.rect(surface, WHITE, self.rect, 1, border_radius=6)


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
#                    Menu
# ============================================================
def show_menu():
    menu_time = 0
    btn_1p = Button(WIDTH // 2, HEIGHT // 2 - 60, 320, 55, "1 PLAYER", NEON_CYAN, NEON_GREEN, 26)
    btn_2p = Button(WIDTH // 2, HEIGHT // 2, 320, 55, "2 PLAYERS", NEON_YELLOW, NEON_ORANGE, 26)
    btn_history = Button(WIDTH // 2, HEIGHT // 2 + 75, 320, 45, "HISTORY", NEON_BLUE, NEON_CYAN, 20)
    btn_settings = Button(WIDTH // 2, HEIGHT // 2 + 130, 320, 45, "SETTINGS", NEON_PURPLE, NEON_PINK, 20)
    btn_achievements = Button(WIDTH // 2, HEIGHT // 2 + 185, 320, 45, "ACHIEVEMENTS", NEON_YELLOW, NEON_ORANGE, 20)
    btn_quit = Button(WIDTH // 2, HEIGHT // 2 + 240, 320, 42, "QUIT", NEON_RED, NEON_ORANGE, 18)
    btn_fullscreen = Button(WIDTH - 40, 30, 40, 40, "[]", NEON_PURPLE, NEON_CYAN, 20)

    # توپ تزئینی
    demo_balls = []
    for _ in range(3):
        demo_balls.append(Ball(
            random.uniform(FIELD_X + 100, FIELD_RIGHT - 100),
            random.uniform(FIELD_Y + 100, FIELD_BOTTOM - 100),
            random.uniform(-3, 3), random.uniform(-3, 3), 4
        ))

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

        # زمین
        pygame.draw.rect(game_surface, (5, 8, 20),
                         (FIELD_X, FIELD_Y, FIELD_W, FIELD_H),
                         border_radius=10)
        pygame.draw.rect(game_surface, NEON_CYAN,
                         (FIELD_X, FIELD_Y, FIELD_W, FIELD_H), 3, border_radius=10)

        # خط مرکزی
        for i in range(FIELD_Y, FIELD_BOTTOM, 20):
            pygame.draw.line(game_surface, (60, 80, 120),
                             (CENTER_X, i), (CENTER_X, i + 10), 2)

        # دایره‌ی وسط
        pygame.draw.circle(game_surface, (60, 80, 120), (CENTER_X, CENTER_Y), 80, 2)
        pygame.draw.circle(game_surface, (60, 80, 120), (CENTER_X, CENTER_Y), 5)

        # توپ‌های تزئینی
        for b in demo_balls:
            b.update()
            if b.x < FIELD_X or b.x > FIELD_RIGHT:
                b.vx = -b.vx
            if b.y < FIELD_Y or b.y > FIELD_BOTTOM:
                b.vy = -b.vy
            b.draw(game_surface)

        # عنوان
        title_y = 100 + math.sin(t * 2) * 8
        draw_text(game_surface, "NEON", 72, WIDTH // 2 - 100, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "PONG", 72, WIDTH // 2 + 100, title_y, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, "BATTLE ROYALE", 24, WIDTH // 2, title_y + 65, NEON_PINK, center=True, glow=True)

        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 20, WIDTH // 2, title_y + 105,
                      NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, f"WINS: {total_wins[0]}   RALLIES: {total_rallies[0]}",
                  14, WIDTH // 2, title_y + 130, NEON_PINK, center=True)

        for b in [btn_1p, btn_2p, btn_history, btn_settings, btn_achievements, btn_quit, btn_fullscreen]:
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
            if btn_1p.is_clicked(event):
                return '1p'
            if btn_2p.is_clicked(event):
                return '2p'
            if btn_history.is_clicked(event):
                show_history()
            if btn_settings.is_clicked(event):
                show_settings()
            if btn_achievements.is_clicked(event):
                show_achievements()
            if btn_quit.is_clicked(event):
                return 'quit'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return '1p'
                if event.key == pygame.K_2:
                    return '2p'
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
    slider_diff = Slider(WIDTH // 2, 360, 400, 12, (settings['difficulty'] - 0.5) / 1.0, 0, 1, "AI Difficulty")
    slider_win = Slider(WIDTH // 2, 450, 400, 12, (settings['win_score'] - 3) / 12, 0, 1, "Win Score")
    btn_shake = Button(WIDTH // 2, 540, 280, 50,
                       f"SHAKE: {'ON' if settings['screen_shake'] else 'OFF'}",
                       NEON_GREEN if settings['screen_shake'] else (100, 100, 100), NEON_CYAN, 20)
    btn_reset = Button(WIDTH // 2 - 130, 610, 220, 45, "RESET SAVE", NEON_RED, NEON_ORANGE, 18)
    btn_back = Button(WIDTH // 2 + 130, 610, 220, 45, "BACK", NEON_CYAN, NEON_GREEN, 20)

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

        box_w, box_h = 700, 660
        box_x = WIDTH // 2 - box_w // 2
        box_y = HEIGHT // 2 - box_h // 2 + 20
        pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h), border_radius=12)
        pygame.draw.rect(game_surface, NEON_PURPLE, (box_x, box_y, box_w, box_h), 3, border_radius=12)

        draw_text(game_surface, "SETTINGS", 48, WIDTH // 2, 60, NEON_CYAN, center=True, glow=True)

        slider_sfx.update(mouse_pos, mouse_pressed)
        slider_music.update(mouse_pos, mouse_pressed)
        slider_diff.update(mouse_pos, mouse_pressed)
        slider_win.update(mouse_pos, mouse_pressed)
        settings['sfx_volume'] = slider_sfx.value
        settings['music_volume'] = slider_music.value
        settings['difficulty'] = 0.5 + slider_diff.value * 1.0
        settings['win_score'] = 3 + int(slider_win.value * 12)
        if music_sound[0]:
            try:
                music_sound[0].set_volume(settings['music_volume'] * 0.5)
            except:
                pass

        slider_sfx.draw(game_surface)
        slider_music.draw(game_surface)
        slider_diff.draw(game_surface)
        slider_win.draw(game_surface)

        # نمایش مقدار win_score
        draw_text(game_surface, f"{settings['win_score']}", 18, WIDTH // 2 + 230, 440, NEON_YELLOW)

        diff_val = settings['difficulty']
        if diff_val < 0.8:
            diff_label, diff_color = "EASY", NEON_GREEN
        elif diff_val < 1.2:
            diff_label, diff_color = "NORMAL", NEON_CYAN
        else:
            diff_label, diff_color = "HARD", NEON_RED
        draw_text(game_surface, diff_label, 18, WIDTH // 2 + 230, 350, diff_color)

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
                settings['win_score'] = 7
                for k in achievements:
                    achievements[k]['unlocked'] = False
                highscore[0] = 0
                game_history.clear()
                total_wins[0] = 0
                total_rallies[0] = 0
                save_async()
                slider_sfx.value = 0.7
                slider_music.value = 0.5
                slider_diff.value = 0.5
                slider_win.value = 4 / 12
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
        card_h = 40
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

        draw_text(game_surface, "MATCH HISTORY", 46, WIDTH // 2, 35, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, f"Total matches: {len(game_history)}", 16, WIDTH // 2, 72, NEON_YELLOW, center=True)

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
                p_score = entry.get('player_score', 0)
                ai_score = entry.get('ai_score', 0)
                won = p_score > ai_score
                rank_color = NEON_GREEN if won else NEON_RED
                rank = "WIN" if won else "LOSS"
                pygame.draw.rect(game_surface, (15, 8, 30), (ix, iy, iw, item_h - 8), border_radius=6)
                pygame.draw.rect(game_surface, rank_color, (ix, iy, iw, item_h - 8), 2, border_radius=6)
                draw_text(game_surface, rank, 20, ix + 35, iy + (item_h - 8) // 2, rank_color, center=True, glow=True)
                draw_text(game_surface, f"{p_score} - {ai_score}", 22, ix + 100, iy + (item_h - 8) // 2,
                          WHITE, center=True)
                draw_text(game_surface, f"{entry.get('mode', '1P').upper()}", 14, ix + 200, iy + 10, NEON_CYAN)
                draw_text(game_surface, f"TIME: {entry.get('duration', 0)}s", 14, ix + 200, iy + 30, (180, 180, 200))
                draw_text(game_surface, entry.get('date', '?'), 12, ix + iw - 180, iy + 10, NEON_CYAN)
                new_achs = entry.get('achievements', [])
                if new_achs:
                    ach_str = " ".join(new_achs[:3])
                    if len(new_achs) > 3:
                        ach_str += f" +{len(new_achs) - 3}"
                    draw_text(game_surface, f"* {ach_str}", 11, ix + iw - 180, iy + 30, NEON_YELLOW)
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
            draw_text(game_surface, "No matches yet", 28, WIDTH // 2, HEIGHT // 2, (150, 150, 180), center=True)

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
def play_game(mode='1p'):
    # پدال‌ها
    paddle_left = Paddle(FIELD_X + 30, CENTER_Y, is_player=True, color=NEON_CYAN)
    paddle_right = Paddle(FIELD_RIGHT - 30, CENTER_Y, is_player=(mode == '2p'), color=NEON_PINK)

    # توپ
    balls = [Ball(CENTER_X, CENTER_Y, 0, 0, 6)]
    balls[0].stuck_to_paddle = paddle_left
    balls[0].stuck_offset = 0

    # Power-upها و موانع
    powerups = []
    obstacles = []

    # امتیاز
    score_left = 0
    score_right = 0
    max_score = settings['win_score']

    # کمبو / rally
    rally_count = 0
    max_rally = 0
    powerup_count = 0
    total_frames = 0

    # حالت
    game_over = False
    paused = False
    serving = True
    serve_timer = 60
    countdown = 3

    # افکت‌ها
    screen_shake = 0
    flash = 0
    goal_flash = 0

    new_achs = []
    notifications = []
    game_saved = False
    go_anim = 0

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
        add_game_to_history(score_left * 100, score_left, score_right,
                            total_frames // FPS, mode, new_achs)

    def reset_ball(direction=None):
        nonlocal serving, serve_timer, countdown
        # حذف توپ‌های اضافی
        balls.clear()
        new_ball = Ball(CENTER_X, CENTER_Y, 0, 0, 6)
        if direction is None:
            direction = random.choice([-1, 1])
        new_ball.stuck_to_paddle = paddle_left if direction == -1 else paddle_right
        new_ball.stuck_offset = 0
        balls.append(new_ball)
        serving = True
        serve_timer = 60
        countdown = 3
        rally_count = 0

    def spawn_powerup():
        x = random.uniform(FIELD_X + 100, FIELD_RIGHT - 100)
        y = random.uniform(FIELD_Y + 100, FIELD_BOTTOM - 100)
        powerups.append(PowerUp(x, y))

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
                    play_game(mode)
                    return
                if btn_menu.is_clicked(event):
                    stop_music()
                    return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not paused and not game_over:
                    # رها کردن توپ
                    for b in balls:
                        if b.stuck_to_paddle:
                            direction = 1 if b.stuck_to_paddle == paddle_left else -1
                            b.launch(direction)
                            serving = False
                            play_sound('paddle_hit')

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
            keys = pygame.key.get_pressed()

            # آپدیت پدال بازیکن چپ
            if serving:
                paddle_left.update(keys, mouse_pos[1], use_mouse=True)
            else:
                paddle_left.update(keys, mouse_pos[1], use_mouse=True)

            # پدال راست
            if mode == '2p':
                # بازیکن دوم با کلید
                if keys[pygame.K_UP]:
                    paddle_right.y -= paddle_right.speed
                if keys[pygame.K_DOWN]:
                    paddle_right.y += paddle_right.speed
                paddle_right.y = max(FIELD_Y + paddle_right.h / 2,
                                     min(FIELD_BOTTOM - paddle_right.h / 2, paddle_right.y))
            else:
                # AI
                if balls:
                    closest_ball = min(balls, key=lambda b: abs(b.x - paddle_right.x))
                    paddle_right.ai_update(closest_ball)

            # شمارش معکوس
            if serving:
                serve_timer -= 1
                if serve_timer <= 0:
                    if countdown > 0:
                        play_sound('countdown')
                        countdown -= 1
                        serve_timer = 60
                    else:
                        for b in balls:
                            if b.stuck_to_paddle:
                                direction = 1 if b.stuck_to_paddle == paddle_left else -1
                                b.launch(direction)
                        serving = False
                        countdown = 3

            # آپدیت توپ‌ها
            for ball in balls[:]:
                ball.update()

                if ball.stuck_to_paddle:
                    continue

                # برخورد با پدال چپ
                if ball.vx < 0 and ball.rect().colliderect(paddle_left.rect()):
                    # محاسبه زاویه
                    offset = (ball.y - paddle_left.y) / (paddle_left.h / 2)
                    offset = max(-1, min(1, offset))
                    ball.speed = min(20, ball.speed + 0.5)
                    rad = math.radians(offset * 60)
                    ball.vx = abs(math.cos(rad)) * ball.speed
                    ball.vy = math.sin(rad) * ball.speed
                    ball.x = paddle_left.rect().right + ball.radius
                    paddle_left.hit_flash = 8
                    rally_count += 1
                    max_rally = max(max_rally, rally_count)
                    play_sound('paddle_hit')
                    spawn_particles(ball.x, ball.y, NEON_CYAN, 8, 1.2, 1.0, 0.6)
                    if rally_count >= 10:
                        try_unlock('rally_10')
                    if rally_count >= 20:
                        try_unlock('rally_20')
                    if ball.speed >= 15:
                        try_unlock('speed_15')
                    if ball.speed >= 20:
                        try_unlock('speed_20')
                    try_unlock('first_hit')

                    # Magnet
                    if paddle_left.magnet_timer > 0:
                        ball.stuck_to_paddle = paddle_left
                        ball.stuck_offset = ball.y - paddle_left.y

                # برخورد با پدال راست
                if ball.vx > 0 and ball.rect().colliderect(paddle_right.rect()):
                    offset = (ball.y - paddle_right.y) / (paddle_right.h / 2)
                    offset = max(-1, min(1, offset))
                    ball.speed = min(20, ball.speed + 0.5)
                    rad = math.radians(offset * 60)
                    ball.vx = -abs(math.cos(rad)) * ball.speed
                    ball.vy = math.sin(rad) * ball.speed
                    ball.x = paddle_right.rect().left - ball.radius
                    paddle_right.hit_flash = 8
                    rally_count += 1
                    max_rally = max(max_rally, rally_count)
                    play_sound('paddle_hit')
                    spawn_particles(ball.x, ball.y, NEON_PINK, 8, 1.2, 1.0, 0.6)

                    if paddle_right.magnet_timer > 0 and mode == '2p':
                        ball.stuck_to_paddle = paddle_right
                        ball.stuck_offset = ball.y - paddle_right.y

                # برخورد با موانع
                for obs in obstacles:
                    if ball.rect().colliderect(obs.rect):
                        # محاسبه برخورد
                        if obs.horizontal:
                            ball.vy = -ball.vy
                        else:
                            ball.vx = -ball.vx
                        play_sound('wall_hit')
                        spawn_particles(ball.x, ball.y, NEON_ORANGE, 5, 1.0, 0.8, 0.5)
                        break

                # گل
                if ball.x - ball.radius < FIELD_X:
                    # گل راست
                    score_right += 1
                    goal_flash = 30
                    flash = 200
                    if settings['screen_shake']:
                        screen_shake = 25
                    play_sound('lose')
                    for _ in range(40):
                        spawn_particles(ball.x, ball.y, NEON_PINK, 1, 2.0, 1.5, 1.5)
                    balls.remove(ball)
                    if score_right >= max_score:
                        game_over = True
                        final_result = 'loss'
                    else:
                        reset_ball(direction=-1)
                    continue
                elif ball.x + ball.radius > FIELD_RIGHT:
                    # گل چپ
                    score_left += 1
                    goal_flash = 30
                    flash = 200
                    if settings['screen_shake']:
                        screen_shake = 25
                    play_sound('score')
                    for _ in range(40):
                        spawn_particles(ball.x, ball.y, NEON_CYAN, 1, 2.0, 1.5, 1.5)
                    balls.remove(ball)
                    if score_left >= max_score:
                        game_over = True
                        final_result = 'win'
                        highscore[0] = max(highscore[0], score_left * 100)
                        total_wins[0] += 1
                        try_unlock('first_win')
                        if total_wins[0] >= 5:
                            try_unlock('win_5')
                        if total_wins[0] >= 10:
                            try_unlock('win_10')
                        if score_right == 0:
                            try_unlock('perfect')
                            try_unlock('sweep')
                        if mode == '1p' and settings['difficulty'] >= 1.2:
                            try_unlock('beat_hard')
                        play_sound('victory')
                    else:
                        reset_ball(direction=1)
                    continue

            # آپدیت موانع
            for obs in obstacles:
                obs.update()

            # اسپاون موانع هر 30 ثانیه
            if total_frames % (FPS * 30) == 0 and total_frames > 0:
                if random.random() < 0.5:
                    w = random.choice([80, 100, 120])
                    h = 15
                    x = random.uniform(CENTER_X - 150, CENTER_X + 50)
                    y = random.uniform(FIELD_Y + 100, FIELD_BOTTOM - 100)
                    obstacles.append(Obstacle(x, y, w, h, horizontal=True))

            # آپدیت power-ups
            for p in powerups[:]:
                p.update()
                if p.life <= 0:
                    powerups.remove(p)
                    continue

                # برخورد با پدال‌ها
                pr = paddle_left.rect()
                if pr.colliderect(pygame.Rect(int(p.x - p.radius), int(p.y - p.radius),
                                              p.radius * 2, p.radius * 2)):
                    powerup_count += 1
                    total_powerups = powerup_count
                    if p.type == 'big_paddle':
                        paddle_left.big_timer = 600
                    elif p.type == 'multi_ball':
                        # اضافه کردن دو توپ جدید
                        new_balls = []
                        for b in balls[:2]:
                            if b.stuck_to_paddle:
                                continue
                            for _ in range(2):
                                nb = Ball(b.x, b.y,
                                          random.uniform(-5, 5),
                                          random.uniform(-5, 5),
                                          b.speed)
                                new_balls.append(nb)
                        balls.extend(new_balls)
                        try_unlock('multi_ball')
                    elif p.type == 'slow_ball':
                        for b in balls:
                            b.speed = max(3, b.speed * 0.6)
                            b.vx *= 0.6
                            b.vy *= 0.6
                    elif p.type == 'speed_ball':
                        # برای حریف
                        for b in balls:
                            b.speed = min(20, b.speed * 1.4)
                            b.vx *= 1.4
                            b.vy *= 1.4
                    elif p.type == 'magnet':
                        paddle_left.magnet_timer = 600
                    play_sound('power')
                    for _ in range(20):
                        spawn_particles(p.x, p.y, NEON_GREEN, 1, 1.5)
                    powerups.remove(p)
                    if powerup_count >= 5:
                        try_unlock('power_5')
                    if powerup_count >= 15:
                        try_unlock('power_15')
                    continue

                # برخورد با پدال راست (فقط توی 2p)
                if mode == '2p':
                    pr2 = paddle_right.rect()
                    if pr2.colliderect(pygame.Rect(int(p.x - p.radius), int(p.y - p.radius),
                                                    p.radius * 2, p.radius * 2)):
                        if p.type == 'big_paddle':
                            paddle_right.big_timer = 600
                        elif p.type == 'magnet':
                            paddle_right.magnet_timer = 600
                        play_sound('power')
                        powerups.remove(p)

            # اسپاون power-up هر 8 ثانیه
            if total_frames % (FPS * 8) == 0 and total_frames > 0:
                if len(powerups) < 3 and random.random() < 0.7:
                    spawn_powerup()

            # چک دستاورد survive
            if total_frames >= FPS * 120:
                try_unlock('survive_2min')

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
            if goal_flash > 0:
                goal_flash -= 1

        # ============================================================
        #                    رسم
        # ============================================================
        game_surface.fill(DARK_BG)
        offset_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        offset_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0

        play_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # گرادیان
        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            play_layer.blit(s, (0, y))

        # زمین
        pygame.draw.rect(play_layer, (5, 8, 20),
                         (FIELD_X, FIELD_Y, FIELD_W, FIELD_H),
                         border_radius=10)
        pygame.draw.rect(play_layer, NEON_CYAN,
                         (FIELD_X, FIELD_Y, FIELD_W, FIELD_H), 3, border_radius=10)

        # خط مرکزی
        for i in range(FIELD_Y, FIELD_BOTTOM, 20):
            pygame.draw.line(play_layer, (60, 80, 120),
                             (CENTER_X, i), (CENTER_X, i + 10), 2)

        # دایره وسط
        pygame.draw.circle(play_layer, (60, 80, 120), (CENTER_X, CENTER_Y), 80, 2)
        pygame.draw.circle(play_layer, (60, 80, 120), (CENTER_X, CENTER_Y), 5)

        # موانع
        for obs in obstacles:
            obs.draw(play_layer)

        # Power-ups
        for p in powerups:
            p.draw(play_layer)

        # ذرات
        for p in active_particles:
            p.draw(play_layer)

        # پدال‌ها
        paddle_left.draw(play_layer)
        paddle_right.draw(play_layer)

        # توپ‌ها
        for ball in balls:
            ball.draw(play_layer)

        # شمارش معکوس
        if serving and not game_over:
            if countdown > 0:
                size = 80 + int(math.sin(t * 10) * 10)
                draw_text(play_layer, f"{countdown}", size, CENTER_X, CENTER_Y,
                          NEON_YELLOW, center=True, glow=True)

        if goal_flash > 0:
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 200, 100, goal_flash * 5))
            play_layer.blit(fs, (0, 0))

        if flash > 0:
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 200, 100, flash))
            play_layer.blit(fs, (0, 0))

        game_surface.blit(play_layer, (offset_x, offset_y))

        # ============================================================
        #                    HUD
        # ============================================================
        # امتیاز
        draw_text(game_surface, f"{score_left}", 60, CENTER_X - 100, 50,
                  NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, f"{score_right}", 60, CENTER_X + 100, 50,
                  NEON_PINK, center=True, glow=True)
        draw_text(game_surface, "-", 60, CENTER_X, 50, WHITE, center=True)

        # نام بازیکنان
        draw_text(game_surface, "YOU", 16, CENTER_X - 100, 15, NEON_CYAN, center=True)
        if mode == '2p':
            draw_text(game_surface, "P2", 16, CENTER_X + 100, 15, NEON_PINK, center=True)
        else:
            draw_text(game_surface, "AI", 16, CENTER_X + 100, 15, NEON_PINK, center=True)

        # برنده
        draw_text(game_surface, f"FIRST TO {max_score}", 16, CENTER_X, HEIGHT - 25,
                  NEON_YELLOW, center=True)

        # Rally
        if rally_count > 1:
            draw_text(game_surface, f"RALLY: {rally_count}", 14, 30, 30, NEON_YELLOW)

        # کلیدها
        draw_text(game_surface, "MOVE: Mouse or W/S | SPACE: Launch | P: Pause",
                  11, 30, HEIGHT - 20, (180, 200, 220))

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
            box_w, box_h = 540, 400
            box_x = WIDTH // 2 - box_w // 2
            box_y = HEIGHT // 2 - box_h // 2
            pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h))
            win_color = NEON_GREEN if final_result == 'win' else NEON_RED
            pygame.draw.rect(game_surface, win_color, (box_x, box_y, box_w, box_h), 3)
            pygame.draw.rect(game_surface, NEON_CYAN, (box_x + 5, box_y + 5, box_w - 10, box_h - 10), 1)
            title = "YOU WIN!" if final_result == 'win' else "YOU LOSE!"
            draw_text(game_surface, title, 60, WIDTH // 2, box_y + 55,
                      win_color, center=True, glow=True)
            draw_text(game_surface, f"{score_left} - {score_right}", 40,
                      WIDTH // 2, box_y + 130, WHITE, center=True)
            draw_text(game_surface, f"MAX RALLY: {max_rally}   TIME: {total_frames // FPS}s",
                      16, WIDTH // 2, box_y + 175, NEON_CYAN, center=True)
            hs = highscore[0]
            if score_left * 100 >= hs and score_left > 0:
                draw_text(game_surface, "* NEW HIGH SCORE! *", 22, WIDTH // 2, box_y + 210,
                          NEON_YELLOW, center=True, glow=True)
            else:
                draw_text(game_surface, f"HIGH SCORE: {hs}", 18, WIDTH // 2, box_y + 210,
                          NEON_YELLOW, center=True)
            if go_anim > 15:
                btn_restart.update(mouse_pos)
                btn_menu.update(mouse_pos)
                btn_restart.draw(game_surface)
                btn_menu.draw(game_surface)

        present()

        # چک باخت نهایی
        if game_over and not game_saved:
            save_current()
            game_saved = True

    stop_music()


# ============================================================
#                    Main
# ============================================================
def main():
    while True:
        result = show_menu()
        if result == 'quit':
            break
        elif result == '1p':
            play_game('1p')
        elif result == '2p':
            play_game('2p')
    pygame.quit()


if __name__ == "__main__":
    main()