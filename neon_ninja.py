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
pygame.display.set_caption("NEON NINJA")
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
GRAVITY = 0.7
JUMP_FORCE = -14
WALL_JUMP_FORCE_X = 8
WALL_JUMP_FORCE_Y = -13
MAX_FALL_SPEED = 18
GROUND_Y = HEIGHT - 80

# --- ذخیره ---
SAVE_FILE = "neon_ninja_save.json"
settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'difficulty': 1.0,
    'screen_shake': True,
}
achievements = {
    'first_kill': {'name': 'FIRST BLOOD', 'desc': 'Defeat your first enemy', 'unlocked': False, 'icon': '*'},
    'kill_10': {'name': 'ROOKIE', 'desc': 'Defeat 10 enemies', 'unlocked': False, 'icon': '**'},
    'kill_50': {'name': 'VETERAN', 'desc': 'Defeat 50 enemies', 'unlocked': False, 'icon': '***'},
    'kill_100': {'name': 'MASTER', 'desc': 'Defeat 100 enemies', 'unlocked': False, 'icon': '****'},
    'combo_5': {'name': 'COMBO KING', 'desc': 'Reach 5x combo', 'unlocked': False, 'icon': 'C5'},
    'combo_10': {'name': 'COMBO GOD', 'desc': 'Reach 10x combo', 'unlocked': False, 'icon': 'C10'},
    'wall_jump': {'name': 'SPIDER NINJA', 'desc': 'Perform a wall jump', 'unlocked': False, 'icon': 'W'},
    'dash_master': {'name': 'DASH MASTER', 'desc': 'Use dash 10 times', 'unlocked': False, 'icon': 'D'},
    'shuriken_20': {'name': 'SHARPSHOOTER', 'desc': 'Throw 20 shurikens', 'unlocked': False, 'icon': 'S'},
    'slow_mo': {'name': 'TIME BENDER', 'desc': 'Use slow motion', 'unlocked': False, 'icon': 'T'},
    'level_3': {'name': 'EXPLORER', 'desc': 'Reach level 3', 'unlocked': False, 'icon': 'L3'},
    'level_5': {'name': 'ADVENTURER', 'desc': 'Reach level 5', 'unlocked': False, 'icon': 'L5'},
    'score_5000': {'name': 'HUNTER', 'desc': 'Score 5000 points', 'unlocked': False, 'icon': '$5K'},
    'score_20000': {'name': 'ACE', 'desc': 'Score 20000 points', 'unlocked': False, 'icon': '$20K'},
    'boss_kill': {'name': 'DEMON SLAYER', 'desc': 'Defeat the Oni boss', 'unlocked': False, 'icon': 'B'},
}
highscore = [0]
game_history = []
total_kills = [0]
total_bosses = [0]


def load_save():
    global settings, achievements, highscore, game_history, total_kills, total_bosses
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
                'total_kills': total_kills[0],
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
    sounds['jump'] = make_sound(600, 900, 0.1, 0.15, 'sine')
    sounds['slash'] = make_sound(1200, 600, 0.1, 0.18, 'saw')
    sounds['hit'] = make_sound(400, 100, 0.15, 0.22, 'noise')
    sounds['kill'] = make_sound(800, 200, 0.25, 0.25, 'saw')
    sounds['dash'] = make_sound(300, 800, 0.15, 0.18, 'sine')
    sounds['shuriken'] = make_sound(1000, 1500, 0.08, 0.15, 'square')
    sounds['slowmo'] = make_sound(800, 200, 0.4, 0.20, 'sine')
    sounds['damage'] = make_sound(200, 60, 0.3, 0.28, 'noise')
    sounds['gameover'] = make_sound(500, 60, 1.2, 0.30, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['levelup'] = make_sound(500, 1500, 0.5, 0.25, 'sine')
    sounds['boss'] = make_sound(150, 400, 1.0, 0.28, 'saw')

    bass = [73.4, 73.4, 82.4, 82.4, 65.4, 65.4, 73.4, 73.4]
    lead = [587, 698, 880, 698, 587, 523, 466, 523]
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
#                    پلتفرم
# ============================================================
class Platform:
    def __init__(self, x, y, w, h=20):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface):
        pygame.draw.rect(surface, (*NEON_CYAN, 60), self.rect, border_radius=4)
        pygame.draw.rect(surface, (15, 30, 50), self.rect, border_radius=4)
        pygame.draw.rect(surface, NEON_CYAN, self.rect, 2, border_radius=4)
        pygame.draw.line(surface, WHITE, (self.rect.x + 4, self.rect.y + 2),
                         (self.rect.right - 4, self.rect.y + 2), 1)


# ============================================================
#                    شوریکن
# ============================================================
class Shuriken:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = 8
        self.life = 120
        self.rotation = 0
        self.trail = []

    def update(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 6:
            self.trail.pop(0)
        self.x += self.vx
        self.y += self.vy
        self.rotation += 25
        self.life -= 1

    def draw(self, surface):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / len(self.trail) * 0.7
            r = max(1, int(self.radius * alpha))
            pygame.draw.circle(surface, NEON_YELLOW, (int(tx), int(ty)), r)

        glow = pygame.Surface((self.radius * 6, self.radius * 6), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*NEON_YELLOW, 80), (self.radius * 3, self.radius * 3), self.radius * 2)
        surface.blit(glow, (self.x - self.radius * 3, self.y - self.radius * 3))

        rad = math.radians(self.rotation)
        for i in range(4):
            a = rad + i * math.pi / 2
            pts = [
                (self.x + math.cos(a) * self.radius, self.y + math.sin(a) * self.radius),
                (self.x + math.cos(a + 0.4) * self.radius * 0.4,
                 self.y + math.sin(a + 0.4) * self.radius * 0.4),
                (self.x + math.cos(a - 0.4) * self.radius * 0.4,
                 self.y + math.sin(a - 0.4) * self.radius * 0.4),
            ]
            pygame.draw.polygon(surface, NEON_YELLOW, pts)
            pygame.draw.polygon(surface, WHITE, pts, 1)

        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 3)


