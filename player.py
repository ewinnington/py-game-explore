import pygame
import os
from data import *

class Player(pygame.sprite.Sprite):
    def __init__(self,pos,groups, obstacle_sprites):
        super().__init__(groups)
        colorkey = (255,0,255)
        self.image = pygame.image.load(os.path.join('sprites','player.png')).convert_alpha()
        self.image.set_colorkey(colorkey)
        self.rect = self.image.get_rect(topleft=pos)

        self.direction = pygame.math.Vector2(0,0)
        self.speed = 5

        self.obstacle_sprites = obstacle_sprites

    def input(self):
        self.direction.x = 0
        self.direction.y = 0
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.direction.x = -1
        if keys[pygame.K_RIGHT]:
            self.direction.x = 1
        if keys[pygame.K_UP]:
            self.direction.y = -1
        if keys[pygame.K_DOWN]:
            self.direction.y = 1

    def move(self, speed):
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()

        self.rect.x += self.direction.x * speed
        self.collision('horizontal')
        self.rect.y += self.direction.y * speed
        self.collision('vertical')
        #self.rect.center += self.direction * speed

    def collision(self, direction):
        if direction == 'horizontal':
            for sprite in self.obstacle_sprites:
                if sprite.rect.colliderect(self.rect):
                    # We assume static obstacles here 
                    if self.direction.x > 0: #moving right & colliding
                        self.rect.right = sprite.rect.left
                    if self.direction.x < 0: #moving left & colliding
                        self.rect.left = sprite.rect.right

        if direction == 'vertical': 
            for sprite in self.obstacle_sprites:
                if sprite.rect.colliderect(self.rect):
                    # We assume static obstacles here 
                    if self.direction.y > 0: #moving down & colliding
                        self.rect.bottom = sprite.rect.top
                    if self.direction.y < 0: #moving up & colliding
                        self.rect.top = sprite.rect.bottom

    def update(self):
        self.input()
        self.move(self.speed)