"""Procedural weapon sprite generation for DemoBlade.

Provides make_weapon_sprite() and make_weapon_icon() using only pygame.draw.
"""

import pygame

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
_BLADE      = (190, 200, 210)
_BLADE_EDGE = (220, 225, 235)
_BLADE_DARK = (140, 150, 165)
_GUARD      = (200, 170,  50)
_GRIP       = (100,  70,  40)
_GRIP_DARK  = ( 70,  50,  30)
_SHAFT      = (130,  95,  55)
_SHAFT_DARK = ( 95,  70,  40)
_SPEAR_TIP  = (200, 210, 220)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _draw_sword_down(w: int, h: int) -> pygame.Surface:
    """Draw a sword pointing downward (canonical orientation).

    Layout (top to bottom) — grip near player, blade away:
      - Pommel  : very top
      - Grip    : top ~25 %
      - Guard   : thin band
      - Blade   : bottom ~58 % with pointed tip at very bottom
    """
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    cx = w // 2  # centre-x

    # -- pommel (top) --
    pygame.draw.circle(surf, _GUARD, (cx, 3), 3)

    # -- grip --
    grip_top = 6
    grip_bot = int(h * 0.28)
    grip_hw = 3
    pygame.draw.rect(surf, _GRIP,
                     (cx - grip_hw, grip_top, grip_hw * 2, grip_bot - grip_top))
    # wrap lines for texture
    for yy in range(grip_top + 3, grip_bot, 4):
        pygame.draw.line(surf, _GRIP_DARK,
                         (cx - grip_hw, yy), (cx + grip_hw - 1, yy), 1)

    # -- cross-guard --
    guard_y = grip_bot + 1
    guard_h = 4
    pygame.draw.rect(surf, _GUARD, (0, guard_y, w, guard_h))
    # small highlight
    pygame.draw.rect(surf, (230, 200, 80), (1, guard_y, w - 2, 1))

    # -- blade (guard to bottom, tip at very bottom) --
    blade_top = guard_y + guard_h
    blade_hw = w // 2 - 2

    # main blade body — triangle with flat top edge, pointed tip at bottom
    pygame.draw.polygon(surf, _BLADE, [
        (cx - blade_hw, blade_top),
        (cx + blade_hw, blade_top),
        (cx, h),                     # pointed tip at bottom
    ])
    # lighter edge highlight (left)
    pygame.draw.line(surf, _BLADE_EDGE,
                     (cx - blade_hw, blade_top),
                     (cx, h), 1)
    # darker edge (right)
    pygame.draw.line(surf, _BLADE_DARK,
                     (cx + blade_hw, blade_top),
                     (cx, h), 1)
    # centre fuller (dark line down the middle)
    pygame.draw.line(surf, _BLADE_DARK,
                     (cx, blade_top + 2),
                     (cx, h - 4), 1)

    return surf


def _draw_spear_down(w: int, h: int) -> pygame.Surface:
    """Draw a spear pointing downward (canonical orientation).

    Layout (top to bottom):
      - Shaft butt  : small cap
      - Shaft       : long wooden section
      - Spear tip   : pointed metallic head at bottom
    """
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    cx = w // 2

    # -- tip (bottom) --
    tip_h   = int(h * 0.22)
    tip_top = h - tip_h
    tip_hw  = w // 2 - 2

    pygame.draw.polygon(surf, _SPEAR_TIP, [
        (cx, h),                         # sharp point
        (cx - tip_hw, tip_top),
        (cx + tip_hw, tip_top),
    ])
    # edge highlights
    pygame.draw.line(surf, _BLADE_EDGE,
                     (cx - tip_hw, tip_top), (cx, h), 1)
    pygame.draw.line(surf, _BLADE_DARK,
                     (cx + tip_hw, tip_top), (cx, h), 1)
    # centre ridge
    pygame.draw.line(surf, _BLADE_DARK,
                     (cx, tip_top + 2), (cx, h - 2), 1)

    # -- shaft --
    shaft_top = 4
    shaft_bot = tip_top - 1
    shaft_hw  = 3

    pygame.draw.rect(surf, _SHAFT,
                     (cx - shaft_hw, shaft_top,
                      shaft_hw * 2, shaft_bot - shaft_top))
    # dark edge on right side of shaft
    pygame.draw.line(surf, _SHAFT_DARK,
                     (cx + shaft_hw - 1, shaft_top),
                     (cx + shaft_hw - 1, shaft_bot), 1)
    # grain lines
    for yy in range(shaft_top + 6, shaft_bot, 8):
        pygame.draw.line(surf, _SHAFT_DARK,
                         (cx - shaft_hw + 1, yy),
                         (cx + shaft_hw - 2, yy), 1)

    # -- butt cap --
    pygame.draw.rect(surf, _GRIP_DARK,
                     (cx - shaft_hw - 1, 0, shaft_hw * 2 + 2, 5))
    pygame.draw.rect(surf, _GRIP,
                     (cx - shaft_hw, 1, shaft_hw * 2, 3))

    return surf


