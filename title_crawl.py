"""Title screen story crawl with decorative bat and demon sprites."""

import pygame
import math
import random
from data import WIDTH, HEIGHT
from enemy_bat import _make_bat_frame
from enemy import _make_frame as _make_demon_frame


# ------------------------------------------------------------------
# Story text
# ------------------------------------------------------------------

_STORY_TEXT = (
    "The colliding worlds of Veyrun and Ingnal have released "
    "the monsters of Ingnal upon the world."
    "\n\n"
    "It is up to brave adventurers to find and close the rifts."
    "\n\n"
    "Magic has been released upon the world in the form of runes "
    "that provide spells."
    "\n\n"
    "Will you be up to the challenge?"
)


# ------------------------------------------------------------------
# Decorative bat
# ------------------------------------------------------------------

class DecoBat:
    """Lightweight decorative bat that flies erratically on the title screen."""

    def __init__(self):
        # Build scaled-down frames for all 4 directions
        self._frames = {}
        for d in ('down', 'up', 'left', 'right'):
            self._frames[d] = [
                pygame.transform.scale(_make_bat_frame(d, f), (24, 18))
                for f in range(4)
            ]
        self.x = random.uniform(60, WIDTH - 60)
        self.y = random.uniform(40, HEIGHT - 120)
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(-1.0, 1.0)
        self.frame_index = random.uniform(0, 4)
        self._flutter_phase = random.uniform(0, 6.28)

    def update(self):
        self._flutter_phase += 0.08
        self.x += self.vx + math.sin(self._flutter_phase * 1.7) * 0.8
        self.y += self.vy + math.cos(self._flutter_phase) * 0.6

        # Random direction change
        if random.random() < 0.008:
            self.vx = random.uniform(-2.0, 2.0)
            self.vy = random.uniform(-1.5, 1.5)

        # Bounce off screen edges
        if self.x < 30 or self.x > WIDTH - 30:
            self.vx = -self.vx
            self.x = max(30, min(WIDTH - 30, self.x))
        if self.y < 30 or self.y > HEIGHT - 100:
            self.vy = -self.vy
            self.y = max(30, min(HEIGHT - 100, self.y))

        self.frame_index += 0.2
        if self.frame_index >= 4:
            self.frame_index = 0

    def draw(self, surface):
        # Determine facing direction from velocity
        if abs(self.vx) > abs(self.vy):
            direction = 'right' if self.vx > 0 else 'left'
        else:
            direction = 'down' if self.vy > 0 else 'up'

        frame = self._frames[direction][int(self.frame_index)]
        frame.set_alpha(170)
        surface.blit(frame, (int(self.x) - 12, int(self.y) - 9))


# ------------------------------------------------------------------
# Decorative demon
# ------------------------------------------------------------------

class DecoDemon:
    """Lightweight decorative demon that walks/charges across the bottom."""

    WALK = 0
    CHARGE = 1

    def __init__(self, x):
        # Build scaled-down frames
        self._frames = {}
        for d in ('left', 'right'):
            self._frames[d] = [
                pygame.transform.scale(_make_demon_frame(d, f), (34, 36))
                for f in range(4)
            ]
        self.x = x
        self.y = HEIGHT - 65
        self.vx = random.choice([-1.5, 1.5])
        self.frame_index = random.uniform(0, 4)
        self.state = self.WALK
        self._charge_timer = 0
        self._charge_dir = 1

    def update(self):
        if self.state == self.WALK:
            self.x += self.vx
            self.frame_index += 0.12

            # Reverse at screen edges
            if self.x < 40 or self.x > WIDTH - 40:
                self.vx = -self.vx
                self.x = max(40, min(WIDTH - 40, self.x))

            # Random charge
            if random.random() < 0.003:
                self.state = self.CHARGE
                self._charge_timer = 0
                self._charge_dir = 1 if self.vx > 0 else -1

        elif self.state == self.CHARGE:
            self.x += self._charge_dir * 5.0
            self.frame_index += 0.25
            self._charge_timer += 1

            # Bounce at edges
            if self.x < 40 or self.x > WIDTH - 40:
                self._charge_dir = -self._charge_dir
                self.x = max(40, min(WIDTH - 40, self.x))

            # Charge lasts ~1 second
            if self._charge_timer > 60:
                self.state = self.WALK
                self.vx = self._charge_dir * 1.5

        if self.frame_index >= 4:
            self.frame_index = 0

    def draw(self, surface):
        direction = 'right' if self.vx > 0 else 'left'
        if self.state == self.CHARGE:
            direction = 'right' if self._charge_dir > 0 else 'left'
        frame = self._frames[direction][int(self.frame_index)]
        surface.blit(frame, (int(self.x) - 17, int(self.y) - 18))


# ------------------------------------------------------------------
# Title crawl coordinator
# ------------------------------------------------------------------

class TitleCrawl:
    """Manages story text scroll and decorative sprites on the title screen."""

    def __init__(self):
        self._font = pygame.font.Font(None, 28)
        self._lines = self._wrap_text(_STORY_TEXT, 600)
        self._line_surfaces = [
            self._font.render(line, True, (160, 150, 130))
            for line in self._lines
        ]
        self._line_spacing = 34
        self._scroll_speed = 0.5
        self._scroll_offset = 0.0
        self._total_height = len(self._lines) * self._line_spacing

        # Decorative sprites
        self.bats = [DecoBat() for _ in range(5)]
        self.demons = [DecoDemon(x) for x in (200, 640, 1080)]

    def _wrap_text(self, text, max_width):
        """Word-wrap text into lines, respecting explicit newlines."""
        paragraphs = text.split('\n')
        lines = []
        for para in paragraphs:
            if not para.strip():
                lines.append('')
                continue
            words = para.split()
            current = ''
            for word in words:
                test = current + ' ' + word if current else word
                if self._font.size(test)[0] <= max_width:
                    current = test
                else:
                    if current:
                        lines.append(current)
                    current = word
            if current:
                lines.append(current)
        return lines

    def update(self):
        self._scroll_offset += self._scroll_speed

        # Loop when all text has scrolled past the top
        if self._scroll_offset > self._total_height + HEIGHT:
            self._scroll_offset = 0.0

        for bat in self.bats:
            bat.update()
        for demon in self.demons:
            demon.update()

    def draw(self, surface):
        # Draw crawl text
        for i, line_surf in enumerate(self._line_surfaces):
            y = HEIGHT + (i * self._line_spacing) - self._scroll_offset
            if y < -40 or y > HEIGHT + 40:
                continue
            # Fade near top of screen
            alpha = 255
            if y < 120:
                alpha = max(0, int(255 * y / 120))
            # Fade near bottom too for smooth entry
            if y > HEIGHT - 60:
                alpha = min(alpha, max(0, int(255 * (HEIGHT - y) / 60)))

            if alpha < 255:
                ls = line_surf.copy()
                ls.set_alpha(alpha)
            else:
                ls = line_surf
            x = (WIDTH - line_surf.get_width()) // 2
            surface.blit(ls, (x, int(y)))

        # Draw decorative sprites
        for bat in self.bats:
            bat.draw(surface)
        for demon in self.demons:
            demon.draw(surface)
