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

BASE_W, BASE_H = 1000, 750
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("ASTEROID HUNTER")
game_surface = pygame.Surface((BASE_W, BASE_H))

clock = pygame.time.Clock()
FPS = 60

# --- رنگ‌ها ---
BLACK = (0, 0, 4)
DARK_BG = (3, 5, 15)
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

# --- ذخیره ---
SAVE_FILE = "asteroid_hunter_save.json"

settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'difficulty': 1.0,
    'screen_shake': True,
}

achievements = {
    'first_rock': {'name': 'FIRST BLOOD', 'desc': 'Destroy your first asteroid', 'unlocked': False, 'icon': '*'},
    'asteroid_10': {'name': 'ROOKIE', 'desc': 'Destroy 10 asteroids', 'unlocked': False, 'icon': '**'},
    'asteroid_50': {'name': 'VETERAN', 'desc': 'Destroy 50 asteroids', 'unlocked': False, 'icon': '***'},
    'asteroid_200': {'name': 'LEGEND', 'desc': 'Destroy 200 asteroids', 'unlocked': False, 'icon': '****'},
    'level_3': {'name': 'EXPLORER', 'desc': 'Reach level 3', 'unlocked': False, 'icon': 'L3'},
    'level_5': {'name': 'ADVENTURER', 'desc': 'Reach level 5', 'unlocked': False, 'icon': 'L5'},
    'level_10': {'name': 'MASTER', 'desc': 'Reach level 10', 'unlocked': False, 'icon': 'L10'},
    'score_5000': {'name': 'HUNTER', 'desc': 'Score 5000 points', 'unlocked': False, 'icon': '$5K'},
    'score_20000': {'name': 'ACE', 'desc': 'Score 20000 points', 'unlocked': False, 'icon': '$20K'},
    'score_50000': {'name': 'GRANDMASTER', 'desc': 'Score 50000 points', 'unlocked': False, 'icon': '$50K'},
    'ufo_kill': {'name': 'UFO HUNTER', 'desc': 'Destroy your first UFO', 'unlocked': False, 'icon': 'U'},
    'ufo_5': {'name': 'ALIEN SLAYER', 'desc': 'Destroy 5 UFOs', 'unlocked': False, 'icon': 'UU'},
    'hyperspace': {'name': 'WARP DRIVE', 'desc': 'Use hyperspace jump', 'unlocked': False, 'icon': 'H'},
    'power_5': {'name': 'POWERED UP', 'desc': 'Collect 5 power-ups', 'unlocked': False, 'icon': 'P5'},
    'survive_2min': {'name': 'SURVIVOR', 'desc': 'Survive 2 minutes', 'unlocked': False, 'icon': 'T'},
}

highscore = [0]
game_history = []
total_asteroids = [0]
total_ufos = [0]


