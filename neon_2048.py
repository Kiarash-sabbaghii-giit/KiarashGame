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

BASE_W, BASE_H = 900, 950
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("NEON 2048")
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

# رنگ کاشی‌ها بر اساس عدد
TILE_COLORS = {
    0: (30, 30, 50),
    2: (100, 200, 255),
    4: (50, 150, 255),
    8: (100, 100, 255),
    16: (170, 60, 255),
    32: (255, 60, 180),
    64: (255, 50, 100),
    128: (255, 100, 50),
    256: (255, 160, 30),
    512: (255, 230, 0),
    1024: (50, 255, 120),
    2048: (0, 255, 200),
    4096: (255, 0, 200),
    8192: (255, 100, 255),
}

# --- ابعاد Grid ---
GRID_SIZE = 4
CELL_SIZE = 130
CELL_GAP = 15
GRID_W = GRID_SIZE * CELL_SIZE + (GRID_SIZE + 1) * CELL_GAP
GRID_H = GRID_W
GRID_X = (WIDTH - GRID_W) // 2
GRID_Y = 120

# --- ذخیره ---
SAVE_FILE = "neon_2048_save.json"
settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'screen_shake': True,
    'animation_speed': 0.15,
}
achievements = {
    'first_tile': {'name': 'FIRST TILE', 'desc': 'Reach tile 4', 'unlocked': False, 'icon': '4'},
    'tile_16': {'name': 'GROWING', 'desc': 'Reach tile 16', 'unlocked': False, 'icon': '16'},
    'tile_64': {'name': 'ROOKIE', 'desc': 'Reach tile 64', 'unlocked': False, 'icon': '64'},
    'tile_128': {'name': 'VETERAN', 'desc': 'Reach tile 128', 'unlocked': False, 'icon': '128'},
    'tile_256': {'name': 'MASTER', 'desc': 'Reach tile 256', 'unlocked': False, 'icon': '256'},
    'tile_512': {'name': 'LEGEND', 'desc': 'Reach tile 512', 'unlocked': False, 'icon': '512'},
    'tile_1024': {'name': 'GRANDMASTER', 'desc': 'Reach tile 1024', 'unlocked': False, 'icon': '1K'},
    'tile_2048': {'name': '2048!', 'desc': 'Reach tile 2048', 'unlocked': False, 'icon': '2048'},
    'tile_4096': {'name': 'ULTIMATE', 'desc': 'Reach tile 4096', 'unlocked': False, 'icon': '4096'},
    'score_1000': {'name': 'SCORER', 'desc': 'Score 1000 points', 'unlocked': False, 'icon': '$1K'},
    'score_5000': {'name': 'ACE', 'desc': 'Score 5000 points', 'unlocked': False, 'icon': '$5K'},
    'score_20000': {'name': 'CHAMPION', 'desc': 'Score 20000 points', 'unlocked': False, 'icon': '$20K'},
    'move_100': {'name': 'PERSISTENT', 'desc': 'Make 100 moves', 'unlocked': False, 'icon': 'M100'},
    'move_500': {'name': 'DEDICATED', 'desc': 'Make 500 moves', 'unlocked': False, 'icon': 'M500'},
    'no_undo': {'name': 'PURIST', 'desc': 'Reach 2048 without undo', 'unlocked': False, 'icon': 'P'},
}
highscore = [0]
game_history = []
total_moves = [0]
total_games = [0]
total_tiles_created = [0]


def load_save():
    global settings, achievements, highscore, game_history, total_moves, total_games, total_tiles_created
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
            settings.update(data.get('settings', {}))
            for k, v in data.get('achievements', {}).items():
                if k in achievements:
                    achievements[k]['unlocked'] = v
            highscore[0] = data.get('highscore', 0)
            game_history = data.get('game_history', [])
            total_moves[0] = data.get('total_moves', 0)
            total_games[0] = data.get('total_games', 0)
            total_tiles_created[0] = data.get('total_tiles_created', 0)
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
                'total_moves': total_moves[0],
                'total_games': total_games[0],
                'total_tiles_created': total_tiles_created[0],
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


