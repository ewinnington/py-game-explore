import pygame
import math
import random


# ======================================================================
# Spell data  (cooldown = how long the player is locked after casting)
# ======================================================================
magic_data = {
    'fire_cone':    {'cooldown': 400, 'damage': 15},
    'ice_ball':     {'cooldown': 300, 'damage': 20},
    'shadow_blade': {'cooldown': 350, 'damage': 25},
}


# ======================================================================
# FireCone – short-range expanding cone of flame
# ======================================================================
class FireCone(pygame.sprite.Sprite):
    """Stationary cone of flickering fire particles in the player's facing
    direction.  Pierces – hits every enemy in the area once."""

    def __init__(self, player, groups):
        super().__init__(groups)
        self.direction = player.status.split('_')[0]
        self.player = player
        self.lifetime = 30       # frames
        self.age = 0
        self.hit_enemies = set()
        self.piercing = True

        self.cone_length = 85
        self.cone_width = 65

        self.image = self._render()
        self.rect = self._positioned_rect()
        self.hitbox = self.rect.copy()

    # --- positioning ---

    def _positioned_rect(self):
        pr = self.player.rect
        if self.direction == 'down':
            return self.image.get_rect(midtop=pr.midbottom)
        if self.direction == 'up':
            return self.image.get_rect(midbottom=pr.midtop)
        if self.direction == 'left':
            return self.image.get_rect(midright=pr.midleft)
        return self.image.get_rect(midleft=pr.midright)

    # --- particle rendering ---

    def _render(self):
        vertical = self.direction in ('up', 'down')
        w = (self.cone_width + 20) if vertical else (self.cone_length + 10)
        h = (self.cone_length + 10) if vertical else (self.cone_width + 20)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2

        fade = max(0.0, 1.0 - self.age / self.lifetime)
        n = int(30 * fade) + 8

        for _ in range(n):
            t = random.uniform(0.05, 1.0)
            spread = self.cone_width * 0.5 * t
            off = random.uniform(-spread, spread)

            if self.direction == 'down':
                px, py = cx + off, t * self.cone_length
            elif self.direction == 'up':
                px, py = cx + off, h - t * self.cone_length
            elif self.direction == 'right':
                px, py = t * self.cone_length, cy + off
            else:
                px, py = w - t * self.cone_length, cy + off

            r = min(255, 200 + random.randint(0, 55))
            g = max(0, min(255, 220 - int(180 * t) + random.randint(-30, 30)))
            b = max(0, random.randint(0, int(30 * (1 - t))))
            a = max(0, min(255, int(210 * (1 - t * 0.4) * fade)))
            sz = max(2, int(8 * (1 - t * 0.3) * fade))

            dot = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot, (r, g, b, a), (sz, sz), sz)
            surf.blit(dot, (int(px - sz), int(py - sz)))

        return surf

    def update(self):
        self.age += 1
        if self.age >= self.lifetime:
            self.kill()
            return
        self.image = self._render()
        self.rect = self._positioned_rect()
        self.hitbox = self.rect.copy()


# ======================================================================
# IceBall – fast straight-line projectile
# ======================================================================
_DIR_VEC = {
    'up': (0, -1), 'down': (0, 1),
    'left': (-1, 0), 'right': (1, 0),
}


class IceBall(pygame.sprite.Sprite):
    """Glowing blue sphere that shoots in a straight line."""

    def __init__(self, player, groups):
        super().__init__(groups)
        dstr = player.status.split('_')[0]
        self.velocity = pygame.math.Vector2(_DIR_VEC.get(dstr, (0, 1)))
        self.speed = 14
        self.lifetime = 90
        self.age = 0
        self.hit_enemies = set()
        self.piercing = False

        self._base = _ice_ball_surface()
        self.image = self._base.copy()

        origin = {
            'up': player.rect.midtop,
            'down': player.rect.midbottom,
            'left': player.rect.midleft,
            'right': player.rect.midright,
        }.get(dstr, player.rect.midbottom)

        self.pos = pygame.math.Vector2(origin)
        self.rect = self.image.get_rect(center=origin)
        self.hitbox = pygame.Rect(0, 0, 16, 16)
        self.hitbox.center = self.rect.center

    def update(self):
        self.age += 1
        if self.age >= self.lifetime:
            self.kill()
            return

        self.pos += self.velocity * self.speed
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = self.rect.center

        # subtle shimmer
        self.image = self._base.copy()
        v = int(18 * math.sin(self.age * 0.6))
        self.image.fill((max(0, v), max(0, v), max(0, v + 8), 0),
                        special_flags=pygame.BLEND_RGBA_ADD)


