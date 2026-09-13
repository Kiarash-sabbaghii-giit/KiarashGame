import pygame
import random
import math
import array
import threading
import json
import sys
from datetime import datetime, date

# --- تنظیمات اولیه ---
pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    AUDIO_OK = True
except:
    AUDIO_OK = False

BASE_W, BASE_H = 1200, 850
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("NEON MINESWEEPER")
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

# رنگ اعداد
NUMBER_COLORS = {
    1: (100, 200, 255),
    2: (50, 255, 120),
    3: (255, 100, 100),
    4: (170, 60, 255),
    5: (255, 160, 30),
    6: (0, 230, 255),
    7: (255, 60, 180),
    8: (255, 230, 0),
}

# --- ابعاد ---
CELL_SIZE = 40
TOP_BAR_HEIGHT = 110

# --- ذخیره ---
SAVE_FILE = "neon_minesweeper_save.json"
settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'screen_shake': True,
    'difficulty': 'medium',
}
achievements = {
    'first_game': {'name': 'FIRST GAME', 'desc': 'Play your first game', 'unlocked': False, 'icon': '1'},
    'first_win': {'name': 'FIRST WIN', 'desc': 'Win your first game', 'unlocked': False, 'icon': 'W1'},
    'win_10': {'name': 'ROOKIE', 'desc': 'Win 10 games', 'unlocked': False, 'icon': 'W10'},
    'win_50': {'name': 'VETERAN', 'desc': 'Win 50 games', 'unlocked': False, 'icon': 'W50'},
    'win_200': {'name': 'MASTER', 'desc': 'Win 200 games', 'unlocked': False, 'icon': 'W200'},
    'easy_win': {'name': 'EASY WIN', 'desc': 'Win on Easy', 'unlocked': False, 'icon': 'E'},
    'medium_win': {'name': 'MEDIUM WIN', 'desc': 'Win on Medium', 'unlocked': False, 'icon': 'M'},
    'hard_win': {'name': 'HARD WIN', 'desc': 'Win on Hard', 'unlocked': False, 'icon': 'H'},
    'easy_sub_30': {'name': 'SPEEDY', 'desc': 'Easy in under 30s', 'unlocked': False, 'icon': 'S30'},
    'medium_sub_120': {'name': 'QUICK', 'desc': 'Medium in under 2min', 'unlocked': False, 'icon': 'Q2'},
    'hard_sub_300': {'name': 'BLITZ', 'desc': 'Hard in under 5min', 'unlocked': False, 'icon': 'B5'},
    'no_flags': {'name': 'NO FLAGS', 'desc': 'Win without using flags', 'unlocked': False, 'icon': 'NF'},
    'chord_10': {'name': 'CHORD MASTER', 'desc': 'Use chord 10 times', 'unlocked': False, 'icon': 'C10'},
    'no_mistake': {'name': 'PERFECT', 'desc': 'Win without revealing a mine', 'unlocked': False, 'icon': 'P'},
    'power_use': {'name': 'POWER USER', 'desc': 'Use 5 power-ups', 'unlocked': False, 'icon': 'PU'},
}
highscore = [0]
game_history = []
total_wins = [0]
total_games = [0]
total_mines_hit = [0]
best_times = {'easy': None, 'medium': None, 'hard': None}


def load_save():
    global settings, achievements, highscore, game_history, total_wins, total_games, total_mines_hit, best_times
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
            total_games[0] = data.get('total_games', 0)
            total_mines_hit[0] = data.get('total_mines_hit', 0)
            best_times.update(data.get('best_times', {}))
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
                'total_games': total_games[0],
                'total_mines_hit': total_mines_hit[0],
                'best_times': best_times,
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


