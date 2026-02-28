import pygame
import math
from circular_menu import CircularMenu


class DualRingMenu:
    """Secret of Mana style dual ring menu.

    Two separate rings — one for weapons, one for magic — that the player
    switches between with UP/DOWN.  LEFT/RIGHT navigates within the current
    ring, SPACE selects.

    The magic ring only becomes accessible once the player has at least one
    magic item.
    """

    WEAPON_RING = 0
    MAGIC_RING = 1

    def __init__(self, weapon_items, magic_items=None, radius=80):
        self.weapon_ring = CircularMenu(items=weapon_items, radius=radius)
        self.magic_ring = CircularMenu(items=magic_items or [], radius=radius)
        self.active_ring_index = self.WEAPON_RING
        self._switch_cd = 0  # cooldown timer for ring switch

        # Ring label font
        self._label_font = None

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------

    @property
    def active(self):
        return self._current_ring().active

    @property
    def is_interactive(self):
        return self._current_ring().is_interactive

    @property
    def dismissed_by_select(self):
        return self._current_ring().dismissed_by_select

    @dismissed_by_select.setter
    def dismissed_by_select(self, val):
        self.weapon_ring.dismissed_by_select = val
        self.magic_ring.dismissed_by_select = val

    @property
    def last_selected(self):
        return self._current_ring().last_selected

    # ------------------------------------------------------------------
    # Ring access
    # ------------------------------------------------------------------

    def _current_ring(self):
        if self.active_ring_index == self.MAGIC_RING:
            return self.magic_ring
        return self.weapon_ring

    def has_magic(self):
        return len(self.magic_ring.items) > 0

    # ------------------------------------------------------------------
    # Open / Close / Select
    # ------------------------------------------------------------------

    def open(self):
        self._current_ring().open()

    def close(self):
        # Close whichever ring is active
        if self.weapon_ring.active:
            self.weapon_ring.close()
        if self.magic_ring.active:
            self.magic_ring.close()

    def select(self):
        return self._current_ring().select()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate_left(self):
        self._current_ring().navigate_left()

    def navigate_right(self):
        self._current_ring().navigate_right()

    def switch_ring_up(self):
        """Switch to the other ring (UP direction)."""
        self._try_switch(-1)

    def switch_ring_down(self):
        """Switch to the other ring (DOWN direction)."""
        self._try_switch(1)

    def _try_switch(self, direction):
        if not self.has_magic():
            return  # only one ring available
        now = pygame.time.get_ticks()
        if now - self._switch_cd < 250:
            return
        self._switch_cd = now

        # Close current ring, switch, open new ring
        old_ring = self._current_ring()
        was_open = old_ring.state == CircularMenu.OPEN

        if was_open:
            old_ring.close()

        if self.active_ring_index == self.WEAPON_RING:
            self.active_ring_index = self.MAGIC_RING
        else:
            self.active_ring_index = self.WEAPON_RING

        # Force the new ring open immediately (skip the close animation of old)
        new_ring = self._current_ring()
        if was_open or old_ring.active:
            # Snap old ring closed
            old_ring.anim_t = 0.0
            old_ring.state = CircularMenu.CLOSED
            # Open new ring
            new_ring.open()

    # ------------------------------------------------------------------
    # Add items (called when runes are collected)
    # ------------------------------------------------------------------

    def add_weapon(self, item):
        self.weapon_ring.items.append(item)

    def add_magic(self, item):
        self.magic_ring.items.append(item)

    # ------------------------------------------------------------------
    # Update & Draw
    # ------------------------------------------------------------------

    def update(self):
        self.weapon_ring.update()
        self.magic_ring.update()

    def draw(self, surface, screen_center):
        ring = self._current_ring()
        if not ring.active:
            return
        ring.draw(surface, screen_center)

        # Draw ring type indicator above the menu
        cx, cy = int(screen_center[0]), int(screen_center[1])
        eased = ring._ease_out_back(max(0, min(1, ring.anim_t)))
        radius = ring.full_radius * eased
        if radius < 3:
            return

        if self._label_font is None:
            self._label_font = pygame.font.Font(None, 20)

        # Ring type label + arrows
        label_y = cy - radius - 44
        ring_name = "WEAPONS" if self.active_ring_index == self.WEAPON_RING else "MAGIC"
        color = (255, 210, 100) if self.active_ring_index == self.WEAPON_RING else (140, 160, 255)

        text = self._label_font.render(ring_name, True, color)
        text_rect = text.get_rect(center=(cx, label_y))

        # Background pill
        bg_rect = text_rect.inflate(20, 8)
        bg = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg, (15, 12, 10, 200), bg.get_rect(), border_radius=4)
        pygame.draw.rect(bg, color + (120,), bg.get_rect(), 1, border_radius=4)
        surface.blit(bg, bg_rect.topleft)
        surface.blit(text, text_rect)

        # UP/DOWN arrows if magic is available
        if self.has_magic():
            arrow_color = (180, 170, 130)
            # Up arrow
            ax = cx
            ay = label_y - 14
            pts_up = [(ax, ay - 4), (ax - 5, ay + 2), (ax + 5, ay + 2)]
            pygame.draw.polygon(surface, arrow_color, pts_up)
            # Down arrow
            ay2 = label_y + 14
            pts_down = [(ax, ay2 + 4), (ax - 5, ay2 - 2), (ax + 5, ay2 - 2)]
            pygame.draw.polygon(surface, arrow_color, pts_down)

    def get_selected_item(self):
        return self._current_ring().get_selected_item()
