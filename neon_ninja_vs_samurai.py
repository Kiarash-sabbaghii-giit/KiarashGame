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

BASE_W, BASE_H = 1200, 700
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("NEON NINJA vs SAMURAI")
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
GROUND_Y = HEIGHT - 120
GRAVITY = 0.8
JUMP_FORCE = -18

# --- ذخیره ---
SAVE_FILE = "neon_fight_save.json"
settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'difficulty': 1.0,
    'screen_shake': True,
    'rounds_to_win': 3,
}
achievements = {
    'first_win': {'name': 'FIRST WIN', 'desc': 'Win your first match', 'unlocked': False, 'icon': 'W1'},
    'win_5': {'name': 'WARRIOR', 'desc': 'Win 5 matches', 'unlocked': False, 'icon': 'W5'},
    'win_20': {'name': 'MASTER', 'desc': 'Win 20 matches', 'unlocked': False, 'icon': 'W20'},
    'combo_3': {'name': 'COMBO STARTER', 'desc': 'Get a 3-hit combo', 'unlocked': False, 'icon': 'C3'},
    'combo_5': {'name': 'COMBO KING', 'desc': 'Get a 5-hit combo', 'unlocked': False, 'icon': 'C5'},
    'perfect_round': {'name': 'PERFECT', 'desc': 'Win a round without damage', 'unlocked': False, 'icon': 'P'},
    'special_5': {'name': 'SPECIALIST', 'desc': 'Use 5 special moves', 'unlocked': False, 'icon': 'S5'},
    'dodge_master': {'name': 'DODGE MASTER', 'desc': 'Dodge 10 times', 'unlocked': False, 'icon': 'D'},
    'beat_hard': {'name': 'HARD WINNER', 'desc': 'Beat Hard AI', 'unlocked': False, 'icon': 'H'},
    'ninja_win': {'name': 'NINJA MASTER', 'desc': 'Win as Ninja', 'unlocked': False, 'icon': 'N'},
    'samurai_win': {'name': 'SAMURAI MASTER', 'desc': 'Win as Samurai', 'unlocked': False, 'icon': 'S'},
    'gun_kill': {'name': 'GUNSLINGER', 'desc': 'Kill with gun', 'unlocked': False, 'icon': 'G'},
    'counter_5': {'name': 'COUNTER KING', 'desc': '5 counter attacks', 'unlocked': False, 'icon': 'CT'},
    'rage_win': {'name': 'RAGE QUIT', 'desc': 'Win in Rage mode', 'unlocked': False, 'icon': 'R'},
    'damage_1000': {'name': 'HEAVY HITTER', 'desc': 'Deal 1000 total damage', 'unlocked': False, 'icon': 'DMG'},
}
highscore = [0]
game_history = []
total_wins = [0]
total_damage = [0]


def load_save():
    global settings, achievements, highscore, game_history, total_wins, total_damage
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
            total_damage[0] = data.get('total_damage', 0)
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
                'total_damage': total_damage[0],
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


def add_game_to_history(score, winner, duration, mode, new_achs):
    entry = {
        'score': score,
        'winner': winner,
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
    sounds['punch'] = make_sound(300, 100, 0.1, 0.20, 'square')
    sounds['hit'] = make_sound(200, 60, 0.15, 0.28, 'noise')
    sounds['heavy_hit'] = make_sound(150, 40, 0.25, 0.35, 'noise')
    sounds['block'] = make_sound(800, 600, 0.1, 0.20, 'square')
    sounds['dodge'] = make_sound(1000, 1400, 0.08, 0.15, 'sine')
    sounds['jump'] = make_sound(600, 900, 0.1, 0.18, 'sine')
    sounds['gun'] = make_sound(1500, 400, 0.15, 0.25, 'saw')
    sounds['counter'] = make_sound(1200, 2000, 0.2, 0.30, 'sine')
    sounds['special'] = make_sound(400, 2000, 0.5, 0.30, 'saw')
    sounds['ko'] = make_sound(500, 60, 1.0, 0.35, 'saw')
    sounds['round_win'] = make_sound(600, 1500, 0.6, 0.30, 'sine')
    sounds['gameover'] = make_sound(400, 60, 1.5, 0.32, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['whoosh'] = make_sound(600, 200, 0.15, 0.15, 'noise')

    bass = [82.4, 82.4, 65.4, 65.4, 73.4, 73.4, 82.4, 82.4]
    lead = [440, 523, 587, 523, 440, 392, 349, 392]
    music_sound[0] = make_music_loop(bass, lead, 0.25, 0.10)
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

    def spawn(self, x, y, color, speed_mult=1.0, size_mult=1.0, life_mult=1.0, gravity=0.5):
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


def spawn_particles(x, y, color, count, speed_mult=1.0, size_mult=1.0, life_mult=1.0, gravity=0.5):
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
#                    Bullet
# ============================================================
class Bullet:
    def __init__(self, x, y, vx, vy, owner):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.owner = owner  # Fighter object
        self.life = 120
        self.damage = 15
        self.color = NEON_YELLOW
        self.alive = True

    def update(self, opponent):
        if not self.alive:
            return
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1  # jykeft
        self.life -= 1
        if self.life <= 0:
            self.alive = False
            return
        # برخورد با حریف
        if opponent.rect().collidepoint(self.x, self.y):
            if opponent.dodge_timer <= 0:
                hit, result = opponent.take_damage(self.damage, self.owner)
                if hit:
                    play_sound('hit')
                    if result == 'ko':
                        play_sound('ko')
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        # Trail
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 5)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 3)