def add_game_to_history(won, difficulty, time_sec, moves, new_achs):
    entry = {
        'won': won,
        'difficulty': difficulty,
        'time': time_sec,
        'moves': moves,
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
    sounds['reveal'] = make_sound(600, 900, 0.08, 0.15, 'sine')
    sounds['flag'] = make_sound(400, 600, 0.1, 0.18, 'square')
    sounds['unflag'] = make_sound(600, 400, 0.1, 0.15, 'square')
    sounds['mine'] = make_sound(300, 50, 0.6, 0.35, 'noise')
    sounds['win'] = make_sound(600, 2000, 1.0, 0.30, 'sine')
    sounds['chord'] = make_sound(800, 1200, 0.15, 0.20, 'sine')
    sounds['power'] = make_sound(500, 1500, 0.4, 0.25, 'sine')
    sounds['gameover'] = make_sound(500, 60, 1.5, 0.30, 'saw')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['hint'] = make_sound(1200, 1800, 0.3, 0.22, 'sine')

    bass = [82.4, 82.4, 73.4, 73.4, 65.4, 65.4, 82.4, 82.4]
    lead = [440, 523, 659, 523, 440, 392, 349, 392]
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
#                    Cell
# ============================================================
class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.is_mine = False
        self.is_revealed = False
        self.is_flagged = False
        self.adjacent_mines = 0
        self.reveal_anim = 0  # 0 تا 1
        self.flag_anim = 0
        self.explode_anim = 0
        self.defused = False  # مین خنثی شده

    def get_x(self):
        return 0  # محاسبه در GameState

    def get_y(self):
        return 0


# ============================================================
#                    GameState
# ============================================================
class GameState:
    def __init__(self, difficulty='medium'):
        self.difficulty = difficulty
        self.setup_board()
        self.first_click = True
        self.game_over = False
        self.won = False
        self.start_time = pygame.time.get_ticks()
        self.elapsed_time = 0
        self.paused = False

        # Power-upها
        self.defuse_count = 0
        self.reveal_count = 0
        self.shield_count = 0
        self.time_freeze_count = 0
        self.auto_flag_count = 0
        self.power_uses = 0

        # برای Undo
        self.move_history = []

        # آمار
        self.moves = 0
        self.cells_revealed = 0
        self.mines_hit = 0

    def setup_board(self):
        if self.difficulty == 'easy':
            self.rows = 9
            self.cols = 9
            self.num_mines = 10
        elif self.difficulty == 'medium':
            self.rows = 16
            self.cols = 16
            self.num_mines = 40
        else:  # hard
            self.rows = 16
            self.cols = 30
            self.num_mines = 99

        # محاسبه ابعاد
        self.cell_size = min(
            (WIDTH - 100) // self.cols,
            (HEIGHT - TOP_BAR_HEIGHT - 100) // self.rows,
            CELL_SIZE
        )
        self.grid_w = self.cols * self.cell_size
        self.grid_h = self.rows * self.cell_size
        self.grid_x = (WIDTH - self.grid_w) // 2
        self.grid_y = TOP_BAR_HEIGHT + (HEIGHT - TOP_BAR_HEIGHT - self.grid_h) // 2

        # ساخت Grid
        self.grid = [[Cell(r, c) for c in range(self.cols)] for r in range(self.rows)]
        self.mines_placed = False
        self.flags_placed = 0

    def place_mines(self, first_r, first_c):
        """مین‌ها رو بعد از اولین کلیک می‌ذاریم تا اولین کلیک هرگز مین نباشه"""
        positions = []
        for r in range(self.rows):
            for c in range(self.cols):
                # به جز خود خونه و 8 همسایه‌اش
                if abs(r - first_r) <= 1 and abs(c - first_c) <= 1:
                    continue
                positions.append((r, c))

        random.shuffle(positions)
        for i in range(min(self.num_mines, len(positions))):
            r, c = positions[i]
            self.grid[r][c].is_mine = True

        # محاسبه اعداد
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c].is_mine:
                    continue
                count = 0
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            if self.grid[nr][nc].is_mine:
                                count += 1
                self.grid[r][c].adjacent_mines = count

        self.mines_placed = True

    def reveal_cell(self, r, c):
        """باز کردن یه خونه"""
        if self.game_over or self.paused:
            return

        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return

        cell = self.grid[r][c]
        if cell.is_revealed or cell.is_flagged:
            return

        # اولین کلیک
        if self.first_click:
            self.place_mines(r, c)
            self.first_click = False

        self.moves += 1

        if cell.is_mine:
            # مین!
            if cell.defused:
                cell.is_revealed = True
                cell.reveal_anim = 1.0
                return
            if self.shield_count > 0:
                # شیلد فعال
                self.shield_count -= 1
                cell.defused = True
                cell.is_revealed = True
                cell.reveal_anim = 1.0
                play_sound('power')
                return
            # باخت
            cell.is_revealed = True
            cell.explode_anim = 1.0
            self.game_over = True
            self.mines_hit += 1
            total_mines_hit[0] += 1
            play_sound('mine')
            return

        # باز کردن خونه
        self._reveal_safe(cell)

        # چک برد
        self.check_win()

    def _reveal_safe(self, cell):
        """باز کردن بازگشتی خونه‌های امن"""
        cell.is_revealed = True
        cell.reveal_anim = 1.0
        self.cells_revealed += 1

        # اگه صفر بود، همسایه‌ها رو هم باز کن
        if cell.adjacent_mines == 0:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = cell.row + dr, cell.col + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        neighbor = self.grid[nr][nc]
                        if not neighbor.is_revealed and not neighbor.is_flagged and not neighbor.is_mine:
                            self._reveal_safe(neighbor)

    def toggle_flag(self, r, c):
        """پرچم گذاشتن یا برداشتن"""
        if self.game_over or self.paused:
            return

        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return

        cell = self.grid[r][c]
        if cell.is_revealed:
            return

        if cell.is_flagged:
            cell.is_flagged = False
            self.flags_placed -= 1
            play_sound('unflag')
        else:
            cell.is_flagged = True
            self.flags_placed += 1
            play_sound('flag')

    def chord(self, r, c):
        """Chord - باز کردن همسایه‌های یه خونه با عدد باز شده"""
        if self.game_over or self.paused:
            return

        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return

        cell = self.grid[r][c]
        if not cell.is_revealed or cell.adjacent_mines == 0:
            return

        # چک کن تعداد پرچم‌ها درست باشه
        flags = 0
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    n = self.grid[nr][nc]
                    neighbors.append(n)
                    if n.is_flagged:
                        flags += 1

        if flags == cell.adjacent_mines:
            # Chord
            for n in neighbors:
                if not n.is_revealed and not n.is_flagged:
                    self.reveal_cell(n.row, n.col)
            play_sound('chord')

    def check_win(self):
        """چک کن آیا بازیکن برده"""
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                if not cell.is_mine and not cell.is_revealed:
                    return False
        self.game_over = True
        self.won = True
        play_sound('win')

        # ثبت رکورد
        time_sec = self.elapsed_time
        if best_times.get(self.difficulty) is None or time_sec < best_times[self.difficulty]:
            best_times[self.difficulty] = time_sec

        total_wins[0] += 1
        return True

    def update(self, dt=1.0):
        """آپدیت زمان و انیمیشن‌ها"""
        if not self.game_over and not self.paused:
            if self.time_freeze_count > 0:
                self.time_freeze_count -= 1
            else:
                self.elapsed_time = (pygame.time.get_ticks() - self.start_time) / 1000.0

        # آپدیت انیمیشن‌ها
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                if cell.reveal_anim < 1.0 and cell.is_revealed:
                    cell.reveal_anim = min(1.0, cell.reveal_anim + 0.1 * dt)
                if cell.flag_anim < 1.0 and cell.is_flagged:
                    cell.flag_anim = min(1.0, cell.flag_anim + 0.15 * dt)
                elif cell.flag_anim > 0 and not cell.is_flagged:
                    cell.flag_anim = max(0.0, cell.flag_anim - 0.15 * dt)
                if cell.explode_anim > 0:
                    cell.explode_anim = max(0.0, cell.explode_anim - 0.02 * dt)

    def get_cell_at_pos(self, mx, my):
        """کدوم خونه زیر ماوسه"""
        if not (self.grid_x <= mx < self.grid_x + self.grid_w):
            return None
        if not (self.grid_y <= my < self.grid_y + self.grid_h):
            return None
        c = int((mx - self.grid_x) // self.cell_size)
        r = int((my - self.grid_y) // self.cell_size)
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return (r, c)
        return None

    # --- Power-ups ---
    def use_defuse(self):
        """خنثی کردن یه مین تصادفی"""
        if self.defuse_count <= 0 or self.game_over:
            return False
        # پیدا کردن یه مین که خنثی نشده
        mines = []
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                if cell.is_mine and not cell.defused:
                    mines.append(cell)
        if not mines:
            return False
        cell = random.choice(mines)
        cell.defused = True
        self.defuse_count -= 1
        self.power_uses += 1
        play_sound('power')
        # ذرات
        px = self.grid_x + cell.col * self.cell_size + self.cell_size // 2
        py = self.grid_y + cell.row * self.cell_size + self.cell_size // 2
        for _ in range(20):
            spawn_particles(px, py, NEON_GREEN, 1, 1.5)
        return True

    def use_reveal(self):
        """نشون دادن یه ناحیه امن"""
        if self.reveal_count <= 0 or self.game_over:
            return False
        # پیدا کردن یه خونه امن که باز نشده
        candidates = []
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                if not cell.is_mine and not cell.is_revealed:
                    candidates.append(cell)
        if not candidates:
            return False
        cell = random.choice(candidates)
        self._reveal_safe(cell)
        self.reveal_count -= 1
        self.power_uses += 1
        play_sound('hint')
        self.check_win()
        return True

    def use_shield(self):
        """فعال کردن شیلد"""
        if self.shield_count > 0:
            return False
        self.shield_count = 1
        self.power_uses += 1
        play_sound('power')
        return True

    def use_time_freeze(self):
        """توقف زمان"""
        if self.time_freeze_count > 0:
            return False
        self.time_freeze_count = FPS * 10  # 10 ثانیه
        self.power_uses += 1
        play_sound('power')
        return True

    def use_auto_flag(self):
        """پرچم زدن خودکار همه مین‌های اطراف اعداد باز شده"""
        if self.auto_flag_count <= 0 or self.game_over:
            return False
        # پیدا کردن همه مین‌های باقی‌مونده
        mines = []
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                if cell.is_mine and not cell.is_flagged:
                    mines.append(cell)
        if not mines:
            return False
        for cell in mines:
            cell.is_flagged = True
            self.flags_placed += 1
        self.auto_flag_count -= 1
        self.power_uses += 1
        play_sound('flag')
        return True


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
#                    Cell Drawing
# ============================================================
def draw_cell(surface, cell, gs, dt=1.0):
    x = gs.grid_x + cell.col * gs.cell_size
    y = gs.grid_y + cell.row * gs.cell_size
    size = gs.cell_size
    padding = 2

    rect = pygame.Rect(x + padding, y + padding, size - padding * 2, size - padding * 2)

    if cell.is_revealed:
        # خونه باز شده
        if cell.is_mine:
            # مین
            color = NEON_RED
            if cell.defused:
                color = NEON_GREEN
            # هاله
            for hr in range(3, 0, -1):
                glow = pygame.Surface((rect.w + hr * 10, rect.h + hr * 10), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*color, 50 - hr * 15),
                                 (0, 0, rect.w + hr * 10, rect.h + hr * 10), border_radius=6)
                surface.blit(glow, (rect.x - hr * 5, rect.y - hr * 5))
            pygame.draw.rect(surface, (color[0] // 4, color[1] // 4, color[2] // 4),
                             rect, border_radius=6)
            pygame.draw.rect(surface, color, rect, 2, border_radius=6)
            # آیکون مین
            cx, cy = rect.centerx, rect.centery
            pygame.draw.circle(surface, (0, 0, 0), (cx, cy), size // 4)
            if cell.defused:
                # ضربدر (خنثی شده)
                pygame.draw.line(surface, WHITE, (cx - size // 6, cy - size // 6),
                                 (cx + size // 6, cy + size // 6), 3)
                pygame.draw.line(surface, WHITE, (cx + size // 6, cy - size // 6),
                                 (cx - size // 6, cy + size // 6), 3)
        elif cell.adjacent_mines > 0:
            # عدد
            color = NUMBER_COLORS.get(cell.adjacent_mines, WHITE)
            # هاله
            for hr in range(2, 0, -1):
                glow = pygame.Surface((rect.w + hr * 6, rect.h + hr * 6), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*color, 30),
                                 (0, 0, rect.w + hr * 6, rect.h + hr * 6), border_radius=4)
                surface.blit(glow, (rect.x - hr * 3, rect.y - hr * 3))
            pygame.draw.rect(surface, (color[0] // 5, color[1] // 5, color[2] // 5),
                             rect, border_radius=4)
            pygame.draw.rect(surface, (color[0] // 2, color[1] // 2, color[2] // 2),
                             rect, 1, border_radius=4)
            font_size = int(size * 0.7)
            draw_text(surface, str(cell.adjacent_mines), font_size,
                      rect.centerx, rect.centery - font_size // 3,
                      color, center=True, glow=True)
        else:
            # خونه خالی
            pygame.draw.rect(surface, (15, 15, 30), rect, border_radius=4)
            pygame.draw.rect(surface, (40, 40, 60), rect, 1, border_radius=4)
    else:
        # خونه بسته
        # هاله
        for hr in range(3, 0, -1):
            glow = pygame.Surface((rect.w + hr * 8, rect.h + hr * 8), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*NEON_PURPLE, 40 - hr * 12),
                             (0, 0, rect.w + hr * 8, rect.h + hr * 8), border_radius=6)
            surface.blit(glow, (rect.x - hr * 4, rect.y - hr * 4))

        # بدنه
        pygame.draw.rect(surface, (30, 20, 60), rect, border_radius=6)
        pygame.draw.rect(surface, NEON_PURPLE, rect, 2, border_radius=6)
        pygame.draw.line(surface, WHITE, (rect.x + 3, rect.y + 3),
                         (rect.right - 3, rect.y + 3), 1)

        # پرچم
        if cell.is_flagged:
            anim_scale = 1.0 + cell.flag_anim * 0.2
            flag_size = int(size * 0.5 * anim_scale)
            cx, cy = rect.centerx, rect.centery
            # چوب پرچم
            pygame.draw.line(surface, WHITE, (cx, cy + flag_size // 2),
                             (cx, cy - flag_size // 2), 2)
            # پارچه پرچم
            pts = [
                (cx, cy - flag_size // 2),
                (cx + flag_size // 2, cy - flag_size // 4),
                (cx, cy),
            ]
            pygame.draw.polygon(surface, NEON_RED, pts)
            pygame.draw.polygon(surface, WHITE, pts, 1)


# ============================================================
#                    Menu
# ============================================================
def show_menu():
    menu_time = 0
    btn_easy = Button(WIDTH // 2 - 240, HEIGHT // 2 - 40, 200, 60, "EASY", NEON_GREEN, NEON_CYAN, 26)
    btn_medium = Button(WIDTH // 2, HEIGHT // 2 - 40, 200, 60, "MEDIUM", NEON_YELLOW, NEON_ORANGE, 26)
    btn_hard = Button(WIDTH // 2 + 240, HEIGHT // 2 - 40, 200, 60, "HARD", NEON_RED, NEON_PINK, 26)
    btn_history = Button(WIDTH // 2, HEIGHT // 2 + 55, 320, 45, "HISTORY", NEON_BLUE, NEON_CYAN, 22)
    btn_settings = Button(WIDTH // 2, HEIGHT // 2 + 110, 320, 45, "SETTINGS", NEON_PURPLE, NEON_PINK, 22)
    btn_achievements = Button(WIDTH // 2, HEIGHT // 2 + 165, 320, 45, "ACHIEVEMENTS", NEON_YELLOW, NEON_ORANGE, 22)
    btn_quit = Button(WIDTH // 2, HEIGHT // 2 + 220, 320, 42, "QUIT", NEON_RED, NEON_ORANGE, 20)
    btn_fullscreen = Button(WIDTH - 40, 30, 40, 40, "[]", NEON_PURPLE, NEON_CYAN, 20)

    while True:
        game_surface.fill(DARK_BG)
        t = pygame.time.get_ticks() / 1000
        menu_time += 1
        mouse_pos = get_game_mouse_pos()

        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            game_surface.blit(s, (0, y))
        for _ in range(100):
            pygame.draw.circle(game_surface, (80, 100, 150),
                               (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 1)

        # عنوان
        title_y = 130 + math.sin(t * 2) * 8
        draw_text(game_surface, "NEON", 72, WIDTH // 2 - 150, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "MINESWEEPER", 72, WIDTH // 2 + 120, title_y, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, "REVEAL  /  FLAG  /  WIN", 20, WIDTH // 2, title_y + 65,
                  (200, 200, 220), center=True)

        # آمار
        if highscore[0] > 0:
            draw_text(game_surface, f"HIGH SCORE: {highscore[0]}", 20, WIDTH // 2, title_y + 110,
                      NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, f"GAMES: {total_games[0]}   WINS: {total_wins[0]}",
                  14, WIDTH // 2, title_y + 140, NEON_PINK, center=True)

        # Best times
        best_y = title_y + 180
        draw_text(game_surface, "BEST TIMES:", 16, WIDTH // 2, best_y, NEON_CYAN, center=True)
        for i, diff in enumerate(['easy', 'medium', 'hard']):
            b = best_times.get(diff)
            if b is not None:
                txt = f"{diff.upper()}: {b:.1f}s"
                color = NEON_GREEN
            else:
                txt = f"{diff.upper()}: --"
                color = (100, 100, 120)
            draw_text(game_surface, txt, 14, WIDTH // 2 + (i - 1) * 200, best_y + 25,
                      color, center=True)

        for b in [btn_easy, btn_medium, btn_hard, btn_history, btn_settings, btn_achievements, btn_quit, btn_fullscreen]:
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
            if btn_easy.is_clicked(event):
                return 'easy'
            if btn_medium.is_clicked(event):
                return 'medium'
            if btn_hard.is_clicked(event):
                return 'hard'
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
                    return 'easy'
                if event.key == pygame.K_2:
                    return 'medium'
                if event.key == pygame.K_3:
                    return 'hard'
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
    btn_shake = Button(WIDTH // 2, 400, 280, 55,
                       f"SHAKE: {'ON' if settings['screen_shake'] else 'OFF'}",
                       NEON_GREEN if settings['screen_shake'] else (100, 100, 100), NEON_CYAN, 22)
    btn_reset = Button(WIDTH // 2 - 130, 500, 220, 50, "RESET SAVE", NEON_RED, NEON_ORANGE, 20)
    btn_back = Button(WIDTH // 2 + 130, 500, 220, 50, "BACK", NEON_CYAN, NEON_GREEN, 22)

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
        box_h = 580
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
                settings['screen_shake'] = True
                for k in achievements:
                    achievements[k]['unlocked'] = False
                highscore[0] = 0
                game_history.clear()
                total_wins[0] = 0
                total_games[0] = 0
                total_mines_hit[0] = 0
                best_times['easy'] = None
                best_times['medium'] = None
                best_times['hard'] = None
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
                won = entry.get('won', False)
                rank_color = NEON_GREEN if won else NEON_RED
                rank = "WIN" if won else "LOSS"
                pygame.draw.rect(game_surface, (15, 8, 30), (ix, iy, iw, item_h - 8), border_radius=6)
                pygame.draw.rect(game_surface, rank_color, (ix, iy, iw, item_h - 8), 2, border_radius=6)
                draw_text(game_surface, rank, 20, ix + 35, iy + (item_h - 8) // 2, rank_color, center=True, glow=True)
                draw_text(game_surface, f"{entry.get('difficulty', '?').upper()}", 16, ix + 120, iy + 10, WHITE)
                draw_text(game_surface, f"Time: {entry.get('time', 0):.1f}s   Moves: {entry.get('moves', 0)}",
                          12, ix + 120, iy + 30, (180, 180, 200))
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
def play_game(difficulty='medium'):
    gs = GameState(difficulty)
    total_games[0] += 1

    # Power-upها
    gs.defuse_count = 1
    gs.reveal_count = 1
    gs.shield_count = 0
    gs.time_freeze_count = 0
    gs.auto_flag_count = 1

    # وضعیت
    paused = False
    game_saved = False
    new_achs = []
    notifications = []
    go_anim = 0
    screen_shake = 0
    flash = 0

    # دکمه‌های Power-up
    btn_defuse = Button(120, HEIGHT - 50, 200, 45, f"DEFUSE ({gs.defuse_count})", NEON_GREEN, NEON_CYAN, 16)
    btn_reveal = Button(340, HEIGHT - 50, 200, 45, f"REVEAL ({gs.reveal_count})", NEON_CYAN, NEON_BLUE, 16)
    btn_shield = Button(560, HEIGHT - 50, 200, 45, f"SHIELD ({gs.shield_count})", NEON_BLUE, NEON_PURPLE, 16)
    btn_freeze = Button(780, HEIGHT - 50, 200, 45, f"FREEZE ({gs.time_freeze_count // FPS})", NEON_PURPLE, NEON_PINK, 16)
    btn_autoflag = Button(1000, HEIGHT - 50, 200, 45, f"AUTO FLAG ({gs.auto_flag_count})", NEON_PINK, NEON_RED, 16)

    # دکمه‌های پاز
    btn_resume = Button(WIDTH // 2, HEIGHT // 2 + 20, 300, 60, "RESUME", NEON_GREEN, NEON_CYAN, 28)
    btn_pause_menu = Button(WIDTH // 2, HEIGHT // 2 + 100, 300, 55, "MAIN MENU", NEON_RED, NEON_ORANGE, 24)
    btn_restart = Button(WIDTH // 2, HEIGHT // 2 + 70, 300, 60, "NEW GAME", NEON_CYAN, NEON_GREEN, 28)
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
        add_game_to_history(gs.won, difficulty, gs.elapsed_time, gs.moves, new_achs)

    # دیفیولت اولین بار
    try_unlock('first_game')

    running = True
    while running:
        dt = clock.tick(FPS) / (1000 / FPS)  # برای انیمیشن
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

            if paused and not gs.game_over:
                if btn_resume.is_clicked(event):
                    paused = False
                if btn_pause_menu.is_clicked(event):
                    stop_music()
                    if not game_saved:
                        save_current()
                        game_saved = True
                    return

            if gs.game_over:
                if btn_restart.is_clicked(event):
                    stop_music()
                    play_game(difficulty)
                    return
                if btn_menu.is_clicked(event):
                    stop_music()
                    if not game_saved:
                        save_current()
                        game_saved = True
                    return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p and not gs.game_over:
                    paused = not paused
                if event.key == pygame.K_r and gs.game_over:
                    stop_music()
                    play_game(difficulty)
                    return
                if event.key == pygame.K_ESCAPE:
                    stop_music()
                    if not game_saved:
                        save_current()
                        game_saved = True
                    return
                # کلیدهای Power-up
                if event.key == pygame.K_1:
                    if gs.use_defuse():
                        try_unlock('power_use')
                if event.key == pygame.K_2:
                    if gs.use_reveal():
                        try_unlock('power_use')
                if event.key == pygame.K_3:
                    if gs.use_shield():
                        try_unlock('power_use')
                if event.key == pygame.K_4:
                    if gs.use_time_freeze():
                        try_unlock('power_use')
                if event.key == pygame.K_5:
                    if gs.use_auto_flag():
                        try_unlock('power_use')

            if not paused and not gs.game_over:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    cell_pos = gs.get_cell_at_pos(mouse_pos[0], mouse_pos[1])
                    if cell_pos:
                        r, c = cell_pos
                        if event.button == 1:  # کلیک چپ
                            # چک دوبار کلیک (Chord)
                            if event.type == pygame.MOUSEBUTTONDOWN and hasattr(gs, '_last_click'):
                                pass
                            gs.reveal_cell(r, c)
                        elif event.button == 3:  # کلیک راست
                            gs.toggle_flag(r, c)
                        elif event.button == 2:  # کلیک وسط (Chord)
                            gs.chord(r, c)

        for notif in notifications[:]:
            notif['timer'] -= 1
            if notif['timer'] <= 0:
                notifications.remove(notif)

        if paused and not gs.game_over:
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

        if not gs.game_over:
            gs.update(dt)

            # چک برد
            if gs.won and not game_saved:
                save_current()
                game_saved = True
                try_unlock('first_win')
                if total_wins[0] >= 10: try_unlock('win_10')
                if total_wins[0] >= 50: try_unlock('win_50')
                if total_wins[0] >= 200: try_unlock('win_200')
                if difficulty == 'easy':
                    try_unlock('easy_win')
                    if gs.elapsed_time < 30: try_unlock('easy_sub_30')
                elif difficulty == 'medium':
                    try_unlock('medium_win')
                    if gs.elapsed_time < 120: try_unlock('medium_sub_120')
                else:
                    try_unlock('hard_win')
                    if gs.elapsed_time < 300: try_unlock('hard_sub_300')
                if gs.flags_placed == 0: try_unlock('no_flags')
                if gs.mines_hit == 0: try_unlock('no_mistake')
                highscore[0] = max(highscore[0], int(100000 / max(1, gs.elapsed_time)))

            if gs.game_over and not gs.won and not game_saved:
                save_current()
                game_saved = True
                if settings['screen_shake']:
                    screen_shake = 25
                flash = 200

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

        # پس‌زمینه
        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            play_layer.blit(s, (0, y))

        # خونه‌ها
        for r in range(gs.rows):
            for c in range(gs.cols):
                draw_cell(play_layer, gs.grid[r][c], gs, dt)

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
        # نوار بالا
        hud_panel = pygame.Surface((WIDTH, TOP_BAR_HEIGHT), pygame.SRCALPHA)
        for y in range(TOP_BAR_HEIGHT):
            alpha = int(200 * (1 - y / TOP_BAR_HEIGHT))
            pygame.draw.line(hud_panel, (5, 10, 25, alpha), (0, y), (WIDTH, y))
        game_surface.blit(hud_panel, (0, 0))
        pygame.draw.line(game_surface, NEON_CYAN, (0, TOP_BAR_HEIGHT), (WIDTH, TOP_BAR_HEIGHT), 1)

        # عنوان
        draw_text(game_surface, "NEON MINESWEEPER", 22, 25, 10, NEON_CYAN, glow=True)
        draw_text(game_surface, f"MODE: {difficulty.upper()}", 16, 25, 40, NEON_YELLOW)

        # اطلاعات
        draw_text(game_surface, f"MINES: {gs.num_mines - gs.flags_placed}", 24, WIDTH // 2 - 200, 20,
                  NEON_RED, center=True, glow=True)
        draw_text(game_surface, f"TIME: {int(gs.elapsed_time)}s", 24, WIDTH // 2, 20,
                  NEON_YELLOW, center=True, glow=True)
        draw_text(game_surface, f"MOVES: {gs.moves}", 24, WIDTH // 2 + 200, 20,
                  NEON_GREEN, center=True, glow=True)

        # Best Time
        b = best_times.get(difficulty)
        if b is not None:
            draw_text(game_surface, f"BEST: {b:.1f}s", 16, WIDTH - 25, 15, NEON_GREEN, center=False)

        # راهنما
        draw_text(game_surface, "LEFT CLICK: reveal  |  RIGHT CLICK: flag  |  MIDDLE CLICK: chord  |  1-5: power-ups",
                  12, WIDTH // 2, TOP_BAR_HEIGHT - 25, (150, 180, 220), center=True)

        # دکمه‌های Power-up
        btn_defuse.text = f"DEFUSE [{gs.defuse_count}]"
        btn_defuse.color = NEON_GREEN if gs.defuse_count > 0 else (80, 80, 80)
        btn_defuse.update(mouse_pos)
        btn_defuse.draw(game_surface)

        btn_reveal.text = f"REVEAL [{gs.reveal_count}]"
        btn_reveal.color = NEON_CYAN if gs.reveal_count > 0 else (80, 80, 80)
        btn_reveal.update(mouse_pos)
        btn_reveal.draw(game_surface)

        btn_shield.text = f"SHIELD [{gs.shield_count}]"
        btn_shield.color = NEON_BLUE if gs.shield_count > 0 else (80, 80, 80)
        btn_shield.update(mouse_pos)
        btn_shield.draw(game_surface)

        btn_freeze.text = f"FREEZE [{gs.time_freeze_count // FPS}]"
        btn_freeze.color = NEON_PURPLE if gs.time_freeze_count > 0 else (80, 80, 80)
        btn_freeze.update(mouse_pos)
        btn_freeze.draw(game_surface)

        btn_autoflag.text = f"AUTO FLAG [{gs.auto_flag_count}]"
        btn_autoflag.color = NEON_PINK if gs.auto_flag_count > 0 else (80, 80, 80)
        btn_autoflag.update(mouse_pos)
        btn_autoflag.draw(game_surface)

        # کلیک روی Power-upها
        if btn_defuse.is_clicked(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=mouse_pos, button=1)):
            if gs.use_defuse():
                try_unlock('power_use')
        if btn_reveal.is_clicked(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=mouse_pos, button=1)):
            if gs.use_reveal():
                try_unlock('power_use')
        if btn_shield.is_clicked(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=mouse_pos, button=1)):
            if gs.use_shield():
                try_unlock('power_use')
        if btn_freeze.is_clicked(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=mouse_pos, button=1)):
            if gs.use_time_freeze():
                try_unlock('power_use')
        if btn_autoflag.is_clicked(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=mouse_pos, button=1)):
            if gs.use_auto_flag():
                try_unlock('power_use')

        # Notifications
        for i, notif in enumerate(notifications):
            ny = TOP_BAR_HEIGHT + 20 + i * 55
            alpha = min(255, notif['timer'] * 2)
            ach = notif['ach']
            notif_surf = pygame.Surface((340, 50), pygame.SRCALPHA)
            notif_surf.fill((10, 5, 25, min(220, alpha)))
            game_surface.blit(notif_surf, (WIDTH - 360, ny))
            pygame.draw.rect(game_surface, NEON_YELLOW, (WIDTH - 360, ny, 340, 50), 2)
            draw_text(game_surface, "ACHIEVEMENT!", 11, WIDTH - 345, ny + 4, NEON_YELLOW)
            draw_text(game_surface, ach['name'], 16, WIDTH - 345, ny + 22, WHITE, glow=True)

        # Game Over / Win
        if gs.game_over:
            go_anim += 1
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            game_surface.blit(overlay, (0, 0))
            box_w = 540
            box_h = 400
            box_x = WIDTH // 2 - box_w // 2
            box_y = HEIGHT // 2 - box_h // 2
            pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h))
            if gs.won:
                title_color = NEON_GREEN
                title_text = "YOU WIN!"
            else:
                title_color = NEON_RED
                title_text = "GAME OVER"
            pygame.draw.rect(game_surface, title_color, (box_x, box_y, box_w, box_h), 3)
            pygame.draw.rect(game_surface, NEON_CYAN, (box_x + 5, box_y + 5, box_w - 10, box_h - 10), 1)
            draw_text(game_surface, title_text, 60, WIDTH // 2, box_y + 55,
                      title_color, center=True, glow=True)
            draw_text(game_surface, f"TIME: {gs.elapsed_time:.1f}s", 28,
                      WIDTH // 2, box_y + 120, WHITE, center=True)
            draw_text(game_surface, f"MOVES: {gs.moves}   MINES HIT: {gs.mines_hit}",
                      16, WIDTH // 2, box_y + 160, NEON_CYAN, center=True)
            if gs.won and best_times[difficulty] is not None:
                draw_text(game_surface, f"BEST: {best_times[difficulty]:.1f}s",
                          18, WIDTH // 2, box_y + 200, NEON_YELLOW, center=True, glow=True)
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
        elif result in ['easy', 'medium', 'hard']:
            play_game(result)
    pygame.quit()


if __name__ == "__main__":
    main()