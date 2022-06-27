import pygame
import os
import random
from data import *
from tile import Tile
from player import Player
from support import *

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
            'rocks':    import_csv_layout(os.path.join('maps','boundary_1.csv')),
            'grass':    import_csv_layout(os.path.join('maps','grass_1.csv')),
            'object':   import_csv_layout(os.path.join('maps','object_1.csv')),
        }

        graphics = {
            'grass':   import_folder(os.path.join('sprites','grass')),
            'objects': import_folder(os.path.join('sprites','objects')),
        }

        for style,layout in layout.items():
            for row_index,row in enumerate(layout):
                for col_index, col in enumerate(row):
                    if col != '-1': 
                        x = col_index * TILESIZE; 
                        y = row_index * TILESIZE;
                        if style == 'boundary':
                           Tile((x,y), [self.obstacle_sprites],'invisible')   # making the boundary invisible
                        if style == 'rocks':
                             # change from video - create rock sprites so I can keep following
                            rocks_image = pygame.image.load(os.path.join('sprites','rock.png')).convert_alpha()
                            rocks_image.set_colorkey(COLORKEY)
                            Tile((x,y), [self.visible_sprites],'rocks', rocks_image )   # making the boundary invisible
                        if style == 'grass':
                            # Grass image
                            random_grass_image = random.choice(graphics['grass'])
                            Tile((x,y), [self.visible_sprites,self.obstacle_sprites],'grass', random_grass_image)   # making the boundary invisible
                        if style == 'object':
                            # Object image
                            
                            object_image = graphics['objects'][int(col)]
                            if (int(col)==1) :
                                objectType = 'sceneryObject' #scenery object can be 64x128 and is impassable
                                Tile((x,y), [self.visible_sprites,self.obstacle_sprites],objectType,object_image)   
                            else: 
                                objectType = 'object'
                                Tile((x,y), [self.visible_sprites],objectType,object_image)   # objects are passable
                    
        self.player = Player((100,200), [self.visible_sprites], self.obstacle_sprites)

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
        # this could be changed to allow the player to move in a central location without camera movement with min, max boxes
        self.offset.x = min(self.floor_rect.width ,max(0, player.rect.centerx - self.half_width))
        self.offset.y = min(self.floor_rect.height ,max(0,player.rect.centery - self.half_height))

        #draw the floor
        floor_offset =  self.floor_rect.topleft - self.offset
        self.display_surface.blit(self.floor_surf, floor_offset)

        #for sprite in self.sprites():
        for sprite in sorted(self.sprites(), key = lambda sprite: sprite.rect.centery):
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)