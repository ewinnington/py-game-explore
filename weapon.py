import pygame
import math
from data import *
from weapon_sprites import make_weapon_sprite


class Weapon(pygame.sprite.Sprite):
    """Melee weapon sprite.

    Sword: wide arc hitbox in front of the player (good for crowd control).
    Spear: narrow line hitbox extending further out (good for reach).
    """

    def __init__(self, player, groups):
        super().__init__(groups)
        self.weapon_type = player.weapon
        direction = player.status.split('_')[0]
        self.image = make_weapon_sprite(self.weapon_type, direction)

        if self.weapon_type == 'sword':
            # Sword: wide arc — bigger hitbox, positioned close
            self._place_arc(player, direction)
        else:
            # Spear: narrow thrust — thin and long hitbox, positioned further out
            self._place_line(player, direction)

    def _place_arc(self, player, direction):
        """Position sword with a wide arc hitbox in front of the player."""
        # Arc: wider but shorter reach
        if direction == 'up':
            self.rect = self.image.get_rect(midbottom=player.rect.midtop)
            # Make hitbox wider (arc sweep)
            self.rect.inflate_ip(24, 0)
        elif direction == 'down':
            self.rect = self.image.get_rect(midtop=player.rect.midbottom)
            self.rect.inflate_ip(24, 0)
        elif direction == 'left':
            self.rect = self.image.get_rect(
                midright=player.rect.midleft + pygame.math.Vector2(0, 12))
            self.rect.inflate_ip(0, 24)
        else:  # right
            self.rect = self.image.get_rect(
                midleft=player.rect.midright + pygame.math.Vector2(0, 12))
            self.rect.inflate_ip(0, 24)

    def _place_line(self, player, direction):
        """Position spear with a narrow line hitbox extending further from player."""
        # Line: narrow but longer reach
        if direction == 'up':
            self.rect = self.image.get_rect(midbottom=player.rect.midtop)
        elif direction == 'down':
            self.rect = self.image.get_rect(midtop=player.rect.midbottom)
        elif direction == 'left':
            self.rect = self.image.get_rect(
                midright=player.rect.midleft + pygame.math.Vector2(0, 12))
        else:  # right
            self.rect = self.image.get_rect(
                midleft=player.rect.midright + pygame.math.Vector2(0, 12))
