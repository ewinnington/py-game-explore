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
    """Generate a 64x64 clump of tall grass blades.

    Returns a Surface with per-pixel alpha.
    """
    size = TILESIZE
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pal = THEMES[theme]

    base_col = pal['grass_base']
    light_col = pal['grass_light']
    dark_col = pal['grass_dark']

    # draw several blades from a shared base area
    num_blades = random.randint(7, 13)
    base_y = size - 10  # ground line

    for _ in range(num_blades):
        bx = random.randint(12, size - 12)
        blade_h = random.randint(20, 44)
        tip_x = bx + random.randint(-8, 8)
        tip_y = base_y - blade_h
        col = _vary(random.choice([base_col, light_col, dark_col]), 8)

        # each blade is two lines (giving 2px width at base tapering to 1px)
        pygame.draw.line(surf, col, (bx, base_y), (tip_x, tip_y), 2)
        # lighter inner highlight
        hcol = _vary(light_col, 6)
        pygame.draw.line(surf, hcol, (bx, base_y - 2), (tip_x, tip_y + 4))

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
