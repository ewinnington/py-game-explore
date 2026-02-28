import pygame
import os
import random
from data import *
from tile import Tile
from player import Player
from support import *
from weapon import Weapon
from player import weapon_data
from enemy import Enemy
from magic import FireCone, IceBall, ShadowBlade
from spawner import CaveSpawner
from hud import HUD

class Level:
    def __init__(self):
        # get the display surface
        self.display_surface = pygame.display.get_surface()

        # setup sprite groups
        self.visible_sprites = YSortCameraGroup()
        self.obstacle_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.magic_sprites = pygame.sprite.Group()

        # attack sprites
        self.current_attack = None

        # HUD
        self.hud = HUD()

        # create the map
        self.create_map()

    def create_attack(self):
        self.current_attack = Weapon(self.player, [self.visible_sprites])

    def destroy_weapon(self):
        if self.current_attack:
            self.current_attack.kill()
        self.current_attack = None

    def create_magic(self):
        """Spawn the spell the player currently has equipped."""
        key = self.player.magic
        groups = [self.visible_sprites, self.magic_sprites]

        if key == 'fire_cone':
            FireCone(self.player, groups)
        elif key == 'ice_ball':
            IceBall(self.player, groups)
        elif key == 'shadow_blade':
            ShadowBlade(self.player, groups, self.enemy_sprites)

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

        self.player = Player(
            (100, 200),
            [self.visible_sprites],
            self.obstacle_sprites,
            self.create_attack,
            self.destroy_weapon,
            self.create_magic,
        )

        # Spawn enemies in open areas
        enemy_positions = [(400, 350), (700, 300), (350, 650)]
        for pos in enemy_positions:
            Enemy(pos,
                  [self.visible_sprites, self.enemy_sprites],
                  self.obstacle_sprites,
                  self.player)

        # Cave spawner near the bottom of the map
        cave_x = 10 * TILESIZE   # column 10 → 640 px
        cave_y = 17 * TILESIZE   # row 17 → 1088 px  (near bottom)
        self.cave_spawner = CaveSpawner(
            pos=(cave_x, cave_y),
            groups=[self.visible_sprites],
            obstacle_sprites=self.obstacle_sprites,
            enemy_groups=[self.visible_sprites, self.enemy_sprites],
            player=self.player,
            spawn_interval=4000,
            max_alive=5,
        )

    def _check_weapon_hits(self):
        """Damage enemies struck by the player's weapon."""
        if not self.current_attack:
            return
        for enemy in self.enemy_sprites:
            if enemy.state == enemy.DYING:
                continue
            if self.current_attack.rect.colliderect(enemy.hitbox):
                weapon_dmg = weapon_data.get(self.player.weapon, {}).get('damage', 10)
                enemy.take_hit(weapon_dmg)

    def _check_magic_hits(self):
        """Damage enemies struck by magic projectiles."""
        from magic import magic_data as _md
        for spell in list(self.magic_sprites):
            for enemy in self.enemy_sprites:
                if enemy.state == enemy.DYING:
                    continue
                if id(enemy) in spell.hit_enemies:
                    continue
                if spell.hitbox.colliderect(enemy.hitbox):
                    spell_key = getattr(spell, 'spell_key', None)
                    dmg = _md.get(spell_key, {}).get('damage', 15) if spell_key else 15
                    enemy.take_hit(dmg)
                    spell.hit_enemies.add(id(enemy))
                    if not spell.piercing:
                        spell.kill()
                        break

    def run(self):
        self.visible_sprites.custom_draw(self.player)
        self.visible_sprites.update()
        self._check_weapon_hits()
        self._check_magic_hits()

        # Draw enemy notice indicators on top of sprites
        offset = self.visible_sprites.offset
        for enemy in self.enemy_sprites:
            enemy.draw_notice_indicator(self.display_surface, offset)

        # Draw the ring menu on top of everything, in screen coordinates
        menu = self.player.circular_menu
        if menu.active:
            screen_center = (
                self.player.rect.centerx - offset.x,
                self.player.rect.centery - offset.y,
            )
            menu.draw(self.display_surface, screen_center)

        # HUD always on top
        self.hud.draw(self.player)


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
