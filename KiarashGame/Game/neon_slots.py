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

BASE_W, BASE_H = 1200, 850
WIDTH, HEIGHT = BASE_W, BASE_H

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("NEON SLOTS")
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
GOLD = (255, 215, 0)

# --- نمادها ---
# (نام، رنگ، ضریب 3x، 4x، 5x)
SYMBOLS = [
    ('CHERRY', NEON_RED, 5, 20, 100),
    ('LEMON', NEON_YELLOW, 5, 20, 100),
    ('BELL', NEON_ORANGE, 10, 40, 200),
    ('BAR', NEON_CYAN, 15, 60, 300),
    ('SEVEN', NEON_MAGENTA, 25, 100, 500),
    ('DIAMOND', NEON_BLUE, 50, 200, 1000),
    ('CROWN', NEON_PURPLE, 100, 400, 2000),
    ('WILD', GOLD, 200, 800, 5000),
]

# --- ابعاد اسلات ---
REELS = 5
ROWS = 3
SYMBOL_SIZE = 120
SYMBOL_GAP = 15
SLOT_W = REELS * SYMBOL_SIZE + (REELS - 1) * SYMBOL_GAP
SLOT_H = ROWS * SYMBOL_SIZE + (ROWS - 1) * SYMBOL_GAP
SLOT_X = (WIDTH - SLOT_W) // 2
SLOT_Y = 220

# --- ذخیره ---
SAVE_FILE = "neon_slots_save.json"
settings = {
    'sfx_volume': 0.7,
    'music_volume': 0.5,
    'screen_shake': True,
    'turbo_mode': False,
}
achievements = {
    'first_spin': {'name': 'FIRST SPIN', 'desc': 'Do your first spin', 'unlocked': False, 'icon': 'S'},
    'first_win': {'name': 'FIRST WIN', 'desc': 'Win your first bet', 'unlocked': False, 'icon': 'W'},
    'win_10': {'name': 'ROOKIE', 'desc': 'Win 10 times', 'unlocked': False, 'icon': 'W10'},
    'win_100': {'name': 'VETERAN', 'desc': 'Win 100 times', 'unlocked': False, 'icon': 'W100'},
    'big_win': {'name': 'BIG WIN', 'desc': 'Win 500+ in one spin', 'unlocked': False, 'icon': 'BW'},
    'mega_win': {'name': 'MEGA WIN', 'desc': 'Win 2000+ in one spin', 'unlocked': False, 'icon': 'MW'},
    'jackpot': {'name': 'JACKPOT!', 'desc': 'Hit the jackpot (5 Wilds)', 'unlocked': False, 'icon': 'JP'},
    'free_spins': {'name': 'FREE SPINS', 'desc': 'Trigger free spins', 'unlocked': False, 'icon': 'FS'},
    'money_5000': {'name': 'RICH', 'desc': 'Reach 5000 coins', 'unlocked': False, 'icon': '$5K'},
    'money_20000': {'name': 'MILLIONAIRE', 'desc': 'Reach 20000 coins', 'unlocked': False, 'icon': '$20K'},
    'combo_3': {'name': 'TRIPLE WIN', 'desc': 'Win on 3+ lines at once', 'unlocked': False, 'icon': 'C3'},
    'gamble_win': {'name': 'GAMBLER', 'desc': 'Win the gamble feature', 'unlocked': False, 'icon': 'G'},
    'max_bet_win': {'name': 'HIGH ROLLER', 'desc': 'Win with max bet', 'unlocked': False, 'icon': 'HR'},
    'wild_5': {'name': 'WILD FEVER', 'desc': 'Get 5 Wilds on screen', 'unlocked': False, 'icon': 'WF'},
    'level_10': {'name': 'LEVEL 10', 'desc': 'Reach level 10', 'unlocked': False, 'icon': 'L10'},
}
highscore = [0]
game_history = []
money = [1000]  # شروع با 1000 سکه
total_spins = [0]
total_wins = [0]
biggest_win = [0]
level = [1]
xp = [0]


def load_save():
    global settings, achievements, highscore, game_history, money, total_spins, total_wins, biggest_win, level, xp
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
            settings.update(data.get('settings', {}))
            for k, v in data.get('achievements', {}).items():
                if k in achievements:
                    achievements[k]['unlocked'] = v
            highscore[0] = data.get('highscore', 0)
            game_history = data.get('game_history', [])
            money[0] = data.get('money', 1000)
            total_spins[0] = data.get('total_spins', 0)
            total_wins[0] = data.get('total_wins', 0)
            biggest_win[0] = data.get('biggest_win', 0)
            level[0] = data.get('level', 1)
            xp[0] = data.get('xp', 0)
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
                'money': money[0],
                'total_spins': total_spins[0],
                'total_wins': total_wins[0],
                'biggest_win': biggest_win[0],
                'level': level[0],
                'xp': xp[0],
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


