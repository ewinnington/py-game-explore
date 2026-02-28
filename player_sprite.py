"""Procedural player sprite generation for DemoBlade.

Produces a heroic warrior character with 4 walk frames, idle, and attack
animations in all 4 directions. Style matches the procedural enemy sprites.
"""

import pygame
import math

# Colour palette – heroic warrior
_SKIN       = (230, 195, 155)
_SKIN_SHADE = (200, 165, 130)
_HAIR       = (80, 55, 35)
_HAIR_LIGHT = (110, 75, 50)
_EYE        = (50, 80, 140)
_TUNIC      = (45, 95, 160)
_TUNIC_LIGHT= (70, 130, 200)
_TUNIC_DARK = (30, 65, 110)
_BELT       = (120, 80, 40)
_BOOT       = (80, 55, 40)
_BOOT_DARK  = (55, 38, 28)
_CAPE       = (150, 40, 45)
_CAPE_LIGHT = (185, 60, 60)
_SWORD      = (190, 200, 210)
_SWORD_EDGE = (220, 225, 230)
_GUARD      = (180, 150, 60)


def build_player_animations():
    """Return dict of animation lists matching the player status strings."""
    anims = {}
    for d in ('down', 'up', 'left', 'right'):
        anims[d] = [_make_walk_frame(d, f) for f in range(4)]
        anims[f'{d}_idle'] = [_make_walk_frame(d, 0)]
        anims[f'{d}_attack'] = [_make_attack_frame(d, f) for f in range(4)]
    return anims


def build_player_icon():
    """Generate the single player.png icon (64x64) for misc use."""
    return _make_walk_frame('down', 0)


