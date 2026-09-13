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
pygame.display.set_caption("NEON ARCHERY")
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
GRAVITY = 0.35
GROUND_Y = HEIGHT - 80
BOW_X = 150
BOW_Y = GROUND_Y - 60

# --- ذخیره ---
SAVE_FILE = "neon_archery_save.json"
settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'screen_shake': True,
    'show_trajectory': True,
    'wind_enabled': True,
}
achievements = {
    'first_shot': {'name': 'FIRST SHOT', 'desc': 'Fire your first arrow', 'unlocked': False, 'icon': '>'},
    'first_hit': {'name': 'FIRST HIT', 'desc': 'Hit the target', 'unlocked': False, 'icon': '*'},
    'hit_10': {'name': 'ROOKIE', 'desc': 'Hit 10 targets', 'unlocked': False, 'icon': 'H10'},
    'hit_50': {'name': 'VETERAN', 'desc': 'Hit 50 targets', 'unlocked': False, 'icon': 'H50'},
    'hit_200': {'name': 'LEGEND', 'desc': 'Hit 200 targets', 'unlocked': False, 'icon': 'H200'},
    'bullseye_1': {'name': 'BULLSEYE!', 'desc': 'Hit the bullseye', 'unlocked': False, 'icon': 'B1'},
    'bullseye_10': {'name': 'SHARPSHOOTER', 'desc': '10 bullseyes', 'unlocked': False, 'icon': 'B10'},
    'bullseye_50': {'name': 'MASTER', 'desc': '50 bullseyes', 'unlocked': False, 'icon': 'B50'},
    'combo_5': {'name': 'COMBO KING', 'desc': '5x combo', 'unlocked': False, 'icon': 'C5'},
    'combo_10': {'name': 'COMBO GOD', 'desc': '10x combo', 'unlocked': False, 'icon': 'C10'},
    'perfect_round': {'name': 'PERFECT ROUND', 'desc': 'Hit all in a round', 'unlocked': False, 'icon': 'PR'},
    'score_1000': {'name': 'SCORER', 'desc': 'Score 1000 points', 'unlocked': False, 'icon': '$1K'},
    'score_5000': {'name': 'ACE', 'desc': 'Score 5000 points', 'unlocked': False, 'icon': '$5K'},
    'campaign_complete': {'name': 'CHAMPION', 'desc': 'Complete campaign', 'unlocked': False, 'icon': 'CC'},
    'long_shot': {'name': 'LONG SHOT', 'desc': 'Hit at max distance', 'unlocked': False, 'icon': 'LS'},
}
highscore = [0]
game_history = []
total_hits = [0]
total_bullseyes = [0]
total_shots = [0]
campaign_progress = [0]


def load_save():
    global settings, achievements, highscore, game_history, total_hits, total_bullseyes, total_shots, campaign_progress
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
            settings.update(data.get('settings', {}))
            for k, v in data.get('achievements', {}).items():
                if k in achievements:
                    achievements[k]['unlocked'] = v
            highscore[0] = data.get('highscore', 0)
            game_history = data.get('game_history', [])
            total_hits[0] = data.get('total_hits', 0)
            total_bullseyes[0] = data.get('total_bullseyes', 0)
            total_shots[0] = data.get('total_shots', 0)
            campaign_progress[0] = data.get('campaign_progress', 0)
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
                'total_hits': total_hits[0],
                'total_bullseyes': total_bullseyes[0],
                'total_shots': total_shots[0],
                'campaign_progress': campaign_progress[0],
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


