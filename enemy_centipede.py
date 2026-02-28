import pygame
import math
import random
from data import *


# ── Centipede colour palette ──────────────────────────────────────
_SEG_TAIL    = (90, 50, 30)       # Dark brown-red tail
_SEG_HEAD    = (180, 50, 40)      # Crimson head
_SEG_HI_ADD = (45, 35, 25)       # Highlight offset
_BELLY       = (60, 100, 35)      # Poisonous green underbelly
_LEG         = (50, 80, 25)       # Dark green legs
_ANTENNA     = (120, 180, 70)     # Bright green antennae
_EYE         = (255, 220, 50)     # Golden eyes
_PUPIL       = (20, 10, 5)        # Near-black pupils
_MANDIBLE    = (140, 40, 30)      # Dark red pincers


class Centipede(pygame.sprite.Sprite):
    """Multi-segment centipede that gets shorter with each hit.

    The centipede slithers in a sinusoidal path. Each hit removes one
    segment. When the last segment is destroyed, the centipede dies.

    AI states:
        SLITHER – moves in a wavy pattern
        PURSUE  – noticed the player, slithers toward them faster
        DYING   – death animation
    """

    SLITHER = 0
    PURSUE = 1
    DYING = 2

    ENEMY_TYPE = 'centipede'
    CONTACT_DAMAGE = 8
    XP_VALUE = 12

    SEG_SIZE = 16  # pixels per segment

    def __init__(self, pos, groups, obstacle_sprites, player, num_segments=7):
        super().__init__(groups)

        self.num_segments = num_segments
        self.max_segments = num_segments
        self.hp = num_segments  # each segment = 1 HP

        self.obstacle_sprites = obstacle_sprites
        self.player = player

        # Movement
        self.direction = pygame.math.Vector2(random.choice([-1, 1]), 0)
        self.speed = 2.0
        self.pursue_speed = 3.5
        self.wave_phase = random.uniform(0, 6.28)
        self.wave_freq = 0.06
        self.wave_amp = 2.5

        # Segment trail (positions for drawing body segments)
        self.trail = [pygame.math.Vector2(pos) for _ in range(num_segments * 4)]
        self.pos = pygame.math.Vector2(pos)

        # Build image
        self._rebuild_image()
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.inflate(-4, -8)

        # AI
        self.state = self.SLITHER
        self.state_start = pygame.time.get_ticks()
        self.detection_radius = 180
        self.slither_change_ms = 3000
        self.last_direction_change = pygame.time.get_ticks()

        # Death
        self.death_timer = 0
        self.death_duration = 30
        self._hit_flash = 0

        # Animation
        self.frame_index = 0
        self.animation_speed = 0.15

    def _enter_state(self, state):
        self.state = state
        self.state_start = pygame.time.get_ticks()

    def _state_elapsed(self):
        return pygame.time.get_ticks() - self.state_start

    def _dist_to_player(self):
        return pygame.math.Vector2(
            self.pos.x - self.player.rect.centerx,
            self.pos.y - self.player.rect.centery,
        ).length()

    def _dir_to_player(self):
        d = pygame.math.Vector2(
            self.player.rect.centerx - self.pos.x,
            self.player.rect.centery - self.pos.y,
        )
        return d.normalize() if d.length() > 0 else pygame.math.Vector2(1, 0)

    # ------------------------------------------------------------------
    # AI
    # ------------------------------------------------------------------

    def _update_ai(self):
        now = pygame.time.get_ticks()

        if self.state == self.SLITHER:
            if now - self.last_direction_change > self.slither_change_ms:
                angle = random.uniform(0, 2 * math.pi)
                self.direction = pygame.math.Vector2(math.cos(angle), math.sin(angle))
                self.last_direction_change = now
            if self._dist_to_player() < self.detection_radius:
                self._enter_state(self.PURSUE)

        elif self.state == self.PURSUE:
            to_player = self._dir_to_player()
            self.direction += (to_player - self.direction) * 0.05
            if self.direction.length() > 0:
                self.direction = self.direction.normalize()
            if self._dist_to_player() > self.detection_radius * 2:
                self._enter_state(self.SLITHER)

        elif self.state == self.DYING:
            self.direction = pygame.math.Vector2(0, 0)
            self.death_timer += 1
            if self.death_timer >= self.death_duration:
                self.kill()

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------

    def take_hit(self, damage=1):
        if self.state == self.DYING:
            return
        self.hp -= damage
        self.num_segments = max(1, self.hp)
        self._hit_flash = 8

        if self.hp <= 0:
            self._enter_state(self.DYING)
            self.death_timer = 0
            self.player.gain_xp(self.XP_VALUE, self.ENEMY_TYPE)
        else:
            self._rebuild_image()

    def check_player_collision(self):
        if self.state == self.DYING:
            return
        if not self.hitbox.colliderect(self.player.hitbox):
            return
        dx = self.player.rect.centerx - self.pos.x
        dy = self.player.rect.centery - self.pos.y
        bump = pygame.math.Vector2(dx, dy)
        bump = bump.normalize() if bump.length() > 0 else pygame.math.Vector2(1, 0)
        self.player.take_damage(self.CONTACT_DAMAGE)
        self.player.apply_knockback(bump)

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    def move(self, speed):
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()

        self.wave_phase += self.wave_freq
        perp = pygame.math.Vector2(-self.direction.y, self.direction.x)
        wave_offset = perp * math.sin(self.wave_phase) * self.wave_amp

        self.pos += self.direction * speed + wave_offset

        self.trail.insert(0, pygame.math.Vector2(self.pos))
        max_trail = self.num_segments * 4
        while len(self.trail) > max_trail:
            self.trail.pop()

        self.hitbox.center = (int(self.pos.x), int(self.pos.y))
        for sprite in self.obstacle_sprites:
            if sprite.hitbox.colliderect(self.hitbox):
                self.direction = -self.direction
                self.pos += self.direction * speed * 2
                self.hitbox.center = (int(self.pos.x), int(self.pos.y))
                break

        margin = TILESIZE
        world_rect = pygame.Rect(margin, margin, 20 * TILESIZE - 2 * margin,
                                  19 * TILESIZE - 2 * margin)
        self.hitbox.clamp_ip(world_rect)
        self.pos.x = self.hitbox.centerx
        self.pos.y = self.hitbox.centery
        self.rect.center = self.hitbox.center

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    @staticmethod
    def _seg_color(t):
        """Return (body, highlight) colours for segment at position t (0=tail, 1=head)."""
        r = int(_SEG_TAIL[0] + (_SEG_HEAD[0] - _SEG_TAIL[0]) * t)
        g = int(_SEG_TAIL[1] + (_SEG_HEAD[1] - _SEG_TAIL[1]) * t)
        b = int(_SEG_TAIL[2] + (_SEG_HEAD[2] - _SEG_TAIL[2]) * t)
        hr = min(255, r + _SEG_HI_ADD[0])
        hg = min(255, g + _SEG_HI_ADD[1])
        hb = min(255, b + _SEG_HI_ADD[2])
        return (r, g, b), (hr, hg, hb)

    def _rebuild_image(self):
        """Rebuild the centipede surface based on current segment count."""
        S = self.SEG_SIZE
        total_w = self.num_segments * S + 20
        total_h = S + 20
        self.image = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
        self._draw_body_static(self.image, total_w, total_h)

    def _draw_body_static(self, surf, w, h):
        """Draw a static centipede body (used for initial image)."""
        cx, cy = w // 2, h // 2
        S = self.SEG_SIZE
        n = self.num_segments

        for i in range(n):
            t = i / max(1, n - 1)
            sx = cx - (n * S // 2) + i * S + S // 2
            body_c, hi_c = self._seg_color(t)
            seg_r = int(S * 0.45 * (0.7 + 0.3 * t))

            # Shadow
            pygame.draw.ellipse(surf, (0, 0, 0, 25),
                                (sx - seg_r, cy + seg_r - 2, seg_r * 2, 6))
            # Body
            pygame.draw.circle(surf, body_c, (sx, cy), seg_r)
            pygame.draw.circle(surf, hi_c, (sx, cy - 2), max(1, seg_r - 3))
            # Belly stripe
            pygame.draw.ellipse(surf, _BELLY,
                                (sx - seg_r // 2, cy + 1, seg_r, seg_r // 2))
            # Legs
            leg_len = 7
            pygame.draw.line(surf, _LEG,
                             (sx - 3, cy + seg_r), (sx - 6, cy + seg_r + leg_len), 2)
            pygame.draw.line(surf, _LEG,
                             (sx + 3, cy + seg_r), (sx + 6, cy + seg_r + leg_len), 2)

        # Head details
        if n > 0:
            hx = cx - (n * S // 2) + (n - 1) * S + S // 2
            self._draw_head(surf, hx, cy)

    def _draw_head(self, surf, hx, hy):
        """Draw head details: antennae, eyes, mandibles."""
        # Antennae (longer, curving)
        pygame.draw.line(surf, _ANTENNA, (hx - 3, hy - 6), (hx - 8, hy - 14), 2)
        pygame.draw.line(surf, _ANTENNA, (hx + 3, hy - 6), (hx + 8, hy - 14), 2)
        # Antenna tips
        pygame.draw.circle(surf, _ANTENNA, (hx - 8, hy - 14), 2)
        pygame.draw.circle(surf, _ANTENNA, (hx + 8, hy - 14), 2)

        # Eyes (larger)
        pygame.draw.circle(surf, _EYE, (hx - 4, hy - 2), 3)
        pygame.draw.circle(surf, _EYE, (hx + 4, hy - 2), 3)
        pygame.draw.circle(surf, _PUPIL, (hx - 4, hy - 1), 1)
        pygame.draw.circle(surf, _PUPIL, (hx + 4, hy - 1), 1)

        # Mandibles / pincers
        pygame.draw.line(surf, _MANDIBLE, (hx - 3, hy + 3), (hx - 7, hy + 10), 2)
        pygame.draw.line(surf, _MANDIBLE, (hx - 7, hy + 10), (hx - 4, hy + 8), 2)
        pygame.draw.line(surf, _MANDIBLE, (hx + 3, hy + 3), (hx + 7, hy + 10), 2)
        pygame.draw.line(surf, _MANDIBLE, (hx + 7, hy + 10), (hx + 4, hy + 8), 2)

    def _animate(self):
        self.frame_index += self.animation_speed

        S = self.SEG_SIZE
        n = self.num_segments
        total_w = max(n * S + 20, 36)
        total_h = S + 24
        surf = pygame.Surface((total_w, total_h), pygame.SRCALPHA)

        cx = total_w // 2
        cy = total_h // 2

        # Draw segments using trail positions for waviness
        for i in range(n):
            t = i / max(1, n - 1)
            trail_idx = min(i * 3, len(self.trail) - 1)
            trail_pos = self.trail[trail_idx]
            rel_x = trail_pos.x - self.pos.x
            rel_y = trail_pos.y - self.pos.y
            sx = cx + int(rel_x)
            sy = cy + int(rel_y)

            body_c, hi_c = self._seg_color(t)
            seg_r = int(S * 0.45 * (0.7 + 0.3 * t))

            # Shadow
            pygame.draw.ellipse(surf, (0, 0, 0, 25),
                                (sx - seg_r, sy + seg_r - 2, seg_r * 2, 6))
            # Body
            pygame.draw.circle(surf, body_c, (sx, sy), seg_r)
            pygame.draw.circle(surf, hi_c, (sx, sy - 2), max(1, seg_r - 3))
            # Belly stripe
            pygame.draw.ellipse(surf, _BELLY,
                                (sx - seg_r // 2, sy + 1, seg_r, seg_r // 2))

            # Animated legs
            leg_off = int(3 * math.sin(self.frame_index + i * 0.5))
            pygame.draw.line(surf, _LEG,
                             (sx - 3, sy + seg_r), (sx - 6 + leg_off, sy + seg_r + 7), 2)
            pygame.draw.line(surf, _LEG,
                             (sx + 3, sy + seg_r), (sx + 6 - leg_off, sy + seg_r + 7), 2)

        # Head (first in trail = current position)
        if n > 0:
            self._draw_head(surf, cx, cy)

        # Death effect
        if self.state == self.DYING:
            dt = self.death_timer / max(1, self.death_duration)
            alpha = max(0, int(255 * (1 - dt)))
            scale = max(0.2, 1.0 - dt * 0.5)
            w = max(1, int(surf.get_width() * scale))
            h = max(1, int(surf.get_height() * scale))
            surf = pygame.transform.scale(surf, (w, h))
            surf.set_alpha(alpha)

        # Hit flash
        if self._hit_flash > 0:
            self._hit_flash -= 1
            flash = surf.copy()
            flash.fill((255, 255, 255, 120), special_flags=pygame.BLEND_RGBA_ADD)
            surf = flash

        self.image = surf
        self.rect = self.image.get_rect(center=self.hitbox.center)

    def draw_notice_indicator(self, surface, offset):
        pass  # Centipedes don't show notice indicators

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self):
        self._update_ai()
        spd = self.pursue_speed if self.state == self.PURSUE else self.speed
        self.move(spd)
        self.check_player_collision()
        self._animate()
