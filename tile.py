import pygame
import os
from data import *

class Tile(pygame.sprite.Sprite):
    def __init__(self,pos,groups):
        super().__init__(groups)
        colorkey = (255,0,255)
        self.image = pygame.image.load(os.path.join('sprites','rock.png')).convert_alpha()
        self.image.set_colorkey(colorkey)
        self.rect = self.image.get_rect(topleft=pos)