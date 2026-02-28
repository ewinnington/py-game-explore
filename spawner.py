import pygame
import math
import random
from enemy import Enemy


# ======================================================================
# CaveSpawner – dark cave entrance that periodically spawns enemies
# ======================================================================

class CaveSpawner(pygame.sprite.Sprite):
    """A rocky cave exit that periodically spawns enemy demons.

    Visual: dark stone archway built procedurally.
    Behaviour: every `spawn_interval` ms, a new Enemy walks out of the
    cave mouth – up to `max_alive` enemies at a time.
    """

    def __init__(self, pos, groups, obstacle_sprites,
                 enemy_groups, player,
                 spawn_interval=4000, max_alive=5):
        """
        pos:             (x, y) world position for the cave base-center.
        groups:          sprite groups this spawner belongs to (e.g. visible).
        obstacle_sprites: passed through to spawned enemies.
        enemy_groups:    list of groups each enemy is added to
                         (e.g. [visible_sprites, enemy_sprites]).
        player:          Player reference for enemy AI.
        spawn_interval:  ms between spawn attempts.
        max_alive:       max enemies alive from this spawner at once.
        """
        super().__init__(groups)

        self.obstacle_sprites = obstacle_sprites
        self.enemy_groups = enemy_groups
        self.player = player
        self.spawn_interval = spawn_interval
        self.max_alive = max_alive

        # Build the cave image once
        self.image = _cave_surface()
        self.rect = self.image.get_rect(midbottom=pos)
        self.hitbox = self.rect.copy()

        # Spawn tracking
        self.spawned = []           # refs to living enemies
        self.last_spawn = pygame.time.get_ticks()

        # Ambient glow animation
        self._glow_phase = random.uniform(0, 6.28)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self):
        now = pygame.time.get_ticks()

        # Purge dead references
        self.spawned = [e for e in self.spawned if e.alive()]

        # Spawn check
        if (now - self.last_spawn >= self.spawn_interval
                and len(self.spawned) < self.max_alive):
            self._spawn_enemy()
            self.last_spawn = now

        # Ambient glow re-render (subtle flicker)
        self._glow_phase += 0.03
        self.image = _cave_surface(
            glow_phase=self._glow_phase
        )

    # ------------------------------------------------------------------
    # Spawning
    # ------------------------------------------------------------------

    def _spawn_enemy(self):
        """Create a new Enemy just in front of the cave mouth."""
        # Spawn a little above the cave base so the enemy walks out
        sx = self.rect.centerx + random.randint(-16, 16)
        sy = self.rect.top + 20
        enemy = Enemy(
            (sx, sy),
            self.enemy_groups,
            self.obstacle_sprites,
            self.player,
        )
        self.spawned.append(enemy)
        print(f"Cave spawned enemy ({len(self.spawned)}/{self.max_alive})")


# ======================================================================
# Procedural cave surface
# ======================================================================

def _cave_surface(glow_phase=0.0):
    """Draw a dark rocky cave entrance (96 x 80 pixels)."""
    W, H = 96, 80
    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    cx = W // 2

    # ── Colours ──
    rock_dark   = (55, 45, 40)
    rock_mid    = (75, 62, 55)
    rock_light  = (95, 80, 70)
    rock_edge   = (40, 32, 28)
    cave_black  = (12, 8, 6)
    moss_green  = (42, 65, 35)
    glow_color  = (180, 60, 30)

    # ── Main rock body (rounded arch shape) ──
    # Outer rock mass
    body_pts = [
        (8,  H),          # bottom-left
        (4,  H - 20),
        (6,  35),
        (14, 18),
        (24, 8),
        (cx - 6, 2),
        (cx, 0),
        (cx + 6, 2),
        (W - 24, 8),
        (W - 14, 18),
        (W - 6, 35),
        (W - 4, H - 20),
        (W - 8, H),       # bottom-right
    ]
    pygame.draw.polygon(surf, rock_mid, body_pts)

    # Dark border around arch
    pygame.draw.polygon(surf, rock_edge, body_pts, 3)

    # ── Cave mouth (dark opening) ──
    mouth_pts = [
        (22, H),
        (20, H - 12),
        (22, 40),
        (28, 28),
        (36, 20),
        (cx - 4, 16),
        (cx + 4, 16),
        (W - 36, 20),
        (W - 28, 28),
        (W - 22, 40),
        (W - 20, H - 12),
        (W - 22, H),
    ]
    pygame.draw.polygon(surf, cave_black, mouth_pts)

    # ── Inner glow from cave depths ──
    glow_val = int(20 + 12 * math.sin(glow_phase))
    glow_r = 22
    glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
    for r in range(glow_r, 0, -2):
        a = int(glow_val * (r / glow_r))
        gc = (glow_color[0], glow_color[1], glow_color[2], a)
        pygame.draw.circle(glow_surf, gc, (glow_r, glow_r), r)
    surf.blit(glow_surf, (cx - glow_r, 38))

    # ── Rock detail: layered stones ──
    stone_rects = [
        (6,  60, 18, 12),
        (W - 24, 58, 18, 14),
        (12, 30, 14, 10),
        (W - 26, 32, 14, 10),
        (20, 14, 12, 8),
        (W - 32, 12, 12, 8),
        (cx - 8, 2, 16, 8),
    ]
    for rx, ry, rw, rh in stone_rects:
        pygame.draw.rect(surf, rock_light, (rx, ry, rw, rh), border_radius=3)
        pygame.draw.rect(surf, rock_edge, (rx, ry, rw, rh), 1, border_radius=3)

    # ── Cracks ──
    cracks = [
        ((16, 40), (22, 52)),
        ((W - 16, 38), (W - 22, 50)),
        ((cx - 2, 6), (cx + 3, 14)),
    ]
    for start, end in cracks:
        pygame.draw.line(surf, rock_dark, start, end, 1)

    # ── Moss patches ──
    moss_spots = [(10, 56), (W - 14, 54), (cx - 10, 8), (cx + 8, 6)]
    for mx, my in moss_spots:
        pygame.draw.circle(surf, moss_green, (mx, my), 3)
        pygame.draw.circle(surf, (55, 80, 45), (mx + 1, my - 1), 2)

    # ── Ground rubble at cave base ──
    for i in range(8):
        rx = 18 + i * 8 + random.randint(-2, 2)
        ry = H - 4 + random.randint(-2, 2)
        rs = random.randint(2, 4)
        c = random.choice([rock_dark, rock_mid, rock_edge])
        pygame.draw.circle(surf, c, (rx, ry), rs)

    return surf