def add_game_to_history(score, hits, shots, mode, new_achs):
    entry = {
        'score': score,
        'hits': hits,
        'shots': shots,
        'accuracy': (hits / max(1, shots)) * 100,
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
    sounds['draw'] = make_sound(200, 400, 0.3, 0.12, 'saw')
    sounds['release'] = make_sound(600, 1200, 0.15, 0.20, 'saw')
    sounds['hit_target'] = make_sound(800, 1200, 0.15, 0.22, 'square')
    sounds['bullseye'] = make_sound(1000, 2500, 0.5, 0.30, 'sine')
    sounds['miss'] = make_sound(300, 150, 0.2, 0.15, 'noise')
    sounds['combo'] = make_sound(1200, 1800, 0.15, 0.18, 'sine')
    sounds['levelup'] = make_sound(500, 1800, 0.6, 0.25, 'sine')
    sounds['gameover'] = make_sound(500, 60, 1.5, 0.30, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['wind'] = make_sound(300, 200, 0.5, 0.10, 'noise')

    bass = [73.4, 73.4, 82.4, 82.4, 65.4, 65.4, 73.4, 73.4]
    lead = [523, 659, 784, 659, 523, 494, 440, 494]
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


# --- کلاس کماندار ---
class Archer:
    def __init__(self):
        self.x = BOW_X
        self.y = BOW_Y
        self.angle = 45
        self.power = 0
        self.is_drawing = False
        self.wind = 0
        self.wind_change_timer = 0
        self.anim_time = 0

    def update(self, mouse_pos, mouse_pressed):
        # باد
        if settings['wind_enabled']:
            self.wind_change_timer += 1
            if self.wind_change_timer > 200:
                self.wind_change_timer = 0
                self.wind = random.uniform(-3, 3)
        else:
            self.wind = 0

        mx, my = mouse_pos
        dx = mx - self.x
        dy = my - self.y
        self.angle = math.degrees(math.atan2(dy, dx))
        self.angle = max(-80, min(80, self.angle))

        if mouse_pressed:
            if not self.is_drawing:
                self.is_drawing = True
                play_sound('draw')
            self.power = min(100, self.power + 3)
        else:
            if self.is_drawing:
                self.is_drawing = False
                power_used = self.power
                self.power = 0
                return power_used
        self.anim_time += 1
        return None

    def draw(self, surface):
        # پایه
        pygame.draw.line(surface, NEON_GREEN, (self.x - 20, GROUND_Y),
                         (self.x + 20, GROUND_Y), 4)

        # بدن
        body_rect = pygame.Rect(int(self.x - 12), int(self.y - 40), 24, 50)
        pygame.draw.rect(surface, (10, 40, 20), body_rect, border_radius=5)
        pygame.draw.rect(surface, NEON_GREEN, body_rect, 2, border_radius=5)

        # سر
        head_rect = pygame.Rect(int(self.x - 10), int(self.y - 65), 20, 22)
        pygame.draw.rect(surface, (10, 40, 20), head_rect, border_radius=5)
        pygame.draw.rect(surface, NEON_GREEN, head_rect, 2, border_radius=5)

        # چشم
        pygame.draw.circle(surface, NEON_YELLOW, (int(self.x + 4), int(self.y - 54)), 3)

        # بازو + کمان
        rad = math.radians(self.angle)
        arm_x = self.x + math.cos(rad) * 30
        arm_y = self.y + math.sin(rad) * 30

        pygame.draw.line(surface, NEON_GREEN, (self.x, self.y - 10), (arm_x, arm_y), 5)

        # کمان
        bow_r = 35
        perp = rad + math.pi / 2
        p1x = arm_x + math.cos(perp) * bow_r
        p1y = arm_y + math.sin(perp) * bow_r
        p2x = arm_x - math.cos(perp) * bow_r
        p2y = arm_y - math.sin(perp) * bow_r

        # هاله کمان
        for hr in range(3, 0, -1):
            pygame.draw.line(surface, (*NEON_ORANGE, 100 - hr * 25),
                             (p1x, p1y), (arm_x, arm_y), 4 + hr)
            pygame.draw.line(surface, (*NEON_ORANGE, 100 - hr * 25),
                             (arm_x, arm_y), (p2x, p2y), 4 + hr)

        pygame.draw.line(surface, NEON_ORANGE, (p1x, p1y), (arm_x, arm_y), 4)
        pygame.draw.line(surface, NEON_ORANGE, (arm_x, arm_y), (p2x, p2y), 4)
        pygame.draw.line(surface, WHITE, (p1x, p1y), (arm_x, arm_y), 1)
        pygame.draw.line(surface, WHITE, (arm_x, arm_y), (p2x, p2y), 1)

        # رشته کمان
        if self.is_drawing:
            pull = self.power * 0.3
            string_x = arm_x - math.cos(rad) * pull
            string_y = arm_y - math.sin(rad) * pull
            pygame.draw.line(surface, WHITE, (p1x, p1y), (string_x, string_y), 2)
            pygame.draw.line(surface, WHITE, (string_x, string_y), (p2x, p2y), 2)
        else:
            pygame.draw.line(surface, WHITE, (p1x, p1y), (p2x, p2y), 2)

        # نوار قدرت
        if self.is_drawing:
            bar_w = 100
            bar_h = 12
            bar_x = self.x - bar_w // 2
            bar_y = self.y - 100

            pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
            power_ratio = self.power / 100
            if power_ratio < 0.33:
                power_color = NEON_GREEN
            elif power_ratio < 0.66:
                power_color = NEON_YELLOW
            else:
                power_color = NEON_RED
            pygame.draw.rect(surface, power_color,
                             (bar_x, bar_y, bar_w * power_ratio, bar_h), border_radius=6)
            pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=6)
            draw_text(surface, f"POWER: {int(self.power)}%", 14,
                      self.x, bar_y - 20, WHITE, center=True, glow=True)


# --- کلاس تیر ---
class Arrow:
    def __init__(self, x, y, vx, vy, arrow_type='normal'):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.arrow_type = arrow_type
        self.alive = True
        self.stuck = False
        self.stuck_timer = 0
        self.angle = math.degrees(math.atan2(vy, vx))
        self.trail = []
        self.hit_something = False

    def update(self, wind=0):
        if self.stuck:
            self.stuck_timer += 1
            if self.stuck_timer > 180:
                self.alive = False
            return

        self.trail.append((self.x, self.y))
        if len(self.trail) > 15:
            self.trail.pop(0)

        self.vy += GRAVITY
        self.vx += wind * 0.01
        self.x += self.vx
        self.y += self.vy
        self.angle = math.degrees(math.atan2(self.vy, self.vx))

        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.stuck = True
        if self.x < -50 or self.x > WIDTH + 100:
            self.alive = False

    def draw(self, surface):
        # Trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / len(self.trail) * 0.6
            r = max(1, int(4 * alpha))
            pygame.draw.circle(surface, NEON_YELLOW, (int(tx), int(ty)), r)

        rad = math.radians(self.angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        tip_x = self.x + cos_a * 20
        tip_y = self.y + sin_a * 20
        tail_x = self.x - cos_a * 20
        tail_y = self.y - sin_a * 20

        # هاله
        for hr in range(3, 0, -1):
            pygame.draw.line(surface, (*NEON_YELLOW, 60 - hr * 15),
                             (tail_x, tail_y), (tip_x, tip_y), 4 + hr)

        pygame.draw.line(surface, NEON_YELLOW, (tail_x, tail_y), (tip_x, tip_y), 4)
        pygame.draw.line(surface, WHITE, (tail_x, tail_y), (tip_x, tip_y), 2)
        pygame.draw.circle(surface, WHITE, (int(tip_x), int(tip_y)), 3)

        # پرها
        perp = rad + math.pi / 2
        for side in [-1, 1]:
            fx = tail_x + math.cos(perp) * 6 * side
            fy = tail_y + math.sin(perp) * 6 * side
            pygame.draw.line(surface, NEON_PINK, (tail_x, tail_y), (fx, fy), 3)


# --- کلاس هدف ---
class Target:
    def __init__(self, x, y, size, moving=False, move_range=100):
        self.x = x
        self.base_y = y
        self.y = y
        self.size = size
        self.moving = moving
        self.move_range = move_range
        self.move_phase = random.uniform(0, math.pi * 2)
        self.move_speed = 0.02
        self.hit = False
        self.anim = 0

    def update(self):
        if self.moving:
            self.move_phase += self.move_speed
            self.y = self.base_y + math.sin(self.move_phase) * self.move_range
        if self.anim > 0:
            self.anim -= 0.05

    def rect(self):
        return pygame.Rect(int(self.x - self.size), int(self.y - self.size),
                           self.size * 2, self.size * 2)

    def check_hit(self, x, y):
        """چک برخورد و برگرداندن امتیاز (0 اگر miss)"""
        dx = x - self.x
        dy = y - self.y
        dist = math.hypot(dx, dy)

        if dist > self.size:
            return 0

        # محاسبه امتیاز بر اساس فاصله از مرکز
        ratio = dist / self.size
        if ratio < 0.15:
            return 100  # Bullseye
        elif ratio < 0.35:
            return 50
        elif ratio < 0.6:
            return 25
        else:
            return 10

    def draw(self, surface):
        # هاله
        for hr in range(4, 0, -1):
            glow = pygame.Surface((self.size * 2 + hr * 15, self.size * 2 + hr * 15), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*NEON_CYAN, 50 - hr * 10),
                               ((self.size * 2 + hr * 15) // 2, (self.size * 2 + hr * 15) // 2),
                               self.size + hr * 7)
            surface.blit(glow, (self.x - self.size - hr * 7, self.y - self.size - hr * 7))

        # دایره‌های تودرتو
        colors_outer = [NEON_BLUE, WHITE, NEON_BLUE, WHITE, NEON_RED]
        for i in range(5):
            ratio = (5 - i) / 5
            r = int(self.size * ratio)
            color = colors_outer[i]
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), r)
            pygame.draw.circle(surface, WHITE if color != WHITE else NEON_BLUE,
                               (int(self.x), int(self.y)), r, 2)

        # مرکز
        pygame.draw.circle(surface, NEON_RED, (int(self.x), int(self.y)), int(self.size * 0.15))
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), int(self.size * 0.15), 2)

        # اثر ضربه
        if self.anim > 0:
            hit_glow = pygame.Surface((self.size * 2 + 50, self.size * 2 + 50), pygame.SRCALPHA)
            pygame.draw.circle(hit_glow, (*NEON_YELLOW, int(self.anim * 200)),
                               ((self.size * 2 + 50) // 2, (self.size * 2 + 50) // 2),
                               int(self.size + 25 * (1 - self.anim)))
            surface.blit(hit_glow, (self.x - self.size - 25, self.y - self.size - 25))
# --- کلاس بازی ---
class Game:
    def __init__(self, mode='practice'):
        self.mode = mode
        self.archer = Archer()
        self.arrows = []
        self.targets = []
        self.score = 0
        self.display_score = 0
        self.shots = 0
        self.hits = 0
        self.bullseyes = 0
        self.combo = 0
        self.max_combo = 0
        self.combo_timer = 0
        self.arrows_left = 20 if mode == 'practice' else 30
        self.time_left = 60 if mode == 'time' else None
        self.current_level = campaign_progress[0] if mode == 'campaign' else 0
        self.level_target_count = 5
        self.level_hits = 0
        self.game_over = False
        self.won = False
        self.paused = False

        # افکت‌ها
        self.screen_shake = 0
        self.flash = 0
        self.hit_marker_timer = 0
        self.hit_marker_pos = (0, 0)
        self.hit_marker_score = 0

        self.setup_targets()

    def setup_targets(self):
        self.targets.clear()
        if self.mode == 'practice':
            self.targets.append(Target(WIDTH - 200, HEIGHT // 2, 80, moving=False))
        elif self.mode == 'time':
            self.targets.append(Target(WIDTH - 200, HEIGHT // 2, 70, moving=True, move_range=150))
        elif self.mode == 'campaign':
            # مرحله‌ها سخت‌تر میشن
            diff = self.current_level
            num_targets = 1 + diff // 3
            for i in range(num_targets):
                tx = WIDTH - 200 - i * 150
                ty = HEIGHT // 2 + random.randint(-100, 100)
                size = max(40, 90 - diff * 3)
                moving = diff >= 2
                move_range = 100 + diff * 20
                self.targets.append(Target(tx, ty, size, moving, move_range))

    def shoot(self, power):
        if self.arrows_left <= 0 and self.mode != 'time':
            return
        if self.game_over:
            return

        self.shots += 1
        total_shots[0] += 1

        rad = math.radians(self.archer.angle)
        speed = 5 + power * 0.25

        start_x = self.archer.x + math.cos(rad) * 40
        start_y = self.archer.y + math.sin(rad) * 40

        vx = math.cos(rad) * speed
        vy = math.sin(rad) * speed

        self.arrows.append(Arrow(start_x, start_y, vx, vy))
        play_sound('release')

        if self.mode != 'time':
            self.arrows_left -= 1

    def update(self):
        if self.paused or self.game_over:
            return

        # آپدیت تیرها
        for arrow in self.arrows[:]:
            arrow.update(self.archer.wind)
            if not arrow.alive:
                self.arrows.remove(arrow)
                continue

            # چک برخورد با اهداف
            if not arrow.stuck and not arrow.hit_something:
                for target in self.targets:
                    if target.rect().collidepoint(arrow.x, arrow.y):
                        score = target.check_hit(arrow.x, arrow.y)
                        if score > 0:
                            arrow.stuck = True
                            arrow.hit_something = True
                            target.anim = 1.0

                            # Combo
                            if self.combo_timer > 0:
                                self.combo += 1
                            else:
                                self.combo = 1
                            self.combo_timer = 120
                            self.max_combo = max(self.max_combo, self.combo)

                            combo_mult = 1 + (self.combo - 1) * 0.2
                            final_score = int(score * combo_mult)
                            self.score += final_score
                            self.hits += 1
                            total_hits[0] += 1
                            self.level_hits += 1

                            if score == 100:
                                self.bullseyes += 1
                                total_bullseyes[0] += 1
                                play_sound('bullseye')
                                self.flash = 200
                                for _ in range(40):
                                    spawn_particles(target.x, target.y, NEON_RED, 1, 2.0, 1.5, 1.5)
                            else:
                                play_sound('hit_target')
                                for _ in range(20):
                                    spawn_particles(target.x, target.y, NEON_CYAN, 1, 1.5)

                            # Hit marker
                            self.hit_marker_timer = 30
                            self.hit_marker_pos = (arrow.x, arrow.y)
                            self.hit_marker_score = final_score

                            # دستاورد
                            if total_hits[0] >= 1: unlock_achievement('first_hit')
                            if total_hits[0] >= 10: unlock_achievement('hit_10')
                            if total_hits[0] >= 50: unlock_achievement('hit_50')
                            if total_hits[0] >= 200: unlock_achievement('hit_200')
                            if total_bullseyes[0] >= 1: unlock_achievement('bullseye_1')
                            if total_bullseyes[0] >= 10: unlock_achievement('bullseye_10')
                            if total_bullseyes[0] >= 50: unlock_achievement('bullseye_50')
                            if self.max_combo >= 5: unlock_achievement('combo_5')
                            if self.max_combo >= 10: unlock_achievement('combo_10')
                            if self.score >= 1000: unlock_achievement('score_1000')
                            if self.score >= 5000: unlock_achievement('score_5000')

                            break

            # miss
            if arrow.stuck and not arrow.hit_something and not self.game_over:
                if not hasattr(arrow, '_miss_counted'):
                    arrow._miss_counted = True
                    self.combo = 0

        # آپدیت اهداف
        for target in self.targets:
            target.update()

        # Combo timer
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0:
                self.combo = 0

        # نمایش score
        if self.display_score < self.score:
            self.display_score += max(1, (self.score - self.display_score) // 5)
            if self.display_score > self.score:
                self.display_score = self.score

        # Time mode
        if self.mode == 'time' and self.time_left is not None:
            self.time_left -= 1 / FPS
            if self.time_left <= 0:
                self.game_over = True
                self.won = True

        # Check end (practice/campaign)
        if self.mode != 'time':
            if self.arrows_left <= 0 and len(self.arrows) == 0:
                self.game_over = True

            # Campaign level complete
            if self.mode == 'campaign' and self.level_hits >= self.level_target_count:
                self.game_over = True
                self.won = True
                campaign_progress[0] = max(campaign_progress[0], self.current_level + 1)
                if campaign_progress[0] >= 10:
                    unlock_achievement('campaign_complete')

        # افکت‌ها
        if self.screen_shake > 0:
            self.screen_shake -= 1
        if self.flash > 0:
            self.flash -= 8
        if self.hit_marker_timer > 0:
            self.hit_marker_timer -= 1

        # آپدیت ذرات
        for p in active_particles[:]:
            p.update()
            if not p.active:
                active_particles.remove(p)

    def draw(self, surface):
        # آسمان
        for y in range(0, HEIGHT, 4):
            t = y / HEIGHT
            r = int(30 + 50 * t)
            g = int(20 + 40 * t)
            b = int(60 + 60 * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))

        # ابرها
        for i in range(5):
            cx = (i * 300 + pygame.time.get_ticks() * 0.02) % (WIDTH + 300) - 150
            cy = 80 + i * 30
            for hr in range(3, 0, -1):
                glow = pygame.Surface((200 + hr * 15, 80 + hr * 15), pygame.SRCALPHA)
                pygame.draw.ellipse(glow, (*WHITE, 20 - hr * 5),
                                    (0, 0, 200 + hr * 15, 80 + hr * 15))
                surface.blit(glow, (cx - hr * 7, cy - hr * 7))
            pygame.draw.ellipse(surface, (60, 60, 100), (cx, cy, 200, 80))
            pygame.draw.ellipse(surface, (90, 90, 140), (cx + 30, cy + 15, 140, 50))

        # کوه‌ها
        for i in range(8):
            mx = i * 180 - 50
            mh = 100 + (i % 3) * 40
            pts = [
                (mx, GROUND_Y),
                (mx + 90, GROUND_Y - mh),
                (mx + 180, GROUND_Y),
            ]
            pygame.draw.polygon(surface, (20, 15, 40), pts)
            pygame.draw.polygon(surface, NEON_PURPLE, pts, 2)
            # برف قله
            pygame.draw.polygon(surface, WHITE, [
                (mx + 80, GROUND_Y - mh + 15),
                (mx + 90, GROUND_Y - mh),
                (mx + 100, GROUND_Y - mh + 15),
            ])

        # زمین
        pygame.draw.rect(surface, (15, 30, 15), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.line(surface, NEON_GREEN, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)

        # اهداف
        for target in self.targets:
            target.draw(surface)

        # کماندار
        self.archer.draw(surface)

        # خط نشانه‌گیری (اگه فعاله و در حال کشیدن)
        if settings['show_trajectory'] and self.archer.is_drawing:
            rad = math.radians(self.archer.angle)
            speed = 5 + self.archer.power * 0.25
            vx = math.cos(rad) * speed
            vy = math.sin(rad) * speed
            tx = self.archer.x + math.cos(rad) * 40
            ty = self.archer.y + math.sin(rad) * 40
            for i in range(80):
                tx += vx
                ty += vy
                vy += GRAVITY
                if self.archer.wind != 0:
                    vx += self.archer.wind * 0.01
                if ty > GROUND_Y or tx > WIDTH:
                    break
                if i % 3 == 0:
                    alpha = max(30, 200 - i * 3)
                    dot = pygame.Surface((4, 4), pygame.SRCALPHA)
                    pygame.draw.circle(dot, (*NEON_YELLOW, alpha), (2, 2), 2)
                    surface.blit(dot, (tx - 2, ty - 2))

        # تیرها
        for arrow in self.arrows:
            arrow.draw(surface)

        # ذرات
        for p in active_particles:
            p.draw(surface)

        # Hit marker
        if self.hit_marker_timer > 0:
            alpha = min(255, self.hit_marker_timer * 10)
            mx, my = self.hit_marker_pos
            for angle in [0, 90, 180, 270]:
                a_rad = math.radians(angle)
                x1 = mx + math.cos(a_rad) * 12
                y1 = my + math.sin(a_rad) * 12
                x2 = mx + math.cos(a_rad) * 22
                y2 = my + math.sin(a_rad) * 22
                line_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(line_surf, (*NEON_RED, alpha), (x1, y1), (x2, y2), 3)
                surface.blit(line_surf, (0, 0))
            draw_text(surface, f"+{self.hit_marker_score}", 24, mx, my - 35,
                      NEON_YELLOW, center=True, glow=True)

        # Flash
        if self.flash > 0:
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 200, 100, self.flash))
            surface.blit(fs, (0, 0))


# --- Button & Slider ---
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


# --- Resize & Fullscreen ---
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


# --- Menu ---
def show_menu():
    menu_time = 0
    btn_practice = Button(WIDTH // 2, HEIGHT // 2 - 60, 350, 55, "TARGET PRACTICE", NEON_CYAN, NEON_GREEN, 26)
    btn_time = Button(WIDTH // 2, HEIGHT // 2, 350, 55, "TIME ATTACK (60s)", NEON_YELLOW, NEON_ORANGE, 26)
    btn_campaign = Button(WIDTH // 2, HEIGHT // 2 + 60, 350, 55, f"CAMPAIGN ({campaign_progress[0]}/10)", NEON_PURPLE, NEON_PINK, 24)
    btn_history = Button(WIDTH // 2 - 110, HEIGHT // 2 + 130, 200, 45, "HISTORY", NEON_BLUE, NEON_CYAN, 20)
    btn_settings = Button(WIDTH // 2 + 110, HEIGHT // 2 + 130, 200, 45, "SETTINGS", NEON_PURPLE, NEON_PINK, 20)
    btn_achievements = Button(WIDTH // 2 - 110, HEIGHT // 2 + 185, 200, 45, "AWARDS", NEON_YELLOW, NEON_ORANGE, 20)
    btn_quit = Button(WIDTH // 2 + 110, HEIGHT // 2 + 185, 200, 45, "QUIT", NEON_RED, NEON_ORANGE, 20)
    btn_fullscreen = Button(WIDTH - 40, 30, 40, 40, "[]", NEON_PURPLE, NEON_CYAN, 20)

    # عناصر تزئینی
    demo_arrows = []
    for i in range(5):
        demo_arrows.append({
            'x': random.randint(0, WIDTH),
            'y': random.randint(0, HEIGHT),
            'vx': random.uniform(-2, 2),
            'vy': random.uniform(-2, 2),
        })

    while True:
        game_surface.fill(DARK_BG)
        t = pygame.time.get_ticks() / 1000
        menu_time += 1
        mouse_pos = get_game_mouse_pos()

        # پس‌زمینه
        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            game_surface.blit(s, (0, y))
        # ستاره‌ها
        for _ in range(80):
            pygame.draw.circle(game_surface, (80, 100, 150),
                               (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 1)

        # عنوان
        title_y = 130 + math.sin(t * 2) * 8
        draw_text(game_surface, "NEON", 72, WIDTH // 2 - 100, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "ARCHERY", 72, WIDTH // 2 + 130, title_y, NEON_GREEN, center=True, glow=True)
        draw_text(game_surface, "AIM  /  SHOOT  /  SCORE", 20, WIDTH // 2, title_y + 65,
                  (200, 200, 220), center=True)

        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 22, WIDTH // 2, title_y + 110,
                      NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, f"SHOTS: {total_shots[0]}   HITS: {total_hits[0]}   BULLSEYES: {total_bullseyes[0]}",
                  14, WIDTH // 2, title_y + 140, NEON_PINK, center=True)

        for b in [btn_practice, btn_time, btn_campaign, btn_history, btn_settings,
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
            if btn_practice.is_clicked(event):
                return 'practice'
            if btn_time.is_clicked(event):
                return 'time'
            if btn_campaign.is_clicked(event):
                return 'campaign'
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
                    return 'practice'
                if event.key == pygame.K_2:
                    return 'time'
                if event.key == pygame.K_3:
                    return 'campaign'
                if event.key == pygame.K_ESCAPE:
                    return 'quit'
        clock.tick(FPS)


# --- Settings ---
def show_settings():
    global settings
    slider_sfx = Slider(WIDTH // 2, 180, 400, 12, settings['sfx_volume'], 0, 1, "SFX Volume")
    slider_music = Slider(WIDTH // 2, 260, 400, 12, settings['music_volume'], 0, 1, "Music Volume")
    btn_traj = Button(WIDTH // 2, 340, 280, 50,
                      f"TRAJECTORY: {'ON' if settings['show_trajectory'] else 'OFF'}",
                      NEON_GREEN if settings['show_trajectory'] else (100, 100, 100), NEON_CYAN, 20)
    btn_wind = Button(WIDTH // 2, 405, 280, 50,
                      f"WIND: {'ON' if settings['wind_enabled'] else 'OFF'}",
                      NEON_GREEN if settings['wind_enabled'] else (100, 100, 100), NEON_CYAN, 20)
    btn_shake = Button(WIDTH // 2, 470, 280, 50,
                       f"SHAKE: {'ON' if settings['screen_shake'] else 'OFF'}",
                       NEON_GREEN if settings['screen_shake'] else (100, 100, 100), NEON_CYAN, 20)
    btn_reset = Button(WIDTH // 2 - 130, 550, 220, 50, "RESET SAVE", NEON_RED, NEON_ORANGE, 20)
    btn_back = Button(WIDTH // 2 + 130, 550, 220, 50, "BACK", NEON_CYAN, NEON_GREEN, 22)

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
        box_h = 620
        box_x = WIDTH // 2 - box_w // 2
        box_y = HEIGHT // 2 - box_h // 2 + 20
        pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h), border_radius=12)
        pygame.draw.rect(game_surface, NEON_PURPLE, (box_x, box_y, box_w, box_h), 3, border_radius=12)

        draw_text(game_surface, "SETTINGS", 48, WIDTH // 2, 80, NEON_CYAN, center=True, glow=True)

        slider_sfx.update(mouse_pos, mouse_pressed)
        slider_music.update(mouse_pos, mouse_pressed)
        settings['sfx_volume'] = slider_sfx.value
        settings['music_volume'] = slider_music.value
        if music_sound[0]:
            try:
                music_sound[0].set_volume(settings['music_volume'] * 0.5)
            except:
                pass

        slider_sfx.draw(game_surface)
        slider_music.draw(game_surface)

        for btn in [btn_traj, btn_wind, btn_shake]:
            btn.update(mouse_pos)
            btn.draw(game_surface)

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
            if btn_traj.is_clicked(event):
                settings['show_trajectory'] = not settings['show_trajectory']
                save_async()
            if btn_wind.is_clicked(event):
                settings['wind_enabled'] = not settings['wind_enabled']
                save_async()
            if btn_shake.is_clicked(event):
                settings['screen_shake'] = not settings['screen_shake']
                save_async()
            if btn_reset.is_clicked(event):
                settings['sfx_volume'] = 0.7
                settings['music_volume'] = 0.5
                settings['screen_shake'] = True
                settings['show_trajectory'] = True
                settings['wind_enabled'] = True
                for k in achievements:
                    achievements[k]['unlocked'] = False
                highscore[0] = 0
                game_history.clear()
                total_hits[0] = 0
                total_bullseyes[0] = 0
                total_shots[0] = 0
                campaign_progress[0] = 0
                save_async()
                slider_sfx.value = 0.7
                slider_music.value = 0.5
            if btn_back.is_clicked(event):
                save_async()
                return
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_b):
                save_async()
                return
        clock.tick(FPS)


# --- Achievements & History ---
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

        draw_text(game_surface, "GAME HISTORY", 46, WIDTH // 2, 35, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, f"Total games: {len(game_history)}", 16, WIDTH // 2, 72, NEON_YELLOW, center=True)

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
                score = entry.get('score', 0)
                if score >= 5000:
                    rank_color, rank = NEON_PINK, "S"
                elif score >= 2000:
                    rank_color, rank = NEON_YELLOW, "A"
                elif score >= 1000:
                    rank_color, rank = NEON_GREEN, "B"
                elif score >= 500:
                    rank_color, rank = NEON_CYAN, "C"
                else:
                    rank_color, rank = (150, 150, 180), "D"
                pygame.draw.rect(game_surface, (15, 8, 30), (ix, iy, iw, item_h - 8), border_radius=6)
                pygame.draw.rect(game_surface, rank_color, (ix, iy, iw, item_h - 8), 2, border_radius=6)
                draw_text(game_surface, rank, 28, ix + 35, iy + (item_h - 8) // 2, rank_color, center=True, glow=True)
                draw_text(game_surface, f"SCORE: {score}", 18, ix + 90, iy + 8, WHITE)
                draw_text(game_surface, f"HITS: {entry.get('hits', 0)}/{entry.get('shots', 0)}   ACC: {entry.get('accuracy', 0):.0f}%",
                          12, ix + 90, iy + 30, (180, 180, 200))
                draw_text(game_surface, entry.get('mode', '?').upper(), 12, ix + iw - 220, iy + 8, NEON_CYAN)
                draw_text(game_surface, entry.get('date', '?'), 12, ix + iw - 220, iy + 30, NEON_CYAN)
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


# --- Main Game ---
def play_game(mode='practice'):
    game = Game(mode)

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
        add_game_to_history(game.score, game.hits, game.shots, mode, new_achs)

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

            if game.paused and not game.game_over:
                if btn_resume.is_clicked(event):
                    game.paused = False
                if btn_pause_menu.is_clicked(event):
                    stop_music()
                    if not game_saved:
                        save_current()
                        game_saved = True
                    return

            if game.game_over:
                if btn_restart.is_clicked(event):
                    stop_music()
                    play_game(mode)
                    return
                if btn_menu.is_clicked(event):
                    stop_music()
                    if not game_saved:
                        save_current()
                        game_saved = True
                    return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p and not game.game_over:
                    game.paused = not game.paused
                if event.key == pygame.K_r and game.game_over:
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

        if game.paused and not game.game_over:
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

        if not game.game_over:
            # آپدیت کماندار
            power = game.archer.update(mouse_pos, mouse_pressed)
            if power is not None and power > 10:
                game.shoot(power)

            # آپدیت بازی
            game.update()

            # چک برد
            if game.game_over and not game_saved:
                save_current()
                game_saved = True
                highscore[0] = max(highscore[0], game.score)
                if game.score >= 1000: try_unlock('score_1000')
                if game.score >= 5000: try_unlock('score_5000')
                if game.won and game.mode == 'campaign':
                    try_unlock('campaign_complete')

        # ============================================================
        #                    رسم
        # ============================================================
        game_surface.fill(DARK_BG)
        offset_x = random.randint(-game.screen_shake, game.screen_shake) if game.screen_shake > 0 else 0
        offset_y = random.randint(-game.screen_shake, game.screen_shake) if game.screen_shake > 0 else 0

        play_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        game.draw(play_layer)
        game_surface.blit(play_layer, (offset_x, offset_y))

        # ============================================================
        #                    HUD
        # ============================================================
        # نوار بالا
        hud_panel = pygame.Surface((WIDTH, 70), pygame.SRCALPHA)
        for y in range(70):
            alpha = int(180 * (1 - y / 70))
            pygame.draw.line(hud_panel, (5, 10, 25, alpha), (0, y), (WIDTH, y))
        game_surface.blit(hud_panel, (0, 0))
        pygame.draw.line(game_surface, NEON_CYAN, (0, 70), (WIDTH, 70), 1)

        # عنوان
        draw_text(game_surface, "NEON ARCHERY", 22, 25, 10, NEON_GREEN, glow=True)
        mode_text = {'practice': 'PRACTICE', 'time': 'TIME ATTACK', 'campaign': f'CAMPAIGN LV{game.current_level + 1}'}
        draw_text(game_surface, mode_text.get(mode, 'PRACTICE'), 14, 25, 40, NEON_YELLOW)

        # Score
        draw_text(game_surface, "SCORE", 14, WIDTH // 2, 10, NEON_CYAN, center=True)
        draw_text(game_surface, f"{game.display_score}", 32, WIDTH // 2, 30, WHITE, center=True, glow=True)

        # Arrows left / Time
        if mode == 'time':
            draw_text(game_surface, f"TIME: {int(game.time_left)}s", 20, WIDTH - 25, 15, NEON_YELLOW, glow=True)
        else:
            draw_text(game_surface, f"ARROWS: {game.arrows_left}", 20, WIDTH - 25, 15, NEON_YELLOW, glow=True)

        # Hits
        acc = (game.hits / max(1, game.shots)) * 100
        draw_text(game_surface, f"HITS: {game.hits}/{game.shots}  ({acc:.0f}%)", 14, WIDTH - 25, 40, NEON_CYAN)

        # Combo
        if game.combo > 1:
            combo_color = NEON_GREEN if game.combo < 5 else NEON_YELLOW if game.combo < 10 else NEON_PINK
            scale = 1 + math.sin(t * 10) * 0.1
            draw_text(game_surface, f"x{game.combo} COMBO", int(24 * scale), WIDTH // 2, 100,
                      combo_color, center=True, glow=True)

        # Wind
        if settings['wind_enabled'] and abs(game.archer.wind) > 0.5:
            wind_dir = 1 if game.archer.wind > 0 else -1
            wind_speed = abs(game.archer.wind)
            arrow = "→" if wind_dir > 0 else "←"
            color = NEON_CYAN if wind_speed < 2 else NEON_YELLOW if wind_speed < 3 else NEON_RED
            draw_text(game_surface, f"WIND: {arrow * int(wind_speed)}", 16, 25, HEIGHT - 40, color, glow=True)

        # راهنما
        if game.shots < 3:
            draw_text(game_surface, "Click and DRAG to aim, RELEASE to shoot!", 16,
                      WIDTH // 2, HEIGHT - 40, NEON_CYAN, center=True)

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
        if game.game_over:
            go_anim += 1
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            game_surface.blit(overlay, (0, 0))
            box_w = 540
            box_h = 420
            box_x = WIDTH // 2 - box_w // 2
            box_y = HEIGHT // 2 - box_h // 2
            pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h))
            win_color = NEON_GREEN if game.won else NEON_RED
            pygame.draw.rect(game_surface, win_color, (box_x, box_y, box_w, box_h), 3)
            pygame.draw.rect(game_surface, NEON_CYAN, (box_x + 5, box_y + 5, box_w - 10, box_h - 10), 1)

            title = "LEVEL COMPLETE!" if game.won and mode == 'campaign' else \
                    "TIME'S UP!" if mode == 'time' else \
                    "ROUND COMPLETE"
            draw_text(game_surface, title, 48, WIDTH // 2, box_y + 50,
                      win_color, center=True, glow=True)
            draw_text(game_surface, f"SCORE: {game.score}", 32, WIDTH // 2, box_y + 120,
                      WHITE, center=True, glow=True)
            acc = (game.hits / max(1, game.shots)) * 100
            draw_text(game_surface, f"HITS: {game.hits}/{game.shots}  ({acc:.0f}%)", 20,
                      WIDTH // 2, box_y + 165, NEON_CYAN, center=True)
            draw_text(game_surface, f"BULLSEYES: {game.bullseyes}   MAX COMBO: {game.max_combo}",
                      16, WIDTH // 2, box_y + 200, NEON_YELLOW, center=True)
            hs = highscore[0]
            if game.score >= hs and game.score > 0:
                draw_text(game_surface, "* NEW HIGH SCORE! *", 22, WIDTH // 2, box_y + 240,
                          NEON_YELLOW, center=True, glow=True)
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
        elif result in ['practice', 'time', 'campaign']:
            play_game(result)
    pygame.quit()


if __name__ == "__main__":
    main()