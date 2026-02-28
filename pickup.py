import pygame
import math
import random


class Pickup(pygame.sprite.Sprite):
    """Base class for world pickups with floating/glowing animation."""

    def __init__(self, pos, groups, pickup_type, icon, color_tint):
        super().__init__(groups)
        self.pickup_type = pickup_type
        self.base_icon = icon
        self.color_tint = color_tint
        self.pos = pygame.math.Vector2(pos)
        self.age = random.uniform(0, 6.28)  # random phase offset

        self.image = self._render()
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = pygame.Rect(0, 0, 28, 28)
        self.hitbox.center = self.rect.center
        self.collected = False

    def _render(self):
        sz = 40
        surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
        c = sz // 2

        # Glow
        glow_pulse = 0.7 + 0.3 * math.sin(self.age * 2.5)
        glow_r = int(18 * glow_pulse)
        for r in range(glow_r, 0, -2):
            a = int(30 * (r / glow_r) * glow_pulse)
            gc = (self.color_tint[0], self.color_tint[1], self.color_tint[2], a)
            pygame.draw.circle(surf, gc, (c, c), r)

        # Icon
        if self.base_icon:
            icon_size = 24
            try:
                scaled = pygame.transform.smoothscale(self.base_icon, (icon_size, icon_size))
            except Exception:
                scaled = pygame.transform.scale(self.base_icon, (icon_size, icon_size))
            surf.blit(scaled, scaled.get_rect(center=(c, c)))

        return surf

    def update(self):
        self.age += 0.05
        # Floating bob
        bob = math.sin(self.age * 2.0) * 3
        self.image = self._render()
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y + bob)))
        self.hitbox.center = self.rect.center

    def collect(self, player):
        """Override in subclasses for specific pickup behavior."""
        self.collected = True
        self.kill()


class RunePickup(Pickup):
    """A rune that grants a weapon or spell when collected."""

    # Color tints per rune type
    RUNE_COLORS = {
        'spear':        (200, 180, 100),
        'fire_cone':    (255, 120, 30),
        'ice_ball':     (80, 160, 255),
        'shadow_blade': (150, 60, 200),
    }

    def __init__(self, pos, groups, rune_type, icon=None):
        color = self.RUNE_COLORS.get(rune_type, (200, 200, 200))
        if icon is None:
            icon = self._make_rune_icon(rune_type, color)
        super().__init__(pos, groups, f'rune_{rune_type}', icon, color)
        self.rune_type = rune_type

    def collect(self, player):
        player.collect_rune(self.rune_type)
        self.collected = True
        self.kill()

    @staticmethod
    def _make_rune_icon(rune_type, color):
        """Procedural rune stone icon."""
        sz = 28
        surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
        c = sz // 2

        # Stone shape
        pts = [
            (c, 2),
            (sz - 4, c - 4),
            (sz - 2, c + 4),
            (c + 2, sz - 2),
            (c - 2, sz - 2),
            (2, c + 4),
            (4, c - 4),
        ]
        # Dark stone base
        pygame.draw.polygon(surf, (60, 55, 50), pts)
        pygame.draw.polygon(surf, (90, 80, 70), pts, 2)

        # Glowing rune symbol
        inner_pts = [
            (c, 6),
            (c + 6, c),
            (c, sz - 6),
            (c - 6, c),
        ]
        pygame.draw.polygon(surf, color, inner_pts, 2)
        # Center dot
        pygame.draw.circle(surf, color, (c, c), 3)

        # First letter
        font = pygame.font.Font(None, 16)
        letter = rune_type[0].upper()
        if rune_type == 'fire_cone':
            letter = 'F'
        elif rune_type == 'ice_ball':
            letter = 'I'
        elif rune_type == 'shadow_blade':
            letter = 'S'
        txt = font.render(letter, True, (255, 255, 255))
        surf.blit(txt, txt.get_rect(center=(c, c)))

        return surf


class HealthPickup(Pickup):
    """A heart/potion that restores player HP."""

    def __init__(self, pos, groups, heal_amount=20):
        icon = self._make_heart_icon()
        super().__init__(pos, groups, 'health', icon, (255, 60, 60))
        self.heal_amount = heal_amount

    def collect(self, player):
        if player.hp < player.max_hp:
            player.heal(self.heal_amount)
            self.collected = True
            self.kill()
            return True
        return False  # don't collect if full HP

    @staticmethod
    def _make_heart_icon():
        sz = 24
        surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
        c = sz // 2
        # Heart shape using two circles + triangle
        pygame.draw.circle(surf, (220, 40, 50), (c - 4, c - 3), 5)
        pygame.draw.circle(surf, (220, 40, 50), (c + 4, c - 3), 5)
        pygame.draw.polygon(surf, (220, 40, 50), [
            (c - 9, c - 1), (c, sz - 4), (c + 9, c - 1)
        ])
        # Highlight
        pygame.draw.circle(surf, (255, 120, 130), (c - 3, c - 5), 2)
        return surf
