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

BASE_W, BASE_H = 1100, 750
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("NEON DARTS")
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

# --- تخته دارت ---
BOARD_X = WIDTH // 2 - 100
BOARD_Y = HEIGHT // 2
BOARD_RADIUS = 280

# شعاع‌های تخته (نسبت به شعاع کل)
R_SINGLE_INNER = 0.15  # از مرکز
R_TRIPLE_OUTER = 0.50  # نوار Triple
R_DOUBLE_INNER = 0.85  # از R_TRIPLE_OUTER تا DOUBLE
R_DOUBLE_OUTER = 1.00

# زاویه‌ی هر عدد (20 در بالا)
NUMBER_ORDER = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5]

# --- ذخیره ---
SAVE_FILE = "neon_darts_save.json"
settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'difficulty': 1.0,
    'screen_shake': True,
    'wind_enabled': True,
}
achievements = {
    'first_throw': {'name': 'FIRST THROW', 'desc': 'Throw your first dart', 'unlocked': False, 'icon': '>'},
    'first_bull': {'name': 'BULLSEYE!', 'desc': 'Hit the bullseye', 'unlocked': False, 'icon': '50'},
    'bull_10': {'name': 'BULL MASTER', 'desc': 'Hit 10 bullseyes', 'unlocked': False, 'icon': 'B10'},
    'triple_20': {'name': 'TRIPLE 20', 'desc': 'Hit triple 20', 'unlocked': False, 'icon': 'T20'},
    't20_5': {'name': 'T20 KING', 'desc': 'Hit triple 20 five times', 'unlocked': False, 'icon': 'T5'},
    'checkout': {'name': 'CHECKOUT!', 'desc': 'Complete a checkout', 'unlocked': False, 'icon': 'C'},
    'nine_dart': {'name': '9 DART FINISH', 'desc': 'Win with 9 darts', 'unlocked': False, 'icon': '9D'},
    'win_301': {'name': 'WINNER 301', 'desc': 'Win a 301 game', 'unlocked': False, 'icon': 'W3'},
    'win_501': {'name': 'WINNER 501', 'desc': 'Win a 501 game', 'unlocked': False, 'icon': 'W5'},
    'win_cricket': {'name': 'CRICKET MASTER', 'desc': 'Win a Cricket game', 'unlocked': False, 'icon': 'CR'},
    'score_100': {'name': 'TON+', 'desc': 'Score 100+ in one turn', 'unlocked': False, 'icon': '100'},
    'score_180': {'name': '180!', 'desc': 'Score 180 in one turn', 'unlocked': False, 'icon': '180'},
    'hat_trick': {'name': 'HAT TRICK', 'desc': 'Hit 3 bullseyes in a row', 'unlocked': False, 'icon': 'HT'},
    'perfect_leg': {'name': 'PERFECT LEG', 'desc': 'Win a leg without missing', 'unlocked': False, 'icon': 'PL'},
    'beat_hard': {'name': 'BEAT HARD AI', 'desc': 'Beat Hard AI', 'unlocked': False, 'icon': 'H'},
}
highscore = [0]
game_history = []
total_throws = [0]
total_bulls = [0]
total_180s = [0]


def load_save():
    global settings, achievements, highscore, game_history, total_throws, total_bulls, total_180s
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
            settings.update(data.get('settings', {}))
            for k, v in data.get('achievements', {}).items():
                if k in achievements:
                    achievements[k]['unlocked'] = v
            highscore[0] = data.get('highscore', 0)
            game_history = data.get('game_history', [])
            total_throws[0] = data.get('total_throws', 0)
            total_bulls[0] = data.get('total_bulls', 0)
            total_180s[0] = data.get('total_180s', 0)
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
                'total_throws': total_throws[0],
                'total_bulls': total_bulls[0],
                'total_180s': total_180s[0],
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


