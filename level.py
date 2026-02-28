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
from pickup import RunePickup, HealthPickup, ArmourPickup
from portal import Portal
from sounds import SoundManager
from tile_graphics import make_floor_surface, make_rock, make_grass_tuft, make_column, make_chainmail_stand

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
        self.theme = level_config.get('theme', 'meadow')

        # Sprite groups
        self.visible_sprites = YSortCameraGroup(
            floor_path=level_config.get('floor'),
            theme=self.theme,
        )
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
        SoundManager.get().play('sword_hit')

    def destroy_weapon(self):
        if self.current_attack:
            self.current_attack.kill()
        self.current_attack = None

    def create_magic(self):
        key = self.player.magic
        groups = [self.visible_sprites, self.magic_sprites]
        SoundManager.get().play('spell_cast')
        if key == 'fire_cone':
            FireCone(self.player, groups)
        elif key == 'ice_ball':
            IceBall(self.player, groups)
        elif key == 'shadow_blade':
            ShadowBlade(self.player, groups, self.enemy_sprites)

    def create_map(self):
        cfg = self.config
        csv_paths = cfg['map_csv']
        theme = self.theme

        layout = {
            'boundary': import_csv_layout(csv_paths['boundary']),
            'rocks':    import_csv_layout(csv_paths['rocks']),
            'grass':    import_csv_layout(csv_paths['grass']),
            'object':   import_csv_layout(csv_paths['object']),
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
                            rock_img = make_rock(theme)
                            Tile((x, y), [self.visible_sprites], 'rocks', rock_img)
                        if style == 'grass':
                            grass_img = make_grass_tuft(theme)
                            Tile((x, y), [self.visible_sprites, self.obstacle_sprites],
                                 'grass', grass_img)
                        if style == 'object':
                            col_val = int(col)
                            if col_val == 1:
                                col_img = make_column(theme)
                                Tile((x, y),
                                     [self.visible_sprites, self.obstacle_sprites],
                                     'sceneryObject', col_img)
                            else:
                                stand_img = make_chainmail_stand()
                                Tile((x, y), [self.visible_sprites],
                                     'object', stand_img)

        # --- Player ---
        if self._existing_player:
            self.player = self._existing_player
            self.player.rect.topleft = cfg['player_pos']
            self.player.hitbox.center = self.player.rect.center
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
                    num_segments=7)
            else:
                cls(pos, enemy_groups, self.obstacle_sprites, self.player)

        # --- Pickups ---
        pickup_groups = [self.visible_sprites, self.pickup_sprites]
        for ptype, pos in cfg.get('pickups', []):
            clear_pos = self._find_clear_pos(pos)
            if ptype.startswith('rune_'):
                rune_info = _RUNE_MAP.get(ptype)
                if rune_info:
                    rune_type, icon_fn = rune_info
                    if self._existing_player and rune_type in self._existing_player.collected_runes:
                        continue
                    RunePickup(clear_pos, pickup_groups, rune_type, icon=icon_fn())
            elif ptype == 'health':
                HealthPickup(clear_pos, pickup_groups, heal_amount=20)
            elif ptype == 'chainmail':
                if self._existing_player and self._existing_player.has_chainmail:
                    continue
                ArmourPickup(clear_pos, pickup_groups)

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

    def _find_clear_pos(self, pos, margin=20):
        """Return pos or nearest clear position that doesn't overlap obstacles."""
        test = pygame.Rect(0, 0, 32, 32)
        test.center = pos
        if not any(test.colliderect(s.hitbox) for s in self.obstacle_sprites):
            return pos
        for dist in range(TILESIZE, TILESIZE * 5, TILESIZE // 2):
            for dx, dy in [(dist, 0), (-dist, 0), (0, dist), (0, -dist),
                           (dist, dist), (-dist, dist), (dist, -dist), (-dist, -dist)]:
                test.center = (pos[0] + dx, pos[1] + dy)
                if not any(test.colliderect(s.hitbox) for s in self.obstacle_sprites):
                    return (pos[0] + dx, pos[1] + dy)
        return pos

    # ------------------------------------------------------------------
    # Objective checking
    # ------------------------------------------------------------------

    def _check_objective(self):
        if self.objective_complete:
            return
        obj = self.config.get('objective', {})
        otype = obj.get('type', 'kill_all')

        if otype == 'kill_all':
            alive = sum(1 for e in self.enemy_sprites if e.state != e.DYING)
            if alive == 0 and self.level_kills > 0:
                self._complete_objective()

        elif otype == 'kill_count':
            if self.level_kills >= obj.get('count', 10):
                self._complete_objective()

    def _complete_objective(self):
        self.objective_complete = True
        SoundManager.get().play('portal')
        portal_pos = self.config.get('portal_pos', (640, 360))
        self.portal = Portal(portal_pos, [self.visible_sprites])

    def _check_portal(self):
        if self.portal and self.portal.hitbox.colliderect(self.player.hitbox):
            return True
        return False

    # ------------------------------------------------------------------
    # Collision checks
    # ------------------------------------------------------------------

    def _check_weapon_hits(self):
        if not self.current_attack:
            return
        snd = SoundManager.get()
        for enemy in list(self.enemy_sprites):
            if enemy.state == enemy.DYING:
                continue
            if self.current_attack.rect.colliderect(enemy.hitbox):
                weapon_dmg = weapon_data.get(self.player.weapon, {}).get('damage', 10)
                old_hp = enemy.hp
                enemy.take_hit(weapon_dmg)
                if enemy.hp <= 0 and old_hp > 0:
                    self.level_kills += 1
                    snd.play('enemy_death')
                else:
                    snd.play('enemy_hit')

    def _check_magic_hits(self):
        snd = SoundManager.get()
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
                        snd.play('enemy_death')
                    else:
                        snd.play('enemy_hit')
                    spell.hit_enemies.add(id(enemy))
                    if not spell.piercing:
                        spell.kill()
                        break

    def _check_pickup_collisions(self):
        for pickup in list(self.pickup_sprites):
            if pickup.hitbox.colliderect(self.player.hitbox):
                result = pickup.collect(self.player)
                if result is not False:
                    SoundManager.get().play('pickup')

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self):
        """Returns a string signal or None."""
        self.visible_sprites.custom_draw(self.player)
        self.visible_sprites.update()
        self._check_weapon_hits()
        self._check_magic_hits()
        self._check_pickup_collisions()
        self._check_objective()

        if self._check_portal():
            return 'next_level'

        if not self.player.alive_flag:
            if self.player.death_timer >= self.player.death_duration:
                return 'player_dead'

        offset = self.visible_sprites.offset
        for enemy in self.enemy_sprites:
            enemy.draw_notice_indicator(self.display_surface, offset)

        menu = self.player.circular_menu
        if menu.active:
            screen_center = (
                self.player.rect.centerx - offset.x,
                self.player.rect.centery - offset.y,
            )
            menu.draw(self.display_surface, screen_center)

        self.hud.draw(self.player)
        self._draw_objective()
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
        bg = pygame.Surface((text.get_width() + 16, text.get_height() + 8), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        self.display_surface.blit(bg, (x - 8, y - 4))
        self.display_surface.blit(text, (x, y))

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
    def __init__(self, floor_path=None, theme='meadow'):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.half_height = self.display_surface.get_height() // 2
        self.half_width = self.display_surface.get_width() // 2
        self.offset = pygame.math.Vector2(0, 0)

        if floor_path:
            self.floor_surf = pygame.image.load(floor_path).convert()
        else:
            self.floor_surf = make_floor_surface(theme, 20 * TILESIZE, 20 * TILESIZE)
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