def _make_walk_frame(direction, frame):
    """Draw one walk frame of the hero character (64x64)."""
    W, H = 64, 64
    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    cx = W // 2
    cy = H // 2 + 6

    # Walk cycle offsets
    bob   = (0, -2, 0, 2)[frame]
    foot  = (-3, -1, 3, 1)[frame]
    arm_s = (3, 1, -3, -1)[frame]

    # --- Shadow ---
    shadow = pygame.Surface((32, 8), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 40), shadow.get_rect())
    surf.blit(shadow, (cx - 16, cy + 16))

    # --- Cape (behind character) ---
    if direction == 'down':
        _draw_cape_back(surf, cx, cy, bob)
    elif direction == 'up':
        _draw_cape_front(surf, cx, cy, bob)

    # --- Boots ---
    boot_y = cy + 14 + bob
    pygame.draw.ellipse(surf, _BOOT, (cx - 10 + foot, boot_y, 10, 7))
    pygame.draw.ellipse(surf, _BOOT, (cx + 0 - foot, boot_y, 10, 7))
    # Boot soles
    pygame.draw.ellipse(surf, _BOOT_DARK, (cx - 9 + foot, boot_y + 4, 8, 3))
    pygame.draw.ellipse(surf, _BOOT_DARK, (cx + 1 - foot, boot_y + 4, 8, 3))

    # --- Legs (tunic skirt) ---
    leg_y = cy + 4 + bob
    pygame.draw.rect(surf, _TUNIC_DARK, (cx - 10, leg_y, 20, 12), border_radius=2)

    # --- Body (tunic) ---
    bw, bh = 24, 18
    bx = cx - bw // 2
    by = cy - 8 + bob
    pygame.draw.ellipse(surf, _TUNIC, (bx, by, bw, bh))
    # Highlight
    pygame.draw.ellipse(surf, _TUNIC_LIGHT, (cx - 8, by + 2, 16, 10))
    # Belt
    pygame.draw.rect(surf, _BELT, (bx + 2, by + bh - 6, bw - 4, 4), border_radius=2)
    # Belt buckle
    pygame.draw.rect(surf, (200, 180, 80), (cx - 3, by + bh - 6, 6, 4), border_radius=1)

    # --- Arms ---
    arm_y = by + 5 + bob
    if direction in ('down', 'up'):
        # Left arm
        pygame.draw.ellipse(surf, _SKIN, (bx - 5, arm_y + arm_s, 8, 10))
        pygame.draw.ellipse(surf, _TUNIC, (bx - 4, arm_y + arm_s, 7, 6))
        # Right arm
        pygame.draw.ellipse(surf, _SKIN, (bx + bw - 3, arm_y - arm_s, 8, 10))
        pygame.draw.ellipse(surf, _TUNIC, (bx + bw - 3, arm_y - arm_s, 7, 6))
    elif direction == 'left':
        pygame.draw.ellipse(surf, _SKIN, (bx - 4, arm_y + arm_s, 8, 10))
        pygame.draw.ellipse(surf, _TUNIC, (bx - 3, arm_y + arm_s, 7, 6))
    else:
        pygame.draw.ellipse(surf, _SKIN, (bx + bw - 4, arm_y + arm_s, 8, 10))
        pygame.draw.ellipse(surf, _TUNIC, (bx + bw - 4, arm_y + arm_s, 7, 6))

    # --- Head ---
    hy = by - 14 + bob
    head_w, head_h = 20, 20
    # Hair base (behind head)
    pygame.draw.ellipse(surf, _HAIR, (cx - head_w // 2 - 1, hy - 2, head_w + 2, head_h + 2))
    # Face
    pygame.draw.ellipse(surf, _SKIN, (cx - head_w // 2 + 1, hy + 2, head_w - 2, head_h - 4))

    # --- Face details ---
    _draw_face(surf, cx, hy, bob, direction, head_w, head_h)

    # --- Hair on top ---
    _draw_hair(surf, cx, hy, bob, direction)

    return surf


def _make_attack_frame(direction, frame):
    """Draw one attack frame - base body + sword slash."""
    surf = _make_walk_frame(direction, 0)
    cx = 64 // 2
    cy = 64 // 2 + 6

    # Draw sword slash
    progress = frame / 3.0  # 0 to 1

    if direction == 'down':
        _draw_sword_slash(surf, cx, cy + 12, progress, 0)
    elif direction == 'up':
        _draw_sword_slash(surf, cx, cy - 20, progress, 180)
    elif direction == 'left':
        _draw_sword_slash(surf, cx - 18, cy - 2, progress, 90)
    elif direction == 'right':
        _draw_sword_slash(surf, cx + 18, cy - 2, progress, -90)

    return surf


# ------------------------------------------------------------------
# Detail drawing helpers
# ------------------------------------------------------------------

def _draw_face(surf, cx, hy, bob, direction, hw, hh):
    ey = hy + 10 + bob

    if direction == 'down':
        # Eyes
        pygame.draw.circle(surf, (255, 255, 255), (cx - 4, ey), 3)
        pygame.draw.circle(surf, (255, 255, 255), (cx + 4, ey), 3)
        pygame.draw.circle(surf, _EYE, (cx - 4, ey + 1), 2)
        pygame.draw.circle(surf, _EYE, (cx + 4, ey + 1), 2)
        pygame.draw.circle(surf, (20, 20, 40), (cx - 4, ey + 1), 1)
        pygame.draw.circle(surf, (20, 20, 40), (cx + 4, ey + 1), 1)
        # Nose
        pygame.draw.line(surf, _SKIN_SHADE, (cx, ey + 3), (cx - 1, ey + 5), 1)
        # Mouth
        pygame.draw.line(surf, (180, 130, 110), (cx - 2, ey + 7), (cx + 2, ey + 7), 1)

    elif direction == 'up':
        # Back of head - just hair, no face
        pass

    elif direction == 'left':
        # Side face
        pygame.draw.circle(surf, (255, 255, 255), (cx - 3, ey), 3)
        pygame.draw.circle(surf, _EYE, (cx - 4, ey + 1), 2)
        pygame.draw.circle(surf, (20, 20, 40), (cx - 4, ey + 1), 1)
        # Nose
        pygame.draw.line(surf, _SKIN_SHADE, (cx - 7, ey + 3), (cx - 6, ey + 5), 1)

    elif direction == 'right':
        pygame.draw.circle(surf, (255, 255, 255), (cx + 3, ey), 3)
        pygame.draw.circle(surf, _EYE, (cx + 4, ey + 1), 2)
        pygame.draw.circle(surf, (20, 20, 40), (cx + 4, ey + 1), 1)
        pygame.draw.line(surf, _SKIN_SHADE, (cx + 7, ey + 3), (cx + 6, ey + 5), 1)


def _draw_hair(surf, cx, hy, bob, direction):
    hair_y = hy - 1 + bob

    if direction in ('down', 'up'):
        # Spiky top
        pts = [
            (cx - 10, hair_y + 8),
            (cx - 8,  hair_y - 2),
            (cx - 3,  hair_y + 2),
            (cx,      hair_y - 4),
            (cx + 3,  hair_y + 2),
            (cx + 8,  hair_y - 2),
            (cx + 10, hair_y + 8),
        ]
        pygame.draw.polygon(surf, _HAIR, pts)
        # Highlight
        pygame.draw.polygon(surf, _HAIR_LIGHT, [
            (cx - 5, hair_y + 4),
            (cx, hair_y - 2),
            (cx + 5, hair_y + 4),
        ])
    elif direction == 'left':
        pts = [
            (cx - 8, hair_y + 10),
            (cx - 10, hair_y),
            (cx - 5, hair_y - 3),
            (cx + 2, hair_y - 2),
            (cx + 8, hair_y + 4),
            (cx + 6, hair_y + 10),
        ]
        pygame.draw.polygon(surf, _HAIR, pts)
    elif direction == 'right':
        pts = [
            (cx + 8, hair_y + 10),
            (cx + 10, hair_y),
            (cx + 5, hair_y - 3),
            (cx - 2, hair_y - 2),
            (cx - 8, hair_y + 4),
            (cx - 6, hair_y + 10),
        ]
        pygame.draw.polygon(surf, _HAIR, pts)


def _draw_cape_back(surf, cx, cy, bob):
    """Cape flowing behind (visible when facing down)."""
    cape_y = cy - 6 + bob
    pts = [
        (cx - 10, cape_y),
        (cx + 10, cape_y),
        (cx + 14, cape_y + 22),
        (cx + 8,  cape_y + 26),
        (cx,      cape_y + 24),
        (cx - 8,  cape_y + 26),
        (cx - 14, cape_y + 22),
    ]
    pygame.draw.polygon(surf, _CAPE, pts)
    # Highlight fold
    pygame.draw.polygon(surf, _CAPE_LIGHT, [
        (cx - 4, cape_y + 2),
        (cx + 4, cape_y + 2),
        (cx + 2, cape_y + 18),
        (cx - 2, cape_y + 18),
    ])


def _draw_cape_front(surf, cx, cy, bob):
    """Cape visible from front (when facing up, cape is behind = not drawn large)."""
    # Small shoulder drape visible
    cape_y = cy - 6 + bob
    pygame.draw.arc(surf, _CAPE, (cx - 14, cape_y - 2, 28, 12), 0, 3.14, 3)


def _draw_sword_slash(surf, sx, sy, progress, base_angle):
    """Draw a sword slash arc effect."""
    angle = base_angle + progress * 120 - 60
    rad = math.radians(angle)
    length = 18
    ex = sx + math.cos(rad) * length
    ey = sy + math.sin(rad) * length

    # Sword blade
    pygame.draw.line(surf, _SWORD, (sx, sy), (int(ex), int(ey)), 3)
    pygame.draw.line(surf, _SWORD_EDGE, (sx, sy), (int(ex), int(ey)), 1)

    # Guard
    perp_rad = rad + math.pi / 2
    gx1 = sx + math.cos(perp_rad) * 4
    gy1 = sy + math.sin(perp_rad) * 4
    gx2 = sx - math.cos(perp_rad) * 4
    gy2 = sy - math.sin(perp_rad) * 4
    pygame.draw.line(surf, _GUARD, (int(gx1), int(gy1)), (int(gx2), int(gy2)), 2)

    # Slash trail (arc effect)
    if progress > 0.2:
        trail_alpha = int(150 * (1.0 - progress))
        trail_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        arc_rect = pygame.Rect(2, 2, 36, 36)
        start_a = math.radians(base_angle - 60)
        end_a = math.radians(base_angle + progress * 120 - 60)
        pygame.draw.arc(trail_surf, (255, 255, 200, trail_alpha),
                        arc_rect, min(start_a, end_a), max(start_a, end_a), 2)
        surf.blit(trail_surf, (sx - 20, sy - 20))
