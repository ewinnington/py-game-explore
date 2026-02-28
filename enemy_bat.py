import pygame
import math
import random
from data import *


class Bat(pygame.sprite.Sprite):
    """Fast-moving bat that swoops erratically at the player.

    AI states:
        IDLE    – flutters in place
        SWOOP   – dives toward the player in an arc
        RETREAT – flies away after a swoop, then returns to IDLE
        DYING   – shrink + fade death animation
    """

    IDLE = 0
    SWOOP = 1
    RETREAT = 2
    DYING = 3

    # Stats
    ENEMY_TYPE = 'bat'
    MAX_HP = 1
    CONTACT_DAMAGE = 5
    XP_VALUE = 3

    def __init__(self, pos, groups, obstacle_sprites, player):
        super().__init__(groups)

        self.animations = _build_bat_animations()
        self.status = 'down'
        self.frame_index = 0
        self.animation_speed = 0.2

        self.image = self.animations[self.status][0]
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(-8, -10)

        self.hp = self.MAX_HP
        self.direction = pygame.math.Vector2(0, 0)
        self.speed = 3.5
        self.swoop_speed = 9
        self.obstacle_sprites = obstacle_sprites
        self.player = player

        # AI
        self.state = self.IDLE
        self.state_start = pygame.time.get_ticks()

        # Idle flutter
        self._flutter_phase = random.uniform(0, 6.28)
        self._flutter_center = pygame.math.Vector2(pos)

        # Swoop
        self.swoop_duration = 800    # ms
        self.swoop_target = pygame.math.Vector2(0, 0)
        self.detection_radius = 180
        self._idle_duration = random.randint(1500, 3000)

        # Retreat
        self.retreat_duration = 600

        # Death
        self.death_timer = 0
        self.death_duration = 20
        self._hit_flash = 0

    def _enter_state(self, state):
        self.state = state
        self.state_start = pygame.time.get_ticks()

    def _state_elapsed(self):
        return pygame.time.get_ticks() - self.state_start

    def _dist_to_player(self):
        return pygame.math.Vector2(
            self.rect.centerx - self.player.rect.centerx,
            self.rect.centery - self.player.rect.centery,
        ).length()

    def _dir_to_player(self):
        d = pygame.math.Vector2(
            self.player.rect.centerx - self.rect.centerx,
            self.player.rect.centery - self.rect.centery,
        )
        return d.normalize() if d.length() > 0 else pygame.math.Vector2(1, 0)

    # ------------------------------------------------------------------
    # AI
    # ------------------------------------------------------------------

    def _update_ai(self):
        if self.state == self.IDLE:
            # Flutter in place with slight oscillation
            self._flutter_phase += 0.05
            ox = math.sin(self._flutter_phase * 1.3) * 0.8
            oy = math.cos(self._flutter_phase) * 0.6
            self.direction = pygame.math.Vector2(ox, oy)

            # Detect player and swoop
            if self._dist_to_player() < self.detection_radius:
                if self._state_elapsed() > self._idle_duration:
                    self.swoop_target = self._dir_to_player()
                    self._enter_state(self.SWOOP)

        elif self.state == self.SWOOP:
            # Add slight sine wave to swoop for erratic feel
            t = self._state_elapsed() / self.swoop_duration
            wave = math.sin(t * 12) * 0.3
            perp = pygame.math.Vector2(-self.swoop_target.y, self.swoop_target.x)
            self.direction = self.swoop_target + perp * wave
            if self._state_elapsed() > self.swoop_duration:
                # Retreat in opposite direction
                self.direction = -self.swoop_target
                self._enter_state(self.RETREAT)
                self._flutter_center = pygame.math.Vector2(self.rect.center)

        elif self.state == self.RETREAT:
            # Fly away
            if self._state_elapsed() > self.retreat_duration:
                self._enter_state(self.IDLE)
                self._idle_duration = random.randint(1000, 2500)
                self._flutter_center = pygame.math.Vector2(self.rect.center)

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
        if self.hp <= 0:
            self._enter_state(self.DYING)
            self.death_timer = 0
            self.player.gain_xp(self.XP_VALUE, self.ENEMY_TYPE)
        else:
            self._hit_flash = 6

    def check_player_collision(self):
        if self.state == self.DYING:
            return
        if not self.hitbox.colliderect(self.player.hitbox):
            return
        dx = self.player.rect.centerx - self.rect.centerx
        dy = self.player.rect.centery - self.rect.centery
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
        # Bats fly over obstacles (no collision with obstacles)
        self.hitbox.x += self.direction.x * speed
        self.hitbox.y += self.direction.y * speed

        # Clamp to world boundaries (1 tile inset)
        margin = TILESIZE
        self.hitbox.clamp_ip(pygame.Rect(margin, margin, 20 * TILESIZE - 2 * margin,
                                          19 * TILESIZE - 2 * margin))
        # Reverse direction if hitting boundary
        if self.hitbox.left <= margin or self.hitbox.right >= 20 * TILESIZE - margin:
            self.direction.x = -self.direction.x
        if self.hitbox.top <= margin or self.hitbox.bottom >= 19 * TILESIZE - margin:
            self.direction.y = -self.direction.y

        self.rect.center = self.hitbox.center

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------

    def _update_status(self):
        if self.direction.length_squared() < 0.01:
            self.status = 'down'
        elif abs(self.direction.x) > abs(self.direction.y):
            self.status = 'right' if self.direction.x > 0 else 'left'
        else:
            self.status = 'down' if self.direction.y > 0 else 'up'

    def _animate(self):
        self._update_status()
        frames = self.animations.get(self.status, self.animations['down'])
        self.frame_index += self.animation_speed
        if self.frame_index >= len(frames):
            self.frame_index = 0
        self.image = frames[int(self.frame_index)]

        if self.state == self.DYING:
            t = self.death_timer / max(1, self.death_duration)
            alpha = max(0, int(255 * (1 - t)))
            scale = max(0.2, 1.0 - t * 0.5)
            w = max(1, int(self.image.get_width() * scale))
            h = max(1, int(self.image.get_height() * scale))
            self.image = pygame.transform.scale(self.image.copy(), (w, h))
            self.image.set_alpha(alpha)

        if self._hit_flash > 0:
            self._hit_flash -= 1
            flash_surf = self.image.copy()
            flash_surf.fill((255, 255, 255, 120), special_flags=pygame.BLEND_RGBA_ADD)
            self.image = flash_surf

        self.rect = self.image.get_rect(center=self.hitbox.center)

    def draw_notice_indicator(self, surface, offset):
        pass  # Bats don't show "!" indicators

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self):
        self._update_ai()
        spd = self.swoop_speed if self.state == self.SWOOP else self.speed
        self.move(spd)
        self.check_player_collision()
        self._animate()


