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

BASE_W, BASE_H = 900, 700
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("PYTHON BRICK BREAKER")
game_surface = pygame.Surface((BASE_W, BASE_H))

clock = pygame.time.Clock()
FPS = 60

# --- رنگ‌ها ---
BLACK = (5, 5, 15)
DARK_BG = (8, 10, 25)
WHITE = (255, 255, 255)
NEON_BLUE = (50, 150, 255)
NEON_CYAN = (0, 255, 255)
NEON_PURPLE = (170, 60, 255)
NEON_PINK = (255, 60, 180)
NEON_RED = (255, 60, 60)
NEON_ORANGE = (255, 150, 30)
NEON_YELLOW = (255, 230, 0)
NEON_GREEN = (50, 255, 120)
NEON_TEAL = (0, 220, 180)

BRICK_COLORS = [NEON_BLUE, NEON_RED, NEON_ORANGE, NEON_TEAL, NEON_PURPLE]

# --- فایل ذخیره ---
SAVE_FILE = "brick_breaker_save.json"

settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'difficulty': 1.0,
    'screen_shake': True,
}

achievements = {
    'first_brick': {'name': 'FIRST BREAK', 'desc': 'Break your first brick', 'unlocked': False, 'icon': '*'},
    'combo_5': {'name': 'COMBO MASTER', 'desc': 'Reach a 5x combo', 'unlocked': False, 'icon': 'F'},
    'combo_10': {'name': 'COMBO LEGEND', 'desc': 'Reach a 10x combo', 'unlocked': False, 'icon': 'Z'},
    'score_1000': {'name': 'ROOKIE', 'desc': 'Score 1000 points', 'unlocked': False, 'icon': '*'},
    'score_5000': {'name': 'VETERAN', 'desc': 'Score 5000 points', 'unlocked': False, 'icon': '**'},
    'score_10000': {'name': 'LEGEND', 'desc': 'Score 10000 points', 'unlocked': False, 'icon': '***'},
    'level_3': {'name': 'EXPLORER', 'desc': 'Reach level 3', 'unlocked': False, 'icon': '>'},
    'level_5': {'name': 'ADVENTURER', 'desc': 'Reach level 5', 'unlocked': False, 'icon': '>>'},
    'multiball': {'name': 'MULTIBALL!', 'desc': 'Activate multiball', 'unlocked': False, 'icon': 'O'},
    'no_life_lost': {'name': 'PERFECT', 'desc': 'Clear a level without losing a life', 'unlocked': False, 'icon': 'P'},
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
def get_font(size, bold=True):
    key = (size, bold)
    if key not in FONT_CACHE:
        FONT_CACHE[key] = pygame.font.SysFont("consolas", size, bold=bold)
    return FONT_CACHE[key]

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

# --- صدا ---
sounds = {}
music_sound = [None]
sound_ready = threading.Event()

def make_sound(freq_start, freq_end, duration, volume=0.3, wave='sine'):
    if not AUDIO_OK:
        return None
    sr = 44100
    n = int(sr * duration)
    buf = array.array('h')
    for i in range(n):
        t = i / sr
        freq = freq_start + (freq_end - freq_start) * (i / n)
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
        env = 1.0 - (i / n)
        val *= env * volume
        buf.append(int(val * 32767))
    try:
        return pygame.mixer.Sound(buffer=buf)
    except:
        return None

def make_music_loop(notes, note_dur, volume=0.3, waveform='triangle'):
    if not AUDIO_OK:
        return None
    sr = 44100
    buf = array.array('h')
    for note in notes:
        n = int(sr * note_dur)
        for i in range(n):
            t = i / sr
            if note == 0:
                buf.append(0)
                continue
            if waveform == 'sine':
                val = math.sin(2 * math.pi * note * t)
            elif waveform == 'triangle':
                val = 2 * abs(2 * (note * t - math.floor(note * t + 0.5))) - 1
            elif waveform == 'saw':
                val = 2 * (note * t - math.floor(note * t + 0.5))
            else:
                val = math.sin(2 * math.pi * note * t)
            val += math.sin(2 * math.pi * note * 2 * t) * 0.12
            env = 1.0
            if i < n * 0.05:
                env = i / (n * 0.05)
            elif i > n * 0.85:
                env = 1.0 - (i - n * 0.85) / (n * 0.15)
            val *= env * volume
            buf.append(int(max(-1, min(1, val)) * 32767))
    try:
        return pygame.mixer.Sound(buffer=buf)
    except:
        return None

def build_sounds():
    sounds['bounce'] = make_sound(600, 800, 0.05, 0.15, 'square')
    sounds['brick'] = make_sound(800, 1200, 0.08, 0.15, 'square')
    sounds['brick_break'] = make_sound(1000, 500, 0.15, 0.20, 'square')
    sounds['powerup'] = make_sound(600, 1400, 0.3, 0.2, 'sine')
    sounds['life_lost'] = make_sound(400, 100, 0.5, 0.25, 'saw')
    sounds['gameover'] = make_sound(500, 60, 1.2, 0.3, 'saw')
    sounds['level_up'] = make_sound(400, 1200, 0.5, 0.25, 'sine')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['multiball'] = make_sound(300, 1500, 0.5, 0.25, 'sine')
    sounds['boss_hit'] = make_sound(300, 200, 0.1, 0.2, 'square')

    music_notes = [
        261.63, 329.63, 392, 523.25, 392, 329.63,
        261.63, 329.63, 392, 523.25, 659.25, 523.25,
        293.66, 349.23, 440, 587.33, 440, 349.23,
        261.63, 329.63, 392, 523.25, 392, 329.63,
    ]
    music_sound[0] = make_music_loop(music_notes, 0.22, 0.1, 'triangle')
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
        self.size = random.randint(2, 5) * size_mult
        self.active = True
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.94
        self.vy *= 0.94
        self.vy += 0.15
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

# --- Paddle ---
class Paddle:
    def __init__(self):
        self.base_w = 130
        self.base_h = 18
        self.w = self.base_w
        self.h = self.base_h
        self.x = WIDTH // 2 - self.w // 2
        self.y = HEIGHT - 60
        self.speed = 9
        self.wide_timer = 0
        self.laser_timer = 0
        self.sticky_timer = 0
        self.glow_phase = 0

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        self.x = max(20, min(WIDTH - self.w - 20, self.x))

        if self.wide_timer > 0:
            self.wide_timer -= 1
            self.w = self.base_w + 60
        else:
            self.w = self.base_w
        if self.laser_timer > 0:
            self.laser_timer -= 1
        if self.sticky_timer > 0:
            self.sticky_timer -= 1
        self.glow_phase += 0.15

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(self.w), int(self.h))

    def draw(self, surface):
        # هاله بزرگ
        glow = pygame.Surface((self.w + 80, 80), pygame.SRCALPHA)
        pulse = 1 + math.sin(self.glow_phase) * 0.2
        pygame.draw.ellipse(glow, (100, 200, 255, 50),
                            (40 - 10, 30, self.w + 60, 20))
        surface.blit(glow, (self.x - 40, self.y - 30))

        # پدال اصلی (سفید)
        r = self.rect()
        pygame.draw.rect(surface, (200, 230, 255), r, border_radius=10)
        pygame.draw.rect(surface, WHITE, r, 3, border_radius=10)

        # خطوط نئونی
        if self.wide_timer > 0:
            pygame.draw.rect(surface, NEON_CYAN, r, 2, border_radius=10)
        if self.sticky_timer > 0:
            pygame.draw.rect(surface, NEON_GREEN, r, 2, border_radius=10)

        # جزئیات
        inner = pygame.Rect(r.x + 8, r.y + 3, r.w - 16, r.h - 6)
        pygame.draw.rect(surface, (220, 240, 255), inner, border_radius=6)

        # چراغ‌های دو سر
        pygame.draw.circle(surface, NEON_CYAN, (r.x + 8, r.centery), 4)
        pygame.draw.circle(surface, NEON_CYAN, (r.right - 8, r.centery), 4)