def load_save():
    global settings, achievements, highscore, game_history, total_asteroids, total_ufos
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
            settings.update(data.get('settings', {}))
            for k, v in data.get('achievements', {}).items():
                if k in achievements:
                    achievements[k]['unlocked'] = v
            highscore[0] = data.get('highscore', 0)
            game_history = data.get('game_history', [])
            total_asteroids[0] = data.get('total_asteroids', 0)
            total_ufos[0] = data.get('total_ufos', 0)
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
                'total_asteroids': total_asteroids[0],
                'total_ufos': total_ufos[0],
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
    sounds['shoot'] = make_sound(900, 1400, 0.08, 0.12, 'square')
    sounds['explode'] = make_sound(400, 50, 0.3, 0.25, 'noise')
    sounds['big_explode'] = make_sound(250, 30, 0.5, 0.32, 'noise')
    sounds['hit'] = make_sound(200, 60, 0.4, 0.28, 'noise')
    sounds['power'] = make_sound(500, 1400, 0.35, 0.20, 'sine')
    sounds['hyperspace'] = make_sound(2000, 200, 0.4, 0.22, 'saw')
    sounds['ufo'] = make_sound(600, 900, 0.3, 0.15, 'saw')
    sounds['ufo_shoot'] = make_sound(500, 800, 0.1, 0.18, 'square')
    sounds['gameover'] = make_sound(500, 60, 1.2, 0.30, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['levelup'] = make_sound(500, 1500, 0.4, 0.20, 'sine')
    sounds['boss'] = make_sound(150, 400, 1.0, 0.28, 'saw')

    bass = [49, 49, 55, 55, 44, 44, 49, 49]
    lead = [392, 466, 587, 466, 392, 349, 311, 349]
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
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'size', 'active')

    def __init__(self):
        self.active = False

    def spawn(self, x, y, color, speed_mult=1.0, size_mult=1.0, life_mult=1.0):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 6) * speed_mult
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
        self.vx *= 0.97
        self.vy *= 0.97
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
#                    Spaceship
# ============================================================
class Ship:
    def __init__(self):
        self.x = WIDTH / 2
        self.y = HEIGHT / 2
        self.vx = 0
        self.vy = 0
        self.angle = -90  # رو به بالا
        self.radius = 15
        self.alive = True
        self.invincible = 120  # 2 ثانیه اول
        self.shield = 0
        self.triple_shot = 0
        self.rapid_fire = 0
        self.piercing = 0
        self.magnet = 0
        self.thrust_power = 0.25
        self.rotation_speed = 4
        self.friction = 0.99
        self.max_speed = 8
        self.shoot_cooldown = 0
        self.engine_particles_timer = 0

    def update(self, keys):
        if not self.alive:
            return

        # چرخش
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle -= self.rotation_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle += self.rotation_speed

        # شتاب
        thrusting = False
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            rad = math.radians(self.angle)
            self.vx += math.cos(rad) * self.thrust_power
            self.vy += math.sin(rad) * self.thrust_power
            thrusting = True

        # اصطکاک
        self.vx *= self.friction
        self.vy *= self.friction

        # محدودیت سرعت
        speed = math.hypot(self.vx, self.vy)
        if speed > self.max_speed:
            self.vx = self.vx / speed * self.max_speed
            self.vy = self.vy / speed * self.max_speed

        # حرکت
        self.x += self.vx
        self.y += self.vy

        # Wrap around
        if self.x < -self.radius:
            self.x = WIDTH + self.radius
        elif self.x > WIDTH + self.radius:
            self.x = -self.radius
        if self.y < -self.radius:
            self.y = HEIGHT + self.radius
        elif self.y > HEIGHT + self.radius:
            self.y = -self.radius

        # تایمرها
        if self.invincible > 0:
            self.invincible -= 1
        if self.shield > 0:
            self.shield -= 1
        if self.triple_shot > 0:
            self.triple_shot -= 1
        if self.rapid_fire > 0:
            self.rapid_fire -= 1
        if self.piercing > 0:
            self.piercing -= 1
        if self.magnet > 0:
            self.magnet -= 1
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        # ذرات موتور
        if thrusting:
            self.engine_particles_timer += 1
            if self.engine_particles_timer > 1:
                self.engine_particles_timer = 0
                rad = math.radians(self.angle)
                back_x = self.x - math.cos(rad) * self.radius
                back_y = self.y - math.sin(rad) * self.radius
                for _ in range(2):
                    offset = random.uniform(-3, 3)
                    perp = rad + math.pi / 2
                    px = back_x + math.cos(perp) * offset
                    py = back_y + math.sin(perp) * offset
                    p = None
                    for pp in particle_pool:
                        if not pp.active:
                            p = pp
                            break
                    if p is None:
                        p = Particle()
                        particle_pool.append(p)
                    p.x = px
                    p.y = py
                    p.vx = -math.cos(rad) * random.uniform(2, 4) + self.vx * 0.3
                    p.vy = -math.sin(rad) * random.uniform(2, 4) + self.vy * 0.3
                    p.life = random.randint(10, 20)
                    p.max_life = p.life
                    p.color = random.choice([NEON_CYAN, NEON_BLUE, (150, 200, 255)])
                    p.size = random.randint(2, 4)
                    p.active = True
                    active_particles.append(p)

    def draw(self, surface):
        if not self.alive:
            return

        # چشمک‌زدن در حالت نامیرایی
        if self.invincible > 0 and (self.invincible // 4) % 2 == 0:
            # در حالت چشمک، فقط هاله رو بکش
            glow = pygame.Surface((self.radius * 6, self.radius * 6), pygame.SRCALPHA)
            pygame.draw.circle(glow, (100, 200, 255, 50),
                               (self.radius * 3, self.radius * 3), self.radius * 2)
            surface.blit(glow, (self.x - self.radius * 3, self.y - self.radius * 3))
            return

        rad = math.radians(self.angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        # نقاط سفینه (سه‌ضلعی)
        tip = (self.x + cos_a * self.radius, self.y + sin_a * self.radius)
        # بال چپ
        left_angle = rad + math.radians(140)
        left = (self.x + math.cos(left_angle) * self.radius * 0.9,
                self.y + math.sin(left_angle) * self.radius * 0.9)
        # بال راست
        right_angle = rad - math.radians(140)
        right = (self.x + math.cos(right_angle) * self.radius * 0.9,
                 self.y + math.sin(right_angle) * self.radius * 0.9)
        # فرورفتگی عقب
        back_angle = rad + math.pi
        back = (self.x + math.cos(back_angle) * self.radius * 0.4,
                self.y + math.sin(back_angle) * self.radius * 0.4)

        # هاله درخشان
        for r in range(3, 0, -1):
            glow = pygame.Surface((self.radius * 5, self.radius * 5), pygame.SRCALPHA)
            pygame.draw.polygon(glow, (50, 150, 255, 40 - r * 10),
                                [(self.radius * 2.5 + (px - self.x) * (1 + r * 0.3),
                                  self.radius * 2.5 + (py - self.y) * (1 + r * 0.3))
                                 for px, py in [tip, right, back, left]])
            surface.blit(glow, (self.x - self.radius * 2.5, self.y - self.radius * 2.5))

        # بدنه‌ی سفینه
        pygame.draw.polygon(surface, (20, 60, 120), [tip, right, back, left])
        pygame.draw.polygon(surface, NEON_CYAN, [tip, right, back, left], 2)
        pygame.draw.polygon(surface, WHITE, [tip, right, back, left], 1)

        # خط مرکزی
        pygame.draw.line(surface, WHITE, (self.x, self.y), tip, 2)

        # کابین (دایره‌ی نورانی وسط)
        cabin_glow = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(cabin_glow, (100, 220, 255, 150), (10, 10), 8)
        surface.blit(cabin_glow, (self.x - 10, self.y - 10))
        pygame.draw.circle(surface, NEON_CYAN, (int(self.x), int(self.y)), 4)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 2)

        # شیلد
        if self.shield > 0:
            shield_alpha = 100 + int(math.sin(pygame.time.get_ticks() / 100) * 60)
            for r in range(3):
                shield_surf = pygame.Surface((self.radius * 6, self.radius * 6), pygame.SRCALPHA)
                pygame.draw.circle(shield_surf, (*NEON_GREEN, shield_alpha // (r + 2)),
                                   (self.radius * 3, self.radius * 3), self.radius * 2 + r * 3, 2)
                surface.blit(shield_surf, (self.x - self.radius * 3, self.y - self.radius * 3))

        # نشانگرهای قدرت
        if self.triple_shot > 0:
            draw_text(surface, "3x", 14, self.x, self.y - self.radius - 15, NEON_YELLOW, center=True)
        if self.rapid_fire > 0:
            draw_text(surface, "RF", 14, self.x, self.y - self.radius - 30, NEON_ORANGE, center=True)

    def shoot(self):
        if self.shoot_cooldown > 0:
            return []

        bullets = []
        rad = math.radians(self.angle)
        # سرعت تیر = سرعت سفینه + سرعت خروج
        base_speed = 12
        bullet_speed_x = math.cos(rad) * base_speed + self.vx * 0.5
        bullet_speed_y = math.sin(rad) * base_speed + self.vy * 0.5

        if self.triple_shot > 0:
            # سه تیر با زاویه‌های مختلف
            for offset_angle in [-15, 0, 15]:
                a = rad + math.radians(offset_angle)
                vx = math.cos(a) * base_speed + self.vx * 0.5
                vy = math.sin(a) * base_speed + self.vy * 0.5
                bullets.append(Bullet(self.x, self.y, vx, vy, piercing=self.piercing > 0))
        else:
            bullets.append(Bullet(self.x, self.y, bullet_speed_x, bullet_speed_y,
                                   piercing=self.piercing > 0))

        self.shoot_cooldown = 8 if self.rapid_fire > 0 else 12
        play_sound('shoot')
        return bullets

    def hyperspace(self):
        """پرش تصادفی به مکان دیگه"""
        old_x, old_y = self.x, self.y
        # ذرات در محل قدیم
        spawn_particles(old_x, old_y, NEON_CYAN, 25, 1.5, 1.2, 1.2)
        # جای جدید
        self.x = random.uniform(100, WIDTH - 100)
        self.y = random.uniform(100, HEIGHT - 100)
        self.vx = 0
        self.vy = 0
        # ذرات در محل جدید
        spawn_particles(self.x, self.y, NEON_CYAN, 25, 1.5, 1.2, 1.2)
        # خطر: ممکنه اتفاق بدی بیفته (10%)
        if random.random() < 0.1:
            return False  # باخت
        self.invincible = max(self.invincible, 60)
        return True


# ============================================================
#                    Bullet
# ============================================================
class Bullet:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'radius', 'piercing', 'trail')

    def __init__(self, x, y, vx, vy, piercing=False):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = 60
        self.radius = 3
        self.piercing = piercing
        self.trail = []

    def update(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 8:
            self.trail.pop(0)
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        # Wrap
        if self.x < 0:
            self.x = WIDTH
        elif self.x > WIDTH:
            self.x = 0
        if self.y < 0:
            self.y = HEIGHT
        elif self.y > HEIGHT:
            self.y = 0

    def draw(self, surface):
        # دنباله
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / len(self.trail)
            r = max(1, int(self.radius * alpha))
            c = (0, int(200 * alpha + 55), 255)
            pygame.draw.circle(surface, c, (int(tx), int(ty)), r)

        # گلوله
        color = NEON_MAGENTA if self.piercing else NEON_CYAN
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 1)


# ============================================================
#                    Asteroid
# ============================================================
class Asteroid:
    def __init__(self, x, y, size=3, vx=None, vy=None):
        self.x = x
        self.y = y
        self.size = size  # 3=بزرگ، 2=متوسط، 1=کوچک
        self.radius = {3: 50, 2: 30, 1: 18}[size]
        self.score_value = {3: 20, 2: 50, 1: 100}[size]
        if vx is None:
            speed = random.uniform(1, 3)
            angle = random.uniform(0, 2 * math.pi)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
        else:
            self.vx = vx
            self.vy = vy
        # شکل چندضلعی تصادفی
        self.shape_points = []
        num_points = random.randint(7, 11)
        for i in range(num_points):
            angle = (2 * math.pi / num_points) * i
            offset = random.uniform(0.75, 1.0)
            px = math.cos(angle) * self.radius * offset
            py = math.sin(angle) * self.radius * offset
            self.shape_points.append((px, py))
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-2, 2)
        self.alive = True
        self.hit_flash = 0

    def update(self, speed_mult=1.0):
        self.x += self.vx * speed_mult
        self.y += self.vy * speed_mult
        self.rotation += self.rot_speed
        if self.hit_flash > 0:
            self.hit_flash -= 1
        # Wrap
        if self.x < -self.radius:
            self.x = WIDTH + self.radius
        elif self.x > WIDTH + self.radius:
            self.x = -self.radius
        if self.y < -self.radius:
            self.y = HEIGHT + self.radius
        elif self.y > HEIGHT + self.radius:
            self.y = -self.radius

    def split(self):
        """تقسیم به دو سیارک کوچیک‌تر"""
        if self.size <= 1:
            return []
        new_size = self.size - 1
        asteroids = []
        for _ in range(2):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 4)
            vx = math.cos(angle) * speed + self.vx * 0.5
            vy = math.sin(angle) * speed + self.vy * 0.5
            asteroids.append(Asteroid(self.x, self.y, new_size, vx, vy))
        return asteroids

    def draw(self, surface):
        # محاسبه نقاط چرخیده
        rad = math.radians(self.rotation)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)
        points = []
        for px, py in self.shape_points:
            rx = px * cos_r - py * sin_r
            ry = px * sin_r + py * cos_r
            points.append((self.x + rx, self.y + ry))

        # رنگ بر اساس اندازه
        if self.hit_flash > 0:
            main_color = WHITE
        else:
            if self.size == 3:
                main_color = NEON_ORANGE
            elif self.size == 2:
                main_color = NEON_RED
            else:
                main_color = NEON_PINK

        # هاله
        glow = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        glow_points = [(self.radius * 2 + (px - self.x), self.radius * 2 + (py - self.y))
                       for px, py in points]
        pygame.draw.polygon(glow, (*main_color, 40), glow_points)
        surface.blit(glow, (self.x - self.radius * 2, self.y - self.radius * 2))

        # بدنه
        darker = (main_color[0] // 3, main_color[1] // 3, main_color[2] // 3)
        pygame.draw.polygon(surface, darker, points)
        pygame.draw.polygon(surface, main_color, points, 2)
        pygame.draw.polygon(surface, WHITE, points, 1)

        # جزئیات سطح (دهانه‌ها)
        if self.size >= 2:
            for _ in range(3):
                cx = self.x + random.uniform(-self.radius * 0.3, self.radius * 0.3)
                cy = self.y + random.uniform(-self.radius * 0.3, self.radius * 0.3)
                pygame.draw.circle(surface, (main_color[0] // 2, main_color[1] // 2, main_color[2] // 2),
                                   (int(cx), int(cy)), random.randint(2, 4))


# ============================================================
#                    UFO
# ============================================================
class UFO:
    def __init__(self, size='small'):
        self.size = size
        self.radius = 20 if size == 'small' else 35
        self.score_value = 200 if size == 'small' else 500
        # از طرفین وارد میشه
        if random.random() < 0.5:
            self.x = -self.radius
            self.vx = random.uniform(1.5, 2.5)
        else:
            self.x = WIDTH + self.radius
            self.vx = -random.uniform(1.5, 2.5)
        self.y = random.uniform(100, HEIGHT - 100)
        self.vy = random.uniform(-0.5, 0.5)
        self.shoot_timer = 0
        self.shoot_interval = 90 if size == 'small' else 60
        self.alive = True
        self.hit_flash = 0

    def update(self, player_pos):
        self.x += self.vx
        self.y += self.vy
        # Wrap y
        if self.y < 0:
            self.y = HEIGHT
        elif self.y > HEIGHT:
            self.y = 0
        if self.hit_flash > 0:
            self.hit_flash -= 1

        # چک خروج
        if self.x < -self.radius * 2 or self.x > WIDTH + self.radius * 2:
            self.alive = False

        # شلیک
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_interval:
            self.shoot_timer = 0
            return self.shoot(player_pos)
        return None

    def shoot(self, player_pos):
        """شلیک به سمت بازیکن"""
        px, py = player_pos
        dx = px - self.x
        dy = py - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            speed = 5
            vx = dx / dist * speed
            vy = dy / dist * speed
            # دقت کمتر برای UFO کوچیک
            if self.size == 'small':
                vx += random.uniform(-1, 1)
                vy += random.uniform(-1, 1)
            play_sound('ufo_shoot')
            return Bullet(self.x, self.y, vx, vy)
        return None

    def draw(self, surface):
        # هاله
        color = WHITE if self.hit_flash > 0 else (NEON_MAGENTA if self.size == 'small' else NEON_PURPLE)
        for r in range(3, 0, -1):
            glow = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*color, 30 - r * 8),
                                (0, self.radius, self.radius * 4, self.radius * 1.5))
            surface.blit(glow, (self.x - self.radius * 2, self.y - self.radius * 2))

        # بشقاب پایین
        rect = pygame.Rect(int(self.x - self.radius), int(self.y),
                           self.radius * 2, self.radius * 0.7)
        pygame.draw.ellipse(surface, (color[0] // 2, color[1] // 2, color[2] // 2), rect)
        pygame.draw.ellipse(surface, color, rect, 2)

        # گنبد بالا
        dome_rect = pygame.Rect(int(self.x - self.radius * 0.5), int(self.y - self.radius * 0.5),
                                self.radius, self.radius * 0.7)
        pygame.draw.ellipse(surface, (color[0] // 3, color[1] // 3, color[2] // 3), dome_rect)
        pygame.draw.ellipse(surface, color, dome_rect, 2)

        # چراغ‌های چشمک‌زن
        blink = (pygame.time.get_ticks() // 200) % 3
        for i in range(3):
            lx = self.x - self.radius * 0.6 + i * self.radius * 0.6
            ly = self.y + self.radius * 0.35
            light_color = color if i == blink else (color[0] // 3, color[1] // 3, color[2] // 3)
            pygame.draw.circle(surface, light_color, (int(lx), int(ly)), 3)


# ============================================================
#                    PowerUp
# ============================================================
class PowerUp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 2)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.type = random.choices(
            ['shield', 'triple', 'rapid', 'piercing', 'magnet', 'life'],
            weights=[3, 3, 3, 2, 2, 1]
        )[0]
        self.radius = 15
        self.pulse = 0
        self.life = 600  # 10 ثانیه

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.pulse += 0.15
        self.life -= 1
        # Wrap
        if self.x < -self.radius:
            self.x = WIDTH + self.radius
        elif self.x > WIDTH + self.radius:
            self.x = -self.radius
        if self.y < -self.radius:
            self.y = HEIGHT + self.radius
        elif self.y > HEIGHT + self.radius:
            self.y = -self.radius

    def draw(self, surface):
        colors = {
            'shield': NEON_GREEN,
            'triple': NEON_YELLOW,
            'rapid': NEON_ORANGE,
            'piercing': NEON_MAGENTA,
            'magnet': NEON_CYAN,
            'life': NEON_RED,
        }
        color = colors[self.type]
        r = self.radius + int(math.sin(self.pulse) * 3)

        # هاله
        for i in range(3, 0, -1):
            glow = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 50 - i * 12), (r * 2, r * 2), r * 1.5)
            surface.blit(glow, (self.x - r * 2, self.y - r * 2))

        # دایره اصلی
        pygame.draw.circle(surface, (color[0] // 3, color[1] // 3, color[2] // 3),
                           (int(self.x), int(self.y)), r)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), r, 2)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), r, 1)

        # آیکون
        icon = {
            'shield': 'S', 'triple': '3', 'rapid': 'R',
            'piercing': 'P', 'magnet': 'M', 'life': '+'
        }[self.type]
        draw_text(surface, icon, 16, self.x, self.y - 8, WHITE, center=True, bold=True)


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
#                    پس‌زمینه (Pre-render)
# ============================================================
def build_space_bg():
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    # گرادیان
    for y in range(HEIGHT):
        t = y / HEIGHT
        c = (int(2 + 5 * t), int(3 + 8 * t), int(10 + 20 * t))
        pygame.draw.line(surf, c, (0, y), (WIDTH, y))
    # ستاره‌ها (سه لایه)
    for _ in range(80):
        x, y = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        size = random.choice([1, 1, 1, 2])
        brightness = random.randint(80, 150)
        pygame.draw.circle(surf, (brightness, brightness, brightness + 30), (x, y), size)
    for _ in range(50):
        x, y = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        pygame.draw.circle(surf, (180, 190, 220), (x, y), random.choice([1, 2]))
    for _ in range(20):
        x, y = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        pygame.draw.circle(surf, (230, 240, 255), (x, y), 2)
    return surf


