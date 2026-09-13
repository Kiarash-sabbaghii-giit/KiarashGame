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

BASE_W, BASE_H = 1200, 750
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("NEON FISHER")
game_surface = pygame.Surface((BASE_W, BASE_H))

clock = pygame.time.Clock()
FPS = 60

# --- رنگ‌ها ---
BLACK = (0, 0, 4)
DARK_BG = (2, 5, 15)
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

# --- آب ---
WATER_TOP = 100  # سطح آب
WATER_BOTTOM = HEIGHT - 80  # کف دریا

# --- ذخیره ---
SAVE_FILE = "neon_fisher_save.json"
settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'difficulty': 1.0,
    'screen_shake': True,
    'time_limit': 60,
}
achievements = {
    'first_catch': {'name': 'FIRST CATCH', 'desc': 'Catch your first fish', 'unlocked': False, 'icon': 'F'},
    'catch_10': {'name': 'ROOKIE', 'desc': 'Catch 10 fish', 'unlocked': False, 'icon': 'F10'},
    'catch_50': {'name': 'VETERAN', 'desc': 'Catch 50 fish', 'unlocked': False, 'icon': 'F50'},
    'catch_200': {'name': 'LEGEND', 'desc': 'Catch 200 fish', 'unlocked': False, 'icon': 'F200'},
    'first_shark': {'name': 'SHARK HUNTER', 'desc': 'Catch a shark', 'unlocked': False, 'icon': 'S'},
    'golden_fish': {'name': 'GOLDEN CATCH', 'desc': 'Catch a golden fish', 'unlocked': False, 'icon': 'G'},
    'treasure': {'name': 'TREASURE HUNTER', 'desc': 'Catch a treasure chest', 'unlocked': False, 'icon': 'T'},
    'octopus': {'name': 'OCTOPUS HUNTER', 'desc': 'Catch an octopus', 'unlocked': False, 'icon': 'O'},
    'combo_5': {'name': 'COMBO FISHER', 'desc': 'Catch 5 fish in a row', 'unlocked': False, 'icon': 'C5'},
    'combo_10': {'name': 'COMBO MASTER', 'desc': 'Catch 10 fish in a row', 'unlocked': False, 'icon': 'C10'},
    'score_1000': {'name': 'SCORER', 'desc': 'Score 1000 points', 'unlocked': False, 'icon': '$1K'},
    'score_5000': {'name': 'ACE', 'desc': 'Score 5000 points', 'unlocked': False, 'icon': '$5K'},
    'score_10000': {'name': 'GRANDMASTER', 'desc': 'Score 10000 points', 'unlocked': False, 'icon': '$10K'},
    'perfect_minute': {'name': 'PERFECT', 'desc': 'Catch 20 fish in 1 minute', 'unlocked': False, 'icon': 'P'},
    'frenzy_catch': {'name': 'FRENZY!', 'desc': 'Catch 10 fish during frenzy', 'unlocked': False, 'icon': 'FR'},
}
highscore = [0]
game_history = []
total_catches = [0]
total_score = [0]
total_sharks = [0]


def load_save():
    global settings, achievements, highscore, game_history, total_catches, total_score, total_sharks
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
            settings.update(data.get('settings', {}))
            for k, v in data.get('achievements', {}).items():
                if k in achievements:
                    achievements[k]['unlocked'] = v
            highscore[0] = data.get('highscore', 0)
            game_history = data.get('game_history', [])
            total_catches[0] = data.get('total_catches', 0)
            total_score[0] = data.get('total_score', 0)
            total_sharks[0] = data.get('total_sharks', 0)
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
                'total_catches': total_catches[0],
                'total_score': total_score[0],
                'total_sharks': total_sharks[0],
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