# --- Ball ---
class Ball:
    __slots__ = ('x', 'y', 'vx', 'vy', 'radius', 'speed', 'trail', 'stuck_to_paddle')
    def __init__(self, x, y, vx, vy, speed=6):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = 8
        self.speed = speed
        self.trail = []
        self.stuck_to_paddle = False

    def update(self, paddle, slow_timer=0):
        if self.stuck_to_paddle:
            self.x = paddle.x + paddle.w / 2
            self.y = paddle.y - self.radius - 1
            return

        mult = 0.6 if slow_timer > 0 else 1.0
        self.trail.append((self.x, self.y))
        if len(self.trail) > 12:
            self.trail.pop(0)

        self.x += self.vx * mult
        self.y += self.vy * mult

        # برخورد دیوارها
        if self.x - self.radius < 20:
            self.x = 20 + self.radius
            self.vx = abs(self.vx)
            play_sound('bounce')
        elif self.x + self.radius > WIDTH - 20:
            self.x = WIDTH - 20 - self.radius
            self.vx = -abs(self.vx)
            play_sound('bounce')
        if self.y - self.radius < 90:
            self.y = 90 + self.radius
            self.vy = abs(self.vy)
            play_sound('bounce')

    def draw(self, surface):
        # trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / len(self.trail)
            r = max(1, int(self.radius * alpha * 0.7))
            c = (int(100 * alpha), int(150 * alpha), 255)
            pygame.draw.circle(surface, c, (int(tx), int(ty)), r)

        # هاله درخشان
        glow = pygame.Surface((self.radius * 6, self.radius * 6), pygame.SRCALPHA)
        pygame.draw.circle(glow, (100, 100, 255, 100),
                           (self.radius * 3, self.radius * 3), self.radius * 2)
        surface.blit(glow, (self.x - self.radius * 3, self.y - self.radius * 3))

        # بدنه توپ (آبی-بنفش)
        pygame.draw.circle(surface, (80, 60, 220), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 2)
        # نقاط روشن
        pygame.draw.circle(surface, (200, 200, 255),
                           (int(self.x - 2), int(self.y - 2)), self.radius // 3)

# --- Brick ---
class Brick:
    def __init__(self, x, y, w, h, color, hp=1, is_boss=False):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.hp = hp
        self.max_hp = hp
        self.is_boss = is_boss
        self.hit_flash = 0
        # حرکت باس
        self.boss_vx = random.choice([-1.5, 1.5]) if is_boss else 0
        self.boss_vy = 0
        self.boss_shoot_timer = 0
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))

    def update(self):
        if self.hit_flash > 0:
            self.hit_flash -= 1
        if self.is_boss:
            self.x += self.boss_vx
            if self.x < 20 or self.x + self.w > WIDTH - 20:
                self.boss_vx = -self.boss_vx
            self.rect.x = int(self.x)

    def draw(self, surface):
        color = self.color
        if self.hit_flash > 0:
            color = WHITE

        # هاله درخشان
        glow = pygame.Surface((int(self.w) + 40, int(self.h) + 40), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*color, 50),
                         (20, 20, int(self.w), int(self.h)), border_radius=12)
        surface.blit(glow, (self.x - 20, self.y - 20))

        # بدنه
        r = pygame.Rect(int(self.x), int(self.y), int(self.w), int(self.h))
        darker = (max(0, color[0] - 60), max(0, color[1] - 60), max(0, color[2] - 60))
        pygame.draw.rect(surface, darker, r, border_radius=8)
        pygame.draw.rect(surface, color, r, 3, border_radius=8)
        pygame.draw.rect(surface, WHITE, r, 1, border_radius=8)

        # خط بالای آجر (نور)
        top_line = pygame.Rect(r.x + 4, r.y + 3, r.w - 8, 3)
        pygame.draw.rect(surface, (255, 255, 255, 100), top_line, border_radius=2)
        pygame.draw.rect(surface, (*color, 150) if len(color) == 3 else color,
                         top_line, border_radius=2)

        # نشانگر HP برای آجرهای چندجانی
        if self.max_hp > 1:
            for i in range(self.hp):
                px = r.x + r.w // 2 - (self.max_hp * 5) // 2 + i * 10 + 5
                pygame.draw.circle(surface, WHITE, (px, r.y + 6), 2)

        if self.is_boss:
            # چشم‌ها برای باس
            cy = r.y + r.h // 2
            pygame.draw.circle(surface, WHITE, (r.x + r.w // 3, cy), 6)
            pygame.draw.circle(surface, WHITE, (r.x + 2 * r.w // 3, cy), 6)
            pygame.draw.circle(surface, NEON_RED, (r.x + r.w // 3, cy), 3)
            pygame.draw.circle(surface, NEON_RED, (r.x + 2 * r.w // 3, cy), 3)

# --- PowerUp ---
class PowerUp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vy = 3
        self.type = random.choices(
            ['multi', 'wide', 'slow', 'laser', 'life', 'sticky'],
            weights=[3, 3, 2, 2, 1, 2]
        )[0]
        self.radius = 16
        self.pulse = random.uniform(0, math.pi * 2)

    def update(self):
        self.y += self.vy
        self.pulse += 0.15

    def draw(self, surface):
        colors = {
            'multi': NEON_CYAN,
            'wide': NEON_GREEN,
            'slow': NEON_YELLOW,
            'laser': NEON_PINK,
            'life': NEON_RED,
            'sticky': NEON_PURPLE,
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

        # متن کوتاه داخل
        if self.type == 'life':
            draw_text(surface, "+1", 14, self.x, self.y - 8, WHITE, center=True)
            draw_text(surface, "LIFE", 10, self.x, self.y + 6, WHITE, center=True)
        elif self.type == 'multi':
            draw_text(surface, "3X", 16, self.x, self.y, WHITE, center=True)
        elif self.type == 'wide':
            draw_text(surface, "W", 18, self.x, self.y, WHITE, center=True)
        elif self.type == 'slow':
            draw_text(surface, "S", 18, self.x, self.y, WHITE, center=True)
        elif self.type == 'laser':
            draw_text(surface, "L", 18, self.x, self.y, WHITE, center=True)
        elif self.type == 'sticky':
            draw_text(surface, "ST", 14, self.x, self.y, WHITE, center=True)

# --- LaserBullet ---
class LaserBullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vy = -12
    def update(self):
        self.y += self.vy
    def draw(self, surface):
        pygame.draw.rect(surface, NEON_PINK, (self.x - 2, self.y - 12, 4, 16))
        pygame.draw.rect(surface, WHITE, (self.x - 1, self.y - 10, 2, 12))

# --- Button ---
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
        for cx, cy in [(rx, ry), (rx + w - corner, ry),
                       (rx, ry + h - corner), (rx + w - corner, ry + h - corner)]:
            pygame.draw.rect(surface, color, (cx, cy, corner, 3))
            pygame.draw.rect(surface, color, (cx, cy, 3, corner))

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
                         (self.rect.x, self.rect.y, fill_w, self.rect.height), border_radius=4)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=4)
        knob = self._knob_rect()
        color = NEON_GREEN if self.hovered else NEON_PINK
        pygame.draw.rect(surface, color, knob, border_radius=4)
        pygame.draw.rect(surface, WHITE, knob, 2, border_radius=4)
        draw_text(surface, self.label, 18, self.rect.x, self.rect.y - 30, WHITE)
        draw_text(surface, f"{int(self.value * 100)}%", 18,
                  self.rect.right - 60, self.rect.y - 30, NEON_YELLOW)

# --- پس‌زمینه ---
_bg_cache = None
def build_background():
    global _bg_cache
    surf = pygame.Surface((WIDTH, HEIGHT))
    surf.fill(DARK_BG)

    # خطوط نئونی عمودی (طرفین)
    for i in range(80):
        alpha = int(100 * (1 - i / 80))
        c = (0, min(255, 100 + alpha), 255)
        pygame.draw.line(surf, c, (20 + i, 80), (20 + i, HEIGHT - 20), 1)
        pygame.draw.line(surf, c, (WIDTH - 20 - i, 80), (WIDTH - 20 - i, HEIGHT - 20), 1)

    # کادر اصلی
    pygame.draw.rect(surf, (30, 100, 200), (15, 75, WIDTH - 30, HEIGHT - 90), 2, border_radius=10)

    # کف نورانی
    for i in range(20):
        alpha = int(120 * (1 - i / 20))
        pygame.draw.line(surf, (0, 150, 255), (30, HEIGHT - 20 - i),
                         (WIDTH - 30, HEIGHT - 20 - i), 1)

    # گوشه‌های نئونی
    for cx, cy, sx, sy in [(20, 80, 1, 1), (WIDTH - 20, 80, -1, 1),
                           (20, HEIGHT - 20, 1, -1), (WIDTH - 20, HEIGHT - 20, -1, -1)]:
        for i in range(30):
            alpha = 255 - i * 8
            color = (0, min(255, 150 + i * 3), 255)
            pygame.draw.line(surf, color,
                             (cx, cy + sy * i), (cx + sx * i, cy), 2)

    # ستاره‌های ریز
    for _ in range(100):
        x, y = random.randint(30, WIDTH - 30), random.randint(90, HEIGHT - 30)
        c = random.choice([(100, 100, 150), (150, 150, 200), (200, 200, 255)])
        surf.set_at((x, y), c)

    _bg_cache = surf

build_background()

def draw_background(surface):
    surface.blit(_bg_cache, (0, 0))

# --- Game State ---
class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.paddle = Paddle()
        self.balls = [Ball(WIDTH // 2, HEIGHT - 90, 0, -6, 6)]
        self.balls[0].stuck_to_paddle = True
        self.bricks = []
        self.powerups = []
        self.lasers = []
        self.score = 0
        self.display_score = 0
        self.lives = 3
        self.level = 1
        self.combo = 0
        self.combo_timer = 0
        self.max_combo = 0
        self.slow_timer = 0
        self.boss_spawned = False
        self.level_lost_life = False
        self.new_achs = []
        self.multiball_banner = 0

    def load_level(self):
        self.bricks.clear()
        self.powerups.clear()
        self.lasers.clear()
        self.balls = [Ball(WIDTH // 2, HEIGHT - 90, 0, -6, 6)]
        self.balls[0].stuck_to_paddle = True
        self.level_lost_life = False

        if self.level % 4 == 0:
            # باس
            boss = Brick(WIDTH // 2 - 100, 150, 200, 60, NEON_PINK, hp=30, is_boss=True)
            self.bricks.append(boss)
            # چند آجر محافظ
            for i in range(8):
                bx = 100 + i * 90
                self.bricks.append(Brick(bx, 250, 75, 30, random.choice(BRICK_COLORS), hp=1))
        else:
            cols = 10
            rows = min(4 + self.level, 7)
            pad_x = 40
            gap = 6
            brick_w = (WIDTH - pad_x * 2 - gap * (cols - 1)) / cols
            brick_h = 30
            start_y = 130

            for row in range(rows):
                for col in range(cols):
                    # بعضی جاها خالی
                    if random.random() < 0.1 and row > 0:
                        continue
                    x = pad_x + col * (brick_w + gap)
                    y = start_y + row * (brick_h + gap)
                    # رنگ بر اساس ردیف
                    color = BRICK_COLORS[row % len(BRICK_COLORS)]
                    # آجرهای ردیف بالا قوی‌تر
                    hp = 1
                    if self.level >= 3 and row < 2:
                        hp = 2
                    if self.level >= 5 and row == 0:
                        hp = 3
                    self.bricks.append(Brick(x, y, brick_w, brick_h, color, hp=hp))

    def try_unlock(self, key):
        if unlock_achievement(key):
            self.new_achs.append(achievements[key]['name'])
            return True
        return False

# --- Resize handling ---
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
    scale = screen_scale[0]
    ox = screen_offset_x[0]
    oy = screen_offset_y[0]
    return ((mx - ox) / scale, (my - oy) / scale)

# --- HUD ---
def draw_hud(surface, gs):
    # عنوان
    draw_text(surface, "PYTHON ", 30, 30, 20, WHITE, glow=False)
    title_w = get_font(30).size("PYTHON ")[0]
    draw_text(surface, "BRICK BREAKER", 30, 30 + title_w, 20, NEON_BLUE, glow=True)

    # زیرنویس
    draw_text(surface, "BREAK  /  CATCH  /  MULTIBALL", 15, 30, 55, (200, 200, 220))

    # SCORE و COMBO راست
    draw_text(surface, f"SCORE: {gs.display_score}", 26, WIDTH - 30, 20, WHITE, glow=True)
    if gs.combo > 1:
        combo_color = NEON_GREEN if gs.combo < 5 else NEON_YELLOW if gs.combo < 10 else NEON_PINK
        draw_text(surface, f"COMBO: {gs.combo}", 26, WIDTH - 30, 52, combo_color, glow=True)

    # Lives و Level
    draw_text(surface, f"LIVES: {gs.lives}", 18, 30, HEIGHT - 30, NEON_PINK)
    draw_text(surface, f"LEVEL: {gs.level}", 18, WIDTH - 130, HEIGHT - 30, NEON_CYAN)

# --- Menu ---
def show_menu():
    menu_time = 0
    btn_start = Button(WIDTH // 2, HEIGHT // 2 + 20, 320, 55, "START GAME", NEON_CYAN, NEON_GREEN, 26)
    btn_history = Button(WIDTH // 2, HEIGHT // 2 + 85, 320, 45, "HISTORY", NEON_BLUE, NEON_CYAN, 22)
    btn_settings = Button(WIDTH // 2, HEIGHT // 2 + 140, 320, 45, "SETTINGS", NEON_PURPLE, NEON_PINK, 22)
    btn_achievements = Button(WIDTH // 2, HEIGHT // 2 + 195, 320, 45, "ACHIEVEMENTS", NEON_YELLOW, NEON_ORANGE, 22)
    btn_quit = Button(WIDTH // 2, HEIGHT // 2 + 250, 320, 42, "QUIT", NEON_RED, NEON_ORANGE, 20)

    while True:
        game_surface.fill(BLACK)
        t = pygame.time.get_ticks() / 1000
        menu_time += 1
        mouse_pos = get_game_mouse_pos()

        draw_background(game_surface)

        # عنوان بزرگ
        title_y = 120 + math.sin(t * 2) * 8
        draw_text(game_surface, "PYTHON", 68, WIDTH // 2, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "BRICK BREAKER", 68, WIDTH // 2, title_y + 65, NEON_BLUE, center=True, glow=True)
        draw_text(game_surface, "BREAK  /  CATCH  /  MULTIBALL", 20,
                  WIDTH // 2, title_y + 125, (200, 200, 220), center=True)

        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 22, WIDTH // 2, title_y + 175,
                      NEON_YELLOW, center=True)
        draw_text(game_surface, f"TOTAL GAMES: {len(game_history)}", 15,
                  WIDTH // 2, title_y + 200, NEON_PINK, center=True)

        for b in [btn_start, btn_history, btn_settings, btn_achievements, btn_quit]:
            b.update(mouse_pos)
            b.draw(game_surface)

        # ذرات
        if menu_time % 5 == 0:
            p = None
            for pp in particle_pool:
                if not pp.active:
                    p = pp
                    break
            if p is None:
                p = Particle()
                particle_pool.append(p)
            p.spawn(random.randint(30, WIDTH - 30), random.randint(90, HEIGHT - 30),
                    random.choice(BRICK_COLORS), 0.3, 1, 1.5)
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

# --- Settings ---
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
        game_surface.fill(BLACK)
        mouse_pos = get_game_mouse_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        draw_background(game_surface)

        box_w, box_h = 700, 580
        box_x = WIDTH // 2 - box_w // 2
        box_y = HEIGHT // 2 - box_h // 2 + 20
        pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h), border_radius=12)
        pygame.draw.rect(game_surface, NEON_PURPLE, (box_x, box_y, box_w, box_h), 3, border_radius=12)
        pygame.draw.rect(game_surface, NEON_PINK, (box_x + 5, box_y + 5, box_w - 10, box_h - 10), 1, border_radius=10)

        draw_text(game_surface, "SETTINGS", 50, WIDTH // 2, 60, NEON_CYAN, center=True, glow=True)

        slider_sfx.update(mouse_pos, mouse_pressed)
        slider_music.update(mouse_pos, mouse_pressed)
        slider_diff.update(mouse_pos, mouse_pressed)
        settings['sfx_volume'] = slider_sfx.value
        settings['music_volume'] = slider_music.value
        settings['difficulty'] = 0.5 + slider_diff.value * 1.0
        if music_sound[0]:
            try:
                music_sound[0].set_volume(settings['music_volume'] * 0.4)
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

# --- Achievements ---
def show_achievements():
    btn_back = Button(WIDTH // 2, HEIGHT - 55, 240, 55, "BACK", NEON_CYAN, NEON_GREEN, 26)
    while True:
        game_surface.fill(BLACK)
        mouse_pos = get_game_mouse_pos()
        draw_background(game_surface)

        draw_text(game_surface, "ACHIEVEMENTS", 50, WIDTH // 2, 50, NEON_YELLOW, center=True, glow=True)
        unlocked_count = sum(1 for a in achievements.values() if a['unlocked'])
        draw_text(game_surface, f"{unlocked_count} / {len(achievements)}", 24, WIDTH // 2, 95,
                  NEON_CYAN, center=True)

        y_pos = 140
        card_w = 720
        card_h = 48
        for key, a in achievements.items():
            cx = WIDTH // 2 - card_w // 2
            color = NEON_GREEN if a['unlocked'] else (60, 60, 80)
            pygame.draw.rect(game_surface, (10, 5, 25), (cx, y_pos, card_w, card_h), border_radius=8)
            pygame.draw.rect(game_surface, color, (cx, y_pos, card_w, card_h), 2, border_radius=8)
            icon_color = NEON_YELLOW if a['unlocked'] else (80, 80, 80)
            draw_text(game_surface, a['icon'], 24, cx + 35, y_pos + card_h // 2, icon_color, center=True)
            name_color = NEON_YELLOW if a['unlocked'] else (120, 120, 120)
            draw_text(game_surface, a['name'], 18, cx + 70, y_pos + 6, name_color)
            draw_text(game_surface, a['desc'], 13, cx + 70, y_pos + 28, (150, 150, 180))
            if a['unlocked']:
                draw_text(game_surface, "[OK]", 15, cx + card_w - 50, y_pos + card_h // 2, NEON_GREEN, center=True)
            else:
                draw_text(game_surface, "[--]", 15, cx + card_w - 50, y_pos + card_h // 2, (100, 100, 100), center=True)
            y_pos += card_h + 5

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

# --- History ---
def show_history():
    btn_back = Button(WIDTH // 2 - 160, HEIGHT - 40, 220, 50, "BACK", NEON_CYAN, NEON_GREEN, 24)
    btn_clear = Button(WIDTH // 2 + 160, HEIGHT - 40, 220, 50, "CLEAR ALL", NEON_RED, NEON_ORANGE, 22)
    scroll_offset = [0]

    while True:
        game_surface.fill(BLACK)
        mouse_pos = get_game_mouse_pos()
        draw_background(game_surface)

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

                draw_text(game_surface, rank, 36, ix + 35, iy + (item_h - 8) // 2,
                          rank_color, center=True, glow=True)
                draw_text(game_surface, f"SCORE: {score}", 20, ix + 70, iy + 6, WHITE)
                draw_text(game_surface, f"LEVEL: {entry.get('level', 1)}   TIME: {entry.get('duration', 0)}s",
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
            draw_text(game_surface, "No games played yet", 28, WIDTH // 2, HEIGHT // 2, (150, 150, 180), center=True)

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

# --- بازی ---
def play_game():
    gs = GameState()
    gs.load_level()

    game_over = False
    paused = False
    paused_msg = "PAUSED"
    final_score = 0
    go_anim = 0
    level_banner = 90
    game_saved = False
    total_frames = 0
    shake = 0
    flash = 0

    btn_resume = Button(WIDTH // 2, HEIGHT // 2 + 20, 300, 60, "RESUME", NEON_GREEN, NEON_CYAN, 28)
    btn_pause_menu = Button(WIDTH // 2, HEIGHT // 2 + 100, 300, 55, "MAIN MENU", NEON_RED, NEON_ORANGE, 24)
    btn_restart = Button(WIDTH // 2, HEIGHT // 2 + 70, 300, 60, "RESTART", NEON_CYAN, NEON_GREEN, 28)
    btn_menu = Button(WIDTH // 2, HEIGHT // 2 + 145, 300, 55, "MAIN MENU", NEON_YELLOW, NEON_ORANGE, 24)

    notifications = []
    active_particles.clear()
    for p in particle_pool:
        p.active = False

    start_music()

    def try_unlock(key):
        if gs.try_unlock(key):
            notifications.append({'ach': achievements[key], 'timer': 180})

    def save_current():
        add_game_to_history(gs.score, gs.level, total_frames // FPS, gs.new_achs)

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
                if event.key == pygame.K_SPACE:
                    if game_over:
                        stop_music()
                        play_game()
                        return
                    elif not paused:
                        # رها کردن توپ
                        for b in gs.balls:
                            if b.stuck_to_paddle:
                                b.stuck_to_paddle = False
                                b.vx = random.choice([-1, 1]) * 3
                                b.vy = -6
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
            keys = pygame.key.get_pressed()
            gs.paddle.update(keys)

            # آپدیت display_score
            if gs.display_score < gs.score:
                gs.display_score += max(1, (gs.score - gs.display_score) // 5)
                if gs.display_score > gs.score:
                    gs.display_score = gs.score

            # combo timer
            if gs.combo_timer > 0:
                gs.combo_timer -= 1
                if gs.combo_timer == 0:
                    gs.combo = 0

            # slow timer
            if gs.slow_timer > 0:
                gs.slow_timer -= 1

            # banner
            if level_banner > 0:
                level_banner -= 1
            if gs.multiball_banner > 0:
                gs.multiball_banner -= 1

            # shake و flash
            if shake > 0:
                shake -= 1
            if flash > 0:
                flash -= 5

            # آپدیت توپ‌ها
            for ball in gs.balls[:]:
                ball.update(gs.paddle, gs.slow_timer)

                # برخورد با پدال
                pr = gs.paddle.rect()
                br = pygame.Rect(int(ball.x - ball.radius), int(ball.y - ball.radius),
                                 ball.radius * 2, ball.radius * 2)
                if ball.vy > 0 and br.colliderect(pr):
                    ball.y = pr.y - ball.radius
                    # زاویه بر اساس محل برخورد
                    hit_pos = (ball.x - gs.paddle.x) / gs.paddle.w  # 0..1
                    angle = (hit_pos - 0.5) * 2  # -1..1
                    speed = ball.speed * (1 + (gs.level - 1) * 0.03)
                    ball.vx = angle * speed
                    ball.vy = -abs(math.sqrt(max(1, speed ** 2 - ball.vx ** 2)))
                    # normalize
                    mag = math.hypot(ball.vx, ball.vy)
                    if mag > 0:
                        ball.vx = ball.vx / mag * speed
                        ball.vy = ball.vy / mag * speed
                    if ball.vy > -3:
                        ball.vy = -3
                    play_sound('bounce')

                    if gs.paddle.sticky_timer > 0:
                        ball.stuck_to_paddle = True

                # خارج شدن از پایین
                if ball.y - ball.radius > HEIGHT:
                    if ball in gs.balls:
                        gs.balls.remove(ball)

            # اگه همه توپ‌ها از دست رفتن
            if not gs.balls:
                gs.lives -= 1
                gs.level_lost_life = True
                play_sound('life_lost')
                flash = 100
                if gs.lives <= 0:
                    game_over = True
                    final_score = gs.score
                    highscore[0] = max(highscore[0], gs.score)
                    if gs.score >= 1000: try_unlock('score_1000')
                    if gs.score >= 5000: try_unlock('score_5000')
                    if gs.score >= 10000: try_unlock('score_10000')
                    save_current()
                    game_saved = True
                    play_sound('gameover')
                    go_anim = 0
                else:
                    new_ball = Ball(WIDTH // 2, HEIGHT - 90, 0, -6, 6)
                    new_ball.stuck_to_paddle = True
                    gs.balls.append(new_ball)

            # آپدیت آجرها
            boss_shot = False
            for brick in gs.bricks[:]:
                brick.update()
                if brick.is_boss:
                    brick.boss_shoot_timer += 1
                    if brick.boss_shoot_timer > 90:
                        brick.boss_shoot_timer = 0
                        boss_shot = True

            # باس شلیک نمی‌کنه چون brick breaker هست، فقط حرکت می‌کنه

            # برخورد توپ با آجر
            for ball in gs.balls:
                if ball.stuck_to_paddle:
                    continue
                # حذف trail برای دقت
                for brick in gs.bricks[:]:
                    bx = brick.x
                    by = brick.y
                    bw = brick.w
                    bh = brick.h
                    closest_x = max(bx, min(ball.x, bx + bw))
                    closest_y = max(by, min(ball.y, by + bh))
                    dx = ball.x - closest_x
                    dy = ball.y - closest_y
                    if dx * dx + dy * dy < ball.radius * ball.radius:
                        # برخورد!
                        brick.hp -= 1
                        brick.hit_flash = 5
                        play_sound('brick')
                        gs.combo += 1
                        gs.combo_timer = 90
                        gs.max_combo = max(gs.max_combo, gs.combo)
                        try_unlock('first_brick')
                        if gs.max_combo >= 5: try_unlock('combo_5')
                        if gs.max_combo >= 10: try_unlock('combo_10')

                        # تشخیص جهت برخورد
                        overlap_x = min(ball.x + ball.radius - bx, bx + bw - (ball.x - ball.radius))
                        overlap_y = min(ball.y + ball.radius - by, by + bh - (ball.y - ball.radius))
                        if overlap_x < overlap_y:
                            ball.vx = -ball.vx
                            ball.x += ball.vx * 0.5
                        else:
                            ball.vy = -ball.vy
                            ball.y += ball.vy * 0.5

                        if brick.hp <= 0:
                            if brick in gs.bricks:
                                gs.bricks.remove(brick)
                            # امتیاز
                            if brick.is_boss:
                                pts = 500
                                play_sound('big_explosion')
                                shake = 25
                                flash = 200
                                for _ in range(80):
                                    spawn_particles(brick.x + random.uniform(0, brick.w),
                                                    brick.y + random.uniform(0, brick.h),
                                                    NEON_PINK, 1, 1.5, 1.5, 1.5)
                            else:
                                pts = 10 * (1 + gs.combo * 0.1)
                                pts = int(pts)
                                for _ in range(12):
                                    spawn_particles(brick.x + random.uniform(0, brick.w),
                                                    brick.y + random.uniform(0, brick.h),
                                                    brick.color, 1, 1.2, 1.2, 1.2)
                            combo_bonus = 1 + (gs.combo - 1) * 0.1
                            gs.score += int(pts * combo_bonus)
                            # powerup drop
                            if random.random() < 0.15:
                                gs.powerups.append(PowerUp(brick.x + brick.w // 2, brick.y + brick.h // 2))
                        break

            # آپدیت لیزرها
            for l in gs.lasers[:]:
                l.update()
                if l.y < 80:
                    gs.lasers.remove(l)
                    continue
                # برخورد با آجر
                lr = pygame.Rect(l.x - 2, l.y - 12, 4, 16)
                for brick in gs.bricks[:]:
                    br = pygame.Rect(int(brick.x), int(brick.y), int(brick.w), int(brick.h))
                    if lr.colliderect(br):
                        brick.hp -= 1
                        brick.hit_flash = 5
                        if brick.hp <= 0:
                            if brick in gs.bricks:
                                gs.bricks.remove(brick)
                            pts = 500 if brick.is_boss else 10
                            gs.score += pts
                            for _ in range(12):
                                spawn_particles(brick.x + random.uniform(0, brick.w),
                                                brick.y + random.uniform(0, brick.h),
                                                brick.color, 1, 1.2)
                        if l in gs.lasers:
                            gs.lasers.remove(l)
                        break

            # شلیک لیزر با Space اگه لیزر فعاله
            if gs.paddle.laser_timer > 0 and keys[pygame.K_SPACE]:
                if random.random() < 0.3:
                    pr = gs.paddle.rect()
                    gs.lasers.append(LaserBullet(pr.x + 15, pr.y))
                    gs.lasers.append(LaserBullet(pr.right - 15, pr.y))
                    play_sound('laser') if 'laser' in sounds else None

            # برخورد پدال با powerup
            for p in gs.powerups[:]:
                p.update()
                pr = gs.paddle.rect()
                if pr.colliderect(pygame.Rect(int(p.x - p.radius), int(p.y - p.radius),
                                              p.radius * 2, p.radius * 2)):
                    play_sound('powerup')
                    for _ in range(15):
                        spawn_particles(p.x, p.y, WHITE, 1, 1.2)
                    if p.type == 'multi':
                        # multiball
                        new_balls = []
                        for ball in gs.balls[:2]:
                            for _ in range(2):
                                nb = Ball(ball.x, ball.y,
                                          random.uniform(-5, 5), random.uniform(-7, -4), 6)
                                new_balls.append(nb)
                        gs.balls.extend(new_balls)
                        gs.multiball_banner = 90
                        play_sound('multiball')
                        try_unlock('multiball')
                    elif p.type == 'wide':
                        gs.paddle.wide_timer = 600
                    elif p.type == 'slow':
                        gs.slow_timer = 360
                    elif p.type == 'laser':
                        gs.paddle.laser_timer = 480
                    elif p.type == 'life':
                        gs.lives = min(5, gs.lives + 1)
                    elif p.type == 'sticky':
                        gs.paddle.sticky_timer = 480
                    gs.powerups.remove(p)
                elif p.y > HEIGHT:
                    gs.powerups.remove(p)

            # ذرات
            for part in active_particles[:]:
                part.update()
                if not part.active:
                    active_particles.remove(part)

            # چک تموم شدن مرحله
            if len(gs.bricks) == 0:
                # level up
                if not gs.level_lost_life:
                    try_unlock('no_life_lost')
                gs.level += 1
                if gs.level == 3: try_unlock('level_3')
                if gs.level == 5: try_unlock('level_5')
                play_sound('level_up')
                level_banner = 90
                gs.load_level()

        # --- رسم ---
        game_surface.fill(BLACK)
        draw_background(game_surface)

        # آجرها
        for brick in gs.bricks:
            brick.draw(game_surface)

        # powerups
        for p in gs.powerups:
            p.draw(game_surface)

        # لیزرها
        for l in gs.lasers:
            l.draw(game_surface)

        # ذرات
        for part in active_particles:
            part.draw(game_surface)

        # پدال
        gs.paddle.draw(game_surface)

        # توپ‌ها
        for ball in gs.balls:
            ball.draw(game_surface)

        # Flash
        if flash > 0:
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 100, 100, flash))
            game_surface.blit(fs, (0, 0))

        # Banner
        if level_banner > 0:
            alpha = min(255, level_banner * 4)
            color = NEON_CYAN if level_banner > 45 else NEON_GREEN
            draw_text(game_surface, f"LEVEL {gs.level}", 80, WIDTH // 2, HEIGHT // 2 - 50,
                      color, center=True, glow=True)
            draw_text(game_surface, "GET READY!", 30, WIDTH // 2, HEIGHT // 2 + 20,
                      WHITE, center=True, glow=True)

        if gs.multiball_banner > 0:
            alpha = min(255, gs.multiball_banner * 4)
            size = 90 + int(math.sin(t * 10) * 8)
            draw_text(game_surface, "MULTIBALL", size, WIDTH // 2, HEIGHT // 2,
                      WHITE, center=True, glow=True)

        # HUD
        draw_hud(game_surface, gs)

        # Notifications
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

        # Game Over
        if game_over:
            go_anim += 1
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            game_surface.blit(overlay, (0, 0))
            box_w, box_h = 520, 400
            box_x = WIDTH // 2 - box_w // 2
            box_y = HEIGHT // 2 - box_h // 2
            pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h))
            pygame.draw.rect(game_surface, NEON_PINK, (box_x, box_y, box_w, box_h), 3)
            pygame.draw.rect(game_surface, NEON_CYAN, (box_x + 5, box_y + 5, box_w - 10, box_h - 10), 1)
            draw_text(game_surface, "GAME OVER", 60, WIDTH // 2, box_y + 60,
                      NEON_RED, center=True, glow=True)
            draw_text(game_surface, f"SCORE: {final_score}", 34, WIDTH // 2, box_y + 125,
                      WHITE, center=True)
            hs = highscore[0]
            if final_score >= hs and final_score > 0:
                draw_text(game_surface, "* NEW HIGH SCORE! *", 24, WIDTH // 2, box_y + 165,
                          NEON_YELLOW, center=True, glow=True)
            else:
                draw_text(game_surface, f"HIGH SCORE: {hs}", 20, WIDTH // 2, box_y + 165,
                          NEON_YELLOW, center=True)
            if go_anim > 15:
                btn_restart.update(mouse_pos)
                btn_menu.update(mouse_pos)
                btn_restart.draw(game_surface)
                btn_menu.draw(game_surface)

        present()

    stop_music()

# --- Main ---
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