space_bg = build_space_bg()


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

    # سیارک‌های تزئینی
    menu_asteroids = []
    for _ in range(5):
        a = Asteroid(random.uniform(0, WIDTH), random.uniform(0, HEIGHT),
                     random.choice([1, 2, 3]))
        menu_asteroids.append(a)

    # سفینه تزئینی
    menu_ship = Ship()
    menu_ship.x = WIDTH // 2
    menu_ship.y = 550
    menu_ship.invincible = 0

    while True:
        game_surface.fill(BLACK)
        t = pygame.time.get_ticks() / 1000
        menu_time += 1
        mouse_pos = get_game_mouse_pos()

        game_surface.blit(space_bg, (0, 0))

        # سیارک‌های شناور
        for a in menu_asteroids:
            a.update(0.5)
            a.draw(game_surface)

        # سفینه
        menu_ship.angle += 0.5
        menu_ship.draw(game_surface)

        # عنوان
        title_y = 130 + math.sin(t * 2) * 8
        draw_text(game_surface, "ASTEROID", 68, WIDTH // 2, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "HUNTER", 68, WIDTH // 2, title_y + 65, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, "ROTATE  /  SHOOT  /  SURVIVE", 20, WIDTH // 2, title_y + 130,
                  (200, 200, 220), center=True)

        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 22, WIDTH // 2, title_y + 175,
                      NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, f"ASTEROIDS: {total_asteroids[0]}   UFOs: {total_ufos[0]}",
                  14, WIDTH // 2, title_y + 205, NEON_PINK, center=True)

        for b in [btn_start, btn_history, btn_settings, btn_achievements, btn_quit, btn_fullscreen]:
            b.update(mouse_pos)
            b.draw(game_surface)

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
    btn_shake = Button(WIDTH // 2, 450, 280, 55,
                       f"SHAKE: {'ON' if settings['screen_shake'] else 'OFF'}",
                       NEON_GREEN if settings['screen_shake'] else (100, 100, 100), NEON_CYAN, 22)
    btn_reset = Button(WIDTH // 2 - 130, 530, 220, 50, "RESET SAVE", NEON_RED, NEON_ORANGE, 20)
    btn_back = Button(WIDTH // 2 + 130, 530, 220, 50, "BACK", NEON_CYAN, NEON_GREEN, 22)

    while True:
        game_surface.fill(DARK_BG)
        mouse_pos = get_game_mouse_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        game_surface.blit(space_bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 5, 200))
        game_surface.blit(overlay, (0, 0))

        box_w, box_h = 700, 580
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
                total_asteroids[0] = 0
                total_ufos[0] = 0
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

        game_surface.blit(space_bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 5, 200))
        game_surface.blit(overlay, (0, 0))

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

        game_surface.blit(space_bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 5, 200))
        game_surface.blit(overlay, (0, 0))

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
                draw_text(game_surface, f"LEVEL: {entry.get('level', 1)}   TIME: {entry.get('duration', 0)}s",
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
    ship = Ship()
    bullets = []
    asteroids = []
    ufos = []
    ufo_bullets = []
    powerups = []

    score = 0
    display_score = 0
    asteroids_destroyed = 0
    ufos_destroyed = 0
    powers_collected = 0
    total_frames = 0
    level = 1

    # افکت‌ها
    screen_shake = 0
    flash = 0
    game_over = False
    paused = False
    final_score = 0
    final_level = 1
    new_achs = []
    notifications = []
    go_anim = 0
    game_saved = False

    # تایمرها
    ufo_spawn_timer = FPS * 15  # اولین UFO بعد از 15 ثانیه
    ufo_spawn_interval = FPS * 25  # بعدی هر 25 ثانیه
    powerup_spawn_timer = FPS * 8
    next_level_timer = 0
    level_banner_timer = 90

    # دکمه‌ها
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
        add_game_to_history(score, level, total_frames // FPS, new_achs)

    def spawn_initial_asteroids(count):
        for _ in range(count):
            # از لبه‌ها بیا
            side = random.randint(0, 3)
            if side == 0:
                x, y = random.uniform(0, WIDTH), -50
            elif side == 1:
                x, y = WIDTH + 50, random.uniform(0, HEIGHT)
            elif side == 2:
                x, y = random.uniform(0, WIDTH), HEIGHT + 50
            else:
                x, y = -50, random.uniform(0, HEIGHT)
            asteroids.append(Asteroid(x, y, 3))

    spawn_initial_asteroids(3 + level)

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
                if not paused and not game_over:
                    if event.key == pygame.K_SPACE:
                        new_bullets = ship.shoot()
                        bullets.extend(new_bullets)
                    if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        if not ship.hyperspace():
                            # خطر: بازیکن باخت
                            ship.alive = False
                        try_unlock('hyperspace')
                        play_sound('hyperspace')
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
            if total_frames >= FPS * 120:
                try_unlock('survive_2min')

            # آپدیت اسکور
            if display_score < score:
                display_score += max(1, (score - display_score) // 5)
                if display_score > score:
                    display_score = score

            # ورودی
            keys = pygame.key.get_pressed()
            if not paused:
                ship.update(keys)
                # شلیک پیوسته
                if keys[pygame.K_SPACE]:
                    new_bullets = ship.shoot()
                    bullets.extend(new_bullets)

            if not ship.alive:
                game_over = True
                final_score = score
                final_level = level
                highscore[0] = max(highscore[0], score)
                if score >= 5000:
                    try_unlock('score_5000')
                if score >= 20000:
                    try_unlock('score_20000')
                if score >= 50000:
                    try_unlock('score_50000')
                if settings['screen_shake']:
                    screen_shake = 30
                flash = 200
                play_sound('big_explode')
                for _ in range(60):
                    spawn_particles(ship.x, ship.y,
                                    random.choice([NEON_CYAN, NEON_BLUE, WHITE]),
                                    1, 2.0, 1.5, 1.5)
                save_current()
                game_saved = True
                play_sound('gameover')
                go_anim = 0

            # آپدیت تیرها
            for b in bullets[:]:
                b.update()
                if b.life <= 0:
                    bullets.remove(b)

            # آپدیت UFO bullets
            for b in ufo_bullets[:]:
                b.update()
                if b.life <= 0:
                    ufo_bullets.remove(b)

            # آپدیت سیارک‌ها
            speed_mult = settings['difficulty'] * (1 + (level - 1) * 0.1)
            for a in asteroids[:]:
                a.update(speed_mult)

                # برخورد تیر با سیارک
                for b in bullets[:]:
                    dist = math.hypot(a.x - b.x, a.y - b.y)
                    if dist < a.radius + b.radius:
                        if not b.piercing:
                            if b in bullets:
                                bullets.remove(b)
                        a.hit_flash = 5
                        # تقسیم
                        asteroids_destroyed += 1
                        total_asteroids[0] += 1
                        score += a.score_value
                        # ذرات
                        for _ in range(15):
                            spawn_particles(a.x, a.y, NEON_ORANGE, 1, 1.5, 1.2, 1.2)
                        if settings['screen_shake'] and a.size == 3:
                            screen_shake = 8
                        play_sound('big_explode' if a.size == 3 else 'explode')

                        # چک دستاورد
                        if asteroids_destroyed >= 1:
                            try_unlock('first_rock')
                        if asteroids_destroyed >= 10:
                            try_unlock('asteroid_10')
                        if asteroids_destroyed >= 50:
                            try_unlock('asteroid_50')
                        if asteroids_destroyed >= 200:
                            try_unlock('asteroid_200')

                        # تقسیم
                        if a.size > 1:
                            asteroids.extend(a.split())
                        if a in asteroids:
                            asteroids.remove(a)
                        if not b.piercing:
                            break

                # برخورد با سفینه
                if a in asteroids and ship.alive and ship.invincible == 0 and ship.shield == 0:
                    dist = math.hypot(a.x - ship.x, a.y - ship.y)
                    if dist < a.radius + ship.radius:
                        ship.alive = False

            # آپدیت UFO
            ufo_spawn_timer += 1
            if ufo_spawn_timer >= ufo_spawn_interval:
                ufo_spawn_timer = 0
                size = random.choice(['small', 'large'])
                ufos.append(UFO(size))
                play_sound('ufo')

            for ufo in ufos[:]:
                if not ufo.alive:
                    if ufo in ufos:
                        ufos.remove(ufo)
                    continue
                bullet = ufo.update((ship.x, ship.y))
                if bullet:
                    ufo_bullets.append(bullet)

                # برخورد تیر با UFO
                for b in bullets[:]:
                    dist = math.hypot(ufo.x - b.x, ufo.y - b.y)
                    if dist < ufo.radius + b.radius:
                        if not b.piercing:
                            if b in bullets:
                                bullets.remove(b)
                        ufo.hit_flash = 5
                        ufo.alive = False
                        ufos_destroyed += 1
                        total_ufos[0] += 1
                        score += ufo.score_value
                        play_sound('big_explode')
                        for _ in range(30):
                            spawn_particles(ufo.x, ufo.y, NEON_MAGENTA, 1, 1.8, 1.3, 1.3)
                        if ufos_destroyed >= 1:
                            try_unlock('ufo_kill')
                        if ufos_destroyed >= 5:
                            try_unlock('ufo_5')
                        break

                # برخورد با سفینه
                if ufo.alive and ship.alive and ship.invincible == 0 and ship.shield == 0:
                    dist = math.hypot(ufo.x - ship.x, ufo.y - ship.y)
                    if dist < ufo.radius + ship.radius:
                        ship.alive = False

            # برخورد UFO bullet با سفینه
            if ship.alive and ship.invincible == 0 and ship.shield == 0:
                for b in ufo_bullets[:]:
                    dist = math.hypot(b.x - ship.x, b.y - ship.y)
                    if dist < b.radius + ship.radius:
                        ufo_bullets.remove(b)
                        ship.alive = False
                        break

            # Magnet
            if ship.magnet > 0:
                for p in powerups[:]:
                    dx = ship.x - p.x
                    dy = ship.y - p.y
                    dist = math.hypot(dx, dy)
                    if dist < 200:
                        p.x += dx / dist * 3
                        p.y += dy / dist * 3

            # اسپاون Power-up
            powerup_spawn_timer -= 1
            if powerup_spawn_timer <= 0:
                powerup_spawn_timer = random.randint(FPS * 8, FPS * 15)
                if len(powerups) < 3 and asteroids_destroyed > 0:
                    x = random.uniform(50, WIDTH - 50)
                    y = random.uniform(50, HEIGHT - 50)
                    powerups.append(PowerUp(x, y))

            # آپدیت Power-ups
            for p in powerups[:]:
                p.update()
                if p.life <= 0:
                    powerups.remove(p)
                    continue
                if ship.alive:
                    dist = math.hypot(p.x - ship.x, p.y - ship.y)
                    if dist < p.radius + ship.radius:
                        # اعمال
                        powers_collected += 1
                        if p.type == 'shield':
                            ship.shield = 480
                        elif p.type == 'triple':
                            ship.triple_shot = 480
                        elif p.type == 'rapid':
                            ship.rapid_fire = 480
                        elif p.type == 'piercing':
                            ship.piercing = 480
                        elif p.type == 'magnet':
                            ship.magnet = 480
                        elif p.type == 'life':
                            # اضافه کردن جون - در این بازی فقط امتیاز
                            score += 500
                        play_sound('power')
                        for _ in range(20):
                            spawn_particles(p.x, p.y, NEON_GREEN, 1, 1.5, 1.2, 1.2)
                        if powers_collected >= 5:
                            try_unlock('power_5')
                        powerups.remove(p)

            # چک تموم شدن مرحله
            if len(asteroids) == 0 and len(ufos) == 0:
                level += 1
                if level >= 3:
                    try_unlock('level_3')
                if level >= 5:
                    try_unlock('level_5')
                if level >= 10:
                    try_unlock('level_10')
                play_sound('levelup')
                level_banner_timer = 90
                spawn_initial_asteroids(3 + level)

            # ذرات
            for p in active_particles[:]:
                p.update()
                if not p.active:
                    active_particles.remove(p)

            # افکت‌ها
            if screen_shake > 0:
                screen_shake -= 1
            if flash > 0:
                flash -= 8
            if level_banner_timer > 0:
                level_banner_timer -= 1

        # ============================================================
        #                    رسم
        # ============================================================
        game_surface.fill(BLACK)
        offset_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        offset_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0

        play_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        play_layer.blit(space_bg, (0, 0))

        # ذرات
        for p in active_particles:
            p.draw(play_layer)

        # Power-ups
        for p in powerups:
            p.draw(play_layer)

        # سیارک‌ها
        for a in asteroids:
            a.draw(play_layer)

        # UFOها
        for ufo in ufos:
            ufo.draw(play_layer)

        # تیرها
        for b in bullets:
            b.draw(play_layer)

        # UFO bullets
        for b in ufo_bullets:
            b.draw(play_layer)

        # سفینه
        if ship.alive:
            ship.draw(play_layer)

        if flash > 0:
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 200, 100, flash))
            play_layer.blit(fs, (0, 0))

        game_surface.blit(play_layer, (offset_x, offset_y))

        # ============================================================
        #                    HUD
        # ============================================================
        # پنل بالا
        hud_panel = pygame.Surface((WIDTH, 90), pygame.SRCALPHA)
        for y in range(90):
            alpha = int(180 * (1 - y / 90))
            pygame.draw.line(hud_panel, (5, 10, 25, alpha), (0, y), (WIDTH, y))
        game_surface.blit(hud_panel, (0, 0))
        pygame.draw.line(game_surface, NEON_CYAN, (0, 90), (WIDTH, 90), 1)

        # عنوان
        draw_text(game_surface, "ASTEROID", 22, 25, 15, WHITE)
        draw_text(game_surface, "HUNTER", 22, 25 + get_font(22).size("ASTEROID ")[0], 15, NEON_CYAN, glow=True)
        draw_text(game_surface, "ROTATE / SHOOT / SURVIVE", 12, 25, 45, (180, 200, 220))

        # SCORE
        draw_text(game_surface, "SCORE", 14, WIDTH - 25, 12, NEON_CYAN)
        draw_text(game_surface, f"{display_score}", 26, WIDTH - 25, 30, WHITE, glow=True)

        # LEVEL
        draw_text(game_surface, f"LEVEL: {level}", 16, WIDTH - 25, 62, NEON_GREEN)
        draw_text(game_surface, f"ROCKS: {asteroids_destroyed}", 14, WIDTH - 25, 84, NEON_YELLOW)

        # LIVES (با آیکون)
        lives_text = "LIVES: " + ("|" * max(0, 1 if ship.alive else 0))
        draw_text(game_surface, lives_text, 14, WIDTH // 2, 15, NEON_PINK)

        # Banner مرحله جدید
        if level_banner_timer > 0:
            alpha = min(255, level_banner_timer * 4)
            size = 60 + int(math.sin(t * 10) * 5)
            draw_text(game_surface, f"LEVEL {level}", size, WIDTH // 2, HEIGHT // 2 - 50,
                      NEON_CYAN, center=True, glow=True)
            draw_text(game_surface, "GET READY!", 30, WIDTH // 2, HEIGHT // 2 + 20,
                      WHITE, center=True)

        # Notifications
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
            pygame.draw.rect(game_surface, NEON_PINK, (box_x, box_y, box_w, box_h), 3)
            pygame.draw.rect(game_surface, NEON_CYAN, (box_x + 5, box_y + 5, box_w - 10, box_h - 10), 1)
            draw_text(game_surface, "GAME OVER", 60, WIDTH // 2, box_y + 55,
                      NEON_RED, center=True, glow=True)
            draw_text(game_surface, f"SCORE: {final_score}", 32, WIDTH // 2, box_y + 120,
                      WHITE, center=True)
            draw_text(game_surface, f"LEVEL: {final_level}   ROCKS: {asteroids_destroyed}   UFOs: {ufos_destroyed}",
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