def add_game_to_history(score, catches, duration, new_achs):
    entry = {
        'score': score,
        'catches': catches,
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
    sounds['catch'] = make_sound(600, 1200, 0.2, 0.22, 'sine')
    sounds['big_catch'] = make_sound(400, 1000, 0.4, 0.28, 'sine')
    sounds['miss'] = make_sound(300, 200, 0.15, 0.15, 'square')
    sounds['cast'] = make_sound(800, 1400, 0.15, 0.15, 'sine')
    sounds['line_break'] = make_sound(200, 100, 0.3, 0.28, 'saw')
    sounds['shark'] = make_sound(150, 100, 0.4, 0.25, 'saw')
    sounds['frenzy'] = make_sound(500, 1500, 0.6, 0.30, 'sine')
    sounds['gameover'] = make_sound(500, 60, 1.2, 0.30, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['combo'] = make_sound(1200, 1800, 0.15, 0.18, 'sine')

    bass = [65.4, 65.4, 73.4, 73.4, 82.4, 82.4, 73.4, 73.4]
    lead = [392, 440, 494, 440, 392, 349, 330, 349]
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

    def spawn(self, x, y, color, speed_mult=1.0, size_mult=1.0, life_mult=1.0, gravity=-0.05):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 5) * speed_mult
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = int(random.randint(30, 60) * life_mult)
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


def spawn_particles(x, y, color, count, speed_mult=1.0, size_mult=1.0, life_mult=1.0, gravity=-0.05):
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
#                    Bubble
# ============================================================
class Bubble:
    def __init__(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(WATER_TOP, WATER_BOTTOM)
        self.size = random.randint(2, 8)
        self.speed = random.uniform(0.3, 1.5)
        self.wobble = random.uniform(0, math.pi * 2)
        self.wobble_speed = random.uniform(0.02, 0.05)

    def update(self):
        self.y -= self.speed
        self.wobble += self.wobble_speed
        if self.y < WATER_TOP:
            self.y = WATER_BOTTOM
            self.x = random.uniform(0, WIDTH)

    def draw(self, surface):
        # حباب با هاله
        wobble_x = self.x + math.sin(self.wobble) * 5
        pygame.draw.circle(surface, (*NEON_CYAN, 100), (int(wobble_x), int(self.y)), self.size, 1)
        pygame.draw.circle(surface, (*WHITE, 150), (int(wobble_x - self.size / 3), int(self.y - self.size / 3)), max(1, self.size // 3))


# ============================================================
#                    Seaweed
# ============================================================
class Seaweed:
    def __init__(self, x):
        self.x = x
        self.base_y = WATER_BOTTOM
        self.segments = []
        self.phase = random.uniform(0, math.pi * 2)
        self.height = random.randint(80, 200)
        num_segments = self.height // 20
        for i in range(num_segments):
            self.segments.append({
                'y': self.base_y - i * 20,
                'width': max(3, 15 - i),
            })
        self.color = random.choice([NEON_GREEN, NEON_CYAN, NEON_PURPLE, (100, 255, 100)])

    def update(self):
        self.phase += 0.03

    def draw(self, surface):
        for i, seg in enumerate(self.segments):
            wave = math.sin(self.phase + i * 0.3) * 8
            x = self.x + wave
            y = seg['y']
            pygame.draw.circle(surface, self.color, (int(x), int(y)), seg['width'])


# ============================================================
#                    Fish
# ============================================================
class Fish:
    def __init__(self, fish_type='small', x=None, y=None):
        self.fish_type = fish_type
        self.alive = True
        self.caught = False

        if x is None:
            if random.random() < 0.5:
                self.x = -50
                self.vx = random.uniform(1, 3)
            else:
                self.x = WIDTH + 50
                self.vx = random.uniform(-3, -1)
        else:
            self.x = x
            self.vx = random.uniform(-3, 3)

        if y is None:
            self.y = random.uniform(WATER_TOP + 100, WATER_BOTTOM - 50)
        else:
            self.y = y

        self.vy = random.uniform(-0.5, 0.5)
        self.facing = 1 if self.vx > 0 else -1
        self.anim_time = random.uniform(0, 10)

        # مشخصات بر اساس نوع
        if fish_type == 'small':
            self.size = 15
            self.color = random.choice([NEON_CYAN, NEON_PINK, NEON_GREEN, NEON_YELLOW])
            self.score_value = 10
            self.weight = 1
            self.speed_mult = 1.5
        elif fish_type == 'medium':
            self.size = 25
            self.color = random.choice([NEON_ORANGE, NEON_PURPLE, NEON_BLUE])
            self.score_value = 25
            self.weight = 3
            self.speed_mult = 1.0
        elif fish_type == 'big':
            self.size = 40
            self.color = NEON_RED
            self.score_value = 50
            self.weight = 6
            self.speed_mult = 0.6
        elif fish_type == 'golden':
            self.size = 22
            self.color = (255, 215, 0)
            self.score_value = 200
            self.weight = 2
            self.speed_mult = 2.0
        elif fish_type == 'squid':
            self.size = 20
            self.color = NEON_MAGENTA
            self.score_value = 40
            self.weight = 2
            self.speed_mult = 2.5
        elif fish_type == 'octopus':
            self.size = 35
            self.color = NEON_PURPLE
            self.score_value = 100
            self.weight = 5
            self.speed_mult = 0.8
            self.hits_remaining = 3
        elif fish_type == 'shark':
            self.size = 60
            self.color = (80, 80, 120)
            self.score_value = 300
            self.weight = 10
            self.speed_mult = 1.5
            self.aggressive = True
        elif fish_type == 'treasure':
            self.size = 30
            self.color = (255, 215, 0)
            self.score_value = 500
            self.weight = 4
            self.speed_mult = 0.3

    def update(self):
        self.x += self.vx * self.speed_mult
        self.y += self.vy
        self.anim_time += 0.15

        # موج خوردن
        self.y += math.sin(self.anim_time * 0.5) * 0.3

        # محدودیت y
        if self.y < WATER_TOP + 50:
            self.y = WATER_TOP + 50
            self.vy = abs(self.vy)
        elif self.y > WATER_BOTTOM - 30:
            self.y = WATER_BOTTOM - 30
            self.vy = -abs(self.vy)

        # حذف از صحنه
        if self.x < -100 or self.x > WIDTH + 100:
            self.alive = False

    def catch_rect(self):
        return pygame.Rect(int(self.x - self.size / 2), int(self.y - self.size / 2),
                           self.size, self.size)

    def draw(self, surface):
        # هاله
        for hr in range(3, 0, -1):
            glow_size = self.size * 2 + hr * 8
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*self.color, 60 - hr * 15),
                               (glow_size // 2, glow_size // 2), glow_size // 2)
            surface.blit(glow, (self.x - glow_size // 2, self.y - glow_size // 2))

        # بدنه
        if self.fish_type == 'squid':
            # اختاپوس کوچک - شکلی متفاوت
            pygame.draw.polygon(surface, self.color, [
                (self.x, self.y - self.size),
                (self.x + self.size, self.y),
                (self.x, self.y + self.size),
                (self.x - self.size, self.y),
            ])
            pygame.draw.polygon(surface, WHITE, [
                (self.x, self.y - self.size),
                (self.x + self.size, self.y),
                (self.x, self.y + self.size),
                (self.x - self.size, self.y),
            ], 2)
            # چوپ‌ها (شاخک‌ها)
            for i in range(4):
                angle = math.pi + i * math.pi / 3
                ex = self.x + math.cos(angle) * self.size * 1.5
                ey = self.y + math.sin(angle) * self.size * 1.5
                pygame.draw.line(surface, self.color, (self.x, self.y), (ex, ey), 3)
        elif self.fish_type == 'octopus':
            # اختاپوس بزرگ
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y - self.size / 2)), self.size)
            # چوپ‌ها
            for i in range(6):
                angle = math.pi + i * math.pi / 5
                ex = self.x + math.cos(angle) * self.size * 1.3
                ey = self.y + math.sin(angle) * self.size * 1.3
                # موج در چوپ‌ها
                wave = math.sin(self.anim_time * 3 + i) * 5
                pygame.draw.line(surface, self.color, (self.x, self.y), (ex + wave, ey), 3)
            # چشم
            pygame.draw.circle(surface, WHITE, (int(self.x - 8), int(self.y - self.size / 2 - 5)), 5)
            pygame.draw.circle(surface, BLACK, (int(self.x - 8), int(self.y - self.size / 2 - 5)), 2)
            # نشانگر چند-ضربه
            if hasattr(self, 'hits_remaining'):
                for i in range(self.hits_remaining):
                    pygame.draw.circle(surface, NEON_RED,
                                       (int(self.x - 20 + i * 15), int(self.y + self.size + 10)), 4)
        elif self.fish_type == 'shark':
            # کوسه
            pygame.draw.polygon(surface, self.color, [
                (self.x - self.size, self.y),  # دم
                (self.x - self.size * 0.5, self.y - self.size / 3),
                (self.x, self.y - self.size / 2),  # باله بالا
                (self.x + self.size * 0.7, self.y - self.size / 4),
                (self.x + self.size, self.y),  # سر
                (self.x + self.size * 0.7, self.y + self.size / 4),
                (self.x, self.y + self.size / 2),  # پایین
                (self.x - self.size * 0.5, self.y + self.size / 3),
            ])
            pygame.draw.polygon(surface, WHITE, [
                (self.x - self.size, self.y),
                (self.x - self.size * 0.5, self.y - self.size / 3),
                (self.x, self.y - self.size / 2),
                (self.x + self.size * 0.7, self.y - self.size / 4),
                (self.x + self.size, self.y),
                (self.x + self.size * 0.7, self.y + self.size / 4),
                (self.x, self.y + self.size / 2),
                (self.x - self.size * 0.5, self.y + self.size / 3),
            ], 3)
            # چشم
            pygame.draw.circle(surface, NEON_RED, (int(self.x + self.size * 0.5), int(self.y - 5)), 5)
            pygame.draw.circle(surface, WHITE, (int(self.x + self.size * 0.5), int(self.y - 5)), 2)
        elif self.fish_type == 'treasure':
            # صندوق گنج
            rect = pygame.Rect(int(self.x - self.size), int(self.y - self.size / 2),
                               self.size * 2, self.size)
            pygame.draw.rect(surface, (139, 69, 19), rect, border_radius=4)
            pygame.draw.rect(surface, (255, 215, 0), rect, 3, border_radius=4)
            # درب
            pygame.draw.line(surface, (255, 215, 0), (rect.x, rect.y + self.size // 3),
                             (rect.right, rect.y + self.size // 3), 3)
            # قفل
            pygame.draw.circle(surface, (255, 215, 0), (int(self.x), int(self.y)), 6)
            pygame.draw.circle(surface, (139, 69, 19), (int(self.x), int(self.y)), 3)
        else:
            # ماهی معمولی
            # دم
            tail_x = self.x - self.facing * self.size
            pygame.draw.polygon(surface, self.color, [
                (tail_x, self.y),
                (tail_x - self.facing * self.size * 0.5, self.y - self.size * 0.6),
                (tail_x - self.facing * self.size * 0.5, self.y + self.size * 0.6),
            ])
            # بدنه
            pygame.draw.ellipse(surface, self.color,
                                (int(self.x - self.size), int(self.y - self.size * 0.6),
                                 self.size * 2, self.size * 1.2))
            # حاشیه سفید
            pygame.draw.ellipse(surface, WHITE,
                                (int(self.x - self.size), int(self.y - self.size * 0.6),
                                 self.size * 2, self.size * 1.2), 2)
            # چشم
            eye_x = self.x + self.facing * self.size * 0.5
            pygame.draw.circle(surface, WHITE, (int(eye_x), int(self.y - 3)), 4)
            pygame.draw.circle(surface, BLACK, (int(eye_x + self.facing), int(self.y - 3)), 2)
            # باله
            pygame.draw.line(surface, self.color,
                             (self.x, self.y - self.size * 0.6),
                             (self.x - self.facing * self.size * 0.3, self.y - self.size),
                             3)

        # برای Golden Fish - درخشش اضافه
        if self.fish_type == 'golden':
            pulse = abs(math.sin(self.anim_time * 2)) * 10
            pygame.draw.circle(surface, (255, 255, 200, 100),
                               (int(self.x), int(self.y)), int(self.size + pulse), 2)


# ============================================================
#                    Hook
# ============================================================
class Hook:
    def __init__(self):
        self.anchor_x = WIDTH // 2
        self.anchor_y = WATER_TOP - 30
        self.x = self.anchor_x
        self.y = self.anchor_y + 30
        self.length = 30  # طول خط
        self.max_length = 500
        self.state = 'idle'  # idle, dropping, rising, caught
        self.caught_fish = None
        self.speed = 8
        self.line_tension = 0  # 0-100
        self.max_tension = 100

    def update(self, mouse_x, mouse_y, mouse_click, fish_list):
        if self.state == 'idle':
            # قلاب در سطح آبه - با ماوس حرکت می‌کنه
            self.anchor_x = max(100, min(WIDTH - 100, mouse_x))
            self.x = self.anchor_x
            self.y = self.anchor_y + 30

            if mouse_click:
                self.state = 'dropping'
                self.length = 30
                play_sound('cast')

        elif self.state == 'dropping':
            self.length += self.speed
            if self.length >= self.max_length:
                self.state = 'rising'

            self.x = self.anchor_x
            self.y = self.anchor_y + self.length

            # چک برخورد با ماهی
            hook_rect = pygame.Rect(int(self.x - 10), int(self.y - 10), 20, 20)
            for fish in fish_list:
                if fish.alive and not fish.caught:
                    if hook_rect.colliderect(fish.catch_rect()):
                        if fish.fish_type == 'octopus':
                            # اختاپوس چند ضربه
                            if fish.hits_remaining > 1:
                                fish.hits_remaining -= 1
                                play_sound('catch')
                                # ذرات
                                for _ in range(15):
                                    spawn_particles(fish.x, fish.y, fish.color, 1, 1.5, 1.0, 1.0)
                                # کمی به عقب
                                self.length -= 50
                            else:
                                self.caught_fish = fish
                                fish.caught = True
                                self.state = 'rising'
                                play_sound('catch')
                        else:
                            self.caught_fish = fish
                            fish.caught = True
                            self.state = 'rising'
                            if fish.fish_type in ['big', 'shark', 'treasure']:
                                play_sound('big_catch')
                            else:
                                play_sound('catch')
                            # ذرات
                            for _ in range(20):
                                spawn_particles(fish.x, fish.y, fish.color, 1, 1.5, 1.0, 1.0)
                            break

        elif self.state == 'rising':
            # وزن ماهی سرعت بالا اومدن رو کم می‌کنه
            weight_factor = 1.0
            if self.caught_fish:
                weight_factor = max(0.3, 1.0 - self.caught_fish.weight * 0.08)

            self.length -= self.speed * weight_factor

            if self.length <= 30:
                # رسید به بالا
                if self.caught_fish:
                    # ماهی گرفته شد!
                    self.caught_fish.alive = False
                    # اینجا در play_game مدیریت میشه
                    self.state = 'idle'
                    self.length = 30
                    result = self.caught_fish
                    self.caught_fish = None
                    return result
                self.state = 'idle'
                self.length = 30

            self.x = self.anchor_x
            self.y = self.anchor_y + self.length

            # اگه ماهی گرفته شده، اون رو با قلاب بکش
            if self.caught_fish:
                self.caught_fish.x = self.x
                self.caught_fish.y = self.y + 10
                # کشش خط
                self.line_tension = min(100, self.line_tension + 0.5)
            else:
                self.line_tension = max(0, self.line_tension - 1)

        return None

    def draw(self, surface):
        # خط ماهیگیری
        if self.y > self.anchor_y + 5:
            # با کشش، خط قرمز میشه
            tension = self.line_tension / 100
            line_color = (
                int(NEON_WHITE[0] if 'NEON_WHITE' in dir() else 255),
                int(255 - tension * 200),
                int(255 - tension * 200)
            )
            line_color = (255, int(255 - tension * 200), int(255 - tension * 200))
            pygame.draw.line(surface, line_color,
                             (self.anchor_x, self.anchor_y),
                             (self.x, self.y), 2)

        # چوب ماهیگیری
        pygame.draw.line(surface, (100, 50, 20),
                         (self.anchor_x - 40, self.anchor_y - 60),
                         (self.anchor_x, self.anchor_y), 6)
        pygame.draw.line(surface, NEON_ORANGE,
                         (self.anchor_x - 40, self.anchor_y - 60),
                         (self.anchor_x, self.anchor_y), 2)

        # قلاب
        pygame.draw.circle(surface, NEON_CYAN, (int(self.x), int(self.y)), 8)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 8, 2)
        # قلاب پایین
        pygame.draw.arc(surface, NEON_CYAN,
                        (int(self.x - 12), int(self.y + 5), 24, 20),
                        0, math.pi, 3)


NEON_WHITE = (255, 255, 255)  # placeholder


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
def draw_underwater_bg(surface, time_val, frenzy=False):
    # گرادیان عمودی آب
    for y in range(WATER_TOP, WATER_BOTTOM):
        t = (y - WATER_TOP) / (WATER_BOTTOM - WATER_TOP)
        if frenzy:
            # قرمزتر
            c = (int(30 + 40 * t), int(5 + 20 * t), int(50 + 30 * t))
        else:
            c = (int(5 + 20 * t), int(20 + 30 * t), int(60 + 50 * t))
        pygame.draw.line(surface, c, (0, y), (WIDTH, y))

    # سطح آب
    pygame.draw.rect(surface, (0, 30, 60), (0, 0, WIDTH, WATER_TOP))
    # موج
    for x in range(0, WIDTH, 5):
        wave_y = WATER_TOP + math.sin(x * 0.02 + time_val * 2) * 8
        pygame.draw.line(surface, NEON_CYAN, (x, wave_y), (x, wave_y + 3), 2)
    pygame.draw.line(surface, NEON_CYAN, (0, WATER_TOP), (WIDTH, WATER_TOP), 3)

    # کف دریا
    pygame.draw.rect(surface, (20, 15, 10), (0, WATER_BOTTOM, WIDTH, HEIGHT - WATER_BOTTOM))
    for x in range(0, WIDTH, 30):
        h = random.randint(5, 15)
        pygame.draw.rect(surface, (40, 30, 20), (x, WATER_BOTTOM - h, 30, h))

    # پرتوهای نور
    for i in range(6):
        light_x = (i * 200 + time_val * 20) % (WIDTH + 400) - 200
        light_surf = pygame.Surface((150, WATER_BOTTOM - WATER_TOP), pygame.SRCALPHA)
        pygame.draw.polygon(light_surf, (*NEON_CYAN, 15),
                            [(75, 0), (0, WATER_BOTTOM - WATER_TOP),
                             (150, WATER_BOTTOM - WATER_TOP)])
        surface.blit(light_surf, (light_x, WATER_TOP))


# ============================================================
#                    Menu
# ============================================================
def show_menu():
    menu_time = 0
    btn_start = Button(WIDTH // 2, HEIGHT // 2 + 30, 320, 55, "START FISHING", NEON_CYAN, NEON_GREEN, 28)
    btn_history = Button(WIDTH // 2, HEIGHT // 2 + 95, 320, 45, "HISTORY", NEON_BLUE, NEON_CYAN, 22)
    btn_settings = Button(WIDTH // 2, HEIGHT // 2 + 150, 320, 45, "SETTINGS", NEON_PURPLE, NEON_PINK, 22)
    btn_achievements = Button(WIDTH // 2, HEIGHT // 2 + 205, 320, 45, "ACHIEVEMENTS", NEON_YELLOW, NEON_ORANGE, 22)
    btn_quit = Button(WIDTH // 2, HEIGHT // 2 + 260, 320, 42, "QUIT", NEON_RED, NEON_ORANGE, 20)
    btn_fullscreen = Button(WIDTH - 40, 30, 40, 40, "[]", NEON_PURPLE, NEON_CYAN, 20)

    # ماهی‌های تزئینی
    menu_fish = []
    for _ in range(6):
        kinds = ['small', 'medium', 'big', 'golden']
        fish = Fish(random.choice(kinds))
        menu_fish.append(fish)

    # حباب‌ها
    bubbles = [Bubble() for _ in range(30)]

    # گیاهان دریایی
    seaweeds = [Seaweed(random.randint(50, WIDTH - 50)) for _ in range(8)]

    while True:
        game_surface.fill(DARK_BG)
        t = pygame.time.get_ticks() / 1000
        menu_time += 1
        mouse_pos = get_game_mouse_pos()

        # پس‌زمینه
        draw_underwater_bg(game_surface, t)

        # گیاهان
        for sw in seaweeds:
            sw.update()
            sw.draw(game_surface)

        # حباب‌ها
        for b in bubbles:
            b.update()
            b.draw(game_surface)

        # ماهی‌های تزئینی
        for fish in menu_fish[:]:
            fish.update()
            if not fish.alive:
                menu_fish.remove(fish)
                kinds = ['small', 'medium', 'big', 'golden']
                menu_fish.append(Fish(random.choice(kinds)))
            fish.draw(game_surface)

        # عنوان
        title_y = 200 + math.sin(t * 2) * 8
        draw_text(game_surface, "NEON", 72, WIDTH // 2 - 100, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "FISHER", 72, WIDTH // 2 + 120, title_y, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, "CATCH  /  COMBO  /  SURVIVE", 20, WIDTH // 2, title_y + 65,
                  (200, 200, 220), center=True)

        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 22, WIDTH // 2, title_y + 115,
                      NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, f"CATCHES: {total_catches[0]}   SHARKS: {total_sharks[0]}",
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
    slider_time = Slider(WIDTH // 2, 380, 400, 12, (settings['time_limit'] - 30) / 90, 0, 1, "Time Limit")
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
        slider_time.update(mouse_pos, mouse_pressed)
        settings['sfx_volume'] = slider_sfx.value
        settings['music_volume'] = slider_music.value
        settings['time_limit'] = 30 + int(slider_time.value * 90)
        if music_sound[0]:
            try:
                music_sound[0].set_volume(settings['music_volume'] * 0.5)
            except:
                pass

        slider_sfx.draw(game_surface)
        slider_music.draw(game_surface)
        slider_time.draw(game_surface)

        draw_text(game_surface, f"{settings['time_limit']}s", 18, WIDTH // 2 + 230, 370, NEON_YELLOW)

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
                settings['time_limit'] = 60
                for k in achievements:
                    achievements[k]['unlocked'] = False
                highscore[0] = 0
                game_history.clear()
                total_catches[0] = 0
                total_score[0] = 0
                total_sharks[0] = 0
                save_async()
                slider_sfx.value = 0.7
                slider_music.value = 0.5
                slider_time.value = (60 - 30) / 90
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
            draw_text(game_surface, a['icon'], 14, cx + 35, y_pos + card_h // 2, icon_color, center=True)
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

        draw_text(game_surface, "FISHING HISTORY", 46, WIDTH // 2, 35, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, f"Total sessions: {len(game_history)}", 16, WIDTH // 2, 72, NEON_YELLOW, center=True)

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
                draw_text(game_surface, f"CATCHES: {entry.get('catches', 0)}   TIME: {entry.get('duration', 0)}s",
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
            draw_text(game_surface, "No sessions yet", 28, WIDTH // 2, HEIGHT // 2, (150, 150, 180), center=True)

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
    hook = Hook()
    fishes = []
    bubbles = [Bubble() for _ in range(40)]
    seaweeds = [Seaweed(random.randint(50, WIDTH - 50)) for _ in range(10)]

    # امتیاز
    score = 0
    display_score = 0
    catches = 0
    combo = 0
    combo_timer = 0
    max_combo = 0
    total_frames = 0
    fish_spawn_timer = 0

    # زمان
    time_left = settings['time_limit'] * FPS

    # Frenzy mode
    frenzy_timer = 0
    frenzy_active = False
    frenzy_cooldown = FPS * 20
    frenzy_catches = 0

    # حالت
    game_over = False
    paused = False
    final_score = 0
    final_catches = 0

    # افکت‌ها
    screen_shake = 0
    flash = 0
    new_achs = []
    notifications = []
    go_anim = 0
    game_saved = False

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
        add_game_to_history(score, catches, total_frames // FPS, new_achs)

    def spawn_fish():
        # انواع ماهی با شانس
        if frenzy_active:
            weights = {
                'small': 20, 'medium': 15, 'big': 8, 'golden': 5,
                'squid': 10, 'octopus': 5, 'shark': 3, 'treasure': 4
            }
        else:
            weights = {
                'small': 50, 'medium': 25, 'big': 10, 'golden': 2,
                'squid': 8, 'octopus': 3, 'shark': 1, 'treasure': 1
            }
        total = sum(weights.values())
        r = random.randint(1, total)
        cum = 0
        kind = 'small'
        for k, w in weights.items():
            cum += w
            if r <= cum:
                kind = k
                break
        fishes.append(Fish(kind))

    running = True
    while running:
        clock.tick(FPS)
        t = pygame.time.get_ticks() / 1000
        mouse_pos = get_game_mouse_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

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
            time_left -= 1

            if display_score < score:
                display_score += max(1, (score - display_score) // 5)
                if display_score > score:
                    display_score = score

            if combo_timer > 0:
                combo_timer -= 1
                if combo_timer == 0:
                    combo = 0

            # Frenzy timer
            if not frenzy_active:
                frenzy_cooldown -= 1
                if frenzy_cooldown <= 0:
                    frenzy_active = True
                    frenzy_timer = FPS * 10  # 10 ثانیه
                    frenzy_catches = 0
                    play_sound('frenzy')
                    flash = 200
                    if settings['screen_shake']:
                        screen_shake = 15
            else:
                frenzy_timer -= 1
                if frenzy_timer <= 0:
                    frenzy_active = False
                    frenzy_cooldown = FPS * random.randint(30, 50)
                    if frenzy_catches >= 10:
                        try_unlock('frenzy_catch')

            # آپدیت گیاهان
            for sw in seaweeds:
                sw.update()

            # آپدیت حباب‌ها
            for b in bubbles:
                b.update()

            # اسپاون ماهی
            fish_spawn_timer += 1
            max_fish = 15 if frenzy_active else 8
            spawn_rate = 30 if frenzy_active else 60
            if fish_spawn_timer >= spawn_rate and len(fishes) < max_fish:
                fish_spawn_timer = 0
                spawn_fish()

            # آپدیت قلاب
            caught_fish = hook.update(mouse_pos[0], mouse_pos[1], mouse_pressed, fishes)

            if caught_fish:
                # ماهی گرفته شد!
                catches += 1
                total_catches[0] += 1
                combo += 1
                combo_timer = 120
                max_combo = max(max_combo, combo)
                combo_mult = 1 + (combo - 1) * 0.15
                points = int(caught_fish.score_value * combo_mult)
                if frenzy_active:
                    points *= 2
                    frenzy_catches += 1
                score += points
                total_score[0] += points

                if caught_fish.fish_type == 'shark':
                    total_sharks[0] += 1
                    try_unlock('first_shark')
                    if settings['screen_shake']:
                        screen_shake = 25
                elif caught_fish.fish_type == 'golden':
                    try_unlock('golden_fish')
                    if settings['screen_shake']:
                        screen_shake = 15
                elif caught_fish.fish_type == 'treasure':
                    try_unlock('treasure')
                    if settings['screen_shake']:
                        screen_shake = 20
                elif caught_fish.fish_type == 'octopus':
                    try_unlock('octopus')

                # افکت
                flash = 100
                for _ in range(30):
                    spawn_particles(caught_fish.x, caught_fish.y, caught_fish.color, 1, 2.0, 1.5, 1.2)

                # چک دستاوردها
                if catches >= 1: try_unlock('first_catch')
                if catches >= 10: try_unlock('catch_10')
                if catches >= 50: try_unlock('catch_50')
                if catches >= 200: try_unlock('catch_200')
                if combo >= 5: try_unlock('combo_5')
                if combo >= 10: try_unlock('combo_10')
                if score >= 1000: try_unlock('score_1000')
                if score >= 5000: try_unlock('score_5000')
                if score >= 10000: try_unlock('score_10000')

                if combo > 1:
                    play_sound('combo')

            # آپدیت ماهی‌ها
            for f in fishes[:]:
                f.update()
                if not f.alive:
                    fishes.remove(f)

            # چک خط پاره شدن
            if hook.line_tension >= hook.max_tension:
                # خط پاره شد
                play_sound('line_break')
                if hook.caught_fish:
                    # ماهی فرار می‌کنه
                    hook.caught_fish.caught = False
                    for _ in range(20):
                        spawn_particles(hook.caught_fish.x, hook.caught_fish.y, NEON_RED, 1, 2.0, 1.5)
                    hook.caught_fish = None
                hook.line_tension = 0
                hook.state = 'idle'
                hook.length = 30

            # چک پایان زمان
            if time_left <= 0:
                game_over = True
                final_score = score
                final_catches = catches
                highscore[0] = max(highscore[0], score)
                # چک دستاورد
                if catches >= 20:
                    try_unlock('perfect_minute')
                save_current()
                game_saved = True
                play_sound('gameover')
                go_anim = 0

            # آپدیت ذرات
            for p in active_particles[:]:
                p.update()
                if not p.active:
                    active_particles.remove(p)

            if screen_shake > 0:
                screen_shake -= 1
            if flash > 0:
                flash -= 6

        # ============================================================
        #                    رسم
        # ============================================================
        game_surface.fill(DARK_BG)
        offset_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        offset_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0

        play_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # پس‌زمینه
        draw_underwater_bg(play_layer, t, frenzy_active)

        # گیاهان
        for sw in seaweeds:
            sw.draw(play_layer)

        # حباب‌ها
        for b in bubbles:
            b.draw(play_layer)

        # ماهی‌ها
        for f in fishes:
            f.draw(play_layer)

        # قلاب
        hook.draw(play_layer)

        # ذرات
        for p in active_particles:
            p.draw(play_layer)

        if flash > 0:
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 200, 100, flash))
            play_layer.blit(fs, (0, 0))

        if frenzy_active:
            # افکت frenzy
            frenzy_alpha = abs(math.sin(t * 5)) * 40
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 0, 100, int(frenzy_alpha)))
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
        draw_text(game_surface, "NEON FISHER", 20, 25, 10, NEON_CYAN, glow=True)
        draw_text(game_surface, f"CATCHES: {catches}   COMBO: x{combo}", 12, 25, 38, NEON_YELLOW)

        # Score
        draw_text(game_surface, "SCORE", 14, WIDTH - 25, 10, NEON_CYAN)
        draw_text(game_surface, f"{display_score}", 26, WIDTH - 25, 28, WHITE, glow=True)

        # Time
        time_sec = time_left // FPS
        time_color = NEON_GREEN if time_sec > 20 else NEON_YELLOW if time_sec > 10 else NEON_RED
        draw_text(game_surface, "TIME", 14, WIDTH // 2 - 50, 10, NEON_CYAN)
        draw_text(game_surface, f"{time_sec}s", 28, WIDTH // 2 - 50, 28, time_color, glow=True)

        # Frenzy
        if frenzy_active:
            frenzy_sec = frenzy_timer // FPS
            draw_text(game_surface, f"FRENZY! {frenzy_sec}s", 24, WIDTH // 2 + 100, 20,
                      NEON_RED, center=True, glow=True)

        # Tension bar
        if hook.line_tension > 0:
            bar_w = 200
            bar_x = WIDTH // 2 - bar_w // 2
            bar_y = 78
            pygame.draw.rect(game_surface, (20, 20, 40), (bar_x, bar_y, bar_w, 8))
            ratio = hook.line_tension / hook.max_tension
            tension_color = NEON_GREEN if ratio < 0.5 else NEON_YELLOW if ratio < 0.75 else NEON_RED
            pygame.draw.rect(game_surface, tension_color, (bar_x, bar_y, bar_w * ratio, 8))
            pygame.draw.rect(game_surface, WHITE, (bar_x, bar_y, bar_w, 8), 1)
            draw_text(game_surface, "LINE TENSION", 10, bar_x, bar_y + 12, WHITE)

        # راهنما
        if total_frames < 200:
            controls = [
                "MOVE MOUSE: aim hook",
                "CLICK: drop hook",
                "Catch fish, earn score!",
            ]
            for i, line in enumerate(controls):
                draw_text(game_surface, line, 14, WIDTH // 2, HEIGHT - 80 + i * 20,
                          (150, 200, 220), center=True)

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
            draw_text(game_surface, "TIME'S UP!", 60, WIDTH // 2, box_y + 55,
                      NEON_RED, center=True, glow=True)
            draw_text(game_surface, f"SCORE: {final_score}", 32,
                      WIDTH // 2, box_y + 120, WHITE, center=True)
            draw_text(game_surface, f"CATCHES: {final_catches}   MAX COMBO: x{max_combo}",
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