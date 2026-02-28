import pygame
import math
import random
from data import *


class Enemy(pygame.sprite.Sprite):
    """Small demon creature that patrols, notices the player, charges, then rests.

    AI states:
        WANDER  – picks a random direction every few seconds
        NOTICE  – spotted the player, pauses ~2 s with a "!" indicator
        CHARGE  – rushes in a straight line toward where the player was
        REST    – stops for 3 s after the charge, then wanders again
        DYING   – shrink + fade death animation, then removed
    """

    WANDER = 0
    NOTICE = 1
    CHARGE = 2
    REST = 3
    DYING = 4

    # Per-type stats
    ENEMY_TYPE = 'demon'
    MAX_HP = 2
    CONTACT_DAMAGE = 8
    XP_VALUE = 5

    def __init__(self, pos, groups, obstacle_sprites, player):
        super().__init__(groups)

        # Sprite animations (generated procedurally)
        self.animations = _build_animations()
        self.status = 'down_idle'
        self.frame_index = 0
        self.animation_speed = 0.12

        self.image = self.animations[self.status][0]
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(-12, -18)

        # HP
        self.hp = self.MAX_HP

        # Movement
        self.direction = pygame.math.Vector2(0, 0)
        self.speed = 2.5
        self.charge_speed = 7
        self.obstacle_sprites = obstacle_sprites
        self.player = player

        # AI ---------------------------------------------------------------
        self.state = self.WANDER
        self.state_start = pygame.time.get_ticks()

        # Wander
        self.wander_change_ms = 2500
        self.last_wander_change = pygame.time.get_ticks()
        self._pick_wander_direction()

        # Notice
        self.detection_radius = 200
        self.notice_duration = 2000   # ms to "notice" the player

        # Charge
        self.charge_direction = pygame.math.Vector2(0, 0)
        self.charge_duration = 1200   # ms

        # Rest
        self.rest_duration = 3000     # ms

        # Death
        self.death_timer = 0
        self.death_duration = 25      # frames (~0.4 s at 60 fps)

        # Hit flash
        self._hit_flash = 0

        # Notice indicator
        self._excl_font = pygame.font.Font(None, 28)

    # ------------------------------------------------------------------
    # AI helpers
    # ------------------------------------------------------------------

    def _pick_wander_direction(self):
        angle = random.uniform(0, 2 * math.pi)
        self.direction = pygame.math.Vector2(math.cos(angle), math.sin(angle))
        if random.random() < 0.25:
            self.direction = pygame.math.Vector2(0, 0)

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
    # AI update
    # ------------------------------------------------------------------

    def _update_ai(self):
        now = pygame.time.get_ticks()

        if self.state == self.WANDER:
            if now - self.last_wander_change > self.wander_change_ms:
                self._pick_wander_direction()
                self.last_wander_change = now
            if self._dist_to_player() < self.detection_radius:
                self._enter_state(self.NOTICE)
                self.direction = pygame.math.Vector2(0, 0)

        elif self.state == self.NOTICE:
            self.direction = pygame.math.Vector2(0, 0)
            if self._dist_to_player() > self.detection_radius * 1.5:
                self._enter_state(self.WANDER)
                return
            if self._state_elapsed() > self.notice_duration:
                self.charge_direction = self._dir_to_player()
                self._enter_state(self.CHARGE)

        elif self.state == self.CHARGE:
            self.direction = self.charge_direction
            if self._state_elapsed() > self.charge_duration:
                self.direction = pygame.math.Vector2(0, 0)
                self._enter_state(self.REST)

        elif self.state == self.REST:
            self.direction = pygame.math.Vector2(0, 0)
            if self._state_elapsed() > self.rest_duration:
                self._enter_state(self.WANDER)
                self._pick_wander_direction()

        elif self.state == self.DYING:
            self.direction = pygame.math.Vector2(0, 0)
            self.death_timer += 1
            if self.death_timer >= self.death_duration:
                self.kill()

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------

    def take_hit(self, damage=1):
        """Reduce HP; die when HP reaches 0."""
        if self.state == self.DYING:
            return
        self.hp -= damage
        if self.hp <= 0:
            self._enter_state(self.DYING)
            self.death_timer = 0
            self.player.gain_xp(self.XP_VALUE, self.ENEMY_TYPE)
        else:
            # Flash white briefly (handled in _animate)
            self._hit_flash = 6  # frames of flash

    def check_player_collision(self):
        """Bump the player sideways on contact and deal damage."""
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
    # Movement & collision (same pattern as Player)
    # ------------------------------------------------------------------

    def move(self, speed):
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()
        self.hitbox.x += self.direction.x * speed
        self._collision('horizontal')
        self.hitbox.y += self.direction.y * speed
        self._collision('vertical')
        self.rect.center = self.hitbox.center

    def _collision(self, axis):
        for sprite in self.obstacle_sprites:
            if sprite.hitbox.colliderect(self.hitbox):
                if axis == 'horizontal':
                    if self.direction.x > 0:
                        self.hitbox.right = sprite.hitbox.left
                    if self.direction.x < 0:
                        self.hitbox.left = sprite.hitbox.right
                else:
                    if self.direction.y > 0:
                        self.hitbox.bottom = sprite.hitbox.top
                    if self.direction.y < 0:
                        self.hitbox.top = sprite.hitbox.bottom

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------

    def _update_status_string(self):
        if self.direction.length_squared() < 0.01:
            base = self.status.split('_')[0] if '_' in self.status else self.status
            if base not in ('down', 'up', 'left', 'right'):
                base = 'down'
            self.status = base + '_idle'
        else:
            if abs(self.direction.x) > abs(self.direction.y):
                self.status = 'right' if self.direction.x > 0 else 'left'
            else:
                self.status = 'down' if self.direction.y > 0 else 'up'

    def _animate(self):
        self._update_status_string()
        frames = self.animations.get(self.status)
        if not frames:
            return

        speed = 0.25 if self.state == self.CHARGE else self.animation_speed
        self.frame_index += speed
        if self.frame_index >= len(frames):
            self.frame_index = 0

        self.image = frames[int(self.frame_index)]

        # Death effect: shrink + fade
        if self.state == self.DYING:
            t = self.death_timer / max(1, self.death_duration)
            alpha = max(0, int(255 * (1 - t)))
            scale = max(0.15, 1.0 - t * 0.6)
            w = max(1, int(self.image.get_width() * scale))
            h = max(1, int(self.image.get_height() * scale))
            self.image = pygame.transform.scale(self.image.copy(), (w, h))
            self.image.set_alpha(alpha)

        # Hit flash: tint white briefly when damaged but not dead
        if self._hit_flash > 0:
            self._hit_flash -= 1
            flash_surf = self.image.copy()
            flash_surf.fill((255, 255, 255, 120), special_flags=pygame.BLEND_RGBA_ADD)
            self.image = flash_surf

        self.rect = self.image.get_rect(center=self.hitbox.center)

    # ------------------------------------------------------------------
    # Notice "!" indicator (drawn by Level after sprites)
    # ------------------------------------------------------------------

    def draw_notice_indicator(self, surface, offset):
        if self.state != self.NOTICE:
            return
        progress = min(1.0, self._state_elapsed() / self.notice_duration)
        sx = self.rect.centerx - offset.x
        sy = self.rect.top - 10 - offset.y
        bob = int(3 * math.sin(pygame.time.get_ticks() * 0.008))
        intensity = int(155 + 100 * progress)
        color = (intensity, max(0, intensity - 180), 0)
        txt = self._excl_font.render('!', True, color)
        surface.blit(txt, txt.get_rect(center=(int(sx), int(sy) + bob)))

    # ------------------------------------------------------------------
    # Main update (called by sprite group)
    # ------------------------------------------------------------------

    def update(self):
        self._update_ai()
        spd = self.charge_speed if self.state == self.CHARGE else self.speed
        self.move(spd)
        self.check_player_collision()
        self._animate()


