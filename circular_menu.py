import pygame
import math


class CircularMenu:
    """Secret of Mana inspired ring menu.

    Items orbit the player in a circle. The selected item is always at the top.
    Smooth spiral opening/closing animation with golden-themed icon boxes.

    Controls (while TAB held):
        LEFT/RIGHT - spin ring to next/prev item
        UP         - add an item from the pool
        DOWN       - remove the selected item
        SPACE      - select the current item and dismiss
    """

    CLOSED = 0
    OPENING = 1
    OPEN = 2
    CLOSING = 3

    def __init__(self, items, radius=80, max_items=8):
        """
        items: list of dicts with 'name' (str) and 'icon' (pygame.Surface)
        radius: ring radius in pixels
        max_items: max number of items the ring can hold
        """
        self.items = list(items)
        self.max_items = max_items
        self.full_radius = radius
        self.state = self.CLOSED

        # Pool of extra items that can be added with UP
        self.item_pool = []

        # Animation state
        self.anim_t = 0.0           # 0 = fully closed, 1 = fully open
        self.ring_angle = 0.0       # current visual rotation (degrees)
        self.target_ring_angle = 0.0
        self.selected_index = 0
        self.spiral_twist = 0.0     # extra twist during open/close spiral

        # Prevents immediate reopen after SPACE dismissal
        self.dismissed_by_select = False

        # Timing
        self.last_tick = pygame.time.get_ticks()

        # Input cooldowns (ms)
        self._cooldowns = {}
        self._nav_cd = 180
        self._action_cd = 250

        # Selection result
        self.last_selected = None

        # Cached font
        self._font = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def active(self):
        return self.state != self.CLOSED

    @property
    def is_interactive(self):
        return self.state == self.OPEN

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def open(self):
        if self.dismissed_by_select:
            return
        if self.state in (self.CLOSED, self.CLOSING):
            self.state = self.OPENING
            self.spiral_twist = 120.0
            self.last_selected = None

    def close(self):
        if self.state in (self.OPEN, self.OPENING):
            self.state = self.CLOSING

    def select(self):
        """Select the current item, print to console, dismiss the menu."""
        if self.state != self.OPEN or not self.items:
            return None
        if not self._check_cd('select', self._action_cd):
            return None

        item = self.items[self.selected_index]
        self.last_selected = item
        self.dismissed_by_select = True
        self.state = self.CLOSING
        print(f">>> Selected: {item['name']} <<<")
        return item

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate_left(self):
        if self.state != self.OPEN or not self.items:
            return
        if not self._check_cd('nav', self._nav_cd):
            return
        self.selected_index = (self.selected_index - 1) % len(self.items)
        self._sync_target_angle()

    def navigate_right(self):
        if self.state != self.OPEN or not self.items:
            return
        if not self._check_cd('nav', self._nav_cd):
            return
        self.selected_index = (self.selected_index + 1) % len(self.items)
        self._sync_target_angle()

    def add_item(self):
        """Pull an item from the pool into the ring."""
        if self.state != self.OPEN:
            return
        if not self._check_cd('add', self._action_cd):
            return
        if len(self.items) >= self.max_items or not self.item_pool:
            return
        item = self.item_pool.pop(0)
        self.items.append(item)
        self._sync_target_angle()
        print(f"Added: {item['name']}")

    def remove_item(self):
        """Remove the selected item and return it to the pool."""
        if self.state != self.OPEN:
            return
        if not self._check_cd('remove', self._action_cd):
            return
        if len(self.items) <= 1:
            return
        removed = self.items.pop(self.selected_index)
        self.item_pool.append(removed)
        if self.selected_index >= len(self.items):
            self.selected_index = 0
        self._sync_target_angle()
        self.ring_angle = self.target_ring_angle  # snap to avoid wild spin
        print(f"Removed: {removed['name']}")

    # ------------------------------------------------------------------
    # Update (call every frame)
    # ------------------------------------------------------------------

    def update(self):
        now = pygame.time.get_ticks()
        dt = min((now - self.last_tick) / 1000.0, 0.05)
        self.last_tick = now

        if self.state == self.CLOSED:
            return

        # Open / close animation
        if self.state == self.OPENING:
            self.anim_t += 3.8 * dt
            self.spiral_twist *= max(0.0, 1.0 - 5.5 * dt)
            if self.anim_t >= 1.0:
                self.anim_t = 1.0
                self.spiral_twist = 0.0
                self.state = self.OPEN

        elif self.state == self.CLOSING:
            self.anim_t -= 5.0 * dt
            self.spiral_twist -= 180.0 * dt
            if self.anim_t <= 0.0:
                self.anim_t = 0.0
                self.spiral_twist = 0.0
                self.state = self.CLOSED

        # Smooth rotation lerp
        diff = self.target_ring_angle - self.ring_angle
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        self.ring_angle += diff * min(1.0, 10.0 * dt)
        if abs(diff) < 0.3:
            self.ring_angle = self.target_ring_angle

    # ------------------------------------------------------------------
    # Draw (call every frame after sprites)
    # ------------------------------------------------------------------

    def draw(self, surface, screen_center):
        if self.state == self.CLOSED:
            return
        if not self.items:
            return

        cx, cy = int(screen_center[0]), int(screen_center[1])
        num = len(self.items)
        eased = self._ease_out_back(max(0.0, min(1.0, self.anim_t)))
        radius = self.full_radius * eased

        if radius < 3:
            return

        # Semi-transparent backdrop circle
        self._draw_backdrop(surface, cx, cy, radius)

        # Decorative ring dots
        self._draw_ring_dots(surface, cx, cy, radius)

        # Draw items (selected last so it's on top)
        step_angle = 360.0 / num
        draw_order = [i for i in range(num) if i != self.selected_index]
        draw_order.append(self.selected_index)

        for i in draw_order:
            angle_deg = (-90.0
                         + self.ring_angle
                         + i * step_angle
                         + self.spiral_twist * (1.0 - self.anim_t))
            angle_rad = math.radians(angle_deg)

            ix = cx + math.cos(angle_rad) * radius
            iy = cy + math.sin(angle_rad) * radius

            self._draw_icon_box(surface, ix, iy, self.items[i],
                                eased, i == self.selected_index)

        # Selection arrow above the top slot
        if self.anim_t > 0.5:
            arrow_alpha = (self.anim_t - 0.5) / 0.5
            self._draw_selection_arrow(surface, cx, cy - radius, arrow_alpha)

        # Item name label below the ring
        if self.state == self.OPEN:
            self._draw_item_label(surface, cx, cy + radius + 28)

    # ------------------------------------------------------------------
    # Private drawing helpers
    # ------------------------------------------------------------------

    def _draw_backdrop(self, surface, cx, cy, radius):
        """Dark semi-transparent circle behind the ring."""
        r = int(radius + 36)
        d = r * 2
        backdrop = pygame.Surface((d, d), pygame.SRCALPHA)
        alpha = int(100 * min(1.0, self.anim_t))
        pygame.draw.circle(backdrop, (10, 8, 6, alpha), (r, r), r)
        surface.blit(backdrop, (cx - r, cy - r))

    def _draw_ring_dots(self, surface, cx, cy, radius):
        """Animated dotted golden ring."""
        tick = pygame.time.get_ticks()
        for i in range(72):
            deg = i * 5.0 + self.ring_angle * 0.2
            rad = math.radians(deg)
            px = cx + math.cos(rad) * radius
            py = cy + math.sin(rad) * radius
            shimmer = math.sin(i * 0.4 + tick * 0.004)
            brightness = int(110 + 50 * shimmer)
            color = (brightness,
                     max(0, brightness - 25),
                     max(0, brightness - 65))
            pygame.draw.circle(surface, color, (int(px), int(py)), 1)

    def _draw_icon_box(self, surface, x, y, item, scale, selected):
        """Render a single icon box with decorations."""
        base_box = 48
        base_icon = 36
        box_size = int(base_box * scale)
        icon_size = int(base_icon * scale)
        if box_size < 6:
            return

        x, y = int(x), int(y)
        half = box_size // 2
        rect = pygame.Rect(x - half, y - half, box_size, box_size)

        # Pulse for selected item
        pulse = 1.0
        if selected and scale > 0.9:
            pulse = 1.0 + 0.04 * math.sin(pygame.time.get_ticks() * 0.006)
            pbox = int(base_box * scale * pulse)
            phalf = pbox // 2
            rect = pygame.Rect(x - phalf, y - phalf, pbox, pbox)
            icon_size = int(base_icon * scale * pulse)

        # Glow behind selected
        if selected and scale > 0.5:
            glow_r = int(box_size * 0.7 * pulse)
            glow_d = glow_r * 2
            glow = pygame.Surface((glow_d, glow_d), pygame.SRCALPHA)
            for r in range(glow_r, 0, -2):
                a = int(25 * (r / glow_r))
                pygame.draw.circle(glow, (255, 200, 50, a), (glow_r, glow_r), r)
            surface.blit(glow, (x - glow_r, y - glow_r))

        # Shadow
        shadow_rect = rect.move(2, 2)
        pygame.draw.rect(surface, (0, 0, 0, 60) if hasattr(pygame, 'SRCALPHA') else (15, 12, 8),
                         shadow_rect, border_radius=4)

        # Box background
        bg = (70, 55, 30) if selected else (45, 38, 28)
        pygame.draw.rect(surface, bg, rect, border_radius=4)

        # Border
        if selected:
            border_color = (255, 215, 65)
            border_w = 3
        else:
            border_color = (155, 135, 85)
            border_w = 2
        pygame.draw.rect(surface, border_color, rect, border_w, border_radius=4)

        # Inner frame
        if box_size > 22:
            inner = rect.inflate(-8, -8)
            inner_c = (175, 145, 55) if selected else (95, 80, 48)
            pygame.draw.rect(surface, inner_c, inner, 1, border_radius=2)

        # Icon
        icon_surf = item.get('icon') if isinstance(item, dict) else item
        if icon_surf and icon_size > 4:
            try:
                scaled = pygame.transform.smoothscale(icon_surf, (icon_size, icon_size))
            except Exception:
                scaled = pygame.transform.scale(icon_surf, (icon_size, icon_size))
            surface.blit(scaled, scaled.get_rect(center=(x, y)))

        # Corner brackets on selected
        if selected and scale > 0.8:
            self._draw_corner_brackets(surface, rect)

    def _draw_corner_brackets(self, surface, rect):
        """Golden corner brackets around the selected box."""
        c = (255, 230, 100)
        l = 6
        offsets = [
            # top-left
            ((rect.left - 3, rect.top - 3), (rect.left - 3 + l, rect.top - 3),
             (rect.left - 3, rect.top - 3), (rect.left - 3, rect.top - 3 + l)),
            # top-right
            ((rect.right + 2, rect.top - 3), (rect.right + 2 - l, rect.top - 3),
             (rect.right + 2, rect.top - 3), (rect.right + 2, rect.top - 3 + l)),
            # bottom-left
            ((rect.left - 3, rect.bottom + 2), (rect.left - 3 + l, rect.bottom + 2),
             (rect.left - 3, rect.bottom + 2), (rect.left - 3, rect.bottom + 2 - l)),
            # bottom-right
            ((rect.right + 2, rect.bottom + 2), (rect.right + 2 - l, rect.bottom + 2),
             (rect.right + 2, rect.bottom + 2), (rect.right + 2, rect.bottom + 2 - l)),
        ]
        for h_start, h_end, v_start, v_end in offsets:
            pygame.draw.line(surface, c, h_start, h_end, 2)
            pygame.draw.line(surface, c, v_start, v_end, 2)

    def _draw_selection_arrow(self, surface, cx, top_y, alpha):
        """Bobbing arrow above the selected slot."""
        bob = int(3 * math.sin(pygame.time.get_ticks() * 0.005))
        tip_y = int(top_y) - 22 + bob
        size = 7
        points = [
            (cx, tip_y + size * 2),
            (cx - size, tip_y),
            (cx + size, tip_y),
        ]
        a = max(0, min(255, int(255 * alpha)))
        color = (255, 220, 70)
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, (200, 170, 40), points, 1)

    def _draw_item_label(self, surface, cx, label_y):
        """Render the name of the selected item in a small label."""
        if not self.items:
            return
        name = self.items[self.selected_index].get('name', '???')

        if self._font is None:
            self._font = pygame.font.Font(None, 22)

        text = self._font.render(name, True, (255, 230, 155))
        text_rect = text.get_rect(center=(cx, int(label_y)))

        # Background pill
        bg_rect = text_rect.inflate(14, 8)
        bg = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg, (25, 20, 15, 210), bg.get_rect(), border_radius=4)
        pygame.draw.rect(bg, (140, 120, 70, 200), bg.get_rect(), 1, border_radius=4)
        surface.blit(bg, bg_rect.topleft)
        surface.blit(text, text_rect)

    # ------------------------------------------------------------------
    # Easing
    # ------------------------------------------------------------------

    @staticmethod
    def _ease_out_back(t):
        """Overshoot easing for a bouncy pop-out feel."""
        c1 = 1.70158
        c3 = c1 + 1
        return 1.0 + c3 * pow(t - 1.0, 3) + c1 * pow(t - 1.0, 2)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sync_target_angle(self):
        if self.items:
            step = 360.0 / len(self.items)
            self.target_ring_angle = -self.selected_index * step

    def _check_cd(self, action, cooldown_ms):
        now = pygame.time.get_ticks()
        if now - self._cooldowns.get(action, 0) >= cooldown_ms:
            self._cooldowns[action] = now
            return True
        return False

    def get_selected_item(self):
        if self.items:
            return self.items[self.selected_index % len(self.items)]
        return None