def add_game_to_history(score, mode, darts_used, won, new_achs):
    entry = {
        'score': score,
        'mode': mode,
        'darts_used': darts_used,
        'won': won,
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
    sounds['throw'] = make_sound(300, 600, 0.15, 0.18, 'saw')
    sounds['hit_board'] = make_sound(400, 200, 0.1, 0.20, 'square')
    sounds['bullseye'] = make_sound(800, 1600, 0.4, 0.28, 'sine')
    sounds['triple'] = make_sound(600, 1200, 0.25, 0.22, 'sine')
    sounds['miss'] = make_sound(200, 100, 0.2, 0.15, 'noise')
    sounds['turn_end'] = make_sound(500, 800, 0.2, 0.20, 'sine')
    sounds['win'] = make_sound(400, 1500, 0.8, 0.30, 'sine')
    sounds['lose'] = make_sound(500, 100, 0.6, 0.25, 'saw')
    sounds['gameover'] = make_sound(500, 60, 1.5, 0.30, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['180'] = make_sound(800, 2000, 0.6, 0.32, 'sine')

    bass = [73.4, 73.4, 82.4, 82.4, 65.4, 65.4, 73.4, 73.4]
    lead = [440, 523, 659, 523, 440, 392, 349, 392]
    music_sound[0] = make_music_loop(bass, lead, 0.25, 0.08)
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

    def spawn(self, x, y, color, speed_mult=1.0, size_mult=1.0, life_mult=1.0, gravity=0.2):
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


def spawn_particles(x, y, color, count, speed_mult=1.0, size_mult=1.0, life_mult=1.0, gravity=0.2):
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
#                    Darboard Logic
# ============================================================
def get_dart_score(x, y):
    """محاسبه امتیاز یک نقطه روی تخته"""
    dx = x - BOARD_X
    dy = y - BOARD_Y
    distance = math.hypot(dx, dy)
    r_normalized = distance / BOARD_RADIUS

    # اگه بیرون تخته
    if r_normalized > 1.0:
        return (0, 'miss', 'MISS')

    # محاسبه زاویه
    angle = math.degrees(math.atan2(-dy, dx))  # -dy چون y معکوس
    # تبدیل به 0-360
    angle = (angle + 90) % 360  # چرخش برای شروع از بالا
    # هر سکتور 18 درجه
    sector_index = int((angle + 9) / 18) % 20
    number = NUMBER_ORDER[sector_index]

    # چک ناحیه
    if r_normalized < 0.045:  # Bullseye inner
        return (50, 'bull', 'INNER BULL')
    elif r_normalized < 0.08:  # Outer Bull
        return (25, 'outer_bull', 'OUTER BULL')
    elif r_normalized < R_SINGLE_INNER:
        return (number, 'single', f'SINGLE {number}')
    elif r_normalized < R_TRIPLE_OUTER:
        # چک نوار Triple (بین R_SINGLE_INNER و R_TRIPLE_OUTER)
        # نوار triple بین 0.42 تا 0.50
        if r_normalized < 0.42:
            return (number, 'single', f'SINGLE {number}')
        else:
            return (number * 3, 'triple', f'TRIPLE {number}')
    elif r_normalized < R_DOUBLE_INNER:
        return (number, 'single', f'SINGLE {number}')
    elif r_normalized < R_DOUBLE_OUTER:
        return (number * 2, 'double', f'DOUBLE {number}')
    else:
        return (0, 'miss', 'MISS')


# ============================================================
#                    Dart
# ============================================================
class Dart:
    def __init__(self, start_x, start_y, vx, vy):
        self.x = start_x
        self.y = start_y
        self.vx = vx
        self.vy = vy
        self.alive = True
        self.stuck = False
        self.stuck_x = 0
        self.stuck_y = 0
        self.angle = math.degrees(math.atan2(vy, vx))
        self.trail = []
        self.score = 0
        self.score_type = ''
        self.score_label = ''
        self.anim_time = 0

    def update(self, wind=0):
        if self.stuck:
            self.anim_time += 0.15
            return

        self.trail.append((self.x, self.y))
        if len(self.trail) > 15:
            self.trail.pop(0)

        # گرانش
        self.vy += 0.3
        # باد
        self.vx += wind * 0.01

        self.x += self.vx
        self.y += self.vy
        self.angle = math.degrees(math.atan2(self.vy, self.vx))

        # چک برخورد با تخته
        dx = self.x - BOARD_X
        dy = self.y - BOARD_Y
        dist = math.hypot(dx, dy)
        if dist <= BOARD_RADIUS:
            # برخورد!
            self.stuck = True
            self.stuck_x = self.x
            self.stuck_y = self.y
            score, stype, label = get_dart_score(self.x, self.y)
            self.score = score
            self.score_type = stype
            self.score_label = label
            play_sound('hit_board')

            # افکت‌های خاص
            if stype == 'bull':
                play_sound('bullseye')
                for _ in range(30):
                    spawn_particles(self.x, self.y, NEON_RED, 1, 2.0, 1.5, 1.5)
            elif stype == 'outer_bull':
                play_sound('bullseye')
                for _ in range(20):
                    spawn_particles(self.x, self.y, NEON_GREEN, 1, 1.5, 1.2, 1.2)
            elif stype == 'triple':
                play_sound('triple')
                for _ in range(20):
                    spawn_particles(self.x, self.y, NEON_YELLOW, 1, 1.5, 1.2, 1.2)
            elif stype == 'double':
                play_sound('triple')
                for _ in range(15):
                    spawn_particles(self.x, self.y, NEON_ORANGE, 1, 1.5, 1.0, 1.0)
            else:
                for _ in range(10):
                    spawn_particles(self.x, self.y, NEON_CYAN, 1, 1.2, 1.0, 0.8)

        # اگه از صفحه خارج شد
        if self.x < -100 or self.x > WIDTH + 100 or self.y > HEIGHT + 100:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return

        # Trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / len(self.trail) * 0.5
            r = max(1, int(4 * alpha))
            pygame.draw.circle(surface, NEON_CYAN, (int(tx), int(ty)), r)

        # بدنه دارت
        rad = math.radians(self.angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        # نوک
        tip_x = self.x + cos_a * 15
        tip_y = self.y + sin_a * 15

        # هاله
        for hr in range(3, 0, -1):
            glow_size = 30 + hr * 8
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*NEON_YELLOW, 60 - hr * 15),
                               (glow_size // 2, glow_size // 2), glow_size // 2)
            surface.blit(glow, (self.x - glow_size // 2, self.y - glow_size // 2))

        # بدنه اصلی
        pygame.draw.line(surface, NEON_YELLOW,
                         (self.x, self.y), (tip_x, tip_y), 4)
        pygame.draw.line(surface, WHITE,
                         (self.x, self.y), (tip_x, tip_y), 2)
        # دم
        tail_x = self.x - cos_a * 15
        tail_y = self.y - sin_a * 15
        pygame.draw.line(surface, NEON_ORANGE,
                         (self.x, self.y), (tail_x, tail_y), 4)
        # پرها
        perp = rad + math.pi / 2
        for side in [-1, 1]:
            px = tail_x + math.cos(perp) * 5 * side
            py = tail_y + math.sin(perp) * 5 * side
            pygame.draw.line(surface, NEON_PINK, (tail_x, tail_y), (px, py), 3)

        # اگه چسبیده، هاله‌ی قرمز
        if self.stuck:
            pulse = 1 + math.sin(self.anim_time * 5) * 0.3
            for hr in range(2):
                glow_size = int(40 * pulse) + hr * 10
                glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                color = NEON_RED if self.score_type == 'bull' else NEON_YELLOW
                pygame.draw.circle(glow, (*color, 100), (glow_size // 2, glow_size // 2), glow_size // 2, 2)
                surface.blit(glow, (self.x - glow_size // 2, self.y - glow_size // 2))


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
def build_bg():
    layers = []
    # گرادیان
    surf1 = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(HEIGHT):
        t = y / HEIGHT
        c = (int(20 + 30 * t), int(10 + 20 * t), int(40 + 30 * t))
        pygame.draw.line(surf1, c, (0, y), (WIDTH, y))
    # ستاره‌ها
    for _ in range(100):
        x, y = random.randint(0, WIDTH), random.randint(0, HEIGHT // 2)
        b = random.randint(80, 180)
        pygame.draw.circle(surf1, (b, b, min(255, b + 40)), (x, y), random.choice([1, 1, 2]))
    layers.append(surf1)

    # نور نئونی پس‌زمینه
    surf2 = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for _ in range(3):
        nx = random.randint(100, WIDTH - 100)
        ny = random.randint(100, HEIGHT - 100)
        for hr in range(5, 0, -1):
            glow_size = 300 + hr * 30
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            color = random.choice([NEON_PURPLE, NEON_PINK, NEON_BLUE])
            pygame.draw.circle(glow, (*color, 20), (glow_size // 2, glow_size // 2), glow_size // 2)
            surf2.blit(glow, (nx - glow_size // 2, ny - glow_size // 2))

    return surf1, surf2


# ============================================================
#                    Board Drawing
# ============================================================
def draw_dartboard(surface):
    # هاله‌ی بیرونی
    for hr in range(5, 0, -1):
        glow_size = BOARD_RADIUS * 2 + hr * 15
        glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*NEON_PURPLE, 40 - hr * 6),
                           (glow_size // 2, glow_size // 2), glow_size // 2)
        surface.blit(glow, (BOARD_X - glow_size // 2, BOARD_Y - glow_size // 2))

    # حلقه‌های رنگی
    # Single Outer (کل تخته)
    pygame.draw.circle(surface, (15, 10, 30), (BOARD_X, BOARD_Y), BOARD_RADIUS)

    # رسم سکتورها
    for i, number in enumerate(NUMBER_ORDER):
        # هر سکتور 18 درجه
        start_angle = i * 18 - 9
        end_angle = start_angle + 18

        # چک سیاه/سفید (مثل دارت واقعی)
        if i % 2 == 0:
            color = (10, 5, 20)
        else:
            color = (30, 20, 50)

        # رسم سکتور Single Outer (بین single_inner و triple)
        pygame.draw.circle(surface, color, (BOARD_X, BOARD_Y), BOARD_RADIUS)
        # بهتره با polygon بریم
        points = [(BOARD_X, BOARD_Y)]
        for a in [start_angle, end_angle]:
            rad = math.radians(a - 90)
            px = BOARD_X + math.cos(rad) * BOARD_RADIUS
            py = BOARD_Y + math.sin(rad) * BOARD_RADIUS
            points.append((px, py))
        pygame.draw.polygon(surface, color, points)

    # حلقه‌های رنگی
    # Double (بیرونی‌ترین نوار)
    for i, number in enumerate(NUMBER_ORDER):
        start_angle = i * 18 - 9
        end_angle = start_angle + 18
        color = NEON_GREEN if i % 2 == 0 else NEON_RED
        # نوار double: R_DOUBLE_INNER * R تا R_DOUBLE_OUTER * R
        points = []
        for a in [start_angle, end_angle]:
            rad = math.radians(a - 90)
            px1 = BOARD_X + math.cos(rad) * BOARD_RADIUS * R_DOUBLE_INNER
            py1 = BOARD_Y + math.sin(rad) * BOARD_RADIUS * R_DOUBLE_INNER
            points.append((px1, py1))
        for a in [end_angle, start_angle]:
            rad = math.radians(a - 90)
            px2 = BOARD_X + math.cos(rad) * BOARD_RADIUS * R_DOUBLE_OUTER
            py2 = BOARD_Y + math.sin(rad) * BOARD_RADIUS * R_DOUBLE_OUTER
            points.append((px2, py2))
        # بهتره با arc بریم
        # بذار به سادگی با دایره‌ها رسم کنیم
        pass

    # رسم حلقه‌های دایره‌ای (ساده‌تر)
    # Double ring
    pygame.draw.circle(surface, NEON_GREEN, (BOARD_X, BOARD_Y), BOARD_RADIUS, 3)
    pygame.draw.circle(surface, NEON_RED, (BOARD_X, BOARD_Y), int(BOARD_RADIUS * R_DOUBLE_INNER), 25)

    # Triple ring
    pygame.draw.circle(surface, NEON_YELLOW, (BOARD_X, BOARD_Y), int(BOARD_RADIUS * R_TRIPLE_OUTER), 3)
    pygame.draw.circle(surface, NEON_ORANGE, (BOARD_X, BOARD_Y), int(BOARD_RADIUS * R_TRIPLE_OUTER) - 25, 3)

    # Single inner ring
    pygame.draw.circle(surface, NEON_CYAN, (BOARD_X, BOARD_Y), int(BOARD_RADIUS * R_SINGLE_INNER), 2)

    # Bull rings
    pygame.draw.circle(surface, NEON_GREEN, (BOARD_X, BOARD_Y), int(BOARD_RADIUS * 0.08), 2)
    pygame.draw.circle(surface, NEON_RED, (BOARD_X, BOARD_Y), int(BOARD_RADIUS * 0.045), 2)
    pygame.draw.circle(surface, NEON_RED, (BOARD_X, BOARD_Y), int(BOARD_RADIUS * 0.045))

    # خطوط جداکننده سکتورها
    for i in range(20):
        angle = math.radians(i * 18 - 90)
        x1 = BOARD_X + math.cos(angle) * BOARD_RADIUS * 0.08
        y1 = BOARD_Y + math.sin(angle) * BOARD_RADIUS * 0.08
        x2 = BOARD_X + math.cos(angle) * BOARD_RADIUS
        y2 = BOARD_Y + math.sin(angle) * BOARD_RADIUS
        pygame.draw.line(surface, (60, 60, 90), (x1, y1), (x2, y2), 1)

    # اعداد
    for i, number in enumerate(NUMBER_ORDER):
        angle = math.radians(i * 18 - 90)
        num_x = BOARD_X + math.cos(angle) * BOARD_RADIUS * 0.92
        num_y = BOARD_Y + math.sin(angle) * BOARD_RADIUS * 0.92
        draw_text(surface, str(number), 18, num_x, num_y - 10, WHITE, center=True, bold=True, glow=True)

    # نشانگر بالا
    pygame.draw.circle(surface, NEON_YELLOW, (int(BOARD_X), int(BOARD_Y - BOARD_RADIUS)), 5)


# ============================================================
#                    Menu
# ============================================================
def show_menu():
    menu_time = 0
    btn_301 = Button(WIDTH // 2, HEIGHT // 2 - 60, 320, 50, "301", NEON_CYAN, NEON_GREEN, 26)
    btn_501 = Button(WIDTH // 2, HEIGHT // 2 - 5, 320, 50, "501", NEON_YELLOW, NEON_ORANGE, 26)
    btn_atc = Button(WIDTH // 2, HEIGHT // 2 + 50, 320, 50, "AROUND THE CLOCK", NEON_PURPLE, NEON_PINK, 22)
    btn_practice = Button(WIDTH // 2, HEIGHT // 2 + 105, 320, 50, "PRACTICE", NEON_GREEN, NEON_CYAN, 22)
    btn_history = Button(WIDTH // 2 - 110, HEIGHT // 2 + 170, 150, 45, "HISTORY", NEON_BLUE, NEON_CYAN, 18)
    btn_settings = Button(WIDTH // 2 + 110, HEIGHT // 2 + 170, 150, 45, "SETTINGS", NEON_PURPLE, NEON_PINK, 18)
    btn_achievements = Button(WIDTH // 2 - 110, HEIGHT // 2 + 225, 150, 45, "AWARDS", NEON_YELLOW, NEON_ORANGE, 18)
    btn_quit = Button(WIDTH // 2 + 110, HEIGHT // 2 + 225, 150, 45, "QUIT", NEON_RED, NEON_ORANGE, 18)
    btn_fullscreen = Button(WIDTH - 40, 30, 40, 40, "[]", NEON_PURPLE, NEON_CYAN, 20)

    bg1, bg2 = build_bg()

    while True:
        game_surface.fill(DARK_BG)
        t = pygame.time.get_ticks() / 1000
        menu_time += 1
        mouse_pos = get_game_mouse_pos()

        # پس‌زمینه
        game_surface.blit(bg1, (0, 0))
        game_surface.blit(bg2, (0, 0))

        # تخته دارت در پس‌زمینه (نیمه شفاف)
        board_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        draw_dartboard(board_surf)
        board_surf.set_alpha(100)
        game_surface.blit(board_surf, (0, 0))

        # عنوان
        title_y = 80 + math.sin(t * 2) * 5
        draw_text(game_surface, "NEON", 64, WIDTH // 2 - 90, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "DARTS", 64, WIDTH // 2 + 90, title_y, NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, "AIM  /  THROW  /  SCORE", 18, WIDTH // 2, title_y + 55,
                  (200, 200, 220), center=True)

        # آمار
        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 20, WIDTH // 2, title_y + 90,
                      NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, f"THROWS: {total_throws[0]}   BULLS: {total_bulls[0]}   180s: {total_180s[0]}",
                  12, WIDTH // 2, title_y + 115, NEON_PINK, center=True)

        for b in [btn_301, btn_501, btn_atc, btn_practice, btn_history, btn_settings,
                  btn_achievements, btn_quit, btn_fullscreen]:
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
            if btn_301.is_clicked(event):
                return '301'
            if btn_501.is_clicked(event):
                return '501'
            if btn_atc.is_clicked(event):
                return 'atc'
            if btn_practice.is_clicked(event):
                return 'practice'
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
                    return '301'
                if event.key == pygame.K_2:
                    return '501'
                if event.key == pygame.K_3:
                    return 'atc'
                if event.key == pygame.K_4:
                    return 'practice'
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
    btn_wind = Button(WIDTH // 2, 450, 280, 50,
                      f"WIND: {'ON' if settings['wind_enabled'] else 'OFF'}",
                      NEON_GREEN if settings['wind_enabled'] else (100, 100, 100), NEON_CYAN, 22)
    btn_shake = Button(WIDTH // 2, 515, 280, 50,
                       f"SHAKE: {'ON' if settings['screen_shake'] else 'OFF'}",
                       NEON_GREEN if settings['screen_shake'] else (100, 100, 100), NEON_CYAN, 22)
    btn_reset = Button(WIDTH // 2 - 130, 590, 220, 45, "RESET SAVE", NEON_RED, NEON_ORANGE, 18)
    btn_back = Button(WIDTH // 2 + 130, 590, 220, 45, "BACK", NEON_CYAN, NEON_GREEN, 20)

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
        draw_text(game_surface, diff_label, 20, WIDTH // 2, 390, diff_color, center=True)

        btn_wind.update(mouse_pos)
        btn_wind.text = f"WIND: {'ON' if settings['wind_enabled'] else 'OFF'}"
        btn_wind.color = NEON_GREEN if settings['wind_enabled'] else (100, 100, 100)
        btn_wind.draw(game_surface)

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
            if btn_wind.is_clicked(event):
                settings['wind_enabled'] = not settings['wind_enabled']
                save_async()
            if btn_shake.is_clicked(event):
                settings['screen_shake'] = not settings['screen_shake']
                save_async()
            if btn_reset.is_clicked(event):
                settings['sfx_volume'] = 0.7
                settings['music_volume'] = 0.5
                settings['difficulty'] = 1.0
                settings['screen_shake'] = True
                settings['wind_enabled'] = True
                for k in achievements:
                    achievements[k]['unlocked'] = False
                highscore[0] = 0
                game_history.clear()
                total_throws[0] = 0
                total_bulls[0] = 0
                total_180s[0] = 0
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
                won = entry.get('won', False)
                rank_color = NEON_GREEN if won else NEON_RED
                rank = "WIN" if won else "LOSS"
                pygame.draw.rect(game_surface, (15, 8, 30), (ix, iy, iw, item_h - 8), border_radius=6)
                pygame.draw.rect(game_surface, rank_color, (ix, iy, iw, item_h - 8), 2, border_radius=6)
                draw_text(game_surface, rank, 18, ix + 35, iy + (item_h - 8) // 2, rank_color, center=True, glow=True)
                draw_text(game_surface, f"MODE: {entry.get('mode', '?')}", 16, ix + 100, iy + 10, WHITE)
                draw_text(game_surface, f"Darts: {entry.get('darts_used', 0)}   Score: {entry.get('score', 0)}",
                          12, ix + 100, iy + 30, (180, 180, 200))
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
def play_game(mode='501'):
    # تنظیمات بر اساس حالت
    if mode == '301':
        starting_score = 301
    elif mode == '501':
        starting_score = 501
    elif mode == 'atc':
        starting_score = 0  # 1-20
    elif mode == 'practice':
        starting_score = 0
    else:
        starting_score = 501

    # وضعیت بازی
    player_score = starting_score
    ai_score = starting_score
    player_darts = 0
    ai_darts = 0
    turn_darts_left = 3
    current_player = 'player'  # 'player' یا 'ai'

    # برای ATC
    atc_player_target = 1
    atc_ai_target = 1

    # برای Practice
    practice_score = 0

    # باد
    wind = 0
    wind_change_timer = 0

    # دارت‌ها
    player_darts_thrown = []
    ai_darts_thrown = []

    # پرتاب
    is_aiming = False
    aim_start = (0, 0)
    aim_current = (0, 0)

    # وضعیت
    game_over = False
    paused = False
    winner = None
    win_condition = ''

    # آمار
    turn_score = 0
    max_turn_score = 0
    bullseyes = 0
    t20_count = 0
    perfect_leg = True
    total_frames = 0

    # افکت‌ها
    screen_shake = 0
    flash = 0
    new_achs = []
    notifications = []
    go_anim = 0
    game_saved = False
    turn_banner = 0

    btn_resume = Button(WIDTH // 2, HEIGHT // 2 + 20, 300, 60, "RESUME", NEON_GREEN, NEON_CYAN, 28)
    btn_pause_menu = Button(WIDTH // 2, HEIGHT // 2 + 100, 300, 55, "MAIN MENU", NEON_RED, NEON_ORANGE, 24)
    btn_rematch = Button(WIDTH // 2, HEIGHT // 2 + 70, 300, 60, "REMATCH", NEON_CYAN, NEON_GREEN, 28)
    btn_menu = Button(WIDTH // 2, HEIGHT // 2 + 145, 300, 55, "MAIN MENU", NEON_YELLOW, NEON_ORANGE, 24)

    active_particles.clear()
    for p in particle_pool:
        p.active = False

    bg1, bg2 = build_bg()

    start_music()

    def try_unlock(key):
        if unlock_achievement(key):
            new_achs.append(achievements[key]['name'])
            notifications.append({'ach': achievements[key], 'timer': 180})
            return True
        return False

    def save_current():
        add_game_to_history(practice_score if mode == 'practice' else player_score,
                            mode, player_darts, winner == 'player', new_achs)

    def reset_turn():
        nonlocal turn_darts_left, turn_score
        turn_darts_left = 3
        turn_score = 0

    def switch_player():
        nonlocal current_player, turn_darts_left, turn_score, turn_banner
        current_player = 'ai' if current_player == 'player' else 'player'
        turn_darts_left = 3
        turn_score = 0
        turn_banner = 60
        play_sound('turn_end')

    def ai_throw():
        """شبیه‌سازی پرتاب AI"""
        nonlocal ai_darts, ai_score, turn_darts_left, turn_score

        # هدف‌گیری بر اساس سختی
        difficulty = settings['difficulty']

        # شانس خطا
        error = (1 - difficulty) * 50 + 10

        # هدف معمولاً Triple 20 یا چک‌اوت
        if ai_score <= 40 and ai_score % 2 == 0:
            # چک‌اوت
            target_score = ai_score
            # هدف‌گیری Double
            target_double = target_score // 2
            if target_double in NUMBER_ORDER:
                target_index = NUMBER_ORDER.index(target_double)
                target_angle = target_index * 18 - 90
                target_radius = BOARD_RADIUS * 0.925
            else:
                target_angle = random.uniform(-90, 90)
                target_radius = BOARD_RADIUS * 0.5
        else:
            # Triple 20
            target_index = NUMBER_ORDER.index(20)
            target_angle = target_index * 18 - 90
            target_radius = BOARD_RADIUS * 0.46

        # اضافه کردن خطا
        final_angle = target_angle + random.uniform(-error, error) * 0.5
        final_radius = target_radius + random.uniform(-error, error)

        # محاسبه مختصات
        rad = math.radians(final_angle)
        x = BOARD_X + math.cos(rad) * final_radius
        y = BOARD_Y + math.sin(rad) * final_radius

        # امتیاز
        score, stype, label = get_dart_score(x, y)

        # ذخیره دارت
        dart = Dart(BOARD_X, BOARD_Y, 0, 0)
        dart.x = x
        dart.y = y
        dart.stuck = True
        dart.stuck_x = x
        dart.stuck_y = y
        dart.score = score
        dart.score_type = stype
        dart.score_label = label
        ai_darts_thrown.append(dart)

        ai_darts += 1
        total_throws[0] += 1

        # ذرات
        for _ in range(15):
            spawn_particles(x, y, NEON_RED if stype == 'bull' else NEON_ORANGE, 1, 1.5, 1.0, 1.0)

        play_sound('hit_board')

        if stype == 'bull':
            bullseyes += 1

        # بروزرسانی امتیاز AI
        if mode == '301' or mode == '501':
            ai_score -= score
            if ai_score == 0 and stype == 'double':
                nonlocal winner, game_over
                winner = 'ai'
                game_over = True
            elif ai_score < 0 or ai_score == 1:
                ai_score += score  # برگشت
        elif mode == 'atc':
            if score == atc_ai_target:
                atc_ai_target += 1
                if atc_ai_target > 20:
                    winner = 'ai'
                    game_over = True
        elif mode == 'practice':
            pass

        turn_darts_left -= 1

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
                if btn_rematch.is_clicked(event):
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

            # پرتاب با ماوس
            if not game_over and not paused and current_player == 'player' and turn_darts_left > 0:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not is_aiming:
                        is_aiming = True
                        aim_start = mouse_pos
                        aim_current = mouse_pos

                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if is_aiming:
                        is_aiming = False
                        # محاسبه بردار
                        dx = aim_start[0] - aim_current[0]
                        dy = aim_start[1] - aim_current[1]
                        power = math.hypot(dx, dy) / 5
                        power = min(power, 30)
                        if power < 3:
                            continue
                        angle = math.atan2(dy, dx)
                        vx = math.cos(angle) * power
                        vy = math.sin(angle) * power

                        # دارت از پایین صفحه
                        dart = Dart(WIDTH // 2 - 200, HEIGHT - 100, vx, vy)
                        player_darts_thrown.append(dart)

                        play_sound('throw')
                        total_throws[0] += 1
                        player_darts += 1

                if event.type == pygame.MOUSEMOTION and is_aiming:
                    aim_current = mouse_pos

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

            # باد
            if settings['wind_enabled']:
                wind_change_timer += 1
                if wind_change_timer > 180:
                    wind_change_timer = 0
                    wind = random.uniform(-3, 3)
            else:
                wind = 0

            # آپدیت دارت‌های بازیکن
            for d in player_darts_thrown[:]:
                d.update(wind if settings['wind_enabled'] else 0)
                if not d.alive:
                    player_darts_thrown.remove(d)
                    continue
                if d.stuck and d.anim_time == 1:
                    # اولین فریم که چسبید
                    score = d.score
                    turn_score += score

                    if score == 50:
                        bullseyes += 1
                        total_bulls[0] += 1
                        try_unlock('first_bull')
                        if bullseyes >= 1: try_unlock('first_bull')
                        if bullseyes >= 10: try_unlock('bull_10')
                        if settings['screen_shake']:
                            screen_shake = 15
                        flash = 150

                    if d.score_type == 'triple' and score == 60:
                        t20_count += 1
                        try_unlock('triple_20')
                        if t20_count >= 5: try_unlock('t20_5')

                    # برای 301/501
                    if mode in ['301', '501']:
                        player_score -= score
                        # چک برد
                        if player_score == 0 and d.score_type == 'double':
                            winner = 'player'
                            game_over = True
                            win_condition = 'Checkout!'
                            try_unlock('checkout')
                            if player_darts <= 9:
                                try_unlock('nine_dart')
                            if mode == '301': try_unlock('win_301')
                            if mode == '501': try_unlock('win_501')
                            if perfect_leg: try_unlock('perfect_leg')
                            if settings['difficulty'] >= 1.2:
                                try_unlock('beat_hard')
                            play_sound('win')
                            for _ in range(50):
                                spawn_particles(BOARD_X, BOARD_Y, NEON_YELLOW, 1, 2.5, 2.0, 2.0)
                        elif player_score < 0 or player_score == 1:
                            player_score += score  # برگشت
                    elif mode == 'atc':
                        if score == atc_player_target:
                            atc_player_target += 1
                            if atc_player_target > 20:
                                winner = 'player'
                                game_over = True
                                play_sound('win')
                    elif mode == 'practice':
                        practice_score += score

                    if score == 0:
                        perfect_leg = False

                    # چک 180
                    if turn_score >= 180:
                        try_unlock('score_180')
                        total_180s[0] += 1
                        play_sound('180')
                        if settings['screen_shake']:
                            screen_shake = 30
                        flash = 200
                    elif turn_score >= 100:
                        try_unlock('score_100')

            # آپدیت دارت‌های AI
            for d in ai_darts_thrown[:]:
                d.update(wind if settings['wind_enabled'] else 0)
                if not d.alive:
                    ai_darts_thrown.remove(d)
                    continue

            # حرکات AI
            if current_player == 'ai' and not game_over:
                # با تاخیر پرتاب کن
                if total_frames % 60 == 0:
                    ai_throw()
                    if turn_darts_left <= 0:
                        switch_player()

            # پایان نوبت بازیکن
            if current_player == 'player' and turn_darts_left <= 0 and not game_over:
                if len(player_darts_thrown) == 0 or all(d.stuck for d in player_darts_thrown):
                    switch_player()

            # آپدیت ذرات
            for p in active_particles[:]:
                p.update()
                if not p.active:
                    active_particles.remove(p)

            if screen_shake > 0:
                screen_shake -= 1
            if flash > 0:
                flash -= 8
            if turn_banner > 0:
                turn_banner -= 1

        # ============================================================
        #                    رسم
        # ============================================================
        game_surface.fill(DARK_BG)
        offset_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        offset_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0

        play_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # پس‌زمینه
        play_layer.blit(bg1, (0, 0))
        play_layer.blit(bg2, (0, 0))

        # تخته
        draw_dartboard(play_layer)

        # دارت‌های چسبیده
        for d in player_darts_thrown:
            d.draw(play_layer)
        for d in ai_darts_thrown:
            d.draw(play_layer)

        # ذرات
        for p in active_particles:
            p.draw(play_layer)

        # نشانه‌گیری
        if is_aiming:
            dx = aim_start[0] - aim_current[0]
            dy = aim_start[1] - aim_current[1]
            power = min(math.hypot(dx, dy) / 5, 30)

            # خط نشانه‌گیری
            pygame.draw.line(play_layer, NEON_YELLOW, aim_start, aim_current, 2)

            # نوار قدرت
            power_ratio = power / 30
            bar_w = 200
            bar_x = WIDTH // 2 - 200 - bar_w // 2
            bar_y = HEIGHT - 150
            pygame.draw.rect(play_layer, (40, 40, 40), (bar_x, bar_y, bar_w, 15))
            color = NEON_GREEN if power_ratio < 0.5 else NEON_YELLOW if power_ratio < 0.8 else NEON_RED
            pygame.draw.rect(play_layer, color, (bar_x, bar_y, bar_w * power_ratio, 15))
            pygame.draw.rect(play_layer, WHITE, (bar_x, bar_y, bar_w, 15), 2)
            draw_text(play_layer, "POWER", 12, bar_x + bar_w // 2, bar_y - 15, WHITE, center=True)

        # ذرات پرتاب
        if flash > 0:
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 200, 100, flash))
            play_layer.blit(fs, (0, 0))

        game_surface.blit(play_layer, (offset_x, offset_y))

        # ============================================================
        #                    HUD
        # ============================================================
        # نوار بالا
        hud_panel = pygame.Surface((WIDTH, 90), pygame.SRCALPHA)
        for y in range(90):
            alpha = int(180 * (1 - y / 90))
            pygame.draw.line(hud_panel, (5, 10, 25, alpha), (0, y), (WIDTH, y))
        game_surface.blit(hud_panel, (0, 0))
        pygame.draw.line(game_surface, NEON_CYAN, (0, 90), (WIDTH, 90), 1)

        # عنوان
        draw_text(game_surface, f"NEON DARTS - {mode.upper()}", 20, 25, 15, NEON_CYAN, glow=True)

        # امتیاز بازیکن
        if mode in ['301', '501']:
            draw_text(game_surface, "PLAYER", 16, WIDTH // 2 - 200, 15, NEON_GREEN)
            draw_text(game_surface, f"{player_score}", 32, WIDTH // 2 - 200, 38, WHITE, glow=True)
            draw_text(game_surface, "AI", 16, WIDTH // 2 + 200, 15, NEON_RED)
            draw_text(game_surface, f"{ai_score}", 32, WIDTH // 2 + 200, 38, WHITE, glow=True)
        elif mode == 'atc':
            draw_text(game_surface, "PLAYER TARGET", 14, WIDTH // 2 - 200, 15, NEON_GREEN)
            draw_text(game_surface, f"{atc_player_target}", 32, WIDTH // 2 - 200, 38, WHITE, glow=True)
            draw_text(game_surface, "AI TARGET", 14, WIDTH // 2 + 200, 15, NEON_RED)
            draw_text(game_surface, f"{atc_ai_target}", 32, WIDTH // 2 + 200, 38, WHITE, glow=True)
        elif mode == 'practice':
            draw_text(game_surface, "SCORE", 16, WIDTH // 2, 15, NEON_GREEN, center=True)
            draw_text(game_surface, f"{practice_score}", 36, WIDTH // 2, 42, WHITE, center=True, glow=True)

        # نوبت
        turn_color = NEON_GREEN if current_player == 'player' else NEON_RED
        draw_text(game_surface, f"{current_player.upper()}'S TURN", 20, WIDTH // 2, 70,
                  turn_color, center=True, glow=True)

        # دارت‌های باقی‌مانده
        for i in range(3):
            x = 25 + i * 30
            y = 70
            if i < turn_darts_left:
                pygame.draw.circle(game_surface, NEON_YELLOW, (x, y), 8)
                pygame.draw.circle(game_surface, WHITE, (x, y), 8, 2)
            else:
                pygame.draw.circle(game_surface, (60, 60, 60), (x, y), 8, 2)

        # امتیاز این نوبت
        draw_text(game_surface, f"TURN: {turn_score}", 18, WIDTH - 25, 15, NEON_YELLOW)

        # باد
        if settings['wind_enabled'] and abs(wind) > 0.5:
            wind_text = "WIND: " + ("→" if wind > 0 else "←") * int(abs(wind))
            wind_color = NEON_CYAN if abs(wind) < 2 else NEON_YELLOW if abs(wind) < 3 else NEON_RED
            draw_text(game_surface, wind_text, 14, WIDTH - 25, 40, wind_color)
        else:
            draw_text(game_surface, "WIND: none", 14, WIDTH - 25, 40, (100, 100, 100))

        # راهنما
        if total_frames < 300:
            draw_text(game_surface, "CLICK + DRAG to aim, RELEASE to throw!",
                      18, WIDTH // 2, HEIGHT - 40, NEON_CYAN, center=True, glow=True)

        # Turn banner
        if turn_banner > 0:
            pulse = 1 + math.sin(t * 15) * 0.1
            turn_text = f"PLAYER TURN" if current_player == 'player' else "AI TURN"
            color = NEON_GREEN if current_player == 'player' else NEON_RED
            draw_text(game_surface, turn_text, int(60 * pulse), WIDTH // 2, HEIGHT // 2 - 100,
                      color, center=True, glow=True)

        # Notifications
        for i, notif in enumerate(notifications):
            ny = 100 + i * 55
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
            win_color = NEON_GREEN if winner == 'player' else NEON_RED
            pygame.draw.rect(game_surface, win_color, (box_x, box_y, box_w, box_h), 3)
            pygame.draw.rect(game_surface, NEON_CYAN, (box_x + 5, box_y + 5, box_w - 10, box_h - 10), 1)
            result_text = "YOU WIN!" if winner == 'player' else "YOU LOSE!"
            draw_text(game_surface, result_text, 60, WIDTH // 2, box_y + 55,
                      win_color, center=True, glow=True)
            draw_text(game_surface, f"DARTS USED: {player_darts}", 24,
                      WIDTH // 2, box_y + 130, WHITE, center=True)
            draw_text(game_surface, f"BULLSEYES: {bullseyes}   T20: {t20_count}",
                      16, WIDTH // 2, box_y + 170, NEON_CYAN, center=True)
            if go_anim > 15:
                btn_rematch.update(mouse_pos)
                btn_menu.update(mouse_pos)
                btn_rematch.draw(game_surface)
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
        elif result in ['301', '501', 'atc', 'practice']:
            play_game(result)
    pygame.quit()


if __name__ == "__main__":
    main()