# ======================================================================
# Procedural sprite generation
# ======================================================================
# A little crimson demon/imp with horns, glowing eyes, and stubby limbs.
# Colour palette – tweak these to reskin the creature.
_BODY       = (170, 42, 48)
_BODY_LIGHT = (210, 62, 58)
_BODY_DARK  = (120, 30, 35)
_BELLY      = (220, 110, 90)
_HEAD       = (155, 38, 44)
_HEAD_LIGHT = (190, 55, 55)
_HORN       = (110, 24, 28)
_EYE        = (255, 230, 50)
_PUPIL      = (25, 5, 5)
_FOOT       = (100, 28, 32)
_ARM        = (150, 36, 42)
_SNOUT      = (145, 35, 40)
_MOUTH      = (80, 15, 20)


def _build_animations():
    """Return dict of animation lists keyed by status string."""
    anims = {}
    for d in ('down', 'up', 'left', 'right'):
        anims[d] = [_make_frame(d, f) for f in range(4)]
        anims[f'{d}_idle'] = [_make_frame(d, 0)]
    return anims


def _make_frame(direction, frame):
    """Draw one frame of the demon creature sprite."""
    W, H = 48, 52
    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    cx = W // 2
    cy = H // 2 + 4

    # Per-frame offsets for walk cycle
    bob   = (0, -2, 0, 2)[frame]
    sqx   = (0, 1, 0, -1)[frame]
    foot  = (-3, -1, 3, 1)[frame]
    arm_s = (2, 0, -2, 0)[frame]

    # --- Shadow ---
    shadow = pygame.Surface((28, 8), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 50), shadow.get_rect())
    surf.blit(shadow, (cx - 14, cy + 14))

    # --- Feet ---
    fy = cy + 12 + bob
    pygame.draw.ellipse(surf, _FOOT, (cx - 10 + foot, fy, 8, 6))
    pygame.draw.ellipse(surf, _FOOT, (cx + 2 - foot,  fy, 8, 6))

    # --- Body ---
    bw = 26 + sqx * 2
    bh = 22
    bx = cx - bw // 2
    by = cy - 6 + bob
    pygame.draw.ellipse(surf, _BODY, (bx, by, bw, bh))

    # Highlight
    hw, hh = bw - 8, bh - 10
    pygame.draw.ellipse(surf, _BODY_LIGHT, (cx - hw // 2, by + 2, hw, hh))

    # Belly
    bew, beh = 12, 8
    pygame.draw.ellipse(surf, _BELLY,
                        (cx - bew // 2, by + bh - beh - 2, bew, beh))

    # --- Arms ---
    ay = by + 6 + bob
    if direction in ('down', 'up'):
        pygame.draw.ellipse(surf, _ARM, (bx - 4,      ay + arm_s, 7, 9))
        pygame.draw.ellipse(surf, _ARM, (bx + bw - 3, ay - arm_s, 7, 9))
    elif direction == 'left':
        pygame.draw.ellipse(surf, _ARM, (bx - 3, ay + arm_s, 7, 9))
    else:
        pygame.draw.ellipse(surf, _ARM, (bx + bw - 4, ay + arm_s, 7, 9))

    # --- Head ---
    hy = by - 10 + bob
    hw2, hh2 = 22, 18
    pygame.draw.ellipse(surf, _HEAD, (cx - hw2 // 2, hy, hw2, hh2))
    pygame.draw.ellipse(surf, _HEAD_LIGHT, (cx - 7, hy + 2, 14, 10))

    # --- Horns ---
    hby = hy + 3
    pygame.draw.polygon(surf, _HORN, [(cx - 9, hby + 4), (cx - 14, hby - 8), (cx - 6, hby + 1)])
    pygame.draw.polygon(surf, _HORN, [(cx + 9, hby + 4), (cx + 14, hby - 8), (cx + 6, hby + 1)])

    # --- Eyes & face ---
    ey = hy + 8 + bob
    if direction == 'down':
        for ex in (cx - 5, cx + 5):
            pygame.draw.circle(surf, _EYE,   (ex, ey), 3)
            pygame.draw.circle(surf, _PUPIL, (ex, ey + 1), 1)
        pygame.draw.arc(surf, _MOUTH, (cx - 4, ey + 4, 8, 5), 3.14, 6.28, 1)

    elif direction == 'up':
        pygame.draw.ellipse(surf, (140, 34, 38), (cx - 5, hy + 1, 10, 6))

    elif direction == 'left':
        pygame.draw.circle(surf, _EYE,   (cx - 6, ey), 3)
        pygame.draw.circle(surf, _PUPIL, (cx - 7, ey + 1), 1)
        pygame.draw.ellipse(surf, _SNOUT, (cx - 12, ey + 1, 6, 5))

    elif direction == 'right':
        pygame.draw.circle(surf, _EYE,   (cx + 6, ey), 3)
        pygame.draw.circle(surf, _PUPIL, (cx + 7, ey + 1), 1)
        pygame.draw.ellipse(surf, _SNOUT, (cx + 6, ey + 1, 6, 5))

    return surf
