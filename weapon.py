import pygame
import os
from data import *

class Weapon(pygame.sprite.Sprite):
    def __init__(self, player, groups):
        super().__init__(groups)
        direction = player.status.split('_')[0]
        full_path = os.path.join('sprites','weapons',player.weapon,direction + '.png')
        self.image = pygame.image.load(full_path).convert_alpha()
        self.image.set_colorkey(COLORKEY)

        if direction == 'up':
            self.rect = self.image.get_rect(midbottom = player.rect.midtop)
        elif direction == 'down':
            self.rect = self.image.get_rect(midtop = player.rect.midbottom)
        elif direction== 'left':
            self.rect = self.image.get_rect(midright = player.rect.midleft + pygame.math.Vector2(0,12)) # to get correct height for hand
        else:
            self.rect = self.image.get_rect(midleft = player.rect.midright + pygame.math.Vector2(0,12)) # to get correct height for hand
