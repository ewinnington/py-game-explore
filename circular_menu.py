import pygame
import math
from data import *

class CircularMenu:
    def __init__(self, center_pos, radius, items):
        self.center_pos = center_pos
        self.radius = radius
        self.items = items
        self.angle = 0
        self.active = False
        self.selected_index = 0
        self.animation_progress = 0
        self.animation_speed = 0.1

    def toggle(self):
        self.active = not self.active
        if self.active:
            self.animation_progress = 0

    def update(self, left_pressed, right_pressed):
        if self.active:
            self.animation_progress = min(1, self.animation_progress + self.animation_speed)
            
            if left_pressed:
                self.angle += 5
            if right_pressed:
                self.angle -= 5

            self.selected_index = int((-self.angle / 360) * len(self.items)) % len(self.items)

    def draw(self, surface):
        if not self.active and self.animation_progress == 0:
            return

        for i, item in enumerate(self.items):
            angle = self.angle + (i * 360 / len(self.items))
            rad_angle = math.radians(angle)
            
            # Calculate position with easing
            eased_progress = self.ease_out_cubic(self.animation_progress)
            x = self.center_pos[0] + math.cos(rad_angle) * self.radius * eased_progress
            y = self.center_pos[1] + math.sin(rad_angle) * self.radius * eased_progress
            
            # Draw item
            item_rect = item.get_rect(center=(x, y))
            surface.blit(item, item_rect)

            # Highlight selected item
            if i == self.selected_index:
                pygame.draw.circle(surface, (255, 255, 255), (int(x), int(y)), item.get_width() // 2 + 5, 2)

    def ease_out_cubic(self, t):
        return 1 - math.pow(1 - t, 3)

    def get_selected_item(self):
        return self.items[self.selected_index]