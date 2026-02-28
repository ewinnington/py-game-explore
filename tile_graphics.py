"""Procedural tile graphics for DemoBlade's four themed levels."""

import pygame
import random
from data import TILESIZE

# ---------------------------------------------------------------------------
# Theme colour palettes
# ---------------------------------------------------------------------------
THEMES = {
    'meadow': {
        'grass_base': (80, 140, 50),
        'grass_light': (100, 170, 65),
        'grass_dark': (60, 110, 40),
        'rock_tint': (0, 10, 0),
    },
    'darkwoods': {
        'grass_base': (40, 80, 30),
        'grass_light': (50, 95, 38),
        'grass_dark': (30, 60, 22),
        'rock_tint': (-10, 0, -5),
    },
    'swarm': {
        'grass_base': (120, 110, 50),
        'grass_light': (140, 130, 65),
        'grass_dark': (95, 85, 38),
        'rock_tint': (5, 0, -10),
    },
    'demonsgate': {
        'grass_base': (60, 45, 35),
        'grass_light': (75, 55, 42),
        'grass_dark': (45, 35, 28),
        'rock_tint': (10, -5, -10),
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(v, lo=0, hi=255):
    """Clamp an integer to [lo, hi]."""
    return max(lo, min(hi, int(v)))


def _tint(base, offset):
    """Add an (r,g,b) offset to a base colour, clamping each channel."""
    return (_clamp(base[0] + offset[0]),
            _clamp(base[1] + offset[1]),
            _clamp(base[2] + offset[2]))


def _vary(color, amount=10):
    """Return a slightly randomised copy of *color*."""
    return (_clamp(color[0] + random.randint(-amount, amount)),
            _clamp(color[1] + random.randint(-amount, amount)),
            _clamp(color[2] + random.randint(-amount, amount)))


# ---------------------------------------------------------------------------
# Floor surface
# ---------------------------------------------------------------------------

def make_floor_surface(theme, width=1280, height=1216):
    """Create a large themed floor background surface.

    Parameters
    ----------
    theme : str
        One of 'meadow', 'darkwoods', 'swarm', 'demonsgate'.
    width, height : int
        Pixel dimensions of the floor surface.

    Returns
    -------
    pygame.Surface
    """
    pal = THEMES[theme]
    surf = pygame.Surface((width, height))
    surf.fill(pal['grass_base'])

    # -- noise patches (lighter / darker splotches) -------------------------
    for _ in range(width * height // 120):
        px = random.randint(0, width - 1)
        py = random.randint(0, height - 1)
        size = random.randint(4, 8)
        col = _vary(random.choice([pal['grass_light'], pal['grass_dark']]), 8)
        pygame.draw.rect(surf, col, (px, py, size, size))

    # -- theme-specific detail layers ----------------------------------------
    if theme == 'meadow':
        # tiny flowers scattered across the meadow
        flower_colors = [(220, 60, 60), (240, 200, 50), (200, 120, 220),
                         (255, 255, 255), (255, 160, 60)]
        for _ in range(width * height // 2000):
            fx = random.randint(2, width - 3)
            fy = random.randint(2, height - 3)
            fc = random.choice(flower_colors)
            pygame.draw.rect(surf, fc, (fx, fy, 2, 2))
            # tiny green stem below
            pygame.draw.rect(surf, pal['grass_dark'], (fx, fy + 2, 1, 2))

    elif theme == 'darkwoods':
        # mossy patches – slightly blue-green blobs
        for _ in range(width * height // 800):
            mx = random.randint(0, width - 1)
            my = random.randint(0, height - 1)
            mr = random.randint(3, 7)
            mc = _vary((35, 75, 45), 10)
            pygame.draw.circle(surf, mc, (mx, my), mr)

    elif theme == 'swarm':
        # dried / sandy patches
        for _ in range(width * height // 600):
            dx = random.randint(0, width - 1)
            dy = random.randint(0, height - 1)
            ds = random.randint(4, 10)
            dc = _vary((140, 130, 80), 12)
            pygame.draw.rect(surf, dc, (dx, dy, ds, ds))

    elif theme == 'demonsgate':
        # ember-red glowing spots on charred ground
        for _ in range(width * height // 1500):
            ex = random.randint(0, width - 1)
            ey = random.randint(0, height - 1)
            er = random.randint(2, 5)
            ec = _vary((180, 50, 20), 20)
            pygame.draw.circle(surf, ec, (ex, ey), er)
        # ash streaks
        for _ in range(width * height // 3000):
            sx = random.randint(0, width - 6)
            sy = random.randint(0, height - 1)
            sl = random.randint(6, 18)
            sc = _vary((40, 38, 36), 5)
            pygame.draw.line(surf, sc, (sx, sy), (sx + sl, sy))

    return surf


# ---------------------------------------------------------------------------
# Rock obstacle  (64x64)
# ---------------------------------------------------------------------------

def make_rock(theme='meadow'):
    """Generate a 64x64 rock sprite with theme-appropriate tint.

    Returns a Surface with per-pixel alpha.
    """
    size = TILESIZE
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pal = THEMES[theme]
    tint = pal['rock_tint']

    # base grey stone colour
    base = _tint((128, 128, 128), tint)
    highlight = _tint((170, 170, 170), tint)
    shadow = _tint((85, 85, 85), tint)

    # main body – an irregular ellipse built from overlapping circles
    cx, cy = size // 2, size // 2 + 4
    # large base shape
    pygame.draw.ellipse(surf, base, (8, 14, 48, 40))
    # highlight top-left area
    pygame.draw.ellipse(surf, highlight, (12, 14, 30, 20))
    # shadow bottom-right
    pygame.draw.ellipse(surf, shadow, (26, 34, 28, 18))

    # surface noise
    for _ in range(90):
        nx = random.randint(10, size - 12)
        ny = random.randint(16, size - 12)
        # only draw inside the rough ellipse
        dx = (nx - cx) / 24.0
        dy = (ny - cy) / 20.0
        if dx * dx + dy * dy <= 1.0:
            nc = _vary(base, 15)
            pygame.draw.rect(surf, nc, (nx, ny, 2, 2))

    # crack lines
    for _ in range(random.randint(1, 3)):
        x1 = random.randint(16, 46)
        y1 = random.randint(20, 44)
        x2 = x1 + random.randint(-10, 10)
        y2 = y1 + random.randint(-6, 6)
        pygame.draw.line(surf, shadow, (x1, y1), (x2, y2))

    return surf


# ---------------------------------------------------------------------------
# Grass tuft  (64x64)
# ---------------------------------------------------------------------------

def make_grass_tuft(theme='meadow'):
    """Generate a 64x64 bush obstacle with contrasting flowers/vines.

    Returns a Surface with per-pixel alpha.  Designed to stand out
    clearly against the themed floor background.
    """
    size = TILESIZE
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pal = THEMES[theme]

    # Use DARKER shades than the floor so the bush contrasts
    bush_dark = (_clamp(pal['grass_dark'][0] - 20),
                 _clamp(pal['grass_dark'][1] - 15),
                 _clamp(pal['grass_dark'][2] - 20))
    bush_mid = pal['grass_dark']
    bush_light = pal['grass_base']

    cx, cy = size // 2, size // 2 + 6  # slightly lower center

    # -- shadow on ground --
    pygame.draw.ellipse(surf, (0, 0, 0, 50), (8, size - 14, 48, 12))

    # -- main bush body: overlapping ellipses for a chunky shrub shape --
    # Large dark base
    pygame.draw.ellipse(surf, bush_dark, (8, 16, 48, 38))
    # Medium mid-tone overlay (upper-left bias = highlight)
    pygame.draw.ellipse(surf, bush_mid, (10, 14, 40, 30))
    # Small lighter crown
    pygame.draw.ellipse(surf, bush_light, (14, 12, 32, 22))

    # -- leafy texture: small random circles across the bush --
    for _ in range(25):
        lx = random.randint(12, size - 12)
        ly = random.randint(14, size - 16)
        # Only draw inside the rough ellipse shape
        dx = (lx - cx) / 24.0
        dy = (ly - cy) / 19.0
        if dx * dx + dy * dy <= 1.0:
            lr = random.randint(2, 4)
            lc = _vary(random.choice([bush_dark, bush_mid, bush_light]), 12)
            pygame.draw.circle(surf, lc, (lx, ly), lr)

    # -- dark outline strokes for definition --
    outline_col = (_clamp(bush_dark[0] - 30),
                   _clamp(bush_dark[1] - 25),
                   _clamp(bush_dark[2] - 30))
    pygame.draw.ellipse(surf, outline_col, (8, 16, 48, 38), 2)

    # -- colourful flowers / accents on top (theme-varied) --
    if theme == 'meadow':
        flower_colors = [
            (220, 60, 80),    # red
            (240, 200, 50),   # yellow
            (200, 120, 220),  # purple
            (255, 255, 255),  # white
            (255, 140, 50),   # orange
        ]
    elif theme == 'darkwoods':
        flower_colors = [
            (180, 80, 220),   # purple
            (255, 255, 255),  # white
            (100, 200, 255),  # pale blue
            (220, 180, 255),  # lavender
        ]
    elif theme == 'swarm':
        flower_colors = [
            (255, 200, 80),   # gold
            (255, 140, 50),   # orange
            (220, 220, 180),  # cream
        ]
    else:  # demonsgate
        flower_colors = [
            (255, 80, 40),    # fiery red
            (255, 160, 30),   # ember orange
            (200, 60, 200),   # dark purple
        ]

    # Scatter 4-7 flowers on the bush surface
    num_flowers = random.randint(4, 7)
    for _ in range(num_flowers):
        fx = random.randint(14, size - 14)
        fy = random.randint(14, size - 20)
        dx = (fx - cx) / 22.0
        dy = (fy - cy) / 17.0
        if dx * dx + dy * dy <= 0.85:
            fc = random.choice(flower_colors)
            # Flower = small circle with a bright center dot
            pygame.draw.circle(surf, fc, (fx, fy), 3)
            pygame.draw.circle(surf, (255, 255, 220), (fx, fy), 1)

    # -- small vine/leaf tips poking out at edges --
    for _ in range(random.randint(3, 5)):
        side = random.choice(['left', 'right', 'top'])
        if side == 'left':
            vx = random.randint(4, 10)
            vy = random.randint(20, 44)
        elif side == 'right':
            vx = random.randint(size - 10, size - 4)
            vy = random.randint(20, 44)
        else:
            vx = random.randint(16, size - 16)
            vy = random.randint(8, 14)
        vc = _vary(bush_light, 10)
        pygame.draw.circle(surf, vc, (vx, vy), 2)

    return surf


# ---------------------------------------------------------------------------
# Column / pillar  (64x128)
# ---------------------------------------------------------------------------

def make_column(theme='meadow'):
    """Generate a 64x128 stone column with wider top/base, banding, and cracks.

    Returns a Surface with per-pixel alpha.
    """
    w = TILESIZE        # 64
    h = TILESIZE * 2    # 128
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pal = THEMES[theme]
    tint = pal['rock_tint']

    base_col = _tint((145, 140, 135), tint)
    light_col = _tint((175, 170, 165), tint)
    shadow_col = _tint((100, 95, 90), tint)
    dark_col = _tint((75, 70, 65), tint)

    # -- wider base (bottom 16px) -------------------------------------------
    base_rect = pygame.Rect(6, h - 16, w - 12, 16)
    pygame.draw.rect(surf, base_col, base_rect)
    pygame.draw.rect(surf, light_col, (6, h - 16, w - 12, 3))    # top highlight
    pygame.draw.rect(surf, shadow_col, (6, h - 3, w - 12, 3))    # bottom shadow

    # -- wider capital / top (top 14px) -------------------------------------
    cap_rect = pygame.Rect(8, 4, w - 16, 14)
    pygame.draw.rect(surf, base_col, cap_rect)
    pygame.draw.rect(surf, light_col, (8, 4, w - 16, 3))
    pygame.draw.rect(surf, shadow_col, (8, 15, w - 16, 3))

    # -- shaft (between capital and base) -----------------------------------
    shaft_top = 18
    shaft_bot = h - 16
    shaft_left = 14
    shaft_right = w - 14
    shaft_w = shaft_right - shaft_left
    shaft_rect = pygame.Rect(shaft_left, shaft_top, shaft_w, shaft_bot - shaft_top)
    pygame.draw.rect(surf, base_col, shaft_rect)

    # left highlight strip
    pygame.draw.rect(surf, light_col, (shaft_left, shaft_top, 4, shaft_bot - shaft_top))
    # right shadow strip
    pygame.draw.rect(surf, shadow_col, (shaft_right - 4, shaft_top, 4, shaft_bot - shaft_top))

    # -- horizontal banding -------------------------------------------------
    band_y = shaft_top + 8
    while band_y < shaft_bot - 8:
        bc = _vary(dark_col, 5)
        pygame.draw.line(surf, bc, (shaft_left + 2, band_y),
                         (shaft_right - 3, band_y))
        band_y += random.randint(10, 18)

    # -- cracks -------------------------------------------------------------
    for _ in range(random.randint(2, 4)):
        cx = random.randint(shaft_left + 4, shaft_right - 5)
        cy = random.randint(shaft_top + 6, shaft_bot - 10)
        for seg in range(random.randint(2, 4)):
            nx = cx + random.randint(-5, 5)
            ny = cy + random.randint(2, 8)
            pygame.draw.line(surf, dark_col, (cx, cy), (nx, ny))
            cx, cy = nx, ny

    # -- surface noise on shaft --------------------------------------------
    for _ in range(60):
        nx = random.randint(shaft_left + 1, shaft_right - 2)
        ny = random.randint(shaft_top + 1, shaft_bot - 2)
        nc = _vary(base_col, 10)
        surf.set_at((nx, ny), (*nc, 255))

    return surf


# ---------------------------------------------------------------------------
# Chainmail stand  (64x64)
# ---------------------------------------------------------------------------

def make_chainmail_stand():
    """Generate a 64x64 wooden stand displaying silver chainmail.

    Returns a Surface with per-pixel alpha.
    """
    size = TILESIZE
    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    # -- colours ------------------------------------------------------------
    wood_base = (120, 80, 40)
    wood_dark = (90, 58, 28)
    wood_light = (145, 100, 55)
    mail_base = (170, 175, 180)
    mail_dark = (120, 125, 130)
    mail_light = (210, 215, 220)

    # -- wooden stand legs & crossbar ---------------------------------------
    # two vertical legs
    pygame.draw.rect(surf, wood_base, (18, 22, 6, 40))
    pygame.draw.rect(surf, wood_base, (40, 22, 6, 40))
    # left highlight
    pygame.draw.rect(surf, wood_light, (18, 22, 2, 40))
    pygame.draw.rect(surf, wood_light, (40, 22, 2, 40))
    # right shadow
    pygame.draw.rect(surf, wood_dark, (22, 22, 2, 40))
    pygame.draw.rect(surf, wood_dark, (44, 22, 2, 40))

    # horizontal crossbar at top
    pygame.draw.rect(surf, wood_base, (14, 18, 36, 6))
    pygame.draw.rect(surf, wood_light, (14, 18, 36, 2))
    pygame.draw.rect(surf, wood_dark, (14, 22, 36, 2))

    # base plank
    pygame.draw.rect(surf, wood_base, (10, 58, 44, 5))
    pygame.draw.rect(surf, wood_light, (10, 58, 44, 2))

    # -- chainmail draped on crossbar (small interlocking circles) ----------
    mail_top = 20
    mail_bottom = 52
    mail_left = 20
    mail_right = 44
    ring_r = 3

    row = 0
    y = mail_top
    while y < mail_bottom:
        offset = (ring_r) if (row % 2) else 0
        x = mail_left + offset
        while x < mail_right:
            # draw a small ring
            col = _vary(mail_base, 8)
            pygame.draw.circle(surf, col, (x, y), ring_r, 1)
            # tiny highlight at top-left of ring
            pygame.draw.rect(surf, mail_light, (x - 1, y - 2, 1, 1))
            # tiny shadow at bottom-right
            pygame.draw.rect(surf, mail_dark, (x + 1, y + 1, 1, 1))
            x += ring_r * 2
        y += ring_r * 2 - 1
        row += 1

    return surf
