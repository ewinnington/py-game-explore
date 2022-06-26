import pygame
import os
from data import *

class Tile(pygame.sprite.Sprite):
    def __init__(self,pos,groups,sprite_type, surface = pygame.Surface((TILESIZE,TILESIZE))):
        super().__init__(groups)
        self.sprite_type = sprite_type
        self.image = surface
        colorkey = (255,0,255)
        self.image.set_colorkey(colorkey)
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(0,-8) # allow 8px overlap on vertical