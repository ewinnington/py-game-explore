import pygame
import os
from data import *
from tile import Tile
from player import Player
from support import import_csv_layout

class Level:
    def __init__(self):
        # get the display surface
        self.display_surface = pygame.display.get_surface()

        # setup sprite groups
        self.visible_sprites = YSortCameraGroup()
        self.obstacle_sprites = pygame.sprite.Group()

        # create the map
        self.create_map()

    def create_map(self):
        layout = {
            'boundary': import_csv_layout(os.path.join('maps','boundary_1.csv')),
            'rocks': import_csv_layout(os.path.join('maps','boundary_1.csv')),
        }

        # change from video - create rock sprites so I can keep following
        rocks_image = pygame.image.load(os.path.join('sprites','rock.png')).convert_alpha()
        rocks_image.set_colorkey(COLORKEY)

        for style,layout in layout.items():
            for row_index,row in enumerate(layout):
                for col_index, col in enumerate(row):
                    if col != '-1': 
                        x = col_index * TILESIZE; 
                        y = row_index * TILESIZE;
                        if style == 'boundary':
                            Tile((x,y), [self.obstacle_sprites],'invisible')   # making the boundary invisible
                        if style == 'rocks':
                            Tile((x,y), [self.visible_sprites],'rocks', rocks_image )   # making the boundary invisible
                    
        self.player = Player((100,100), [self.visible_sprites], self.obstacle_sprites)

    def run(self):
        self.visible_sprites.custom_draw(self.player)
        self.visible_sprites.update()


class YSortCameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.half_height = self.display_surface.get_height() // 2
        self.half_width = self.display_surface.get_width() // 2
        self.offset = pygame.math.Vector2(0,0)

        #creating the floor 
        self.floor_surf = pygame.image.load(os.path.join('sprites','landscape_grass.png')).convert()
        self.floor_rect = self.floor_surf.get_rect(topleft = (0,0))

    def custom_draw(self, player):

        # Creating the camera movement offset 
        # this could be changed to allow the player to move in a central location without camera movement
        self.offset.x = player.rect.centerx - self.half_width
        self.offset.y = player.rect.centery - self.half_height

        #draw the floor
        floor_offset =  self.floor_rect.topleft - self.offset
        self.display_surface.blit(self.floor_surf, floor_offset)

        #for sprite in self.sprites():
        for sprite in sorted(self.sprites(), key = lambda sprite: sprite.rect.centery):
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)