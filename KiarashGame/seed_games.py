"""
Seed script: Automatically add all 20 games to the database.

Usage (recommended):
    python manage.py shell < seed_games.py

Or:
    python seed_games.py
"""
import os
import sys

# --- Django setup (only if not already set up) ---
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'KiarashGame.settings')

try:
    import django
    from django.apps import apps
    if not apps.ready:
        django.setup()
except Exception as e:
    print(f"[WARN] Django setup skipped: {e}")


from games.models import Game


# ============================================================
#  ALL 20 GAMES DATA
#  Format: (order, title, slug, cover_image, demo_gif, game_file, description)
# ============================================================
GAMES_DATA = [
    (1, "Neon Space Shooter", "neon-space-shooter", "1.png", "demo1.gif", "neon_space_shooter.py",
     "Classic space shooter with neon graphics, power-ups, and epic boss fights."),

    (2, "Brick Breaker", "brick-breaker", "2.png", "demo2.gif", "brick_breaker.py",
     "Smash through neon bricks with multiball, lasers, and powerful pickups."),

    (3, "Neon Racer", "neon-racer", "3.png", "demo3.gif", "neon_racer.py",
     "High-speed cyberpunk racing with boost, obstacles, and endless highways."),

    (4, "Neon Snake", "neon-snake", "4.png", "demo4.gif", "neon_snake.py",
     "Modern neon take on the classic Snake. Grow, dodge, and survive."),

    (5, "Neon Tetris", "neon-tetris", "5.png", "demo5.gif", "neon_tetris.py",
     "Glowing block puzzle with combos, T-spins, and marathon mode."),

    (6, "Asteroid Hunter", "asteroid-hunter", "6.png", "demo6.gif", "asteroid_hunter.py",
     "Destroy asteroids, dodge UFOs, and survive the neon space storm."),

    (7, "Neon Ninja", "neon-ninja", "7.png", "demo7.gif", "neon_ninja.py",
     "Slicing cyberpunk action with wall jumps, shurikens, and combo attacks."),

    (8, "Neon Archer", "neon-archer", "8.png", "demo8.gif", "neon_archer.py",
     "Aim with your mouse and shoot arrows at waves of incoming enemies."),

    (9, "Neon Pong", "neon-pong", "9.png", "demo9.gif", "neon_pong.py",
     "Reimagined Pong with power-ups, multiball, and fierce AI opponents."),

    (10, "Neon Pac-Man", "neon-pacman", "10.png", "demo10.gif", "neon_pacman.py",
     "Eat pellets, dodge ghosts, and chase the high score in this neon maze."),

    (11, "Neon Defender", "neon-defender", "11.png", "demo11.gif", "neon_defender.py",
     "Tower defense with 5 tower types, enemy waves, and boss battles."),

    (12, "Ninja vs Samurai", "ninja-vs-samurai", "12.png", "demo12.gif", "neon_ninja_vs_samurai.py",
     "1v1 fighting game with combos, special moves, and AI opponents."),

    (13, "Neon Fisher", "neon-fisher", "13.png", "demo13.gif", "neon_fisher.py",
     "Relaxing neon fishing with hooks, coins, power-ups, and frenzy mode."),

    (14, "Neon Helicopter", "neon-helicopter", "14.png", "demo14.gif", "neon_helicopter.py",
     "Flappy-style flying adventure with obstacles, coins, and boss fights."),

    (15, "Neon Darts", "neon-darts", "15.png", "demo15.gif", "neon_darts.py",
     "Classic darts with 301/501/Cricket modes and realistic physics."),

    (16, "Neon 2048", "neon-2048", "16.png", "demo16.gif", "neon_2048.py",
     "Merge glowing tiles to reach 2048 and beyond with smooth animations."),

    (17, "Neon Tower Stack", "neon-tower-stack", "17.png", "demo17.gif", "neon_tower_stack.py",
     "Build the tallest neon tower by stacking blocks with perfect timing."),

    (18, "Neon Minesweeper", "neon-minesweeper", "18.png", "demo18.gif", "neon_minesweeper.py",
     "Classic minesweeper with neon graphics, power-ups, and 3 difficulties."),

    (19, "Neon Slots", "neon-slots", "19.png", "demo19.gif", "neon_slots.py",
     "Spin the reels, hit jackpots, and trigger free spins in neon slots."),

    (20, "Neon Archery", "neon-archery", "20.png", "demo20.gif", "neon_archery.py",
     "Aim, draw, and release. Target practice, time attack, and campaign modes."),
]


def seed_games():
    print("\n" + "=" * 60)
    print("  SEEDING 20 GAMES INTO DATABASE")
    print("=" * 60 + "\n")

    created_count = 0
    updated_count = 0

    for order, title, slug, cover, demo, game_file, description in GAMES_DATA:
        obj, created = Game.objects.update_or_create(
            slug=slug,
            defaults={
                'title': title,
                'description': description,
                'cover_image': cover,
                'demo_gif': demo,
                'game_file': game_file,
                'order': order,
            }
        )
        if created:
            created_count += 1
            print(f"  [+] Added:   {order:2d}. {title}")
        else:
            updated_count += 1
            print(f"  [~] Updated: {order:2d}. {title}")

    print("\n" + "=" * 60)
    print(f"  Created: {created_count}  |  Updated: {updated_count}")
    print(f"  Total games in database: {Game.objects.count()}")
    print("=" * 60 + "\n")


# --- Auto-run when executed as script ---
if __name__ == "__main__":
    seed_games()