# ======================================================================
# ShadowBlade – wavy homing dark blade (1.25 s lifetime)
# ======================================================================
class ShadowBlade(pygame.sprite.Sprite):
    """Dark crescent that weaves along a sinusoidal path while homing
    toward the nearest enemy.  Launched in the player's facing direction,
    the blade oscillates perpendicular to its travel vector, creating a
    serpentine flight path."""

    def __init__(self, player, groups, enemy_sprites):
        super().__init__(groups)
        self.enemy_sprites = enemy_sprites
        dstr = player.status.split('_')[0]
        self.velocity = pygame.math.Vector2(_DIR_VEC.get(dstr, (0, 1)))
        self.speed = 8
        self.homing = 0.12
        self.detect_range = 250
        self.lifetime = 75          # 1.25 s at 60 fps
        self.age = 0
        self.hit_enemies = set()
        self.piercing = False
        self.rotation = 0.0

        # Wavy flight parameters
        self.wave_freq = 0.28       # radians per frame
        self.wave_amp = 16.0        # pixels of lateral swing

        self._base = _shadow_blade_surface()
        self.image = self._base
        self.target = self._closest_enemy(player.rect.center)

        origin = {
            'up': player.rect.midtop,
            'down': player.rect.midbottom,
            'left': player.rect.midleft,
            'right': player.rect.midright,
        }.get(dstr, player.rect.midbottom)

        # base_pos follows the homing path; pos adds the wave offset
        self.base_pos = pygame.math.Vector2(origin)
        self.pos = pygame.math.Vector2(origin)
        self.rect = self.image.get_rect(center=origin)
        self.hitbox = pygame.Rect(0, 0, 20, 20)
        self.hitbox.center = self.rect.center

    def _closest_enemy(self, origin):
        best, best_d = None, self.detect_range
        for e in self.enemy_sprites:
            if hasattr(e, 'state') and e.state == 4:   # DYING
                continue
            d = pygame.math.Vector2(
                e.rect.centerx - origin[0],
                e.rect.centery - origin[1],
            ).length()
            if d < best_d:
                best_d = d
                best = e
        return best

    def update(self):
        self.age += 1
        if self.age >= self.lifetime:
            self.kill()
            return

        # --- homing steering ---
        if self.target and self.target.alive():
            if hasattr(self.target, 'state') and self.target.state == 4:
                self.target = None
            else:
                to = pygame.math.Vector2(
                    self.target.rect.centerx - self.base_pos.x,
                    self.target.rect.centery - self.base_pos.y,
                )
                if to.length() > 0:
                    desired = to.normalize()
                    self.velocity += (desired - self.velocity) * self.homing
                    if self.velocity.length() > 0:
                        self.velocity = self.velocity.normalize()

        # --- advance along homing path ---
        self.base_pos += self.velocity * self.speed

        # --- wavy offset perpendicular to travel direction ---
        perp = pygame.math.Vector2(-self.velocity.y, self.velocity.x)
        wave = math.sin(self.age * self.wave_freq) * self.wave_amp
        self.pos = self.base_pos + perp * wave

        # --- spin & render ---
        self.rotation += 14
        self.image = pygame.transform.rotate(self._base, self.rotation)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.hitbox.center = self.rect.center


# ======================================================================
# Procedural surfaces – projectile graphics
# ======================================================================