# ======================================================================
# Procedural bat sprite
# ======================================================================

_BAT_BODY = (60, 50, 70)
_BAT_WING = (45, 35, 55)
_BAT_WING_INNER = (70, 55, 80)
_BAT_EYE = (255, 80, 80)


def _build_bat_animations():
    anims = {}
    for d in ('down', 'up', 'left', 'right'):
        anims[d] = [_make_bat_frame(d, f) for f in range(4)]
    return anims


def _make_bat_frame(direction, frame):
    W, H = 36, 28
    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    cx, cy = W // 2, H // 2

    # Wing flap cycle
    wing_angles = [15, -5, -20, -5]
    flap = wing_angles[frame]

    # Shadow
    shadow = pygame.Surface((20, 6), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 30), shadow.get_rect())
    surf.blit(shadow, (cx - 10, H - 6))

    # Body (small oval)
    pygame.draw.ellipse(surf, _BAT_BODY, (cx - 6, cy - 4, 12, 10))

    # Wings
    wing_y = cy - 2
    # Left wing
    lw_pts = [
        (cx - 5, wing_y),
        (cx - 16, wing_y - 8 + flap),
        (cx - 12, wing_y + 2 + flap // 2),
        (cx - 5, wing_y + 3),
    ]
    pygame.draw.polygon(surf, _BAT_WING, lw_pts)
    # Wing membrane lines
    pygame.draw.line(surf, _BAT_WING_INNER,
                     (cx - 5, wing_y), (cx - 14, wing_y - 6 + flap), 1)
    pygame.draw.line(surf, _BAT_WING_INNER,
                     (cx - 5, wing_y + 1), (cx - 13, wing_y + flap // 2), 1)

    # Right wing
    rw_pts = [
        (cx + 5, wing_y),
        (cx + 16, wing_y - 8 + flap),
        (cx + 12, wing_y + 2 + flap // 2),
        (cx + 5, wing_y + 3),
    ]
    pygame.draw.polygon(surf, _BAT_WING, rw_pts)
    pygame.draw.line(surf, _BAT_WING_INNER,
                     (cx + 5, wing_y), (cx + 14, wing_y - 6 + flap), 1)
    pygame.draw.line(surf, _BAT_WING_INNER,
                     (cx + 5, wing_y + 1), (cx + 13, wing_y + flap // 2), 1)

    # Ears
    pygame.draw.polygon(surf, _BAT_BODY,
                        [(cx - 4, cy - 4), (cx - 6, cy - 10), (cx - 2, cy - 5)])
    pygame.draw.polygon(surf, _BAT_BODY,
                        [(cx + 4, cy - 4), (cx + 6, cy - 10), (cx + 2, cy - 5)])

    # Eyes
    if direction != 'up':
        ey = cy - 1
        if direction == 'left':
            pygame.draw.circle(surf, _BAT_EYE, (cx - 4, ey), 2)
        elif direction == 'right':
            pygame.draw.circle(surf, _BAT_EYE, (cx + 4, ey), 2)
        else:
            pygame.draw.circle(surf, _BAT_EYE, (cx - 3, ey), 2)
            pygame.draw.circle(surf, _BAT_EYE, (cx + 3, ey), 2)

    return surf