def add_game_to_history(score, max_tile, moves, won, new_achs):
    entry = {
        'score': score,
        'max_tile': max_tile,
        'moves': moves,
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
    sounds['move'] = make_sound(400, 600, 0.05, 0.10, 'square')
    sounds['merge'] = make_sound(600, 1200, 0.15, 0.20, 'sine')
    sounds['big_merge'] = make_sound(800, 2000, 0.3, 0.25, 'sine')
    sounds['new_tile'] = make_sound(500, 800, 0.1, 0.12, 'sine')
    sounds['win'] = make_sound(600, 2000, 1.0, 0.30, 'sine')
    sounds['gameover'] = make_sound(400, 60, 1.5, 0.30, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['undo'] = make_sound(1000, 500, 0.2, 0.20, 'sine')

    bass = [82.4, 82.4, 73.4, 73.4, 65.4, 65.4, 82.4, 82.4]
    lead = [523, 659, 784, 659, 523, 494, 440, 494]
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
#                    Tile
# ============================================================
class Tile:
    def __init__(self, value, row, col):
        self.value = value
        self.row = row
        self.col = col
        # موقعیت فعلی (پیکسل) برای انیمیشن
        self.x, self.y = self.get_target_pos()
        # موقعیت قبلی برای انیمیشن
        self.prev_x = self.x
        self.prev_y = self.y
        self.anim_progress = 1.0
        self.merged_from = None  # موقعیت قبلی برای انیمیشن merge
        self.is_new = True
        self.merge_pop = 0  # انیمیشن pop بعد از merge
        self.spawn_anim = 0  # انیمیشن ورود

    def get_target_pos(self):
        x = GRID_X + CELL_GAP + self.col * (CELL_SIZE + CELL_GAP)
        y = GRID_Y + CELL_GAP + self.row * (CELL_SIZE + CELL_GAP)
        return x, y

    def set_pos(self, row, col):
        self.row = row
        self.col = col
        self.prev_x = self.x
        self.prev_y = self.y
        self.anim_progress = 0.0
        tx, ty = self.get_target_pos()
        self.x = tx
        self.y = ty

    def update(self, dt=1.0):
        if self.anim_progress < 1.0:
            self.anim_progress += settings['animation_speed'] * dt
            if self.anim_progress > 1.0:
                self.anim_progress = 1.0
        if self.spawn_anim > 0:
            self.spawn_anim -= 0.1 * dt
            if self.spawn_anim < 0:
                self.spawn_anim = 0
        if self.merge_pop > 0:
            self.merge_pop -= 0.08 * dt
            if self.merge_pop < 0:
                self.merge_pop = 0

    def get_current_pos(self):
        """موقعیت فعلی با interpolate"""
        if self.anim_progress >= 1.0:
            return self.x, self.y
        t = self.anim_progress
        # ease out
        t = 1 - (1 - t) ** 3
        cx = self.prev_x + (self.x - self.prev_x) * t
        cy = self.prev_y + (self.y - self.prev_y) * t
        return cx, cy

    def get_size_mult(self):
        """اندازه با انیمیشن"""
        mult = 1.0
        if self.spawn_anim > 0:
            mult *= 1 - self.spawn_anim * 0.5
        if self.merge_pop > 0:
            mult *= 1 + self.merge_pop * 0.3
        return mult

    def draw(self, surface):
        cx, cy = self.get_current_pos()
        size = CELL_SIZE * self.get_size_mult()
        offset = (CELL_SIZE - size) / 2

        color = TILE_COLORS.get(self.value, (255, 255, 255))

        # هاله
        for hr in range(3, 0, -1):
            glow_size = size + hr * 10
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*color, 50 - hr * 12),
                             (0, 0, glow_size, glow_size), border_radius=12)
            surface.blit(glow, (cx + offset - hr * 5, cy + offset - hr * 5))

        # بدنه
        rect = pygame.Rect(int(cx + offset), int(cy + offset), int(size), int(size))
        pygame.draw.rect(surface, (color[0] // 4, color[1] // 4, color[2] // 4),
                         rect, border_radius=12)
        pygame.draw.rect(surface, color, rect, 3, border_radius=12)
        pygame.draw.rect(surface, WHITE, rect, 1, border_radius=12)

        # عدد
        value = self.value
        if value < 100:
            font_size = 52
        elif value < 1000:
            font_size = 42
        elif value < 10000:
            font_size = 32
        else:
            font_size = 26

        text_color = WHITE if value < 128 else (0, 0, 0)
        draw_text(surface, str(value), font_size,
                  rect.centerx, rect.centery - font_size // 3,
                  text_color, center=True, bold=True)


# ============================================================
#                    Game State
# ============================================================
class Game2048:
    def __init__(self):
        self.reset()

    def reset(self):
        self.grid = [[None for _ in range(4)] for _ in range(4)]
        self.tiles = []
        self.score = 0
        self.display_score = 0
        self.moves = 0
        self.game_over = False
        self.won = False
        self.keep_playing = False
        self.max_tile = 0
        self.undo_stack = []
        self.used_undo = False
        self.new_merge_events = []  # برای انیمیشن

        # اسپاون دو کاشی اولیه
        self.add_random_tile()
        self.add_random_tile()

    def add_random_tile(self):
        empty = []
        for r in range(4):
            for c in range(4):
                if self.grid[r][c] is None:
                    empty.append((r, c))
        if not empty:
            return False
        r, c = random.choice(empty)
        value = 2 if random.random() < 0.9 else 4
        tile = Tile(value, r, c)
        tile.spawn_anim = 1.0
        self.grid[r][c] = tile
        self.tiles.append(tile)
        total_tiles_created[0] += 1
        return True

    def save_undo(self):
        # ذخیره وضعیت قبل از حرکت
        snapshot = []
        for t in self.tiles:
            snapshot.append({
                'value': t.value,
                'row': t.row,
                'col': t.col,
            })
        self.undo_stack.append({
            'tiles': snapshot,
            'score': self.score,
            'moves': self.moves,
            'max_tile': self.max_tile,
            'won': self.won,
        })
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            return False
        state = self.undo_stack.pop()
        self.tiles.clear()
        self.grid = [[None for _ in range(4)] for _ in range(4)]
        for t in state['tiles']:
            tile = Tile(t['value'], t['row'], t['col'])
            self.grid[t['row']][t['col']] = tile
            self.tiles.append(tile)
        self.score = state['score']
        self.moves = state['moves']
        self.max_tile = state['max_tile']
        self.won = state['won']
        self.game_over = False
        self.used_undo = True
        play_sound('undo')
        return True

    def can_move(self):
        # چک کن آیا حرکتی ممکنه
        for r in range(4):
            for c in range(4):
                if self.grid[r][c] is None:
                    return True
                # چک کن هل دادن به سمت دیگه
                if c < 3 and self.grid[r][c] and self.grid[r][c + 1]:
                    if self.grid[r][c].value == self.grid[r][c + 1].value:
                        return True
                if r < 3 and self.grid[r][c] and self.grid[r + 1][c]:
                    if self.grid[r][c].value == self.grid[r + 1][c].value:
                        return True
        return False

    def move(self, direction):
        """direction: 'up', 'down', 'left', 'right'"""
        if self.game_over:
            return False

        self.save_undo()
        moved = False
        merged_positions = []

        # تبدیل جهت به بردار
        if direction == 'left':
            dr, dc = 0, -1
            order = [(r, c) for r in range(4) for c in range(4)]
        elif direction == 'right':
            dr, dc = 0, 1
            order = [(r, c) for r in range(4) for c in range(3, -1, -1)]
        elif direction == 'up':
            dr, dc = -1, 0
            order = [(r, c) for c in range(4) for r in range(4)]
        elif direction == 'down':
            dr, dc = 1, 0
            order = [(r, c) for c in range(4) for r in range(3, -1, -1)]
        else:
            return False

        # پاک کردن merged_positions قبلی
        for tile in self.tiles:
            tile.merged_from = None

        # حرکت
        for r, c in order:
            if self.grid[r][c] is None:
                continue
            tile = self.grid[r][c]

            # پیدا کردن دورترین موقعیت در جهت
            tr, tc = r, c
            while True:
                nr, nc = tr + dr, tc + dc
                if nr < 0 or nr >= 4 or nc < 0 or nc >= 4:
                    break
                if self.grid[nr][nc] is None:
                    tr, tc = nr, nc
                    continue
                # چک merge
                other = self.grid[nr][nc]
                if other.value == tile.value and other.merged_from != 'merged':
                    # Merge!
                    new_value = tile.value * 2
                    other.value = new_value
                    other.merge_pop = 1.0
                    if new_value > self.max_tile:
                        self.max_tile = new_value
                    self.score += new_value
                    if new_value == 2048 and not self.won:
                        self.won = True
                        if not self.keep_playing:
                            play_sound('win')
                    # انیمیشن: tile قبلی رو حذف کن و موقعیتش رو سیو کن
                    other.merged_from = (tile.x, tile.y)
                    # tile رو حذف کن
                    self.grid[r][c] = None
                    if tile in self.tiles:
                        self.tiles.remove(tile)
                    # ذرات
                    color = TILE_COLORS.get(new_value, WHITE)
                    spawn_particles(other.x + CELL_SIZE // 2, other.y + CELL_SIZE // 2,
                                    color, 15, 1.5, 1.2, 1.0)
                    if new_value >= 256:
                        play_sound('big_merge')
                        for _ in range(20):
                            spawn_particles(other.x + CELL_SIZE // 2, other.y + CELL_SIZE // 2,
                                            color, 1, 2.0, 1.5, 1.5)
                    else:
                        play_sound('merge')
                    # merged flag
                    other.merged_from = 'merged'
                    tr, tc = nr, nc
                    moved = True
                    break
                else:
                    break

            # اگه موقعیت تغییر کرد
            if (tr, tc) != (r, c):
                self.grid[r][c] = None
                if self.grid[tr][tc] is None:
                    self.grid[tr][tc] = tile
                    tile.set_pos(tr, tc)
                    moved = True

        # اگه حرکت کرد، کاشی جدید اضافه کن
        if moved:
            self.add_random_tile()
            self.moves += 1
            total_moves[0] += 1
            play_sound('new_tile')

            # چک دستاوردها
            for t in self.tiles:
                v = t.value
                if v >= 4: unlock_achievement('first_tile')
                if v >= 16: unlock_achievement('tile_16')
                if v >= 64: unlock_achievement('tile_64')
                if v >= 128: unlock_achievement('tile_128')
                if v >= 256: unlock_achievement('tile_256')
                if v >= 512: unlock_achievement('tile_512')
                if v >= 1024: unlock_achievement('tile_1024')
                if v >= 2048:
                    unlock_achievement('tile_2048')
                    if not self.used_undo:
                        unlock_achievement('no_undo')
                if v >= 4096: unlock_achievement('tile_4096')

            if self.score >= 1000: unlock_achievement('score_1000')
            if self.score >= 5000: unlock_achievement('score_5000')
            if self.score >= 20000: unlock_achievement('score_20000')
            if self.moves >= 100: unlock_achievement('move_100')
            if self.moves >= 500: unlock_achievement('move_500')

            # چک game over
            if not self.can_move():
                self.game_over = True
                play_sound('gameover')

        return moved

    def update(self, dt=1.0):
        for tile in self.tiles:
            tile.update(dt)
        # آپدیت اسکور نمایشی
        if self.display_score < self.score:
            self.display_score += max(1, (self.score - self.display_score) // 5)
            if self.display_score > self.score:
                self.display_score = self.score

    def draw(self, surface):
        # پس‌زمینه Grid
        grid_rect = pygame.Rect(GRID_X, GRID_Y, GRID_W, GRID_H)
        pygame.draw.rect(surface, (10, 5, 25), grid_rect, border_radius=15)
        pygame.draw.rect(surface, NEON_PURPLE, grid_rect, 3, border_radius=15)
        pygame.draw.rect(surface, NEON_CYAN, grid_rect, 1, border_radius=15)

        # خونه‌های خالی
        for r in range(4):
            for c in range(4):
                x = GRID_X + CELL_GAP + c * (CELL_SIZE + CELL_GAP)
                y = GRID_Y + CELL_GAP + r * (CELL_SIZE + CELL_GAP)
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(surface, (20, 15, 40), rect, border_radius=10)
                pygame.draw.rect(surface, (40, 30, 60), rect, 2, border_radius=10)

        # کاشی‌ها
        for tile in self.tiles:
            tile.draw(surface)


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
#                    Menu
# ============================================================
def show_menu():
    menu_time = 0
    btn_start = Button(WIDTH // 2, HEIGHT // 2 + 30, 320, 55, "NEW GAME", NEON_CYAN, NEON_GREEN, 28)
    btn_history = Button(WIDTH // 2, HEIGHT // 2 + 95, 320, 45, "HISTORY", NEON_BLUE, NEON_CYAN, 22)
    btn_settings = Button(WIDTH // 2, HEIGHT // 2 + 150, 320, 45, "SETTINGS", NEON_PURPLE, NEON_PINK, 22)
    btn_achievements = Button(WIDTH // 2, HEIGHT // 2 + 205, 320, 45, "ACHIEVEMENTS", NEON_YELLOW, NEON_ORANGE, 22)
    btn_quit = Button(WIDTH // 2, HEIGHT // 2 + 260, 320, 42, "QUIT", NEON_RED, NEON_ORANGE, 20)
    btn_fullscreen = Button(WIDTH - 40, 30, 40, 40, "[]", NEON_PURPLE, NEON_CYAN, 20)

    # کاشی‌های تزئینی
    demo_tiles = []
    for i in range(8):
        demo_tiles.append({
            'x': random.randint(50, WIDTH - 100),
            'y': random.randint(50, HEIGHT - 100),
            'value': random.choice([2, 4, 8, 16, 32, 64]),
            'vy': random.uniform(0.3, 1.0),
            'size': 60,
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

        # کاشی‌های تزئینی
        for dt in demo_tiles:
            dt['y'] += dt['vy']
            if dt['y'] > HEIGHT:
                dt['y'] = -100
                dt['x'] = random.randint(50, WIDTH - 100)
                dt['value'] = random.choice([2, 4, 8, 16, 32, 64])
            color = TILE_COLORS.get(dt['value'], WHITE)
            # هاله
            for hr in range(3, 0, -1):
                glow = pygame.Surface((dt['size'] + hr * 10, dt['size'] + hr * 10), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*color, 30 - hr * 8),
                                 (0, 0, dt['size'] + hr * 10, dt['size'] + hr * 10), border_radius=10)
                game_surface.blit(glow, (dt['x'] - hr * 5, dt['y'] - hr * 5))
            rect = pygame.Rect(dt['x'], dt['y'], dt['size'], dt['size'])
            pygame.draw.rect(game_surface, (color[0] // 4, color[1] // 4, color[2] // 4),
                             rect, border_radius=10)
            pygame.draw.rect(game_surface, color, rect, 3, border_radius=10)
            draw_text(game_surface, str(dt['value']), 28, rect.centerx, rect.centery - 10,
                      WHITE, center=True, bold=True)

        # عنوان
        title_y = 150 + math.sin(t * 2) * 8
        draw_text(game_surface, "NEON", 72, WIDTH // 2 - 100, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "2048", 72, WIDTH // 2 + 100, title_y, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, "MERGE  /  COMBINE  /  WIN", 20, WIDTH // 2, title_y + 65,
                  (200, 200, 220), center=True)

        hs = highscore[0]
        if hs > 0:
            draw_text(game_surface, f"HIGH SCORE: {hs}", 22, WIDTH // 2, title_y + 115,
                      NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, f"GAMES: {total_games[0]}   MOVES: {total_moves[0]}",
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
    slider_anim = Slider(WIDTH // 2, 380, 400, 12, settings['animation_speed'] / 0.3, 0, 1, "Animation Speed")
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
        slider_anim.update(mouse_pos, mouse_pressed)
        settings['sfx_volume'] = slider_sfx.value
        settings['music_volume'] = slider_music.value
        settings['animation_speed'] = 0.05 + slider_anim.value * 0.25
        if music_sound[0]:
            try:
                music_sound[0].set_volume(settings['music_volume'] * 0.5)
            except:
                pass

        slider_sfx.draw(game_surface)
        slider_music.draw(game_surface)
        slider_anim.draw(game_surface)

        # نمایش سرعت
        speed_val = settings['animation_speed']
        if speed_val < 0.15:
            speed_label, speed_color = "SLOW", NEON_GREEN
        elif speed_val < 0.22:
            speed_label, speed_color = "NORMAL", NEON_CYAN
        else:
            speed_label, speed_color = "FAST", NEON_RED
        draw_text(game_surface, speed_label, 20, WIDTH // 2, 410, speed_color, center=True)

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
                settings['animation_speed'] = 0.15
                settings['screen_shake'] = True
                for k in achievements:
                    achievements[k]['unlocked'] = False
                highscore[0] = 0
                game_history.clear()
                total_moves[0] = 0
                total_games[0] = 0
                total_tiles_created[0] = 0
                save_async()
                slider_sfx.value = 0.7
                slider_music.value = 0.5
                slider_anim.value = 0.4
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
                if score >= 20000:
                    rank_color, rank = NEON_PINK, "S"
                elif score >= 10000:
                    rank_color, rank = NEON_YELLOW, "A"
                elif score >= 5000:
                    rank_color, rank = NEON_GREEN, "B"
                elif score >= 1000:
                    rank_color, rank = NEON_CYAN, "C"
                else:
                    rank_color, rank = (150, 150, 180), "D"
                pygame.draw.rect(game_surface, (15, 8, 30), (ix, iy, iw, item_h - 8), border_radius=6)
                pygame.draw.rect(game_surface, rank_color, (ix, iy, iw, item_h - 8), 2, border_radius=6)
                draw_text(game_surface, rank, 32, ix + 35, iy + (item_h - 8) // 2, rank_color, center=True, glow=True)
                draw_text(game_surface, f"SCORE: {score}", 20, ix + 70, iy + 6, WHITE)
                draw_text(game_surface, f"TILE: {entry.get('max_tile', 0)}   MOVES: {entry.get('moves', 0)}",
                          14, ix + 70, iy + 30, (180, 180, 200))
                draw_text(game_surface, entry.get('date', '?'), 12, ix + iw - 180, iy + 10, NEON_CYAN)
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
    game = Game2048()
    total_games[0] += 1

    # Key repeat
    key_repeat_timer = 0
    key_repeat_delay = 15
    held_direction = None

    # امتیاز و آمار
    final_score = 0
    final_tile = 0
    game_saved = False

    # افکت‌ها
    screen_shake = 0
    flash = 0
    new_achs = []
    notifications = []
    go_anim = 0

    # دکمه‌ها
    btn_resume = Button(WIDTH // 2, HEIGHT // 2 + 20, 300, 60, "RESUME", NEON_GREEN, NEON_CYAN, 28)
    btn_pause_menu = Button(WIDTH // 2, HEIGHT // 2 + 100, 300, 55, "MAIN MENU", NEON_RED, NEON_ORANGE, 24)
    btn_restart = Button(WIDTH // 2, HEIGHT // 2 + 70, 300, 60, "NEW GAME", NEON_CYAN, NEON_GREEN, 28)
    btn_menu = Button(WIDTH // 2, HEIGHT // 2 + 145, 300, 55, "MAIN MENU", NEON_YELLOW, NEON_ORANGE, 24)
    btn_undo = Button(WIDTH - 100, 60, 140, 45, "UNDO", NEON_ORANGE, NEON_YELLOW, 18)
    btn_keep = Button(WIDTH // 2, HEIGHT // 2 + 80, 300, 60, "KEEP PLAYING", NEON_GREEN, NEON_CYAN, 24)

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
        max_tile = 0
        for t in game.tiles:
            if t.value > max_tile:
                max_tile = t.value
        add_game_to_history(game.score, max_tile, game.moves, game.won, new_achs)

    paused = False
    show_win_dialog = False

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

            if paused and not game.game_over:
                if btn_resume.is_clicked(event):
                    paused = False
                if btn_pause_menu.is_clicked(event):
                    stop_music()
                    if not game_saved:
                        save_current()
                        game_saved = True
                    return

            if game.game_over:
                if btn_restart.is_clicked(event):
                    stop_music()
                    play_game()
                    return
                if btn_menu.is_clicked(event):
                    stop_music()
                    return

            if show_win_dialog:
                if btn_keep.is_clicked(event):
                    show_win_dialog = False
                    game.keep_playing = True
                    continue

            if event.type == pygame.KEYDOWN:
                if not paused and not game.game_over and not show_win_dialog:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        if game.move('left'):
                            held_direction = 'left'
                            key_repeat_timer = 0
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        if game.move('right'):
                            held_direction = 'right'
                            key_repeat_timer = 0
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        if game.move('up'):
                            held_direction = 'up'
                            key_repeat_timer = 0
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        if game.move('down'):
                            held_direction = 'down'
                            key_repeat_timer = 0
                    elif event.key == pygame.K_z:
                        game.undo()

                if event.key == pygame.K_p and not game.game_over:
                    paused = not paused
                if event.key == pygame.K_r and game.game_over:
                    stop_music()
                    play_game()
                    return
                if event.key == pygame.K_ESCAPE:
                    stop_music()
                    if not game_saved:
                        save_current()
                        game_saved = True
                    return

            if event.type == pygame.KEYUP:
                if event.key in [pygame.K_LEFT, pygame.K_a] and held_direction == 'left':
                    held_direction = None
                elif event.key in [pygame.K_RIGHT, pygame.K_d] and held_direction == 'right':
                    held_direction = None
                elif event.key in [pygame.K_UP, pygame.K_w] and held_direction == 'up':
                    held_direction = None
                elif event.key in [pygame.K_DOWN, pygame.K_s] and held_direction == 'down':
                    held_direction = None

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not paused and not game.game_over and not show_win_dialog:
                    # کلیک روی دکمه Undo
                    if btn_undo.rect.collidepoint(mouse_pos):
                        if game.undo():
                            pass

        # Key repeat
        if held_direction and not paused and not game.game_over:
            key_repeat_timer += 1
            if key_repeat_timer > key_repeat_delay:
                key_repeat_timer = 0
                game.move(held_direction)

        for notif in notifications[:]:
            notif['timer'] -= 1
            if notif['timer'] <= 0:
                notifications.remove(notif)

        # چک برد
        if game.won and not game.keep_playing and not show_win_dialog:
            show_win_dialog = True
            play_sound('win')
            for _ in range(100):
                spawn_particles(WIDTH // 2, HEIGHT // 2, NEON_YELLOW, 1, 3.0, 2.0, 2.0)

        if paused and not game.game_over:
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

        if not game.game_over and not paused:
            game.update()

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

        # پس‌زمینه
        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            game_surface.blit(s, (0, y))
        for _ in range(50):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            b = random.randint(80, 150)
            pygame.draw.circle(game_surface, (b, b, b + 40), (x, y), 1)

        # عنوان
        draw_text(game_surface, "NEON 2048", 28, 25, 20, NEON_CYAN, glow=True)

        # امتیاز و Best
        draw_text(game_surface, f"SCORE: {game.display_score}", 22, WIDTH - 25, 20, WHITE, glow=True)
        if highscore[0] > 0:
            draw_text(game_surface, f"BEST: {highscore[0]}", 16, WIDTH - 25, 50, NEON_YELLOW)

        # Undo button
        btn_undo.update(mouse_pos)
        btn_undo.draw(game_surface)
        if game.undo_stack:
            draw_text(game_surface, f"x{len(game.undo_stack)}", 12, btn_undo.rect.right - 15, btn_undo.rect.centery - 5, WHITE, center=True)

        # Grid و کاشی‌ها
        game.draw(game_surface)

        # ذرات
        for p in active_particles:
            p.draw(game_surface)

        # Moves
        draw_text(game_surface, f"MOVES: {game.moves}", 16, WIDTH // 2, 90, NEON_YELLOW, center=True)

        # Notifications
        for i, notif in enumerate(notifications):
            ny = 130 + i * 55
            alpha = min(255, notif['timer'] * 2)
            ach = notif['ach']
            notif_surf = pygame.Surface((340, 50), pygame.SRCALPHA)
            notif_surf.fill((10, 5, 25, min(220, alpha)))
            game_surface.blit(notif_surf, (WIDTH - 360, ny))
            pygame.draw.rect(game_surface, NEON_YELLOW, (WIDTH - 360, ny, 340, 50), 2)
            draw_text(game_surface, "ACHIEVEMENT!", 11, WIDTH - 345, ny + 4, NEON_YELLOW)
            draw_text(game_surface, ach['name'], 16, WIDTH - 345, ny + 22, WHITE, glow=True)

        # راهنما
        if game.moves < 3:
            draw_text(game_surface, "USE ARROW KEYS or WASD to move tiles", 16,
                      WIDTH // 2, HEIGHT - 60, NEON_CYAN, center=True)
            draw_text(game_surface, "Z: Undo  |  P: Pause  |  F11: Fullscreen", 12,
                      WIDTH // 2, HEIGHT - 35, (150, 180, 220), center=True)

        # Win Dialog
        if show_win_dialog:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            game_surface.blit(overlay, (0, 0))
            box_w = 500
            box_h = 300
            box_x = WIDTH // 2 - box_w // 2
            box_y = HEIGHT // 2 - box_h // 2
            pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h))
            pygame.draw.rect(game_surface, NEON_YELLOW, (box_x, box_y, box_w, box_h), 4)
            draw_text(game_surface, "YOU WIN!", 70, WIDTH // 2, box_y + 60,
                      NEON_YELLOW, center=True, glow=True)
            draw_text(game_surface, "You reached 2048!", 24,
                      WIDTH // 2, box_y + 130, WHITE, center=True)
            btn_keep.update(mouse_pos)
            btn_keep.draw(game_surface)

        # Game Over
        if game.game_over and not show_win_dialog:
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

            # اگه باخت ولی به هدف رسید
            if game.max_tile >= 2048:
                draw_text(game_surface, "GAME OVER", 60, WIDTH // 2, box_y + 55,
                          NEON_YELLOW, center=True, glow=True)
                draw_text(game_surface, f"Reached: {game.max_tile}", 24,
                          WIDTH // 2, box_y + 115, NEON_GREEN, center=True)
            else:
                draw_text(game_surface, "GAME OVER", 60, WIDTH // 2, box_y + 55,
                          NEON_RED, center=True, glow=True)
                draw_text(game_surface, f"Best Tile: {game.max_tile}", 24,
                          WIDTH // 2, box_y + 115, NEON_YELLOW, center=True)

            draw_text(game_surface, f"SCORE: {game.score}", 32,
                      WIDTH // 2, box_y + 160, WHITE, center=True)
            draw_text(game_surface, f"MOVES: {game.moves}",
                      16, WIDTH // 2, box_y + 200, NEON_CYAN, center=True)

            if go_anim > 15:
                btn_restart.update(mouse_pos)
                btn_menu.update(mouse_pos)
                btn_restart.draw(game_surface)
                btn_menu.draw(game_surface)

        present()

        # ذخیره بهترین امتیاز
        if game.score > highscore[0]:
            highscore[0] = game.score

        # اگه بازی تموم شد، ذخیره کن
        if game.game_over and not game_saved:
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
        elif result == 'start':
            play_game()
    pygame.quit()


if __name__ == "__main__":
    main()