def _orient(base_surf: pygame.Surface,
            direction: str,
            vert_size: tuple[int, int],
            horiz_size: tuple[int, int]) -> pygame.Surface:
    """Return *base_surf* (drawn as 'down') transformed for *direction*.

    down  -> as-is
    up    -> vertical flip
    left  -> 90-degree CW rotation then horizontal flip
    right -> 90-degree CW rotation
    """
    if direction == "down":
        return base_surf

    if direction == "up":
        return pygame.transform.flip(base_surf, False, True)

    # For left / right we rotate the canonical surface.
    rotated = pygame.transform.rotate(base_surf, 90)  # CCW 90 → tip points right
    if direction == "right":
        return rotated
    # direction == "left" → flip so tip points left
    return pygame.transform.flip(rotated, True, False)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def make_weapon_sprite(weapon_type: str, direction: str) -> pygame.Surface:
    """Return a pygame Surface for the requested weapon and direction.

    Parameters
    ----------
    weapon_type : 'sword' | 'spear'
    direction   : 'up' | 'down' | 'left' | 'right'
    """
    if weapon_type == "sword":
        vw, vh = 20, 48
        base = _draw_sword_down(vw, vh)
    elif weapon_type == "spear":
        vw, vh = 16, 64
        base = _draw_spear_down(vw, vh)
    else:
        raise ValueError(f"Unknown weapon_type: {weapon_type!r}")

    hw, hh = vh, vw  # horizontal dims are swapped
    return _orient(base, direction, (vw, vh), (hw, hh))


def make_weapon_icon(weapon_type: str) -> pygame.Surface:
    """Return a 32x32 icon surface for the ring menu.

    Sword : angled silver blade with gold guard.
    Spear : angled brown shaft with steel tip.
    """
    size = 32
    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    if weapon_type == "sword":
        # blade from bottom-left to upper-right
        pygame.draw.line(surf, _BLADE,      (6, 28), (24,  4), 3)
        pygame.draw.line(surf, _BLADE_EDGE, (5, 27), (23,  3), 1)
        # cross-guard perpendicular to blade
        pygame.draw.line(surf, _GUARD, (10, 14), (22, 20), 3)
        pygame.draw.line(surf, (230, 200, 80), (11, 15), (21, 19), 1)
        # grip / pommel
        pygame.draw.line(surf, _GRIP, (4, 29), (8, 25), 2)
        pygame.draw.circle(surf, _GUARD, (4, 29), 2)

    elif weapon_type == "spear":
        # shaft diagonal
        pygame.draw.line(surf, _SHAFT,      (8, 28), (26,  6), 2)
        pygame.draw.line(surf, _SHAFT_DARK, (9, 29), (27,  7), 1)
        # spear tip (small triangle at upper-right end)
        pygame.draw.polygon(surf, _SPEAR_TIP, [
            (26, 6),
            (28, 2),
            (30, 4),
        ])
        pygame.draw.polygon(surf, _BLADE_EDGE, [
            (26, 6),
            (28, 2),
            (30, 4),
        ], 1)
        # butt cap at lower-left
        pygame.draw.circle(surf, _GRIP_DARK, (7, 29), 2)

    else:
        raise ValueError(f"Unknown weapon_type: {weapon_type!r}")

    return surf