def add_game_to_history(win_amount, bet, lines, symbols_result, new_achs):
    entry = {
        'win': win_amount,
        'bet': bet,
        'lines': lines,
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
    sounds['spin'] = make_sound(300, 500, 0.2, 0.15, 'saw')
    sounds['reel_stop'] = make_sound(500, 700, 0.1, 0.18, 'square')
    sounds['win_small'] = make_sound(600, 1200, 0.3, 0.22, 'sine')
    sounds['win_medium'] = make_sound(700, 1500, 0.5, 0.28, 'sine')
    sounds['win_big'] = make_sound(600, 2000, 1.0, 0.32, 'sine')
    sounds['jackpot'] = make_sound(400, 2500, 2.0, 0.35, 'sine')
    sounds['click'] = make_sound(800, 1200, 0.05, 0.15, 'square')
    sounds['coin'] = make_sound(1000, 1800, 0.15, 0.20, 'sine')
    sounds['gameover'] = make_sound(400, 60, 1.5, 0.30, 'saw')
    sounds['free_spins'] = make_sound(500, 1800, 1.0, 0.30, 'sine')

    bass = [65.4, 65.4, 82.4, 82.4, 73.4, 73.4, 65.4, 65.4]
    lead = [440, 523, 659, 784, 659, 523, 440, 392]
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


# --- Coin Effect ---
class CoinEffect:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vy = -8
        self.vx = random.uniform(-2, 2)
        self.life = 60
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-10, 10)
        self.active = True

    def update(self):
        self.vy += 0.4
        self.x += self.vx
        self.y += self.vy
        self.rotation += self.rot_speed
        self.life -= 1
        if self.life <= 0 or self.y > HEIGHT + 50:
            self.active = False

    def draw(self, surface):
        if not self.active:
            return
        alpha = min(255, self.life * 4)
        for hr in range(2, 0, -1):
            glow = pygame.Surface((30 + hr * 6, 30 + hr * 6), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*GOLD, 60 - hr * 20),
                               ((30 + hr * 6) // 2, (30 + hr * 6) // 2), 15 + hr * 3)
            surface.blit(glow, (self.x - (30 + hr * 6) // 2, self.y - (30 + hr * 6) // 2))
        pygame.draw.circle(surface, GOLD, (int(self.x), int(self.y)), 12)
        pygame.draw.circle(surface, (180, 140, 0), (int(self.x), int(self.y)), 12, 2)
        draw_text(surface, "$", 16, self.x, self.y - 10, WHITE, center=True, bold=True)


coin_effects = []


# ============================================================
#                    Slot Machine
# ============================================================
class SlotMachine:
    def __init__(self):
        self.reels = []  # 5 reel × 3 rows
        self.reel_offsets = [0, 0, 0, 0, 0]  # offset for animation
        self.reel_speeds = [0, 0, 0, 0, 0]
        self.reel_stopping = [False, False, False, False, False]
        self.reel_stopped = [False, False, False, False, False]
        self.spinning = False
        self.results = None

        # مقداردهی اولیه
        self.randomize()

    def randomize(self):
        """پر کردن همه‌ی خانه‌ها با نماد تصادفی"""
        self.reels = []
        for col in range(REELS):
            reel = []
            for row in range(ROWS):
                reel.append(random.randint(0, len(SYMBOLS) - 1))
            self.reels.append(reel)

    def spin(self):
        """شروع چرخش"""
        self.spinning = True
        self.reel_speeds = [25, 25, 25, 25, 25]
        self.reel_stopping = [False, False, False, False, False]
        self.reel_stopped = [False, False, False, False, False]
        self.results = None

    def stop_reel(self, col):
        """متوقف کردن یه reel"""
        if col >= len(self.reel_stopping):
            return
        self.reel_stopping[col] = True
        self.reel_speeds[col] = 0
        # چرخش نهایی رو تعیین کن
        for row in range(ROWS):
            self.reels[col][row] = random.randint(0, len(SYMBOLS) - 1)
        self.reel_offsets[col] = 0
        self.reel_stopped[col] = True
        play_sound('reel_stop')

        # اگه همه متوقف شدن
        if all(self.reel_stopped):
            self.spinning = False
            self.results = [self.reels[c][r] for c in range(REELS) for r in range(ROWS)]

    def update(self, turbo=False):
        """آپدیت انیمیشن"""
        speed_mult = 2.0 if turbo else 1.0
        for col in range(REELS):
            if self.reel_speeds[col] > 0:
                self.reel_offsets[col] += self.reel_speeds[col] * speed_mult
                # چرخش مداوم
                if self.reel_offsets[col] > SYMBOL_SIZE + SYMBOL_GAP:
                    self.reel_offsets[col] -= (SYMBOL_SIZE + SYMBOL_GAP)
                    # جابجایی نمادها
                    self.reels[col].insert(0, self.reels[col].pop())
            elif self.reel_stopping[col]:
                # در حال توقف - انیمیشن برگشت
                if abs(self.reel_offsets[col]) > 0.1:
                    self.reel_offsets[col] *= 0.7
                else:
                    self.reel_offsets[col] = 0

    def get_all_stopped(self):
        return all(self.reel_stopped)


# ============================================================
#                    Game Logic
# ============================================================
def calculate_win(machine, bet, lines_active):
    """محاسبه برد بر اساس خطوط شرط‌بندی"""
    # خطوط استاندارد
    PAYLINES = [
        [1, 1, 1, 1, 1],  # وسط
        [0, 0, 0, 0, 0],  # بالا
        [2, 2, 2, 2, 2],  # پایین
        [0, 1, 2, 1, 0],  # V شکل
        [2, 1, 0, 1, 2],  # Λ شکل
        [0, 0, 1, 2, 2],  # شیب
        [2, 2, 1, 0, 0],  # شیب مخالف
        [1, 0, 0, 0, 1],
        [1, 2, 2, 2, 1],
        [0, 1, 1, 1, 0],
        [2, 1, 1, 1, 2],
        [1, 0, 1, 2, 1],
        [1, 2, 1, 0, 1],
        [0, 1, 0, 1, 0],
        [2, 1, 2, 1, 2],
        [1, 0, 2, 0, 1],
        [1, 2, 0, 2, 1],
        [0, 0, 2, 0, 0],
        [2, 2, 0, 2, 2],
        [0, 2, 0, 2, 0],
    ]

    total_win = 0
    winning_lines = []
    wild_count = 0

    # شمارش Wild‌ها
    for c in range(REELS):
        for r in range(ROWS):
            if machine.reels[c][r] == 7:  # WILD
                wild_count += 1

    # چک هر خط
    for line_idx, line in enumerate(PAYLINES[:lines_active]):
        # نمادهای این خط
        line_symbols = []
        for col in range(REELS):
            row = line[col]
            line_symbols.append(machine.reels[col][row])

        # چک از چپ به راست
        first_symbol = line_symbols[0]
        # اگه Wild بود، نماد واقعی رو پیدا کن
        if first_symbol == 7:
            for s in line_symbols:
                if s != 7:
                    first_symbol = s
                    break

        # شمارش نمادهای یکسان
        count = 0
        for s in line_symbols:
            if s == first_symbol or s == 7:  # Wild جای همه میشینه
                count += 1
            else:
                break

        # محاسبه برد
        if count >= 3 and first_symbol != 7:  # حداقل 3 نماد
            sym_data = SYMBOLS[first_symbol]
            if count == 5:
                multiplier = sym_data[5]
            elif count == 4:
                multiplier = sym_data[4]
            else:
                multiplier = sym_data[3]

            # محاسبه برد
            line_win = bet * multiplier
            total_win += line_win
            winning_lines.append((line_idx, count, first_symbol))

    # چک 5 Wild (Jackpot)
    jackpot = False
    if wild_count >= 5:
        # اگه یه خط 5 Wild داشته باشه
        for line in PAYLINES[:lines_active]:
            all_wild = True
            for col in range(REELS):
                row = line[col]
                if machine.reels[col][row] != 7:
                    all_wild = False
                    break
            if all_wild:
                jackpot = True
                total_win += 5000 * bet
                break

    return total_win, winning_lines, wild_count, jackpot


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
#                    Draw Symbol
# ============================================================
def draw_symbol(surface, symbol_idx, x, y, size, alpha=255):
    """رسم یه نماد در موقعیت مشخص"""
    name, color, m3, m4, m5 = SYMBOLS[symbol_idx]

    # هاله
    if alpha >= 255:
        for hr in range(3, 0, -1):
            glow = pygame.Surface((size + hr * 10, size + hr * 10), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*color, 60 - hr * 15),
                             (0, 0, size + hr * 10, size + hr * 10), border_radius=12)
            surface.blit(glow, (x - hr * 5, y - hr * 5))

    # بدنه
    rect = pygame.Rect(int(x), int(y), int(size), int(size))
    pygame.draw.rect(surface, (color[0] // 4, color[1] // 4, color[2] // 4),
                     rect, border_radius=12)
    pygame.draw.rect(surface, color, rect, 3, border_radius=12)
    pygame.draw.rect(surface, WHITE, rect, 1, border_radius=12)

    # محتوا
    font_size = int(size * 0.5)
    if name == 'WILD':
        draw_text(surface, "WILD", font_size, rect.centerx, rect.centery - font_size // 3,
                  color, center=True, bold=True, glow=True)
    elif name == 'CHERRY':
        # گیلاس ساده
        pygame.draw.circle(surface, NEON_RED, (rect.centerx - 10, rect.centery + 10), 15)
        pygame.draw.circle(surface, NEON_RED, (rect.centerx + 10, rect.centery + 10), 15)
        pygame.draw.line(surface, NEON_GREEN, (rect.centerx - 10, rect.centery - 5),
                         (rect.centerx, rect.top + 15), 3)
        pygame.draw.line(surface, NEON_GREEN, (rect.centerx + 10, rect.centery - 5),
                         (rect.centerx, rect.top + 15), 3)
    elif name == 'LEMON':
        # لیمو
        pygame.draw.ellipse(surface, NEON_YELLOW,
                            (rect.centerx - 25, rect.centery - 18, 50, 36))
        pygame.draw.ellipse(surface, WHITE,
                            (rect.centerx - 25, rect.centery - 18, 50, 36), 2)
    elif name == 'BELL':
        # زنگ
        pts = [
            (rect.centerx - 20, rect.centery + 15),
            (rect.centerx + 20, rect.centery + 15),
            (rect.centerx + 15, rect.centery - 10),
            (rect.centerx, rect.centery - 20),
            (rect.centerx - 15, rect.centery - 10),
        ]
        pygame.draw.polygon(surface, NEON_ORANGE, pts)
        pygame.draw.polygon(surface, WHITE, pts, 2)
    elif name == 'BAR':
        draw_text(surface, "BAR", font_size, rect.centerx, rect.centery - font_size // 3,
                  NEON_CYAN, center=True, bold=True, glow=True)
    elif name == 'SEVEN':
        draw_text(surface, "7", int(size * 0.7), rect.centerx, rect.centery - size // 4,
                  NEON_MAGENTA, center=True, bold=True, glow=True)
    elif name == 'DIAMOND':
        # الماس
        pts = [
            (rect.centerx, rect.top + 20),
            (rect.right - 20, rect.centery),
            (rect.centerx, rect.bottom - 20),
            (rect.left + 20, rect.centery),
        ]
        pygame.draw.polygon(surface, NEON_BLUE, pts)
        pygame.draw.polygon(surface, WHITE, pts, 2)
    elif name == 'CROWN':
        # تاج
        pts = [
            (rect.centerx - 25, rect.centery + 15),
            (rect.centerx + 25, rect.centery + 15),
            (rect.centerx + 20, rect.centery - 10),
            (rect.centerx + 10, rect.centery - 5),
            (rect.centerx, rect.centery - 20),
            (rect.centerx - 10, rect.centery - 5),
            (rect.centerx - 20, rect.centery - 10),
        ]
        pygame.draw.polygon(surface, NEON_PURPLE, pts)
        pygame.draw.polygon(surface, WHITE, pts, 2)
        # جواهرات
        pygame.draw.circle(surface, NEON_RED, (rect.centerx, rect.centery - 20), 4)
        pygame.draw.circle(surface, NEON_CYAN, (rect.centerx - 20, rect.centery - 10), 3)
        pygame.draw.circle(surface, NEON_GREEN, (rect.centerx + 20, rect.centery - 10), 3)
    else:
        draw_text(surface, name[:3], font_size, rect.centerx, rect.centery - font_size // 3,
                  color, center=True, bold=True)


# ============================================================
#                    Menu
# ============================================================
def show_menu():
    menu_time = 0
    btn_start = Button(WIDTH // 2, HEIGHT // 2 + 30, 320, 55, "START SPINNING", GOLD, NEON_YELLOW, 28)
    btn_history = Button(WIDTH // 2, HEIGHT // 2 + 95, 320, 45, "HISTORY", NEON_BLUE, NEON_CYAN, 22)
    btn_settings = Button(WIDTH // 2, HEIGHT // 2 + 150, 320, 45, "SETTINGS", NEON_PURPLE, NEON_PINK, 22)
    btn_achievements = Button(WIDTH // 2, HEIGHT // 2 + 205, 320, 45, "ACHIEVEMENTS", NEON_YELLOW, NEON_ORANGE, 22)
    btn_quit = Button(WIDTH // 2, HEIGHT // 2 + 260, 320, 42, "QUIT", NEON_RED, NEON_ORANGE, 20)
    btn_fullscreen = Button(WIDTH - 40, 30, 40, 40, "[]", NEON_PURPLE, NEON_CYAN, 20)

    # نمادهای تزئینی
    demo_symbols = []
    for i in range(12):
        demo_symbols.append({
            'x': random.randint(50, WIDTH - 150),
            'y': random.randint(0, HEIGHT),
            'idx': random.randint(0, len(SYMBOLS) - 1),
            'vy': random.uniform(0.5, 2),
            'size': random.randint(50, 80),
        })

    while True:
        game_surface.fill(DARK_BG)
        t = pygame.time.get_ticks() / 1000
        menu_time += 1
        mouse_pos = get_game_mouse_pos()

        # پس‌زمینه کازینو
        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            game_surface.blit(s, (0, y))
        # نورهای کازینو
        for i in range(8):
            lx = (i * 200 + t * 50) % (WIDTH + 400) - 200
            ly = 100 + math.sin(t + i) * 30
            for hr in range(3, 0, -1):
                glow = pygame.Surface((100 + hr * 15, 100 + hr * 15), pygame.SRCALPHA)
                color = random.choice([GOLD, NEON_PINK, NEON_CYAN, NEON_PURPLE])
                pygame.draw.circle(glow, (*color, 30 - hr * 8),
                                   ((100 + hr * 15) // 2, (100 + hr * 15) // 2), 50 + hr * 7)
                game_surface.blit(glow, (lx - 50 - hr * 7, ly - 50 - hr * 7))

        # نمادهای تزئینی
        for ds in demo_symbols:
            ds['y'] += ds['vy']
            if ds['y'] > HEIGHT:
                ds['y'] = -100
                ds['x'] = random.randint(50, WIDTH - 150)
                ds['idx'] = random.randint(0, len(SYMBOLS) - 1)
            draw_symbol(game_surface, ds['idx'], ds['x'], ds['y'], ds['size'], alpha=100)

        # عنوان
        title_y = 130 + math.sin(t * 2) * 8
        draw_text(game_surface, "NEON", 72, WIDTH // 2 - 100, title_y, WHITE, center=True, glow=True)
        draw_text(game_surface, "SLOTS", 72, WIDTH // 2 + 100, title_y, GOLD, center=True, glow=True)
        draw_text(game_surface, "SPIN  /  WIN  /  JACKPOT", 20, WIDTH // 2, title_y + 65,
                  (200, 200, 220), center=True)

        # آمار
        draw_text(game_surface, f"MONEY: ${money[0]}", 26, WIDTH // 2, title_y + 115,
                  GOLD, center=True, glow=True)
        draw_text(game_surface, f"SPINS: {total_spins[0]}   WINS: {total_wins[0]}   BIGGEST: ${biggest_win[0]}",
                  14, WIDTH // 2, title_y + 145, NEON_PINK, center=True)
        draw_text(game_surface, f"LEVEL: {level[0]}   XP: {xp[0]}/{level[0] * 100}",
                  14, WIDTH // 2, title_y + 165, NEON_CYAN, center=True)

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
    btn_shake = Button(WIDTH // 2, 380, 280, 55,
                       f"SHAKE: {'ON' if settings['screen_shake'] else 'OFF'}",
                       NEON_GREEN if settings['screen_shake'] else (100, 100, 100), NEON_CYAN, 22)
    btn_turbo = Button(WIDTH // 2, 445, 280, 55,
                       f"TURBO: {'ON' if settings['turbo_mode'] else 'OFF'}",
                       NEON_YELLOW if settings['turbo_mode'] else (100, 100, 100), NEON_ORANGE, 22)
    btn_reset = Button(WIDTH // 2 - 130, 530, 220, 50, "RESET SAVE", NEON_RED, NEON_ORANGE, 20)
    btn_back = Button(WIDTH // 2 + 130, 530, 220, 50, "BACK", NEON_CYAN, NEON_GREEN, 22)

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

        btn_shake.update(mouse_pos)
        btn_shake.text = f"SHAKE: {'ON' if settings['screen_shake'] else 'OFF'}"
        btn_shake.color = NEON_GREEN if settings['screen_shake'] else (100, 100, 100)
        btn_turbo.update(mouse_pos)
        btn_turbo.text = f"TURBO: {'ON' if settings['turbo_mode'] else 'OFF'}"
        btn_turbo.color = NEON_YELLOW if settings['turbo_mode'] else (100, 100, 100)
        btn_reset.update(mouse_pos)
        btn_back.update(mouse_pos)
        btn_shake.draw(game_surface)
        btn_turbo.draw(game_surface)
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
            if btn_turbo.is_clicked(event):
                settings['turbo_mode'] = not settings['turbo_mode']
                save_async()
            if btn_reset.is_clicked(event):
                settings['sfx_volume'] = 0.7
                settings['music_volume'] = 0.5
                settings['screen_shake'] = True
                settings['turbo_mode'] = False
                for k in achievements:
                    achievements[k]['unlocked'] = False
                highscore[0] = 0
                game_history.clear()
                money[0] = 1000
                total_spins[0] = 0
                total_wins[0] = 0
                biggest_win[0] = 0
                level[0] = 1
                xp[0] = 0
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

        draw_text(game_surface, "SPIN HISTORY", 46, WIDTH // 2, 35, NEON_CYAN, center=True, glow=True)
        draw_text(game_surface, f"Total spins: {len(game_history)}", 16, WIDTH // 2, 72, NEON_YELLOW, center=True)

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
                win = entry.get('win', 0)
                if win > 2000:
                    rank_color, rank = GOLD, "S"
                elif win > 500:
                    rank_color, rank = NEON_PINK, "A"
                elif win > 100:
                    rank_color, rank = NEON_YELLOW, "B"
                elif win > 0:
                    rank_color, rank = NEON_GREEN, "C"
                else:
                    rank_color, rank = (150, 150, 180), "D"
                pygame.draw.rect(game_surface, (15, 8, 30), (ix, iy, iw, item_h - 8), border_radius=6)
                pygame.draw.rect(game_surface, rank_color, (ix, iy, iw, item_h - 8), 2, border_radius=6)
                draw_text(game_surface, rank, 28, ix + 35, iy + (item_h - 8) // 2, rank_color, center=True, glow=True)
                if win > 0:
                    draw_text(game_surface, f"+${win}", 22, ix + 100, iy + 10, GOLD, glow=True)
                else:
                    draw_text(game_surface, "-$0", 22, ix + 100, iy + 10, NEON_RED)
                draw_text(game_surface, f"BET: ${entry.get('bet', 0)}   LINES: {entry.get('lines', 0)}",
                          12, ix + 200, iy + 10, (180, 180, 200))
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
            draw_text(game_surface, "No spins yet", 28, WIDTH // 2, HEIGHT // 2, (150, 150, 180), center=True)

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
    machine = SlotMachine()

    # تنظیمات شرط
    bet = 10
    lines = 10
    max_lines = 20

    # Free Spins
    free_spins = 0
    free_spin_multiplier = 1

    # Gamble
    gamble_active = False
    gamble_amount = 0
    gamble_color = None

    # وضعیت
    spinning = False
    spin_timer = 0
    reel_stop_timer = 0
    auto_spin = False
    game_saved = False

    # نمایش برد
    show_win = False
    win_amount = 0
    win_lines = []
    win_timer = 0
    win_banner = ''
    big_win_banner = 0

    new_achs = []
    notifications = []
    go_anim = 0
    screen_shake = 0
    flash = 0

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
        add_game_to_history(win_amount, bet, lines, machine.reels, new_achs)

    # دکمه‌ها
    btn_spin = Button(WIDTH // 2, HEIGHT - 100, 240, 70, "SPIN", GOLD, NEON_YELLOW, 32)
    btn_max_bet = Button(WIDTH // 2 - 200, HEIGHT - 100, 120, 50, "MAX BET", NEON_ORANGE, NEON_RED, 18)
    btn_bet_minus = Button(WIDTH // 2 - 320, HEIGHT - 100, 60, 50, "-", NEON_RED, NEON_ORANGE, 28)
    btn_bet_plus = Button(WIDTH // 2 + 320, HEIGHT - 100, 60, 50, "+", NEON_GREEN, NEON_CYAN, 28)
    btn_auto = Button(WIDTH // 2 + 200, HEIGHT - 100, 120, 50, "AUTO", NEON_PURPLE, NEON_PINK, 18)

    btn_lines_minus = Button(WIDTH // 2 - 320, HEIGHT - 170, 60, 40, "-", NEON_RED, NEON_ORANGE, 22)
    btn_lines_plus = Button(WIDTH // 2 + 320, HEIGHT - 170, 60, 40, "+", NEON_GREEN, NEON_CYAN, 22)

    btn_menu = Button(100, 50, 150, 40, "MENU", NEON_RED, NEON_ORANGE, 18)
    btn_turbo = Button(WIDTH - 100, 50, 150, 40,
                       f"TURBO: {'ON' if settings['turbo_mode'] else 'OFF'}",
                       NEON_YELLOW if settings['turbo_mode'] else (100, 100, 100), NEON_ORANGE, 16)

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

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    stop_music()
                    if not game_saved:
                        save_current()
                        game_saved = True
                    return
                if event.key == pygame.K_SPACE and not spinning:
                    # شروع چرخش
                    if money[0] >= bet * lines and not gamble_active:
                        money[0] -= bet * lines
                        machine.spin()
                        spinning = True
                        spin_timer = 0
                        reel_stop_timer = 0
                        show_win = False
                        win_amount = 0
                        play_sound('spin')
                        total_spins[0] += 1
                        try_unlock('first_spin')

            # دکمه‌ها
            if not spinning and not gamble_active:
                if btn_spin.is_clicked(event):
                    if money[0] >= bet * lines:
                        money[0] -= bet * lines
                        machine.spin()
                        spinning = True
                        spin_timer = 0
                        reel_stop_timer = 0
                        show_win = False
                        win_amount = 0
                        play_sound('spin')
                        total_spins[0] += 1
                        try_unlock('first_spin')

                if btn_bet_minus.is_clicked(event):
                    bet = max(1, bet - 5)
                if btn_bet_plus.is_clicked(event):
                    bet = min(100, bet + 5)
                if btn_max_bet.is_clicked(event):
                    bet = 100
                    lines = max_lines
                if btn_lines_minus.is_clicked(event):
                    lines = max(1, lines - 1)
                if btn_lines_plus.is_clicked(event):
                    lines = min(max_lines, lines + 1)
                if btn_auto.is_clicked(event):
                    auto_spin = not auto_spin

            if btn_menu.is_clicked(event):
                stop_music()
                if not game_saved:
                    save_current()
                    game_saved = True
                return
            if btn_turbo.is_clicked(event):
                settings['turbo_mode'] = not settings['turbo_mode']
                save_async()

        for notif in notifications[:]:
            notif['timer'] -= 1
            if notif['timer'] <= 0:
                notifications.remove(notif)

        # Gamble buttons
        if gamble_active:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # چک کلیک روی دکمه‌های رنگ
                for i, color in enumerate([NEON_RED, BLACK]):
                    bx = WIDTH // 2 + (i - 0.5) * 300
                    by = HEIGHT // 2 + 100
                    rect = pygame.Rect(bx - 100, by - 60, 200, 120)
                    if rect.collidepoint(mouse_pos):
                        # انتخاب رنگ
                        result = random.choice([NEON_RED, BLACK])
                        if result == color:
                            money[0] += gamble_amount * 2
                            win_amount = gamble_amount * 2
                            big_win_banner = 60
                            play_sound('win_big')
                            try_unlock('gamble_win')
                        else:
                            win_amount = 0
                            play_sound('gameover')
                        gamble_active = False
                        break

        if spinning:
            spin_timer += 1
            machine.update(settings['turbo_mode'])

            # توقف reelها یکی یکی
            reel_stop_timer += 1
            stop_delay = 8 if settings['turbo_mode'] else 15
            if reel_stop_timer > stop_delay:
                reel_stop_timer = 0
                for col in range(REELS):
                    if not machine.reel_stopped[col]:
                        machine.stop_reel(col)
                        break

            # اگه همه متوقف شدن
            if not machine.spinning:
                spinning = False
                # محاسبه برد
                win_amount, win_lines, wild_count, jackpot = calculate_win(machine, bet, lines)

                # Free Spins
                if free_spins > 0:
                    win_amount *= free_spin_multiplier

                if win_amount > 0:
                    money[0] += win_amount
                    total_wins[0] += 1
                    if win_amount > biggest_win[0]:
                        biggest_win[0] = win_amount

                    # XP
                    xp[0] += int(win_amount / 10)
                    while xp[0] >= level[0] * 100:
                        xp[0] -= level[0] * 100
                        level[0] += 1
                        play_sound('win_big')
                        try_unlock('level_10') if level[0] >= 10 else None

                    # banners
                    if jackpot:
                        win_banner = 'JACKPOT!'
                        big_win_banner = 120
                        play_sound('jackpot')
                        if settings['screen_shake']:
                            screen_shake = 30
                        flash = 255
                        try_unlock('jackpot')
                    elif win_amount >= 2000 * bet / 10:
                        win_banner = 'MEGA WIN!'
                        big_win_banner = 90
                        play_sound('win_big')
                        if settings['screen_shake']:
                            screen_shake = 20
                        flash = 200
                        try_unlock('mega_win')
                    elif win_amount >= 500 * bet / 10:
                        win_banner = 'BIG WIN!'
                        big_win_banner = 60
                        play_sound('win_big')
                        if settings['screen_shake']:
                            screen_shake = 15
                        flash = 150
                        try_unlock('big_win')
                    elif win_amount > 0:
                        win_banner = 'WIN!'
                        big_win_banner = 30
                        play_sound('win_medium' if win_amount > 50 else 'win_small')

                    # Coin effect
                    for _ in range(min(30, win_amount // 5)):
                        coin_effects.append(CoinEffect(
                            random.randint(SLOT_X, SLOT_X + SLOT_W),
                            SLOT_Y + SLOT_H // 2
                        ))

                    # Achievement
                    if total_wins[0] >= 1: try_unlock('first_win')
                    if total_wins[0] >= 10: try_unlock('win_10')
                    if total_wins[0] >= 100: try_unlock('win_100')
                    if money[0] >= 5000: try_unlock('money_5000')
                    if money[0] >= 20000: try_unlock('money_20000')
                    if len(win_lines) >= 3: try_unlock('combo_3')
                    if wild_count >= 5: try_unlock('wild_5')
                    if bet >= 100 and win_amount > 0: try_unlock('max_bet_win')

                    # ذرات
                    for line_info in win_lines:
                        line_idx, count, sym_idx = line_info
                        sym_data = SYMBOLS[sym_idx]
                        for _ in range(10):
                            spawn_particles(
                                random.randint(SLOT_X, SLOT_X + SLOT_W),
                                random.randint(SLOT_Y, SLOT_Y + SLOT_H),
                                sym_data[1], 1, 1.5, 1.2
                            )
                else:
                    win_banner = ''
                    play_sound('reel_stop')

                # Free Spins (فرض ساده - Scatter = CROWN)
                crown_count = sum(1 for c in range(REELS) for r in range(ROWS)
                                  if machine.reels[c][r] == 6)
                if crown_count >= 3:
                    free_spins = 10
                    free_spin_multiplier = 2
                    play_sound('free_spins')
                    try_unlock('free_spins')

                if free_spins > 0:
                    free_spins -= 1

                save_current()
                game_saved = True

                if auto_spin and money[0] >= bet * lines and free_spins == 0:
                    # چرخش بعدی بعد از تاخیر
                    pygame.time.wait(500)
                    money[0] -= bet * lines
                    machine.spin()
                    spinning = True
                    spin_timer = 0
                    reel_stop_timer = 0
                    show_win = False
                    play_sound('spin')
                    total_spins[0] += 1

        # آپدیت ذرات و سکه‌ها
        for p in active_particles[:]:
            p.update()
            if not p.active:
                active_particles.remove(p)
        for coin in coin_effects[:]:
            coin.update()
            if not coin.active:
                coin_effects.remove(coin)

        if screen_shake > 0:
            screen_shake -= 1
        if flash > 0:
            flash -= 6
        if big_win_banner > 0:
            big_win_banner -= 1

        # ============================================================
        #                    رسم
        # ============================================================
        game_surface.fill(DARK_BG)
        offset_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        offset_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0

        play_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # پس‌زمینه کازینو
        for y in range(0, HEIGHT, 4):
            alpha = int(80 * (1 - y / HEIGHT))
            s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
            s.fill((10, 20, 50, alpha))
            play_layer.blit(s, (0, y))

        # نور چرخان
        for i in range(6):
            angle = t + i * math.pi / 3
            lx = WIDTH // 2 + math.cos(angle) * 400
            ly = HEIGHT // 2 + math.sin(angle) * 300
            for hr in range(3, 0, -1):
                glow = pygame.Surface((150 + hr * 20, 150 + hr * 20), pygame.SRCALPHA)
                color = [NEON_PURPLE, NEON_PINK, NEON_CYAN, GOLD][i % 4]
                pygame.draw.circle(glow, (*color, 20 - hr * 5),
                                   ((150 + hr * 20) // 2, (150 + hr * 20) // 2), 75 + hr * 10)
                play_layer.blit(glow, (lx - 75 - hr * 10, ly - 75 - hr * 10))

        # فریم ماشین اسلات
        frame_padding = 20
        frame_rect = pygame.Rect(SLOT_X - frame_padding, SLOT_Y - frame_padding,
                                 SLOT_W + frame_padding * 2, SLOT_H + frame_padding * 2)
        # هاله فریم
        for hr in range(5, 0, -1):
            glow = pygame.Surface((frame_rect.w + hr * 15, frame_rect.h + hr * 15), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*GOLD, 50 - hr * 8),
                             (0, 0, frame_rect.w + hr * 15, frame_rect.h + hr * 15), border_radius=20)
            play_layer.blit(glow, (frame_rect.x - hr * 7, frame_rect.y - hr * 7))
        pygame.draw.rect(play_layer, (20, 15, 40), frame_rect, border_radius=15)
        pygame.draw.rect(play_layer, GOLD, frame_rect, 4, border_radius=15)
        pygame.draw.rect(play_layer, WHITE, frame_rect, 1, border_radius=15)

        # نمادها
        for col in range(REELS):
            for row in range(ROWS):
                # موقعیت
                x = SLOT_X + col * (SYMBOL_SIZE + SYMBOL_GAP)
                y = SLOT_Y + row * (SYMBOL_SIZE + SYMBOL_GAP)

                # offset انیمیشن
                if machine.reel_speeds[col] > 0 or machine.reel_stopping[col]:
                    y_offset = machine.reel_offsets[col]
                else:
                    y_offset = 0

                sym_idx = machine.reels[col][row]

                # چک اگه توی win خط هست
                is_winning = False
                for line_info in win_lines:
                    li, count, si = line_info
                    if col < count:
                        # چک موقعیت row توی خط
                        # PAYLINES باید تعریف شده باشه
                        PAYLINES_LOCAL = [
                            [1,1,1,1,1],[0,0,0,0,0],[2,2,2,2,2],
                            [0,1,2,1,0],[2,1,0,1,2],[0,0,1,2,2],[2,2,1,0,0],
                            [1,0,0,0,1],[1,2,2,2,1],[0,1,1,1,0],[2,1,1,1,2],
                            [1,0,1,2,1],[1,2,1,0,1],[0,1,0,1,0],[2,1,2,1,2],
                            [1,0,2,0,1],[1,2,0,2,1],[0,0,2,0,0],[2,2,0,2,2],[0,2,0,2,0],
                        ]
                        if li < len(PAYLINES_LOCAL):
                            if PAYLINES_LOCAL[li][col] == row:
                                if sym_idx == si or sym_idx == 7:
                                    is_winning = True
                                    break

                if is_winning and big_win_banner > 0:
                    # هاله اضافه
                    pulse = 1 + math.sin(t * 15) * 0.1
                    glow_size = int(SYMBOL_SIZE * 1.2 * pulse)
                    glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                    pygame.draw.rect(glow, (*GOLD, 100),
                                     (0, 0, glow_size, glow_size), border_radius=12)
                    play_layer.blit(glow, (x - (glow_size - SYMBOL_SIZE) // 2,
                                           y + y_offset - (glow_size - SYMBOL_SIZE) // 2))

                draw_symbol(play_layer, sym_idx, x, y + y_offset, SYMBOL_SIZE)

        # سکه‌ها
        for coin in coin_effects:
            coin.draw(play_layer)

        # ذرات
        for p in active_particles:
            p.draw(play_layer)

        # Flash
        if flash > 0:
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 240, 150, flash))
            play_layer.blit(fs, (0, 0))

        game_surface.blit(play_layer, (offset_x, offset_y))

        # ============================================================
        #                    HUD
        # ============================================================
        # عنوان
        draw_text(game_surface, "NEON SLOTS", 26, 30, 20, GOLD, glow=True)

        # Money
        draw_text(game_surface, "MONEY", 14, WIDTH - 25, 15, GOLD, center=False)
        draw_text(game_surface, f"${money[0]}", 28, WIDTH - 25, 33, GOLD, glow=True)

        # Level
        draw_text(game_surface, f"LVL {level[0]}", 14, WIDTH - 25, 70, NEON_CYAN)

        # Free Spins
        if free_spins > 0:
            pulse = 1 + math.sin(t * 10) * 0.1
            draw_text(game_surface, f"FREE SPINS: {free_spins}  x{free_spin_multiplier}",
                      int(24 * pulse), WIDTH // 2, 60, GOLD, center=True, glow=True)

        # Win display
        if big_win_banner > 0 and win_amount > 0:
            pulse = 1 + math.sin(t * 12) * 0.15
            if win_banner == 'JACKPOT!':
                color = GOLD
            elif win_banner == 'MEGA WIN!':
                color = NEON_PINK
            elif win_banner == 'BIG WIN!':
                color = NEON_YELLOW
            else:
                color = NEON_GREEN
            draw_text(game_surface, win_banner, int(60 * pulse),
                      WIDTH // 2, 120, color, center=True, glow=True)
            draw_text(game_surface, f"+${win_amount}", int(40 * pulse),
                      WIDTH // 2, 170, GOLD, center=True, glow=True)

        # اطلاعات شرط
        draw_text(game_surface, f"BET: ${bet}", 18, WIDTH // 2 - 350, HEIGHT - 105,
                  WHITE, center=True, glow=True)
        draw_text(game_surface, f"LINES: {lines}", 18, WIDTH // 2 - 350, HEIGHT - 175,
                  WHITE, center=True, glow=True)
        draw_text(game_surface, f"TOTAL: ${bet * lines}", 18, WIDTH // 2, HEIGHT - 175,
                  NEON_YELLOW, center=True, glow=True)

        # دکمه‌ها
        btn_spin.text = "STOP" if spinning else "SPIN"
        btn_spin.update(mouse_pos)
        if not spinning and not gamble_active and money[0] >= bet * lines:
            btn_spin.color = GOLD
        else:
            btn_spin.color = (100, 100, 100)
        btn_spin.draw(game_surface)

        btn_bet_minus.update(mouse_pos)
        btn_bet_plus.update(mouse_pos)
        btn_lines_minus.update(mouse_pos)
        btn_lines_plus.update(mouse_pos)
        btn_max_bet.update(mouse_pos)
        btn_auto.update(mouse_pos)
        btn_menu.update(mouse_pos)
        btn_turbo.update(mouse_pos)

        if not spinning:
            btn_bet_minus.draw(game_surface)
            btn_bet_plus.draw(game_surface)
            btn_lines_minus.draw(game_surface)
            btn_lines_plus.draw(game_surface)
            btn_max_bet.draw(game_surface)
            btn_auto.draw(game_surface)
        btn_menu.draw(game_surface)
        btn_turbo.draw(game_surface)

        # Auto indicator
        if auto_spin:
            pulse = 1 + math.sin(t * 8) * 0.2
            draw_text(game_surface, "AUTO SPIN", int(16 * pulse), WIDTH // 2 + 200, HEIGHT - 140,
                      NEON_YELLOW, center=True, glow=True)

        # راهنما
        if total_spins[0] < 3:
            draw_text(game_surface, "SPACE or SPIN button to play", 16,
                      WIDTH // 2, HEIGHT - 30, NEON_CYAN, center=True)

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

        # Game Over (بدون پول)
        if money[0] < bet * lines and not spinning and not show_win:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            game_surface.blit(overlay, (0, 0))
            box_w = 540
            box_h = 350
            box_x = WIDTH // 2 - box_w // 2
            box_y = HEIGHT // 2 - box_h // 2
            pygame.draw.rect(game_surface, (10, 5, 25), (box_x, box_y, box_w, box_h))
            pygame.draw.rect(game_surface, NEON_RED, (box_x, box_y, box_w, box_h), 3)
            draw_text(game_surface, "OUT OF MONEY!", 50, WIDTH // 2, box_y + 60,
                      NEON_RED, center=True, glow=True)
            draw_text(game_surface, "Would you like to reset?", 24,
                      WIDTH // 2, box_y + 130, WHITE, center=True)

            btn_restart = Button(WIDTH // 2 - 100, box_y + 220, 180, 60, "RESET", NEON_GREEN, NEON_CYAN, 22)
            btn_back = Button(WIDTH // 2 + 100, box_y + 220, 180, 60, "BACK", NEON_YELLOW, NEON_ORANGE, 22)
            btn_restart.update(mouse_pos)
            btn_back.update(mouse_pos)
            btn_restart.draw(game_surface)
            btn_back.draw(game_surface)

            # کلیک روی دکمه‌ها
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_restart.rect.collidepoint(mouse_pos):
                        money[0] = 1000
                        save_async()
                    if btn_back.rect.collidepoint(mouse_pos):
                        stop_music()
                        return

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