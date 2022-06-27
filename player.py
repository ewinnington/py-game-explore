import pygame
import os
from data import *
from support import *

class Player(pygame.sprite.Sprite):
    def __init__(self,pos,groups, obstacle_sprites):
        super().__init__(groups)
        colorkey = (255,0,255)
        self.image = pygame.image.load(os.path.join('sprites','player.png')).convert_alpha()
        self.image.set_colorkey(colorkey)
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(0,-14) # allow 8px overlap on vertical

        #graphics setup
        self.import_player_assets()
        self.status = 'down'
        self.frame_index = 0
        self.animation_speed = 0.30

        self.direction = pygame.math.Vector2(0,0)
        self.speed = PLAYER_SPEED

        self.attacking = False
        self.attack_cooldown = 400
        self.attack_time = None

        self.obstacle_sprites = obstacle_sprites



    def import_player_assets(self):
        character_path = os.path.join('sprites','player')
        self.animations = { 
          'up':[],'down':[],'left':[],'right':[], 
          'up_idle':[],'down_idle':[],'left_idle':[],'right_idle':[], 
          'up_attack': [],'down_attack':[],'left_attack':[],'right_attack':[]
        }

        for animation in self.animations.keys():
            animation_path = os.path.join(character_path,animation)
            self.animations[animation] = import_folder(animation_path)

    def get_status(self):

        if self.direction.x == 0 and self.direction.y == 0:
            if not 'idle' in self.status and not 'attack' in self.status:
                self.status = self.status + '_idle'

        if self.attacking: 
            self.direction.x = 0
            self.direction.y = 0
            if not 'attack' in self.status:
                if 'idle' in self.status:
                    self.status = self.status.replace('_idle','_attack')
                else:
                    self.status = self.status + '_attack'
        else:
            if 'attack' in self.status:
                self.status = self.status.replace('_attack','')
        
    def animate(self):
        animation = self.animations[self.status]

        #loop over frame index
        self.frame_index += self.animation_speed
        if self.frame_index >= len(animation):
            self.frame_index = 0

        #set the current frame by animation
        self.image = animation[int(self.frame_index)]
        self.rect = self.image.get_rect(center=self.hitbox.center)

    def input(self):
        self.direction.x = 0
        self.direction.y = 0
        keys = pygame.key.get_pressed()
        if not self.attacking: #stop moving if attacking
            #movement input
            if keys[pygame.K_LEFT]:
                self.direction.x = -1
                self.status = 'left'
            if keys[pygame.K_RIGHT]:
                self.direction.x = 1
                self.status = 'right'
            if keys[pygame.K_UP]:
                self.direction.y = -1
                self.status = 'up'
            if keys[pygame.K_DOWN]:
                self.direction.y = 1
                self.status = 'down'

            #attack input
            if keys[pygame.K_SPACE] and not self.attacking:
                self.attacking = True
                self.attack_time =  pygame.time.get_ticks()
                print('attack')

            #magic input
            if keys[pygame.K_LCTRL] and not self.attacking:
                self.attacking = True
                self.attack_time =  pygame.time.get_ticks()
                print('magic')
        
    def cooldown(self):
        current_time = pygame.time.get_ticks()
        if self.attacking:
            if (current_time - self.attack_time) > self.attack_cooldown:
                self.attacking = False
                self.attack_time = None

    def move(self, speed):
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()

        self.hitbox.x += self.direction.x * speed
        self.collision('horizontal')
        self.hitbox.y += self.direction.y * speed
        self.collision('vertical')
        self.rect.center = self.hitbox.center

    def collision(self, direction):
        if direction == 'horizontal':
            for sprite in self.obstacle_sprites:
                if sprite.hitbox.colliderect(self.hitbox):
                    # We assume static obstacles here 
                    if self.direction.x > 0: #moving right & colliding
                        self.hitbox.right = sprite.hitbox.left
                    if self.direction.x < 0: #moving left & colliding
                        self.hitbox.left = sprite.hitbox.right

        if direction == 'vertical': 
            for sprite in self.obstacle_sprites:
                if sprite.hitbox.colliderect(self.hitbox):
                    # We assume static obstacles here 
                    if self.direction.y > 0: #moving down & colliding
                        self.hitbox.bottom = sprite.hitbox.top
                    if self.direction.y < 0: #moving up & colliding
                        self.hitbox.top = sprite.hitbox.bottom

    def update(self):
        self.input()
        self.cooldown()
        self.get_status()
        self.animate()
        self.move(self.speed)