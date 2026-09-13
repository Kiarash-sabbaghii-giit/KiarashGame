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
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
    AUDIO_OK = True
except:
    AUDIO_OK = False

BASE_W, BASE_H = 900, 750
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("NEON SNAKE")
game_surface = pygame.Surface((BASE_W, BASE_H))

clock = pygame.time.Clock()
FPS = 60

# --- ابعاد بازی ---
CELL_SIZE = 25
GRID_COLS = 30
GRID_ROWS = 24
GRID_W = GRID_COLS * CELL_SIZE
GRID_H = GRID_ROWS * CELL_SIZE
GRID_X = (WIDTH - GRID_W) // 2
GRID_Y = (HEIGHT - GRID_H) // 2 + 20

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
NEON_LIME = (150, 255, 100)
NEON_MAGENTA = (255, 0, 200)

# رنگ‌های بدنه مار (گرادیانت)
SNAKE_COLORS = [
    (0, 100, 200),   # سرمه‌ای
    (0, 150, 230),   # آبی
    (0, 200, 255),   # سایان
    (50, 220, 255),  # سایان روشن
    (100, 230, 255), # فیروزه‌ای
]

# --- ذخیره ---
SAVE_FILE = "neon_snake_save.json"

settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'speed_mode': 'normal',  # slow, normal, fast
    'wrap_mode': False,
    'screen_shake': True,
}