# ============================================================
#                    Fighter
# ============================================================
class Fighter:
    def __init__(self, x, char_type, facing=1, is_ai=False, ai_level=1.0):
        self.x = x
        self.y = GROUND_Y
        self.vx = 0
        self.vy = 0
        self.char_type = char_type
        self.facing = facing
        self.is_ai = is_ai
        self.ai_level = ai_level

        if char_type == 'ninja':
            self.max_hp = 100
            self.speed = 6
            self.color = NEON_CYAN
            self.accent = NEON_PURPLE
            self.name = "NINJA"
        else:
            self.max_hp = 130
            self.speed = 4.5
            self.color = NEON_RED
            self.accent = NEON_ORANGE
            self.name = "SAMURAI"

        self.hp = self.max_hp
        self.w = 45
        self.h = 80
        self.on_ground = True

        # مبارزه
        self.attack_timer = 0
        self.attack_type = None
        self.attack_cooldown = 0
        self.attack_hit_frame = 0
        self.attack_hit = False
        self.hit_stun = 0
        self.block_timer = 0
        self.dodge_timer = 0
        self.dodge_cooldown = 0

        # Combo
        self.combo_count = 0
        self.combo_timer = 0
        self.last_attack_type = None
        self.counter_ready = False  # اگه دوج کنه و حریف حمله کنه
        self.counter_window = 0

        # انرژی ویژه
        self.energy = 0
        self.max_energy = 100
        self.special_active = 0

        # تفنگ
        self.has_gun = False
        self.gun_ammo = 0
        self.gun_cooldown = 0

        # Rage mode
        self.rage_timer = 0
        self.rage_cooldown = 0

        # افکت‌ها
        self.hit_flash = 0
        self.anim_time = 0
        self.attacking = False

        # AI
        self.ai_timer = 0
        self.ai_state = 'idle'
        self.ai_state_timer = 0

    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h), self.w, self.h)

    def attack_rect(self):
        if self.attack_timer <= 0:
            return None
        if self.attack_hit:
            return None

        range_w = 0
        range_h = 0
        if self.attack_type == 'light':
            range_w = 60
            range_h = 40
        elif self.attack_type == 'heavy':
            range_w = 80
            range_h = 60
        elif self.attack_type == 'kick':
            range_w = 70
            range_h = 30
        elif self.attack_type == 'special':
            range_w = 100
            range_h = 80

        if self.facing == 1:
            return pygame.Rect(int(self.x + 20), int(self.y - 60), range_w, range_h)
        else:
            return pygame.Rect(int(self.x - 20 - range_w), int(self.y - 60), range_w, range_h)

    def is_in_rage(self):
        return self.hp <= self.max_hp * 0.3

    def start_attack(self, attack_type):
        if self.attack_cooldown > 0 or self.attack_timer > 0 or self.hit_stun > 0 or self.dodge_timer > 0:
            return False

        self.attack_type = attack_type
        self.attacking = True
        self.attack_hit = False

        if attack_type == 'light':
            self.attack_timer = 12
            self.attack_hit_frame = 5
            self.attack_cooldown = 15
        elif attack_type == 'heavy':
            self.attack_timer = 24
            self.attack_hit_frame = 12
            self.attack_cooldown = 40
        elif attack_type == 'kick':
            self.attack_timer = 18
            self.attack_hit_frame = 8
            self.attack_cooldown = 25
        elif attack_type == 'special':
            self.attack_timer = 30
            self.attack_hit_frame = 8
            self.attack_cooldown = 30

        play_sound('whoosh')
        return True

    def start_block(self):
        if self.attack_timer > 0 or self.hit_stun > 0:
            return
        self.block_timer = 20

    def start_dodge(self):
        if self.dodge_cooldown > 0 or self.attack_timer > 0:
            return
        self.dodge_timer = 15
        self.dodge_cooldown = 40
        play_sound('dodge')
        for _ in range(15):
            spawn_particles(self.x, self.y - self.h / 2, self.accent, 1, 1.2, 1.0, 0.8, gravity=0)
        # اگه حریف حمله می‌کنه، counter ready
        self.counter_window = 30

    def start_special(self):
        if self.energy < self.max_energy or self.special_active > 0:
            return False
        self.energy = 0
        self.special_active = 30
        play_sound('special')
        self.attack_timer = 30
        self.attack_type = 'special'
        self.attack_hit_frame = 8
        return True

    def start_rage(self):
        if self.rage_cooldown > 0 or self.rage_timer > 0:
            return False
        self.rage_timer = 300  # 5 ثانیه
        self.rage_cooldown = 600  # 10 ثانیه کول‌داون
        play_sound('special')
        for _ in range(40):
            spawn_particles(self.x, self.y - self.h / 2, NEON_RED, 1, 2.0, 1.5, 1.5)
        if settings['screen_shake']:
            # نمیشه توی این تابع تنظیم کرد - از flag استفاده می‌کنیم
            pass
        return True

    def shoot_gun(self):
        if not self.has_gun or self.gun_cooldown > 0 or self.gun_ammo <= 0:
            return None
        if self.hit_stun > 0 or self.dodge_timer > 0:
            return None

        self.gun_cooldown = 30
        self.gun_ammo -= 1
        play_sound('gun')

        # جهت شلیک
        if self.facing == 1:
            bullet_x = self.x + 20
            bullet_y = self.y - self.h / 2
            vx = 15
        else:
            bullet_x = self.x - 20
            bullet_y = self.y - self.h / 2
            vx = -15

        # زاویه بر اساس فاصله
        return Bullet(bullet_x, bullet_y, vx, -1, self)

    def pick_up_gun(self):
        self.has_gun = True
        self.gun_ammo = 6

    def take_damage(self, damage, attacker):
        # چک Dodge
        if self.dodge_timer > 0:
            return False, 'dodged'

        # چک Counter
        if self.counter_window > 0 and attacker.attack_timer > 0:
            # Counter attack!
            self.counter_window = 0
            self.counter_ready = True
            # آسیب به حریف
            counter_damage = int(damage * 1.5)
            if attacker.dodge_timer <= 0:
                attacker.hp -= counter_damage
                attacker.hit_stun = 30
                attacker.hit_flash = 10
                total_damage[0] += counter_damage
                play_sound('counter')
                for _ in range(30):
                    spawn_particles(attacker.x, attacker.y - attacker.h / 2, NEON_MAGENTA, 1, 2.0, 1.5, 1.5)
                if attacker.hp <= 0:
                    return True, 'counter_ko'
            return True, 'counter'

        # چک Block
        blocked = False
        if self.block_timer > 0:
            damage = int(damage * 0.3)
            blocked = True
            play_sound('block')

        # Rage mode آسیب بیشتر
        if self.is_in_rage():
            damage = int(damage * 1.5)

        self.hp -= damage
        self.hit_stun = 20 if not blocked else 10
        self.hit_flash = 8
        total_damage[0] += damage

        for _ in range(15):
            spawn_particles(self.x, self.y - self.h / 2, NEON_RED, 1, 1.5, 1.2, 1.0)

        # Knockback
        direction = -1 if attacker.x > self.x else 1
        self.vx = direction * 4

        # کمبو رو ریست کن
        attacker.combo_count = 0
        attacker.combo_timer = 0

        if self.hp <= 0:
            self.hp = 0
            return True, 'ko'

        return True, 'blocked' if blocked else 'hit'

    def update(self, keys, opponent, dt=1.0):
        # اگه HP صفر، متوقف
        if self.hp <= 0:
            if self.hit_flash > 0:
                self.hit_flash -= 1
            self.vy += GRAVITY
            self.y += self.vy
            if self.y >= GROUND_Y:
                self.y = GROUND_Y
                self.vy = 0
            return

        # تایمرها
        if self.attack_timer > 0:
            self.attack_timer -= 1
            frames_passed = 0
            if self.attack_type == 'light': frames_passed = 12 - self.attack_timer
            elif self.attack_type == 'heavy': frames_passed = 24 - self.attack_timer
            elif self.attack_type == 'kick': frames_passed = 18 - self.attack_timer
            elif self.attack_type == 'special': frames_passed = 30 - self.attack_timer

            if frames_passed >= self.attack_hit_frame and not self.attack_hit:
                ar = self.attack_rect()
                if ar and opponent.rect().colliderect(ar):
                    if self.attack_type == 'light': damage = 6
                    elif self.attack_type == 'heavy': damage = 18
                    elif self.attack_type == 'kick': damage = 10
                    elif self.attack_type == 'special': damage = 25 if self.char_type == 'ninja' else 35
                    else: damage = 5

                    if self.combo_count >= 3:
                        damage = int(damage * 1.3)
                    if self.is_in_rage():
                        damage = int(damage * 1.3)

                    hit, result = opponent.take_damage(damage, self)
                    if hit:
                        self.attack_hit = True
                        if result == 'ko':
                            play_sound('ko')
                        elif result == 'counter':
                            pass
                        else:
                            play_sound('hit')
                        if self.combo_timer > 0:
                            self.combo_count += 1
                        else:
                            self.combo_count = 1
                        self.combo_timer = 90

                        for _ in range(10):
                            spawn_particles(self.x + self.facing * 30,
                                            self.y - self.h / 2,
                                            self.color, 1, 1.5, 1.0, 1.0)

        if self.attack_timer <= 0:
            self.attacking = False
            self.attack_type = None

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.hit_stun > 0:
            self.hit_stun -= 1
        if self.block_timer > 0:
            self.block_timer -= 1
        if self.dodge_timer > 0:
            self.dodge_timer -= 1
        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= 1
        if self.hit_flash > 0:
            self.hit_flash -= 1
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0:
                self.combo_count = 0
        if self.special_active > 0:
            self.special_active -= 1
        if self.counter_window > 0:
            self.counter_window -= 1
        if self.gun_cooldown > 0:
            self.gun_cooldown -= 1
        if self.rage_timer > 0:
            self.rage_timer -= 1
        if self.rage_cooldown > 0:
            self.rage_cooldown -= 1

        self.anim_time += 1

        # پر شدن انرژی
        if self.energy < self.max_energy:
            self.energy = min(self.max_energy, self.energy + 0.15)

        # ============ ورودی بازیکن ============
        if not self.is_ai and self.hit_stun <= 0 and self.dodge_timer <= 0:
            is_moving = False
            if keys[pygame.K_a]:
                self.x -= self.speed
                self.facing = -1
                is_moving = True
            if keys[pygame.K_d]:
                self.x += self.speed
                self.facing = 1
                is_moving = True

            if not is_moving:
                self.facing = 1 if opponent.x > self.x else -1

            # پرش
            if (keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
                self.vy = JUMP_FORCE
                self.on_ground = False
                play_sound('jump')

            # حمله
            if keys[pygame.K_j]:
                if self.attack_cooldown <= 0:
                    self.start_attack('light')
            elif keys[pygame.K_k]:
                if self.attack_cooldown <= 0:
                    self.start_attack('heavy')
            elif keys[pygame.K_l]:
                if self.attack_cooldown <= 0:
                    self.start_attack('kick')

            # بلاک و دوج
            if keys[pygame.K_u]:
                if self.block_timer <= 0 and self.attack_timer <= 0:
                    self.start_block()
            if keys[pygame.K_i]:
                self.start_dodge()

            # تفنگ
            if keys[pygame.K_r]:
                bullet = self.shoot_gun()
                if bullet:
                    return ('bullet', bullet)

        # چک فاصله از حریف
        dist = abs(opponent.x - self.x)
        if dist < 60:
            push = (60 - dist) / 2
            if self.x < opponent.x:
                self.x -= push * 0.5
                opponent.x += push * 0.5
            else:
                self.x += push * 0.5
                opponent.x -= push * 0.5

        # فیزیک
        self.vy += GRAVITY
        self.y += self.vy

        # اصطکاک
        if not self.on_ground:
            self.vx *= 0.95

        # برخورد با زمین
        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vy = 0
            self.on_ground = True

        # اعمال vx
        self.x += self.vx
        self.vx *= 0.85

        # محدوده
        self.x = max(80, min(WIDTH - 80, self.x))

        return None

    def ai_update(self, opponent):
        if self.hp <= 0 or self.hit_stun > 0 or self.dodge_timer > 0:
            return

        self.facing = 1 if opponent.x > self.x else -1
        dist = abs(opponent.x - self.x)
        self.ai_timer += 1

        if self.ai_timer > 15 / self.ai_level:
            self.ai_timer = 0

            # اگه حریف حمله می‌کنه، دوج یا بلاک
            if opponent.attack_timer > 0 and dist < 150:
                r = random.random()
                if r < 0.4 * self.ai_level:
                    self.start_dodge()
                elif r < 0.7:
                    self.start_block()
                return

            # Special
            if self.energy >= self.max_energy and dist < 100 and random.random() < 0.5 * self.ai_level:
                self.start_special()
                return

            # تفنگ
            if self.has_gun and self.gun_ammo > 0 and self.gun_cooldown <= 0:
                if random.random() < 0.3 * self.ai_level and dist > 100:
                    bullet = self.shoot_gun()
                    return ('bullet', bullet)

            # تصمیم بر اساس فاصله
            if dist > 200:
                self.vx = self.facing * 2 * self.ai_level
            elif dist > 100:
                if random.random() < 0.4:
                    self.vx = self.facing * 2
                else:
                    r = random.random()
                    if r < 0.3:
                        self.start_attack('light')
                    elif r < 0.5:
                        self.start_attack('kick')
            else:
                r = random.random()
                if r < 0.4 * self.ai_level:
                    self.start_attack('light')
                elif r < 0.65:
                    self.start_attack('heavy')
                elif r < 0.8:
                    self.start_attack('kick')
                else:
                    self.vx = -self.facing * 2

    def reset(self, x, facing):
        self.x = x
        self.y = GROUND_Y
        self.vx = 0
        self.vy = 0
        self.hp = self.max_hp
        self.facing = facing
        self.hit_stun = 0
        self.attack_timer = 0
        self.attack_cooldown = 0
        self.block_timer = 0
        self.dodge_timer = 0
        self.dodge_cooldown = 0
        self.combo_count = 0
        self.combo_timer = 0
        self.hit_flash = 0
        self.energy = 0
        self.special_active = 0
        self.has_gun = False
        self.gun_ammo = 0
        self.rage_timer = 0
        self.counter_window = 0

    def draw(self, surface):
        # رنگ بر اساس rage
        rage = self.is_in_rage() and self.hp > 0
        base_color = self.color
        if self.hit_flash > 0:
            base_color = WHITE
        elif rage:
            # پالس قرمز
            pulse = int(abs(math.sin(self.anim_time * 0.2)) * 100)
            base_color = (min(255, self.color[0] + pulse),
                          max(0, self.color[1] - pulse // 2),
                          max(0, self.color[2] - pulse // 2))

        # هاله
        for hr in range(3, 0, -1):
            glow_size = self.w * 2 + hr * 10
            glow = pygame.Surface((glow_size, self.h + hr * 10), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*base_color, 40 - hr * 10),
                                (0, 0, glow_size, self.h + hr * 10))
            surface.blit(glow, (self.x - glow_size / 2, self.y - self.h - hr * 5))

        color = base_color
        accent = WHITE if self.hit_flash > 0 else self.accent

        # سایه
        pygame.draw.ellipse(surface, (0, 0, 0, 100),
                            (self.x - 25, self.y - 8, 50, 12))

        # پاها
        pygame.draw.line(surface, color,
                         (self.x - 8, self.y - 30),
                         (self.x - 12, self.y), 6)
        pygame.draw.line(surface, color,
                         (self.x + 8, self.y - 30),
                         (self.x + 12, self.y), 6)

        # بدن
        body_rect = pygame.Rect(int(self.x - 12), int(self.y - 65), 24, 40)
        pygame.draw.rect(surface, (10, 20, 50), body_rect, border_radius=4)
        pygame.draw.rect(surface, color, body_rect, 3, border_radius=4)

        # سر
        head_rect = pygame.Rect(int(self.x - 12), int(self.y - 88), 24, 24)
        pygame.draw.rect(surface, (10, 20, 50), head_rect, border_radius=5)
        pygame.draw.rect(surface, color, head_rect, 3, border_radius=5)

        # چشم
        if self.facing == 1:
            pygame.draw.circle(surface, accent, (int(self.x + 4), int(self.y - 76)), 3)
        else:
            pygame.draw.circle(surface, accent, (int(self.x - 4), int(self.y - 76)), 3)

        # کلاه/شال
        if self.char_type == 'ninja':
            scarf_pts = [
                (self.x, self.y - 80),
                (self.x - self.facing * 20, self.y - 75 + math.sin(self.anim_time * 0.1) * 3),
                (self.x - self.facing * 35, self.y - 65),
            ]
            pygame.draw.lines(surface, accent, False, scarf_pts, 4)
        else:
            hat_pts = [
                (self.x - 15, self.y - 88),
                (self.x, self.y - 95),
                (self.x + 15, self.y - 88),
            ]
            pygame.draw.polygon(surface, accent, hat_pts)
            pygame.draw.polygon(surface, WHITE, hat_pts, 2)

        # تفنگ
        if self.has_gun:
            gun_x = self.x + self.facing * 15
            gun_y = self.y - 50
            pygame.draw.rect(surface, NEON_YELLOW, (gun_x - 8, gun_y - 4, 16, 8))
            pygame.draw.rect(surface, WHITE, (gun_x - 8, gun_y - 4, 16, 8), 2)
            # نشونگر مهمات
            for i in range(self.gun_ammo):
                pygame.draw.circle(surface, NEON_YELLOW, (int(self.x - 8 + i * 3), int(self.y - 95)), 2)

        # سلاح
        if self.attack_timer > 0:
            if self.facing == 1:
                weapon_x = self.x + 40
            else:
                weapon_x = self.x - 40
            weapon_y = self.y - 50

            for hr in range(3, 0, -1):
                glow_size = 60 + hr * 10
                glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*accent, 100 - hr * 20),
                                   (glow_size // 2, glow_size // 2), glow_size // 2)
                surface.blit(glow, (weapon_x - glow_size // 2, weapon_y - glow_size // 2))

            if self.attack_type == 'light':
                pygame.draw.line(surface, accent, (self.x, self.y - 50), (weapon_x, weapon_y), 5)
            elif self.attack_type == 'heavy':
                pygame.draw.line(surface, accent, (self.x, self.y - 50), (weapon_x, weapon_y), 8)
            elif self.attack_type == 'kick':
                pygame.draw.line(surface, color, (self.x, self.y - 30), (weapon_x, self.y - 30), 6)
            elif self.attack_type == 'special':
                for i in range(5):
                    offset = i * 5
                    pygame.draw.line(surface, accent,
                                     (self.x, self.y - 50 + offset),
                                     (weapon_x, weapon_y + offset), 4)
                draw_text(surface, "!", 40, self.x, self.y - 120,
                          NEON_YELLOW, center=True, glow=True)

        # Dodge trail
        if self.dodge_timer > 0:
            for i in range(3):
                alpha = (self.dodge_timer / 15) * 200
                dodge_surf = pygame.Surface((30, 80), pygame.SRCALPHA)
                pygame.draw.rect(dodge_surf, (*accent, int(alpha // (i+1))),
                                 (0, 0, 30, 80), border_radius=4)
                surface.blit(dodge_surf, (self.x - 15 - self.facing * i * 15, self.y - 80))

        # Block
        if self.block_timer > 0:
            for hr in range(3, 0, -1):
                glow_size = 80 + hr * 5
                glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*NEON_BLUE, 60 - hr * 15),
                                   (glow_size // 2, glow_size // 2), glow_size // 2, 3)
                surface.blit(glow, (self.x - glow_size // 2, self.y - 50 - glow_size // 2))

        # Counter ready
        if self.counter_window > 0:
            draw_text(surface, "COUNTER!", 14, self.x, self.y - 130,
                      NEON_MAGENTA, center=True, glow=True)

        # Rage indicator
        if self.rage_timer > 0:
            draw_text(surface, "RAGE!", 20, self.x, self.y - 150,
                      NEON_RED, center=True, glow=True)

        # HP bar بالای سر
        bar_w = self.w * 1.5
        bar_h = 6
        bar_x = self.x - bar_w / 2
        bar_y = self.y - self.h - 25
        pygame.draw.rect(surface, (40, 10, 10), (bar_x, bar_y, bar_w, bar_h))
        ratio = self.hp / self.max_hp
        hp_color = NEON_GREEN if ratio > 0.5 else NEON_YELLOW if ratio > 0.25 else NEON_RED
        pygame.draw.rect(surface, hp_color, (bar_x, bar_y, bar_w * ratio, bar_h))
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, bar_h), 2)

        # Energy bar
        if self.energy >= self.max_energy:
            pulse = 1 + math.sin(self.anim_time * 0.3) * 0.3
            draw_text(surface, "SPECIAL READY!", int(10 * pulse), self.x, bar_y - 15,
                      NEON_YELLOW, center=True, glow=True)
        else:
            e_ratio = self.energy / self.max_energy
            e_bar_y = bar_y - 8
            e_bar_h = 3
            pygame.draw.rect(surface, (20, 20, 40), (bar_x, e_bar_y, bar_w, e_bar_h))
            pygame.draw.rect(surface, accent, (bar_x, e_bar_y, bar_w * e_ratio, e_bar_h))

        # Combo
        if self.combo_count > 1:
            draw_text(surface, f"x{self.combo_count}", 24, self.x, self.y - 165,
                      NEON_YELLOW, center=True, glow=True)


# ============================================================
#                    Gun Pickup
# ============================================================
class GunPickup:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vy = 0
        self.life = 600
        self.pulse = 0
        self.radius = 20

    def update(self):
        self.vy += GRAVITY
        self.y += self.vy
        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vy = 0
        self.life -= 1
        self.pulse += 0.15

    def rect(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius),
                           self.radius * 2, self.radius * 2)

    def draw(self, surface):
        r = self.radius + int(math.sin(self.pulse) * 3)

        for hr in range(3, 0, -1):
            glow_size = r * 2 + hr * 8
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*NEON_YELLOW, 60 - hr * 15),
                               (glow_size // 2, glow_size // 2), glow_size // 2)
            surface.blit(glow, (self.x - glow_size // 2, self.y - glow_size // 2))

        pygame.draw.circle(surface, (60, 50, 0), (int(self.x), int(self.y)), r)
        pygame.draw.circle(surface, NEON_YELLOW, (int(self.x), int(self.y)), r, 3)

        # آیکون تفنگ
        draw_text(surface, "G", 20, self.x, self.y - 10, WHITE, center=True, bold=True)


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
    surf1 = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(HEIGHT):
        t = y / HEIGHT
        c = (int(20 + 40 * t), int(5 + 15 * t), int(30 + 30 * t))
        pygame.draw.line(surf1, c, (0, y), (WIDTH, y))
    for _ in range(150):
        x, y = random.randint(0, WIDTH), random.randint(0, HEIGHT // 2)
        b = random.randint(100, 220)
        pygame.draw.circle(surf1, (b, b, min(255, b + 40)), (x, y), random.choice([1, 1, 2]))
    layers.append({'surf': surf1, 'speed': 0.05})

    surf2 = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(surf2, (200, 100, 150, 180), (950, 150), 90)
    pygame.draw.circle(surf2, (230, 130, 180, 220), (950, 150), 85)
    pygame.draw.circle(surf2, (180, 90, 140, 255), (950, 150), 80)
    # Torii Gate
    gate_x = 200
    gate_y = HEIGHT - 250
    pygame.draw.rect(surf2, (150, 30, 60), (gate_x - 100, gate_y, 20, 150))
    pygame.draw.rect(surf2, (150, 30, 60), (gate_x + 80, gate_y, 20, 150))
    pygame.draw.rect(surf2, (200, 50, 80), (gate_x - 130, gate_y - 20, 260, 25))
    pygame.draw.rect(surf2, (150, 30, 60), (gate_x - 100, gate_y + 10, 200, 15))
    layers.append({'surf': surf2, 'speed': 0.15})

    surf3 = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(6):
        bx = 100 + i * 200
        by = HEIGHT - 200
        pygame.draw.rect(surf3, (60, 20, 40), (bx - 8, by, 16, 100))
        for j in range(5):
            ax = bx + (j - 2) * 30
            ay = by - 20 - random.randint(0, 30)
            pygame.draw.line(surf3, (60, 20, 40), (bx, by), (ax, ay), 5)
            for _ in range(8):
                gx = ax + random.randint(-15, 15)
                gy = ay + random.randint(-15, 15)
                pygame.draw.circle(surf3, (255, 130, 180, 180), (gx, gy), 4)
                pygame.draw.circle(surf3, (255, 180, 220, 220), (gx, gy), 2)
    layers.append({'surf': surf3, 'speed': 0.3})

    return layers


# ============================================================
#                    Menu
# ============================================================
def show_menu():
    menu_time = 0
    btn_1p = Button(WIDTH // 2, HEIGHT // 2 + 30, 320, 60, "START FIGHT", NEON_CYAN, NEON_GREEN, 28)
    btn_history = Button(WIDTH // 2, HEIGHT // 2 + 105, 320, 45, "HISTORY", NEON_BLUE, NEON_CYAN, 20)
    btn_settings = Button(WIDTH // 2, HEIGHT // 2 + 160, 320, 45, "SETTINGS", NEON_PURPLE, NEON_PINK, 20)
    btn_achievements = Button(WIDTH // 2, HEIGHT // 2 + 215, 320, 45, "ACHIEVEMENTS", NEON_YELLOW, NEON_ORANGE, 20)
    btn_quit = Button(WIDTH // 2, HEIGHT // 2 + 270, 320, 42, "QUIT", NEON_RED, NEON_ORANGE, 18)
    btn_fullscreen = Button(WIDTH - 40, 30, 40, 40, "[]", NEON_PURPLE, NEON_CYAN, 20)

    bg_layers = build_bg()

    while True:
        game_surface.fill(DARK_BG)
        t = pygame.time.get_ticks() / 1000
        menu_time += 1
        mouse_pos = get_game_mouse_pos()

        for layer in bg_layers:
            game_surface.blit(layer['surf'], (0, 0))

        # زمین
        pygame.draw.rect(game_surface, (10, 5, 20), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.line(game_surface, NEON_PURPLE, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)
        pygame.draw.line(game_surface, NEON_PINK, (0, GROUND_Y + 3), (WIDTH, GROUND_Y + 3), 1)

        # عنوان
        title_y = 120 + math.sin(t * 2) * 8
        draw_text(game_surface, "NEON", 60, WIDTH // 2 - 180, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "NINJA", 60, WIDTH // 2 - 30, title_y, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, "vs", 40, WIDTH // 2 + 65, title_y, NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, "SAMURAI", 60, WIDTH // 2 + 220, title_y, NEON_RED, center=True, glow=True)

        # شخصیت‌ها
        ninja_x = 300 + math.sin(t * 1.5) * 20
        for hr in range(3, 0, -1):
            glow_size = 100 + hr * 15
            glow = pygame.Surface((glow_size, 200), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*NEON_CYAN, 50 - hr * 15), (0, 0, glow_size, 200))
            game_surface.blit(glow, (ninja_x - glow_size / 2, 330))
        pygame.draw.rect(game_surface, NEON_CYAN, (ninja_x - 15, 400, 30, 60), border_radius=4)
        pygame.draw.rect(game_surface, NEON_CYAN, (ninja_x - 15, 360, 30, 30), border_radius=5)
        scarf_pts = [(ninja_x, 370), (ninja_x - 30, 375 + math.sin(t * 3) * 5), (ninja_x - 45, 385)]
        pygame.draw.lines(game_surface, NEON_PURPLE, False, scarf_pts, 5)

        samurai_x = WIDTH - 300 + math.sin(t * 1.5 + 1) * 20
        for hr in range(3, 0, -1):
            glow_size = 100 + hr * 15
            glow = pygame.Surface((glow_size, 200), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*NEON_RED, 50 - hr * 15), (0, 0, glow_size, 200))
            game_surface.blit(glow, (samurai_x - glow_size / 2, 330))
        pygame.draw.rect(game_surface, NEON_RED, (samurai_x - 18, 400, 36, 60), border_radius=4)
        pygame.draw.rect(game_surface, NEON_RED, (samurai_x - 15, 360, 30, 30), border_radius=5)
        hat_pts = [(samurai_x - 22, 365), (samurai_x, 345), (samurai_x + 22, 365)]
        pygame.draw.polygon(game_surface, NEON_ORANGE, hat_pts)
        pygame.draw.polygon(game_surface, WHITE, hat_pts, 2)

        # آمار
        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 18, WIDTH // 2, 240,
                      NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, f"WINS: {total_wins[0]}   DAMAGE: {total_damage[0]}",
                  12, WIDTH // 2, 265, NEON_PINK, center=True)

        for b in [btn_1p, btn_history, btn_settings, btn_achievements, btn_quit, btn_fullscreen]:
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
    slider_diff = Slider(WIDTH // 2, 360, 400, 12, (settings['difficulty'] - 0.5) / 1.0, 0, 1, "AI Difficulty")
    slider_rounds = Slider(WIDTH // 2, 450, 400, 12, (settings['rounds_to_win'] - 1) / 4, 0, 1, "Rounds to Win")
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

        box_w = 700
        box_h = 660
        box_x = WIDTH // 2 - box_w // 2
        box_y = HEIGHT // 2 - box_h // 2 + 20
        pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h), border_radius=12)
        pygame.draw.rect(game_surface, NEON_PURPLE, (box_x, box_y, box_w, box_h), 3, border_radius=12)

        draw_text(game_surface, "SETTINGS", 48, WIDTH // 2, 60, NEON_CYAN, center=True, glow=True)

        slider_sfx.update(mouse_pos, mouse_pressed)
        slider_music.update(mouse_pos, mouse_pressed)
        slider_diff.update(mouse_pos, mouse_pressed)
        slider_rounds.update(mouse_pos, mouse_pressed)
        settings['sfx_volume'] = slider_sfx.value
        settings['music_volume'] = slider_music.value
        settings['difficulty'] = 0.5 + slider_diff.value * 1.0
        settings['rounds_to_win'] = 1 + int(slider_rounds.value * 4)
        if music_sound[0]:
            try:
                music_sound[0].set_volume(settings['music_volume'] * 0.5)
            except:
                pass

        slider_sfx.draw(game_surface)
        slider_music.draw(game_surface)
        slider_diff.draw(game_surface)
        slider_rounds.draw(game_surface)

        draw_text(game_surface, f"{settings['rounds_to_win']}", 18, WIDTH // 2 + 230, 440, NEON_YELLOW)

        diff_val = settings['difficulty']
        if diff_val < 0.8:
            diff_label, diff_color = "EASY", NEON_GREEN
        elif diff_val < 1.2:
            diff_label, diff_color = "NORMAL", NEON_CYAN
        else:
            diff_label, diff_color = "HARD", NEON_RED
        draw_text(game_surface, diff_label, 20, WIDTH // 2 + 230, 350, diff_color)

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
                settings['rounds_to_win'] = 3
                for k in achievements:
                    achievements[k]['unlocked'] = False
                highscore[0] = 0
                game_history.clear()
                total_wins[0] = 0
                total_damage[0] = 0
                save_async()
                slider_sfx.value = 0.7
                slider_music.value = 0.5
                slider_diff.value = 0.5
                slider_rounds.value = 0.5
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
        card_h = 36
        for key, a in achievements.items():
            cx = WIDTH // 2 - card_w // 2
            color = NEON_GREEN if a['unlocked'] else (60, 60, 80)
            pygame.draw.rect(game_surface, (10, 5, 25), (cx, y_pos, card_w, card_h), border_radius=8)
            pygame.draw.rect(game_surface, color, (cx, y_pos, card_w, card_h), 2, border_radius=8)
            icon_color = NEON_YELLOW if a['unlocked'] else (80, 80, 80)
            draw_text(game_surface, a['icon'], 12, cx + 35, y_pos + card_h // 2, icon_color, center=True)
            name_color = NEON_YELLOW if a['unlocked'] else (120, 120, 120)
            draw_text(game_surface, a['name'], 14, cx + 70, y_pos + 4, name_color)
            draw_text(game_surface, a['desc'], 10, cx + 70, y_pos + 20, (150, 150, 180))
            status = "[OK]" if a['unlocked'] else "[--]"
            sc = NEON_GREEN if a['unlocked'] else (100, 100, 100)
            draw_text(game_surface, status, 12, cx + card_w - 50, y_pos + card_h // 2, sc, center=True)
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
                winner = entry.get('winner', '?')
                if 'NINJA' in winner.upper():
                    rank_color = NEON_CYAN
                elif 'SAMURAI' in winner.upper():
                    rank_color = NEON_RED
                else:
                    rank_color = NEON_YELLOW
                pygame.draw.rect(game_surface, (15, 8, 30), (ix, iy, iw, item_h - 8), border_radius=6)
                pygame.draw.rect(game_surface, rank_color, (ix, iy, iw, item_h - 8), 2, border_radius=6)
                draw_text(game_surface, winner, 20, ix + 70, iy + 15, rank_color, center=True, glow=True)
                draw_text(game_surface, f"TIME: {entry.get('duration', 0)}s", 14, ix + 200, iy + 10, (180, 180, 200))
                draw_text(game_surface, entry.get('date', '?'), 12, ix + iw - 180, iy + 10, NEON_CYAN)
                new_achs = entry.get('achievements', [])
                if new_achs:
                    ach_str = " ".join(new_achs[:3])
                    if len(new_achs) > 3:
                        ach_str += f" +{len(new_achs) - 3}"
                    draw_text(game_surface, f"* {ach_str}", 11, ix + iw - 180, iy + 28, NEON_YELLOW)
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
#                    Character Select
# ============================================================
def show_character_select():
    btn_ninja = Button(WIDTH // 2 - 200, HEIGHT // 2, 300, 300, "NINJA", NEON_CYAN, NEON_GREEN, 36)
    btn_samurai = Button(WIDTH // 2 + 200, HEIGHT // 2, 300, 300, "SAMURAI", NEON_RED, NEON_ORANGE, 36)
    btn_back = Button(WIDTH // 2, HEIGHT - 80, 200, 50, "BACK", NEON_RED, NEON_ORANGE, 22)

    while True:
        game_surface.fill(DARK_BG)
        t = pygame.time.get_ticks() / 1000
        mouse_pos = get_game_mouse_pos()

        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            game_surface.blit(s, (0, y))

        draw_text(game_surface, "SELECT YOUR FIGHTER", 44, WIDTH // 2, 80,
                  NEON_YELLOW, center=True, glow=True)

        # Ninja
        nx = WIDTH // 2 - 200
        ny = HEIGHT // 2
        for hr in range(3, 0, -1):
            glow_size = 250 + hr * 15
            glow = pygame.Surface((glow_size, 350), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*NEON_CYAN, 50 - hr * 15), (0, 0, glow_size, 350))
            game_surface.blit(glow, (nx - glow_size / 2, ny - 175))
        pygame.draw.rect(game_surface, NEON_CYAN, (nx - 20, ny - 30, 40, 80), border_radius=4)
        pygame.draw.rect(game_surface, NEON_CYAN, (nx - 20, ny - 80, 40, 40), border_radius=5)
        scarf_pts = [(nx, ny - 70), (nx - 40, ny - 65 + math.sin(t * 3) * 5), (nx - 60, ny - 55)]
        pygame.draw.lines(game_surface, NEON_PURPLE, False, scarf_pts, 6)

        # Samurai
        sx = WIDTH // 2 + 200
        for hr in range(3, 0, -1):
            glow_size = 250 + hr * 15
            glow = pygame.Surface((glow_size, 350), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*NEON_RED, 50 - hr * 15), (0, 0, glow_size, 350))
            game_surface.blit(glow, (sx - glow_size / 2, ny - 175))
        pygame.draw.rect(game_surface, NEON_RED, (sx - 25, ny - 30, 50, 80), border_radius=4)
        pygame.draw.rect(game_surface, NEON_RED, (sx - 20, ny - 80, 40, 40), border_radius=5)
        hat_pts = [(sx - 30, ny - 75), (sx, ny - 100), (sx + 30, ny - 75)]
        pygame.draw.polygon(game_surface, NEON_ORANGE, hat_pts)
        pygame.draw.polygon(game_surface, WHITE, hat_pts, 2)

        btn_ninja.update(mouse_pos)
        btn_samurai.update(mouse_pos)
        btn_back.update(mouse_pos)
        btn_ninja.draw(game_surface)
        btn_samurai.draw(game_surface)
        btn_back.draw(game_surface)

        draw_text(game_surface, "Fast • Agile • Low HP", 14, nx, ny + 180, NEON_CYAN, center=True)
        draw_text(game_surface, "Slow • Powerful • High HP", 14, sx, ny + 180, NEON_RED, center=True)

        present()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                toggle_fullscreen()
            if btn_ninja.is_clicked(event):
                return 'ninja'
            if btn_samurai.is_clicked(event):
                return 'samurai'
            if btn_back.is_clicked(event):
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return 'ninja'
                if event.key == pygame.K_2:
                    return 'samurai'
                if event.key == pygame.K_ESCAPE:
                    return None
        clock.tick(FPS)


# ============================================================
#                    بازی اصلی
# ============================================================
def play_game():
    # انتخاب شخصیت
    player_char = show_character_select()
    if player_char is None:
        return
    ai_char = 'samurai' if player_char == 'ninja' else 'ninja'

    p1 = Fighter(300, player_char, facing=1, is_ai=False)
    p2 = Fighter(WIDTH - 300, ai_char, facing=-1, is_ai=True, ai_level=settings['difficulty'])

    # آمار
    p1_rounds = 0
    p2_rounds = 0
    current_round = 1
    total_frames = 0
    round_start_timer = 120
    round_over_timer = 0
    game_over = False
    winner = None
    paused = False

    # گلوله‌ها
    bullets = []

    # آیتم‌ها (تفنگ)
    gun_pickups = []
    gun_spawn_timer = FPS * 15

    # افکت‌ها
    screen_shake = 0
    flash = 0
    new_achs = []
    notifications = []
    go_anim = 0
    game_saved = False

    # آمار دستاورد
    p1_dodges = 0
    p1_specials_used = 0
    p1_counters = 0
    p1_used_block = False

    btn_resume = Button(WIDTH // 2, HEIGHT // 2 + 20, 300, 60, "RESUME", NEON_GREEN, NEON_CYAN, 28)
    btn_pause_menu = Button(WIDTH // 2, HEIGHT // 2 + 100, 300, 55, "MAIN MENU", NEON_RED, NEON_ORANGE, 24)
    btn_rematch = Button(WIDTH // 2, HEIGHT // 2 + 70, 300, 60, "REMATCH", NEON_CYAN, NEON_GREEN, 28)
    btn_menu = Button(WIDTH // 2, HEIGHT // 2 + 145, 300, 55, "MAIN MENU", NEON_YELLOW, NEON_ORANGE, 24)

    active_particles.clear()
    for p in particle_pool:
        p.active = False

    bg_layers = build_bg()
    start_music()

    def try_unlock(key):
        if unlock_achievement(key):
            new_achs.append(achievements[key]['name'])
            notifications.append({'ach': achievements[key], 'timer': 180})
            return True
        return False

    def save_current():
        w = winner if winner else "DRAW"
        add_game_to_history(p1_rounds * 100 + p2_rounds * 100, w, total_frames // FPS, "1P", new_achs)

    def start_round():
        nonlocal round_start_timer, round_over_timer
        p1.reset(300, 1)
        p2.reset(WIDTH - 300, -1)
        round_start_timer = 120
        round_over_timer = 0
        bullets.clear()
        gun_pickups.clear()

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
                if btn_rematch.is_clicked(event):
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

                if not paused and not game_over and p1.hit_stun <= 0:
                    # حمله ویژه
                    if event.key == pygame.K_SPACE:
                        if p1.start_special():
                            p1_specials_used += 1
                            if p1_specials_used >= 5:
                                try_unlock('special_5')
                    # Rage mode
                    if event.key == pygame.K_q:
                        if p1.start_rage():
                            if settings['screen_shake']:
                                screen_shake = 20

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

            # شمارش معکوس
            if round_start_timer > 0:
                round_start_timer -= 1
            elif round_over_timer <= 0:
                keys = pygame.key.get_pressed()

                # آپدیت P1
                result1 = p1.update(keys, p2)
                if result1 and isinstance(result1, tuple) and result1[0] == 'bullet':
                    bullets.append(result1[1])

                # آپدیت P2 (AI)
                if p2.hp > 0 and p1.hp > 0:
                    result2 = p2.ai_update(p1)
                    if result2 and isinstance(result2, tuple) and result2[0] == 'bullet':
                        bullets.append(result2[1])
                result2 = p2.update(pygame.key.get_pressed(), p1)
                if result2 and isinstance(result2, tuple) and result2[0] == 'bullet':
                    bullets.append(result2[1])

                # آپدیت گلوله‌ها
                for b in bullets[:]:
                    target = p2 if b.owner == p1 else p1
                    b.update(target)
                    if not b.alive:
                        bullets.remove(b)

                # اسپاون تفنگ
                gun_spawn_timer -= 1
                if gun_spawn_timer <= 0:
                    gun_spawn_timer = FPS * random.randint(20, 30)
                    gx = random.uniform(200, WIDTH - 200)
                    gun_pickups.append(GunPickup(gx, GROUND_Y - 300))

                # آپدیت آیتم‌ها
                for g in gun_pickups[:]:
                    g.update()
                    if g.life <= 0:
                        gun_pickups.remove(g)
                        continue
                    # برخورد با بازیکن
                    if g.rect().colliderect(p1.rect()):
                        p1.pick_up_gun()
                        play_sound('power') if 'power' in sounds else None
                        for _ in range(20):
                            spawn_particles(g.x, g.y, NEON_YELLOW, 1, 1.5)
                        gun_pickups.remove(g)
                    elif g.rect().colliderect(p2.rect()):
                        p2.pick_up_gun()
                        for _ in range(20):
                            spawn_particles(g.x, g.y, NEON_YELLOW, 1, 1.5)
                        gun_pickups.remove(g)

                # چک KO (فقط اگه قبلاً KO نشده)
                if round_over_timer == 0:
                    if p1.hp <= 0:
                        p2_rounds += 1
                        round_over_timer = 120
                        play_sound('ko')
                        if settings['screen_shake']:
                            screen_shake = 30
                        flash = 200
                    elif p2.hp <= 0:
                        p1_rounds += 1
                        round_over_timer = 120
                        play_sound('ko')
                        if settings['screen_shake']:
                            screen_shake = 30
                        flash = 200

                        # دستاوردهای راند
                        if p1.hp >= p1.max_hp * 0.9:
                            try_unlock('perfect_round')
                        if not p1_used_block:
                            pass

                # پایان راند
                if round_over_timer > 0:
                    round_over_timer -= 1
                    if round_over_timer == 0:
                        if p1_rounds >= settings['rounds_to_win']:
                            game_over = True
                            winner = p1.name
                            total_wins[0] += 1
                            try_unlock('first_win')
                            if total_wins[0] >= 5:
                                try_unlock('win_5')
                            if total_wins[0] >= 20:
                                try_unlock('win_20')
                            if p1.char_type == 'ninja':
                                try_unlock('ninja_win')
                            else:
                                try_unlock('samurai_win')
                            if settings['difficulty'] >= 1.2:
                                try_unlock('beat_hard')
                            if p1.rage_timer > 0:
                                try_unlock('rage_win')
                            if p1.has_gun:
                                try_unlock('gun_kill')
                            save_current()
                            game_saved = True
                            play_sound('gameover')
                        elif p2_rounds >= settings['rounds_to_win']:
                            game_over = True
                            winner = p2.name
                            save_current()
                            game_saved = True
                            play_sound('gameover')
                        else:
                            current_round += 1
                            start_round()

                # چک دستاورد کمبو
                if p1.combo_count >= 3:
                    try_unlock('combo_3')
                if p1.combo_count >= 5:
                    try_unlock('combo_5')
                if p1_dodges >= 10:
                    try_unlock('dodge_master')
                if p1_counters >= 5:
                    try_unlock('counter_5')
                if total_damage[0] >= 1000:
                    try_unlock('damage_1000')

            # آپدیت ذرات
            for p in active_particles[:]:
                p.update()
                if not p.active:
                    active_particles.remove(p)

            if screen_shake > 0:
                screen_shake -= 1
            if flash > 0:
                flash -= 8

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

        # آیتم‌ها
        for g in gun_pickups:
            g.draw(play_layer)

        # گلوله‌ها
        for b in bullets:
            b.draw(play_layer)

        # مبارزها
        p2.draw(play_layer)
        p1.draw(play_layer)

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
        hud_panel = pygame.Surface((WIDTH, 90), pygame.SRCALPHA)
        for y in range(90):
            alpha = int(180 * (1 - y / 90))
            pygame.draw.line(hud_panel, (5, 10, 25, alpha), (0, y), (WIDTH, y))
        game_surface.blit(hud_panel, (0, 0))
        pygame.draw.line(game_surface, NEON_CYAN, (0, 90), (WIDTH, 90), 1)

        draw_text(game_surface, p1.name, 26, 25, 15, p1.color, glow=True)
        draw_text(game_surface, f"WINS: {p1_rounds}", 16, 25, 48, NEON_GREEN)
        draw_text(game_surface, f"COMBO: {p1.combo_count}", 14, 25, 68, NEON_YELLOW)

        draw_text(game_surface, p2.name, 26, WIDTH - 25, 15, p2.color, glow=True)
        draw_text(game_surface, f"WINS: {p2_rounds}", 16, WIDTH - 25, 48, NEON_GREEN)
        draw_text(game_surface, f"COMBO: {p2.combo_count}", 14, WIDTH - 25, 68, NEON_YELLOW)

        draw_text(game_surface, f"ROUND {current_round}", 20, WIDTH // 2, 15, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, f"FIRST TO {settings['rounds_to_win']}", 14, WIDTH // 2, 40, NEON_YELLOW, center=True)

        # HP bar
        bar_w = 400
        bar_h = 25
        p1_bar_x = 30
        bar_y = HEIGHT - 45
        pygame.draw.rect(game_surface, (40, 10, 10), (p1_bar_x, bar_y, bar_w, bar_h))
        ratio1 = max(0, p1.hp / p1.max_hp)
        hp_color1 = NEON_GREEN if ratio1 > 0.5 else NEON_YELLOW if ratio1 > 0.25 else NEON_RED
        pygame.draw.rect(game_surface, hp_color1, (p1_bar_x, bar_y, bar_w * ratio1, bar_h))
        pygame.draw.rect(game_surface, WHITE, (p1_bar_x, bar_y, bar_w, bar_h), 3)
        draw_text(game_surface, f"{p1.hp}/{p1.max_hp}", 16, p1_bar_x + bar_w // 2,
                  bar_y + 3, WHITE, center=True, glow=True)

        p2_bar_x = WIDTH - 30 - bar_w
        pygame.draw.rect(game_surface, (40, 10, 10), (p2_bar_x, bar_y, bar_w, bar_h))
        ratio2 = max(0, p2.hp / p2.max_hp)
        hp_color2 = NEON_GREEN if ratio2 > 0.5 else NEON_YELLOW if ratio2 > 0.25 else NEON_RED
        pygame.draw.rect(game_surface, hp_color2, (p2_bar_x, bar_y, bar_w * ratio2, bar_h))
        pygame.draw.rect(game_surface, WHITE, (p2_bar_x, bar_y, bar_w, bar_h), 3)
        draw_text(game_surface, f"{p2.hp}/{p2.max_hp}", 16, p2_bar_x + bar_w // 2,
                  bar_y + 3, WHITE, center=True, glow=True)

        # راهنمای کنترل (اول بازی)
        if total_frames < 400:
            controls = [
                "MOVE: A/D  |  JUMP: W  |  LIGHT: J  |  HEAVY: K  |  KICK: L",
                "BLOCK: U  |  DODGE: I  |  SHOOT: R (with gun)",
                "SPECIAL: SPACE (full energy)  |  RAGE: Q  |  PICKUP GUN: walk over",
            ]
            for i, line in enumerate(controls):
                draw_text(game_surface, line, 11, WIDTH // 2, HEIGHT - 105 + i * 16,
                          (150, 180, 220), center=True)

        # شمارش معکوس
        if round_start_timer > 0:
            countdown = (round_start_timer // 40) + 1
            size = 100 + int(math.sin(t * 15) * 15)
            draw_text(game_surface, f"{countdown}", size, WIDTH // 2, HEIGHT // 2,
                      NEON_YELLOW, center=True, glow=True)
            draw_text(game_surface, f"ROUND {current_round}", 40, WIDTH // 2, HEIGHT // 2 - 100,
                      NEON_CYAN, center=True, glow=True)

        # KO
        if round_over_timer > 0 and not game_over:
            ko_pulse = 1 + math.sin(t * 15) * 0.1
            draw_text(game_surface, "KO!", int(120 * ko_pulse), WIDTH // 2, HEIGHT // 2,
                      NEON_RED, center=True, glow=True)

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
            win_color = p1.color if winner == p1.name else p2.color
            pygame.draw.rect(game_surface, win_color, (box_x, box_y, box_w, box_h), 3)
            pygame.draw.rect(game_surface, NEON_CYAN, (box_x + 5, box_y + 5, box_w - 10, box_h - 10), 1)
            draw_text(game_surface, f"{winner} WINS!", 60, WIDTH // 2, box_y + 55,
                      win_color, center=True, glow=True)
            draw_text(game_surface, f"{p1.name}: {p1_rounds}  -  {p2.name}: {p2_rounds}", 30,
                      WIDTH // 2, box_y + 130, WHITE, center=True)
            draw_text(game_surface, f"TIME: {total_frames // FPS}s",
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
        elif result == 'start':
            play_game()
    pygame.quit()


if __name__ == "__main__":
    main()