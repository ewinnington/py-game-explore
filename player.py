from tkinter import Toplevel
import pygame
import os
from data import *

class Player(pygame.sprite.Sprite):
    def __init__(self,pos,groups):
        super().__init__(groups)
        colorkey = (255,0,255)
        self.image = pygame.image.load(os.path.join('sprites','player.png')).set_colorkey(colorkey).convert_alpha()
        self.rect = self.image.get_rect(topleft=pos)