achievements = {
    'first_food': {'name': 'FIRST BITE', 'desc': 'Eat your first food', 'unlocked': False, 'icon': '*'},
    'length_10': {'name': 'GROWING', 'desc': 'Reach length 10', 'unlocked': False, 'icon': '==='},
    'length_20': {'name': 'LONG BOI', 'desc': 'Reach length 20', 'unlocked': False, 'icon': '====='},
    'length_40': {'name': 'ANACONDA', 'desc': 'Reach length 40', 'unlocked': False, 'icon': '======'},
    'score_500': {'name': 'ROOKIE', 'desc': 'Score 500 points', 'unlocked': False, 'icon': '*'},
    'score_2000': {'name': 'VETERAN', 'desc': 'Score 2000 points', 'unlocked': False, 'icon': '**'},
    'score_5000': {'name': 'LEGEND', 'desc': 'Score 5000 points', 'unlocked': False, 'icon': '***'},
    'combo_5': {'name': 'COMBO KING', 'desc': 'Eat 5 foods in a row without missing', 'unlocked': False, 'icon': 'C5'},
    'combo_10': {'name': 'COMBO GOD', 'desc': 'Reach combo 10', 'unlocked': False, 'icon': 'C10'},
    'power_5': {'name': 'POWER HUNGRY', 'desc': 'Collect 5 power-ups', 'unlocked': False, 'icon': 'P5'},
    'power_15': {'name': 'SUPERCHARGED', 'desc': 'Collect 15 power-ups', 'unlocked': False, 'icon': 'P15'},
    'survive_1min': {'name': 'SURVIVOR', 'desc': 'Survive 1 minute', 'unlocked': False, 'icon': 'T'},
    'survive_3min': {'name': 'ENDURANCE', 'desc': 'Survive 3 minutes', 'unlocked': False, 'icon': 'TT'},
    'magnet_use': {'name': 'MAGNETIC', 'desc': 'Use the magnet power-up', 'unlocked': False, 'icon': 'M'},
    'boss_hit': {'name': 'BOSS FIGHTER', 'desc': 'Hit the boss snake', 'unlocked': False, 'icon': 'B'},
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


def add_game_to_history(score, length, duration, new_achs):
    entry = {
        'score': score,
        'length': length,
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
                val += math.sin(2 * math.pi * 50 * t * (1 - i / (sr * 0.05))) * 0.35
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
    sounds['eat'] = make_sound(600, 1200, 0.12, 0.18, 'sine')
    sounds['power'] = make_sound(800, 1600, 0.25, 0.22, 'sine')
    sounds['crash'] = make_sound(400, 50, 0.5, 0.3, 'noise')
    sounds['gameover'] = make_sound(500, 60, 1.2, 0.3, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['boss'] = make_sound(150, 400, 0.8, 0.25, 'saw')
    sounds['combo'] = make_sound(1200, 1800, 0.15, 0.15, 'sine')
    sounds['level_up'] = make_sound(500, 1500, 0.4, 0.2, 'sine')

    # موسیقی: آرپژ A minor با vibe Snake
    bass = [55, 55, 65.4, 65.4, 49, 49, 55, 55]
    lead = [440, 523, 659, 523, 587, 523, 440, 392]
    music_sound[0] = make_music_loop(bass, lead, 0.2, 0.1)
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
        self.life = int(random.randint(20, 45) * life_mult)
        self.max_life = self.life
        self.color = color
        self.size = random.randint(2, 4) * size_mult
        self.active = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.94
        self.vy *= 0.94
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
#                    بخش‌های بازی
# ============================================================
DIRECTIONS = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # راست، پایین، چپ، بالا


class Food:
    def __init__(self, x, y, kind='normal'):
        self.x = x
        self.y = y
        self.kind = kind
        self.pulse = random.uniform(0, math.pi * 2)
        self.lifetime = 9999

        # رنگ و امتیاز
        if kind == 'normal':
            self.color = random.choice([
                NEON_PINK, NEON_ORANGE, NEON_YELLOW, NEON_GREEN, NEON_CYAN, NEON_PURPLE
            ])
            self.points = 10
            self.grow = 1
        elif kind == 'speed':
            self.color = NEON_YELLOW
            self.points = 20
            self.grow = 1
            self.lifetime = 300  # 5 ثانیه
        elif kind == 'slow':
            self.color = NEON_BLUE
            self.points = 20
            self.grow = 1
            self.lifetime = 300
        elif kind == 'shrink':
            self.color = NEON_GREEN
            self.points = 30
            self.grow = 1
            self.lifetime = 300
        elif kind == 'ghost':
            self.color = NEON_PURPLE
            self.points = 50
            self.grow = 1
            self.lifetime = 300
        elif kind == 'double':
            self.color = NEON_ORANGE
            self.points = 30
            self.grow = 1
            self.lifetime = 300
        elif kind == 'magnet':
            self.color = NEON_MAGENTA
            self.points = 40
            self.grow = 1
            self.lifetime = 300
        elif kind == 'gold':
            self.color = (255, 215, 0)
            self.points = 100
            self.grow = 2
            self.lifetime = 240

    def update(self):
        self.pulse += 0.15
        self.lifetime -= 1

    def draw(self, surface):
        cx = GRID_X + self.x * CELL_SIZE + CELL_SIZE / 2
        cy = GRID_Y + self.y * CELL_SIZE + CELL_SIZE / 2

        # هاله درخشان
        size_pulse = 1 + math.sin(self.pulse) * 0.15
        for r in range(4, 0, -1):
            glow_size = int(CELL_SIZE * 0.6 * size_pulse * (1 + r * 0.4))
            glow = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            alpha = 60 - r * 10
            pygame.draw.circle(glow, (*self.color, alpha), (glow_size, glow_size), glow_size)
            surface.blit(glow, (cx - glow_size, cy - glow_size))

        # خود غذا (دایره‌ی اصلی)
        radius = int(CELL_SIZE * 0.35 * size_pulse)
        pygame.draw.circle(surface, self.color, (int(cx), int(cy)), radius)
        pygame.draw.circle(surface, WHITE, (int(cx), int(cy)), radius, 2)

        # درخشش مرکزی
        pygame.draw.circle(surface, WHITE, (int(cx - 2), int(cy - 2)), max(1, radius // 3))

        # آیکون داخل غذا برای Power-up ها
        if self.kind != 'normal' and self.kind != 'gold':
            icon = {
                'speed': 'S', 'slow': 'W', 'shrink': '-',
                'ghost': 'G', 'double': '2', 'magnet': 'M'
            }.get(self.kind, '?')
            draw_text(surface, icon, 12, cx, cy - 6, WHITE, center=True, bold=True)


class Snake:
    def __init__(self, start_x, start_y, color_base=NEON_CYAN, ai=False):
        self.body = deque()
        self.body.append((start_x, start_y))
        self.body.append((start_x - 1, start_y))
        self.body.append((start_x - 2, start_y))
        self.direction = 0  # 0: راست
        self.next_direction = 0
        self.color_base = color_base
        self.ai = ai
        self.alive = True
        self.grow_pending = 0
        self.move_timer = 0
        self.move_delay = 8  # فریم‌های بین هر حرکت
        self.ghost_mode = 0
        self.magnet_mode = 0
        self.double_points = 0
        self.shrink_mode = 0

    def set_direction(self, d):
        # نمی‌شه معکوس حرکت کرد
        if (d + 2) % 4 != self.direction:
            self.next_direction = d

    def move(self, foods, all_snakes):
        self.direction = self.next_direction
        head_x, head_y = self.body[0]
        dx, dy = DIRECTIONS[self.direction]
        new_x = head_x + dx
        new_y = head_y + dy

        # Wrap around
        if settings['wrap_mode']:
            new_x = new_x % GRID_COLS
            new_y = new_y % GRID_ROWS
        else:
            if new_x < 0 or new_x >= GRID_COLS or new_y < 0 or new_y >= GRID_ROWS:
                self.alive = False
                return

        # برخورد با خودش
        if self.ghost_mode <= 0:
            for i, (bx, by) in enumerate(self.body):
                if i == 0:
                    continue
                if bx == new_x and by == new_y:
                    self.alive = False
                    return

        # برخورد با مارهای دیگه
        for other in all_snakes:
            if other is self:
                continue
            for bx, by in other.body:
                if bx == new_x and by == new_y:
                    if self.ghost_mode <= 0:
                        self.alive = False
                        return

        # اضافه کردن سر جدید
        self.body.appendleft((new_x, new_y))

        # خوردن غذا
        ate = False
        for food in foods[:]:
            if food.x == new_x and food.y == new_y:
                self.grow_pending += food.grow
                foods.remove(food)
                ate = True
                # افکت‌ها
                cx = GRID_X + new_x * CELL_SIZE + CELL_SIZE / 2
                cy = GRID_Y + new_y * CELL_SIZE + CELL_SIZE / 2
                if self == all_snakes[0]:  # فقط بازیکن
                    spawn_particles(cx, cy, food.color, 20, 1.5, 1.2, 1.2)
                # قدرت‌ها
                if food.kind == 'speed':
                    self.move_delay = max(3, self.move_delay - 4)
                elif food.kind == 'slow':
                    self.move_delay = min(15, self.move_delay + 3)
                elif food.kind == 'shrink':
                    self.shrink_mode = 30  # 30 فریم
                elif food.kind == 'ghost':
                    self.ghost_mode = 300  # 5 ثانیه
                elif food.kind == 'double':
                    self.double_points = 300
                elif food.kind == 'magnet':
                    self.magnet_mode = 300
                break

        # حذف دم اگر رشد نداریم
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.body.pop()

        # Shrink mode
        if self.shrink_mode > 0:
            self.shrink_mode -= 1
            if len(self.body) > 3:
                self.body.pop()

        # کاهش تایمرها
        if self.ghost_mode > 0:
            self.ghost_mode -= 1
        if self.magnet_mode > 0:
            self.magnet_mode -= 1
        if self.double_points > 0:
            self.double_points -= 1

    def ai_choose_direction(self, foods, all_snakes):
        """AI ساده: به سمت نزدیک‌ترین غذا برو ولی از برخورد فرار کن"""
        head_x, head_y = self.body[0]

        # پیدا کردن نزدیک‌ترین غذا
        if not foods:
            return
        nearest = min(foods, key=lambda f: abs(f.x - head_x) + abs(f.y - head_y))

        # جهت‌های ممکن (نه معکوس)
        possible = []
        for d in range(4):
            if (d + 2) % 4 == self.direction:
                continue
            dx, dy = DIRECTIONS[d]
            nx, ny = head_x + dx, head_y + dy

            # چک امنیت
            if not settings['wrap_mode']:
                if nx < 0 or nx >= GRID_COLS or ny < 0 or ny >= GRID_ROWS:
                    continue

            # چک برخورد با خودش
            safe = True
            for bx, by in list(self.body)[1:]:
                if bx == nx and by == ny:
                    safe = False
                    break
            if not safe:
                continue

            # چک برخورد با دیگران
            for other in all_snakes:
                if other is self:
                    continue
                for bx, by in other.body:
                    if bx == nx and by == ny:
                        safe = False
                        break
                if not safe:
                    break
            if not safe:
                continue

            # محاسبه فاصله به غذا
            dist = abs(nx - nearest.x) + abs(ny - nearest.y)
            possible.append((d, dist))

        if possible:
            possible.sort(key=lambda x: x[1])
            self.set_direction(possible[0][0])
        else:
            # هیچ راه امنی نیست، یه راه تصادفی
            safe_dirs = [d for d in range(4) if (d + 2) % 4 != self.direction]
            if safe_dirs:
                self.set_direction(random.choice(safe_dirs))

    def draw(self, surface):
        for i, (bx, by) in enumerate(self.body):
            cx = GRID_X + bx * CELL_SIZE + CELL_SIZE / 2
            cy = GRID_Y + by * CELL_SIZE + CELL_SIZE / 2

            # رنگ بر اساس موقعیت در بدنه
            if not self.ai:
                base_colors = SNAKE_COLORS
            else:
                # AI مار
                r, g, b = self.color_base
                base_colors = [
                    (max(0, r - 100), max(0, g - 100), max(0, b - 100)),
                    (max(0, r - 60), max(0, g - 60), max(0, b - 60)),
                    (r, g, b),
                    (min(255, r + 60), min(255, g + 60), min(255, b + 60)),
                    (min(255, r + 100), min(255, g + 100), min(255, b + 100)),
                ]

            color_idx = min(i, len(base_colors) - 1)
            # برای دنباله، از آخر به اول
            color_idx = min((len(self.body) - 1 - i) * len(base_colors) // max(1, len(self.body)), len(base_colors) - 1)
            color = base_colors[color_idx]

            # هاله درخشان برای بخش‌های نزدیک به سر
            if i < 5:
                for r in range(3, 0, -1):
                    glow_size = int(CELL_SIZE * 0.7 * (1 + r * 0.3))
                    glow = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                    alpha = 40 - r * 10 - i * 5
                    if alpha > 0:
                        pygame.draw.circle(glow, (*color, alpha), (glow_size, glow_size), glow_size)
                        surface.blit(glow, (cx - glow_size, cy - glow_size))

            # بدنه‌ی اصلی
            size = CELL_SIZE - 2
            rect = pygame.Rect(int(cx - size / 2), int(cy - size / 2), size, size)
            pygame.draw.rect(surface, color, rect, border_radius=6)
            # نوار روشن
            pygame.draw.rect(surface, WHITE, rect, 2, border_radius=6)

            # سر
            if i == 0:
                # چشم‌ها بر اساس جهت
                head_cx, head_cy = cx, cy
                dx, dy = DIRECTIONS[self.direction]

                # چشم چپ
                eye_offset = 5
                if self.direction == 0 or self.direction == 2:  # افقی
                    eye1 = (head_cx - 3, head_cy - eye_offset)
                    eye2 = (head_cx - 3, head_cy + eye_offset)
                else:  # عمودی
                    eye1 = (head_cx - eye_offset, head_cy - 3)
                    eye2 = (head_cx + eye_offset, head_cy - 3)

                for ex, ey in [eye1, eye2]:
                    pygame.draw.circle(surface, WHITE, (int(ex), int(ey)), 3)
                    pygame.draw.circle(surface, (0, 0, 0), (int(ex + dx * 1), int(ey + dy * 1)), 1.5)

                # زبان
                if (pygame.time.get_ticks() // 200) % 2 == 0:
                    tongue_start = (head_cx + dx * (CELL_SIZE // 2 - 2), head_cy + dy * (CELL_SIZE // 2 - 2))
                    tongue_end = (head_cx + dx * (CELL_SIZE // 2 + 6), head_cy + dy * (CELL_SIZE // 2 + 6))
                    pygame.draw.line(surface, NEON_RED, tongue_start, tongue_end, 2)

                # هاله مخصوص اگر حالت خاص فعاله
                if self.ghost_mode > 0:
                    ghost_glow = pygame.Surface((CELL_SIZE * 3, CELL_SIZE * 3), pygame.SRCALPHA)
                    pygame.draw.circle(ghost_glow, (*NEON_PURPLE, 100), (CELL_SIZE * 3 // 2, CELL_SIZE * 3 // 2), CELL_SIZE)
                    surface.blit(ghost_glow, (cx - CELL_SIZE * 3 // 2, cy - CELL_SIZE * 3 // 2))


class MovingWall:
    def __init__(self):
        side = random.randint(0, 3)
        if side == 0:  # بالا
            self.x = random.randint(2, GRID_COLS - 3)
            self.y = 0
            self.dx = 0
            self.dy = 1
        elif side == 1:  # پایین
            self.x = random.randint(2, GRID_COLS - 3)
            self.y = GRID_ROWS - 1
            self.dx = 0
            self.dy = -1
        elif side == 2:  # چپ
            self.x = 0
            self.y = random.randint(2, GRID_ROWS - 3)
            self.dx = 1
            self.dy = 0
        else:  # راست
            self.x = GRID_COLS - 1
            self.y = random.randint(2, GRID_ROWS - 3)
            self.dx = -1
            self.dy = 0
        self.alive = True
        self.move_timer = 0
        self.move_delay = 15

    def update(self):
        self.move_timer += 1
        if self.move_timer >= self.move_delay:
            self.move_timer = 0
            self.x += self.dx
            self.y += self.dy
            if self.x < 0 or self.x >= GRID_COLS or self.y < 0 or self.y >= GRID_ROWS:
                self.alive = False

    def draw(self, surface):
        cx = GRID_X + self.x * CELL_SIZE + CELL_SIZE / 2
        cy = GRID_Y + self.y * CELL_SIZE + CELL_SIZE / 2

        # هاله قرمز
        for r in range(3, 0, -1):
            glow_size = int(CELL_SIZE * 0.7 * (1 + r * 0.3))
            glow = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            alpha = 100 - r * 25
            pygame.draw.circle(glow, (255, 50, 50, alpha), (glow_size, glow_size), glow_size)
            surface.blit(glow, (cx - glow_size, cy - glow_size))

        size = CELL_SIZE - 4
        rect = pygame.Rect(int(cx - size / 2), int(cy - size / 2), size, size)
        pygame.draw.rect(surface, NEON_RED, rect, border_radius=4)
        pygame.draw.rect(surface, WHITE, rect, 2, border_radius=4)

        # X داخل
        pygame.draw.line(surface, WHITE, (rect.x + 6, rect.y + 6),
                         (rect.right - 6, rect.bottom - 6), 2)
        pygame.draw.line(surface, WHITE, (rect.right - 6, rect.y + 6),
                         (rect.x + 6, rect.bottom - 6), 2)


class BossSnake:
    """مار غول‌پیکر که به صورت AI حرکت می‌کنه"""
    def __init__(self):
        mid_x, mid_y = GRID_COLS - 5, GRID_ROWS // 2
        self.body = deque()
        for i in range(8):
            self.body.append((mid_x - i, mid_y))
        self.direction = 0
        self.hp = 10
        self.max_hp = 10
        self.alive = True
        self.move_timer = 0
        self.move_delay = 10
        self.flash_timer = 0

    def update(self, player_body):
        self.move_timer += 1
        if self.flash_timer > 0:
            self.flash_timer -= 1
        if self.move_timer < self.move_delay:
            return
        self.move_timer = 0

        head_x, head_y = self.body[0]

        # تعقیب بازیکن
        if player_body:
            px, py = player_body[0]
            dx = px - head_x
            dy = py - head_y

            # انتخاب محور غالب
            if abs(dx) > abs(dy):
                new_dir = 0 if dx > 0 else 2
            else:
                new_dir = 1 if dy > 0 else 3

            # نمی‌شه معکوس
            if (new_dir + 2) % 4 == self.direction:
                # به محور دیگه برو
                if abs(dx) > abs(dy):
                    new_dir = 1 if dy > 0 else 3
                else:
                    new_dir = 0 if dx > 0 else 2
                if (new_dir + 2) % 4 == self.direction:
                    # هیچ راهی نیست
                    return
            self.direction = new_dir

        dx, dy = DIRECTIONS[self.direction]
        nx = head_x + dx
        ny = head_y + dy

        if nx < 0 or nx >= GRID_COLS or ny < 0 or ny >= GRID_ROWS:
            self.alive = False
            return

        self.body.appendleft((nx, ny))
        self.body.pop()

    def hit(self):
        self.hp -= 1
        self.flash_timer = 8
        if self.hp <= 0:
            self.alive = False

    def draw(self, surface):
        color = WHITE if self.flash_timer > 0 else NEON_MAGENTA
        for i, (bx, by) in enumerate(self.body):
            cx = GRID_X + bx * CELL_SIZE + CELL_SIZE / 2
            cy = GRID_Y + by * CELL_SIZE + CELL_SIZE / 2

            # هاله
            for r in range(2, 0, -1):
                glow_size = int(CELL_SIZE * 0.8 * (1 + r * 0.4))
                glow = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                alpha = 80 - r * 20
                pygame.draw.circle(glow, (*color, alpha), (glow_size, glow_size), glow_size)
                surface.blit(glow, (cx - glow_size, cy - glow_size))

            size = CELL_SIZE - 2
            rect = pygame.Rect(int(cx - size / 2), int(cy - size / 2), size, size)
            pygame.draw.rect(surface, color, rect, border_radius=6)
            pygame.draw.rect(surface, WHITE, rect, 2, border_radius=6)


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
#                    پس‌زمینه Grid
# ============================================================
_bg_cache = None


def build_background():
    global _bg_cache
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    # آسمان گرادیان
    for y in range(HEIGHT):
        t = y / HEIGHT
        c = (int(3 + 5 * t), int(5 + 10 * t), int(15 + 20 * t))
        pygame.draw.line(surf, c, (0, y), (WIDTH, y))

    # Grid تیره
    for i in range(GRID_COLS + 1):
        x = GRID_X + i * CELL_SIZE
        pygame.draw.line(surf, (15, 25, 50), (x, GRID_Y), (x, GRID_Y + GRID_H), 1)
    for j in range(GRID_ROWS + 1):
        y = GRID_Y + j * CELL_SIZE
        pygame.draw.line(surf, (15, 25, 50), (GRID_X, y), (GRID_X + GRID_W, y), 1)

    # حاشیه Grid (کادر اصلی)
    for i in range(5):
        alpha = 200 - i * 30
        c = (0, min(255, 200 + i * 15), 255)
        rect = pygame.Rect(GRID_X - i - 2, GRID_Y - i - 2, GRID_W + 2 * (i + 2), GRID_H + 2 * (i + 2))
        pygame.draw.rect(surf, (*c, alpha) if len(c) == 3 else c, rect, 2, border_radius=4)

    # کادر رنگی دور Grid
    pygame.draw.rect(surf, NEON_CYAN, (GRID_X - 2, GRID_Y - 2, GRID_W + 4, GRID_H + 4), 2, border_radius=6)
    pygame.draw.rect(surf, NEON_PURPLE, (GRID_X - 6, GRID_Y - 6, GRID_W + 12, GRID_H + 12), 1, border_radius=8)

    _bg_cache = surf


build_background()


def draw_background(surface):
    surface.blit(_bg_cache, (0, 0))


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

    # مار تزئینی توی منو
    menu_snake = Snake(5, 12, NEON_CYAN)
    for i in range(10):
        menu_snake.body.append((4 - i, 12))
    menu_snake_dir = 0
    menu_dir_timer = 0

    while True:
        game_surface.fill(BLACK)
        t = pygame.time.get_ticks() / 1000
        menu_time += 1
        mouse_pos = get_game_mouse_pos()

        draw_background(game_surface)

        # ذرات تزئینی
        for _ in range(30):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            pygame.draw.circle(game_surface, (60, 80, 130), (x, y), 1)

        # عنوان
        title_y = 120 + math.sin(t * 2) * 8
        draw_text(game_surface, "NEON", 72, WIDTH // 2 - 100, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "SNAKE", 72, WIDTH // 2 + 110, title_y, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, "EAT  /  GROW  /  SURVIVE", 20, WIDTH // 2, title_y + 65, (200, 200, 220), center=True)

        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 22, WIDTH // 2, title_y + 115, NEON_YELLOW, center=True, glow=True)

        # آمار
        total_games = len(game_history)
        total_food = sum(g.get('score', 0) // 10 for g in game_history)
        draw_text(game_surface, f"GAMES: {total_games}   FOOD EATEN: {total_food}", 14, WIDTH // 2, title_y + 145, NEON_PINK, center=True)

        # دکمه‌ها
        for b in [btn_start, btn_history, btn_settings, btn_achievements, btn_quit]:
            b.update(mouse_pos)
            b.draw(game_surface)

        # ذرات فعال
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


# ============================================================
#                    Settings
# ============================================================
def show_settings():
    global settings
    slider_sfx = Slider(WIDTH // 2, 180, 400, 12, settings['sfx_volume'], 0, 1, "SFX Volume")
    slider_music = Slider(WIDTH // 2, 270, 400, 12, settings['music_volume'], 0, 1, "Music Volume")

    btn_speed = Button(WIDTH // 2, 360, 280, 50,
                       f"SPEED: {settings['speed_mode'].upper()}",
                       NEON_GREEN, NEON_CYAN, 22)
    btn_wrap = Button(WIDTH // 2, 425, 280, 50,
                      f"WRAP: {'ON' if settings['wrap_mode'] else 'OFF'}",
                      NEON_GREEN if settings['wrap_mode'] else (100, 100, 100), NEON_CYAN, 22)
    btn_shake = Button(WIDTH // 2, 490, 280, 50,
                       f"SHAKE: {'ON' if settings['screen_shake'] else 'OFF'}",
                       NEON_GREEN if settings['screen_shake'] else (100, 100, 100), NEON_CYAN, 22)
    btn_reset = Button(WIDTH // 2 - 130, 560, 220, 50, "RESET SAVE", NEON_RED, NEON_ORANGE, 20)
    btn_back = Button(WIDTH // 2 + 130, 560, 220, 50, "BACK", NEON_CYAN, NEON_GREEN, 22)

    while True:
        game_surface.fill(DARK_BG)
        mouse_pos = get_game_mouse_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        draw_background(game_surface)
        # محو کردن
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 5, 220))
        game_surface.blit(overlay, (0, 0))

        box_w, box_h = 700, 600
        box_x = WIDTH // 2 - box_w // 2
        box_y = HEIGHT // 2 - box_h // 2 + 20
        pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h), border_radius=12)
        pygame.draw.rect(game_surface, NEON_PURPLE, (box_x, box_y, box_w, box_h), 3, border_radius=12)

        draw_text(game_surface, "SETTINGS", 48, WIDTH // 2, 70, NEON_CYAN, center=True, glow=True)

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

        # Speed mode
        btn_speed.update(mouse_pos)
        btn_speed.text = f"SPEED: {settings['speed_mode'].upper()}"
        btn_speed.draw(game_surface)

        # Wrap
        btn_wrap.update(mouse_pos)
        btn_wrap.text = f"WRAP: {'ON' if settings['wrap_mode'] else 'OFF'}"
        btn_wrap.color = NEON_GREEN if settings['wrap_mode'] else (100, 100, 100)
        btn_wrap.draw(game_surface)

        # Shake
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
            if btn_speed.is_clicked(event):
                modes = ['slow', 'normal', 'fast']
                idx = (modes.index(settings['speed_mode']) + 1) % len(modes)
                settings['speed_mode'] = modes[idx]
                save_async()
            if btn_wrap.is_clicked(event):
                settings['wrap_mode'] = not settings['wrap_mode']
                save_async()
            if btn_shake.is_clicked(event):
                settings['screen_shake'] = not settings['screen_shake']
                save_async()
            if btn_reset.is_clicked(event):
                settings['sfx_volume'] = 0.7
                settings['music_volume'] = 0.5
                settings['speed_mode'] = 'normal'
                settings['wrap_mode'] = False
                settings['screen_shake'] = True
                for k in achievements:
                    achievements[k]['unlocked'] = False
                highscore[0] = 0
                game_history.clear()
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


# ============================================================
#                    Achievements
# ============================================================
def show_achievements():
    btn_back = Button(WIDTH // 2, HEIGHT - 55, 240, 55, "BACK", NEON_CYAN, NEON_GREEN, 26)
    while True:
        game_surface.fill(DARK_BG)
        mouse_pos = get_game_mouse_pos()

        draw_background(game_surface)
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
            draw_text(game_surface, a['icon'], 18, cx + 35, y_pos + card_h // 2, icon_color, center=True)
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

        draw_background(game_surface)
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
                draw_text(game_surface, rank, 36, ix + 35, iy + (item_h - 8) // 2, rank_color, center=True, glow=True)
                draw_text(game_surface, f"SCORE: {score}", 20, ix + 70, iy + 6, WHITE)
                draw_text(game_surface, f"LENGTH: {entry.get('length', 0)}   TIME: {entry.get('duration', 0)}s",
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
    # تنظیمات اولیه بر اساس سختی
    base_delay = {'slow': 12, 'normal': 8, 'fast': 5}[settings['speed_mode']]

    # مار بازیکن
    player = Snake(GRID_COLS // 2, GRID_ROWS // 2, NEON_CYAN)
    player.move_delay = base_delay
    all_snakes = [player]

    # AI مار (بعد از چند ثانیه فعال میشه)
    ai_snake = None
    ai_spawn_timer = 0

    # باس
    boss = None
    boss_spawn_timer = 0

    # غذاها
    foods = []
    food_spawn_timer = 0
    power_spawn_timer = 0

    # دیوارهای متحرک
    walls = []
    wall_spawn_timer = 0

    # وضعیت
    score = 0
    display_score = 0
    combo = 0
    combo_timer = 0
    max_combo = 0
    food_eaten = 0
    powers_collected = 0
    total_frames = 0
    base_score_mult = 1

    # افکت‌ها
    screen_shake = 0
    flash = 0
    game_over = False
    paused = False
    final_score = 0
    final_length = 0
    new_achs = []
    notifications = []
    go_anim = 0
    game_saved = False

    # اعلان power-up فعال
    active_power = None
    active_power_timer = 0

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
        add_game_to_history(score, len(player.body), total_frames // FPS, new_achs)

    def spawn_food():
        """اسپاون غذا در مکان خالی"""
        occupied = set()
        for s in all_snakes:
            for b in s.body:
                occupied.add(b)
        if boss:
            for b in boss.body:
                occupied.add(b)
        for w in walls:
            occupied.add((w.x, w.y))
        for f in foods:
            occupied.add((f.x, f.y))

        empty = []
        for x in range(GRID_COLS):
            for y in range(GRID_ROWS):
                if (x, y) not in occupied:
                    empty.append((x, y))
        if not empty:
            return None
        x, y = random.choice(empty)
        kind = 'normal'
        # 20% شانس power-up
        if random.random() < 0.20:
            kind = random.choices(
                ['speed', 'slow', 'shrink', 'ghost', 'double', 'magnet', 'gold'],
                weights=[2, 2, 2, 1, 2, 2, 1]
            )[0]
        return Food(x, y, kind)

    # اسپاون اولیه غذا
    for _ in range(3):
        f = spawn_food()
        if f:
            foods.append(f)

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
                if event.key in (pygame.K_UP, pygame.K_w):
                    if not paused and not game_over:
                        player.set_direction(3)
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    if not paused and not game_over:
                        player.set_direction(1)
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    if not paused and not game_over:
                        player.set_direction(2)
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    if not paused and not game_over:
                        player.set_direction(0)
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

            # آپدیت اسکور نمایشی
            if display_score < score:
                display_score += max(1, (score - display_score) // 5)
                if display_score > score:
                    display_score = score

            # تایمر کمبو
            if combo_timer > 0:
                combo_timer -= 1
                if combo_timer == 0:
                    combo = 0

            # حرکت مار بازیکن
            player.move_timer += 1
            if player.move_timer >= player.move_delay:
                player.move_timer = 0
                before_len = len(player.body)
                player.move(foods, all_snakes)
                after_len = len(player.body)

                if not player.alive:
                    game_over = True
                    final_score = score
                    final_length = len(player.body)
                    highscore[0] = max(highscore[0], score)
                    if score >= 500:
                        try_unlock('score_500')
                    if score >= 2000:
                        try_unlock('score_2000')
                    if score >= 5000:
                        try_unlock('score_5000')
                    if settings['screen_shake']:
                        screen_shake = 30
                    flash = 200
                    play_sound('crash')
                    # انفجار مار
                    for bx, by in player.body:
                        cx = GRID_X + bx * CELL_SIZE + CELL_SIZE / 2
                        cy = GRID_Y + by * CELL_SIZE + CELL_SIZE / 2
                        spawn_particles(cx, cy, NEON_CYAN, 5, 1.5, 1.2, 1.2)
                    save_current()
                    game_saved = True
                    play_sound('gameover')
                    go_anim = 0

                # اگه غذا خورد
                if after_len > before_len or (len(player.body) > 0 and len(foods) < 3):
                    pass

            # بررسی خوردن غذا (به صورت جداگانه برای ردیابی)
            # این کار رو توی move انجام دادیم، ولی برای شمارش:
            # (در حال حاضر در move انجام می‌شه)

            # اسپاون AI مار بعد از 15 ثانیه
            if ai_snake is None and total_frames > FPS * 15:
                # جای خالی پیدا کن
                occupied = set()
                for b in player.body:
                    occupied.add(b)
                for x in range(2, GRID_COLS - 2):
                    for y in range(2, GRID_ROWS - 2):
                        if (x, y) not in occupied:
                            ai_snake = Snake(x, y, NEON_PINK, ai=True)
                            ai_snake.move_delay = base_delay + 2
                            all_snakes.append(ai_snake)
                            break
                    if ai_snake:
                        break

            # آپدیت AI
            if ai_snake and ai_snake.alive:
                ai_snake.move_timer += 1
                if ai_snake.move_timer >= ai_snake.move_delay:
                    ai_snake.move_timer = 0
                    ai_snake.ai_choose_direction(foods, all_snakes)
                    ai_snake.move(foods, all_snakes)
                    if not ai_snake.alive:
                        # AI مرد، امتیاز به بازیکن
                        score += 200
                        try_unlock('first_food')  # فقط برای اطمینان
                        # ذرات
                        for bx, by in ai_snake.body:
                            cx = GRID_X + bx * CELL_SIZE + CELL_SIZE / 2
                            cy = GRID_Y + by * CELL_SIZE + CELL_SIZE / 2
                            spawn_particles(cx, cy, NEON_PINK, 8, 1.5)
                        all_snakes.remove(ai_snake)
                        ai_snake = None

            # اسپاون باس هر 60 ثانیه
            boss_spawn_timer += 1
            if boss_spawn_timer > FPS * 60 and boss is None:
                boss_spawn_timer = 0
                if random.random() < 0.5:
                    boss = BossSnake()
                    play_sound('boss')
                    flash = 80

            # آپدیت باس
            if boss:
                if boss.alive:
                    boss.update(player.body)
                    # برخورد با بازیکن
                    for bx, by in boss.body:
                        if (bx, by) == player.body[0]:
                            # به باس آسیب می‌رسه
                            boss.hit()
                            try_unlock('boss_hit')
                            score += 50
                            player.grow_pending += 1  # رشد می‌کنه
                            # ذرات
                            cx = GRID_X + bx * CELL_SIZE + CELL_SIZE / 2
                            cy = GRID_Y + by * CELL_SIZE + CELL_SIZE / 2
                            spawn_particles(cx, cy, NEON_MAGENTA, 20, 1.5)
                            break
                    # برخورد مار با بدن باس
                    if boss.alive:
                        for bx, by in boss.body[1:]:
                            if (bx, by) == player.body[0]:
                                if player.ghost_mode <= 0:
                                    player.alive = False
                                break
                else:
                    # باس مرد
                    score += 500
                    for _ in range(60):
                        spawn_particles(
                            GRID_X + random.randint(0, GRID_W),
                            GRID_Y + random.randint(0, GRID_H),
                            NEON_MAGENTA, 3, 1.5, 1.3
                        )
                    if settings['screen_shake']:
                        screen_shake = 25
                    flash = 200
                    play_sound('crash')
                    boss = None

            # اسپاون غذا
            food_spawn_timer += 1
            if food_spawn_timer > 30 and len(foods) < 5:
                food_spawn_timer = 0
                f = spawn_food()
                if f:
                    foods.append(f)

            # اسپاون power-up اضافی
            power_spawn_timer += 1
            if power_spawn_timer > 300:
                power_spawn_timer = 0
                if random.random() < 0.5:
                    f = spawn_food()
                    if f:
                        if f.kind == 'normal':
                            f.kind = random.choice(['speed', 'slow', 'shrink', 'ghost', 'double', 'magnet'])
                            if f.kind == 'speed':
                                f.color = NEON_YELLOW
                            elif f.kind == 'slow':
                                f.color = NEON_BLUE
                            elif f.kind == 'shrink':
                                f.color = NEON_GREEN
                            elif f.kind == 'ghost':
                                f.color = NEON_PURPLE
                            elif f.kind == 'double':
                                f.color = NEON_ORANGE
                            elif f.kind == 'magnet':
                                f.color = NEON_MAGENTA
                        foods.append(f)

            # اسپاون دیوار متحرک
            wall_spawn_timer += 1
            if wall_spawn_timer > FPS * 20:
                wall_spawn_timer = 0
                if random.random() < 0.4:
                    walls.append(MovingWall())

            # آپدیت دیوارها
            for w in walls[:]:
                w.update()
                if not w.alive:
                    walls.remove(w)

            # آپدیت غذاها
            for f in foods[:]:
                f.update()
                if f.lifetime <= 0:
                    foods.remove(f)

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

            # آپدیت امتیاز بر اساس طول
            score += max(1, len(player.body) // 10)

        # ============================================================
        #                    رسم
        # ============================================================
        game_surface.fill(BLACK)
        offset_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        offset_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0

        play_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        draw_background(play_layer)

        # دیوارها
        for w in walls:
            w.draw(play_layer)

        # غذاها
        for f in foods:
            f.draw(play_layer)

        # باس
        if boss:
            boss.draw(play_layer)

        # مارها
        for s in all_snakes:
            s.draw(play_layer)

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
        # پنل بالا
        hud_panel = pygame.Surface((WIDTH, 90), pygame.SRCALPHA)
        for y in range(90):
            alpha = int(180 * (1 - y / 90))
            pygame.draw.line(hud_panel, (5, 10, 25, alpha), (0, y), (WIDTH, y))
        game_surface.blit(hud_panel, (0, 0))
        pygame.draw.line(game_surface, NEON_CYAN, (0, 90), (WIDTH, 90), 1)

        # عنوان
        draw_text(game_surface, "NEON", 26, 25, 15, WHITE)
        draw_text(game_surface, "SNAKE", 26, 25 + get_font(26).size("NEON ")[0], 15, NEON_CYAN, glow=True)
        draw_text(game_surface, "EAT / GROW / SURVIVE", 12, 25, 48, (180, 200, 220))

        # SCORE
        draw_text(game_surface, "SCORE", 14, WIDTH - 25, 12, NEON_CYAN)
        draw_text(game_surface, f"{display_score}", 26, WIDTH - 25, 30, WHITE, glow=True)

        # LENGTH
        draw_text(game_surface, f"LENGTH: {len(player.body)}", 16, WIDTH - 25, 62, NEON_GREEN)

        # COMBO
        if combo > 1:
            combo_color = NEON_GREEN if combo < 5 else NEON_YELLOW if combo < 10 else NEON_PINK
            scale = 1 + math.sin(t * 8) * 0.1
            draw_text(game_surface, f"x{combo} COMBO", int(20 * scale), WIDTH // 2, 30,
                      combo_color, center=True, glow=True)

        # حالت‌های فعال
        power_y = 100
        if player.ghost_mode > 0:
            draw_text(game_surface, f"GHOST {player.ghost_mode // FPS + 1}s", 14, 25, power_y, NEON_PURPLE)
            power_y += 20
        if player.magnet_mode > 0:
            draw_text(game_surface, f"MAGNET {player.magnet_mode // FPS + 1}s", 14, 25, power_y, NEON_MAGENTA)
            power_y += 20
        if player.double_points > 0:
            draw_text(game_surface, f"x2 POINTS {player.double_points // FPS + 1}s", 14, 25, power_y, NEON_ORANGE)
            power_y += 20

        # اعلان باس
        if boss and boss.alive:
            draw_text(game_surface, f"BOSS HP: {boss.hp}/{boss.max_hp}", 16, WIDTH // 2, 100,
                      NEON_MAGENTA, center=True, glow=True)

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
            draw_text(game_surface, f"SCORE: {final_score}", 32, WIDTH // 2, box_y + 115,
                      WHITE, center=True)
            draw_text(game_surface, f"LENGTH: {final_length}", 20, WIDTH // 2, box_y + 148,
                      NEON_GREEN, center=True)
            hs = highscore[0]
            if final_score >= hs and final_score > 0:
                draw_text(game_surface, "* NEW HIGH SCORE! *", 22, WIDTH // 2, box_y + 180,
                          NEON_YELLOW, center=True, glow=True)
            else:
                draw_text(game_surface, f"HIGH SCORE: {hs}", 18, WIDTH // 2, box_y + 180,
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