def _ice_ball_surface():
    sz = 28
    surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
    c = sz // 2
    for i in range(13, 0, -1):
        a = int(40 * (i / 13))
        pygame.draw.circle(surf, (80, 160, 255, a), (c, c), i)
    pygame.draw.circle(surf, (150, 210, 255), (c, c), 8)
    pygame.draw.circle(surf, (210, 235, 255), (c, c), 6)
    pygame.draw.circle(surf, (255, 255, 255), (c - 2, c - 2), 3)
    return surf


def _shadow_blade_surface():
    sz = 28
    surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
    c = sz // 2
    for r in range(12, 0, -2):
        a = int(28 * (r / 12))
        pygame.draw.circle(surf, (60, 15, 100, a), (c, c), r)
    blade = [(c, c - 10), (c + 5, c), (c, c + 10), (c - 3, c)]
    pygame.draw.polygon(surf, (100, 35, 160), blade)
    pygame.draw.polygon(surf, (160, 80, 210), blade, 1)
    pygame.draw.circle(surf, (50, 10, 80), (c, c), 2)
    return surf


# ======================================================================
# Procedural surfaces – ring-menu icons  (32 x 32)
# ======================================================================

def _make_fire_icon(s=32):
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    cx, cy = s // 2, s // 2
    # glow
    for r in range(s // 2, 0, -2):
        a = int(40 * r / (s // 2))
        pygame.draw.circle(surf, (255, 100, 0, a), (cx, cy), r)
    # outer flame
    pts = [(cx, cy - s // 3), (cx + s // 4, cy + 2),
           (cx + s // 6, cy + s // 3), (cx, cy + s // 4),
           (cx - s // 6, cy + s // 3), (cx - s // 4, cy + 2)]
    pygame.draw.polygon(surf, (255, 155, 25), pts)
    # inner flame
    inn = [(cx, cy - s // 5), (cx + s // 7, cy + 2),
           (cx, cy + s // 5), (cx - s // 7, cy + 2)]
    pygame.draw.polygon(surf, (255, 230, 80), inn)
    return surf


def _make_ice_icon(s=32):
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    cx, cy = s // 2, s // 2
    r = s // 3
    for i in range(r + 4, 0, -1):
        a = int(30 * i / (r + 4))
        pygame.draw.circle(surf, (100, 180, 255, a), (cx, cy), i)
    pygame.draw.circle(surf, (140, 200, 255), (cx, cy), r)
    pygame.draw.circle(surf, (200, 230, 255), (cx, cy), r - 2)
    pygame.draw.circle(surf, (240, 250, 255), (cx - 2, cy - 3), r // 3)
    for deg in range(0, 360, 60):
        rad = math.radians(deg)
        x1 = cx + math.cos(rad) * r
        y1 = cy + math.sin(rad) * r
        x2 = cx + math.cos(rad) * (r + 4)
        y2 = cy + math.sin(rad) * (r + 4)
        pygame.draw.line(surf, (180, 220, 255),
                         (int(x1), int(y1)), (int(x2), int(y2)), 2)
    return surf


def _make_shadow_icon(s=32):
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    cx, cy = s // 2, s // 2
    for r in range(s // 2, 0, -2):
        a = int(30 * r / (s // 2))
        pygame.draw.circle(surf, (60, 20, 100, a), (cx, cy), r)
    blade = [(cx - 2, cy - s // 3), (cx + s // 4, cy - s // 5),
             (cx + s // 3, cy), (cx + s // 4, cy + s // 5),
             (cx - 2, cy + s // 3), (cx + s // 8, cy + s // 6),
             (cx + s // 6, cy), (cx + s // 8, cy - s // 6)]
    pygame.draw.polygon(surf, (120, 50, 180), blade)
    pygame.draw.polygon(surf, (170, 90, 220), blade, 1)
    pygame.draw.circle(surf, (200, 150, 255), (cx + s // 4, cy - 2), 2)
    return surf


# Attach icons to magic_data so player.py can reference them
magic_data['fire_cone']['icon']    = _make_fire_icon()
magic_data['ice_ball']['icon']     = _make_ice_icon()
magic_data['shadow_blade']['icon'] = _make_shadow_icon()
