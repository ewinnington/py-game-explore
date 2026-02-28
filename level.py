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
from enemy_bat import Bat
from enemy_centipede import Centipede
from magic import FireCone, IceBall, ShadowBlade, magic_data
from spawner import CaveSpawner
from hud import HUD
from pickup import RunePickup, HealthPickup
from portal import Portal

# Map enemy type string to class
_ENEMY_CLASSES = {
    'demon': Enemy,
    'bat': Bat,
    'centipede': Centipede,
}

# Map rune pickup string to (rune_type, icon_source)
_RUNE_MAP = {
    'rune_spear':   ('spear',        lambda: weapon_data['spear']['graphic']),
    'rune_fire':    ('fire_cone',    lambda: magic_data['fire_cone']['icon']),
    'rune_ice':     ('ice_ball',     lambda: magic_data['ice_ball']['icon']),
    'rune_shadow':  ('shadow_blade', lambda: magic_data['shadow_blade']['icon']),
}


class Level:
    def __init__(self, level_config, player=None):
        """
        level_config: dict from level_data.LEVELS
        player: existing Player to carry between levels (None for first level)
        """
        self.display_surface = pygame.display.get_surface()
        self.config = level_config

        # Sprite groups
        self.visible_sprites = YSortCameraGroup(level_config.get('floor'))
        self.obstacle_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.magic_sprites = pygame.sprite.Group()
        self.pickup_sprites = pygame.sprite.Group()

        self.current_attack = None
        self.hud = HUD()

        # Objective tracking
        self.level_kills = 0
        self.objective_complete = False
        self.portal = None

        # Font for level name / objective
        self._obj_font = pygame.font.Font(None, 22)
        self._title_font = pygame.font.Font(None, 36)
        self._show_title_until = pygame.time.get_ticks() + 3000  # show name for 3s

        # Carry player or create fresh
        self._existing_player = player

        self.create_map()

    def create_attack(self):
        self.current_attack = Weapon(self.player, [self.visible_sprites])

    def destroy_weapon(self):
        if self.current_attack:
            self.current_attack.kill()
        self.current_attack = None

    def create_magic(self):
        key = self.player.magic
        groups = [self.visible_sprites, self.magic_sprites]
        if key == 'fire_cone':
            FireCone(self.player, groups)
        elif key == 'ice_ball':
            IceBall(self.player, groups)
        elif key == 'shadow_blade':
            ShadowBlade(self.player, groups, self.enemy_sprites)

    def create_map(self):
        cfg = self.config
        csv_paths = cfg['map_csv']

        layout = {
            'boundary': import_csv_layout(csv_paths['boundary']),
            'rocks':    import_csv_layout(csv_paths['rocks']),
            'grass':    import_csv_layout(csv_paths['grass']),
            'object':   import_csv_layout(csv_paths['object']),
        }

        graphics = {
            'grass':   import_folder(os.path.join('sprites', 'grass')),
            'objects': import_folder(os.path.join('sprites', 'objects')),
        }

        for style, layer in layout.items():
            for row_index, row in enumerate(layer):
                for col_index, col in enumerate(row):
                    if col != '-1':
                        x = col_index * TILESIZE
                        y = row_index * TILESIZE
                        if style == 'boundary':
                            Tile((x, y), [self.obstacle_sprites], 'invisible')
                        if style == 'rocks':
                            rocks_image = pygame.image.load(
                                os.path.join('sprites', 'rock.png')).convert_alpha()
                            rocks_image.set_colorkey(COLORKEY)
                            Tile((x, y), [self.visible_sprites], 'rocks', rocks_image)
                        if style == 'grass':
                            random_grass_image = random.choice(graphics['grass'])
                            Tile((x, y), [self.visible_sprites, self.obstacle_sprites],
                                 'grass', random_grass_image)
                        if style == 'object':
                            object_image = graphics['objects'][int(col)]
                            if int(col) == 1:
                                Tile((x, y),
                                     [self.visible_sprites, self.obstacle_sprites],
                                     'sceneryObject', object_image)
                            else:
                                Tile((x, y), [self.visible_sprites],
                                     'object', object_image)

        # --- Player ---
        if self._existing_player:
            # Carry player from previous level
            self.player = self._existing_player
            self.player.rect.topleft = cfg['player_pos']
            self.player.hitbox.center = self.player.rect.center
            # Re-add to new sprite groups
            self.player.add(self.visible_sprites)
            self.player.obstacle_sprites = self.obstacle_sprites
            self.player.create_attack = self.create_attack
            self.player.destroy_weapon = self.destroy_weapon
            self.player.create_magic = self.create_magic
        else:
            self.player = Player(
                cfg['player_pos'],
                [self.visible_sprites],
                self.obstacle_sprites,
                self.create_attack,
                self.destroy_weapon,
                self.create_magic,
            )

        # --- Enemies ---
        enemy_groups = [self.visible_sprites, self.enemy_sprites]
        for etype, pos in cfg.get('enemies', []):
            cls = _ENEMY_CLASSES.get(etype, Enemy)
            if cls == Centipede:
                cls(pos, enemy_groups, self.obstacle_sprites, self.player,
                    num_segments=5)
            else:
                cls(pos, enemy_groups, self.obstacle_sprites, self.player)

        # --- Pickups ---
        pickup_groups = [self.visible_sprites, self.pickup_sprites]
        for ptype, pos in cfg.get('pickups', []):
            if ptype.startswith('rune_'):
                rune_info = _RUNE_MAP.get(ptype)
                if rune_info:
                    rune_type, icon_fn = rune_info
                    # Skip runes the player already has
                    if self._existing_player and rune_type in self._existing_player.collected_runes:
                        continue
                    RunePickup(pos, pickup_groups, rune_type, icon=icon_fn())
            elif ptype == 'health':
                HealthPickup(pos, pickup_groups, heal_amount=20)

        # --- Spawners ---
        for sp_cfg in cfg.get('spawners', []):
            CaveSpawner(
                pos=(sp_cfg['pos_col'] * TILESIZE, sp_cfg['pos_row'] * TILESIZE),
                groups=[self.visible_sprites],
                obstacle_sprites=self.obstacle_sprites,
                enemy_groups=[self.visible_sprites, self.enemy_sprites],
                player=self.player,
                spawn_interval=sp_cfg.get('interval', 4000),
                max_alive=sp_cfg.get('max', 5),
            )

    # ------------------------------------------------------------------
    # Objective checking
    # ------------------------------------------------------------------

    def _check_objective(self):
        if self.objective_complete:
            return
        obj = self.config.get('objective', {})
        otype = obj.get('type', 'kill_all')

        if otype == 'kill_all':
            # All non-spawner enemies dead and no spawners active
            alive = sum(1 for e in self.enemy_sprites if e.state != e.DYING)
            if alive == 0 and self.level_kills > 0:
                self._complete_objective()

        elif otype == 'kill_count':
            if self.level_kills >= obj.get('count', 10):
                self._complete_objective()

    def _complete_objective(self):
        self.objective_complete = True
        # Spawn exit portal
        portal_pos = self.config.get('portal_pos', (640, 360))
        self.portal = Portal(portal_pos, [self.visible_sprites])

    def _check_portal(self):
        """Returns True if player touches the portal."""
        if self.portal and self.portal.hitbox.colliderect(self.player.hitbox):
            return True
        return False

    # ------------------------------------------------------------------
    # Collision checks
    # ------------------------------------------------------------------

    def _check_weapon_hits(self):
        if not self.current_attack:
            return
        for enemy in list(self.enemy_sprites):
            if enemy.state == enemy.DYING:
                continue
            if self.current_attack.rect.colliderect(enemy.hitbox):
                weapon_dmg = weapon_data.get(self.player.weapon, {}).get('damage', 10)
                old_hp = enemy.hp
                enemy.take_hit(weapon_dmg)
                if enemy.hp <= 0 and old_hp > 0:
                    self.level_kills += 1

    def _check_magic_hits(self):
        for spell in list(self.magic_sprites):
            for enemy in list(self.enemy_sprites):
                if enemy.state == enemy.DYING:
                    continue
                if id(enemy) in spell.hit_enemies:
                    continue
                if spell.hitbox.colliderect(enemy.hitbox):
                    spell_key = getattr(spell, 'spell_key', None)
                    dmg = magic_data.get(spell_key, {}).get('damage', 15) if spell_key else 15
                    old_hp = enemy.hp
                    enemy.take_hit(dmg)
                    if enemy.hp <= 0 and old_hp > 0:
                        self.level_kills += 1
                    spell.hit_enemies.add(id(enemy))
                    if not spell.piercing:
                        spell.kill()
                        break

    def _check_pickup_collisions(self):
        for pickup in list(self.pickup_sprites):
            if pickup.hitbox.colliderect(self.player.hitbox):
                pickup.collect(self.player)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self):
        """Returns a string signal or None.
        'next_level' - player entered portal
        'player_dead' - player HP reached 0
        """
        self.visible_sprites.custom_draw(self.player)
        self.visible_sprites.update()
        self._check_weapon_hits()
        self._check_magic_hits()
        self._check_pickup_collisions()
        self._check_objective()

        # Check portal collision
        if self._check_portal():
            return 'next_level'

        # Check player death
        if not self.player.alive_flag:
            if self.player.death_timer >= self.player.death_duration:
                return 'player_dead'

        # Draw enemy notice indicators
        offset = self.visible_sprites.offset
        for enemy in self.enemy_sprites:
            enemy.draw_notice_indicator(self.display_surface, offset)

        # Draw ring menu
        menu = self.player.circular_menu
        if menu.active:
            screen_center = (
                self.player.rect.centerx - offset.x,
                self.player.rect.centery - offset.y,
            )
            menu.draw(self.display_surface, screen_center)

        # HUD
        self.hud.draw(self.player)

        # Objective display
        self._draw_objective()

        # Level title (fades after 3s)
        self._draw_level_title()

        return None

    # ------------------------------------------------------------------
    # UI overlays
    # ------------------------------------------------------------------

    def _draw_objective(self):
        obj = self.config.get('objective', {})
        desc = obj.get('desc', '')
        if self.objective_complete:
            desc = "Objective complete! Find the portal!"
            color = (100, 255, 140)
        else:
            color = (255, 230, 160)

        text = self._obj_font.render(desc, True, color)
        x = WIDTH // 2 - text.get_width() // 2
        y = 10
        # Background
        bg = pygame.Surface((text.get_width() + 16, text.get_height() + 8), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        self.display_surface.blit(bg, (x - 8, y - 4))
        self.display_surface.blit(text, (x, y))

        # Kill progress for kill_count objectives
        if obj.get('type') == 'kill_count' and not self.objective_complete:
            count = obj.get('count', 0)
            prog = self._obj_font.render(
                f"({self.level_kills}/{count})", True, (200, 200, 180))
            self.display_surface.blit(prog, (x + text.get_width() + 8, y))

    def _draw_level_title(self):
        now = pygame.time.get_ticks()
        if now > self._show_title_until:
            return
        elapsed = now - (self._show_title_until - 3000)
        alpha = 255
        if elapsed > 2000:
            alpha = max(0, int(255 * (1.0 - (elapsed - 2000) / 1000.0)))

        name = self.config.get('name', 'Unknown')
        text = self._title_font.render(name, True, (255, 255, 255))
        text.set_alpha(alpha)
        x = WIDTH // 2 - text.get_width() // 2
        y = HEIGHT // 3
        self.display_surface.blit(text, (x, y))


class YSortCameraGroup(pygame.sprite.Group):
    def __init__(self, floor_path=None):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.half_height = self.display_surface.get_height() // 2
        self.half_width = self.display_surface.get_width() // 2
        self.offset = pygame.math.Vector2(0, 0)

        floor = floor_path or os.path.join('sprites', 'landscape_grass.png')
        self.floor_surf = pygame.image.load(floor).convert()
        self.floor_rect = self.floor_surf.get_rect(topleft=(0, 0))

    def custom_draw(self, player):
        self.offset.x = min(self.floor_rect.width,
                            max(0, player.rect.centerx - self.half_width))
        self.offset.y = min(self.floor_rect.height,
                            max(0, player.rect.centery - self.half_height))

        floor_offset = self.floor_rect.topleft - self.offset
        self.display_surface.blit(self.floor_surf, floor_offset)

        for sprite in sorted(self.sprites(), key=lambda s: s.rect.centery):
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)