# ============================================================
#                    Ninja (Player)
# ============================================================
class Ninja:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.w = 30
        self.h = 50
        self.facing = 1
        self.on_ground = False
        self.on_wall = 0
        self.jumps_left = 2
        self.hp = 100
        self.max_hp = 100
        self.lives = 3
        self.invincible = 0
        self.attack_timer = 0
        self.attack_combo = 0
        self.attack_cooldown = 0
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.slowmo_timer = 0
        self.anim_time = 0
        self.hit_flash = 0
        self.hit_enemies_this_attack = []

    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h), self.w, self.h)

    def attack_rect(self):
        if self.attack_timer <= 0:
            return None
        range_w = 55
        if self.facing == 1:
            return pygame.Rect(int(self.x), int(self.y - self.h + 10), range_w, self.h - 20)
        else:
            return pygame.Rect(int(self.x - range_w), int(self.y - self.h + 10), range_w, self.h - 20)

    def update(self, keys, platforms):
        if self.slowmo_timer > 0:
            self.slowmo_timer -= 1
            time_mult = 0.4
        else:
            time_mult = 1.0

        if self.invincible > 0:
            self.invincible -= 1
        if self.attack_timer > 0:
            self.attack_timer -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if self.hit_flash > 0:
            self.hit_flash -= 1
        self.anim_time += 1 * time_mult

        if self.dash_timer > 0:
            self.dash_timer -= 1
            self.vx = self.facing * 15 * time_mult
        else:
            speed = 5
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vx = -speed * time_mult
                self.facing = -1
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vx = speed * time_mult
                self.facing = 1
            else:
                self.vx *= 0.7

        self.vy += GRAVITY * time_mult
        if self.vy > MAX_FALL_SPEED * time_mult:
            self.vy = MAX_FALL_SPEED * time_mult

        if self.on_wall != 0 and not self.on_ground and self.vy > 0:
            self.vy *= 0.5

        self.x += self.vx
        self.y += self.vy

        self.x = max(20, min(WIDTH - 20, self.x))

        self.on_ground = False
        self.on_wall = 0
        rect = self.rect()

        for plat in platforms:
            if rect.colliderect(plat.rect):
                if self.vy > 0 and rect.bottom - self.vy <= plat.rect.top + 5:
                    self.y = plat.rect.top
                    self.vy = 0
                    self.on_ground = True
                    self.jumps_left = 2
                elif self.vy < 0 and rect.top - self.vy >= plat.rect.bottom - 5:
                    self.y = plat.rect.bottom + self.h
                    self.vy = 0

        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vy = 0
            self.on_ground = True
            self.jumps_left = 2

        if self.x <= 25 or self.x >= WIDTH - 25:
            if not self.on_ground:
                self.on_wall = -1 if self.x <= 25 else 1
                self.jumps_left = 2

    def jump(self):
        if self.on_wall != 0:
            self.vy = WALL_JUMP_FORCE_Y
            self.vx = WALL_JUMP_FORCE_X * (-self.on_wall)
            self.facing = -self.on_wall
            self.jumps_left = 1
            self.on_wall = 0
            play_sound('jump')
            return 'wall'
        elif self.on_ground:
            self.vy = JUMP_FORCE
            self.on_ground = False
            self.jumps_left = 1
            play_sound('jump')
            return 'ground'
        elif self.jumps_left > 0:
            self.vy = JUMP_FORCE * 0.9
            self.jumps_left -= 1
            play_sound('jump')
            return 'double'
        return None

    def attack(self):
        if self.attack_cooldown > 0:
            return False
        self.attack_timer = 12
        self.attack_combo = (self.attack_combo + 1) % 3
        self.attack_cooldown = 18
        self.hit_enemies_this_attack = []
        play_sound('slash')
        ax = self.x + self.facing * 30
        ay = self.y - self.h / 2
        for _ in range(8):
            spawn_particles(ax, ay, NEON_CYAN, 1, 1.2, 0.8, 0.8, gravity=0.1)
        return True

    def dash(self):
        if self.dash_cooldown > 0:
            return False
        self.dash_timer = 12
        self.dash_cooldown = 40
        self.invincible = max(self.invincible, 15)
        play_sound('dash')
        for _ in range(15):
            spawn_particles(self.x, self.y - self.h / 2, NEON_PURPLE, 1, 1.5, 1.0, 1.0, gravity=0)
        return True

    def throw_shuriken(self):
        sx = self.x + self.facing * 15
        sy = self.y - self.h / 2
        vx = self.facing * 12
        vy = -1
        play_sound('shuriken')
        return Shuriken(sx, sy, vx, vy)

    def take_damage(self, amount):
        if self.invincible > 0:
            return
        self.hp -= amount
        self.invincible = 60
        self.hit_flash = 15
        play_sound('damage')
        if self.hp <= 0:
            self.lives -= 1
            self.hp = self.max_hp
            self.invincible = 120
            if self.lives <= 0:
                return 'dead'
        return 'hit'

    def draw(self, surface):
        if self.invincible > 0 and (self.invincible // 4) % 2 == 0:
            return

        for r in range(3, 0, -1):
            glow = pygame.Surface((self.w * 4, self.h * 2), pygame.SRCALPHA)
            color = NEON_RED if self.hit_flash > 0 else NEON_CYAN
            pygame.draw.ellipse(glow, (*color, 40 - r * 10),
                                (self.w * 2 - r * 5, self.h - r * 5,
                                 self.w + r * 10, self.h + r * 10))
            surface.blit(glow, (self.x - self.w * 2, self.y - self.h * 2 + 20))

        body_color = WHITE if self.hit_flash > 0 else NEON_CYAN
        accent_color = NEON_PURPLE

        leg_offset = math.sin(self.anim_time * 0.3) * 3 if abs(self.vx) > 1 else 0
        pygame.draw.line(surface, body_color,
                         (self.x - 5, self.y - 15),
                         (self.x - 5 + leg_offset, self.y), 4)
        pygame.draw.line(surface, body_color,
                         (self.x + 5, self.y - 15),
                         (self.x + 5 - leg_offset, self.y), 4)

        body_rect = pygame.Rect(int(self.x - 10), int(self.y - 45), 20, 30)
        pygame.draw.rect(surface, (10, 40, 80), body_rect, border_radius=4)
        pygame.draw.rect(surface, body_color, body_rect, 2, border_radius=4)

        scarf_offset = math.sin(self.anim_time * 0.2) * 5
        scarf_pts = [
            (self.x - self.facing * 5, self.y - 42),
            (self.x - self.facing * 20, self.y - 38 + scarf_offset),
            (self.x - self.facing * 30, self.y - 30 + scarf_offset * 1.5),
        ]
        pygame.draw.lines(surface, NEON_PINK, False, scarf_pts, 4)

        head_rect = pygame.Rect(int(self.x - 10), int(self.y - 60), 20, 18)
        pygame.draw.rect(surface, (15, 50, 90), head_rect, border_radius=5)
        pygame.draw.rect(surface, body_color, head_rect, 2, border_radius=5)

        eye_y = self.y - 52
        if self.facing == 1:
            pygame.draw.line(surface, NEON_PINK, (self.x + 2, eye_y), (self.x + 8, eye_y), 3)
        else:
            pygame.draw.line(surface, NEON_PINK, (self.x - 8, eye_y), (self.x - 2, eye_y), 3)

        sword_base_x = self.x + self.facing * 10
        sword_base_y = self.y - 35

        if self.attack_timer > 0:
            sword_angle = -45 * self.facing
            sword_len = 50
            end_x = sword_base_x + math.cos(math.radians(sword_angle if self.facing == 1 else 180 - sword_angle)) * sword_len
            end_y = sword_base_y + math.sin(math.radians(sword_angle if self.facing == 1 else 180 - sword_angle)) * sword_len
            for r in range(3, 0, -1):
                pygame.draw.line(surface, (*NEON_CYAN, 60 - r * 15),
                                 (sword_base_x, sword_base_y), (end_x, end_y), 6 + r * 2)
            pygame.draw.line(surface, WHITE, (sword_base_x, sword_base_y), (end_x, end_y), 4)
            pygame.draw.line(surface, NEON_CYAN, (sword_base_x, sword_base_y), (end_x, end_y), 2)
        else:
            end_x = self.x - self.facing * 20
            end_y = self.y - 20
            pygame.draw.line(surface, (60, 60, 80), (sword_base_x, sword_base_y), (end_x, end_y), 3)
            pygame.draw.line(surface, WHITE, (sword_base_x, sword_base_y), (end_x, end_y), 1)

        if self.hp < self.max_hp:
            bar_w = 40
            bar_x = self.x - bar_w / 2
            bar_y = self.y - self.h - 15
            pygame.draw.rect(surface, (40, 10, 10), (bar_x, bar_y, bar_w, 4))
            ratio = self.hp / self.max_hp
            hp_color = NEON_GREEN if ratio > 0.5 else NEON_YELLOW if ratio > 0.25 else NEON_RED
            pygame.draw.rect(surface, hp_color, (bar_x, bar_y, bar_w * ratio, 4))


# ============================================================
#                    دشمنان
# ============================================================
class Enemy:
    def __init__(self, x, y, kind='samurai'):
        self.x = x
        self.y = y
        self.kind = kind
        self.vx = 0
        self.vy = 0
        self.facing = -1
        self.hit_flash = 0
        self.attack_timer = 0
        self.attack_cooldown = 0
        self.shoot_timer = 0
        self.anim_time = 0
        self.alive = True
        self.jump_cooldown = 0

        if kind == 'samurai':
            self.w = 30
            self.h = 50
            self.hp = 30
            self.max_hp = 30
            self.speed = 2
            self.color = NEON_RED
            self.detection_range = 300
            self.attack_range = 50
        elif kind == 'robot':
            self.w = 30
            self.h = 45
            self.hp = 20
            self.max_hp = 20
            self.speed = 1
            self.color = NEON_ORANGE
            self.detection_range = 400
            self.shoot_interval = 90
        elif kind == 'ninja_ai':
            self.w = 28
            self.h = 48
            self.hp = 25
            self.max_hp = 25
            self.speed = 3
            self.color = NEON_MAGENTA
            self.detection_range = 400
            self.attack_range = 45

    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h), self.w, self.h)

    def update(self, player, platforms):
        if not self.alive:
            return None

        self.anim_time += 1
        if self.hit_flash > 0:
            self.hit_flash -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.attack_timer > 0:
            self.attack_timer -= 1
        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist < self.detection_range and player.invincible < 30:
            self.facing = 1 if dx > 0 else -1

            if self.kind == 'samurai':
                if abs(dx) > self.attack_range:
                    self.vx = self.facing * self.speed
                else:
                    self.vx = 0
                    if self.attack_cooldown == 0:
                        self.attack_timer = 15
                        self.attack_cooldown = 60
                # پرش اگه بازیکن بالاتره
                if self.on_ground_check(platforms) and dy < -30 and self.jump_cooldown == 0:
                    if random.random() < 0.04:
                        self.vy = -13
                        self.jump_cooldown = 60
                        for _ in range(6):
                            spawn_particles(self.x, self.y, self.color, 1, 0.8, 0.8, 0.5)
                self.vy += GRAVITY
                self.y += self.vy
                self.x += self.vx

            elif self.kind == 'robot':
                self.vx = 0
                # پرش فرار
                if self.on_ground_check(platforms) and dist < 150 and self.jump_cooldown == 0:
                    if random.random() < 0.015:
                        self.vy = -12
                        self.jump_cooldown = 90
                        for _ in range(6):
                            spawn_particles(self.x, self.y, self.color, 1, 0.8, 0.8, 0.5)
                self.vy += GRAVITY
                self.y += self.vy
                self.shoot_timer += 1
                if self.shoot_timer >= self.shoot_interval and abs(dx) < self.detection_range:
                    self.shoot_timer = 0
                    return 'shoot'

            elif self.kind == 'ninja_ai':
                if abs(dx) > self.attack_range:
                    self.vx = self.facing * self.speed
                else:
                    self.vx = 0
                    if self.attack_cooldown == 0:
                        self.attack_timer = 12
                        self.attack_cooldown = 45
                self.vy += GRAVITY
                self.y += self.vy
                self.x += self.vx

                # پرش هوشمند نینجا
                if self.on_ground_check(platforms) and self.jump_cooldown == 0:
                    should_jump = False
                    if dy < -40:
                        should_jump = True
                    elif abs(dx) > 100 and random.random() < 0.035:
                        should_jump = True
                    elif random.random() < 0.02:
                        should_jump = True

                    if should_jump:
                        self.vy = -13
                        self.jump_cooldown = 45
                        for _ in range(6):
                            spawn_particles(self.x, self.y, self.color, 1, 0.8, 0.8, 0.5)

        else:
            self.vx = self.facing * self.speed * 0.3
            self.vy += GRAVITY
            self.y += self.vy
            self.x += self.vx
            # پرش تصادفی موقع گشت
            if self.on_ground_check(platforms) and self.jump_cooldown == 0 and random.random() < 0.008:
                self.vy = -11
                self.jump_cooldown = 120

        for plat in platforms:
            rect = self.rect()
            if rect.colliderect(plat.rect):
                if self.vy > 0 and rect.bottom - self.vy <= plat.rect.top + 5:
                    self.y = plat.rect.top
                    self.vy = 0

        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vy = 0

        self.x = max(30, min(WIDTH - 30, self.x))

        return None

    def on_ground_check(self, platforms):
        rect = self.rect()
        rect.y += 5
        for plat in platforms:
            if rect.colliderect(plat.rect):
                return True
        return self.y >= GROUND_Y - 5

    def take_damage(self, amount):
        self.hp -= amount
        self.hit_flash = 12
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surface):
        if not self.alive:
            return

        color = WHITE if self.hit_flash > 0 else self.color

        for r in range(3, 0, -1):
            glow = pygame.Surface((self.w * 4, self.h * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*color, 30 - r * 8),
                                (self.w * 2 - r * 5, self.h - r * 5,
                                 self.w + r * 10, self.h + r * 10))
            surface.blit(glow, (self.x - self.w * 2, self.y - self.h * 2 + 20))

        body_rect = pygame.Rect(int(self.x - 12), int(self.y - 40), 24, 30)
        pygame.draw.rect(surface, (color[0] // 3, color[1] // 3, color[2] // 3), body_rect, border_radius=4)
        pygame.draw.rect(surface, color, body_rect, 2, border_radius=4)

        head_rect = pygame.Rect(int(self.x - 10), int(self.y - 55), 20, 18)
        pygame.draw.rect(surface, (color[0] // 3, color[1] // 3, color[2] // 3), head_rect, border_radius=5)
        pygame.draw.rect(surface, color, head_rect, 2, border_radius=5)

        eye_color = NEON_YELLOW if self.kind == 'robot' else NEON_RED
        if self.facing == 1:
            pygame.draw.circle(surface, eye_color, (int(self.x + 4), int(self.y - 46)), 3)
        else:
            pygame.draw.circle(surface, eye_color, (int(self.x - 4), int(self.y - 46)), 3)

        if self.kind == 'samurai':
            if self.attack_timer > 0:
                ex = self.x + self.facing * 40
                ey = self.y - 30
                pygame.draw.line(surface, WHITE, (self.x + self.facing * 10, self.y - 30), (ex, ey), 4)
                pygame.draw.line(surface, color, (self.x + self.facing * 10, self.y - 30), (ex, ey), 2)
            else:
                pygame.draw.line(surface, (100, 100, 120),
                                 (self.x + self.facing * 10, self.y - 30),
                                 (self.x + self.facing * 25, self.y - 15), 3)
        elif self.kind == 'robot':
            pygame.draw.line(surface, color,
                             (self.x + self.facing * 10, self.y - 30),
                             (self.x + self.facing * 25, self.y - 30), 5)

        bar_w = 40
        bar_x = self.x - bar_w / 2
        bar_y = self.y - self.h - 12
        pygame.draw.rect(surface, (40, 10, 10), (bar_x, bar_y, bar_w, 4))
        ratio = self.hp / self.max_hp
        pygame.draw.rect(surface, NEON_RED, (bar_x, bar_y, bar_w * ratio, 4))


# ============================================================
#                    باس: Oni
# ============================================================
class OniBoss:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = 80
        self.h = 120
        self.vx = 0
        self.vy = 0
        self.facing = -1
        self.hp = 300
        self.max_hp = 300
        self.phase = 1
        self.hit_flash = 0
        self.anim_time = 0
        self.alive = True
        self.attack_timer = 0
        self.attack_cooldown = 0
        self.dash_timer = 0
        self.charge_timer = 0
        self.shoot_timer = 0

    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h), self.w, self.h)

    def update(self, player):
        if not self.alive:
            return None

        self.anim_time += 1
        if self.hit_flash > 0:
            self.hit_flash -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.attack_timer > 0:
            self.attack_timer -= 1

        ratio = self.hp / self.max_hp
        if ratio > 0.66:
            self.phase = 1
        elif ratio > 0.33:
            self.phase = 2
        else:
            self.phase = 3

        dx = player.x - self.x
        dist = abs(dx)
        self.facing = 1 if dx > 0 else -1

        actions = []

        if self.phase == 1:
            if dist > 80:
                self.x += self.facing * 2
            else:
                if self.attack_cooldown == 0:
                    self.attack_timer = 20
                    self.attack_cooldown = 70
                    actions.append('slash')

        elif self.phase == 2:
            if dist > 60:
                self.x += self.facing * 3
            if self.attack_cooldown == 0:
                if random.random() < 0.5:
                    self.attack_timer = 15
                    self.attack_cooldown = 50
                    actions.append('slash')
                else:
                    self.vy = -15
                    self.attack_cooldown = 60
                    actions.append('jump')

        else:
            if self.charge_timer > 0:
                self.charge_timer -= 1
                self.x += self.facing * 8
            else:
                if dist > 50:
                    self.x += self.facing * 4
                if self.attack_cooldown == 0:
                    action = random.choice(['slash', 'dash', 'shoot'])
                    if action == 'slash':
                        self.attack_timer = 12
                        self.attack_cooldown = 40
                        actions.append('slash')
                    elif action == 'dash':
                        self.charge_timer = 20
                        self.attack_cooldown = 80
                        actions.append('dash')
                    else:
                        self.attack_cooldown = 60
                        actions.append('shoot')

        self.vy += GRAVITY
        self.y += self.vy
        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vy = 0

        self.x = max(80, min(WIDTH - 80, self.x))

        return actions

    def take_damage(self, amount):
        self.hp -= amount
        self.hit_flash = 12
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surface):
        if not self.alive:
            return

        if self.phase == 1:
            color = NEON_RED
        elif self.phase == 2:
            color = NEON_ORANGE
        else:
            color = NEON_MAGENTA

        if self.hit_flash > 0:
            color = WHITE

        for r in range(5, 0, -1):
            glow = pygame.Surface((self.w * 6, self.h * 3), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*color, 40 - r * 6),
                                (self.w * 3 - r * 10, self.h - r * 10,
                                 self.w + r * 20, self.h + r * 20))
            surface.blit(glow, (self.x - self.w * 3, self.y - self.h * 3 + 50))

        body_rect = pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h + 20),
                                self.w, self.h - 20)
        pygame.draw.rect(surface, (color[0] // 4, color[1] // 4, color[2] // 4),
                         body_rect, border_radius=10)
        pygame.draw.rect(surface, color, body_rect, 3, border_radius=10)
        pygame.draw.rect(surface, WHITE, body_rect, 1, border_radius=10)

        horn_pts_l = [
            (self.x - 20, self.y - self.h + 20),
            (self.x - 35, self.y - self.h - 20),
            (self.x - 15, self.y - self.h + 15),
        ]
        horn_pts_r = [
            (self.x + 20, self.y - self.h + 20),
            (self.x + 35, self.y - self.h - 20),
            (self.x + 15, self.y - self.h + 15),
        ]
        pygame.draw.polygon(surface, color, horn_pts_l)
        pygame.draw.polygon(surface, color, horn_pts_r)
        pygame.draw.polygon(surface, WHITE, horn_pts_l, 2)
        pygame.draw.polygon(surface, WHITE, horn_pts_r, 2)

        for ex in [-15, 15]:
            eye_glow = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(eye_glow, (*NEON_YELLOW, 200), (15, 15), 12)
            surface.blit(eye_glow, (self.x + ex - 15, self.y - self.h + 45))
            pygame.draw.circle(surface, NEON_YELLOW, (int(self.x + ex), int(self.y - self.h + 60)), 6)
            pygame.draw.circle(surface, WHITE, (int(self.x + ex), int(self.y - self.h + 60)), 3)

        mouth_y = self.y - self.h + 90
        for i in range(5):
            px = self.x - 30 + i * 15
            pygame.draw.polygon(surface, color, [
                (px, mouth_y),
                (px + 10, mouth_y),
                (px + 5, mouth_y + 8),
            ])

        if self.attack_timer > 0:
            ex = self.x + self.facing * 80
            ey = self.y - 60
            for r in range(3, 0, -1):
                pygame.draw.line(surface, (*color, 100 - r * 25),
                                 (self.x + self.facing * 20, self.y - 60), (ex, ey), 8 + r * 3)
            pygame.draw.line(surface, WHITE, (self.x + self.facing * 20, self.y - 60), (ex, ey), 6)

        bar_w = 500
        bar_x = WIDTH // 2 - bar_w // 2
        bar_y = 100
        pygame.draw.rect(surface, (40, 10, 10), (bar_x - 2, bar_y - 2, bar_w + 4, 24))
        pygame.draw.rect(surface, (60, 15, 15), (bar_x, bar_y, bar_w, 20))
        ratio = self.hp / self.max_hp
        pygame.draw.rect(surface, color, (bar_x, bar_y, int(bar_w * ratio), 20))
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, 20), 2)
        draw_text(surface, f"ONI BOSS  PHASE {self.phase}", 16,
                  WIDTH // 2, bar_y - 25, color, center=True, glow=True)


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
#                    پس‌زمینه پارالاکس
# ============================================================
def build_parallax_bg():
    layers = []
    surf1 = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for _ in range(80):
        x, y = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        b = random.randint(80, 150)
        pygame.draw.circle(surf1, (b, b, b + 40), (x, y), random.choice([1, 1, 2]))
    layers.append({'surf': surf1, 'speed': 0.1, 'offset': 0})

    surf2 = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(surf2, (150, 100, 180, 200), (700, 150), 60)
    pygame.draw.circle(surf2, (200, 150, 220, 220), (700, 150), 55)
    pygame.draw.circle(surf2, (180, 130, 200, 255), (700, 150), 50)
    for _ in range(8):
        mx = 700 + random.randint(-40, 40)
        my = 150 + random.randint(-40, 40)
        r = random.randint(3, 8)
        pygame.draw.circle(surf2, (140, 100, 170, 200), (mx, my), r)
    for i in range(15):
        bx = i * 80 - 100
        bh = random.randint(100, 250)
        by = HEIGHT - 200 - bh
        pygame.draw.rect(surf2, (15, 10, 35), (bx, by, 60, bh))
        for _ in range(random.randint(3, 8)):
            wx = bx + random.randint(5, 50)
            wy = by + random.randint(10, bh - 20)
            color = random.choice([(80, 0, 100), (60, 0, 80), (100, 20, 120)])
            pygame.draw.rect(surf2, color, (wx, wy, 4, 6))
    layers.append({'surf': surf2, 'speed': 0.3, 'offset': 0})

    surf3 = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(12):
        bx = i * 100 - 100
        bh = random.randint(150, 350)
        by = HEIGHT - 150 - bh
        pygame.draw.rect(surf3, (8, 5, 20), (bx, by, 90, bh))
        for _ in range(random.randint(5, 12)):
            wx = bx + random.randint(5, 80)
            wy = by + random.randint(10, bh - 20)
            color = random.choice([NEON_CYAN, NEON_PINK, NEON_PURPLE, NEON_BLUE])
            pygame.draw.rect(surf3, color, (wx, wy, 4, 6))
    layers.append({'surf': surf3, 'speed': 0.6, 'offset': 0})

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

    menu_layers = build_parallax_bg()

    while True:
        game_surface.fill(DARK_BG)
        t = pygame.time.get_ticks() / 1000
        menu_time += 1
        mouse_pos = get_game_mouse_pos()

        for layer in menu_layers:
            layer['offset'] += layer['speed']
            if layer['offset'] > WIDTH:
                layer['offset'] -= WIDTH
            game_surface.blit(layer['surf'], (-layer['offset'], 0))
            game_surface.blit(layer['surf'], (WIDTH - layer['offset'], 0))

        pygame.draw.rect(game_surface, (10, 5, 20), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.line(game_surface, NEON_PURPLE, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)
        pygame.draw.line(game_surface, NEON_PINK, (0, GROUND_Y + 3), (WIDTH, GROUND_Y + 3), 1)

        title_y = 130 + math.sin(t * 2) * 8
        draw_text(game_surface, "NEON", 72, WIDTH // 2 - 100, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "NINJA", 72, WIDTH // 2 + 120, title_y, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, "SLASH  /  DASH  /  SURVIVE", 20, WIDTH // 2, title_y + 65,
                  (200, 200, 220), center=True)

        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 22, WIDTH // 2, title_y + 115,
                      NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, f"KILLS: {total_kills[0]}   BOSSES: {total_bosses[0]}",
                  14, WIDTH // 2, title_y + 145, NEON_PINK, center=True)

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

        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((15, 5, 35, alpha))
            game_surface.blit(s, (0, y))
        for _ in range(80):
            pygame.draw.circle(game_surface, (80, 100, 150),
                               (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 1)

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
                total_kills[0] = 0
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
    platforms = [
        Platform(100, GROUND_Y - 120, 200),
        Platform(400, GROUND_Y - 200, 200),
        Platform(700, GROUND_Y - 150, 200),
        Platform(250, GROUND_Y - 320, 150),
        Platform(550, GROUND_Y - 380, 150),
        Platform(800, GROUND_Y - 280, 150),
    ]

    ninja = Ninja(100, GROUND_Y)

    enemies = []
    shurikens = []
    enemy_shots = []
    powerups = []

    score = 0
    display_score = 0
    kills = 0
    max_combo = 0
    combo = 0
    combо_timer = 0
    total_frames = 0
    level = 1
    level_kills_needed = 5
    level_kills = 0

    slowmo_energy = 100
    slowmo_active = 0

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

    boss = None
    boss_spawned = False

    enemy_spawn_timer = 0
    powerup_spawn_timer = FPS * 10
    level_banner_timer = 90

    btn_resume = Button(WIDTH // 2, HEIGHT // 2 + 20, 300, 60, "RESUME", NEON_GREEN, NEON_CYAN, 28)
    btn_pause_menu = Button(WIDTH // 2, HEIGHT // 2 + 100, 300, 55, "MAIN MENU", NEON_RED, NEON_ORANGE, 24)
    btn_restart = Button(WIDTH // 2, HEIGHT // 2 + 70, 300, 60, "RESTART", NEON_CYAN, NEON_GREEN, 28)
    btn_menu = Button(WIDTH // 2, HEIGHT // 2 + 145, 300, 55, "MAIN MENU", NEON_YELLOW, NEON_ORANGE, 24)

    active_particles.clear()
    for p in particle_pool:
        p.active = False

    bg_layers = build_parallax_bg()

    start_music()

    def try_unlock(key):
        if unlock_achievement(key):
            new_achs.append(achievements[key]['name'])
            notifications.append({'ach': achievements[key], 'timer': 180})
            return True
        return False

    def save_current():
        add_game_to_history(score, level, total_frames // FPS, new_achs)

    def spawn_enemy():
        side = random.choice([-1, 1])
        ex = -50 if side == -1 else WIDTH + 50
        kind = random.choices(['samurai', 'robot', 'ninja_ai'], weights=[4, 3, 2])[0]
        enemies.append(Enemy(ex, GROUND_Y, kind))

    def process_attack_hits():
        """هر فریم که attack_timer > 0، چک کن به کی خورده"""
        nonlocal kills, score, combo, combо_timer, max_combo, level_kills, boss, flash, screen_shake

        if ninja.attack_timer <= 0:
            return
        atk_rect = ninja.attack_rect()
        if not atk_rect:
            return

        for e in enemies[:]:
            if id(e) in ninja.hit_enemies_this_attack:
                continue
            if atk_rect.colliderect(e.rect()):
                ninja.hit_enemies_this_attack.append(id(e))
                if e.take_damage(15):
                    kills += 1
                    total_kills[0] += 1
                    level_kills += 1
                    combo += 1
                    combо_timer = 90
                    max_combo = max(max_combo, combo)
                    combo_mult = 1 + (combo - 1) * 0.2
                    score += int(100 * combo_mult)
                    for _ in range(30):
                        spawn_particles(e.x, e.y - e.h / 2, e.color, 1, 2.0, 1.5, 1.5)
                    play_sound('kill')
                    if settings['screen_shake']:
                        screen_shake = 8
                    enemies.remove(e)
                    if kills >= 1: try_unlock('first_kill')
                    if kills >= 10: try_unlock('kill_10')
                    if kills >= 50: try_unlock('kill_50')
                    if kills >= 100: try_unlock('kill_100')
                    if combo >= 5: try_unlock('combo_5')
                    if combo >= 10: try_unlock('combo_10')
                else:
                    for _ in range(8):
                        spawn_particles(e.x, e.y - e.h / 2, NEON_YELLOW, 1, 1.5, 1.0, 1.0)
                    play_sound('hit')

        if boss and boss.alive and id(boss) not in ninja.hit_enemies_this_attack:
            if atk_rect.colliderect(boss.rect()):
                ninja.hit_enemies_this_attack.append(id(boss))
                if boss.take_damage(15):
                    score += 2000
                    kills += 1
                    total_bosses[0] += 1
                    try_unlock('boss_kill')
                    play_sound('kill')
                    if settings['screen_shake']:
                        screen_shake = 30
                    flash = 200
                    for _ in range(80):
                        spawn_particles(boss.x + random.randint(-60, 60),
                                        boss.y - 60 + random.randint(-40, 40),
                                        random.choice([NEON_RED, NEON_ORANGE, NEON_MAGENTA]),
                                        1, 2.5, 2.0, 2.0)
                    boss = None
                else:
                    for _ in range(12):
                        spawn_particles(boss.x + random.randint(-30, 30),
                                        boss.y - 60 + random.randint(-30, 30),
                                        NEON_YELLOW, 1, 1.5, 1.0, 1.0)
                    play_sound('hit')

    for _ in range(3):
        spawn_enemy()

    running = True
    while running:
        clock.tick(FPS)
        t = pygame.time.get_ticks() / 1000
        mouse_pos = get_game_mouse_pos()

        if slowmo_active > 0:
            slowmo_active -= 1

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
                    # پرش با UP یا W
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        ninja.jump()
                    # حمله با SPACE
                    if event.key == pygame.K_SPACE:
                        ninja.attack()
                    # شوریکن با K یا G
                    if event.key == pygame.K_k or event.key == pygame.K_g:
                        shurikens.append(ninja.throw_shuriken())
                    # Dash با SHIFT
                    if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        if ninja.dash():
                            try_unlock('dash_master')
                    # Slow Motion با E
                    if event.key == pygame.K_e:
                        if slowmo_energy >= 50 and slowmo_active == 0:
                            slowmo_active = 180
                            slowmo_energy -= 50
                            play_sound('slowmo')
                            try_unlock('slow_mo')

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

            if display_score < score:
                display_score += max(1, (score - display_score) // 5)
                if display_score > score:
                    display_score = score

            if combо_timer > 0:
                combо_timer -= 1
                if combо_timer == 0:
                    combo = 0

            keys = pygame.key.get_pressed()
            ninja.update(keys, platforms)

            # چک حمله هر فریم
            process_attack_hits()

            for s in shurikens[:]:
                s.update()
                if s.life <= 0:
                    shurikens.remove(s)
                    continue
                hit_something = False
                for e in enemies[:]:
                    if math.hypot(e.x - s.x, e.y - e.h / 2 - s.y) < e.w / 2 + s.radius:
                        if e.take_damage(20):
                            kills += 1
                            total_kills[0] += 1
                            score += 150
                            combo += 1
                            combо_timer = 90
                            max_combo = max(max_combo, combo)
                            for _ in range(25):
                                spawn_particles(e.x, e.y - e.h / 2, e.color, 1, 1.8, 1.3, 1.3)
                            play_sound('kill')
                            enemies.remove(e)
                        else:
                            for _ in range(8):
                                spawn_particles(e.x, e.y - e.h / 2, NEON_YELLOW, 1, 1.5, 1.0, 1.0)
                        shurikens.remove(s)
                        hit_something = True
                        break
                if hit_something:
                    continue
                if boss and boss.alive:
                    if math.hypot(boss.x - s.x, boss.y - 60 - s.y) < boss.w / 2 + s.radius:
                        if boss.take_damage(20):
                            score += 2000
                            kills += 1
                            total_bosses[0] += 1
                            try_unlock('boss_kill')
                            play_sound('kill')
                            if settings['screen_shake']:
                                screen_shake = 30
                            flash = 200
                            boss = None
                        else:
                            for _ in range(8):
                                spawn_particles(s.x, s.y, NEON_YELLOW, 1, 1.5)
                        shurikens.remove(s)

            enemy_spawn_timer += 1
            spawn_interval = max(60, 180 - level * 10)
            if enemy_spawn_timer >= spawn_interval and len(enemies) < 6:
                enemy_spawn_timer = 0
                spawn_enemy()

            for e in enemies[:]:
                action = e.update(ninja, platforms)

                if ninja.invincible == 0 and e.rect().colliderect(ninja.rect()):
                    result = ninja.take_damage(15)
                    if result == 'dead':
                        game_over = True

                if e.attack_timer > 5 and ninja.invincible == 0:
                    atk = None
                    if e.kind in ['samurai', 'ninja_ai']:
                        if e.facing == 1:
                            atk = pygame.Rect(int(e.x), int(e.y - e.h + 10), 50, e.h - 20)
                        else:
                            atk = pygame.Rect(int(e.x - 50), int(e.y - e.h + 10), 50, e.h - 20)
                        if atk and atk.colliderect(ninja.rect()):
                            result = ninja.take_damage(15)
                            if result == 'dead':
                                game_over = True

                if action == 'shoot':
                    dx = ninja.x - e.x
                    dy = ninja.y - e.y + 25
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        speed = 6
                        vx = dx / dist * speed
                        vy = dy / dist * speed
                        enemy_shots.append(Shuriken(e.x + e.facing * 15, e.y - 30, vx, vy))
                        play_sound('shoot')

            for s in enemy_shots[:]:
                s.update()
                if s.life <= 0:
                    enemy_shots.remove(s)
                    continue
                if ninja.invincible == 0:
                    if math.hypot(s.x - ninja.x, s.y - (ninja.y - ninja.h / 2)) < ninja.w / 2 + s.radius:
                        result = ninja.take_damage(10)
                        if result == 'dead':
                            game_over = True
                        enemy_shots.remove(s)

            if level >= 3 and not boss_spawned and level_kills >= 5:
                boss = OniBoss(WIDTH - 100, GROUND_Y)
                boss_spawned = True
                play_sound('boss')
                flash = 100
                level_banner_timer = 90

            if boss and boss.alive:
                actions = boss.update(ninja)
                if ninja.invincible == 0:
                    if boss.rect().colliderect(ninja.rect()):
                        result = ninja.take_damage(20)
                        if result == 'dead':
                            game_over = True
                if boss.attack_timer > 5 and ninja.invincible == 0:
                    atk = None
                    if boss.facing == 1:
                        atk = pygame.Rect(int(boss.x), int(boss.y - boss.h + 30), 80, 60)
                    else:
                        atk = pygame.Rect(int(boss.x - 80), int(boss.y - boss.h + 30), 80, 60)
                    if atk and atk.colliderect(ninja.rect()):
                        result = ninja.take_damage(25)
                        if result == 'dead':
                            game_over = True

            powerup_spawn_timer -= 1
            if powerup_spawn_timer <= 0:
                powerup_spawn_timer = random.randint(FPS * 10, FPS * 20)
                if len(powerups) < 2:
                    kind = random.choice(['health', 'slowmo', 'dash'])
                    x = random.uniform(100, WIDTH - 100)
                    y = GROUND_Y - 200
                    powerups.append({'x': x, 'y': y, 'kind': kind, 'pulse': 0})

            for p in powerups[:]:
                p['pulse'] += 0.15
                p['y'] += 0.5
                if p['y'] > GROUND_Y - 20:
                    p['y'] = GROUND_Y - 20
                dx = ninja.x - p['x']
                dy = (ninja.y - ninja.h / 2) - p['y']
                if math.hypot(dx, dy) < 30:
                    if p['kind'] == 'health':
                        ninja.hp = min(ninja.max_hp, ninja.hp + 40)
                    elif p['kind'] == 'slowmo':
                        slowmo_energy = min(100, slowmo_energy + 50)
                    elif p['kind'] == 'dash':
                        ninja.dash_cooldown = 0
                    play_sound('jump')
                    for _ in range(20):
                        spawn_particles(p['x'], p['y'], NEON_GREEN, 1, 1.5)
                    powerups.remove(p)

            if level_kills >= level_kills_needed and not boss_spawned:
                level += 1
                level_kills = 0
                level_kills_needed += 2
                if level >= 3: try_unlock('level_3')
                if level >= 5: try_unlock('level_5')
                play_sound('levelup')
                level_banner_timer = 90

            if slowmo_energy < 100:
                slowmo_energy += 0.15

            for p in active_particles[:]:
                p.update()
                if not p.active:
                    active_particles.remove(p)

            if screen_shake > 0:
                screen_shake -= 1
            if flash > 0:
                flash -= 8
            if level_banner_timer > 0:
                level_banner_timer -= 1

        # ============================================================
        #                    رسم
        # ============================================================
        game_surface.fill(DARK_BG)
        offset_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        offset_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0

        play_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        for layer in bg_layers:
            play_layer.blit(layer['surf'], (0, 0))

        pygame.draw.rect(play_layer, (10, 5, 20), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.line(play_layer, NEON_PURPLE, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)
        pygame.draw.line(play_layer, NEON_PINK, (0, GROUND_Y + 3), (WIDTH, GROUND_Y + 3), 1)

        for plat in platforms:
            plat.draw(play_layer)

        for p in powerups:
            r = 18 + int(math.sin(p['pulse']) * 3)
            colors_pu = {'health': NEON_GREEN, 'slowmo': NEON_PURPLE, 'dash': NEON_CYAN}
            color = colors_pu[p['kind']]
            for i in range(3, 0, -1):
                glow = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*color, 50 - i * 12), (r * 2, r * 2), r * 1.5)
                play_layer.blit(glow, (p['x'] - r * 2, p['y'] - r * 2))
            pygame.draw.circle(play_layer, (color[0] // 3, color[1] // 3, color[2] // 3),
                               (int(p['x']), int(p['y'])), r)
            pygame.draw.circle(play_layer, color, (int(p['x']), int(p['y'])), r, 2)
            pygame.draw.circle(play_layer, WHITE, (int(p['x']), int(p['y'])), r, 1)
            icon = {'health': '+', 'slowmo': 'T', 'dash': 'D'}[p['kind']]
            draw_text(play_layer, icon, 20, p['x'], p['y'] - 10, WHITE, center=True, bold=True)

        for e in enemies:
            e.draw(play_layer)

        if boss and boss.alive:
            boss.draw(play_layer)

        for s in shurikens:
            s.draw(play_layer)
        for s in enemy_shots:
            s.draw(play_layer)

        for p in active_particles:
            p.draw(play_layer)

        if not game_over:
            ninja.draw(play_layer)

        if slowmo_active > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((50, 0, 100, 60))
            play_layer.blit(overlay, (0, 0))

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
        draw_text(game_surface, "NINJA", 22, 25 + get_font(22).size("NEON ")[0], 15, NEON_CYAN, glow=True)
        draw_text(game_surface, "UP: Jump | SPACE: Attack | K: Shuriken | SHIFT: Dash | E: SlowMo", 11, 25, 45, (180, 200, 220))

        draw_text(game_surface, "SCORE", 14, WIDTH - 25, 12, NEON_CYAN)
        draw_text(game_surface, f"{display_score}", 26, WIDTH - 25, 30, WHITE, glow=True)

        draw_text(game_surface, f"LEVEL: {level}", 16, WIDTH - 25, 62, NEON_GREEN)
        draw_text(game_surface, f"KILLS: {kills}", 14, WIDTH - 25, 84, NEON_YELLOW)

        draw_text(game_surface, f"LIVES: {ninja.lives}", 14, WIDTH // 2, 15, NEON_PINK)

        hp_bar_w = 200
        hp_bar_x = WIDTH // 2 - hp_bar_w // 2
        hp_bar_y = 35
        pygame.draw.rect(game_surface, (40, 10, 10), (hp_bar_x, hp_bar_y, hp_bar_w, 8))
        hp_ratio = ninja.hp / ninja.max_hp
        hp_color = NEON_GREEN if hp_ratio > 0.5 else NEON_YELLOW if hp_ratio > 0.25 else NEON_RED
        pygame.draw.rect(game_surface, hp_color, (hp_bar_x, hp_bar_y, hp_bar_w * hp_ratio, 8))
        pygame.draw.rect(game_surface, WHITE, (hp_bar_x, hp_bar_y, hp_bar_w, 8), 1)

        sm_bar_w = 200
        sm_bar_x = WIDTH // 2 - sm_bar_w // 2
        sm_bar_y = 55
        pygame.draw.rect(game_surface, (20, 10, 40), (sm_bar_x, sm_bar_y, sm_bar_w, 6))
        pygame.draw.rect(game_surface, NEON_PURPLE, (sm_bar_x, sm_bar_y, sm_bar_w * (slowmo_energy / 100), 6))
        pygame.draw.rect(game_surface, WHITE, (sm_bar_x, sm_bar_y, sm_bar_w, 6), 1)
        draw_text(game_surface, "SLOW-MO [E]", 10, WIDTH // 2, sm_bar_y + 10, NEON_PURPLE, center=True)

        if combo > 1:
            combo_color = NEON_GREEN if combo < 5 else NEON_YELLOW if combo < 10 else NEON_PINK
            scale = 1 + math.sin(t * 10) * 0.1
            draw_text(game_surface, f"x{combo} COMBO", int(28 * scale), WIDTH // 2, HEIGHT // 2 - 150,
                      combo_color, center=True, glow=True)

        if level_banner_timer > 0:
            size = 60 + int(math.sin(t * 10) * 5)
            draw_text(game_surface, f"LEVEL {level}", size, WIDTH // 2, HEIGHT // 2 - 50,
                      NEON_CYAN, center=True, glow=True)
            if boss_spawned and boss and boss.alive:
                draw_text(game_surface, "ONI BOSS!", 30, WIDTH // 2, HEIGHT // 2 + 20,
                          NEON_RED, center=True, glow=True)
            else:
                draw_text(game_surface, "GET READY!", 30, WIDTH // 2, HEIGHT // 2 + 20,
                          WHITE, center=True)

        if slowmo_active > 0:
            draw_text(game_surface, "SLOW MOTION", 30, WIDTH // 2, 130,
                      NEON_PURPLE, center=True, glow=True)

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
            draw_text(game_surface, f"LEVEL: {level}   KILLS: {kills}   MAX COMBO: {max_combo}",
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