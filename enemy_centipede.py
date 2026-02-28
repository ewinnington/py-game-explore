import pygame
import math
import random
from data import *


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
    CONTACT_DAMAGE = 6
    XP_VALUE = 8  # more XP because it's tougher

    def __init__(self, pos, groups, obstacle_sprites, player, num_segments=5):
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
        self.wave_amp = 2.0

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
        self.detection_radius = 160
        self.slither_change_ms = 3000
        self.last_direction_change = pygame.time.get_ticks()

        # Death
        self.death_timer = 0
        self.death_duration = 25
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
            # Random direction changes
            if now - self.last_direction_change > self.slither_change_ms:
                angle = random.uniform(0, 2 * math.pi)
                self.direction = pygame.math.Vector2(math.cos(angle), math.sin(angle))
                self.last_direction_change = now

            # Detect player
            if self._dist_to_player() < self.detection_radius:
                self._enter_state(self.PURSUE)

        elif self.state == self.PURSUE:
            # Steer toward player
            to_player = self._dir_to_player()
            self.direction += (to_player - self.direction) * 0.05
            if self.direction.length() > 0:
                self.direction = self.direction.normalize()

            # Lose interest if player is far
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
            # Rebuild image with fewer segments
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

        # Sinusoidal wave applied perpendicular to direction
        self.wave_phase += self.wave_freq
        perp = pygame.math.Vector2(-self.direction.y, self.direction.x)
        wave_offset = perp * math.sin(self.wave_phase) * self.wave_amp

        self.pos += self.direction * speed + wave_offset

        # Update trail
        self.trail.insert(0, pygame.math.Vector2(self.pos))
        max_trail = self.num_segments * 4
        while len(self.trail) > max_trail:
            self.trail.pop()

        # Collision with obstacles
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))
        for sprite in self.obstacle_sprites:
            if sprite.hitbox.colliderect(self.hitbox):
                # Bounce off
                self.direction = -self.direction
                self.pos += self.direction * speed * 2
                self.hitbox.center = (int(self.pos.x), int(self.pos.y))
                break

        # Safety clamp to world boundaries
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

    def _rebuild_image(self):
        """Rebuild the centipede surface based on current segment count."""
        seg_size = 10
        total_w = self.num_segments * seg_size + 12
        total_h = seg_size + 12
        self.image = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
        self._draw_body(self.image, total_w, total_h)

    def _draw_body(self, surf, w, h):
        """Draw the centipede body onto the given surface."""
        cx = w // 2
        cy = h // 2
        seg_size = 10
        n = self.num_segments

        # Draw segments from tail to head
        for i in range(n):
            t = i / max(1, n - 1)
            sx = cx - (n * seg_size // 2) + i * seg_size + seg_size // 2

            # Color gradient: darker tail, brighter head
            r = int(80 + 120 * t)
            g = int(140 + 60 * t)
            b = int(40 + 30 * t)

            # Body segment
            seg_r = int(seg_size * 0.45 * (0.7 + 0.3 * t))
            pygame.draw.circle(surf, (r, g, b), (sx, cy), seg_r)
            # Highlight
            pygame.draw.circle(surf, (min(255, r + 40), min(255, g + 30), min(255, b + 20)),
                               (sx, cy - 1), max(1, seg_r - 2))

            # Legs (tiny lines)
            leg_len = 4
            pygame.draw.line(surf, (60, 90, 30),
                             (sx - 2, cy + seg_r), (sx - 4, cy + seg_r + leg_len), 1)
            pygame.draw.line(surf, (60, 90, 30),
                             (sx + 2, cy + seg_r), (sx + 4, cy + seg_r + leg_len), 1)

        # Head details (on last segment)
        if n > 0:
            hx = cx - (n * seg_size // 2) + (n - 1) * seg_size + seg_size // 2
            # Antennae
            pygame.draw.line(surf, (100, 160, 60), (hx - 2, cy - 4), (hx - 5, cy - 9), 1)
            pygame.draw.line(surf, (100, 160, 60), (hx + 2, cy - 4), (hx + 5, cy - 9), 1)
            # Eyes
            pygame.draw.circle(surf, (255, 200, 50), (hx - 2, cy - 1), 2)
            pygame.draw.circle(surf, (255, 200, 50), (hx + 2, cy - 1), 2)
            pygame.draw.circle(surf, (20, 10, 5), (hx - 2, cy - 1), 1)
            pygame.draw.circle(surf, (20, 10, 5), (hx + 2, cy - 1), 1)

    def _animate(self):
        self.frame_index += self.animation_speed

        # Rebuild from trail to show slithering motion
        seg_size = 10
        n = self.num_segments
        total_w = max(n * seg_size + 12, 24)
        total_h = seg_size + 16
        surf = pygame.Surface((total_w, total_h), pygame.SRCALPHA)

        cx = total_w // 2
        cy = total_h // 2

        # Draw segments using trail positions for waviness
        for i in range(n):
            t = i / max(1, n - 1)
            # Use trail for wavy body positioning
            trail_idx = min(i * 3, len(self.trail) - 1)
            trail_pos = self.trail[trail_idx]
            # Relative offset from current pos
            rel_x = trail_pos.x - self.pos.x
            rel_y = trail_pos.y - self.pos.y
            sx = cx + int(rel_x)
            sy = cy + int(rel_y)

            # Color
            r = int(80 + 120 * t)
            g = int(140 + 60 * t)
            b = int(40 + 30 * t)
            seg_r = int(seg_size * 0.45 * (0.7 + 0.3 * t))

            pygame.draw.circle(surf, (r, g, b), (sx, sy), seg_r)
            pygame.draw.circle(surf, (min(255, r + 40), min(255, g + 30), min(255, b + 20)),
                               (sx, sy - 1), max(1, seg_r - 2))

            # Legs
            leg_off = int(2 * math.sin(self.frame_index + i * 0.5))
            pygame.draw.line(surf, (60, 90, 30),
                             (sx - 2, sy + seg_r), (sx - 4 + leg_off, sy + seg_r + 4), 1)
            pygame.draw.line(surf, (60, 90, 30),
                             (sx + 2, sy + seg_r), (sx + 4 - leg_off, sy + seg_r + 4), 1)

        # Head (first in trail = current position)
        if n > 0:
            hx, hy = cx, cy
            pygame.draw.line(surf, (100, 160, 60), (hx - 2, hy - 4), (hx - 5, hy - 9), 1)
            pygame.draw.line(surf, (100, 160, 60), (hx + 2, hy - 4), (hx + 5, hy - 9), 1)
            pygame.draw.circle(surf, (255, 200, 50), (hx - 2, hy - 1), 2)
            pygame.draw.circle(surf, (255, 200, 50), (hx + 2, hy - 1), 2)
            pygame.draw.circle(surf, (20, 10, 5), (hx - 2, hy - 1), 1)
            pygame.draw.circle(surf, (20, 10, 5), (hx + 2, hy - 1), 1)

        # Death effect
        if self.state == self.DYING:
            t = self.death_timer / max(1, self.death_duration)
            alpha = max(0, int(255 * (1 - t)))
            scale = max(0.2, 1.0 - t * 0.5)
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
