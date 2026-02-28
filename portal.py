import pygame
import math


class Portal(pygame.sprite.Sprite):
    """Glowing exit portal that appears when the level objective is complete."""

    def __init__(self, pos, groups):
        super().__init__(groups)
        self.pos = pygame.math.Vector2(pos)
        self.age = 0.0
        self.image = self._render()
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = pygame.Rect(0, 0, 40, 40)
        self.hitbox.center = self.rect.center

    def _render(self):
        sz = 56
        surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
        c = sz // 2

        pulse = 0.7 + 0.3 * math.sin(self.age * 3.0)

        # Outer glow
        for r in range(26, 0, -2):
            a = int(25 * (r / 26) * pulse)
            pygame.draw.circle(surf, (60, 180, 255, a), (c, c), r)

        # Spinning ring
        ring_r = int(16 * pulse)
        num_dots = 12
        for i in range(num_dots):
            angle = (i / num_dots) * 6.28 + self.age * 2.0
            dx = math.cos(angle) * ring_r
            dy = math.sin(angle) * ring_r
            brightness = int(150 + 80 * math.sin(angle + self.age))
            color = (brightness, min(255, brightness + 60), 255)
            pygame.draw.circle(surf, color, (int(c + dx), int(c + dy)), 2)

        # Center bright core
        pygame.draw.circle(surf, (200, 230, 255), (c, c), 6)
        pygame.draw.circle(surf, (255, 255, 255), (c, c), 3)

        return surf

    def update(self):
        self.age += 0.05
        self.image = self._render()
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.hitbox.center = self.rect.center
