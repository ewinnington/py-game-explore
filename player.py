import pygame
import os
from data import *
from support import *
from circular_menu import CircularMenu
from magic import magic_data

weapon_data = {
    'sword': { 'cooldown':100, 'damage':10, 'graphic': pygame.image.load(os.path.join('sprites','weapons','sword','full.png')) },
    'spear': { 'cooldown':120, 'damage':10, 'graphic': pygame.image.load(os.path.join('sprites','weapons','spear','full.png')) },
}


def _make_placeholder_icon(label, color, size=32):
    """Generate a simple colored placeholder icon with a letter."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(surf, color, (0, 0, size, size), border_radius=6)
    # Subtle highlight on top half
    highlight = pygame.Surface((size, size // 3), pygame.SRCALPHA)
    highlight.fill((255, 255, 255, 35))
    surf.blit(highlight, (0, 0))
    # Letter
    font = pygame.font.Font(None, 22)
    letter = font.render(label[0].upper(), True, (255, 255, 255))
    surf.blit(letter, letter.get_rect(center=(size // 2, size // 2)))
    return surf


class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites,
                 create_attack, destroy_weapon, create_magic):
        super().__init__(groups)
        self.image = pygame.image.load(os.path.join('sprites','player.png')).convert_alpha()
        self.image.set_colorkey(COLORKEY)
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

        self.create_attack = create_attack
        self.destroy_weapon = destroy_weapon
        self.weapon_index = 0
        self.weapon = list(weapon_data.keys())[self.weapon_index]
        self.can_switch_weapon = True
        self.weapon_switch_time = None
        self.switch_duration_cooldown = 200

        # --- Magic ---
        self.create_magic = create_magic
        self.magic = 'fire_cone'
        self.casting_magic = False

        # --- Knockback (enemy bump) ---
        self.knockback_dir = pygame.math.Vector2(0, 0)
        self.knockback_timer = 0        # frames remaining
        self.knockback_duration = 12    # frames (~0.2 s at 60 fps)
        self.knockback_speed = 14
        self.knockback_invuln = 0       # invulnerability frames remaining
        self.knockback_invuln_time = 36 # frames (~0.6 s)

        # --- Circular ring menu (Secret of Mana style) ---
        menu_items = [
            {'name': 'Sword',        'icon': weapon_data['sword']['graphic'], 'weapon_key': 'sword'},
            {'name': 'Spear',        'icon': weapon_data['spear']['graphic'], 'weapon_key': 'spear'},
            {'name': 'Fire Cone',    'icon': magic_data['fire_cone']['icon'],    'magic_key': 'fire_cone'},
            {'name': 'Ice Ball',     'icon': magic_data['ice_ball']['icon'],     'magic_key': 'ice_ball'},
            {'name': 'Shadow Blade', 'icon': magic_data['shadow_blade']['icon'], 'magic_key': 'shadow_blade'},
        ]
        self.circular_menu = CircularMenu(items=menu_items, radius=80)
        self.circular_menu.item_pool = [
            {'name': 'Shield', 'icon': _make_placeholder_icon('Shield', (70, 95, 170))},
            {'name': 'Potion', 'icon': _make_placeholder_icon('Potion', (55, 150, 75))},
        ]

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

        # Flash during knockback invulnerability
        if self.knockback_invuln > 0:
            if (self.knockback_invuln // 4) % 2 == 0:
                self.image.set_alpha(80)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

    def input(self):
        keys = pygame.key.get_pressed()

        # --- Ring menu controls ---
        # TAB held = menu open, TAB released = menu closes
        if keys[pygame.K_TAB]:
            if not self.circular_menu.active:
                self.circular_menu.open()
        else:
            # TAB released
            if self.circular_menu.active:
                self.circular_menu.close()
            # Reset dismiss lock so menu can reopen on next TAB press
            self.circular_menu.dismissed_by_select = False

        if self.circular_menu.active:
            # Freeze player movement while menu is up
            self.direction.x = 0
            self.direction.y = 0

            if self.circular_menu.is_interactive:
                # Navigate ring
                if keys[pygame.K_LEFT]:
                    self.circular_menu.navigate_left()
                if keys[pygame.K_RIGHT]:
                    self.circular_menu.navigate_right()

                # Add / remove items
                if keys[pygame.K_UP]:
                    self.circular_menu.add_item()
                if keys[pygame.K_DOWN]:
                    self.circular_menu.remove_item()

                # Select current item
                if keys[pygame.K_SPACE]:
                    selected = self.circular_menu.select()
                    if selected:
                        if selected.get('weapon_key'):
                            weapon_key = selected['weapon_key']
                            if weapon_key in weapon_data:
                                self.weapon_index = list(weapon_data.keys()).index(weapon_key)
                                self.weapon = weapon_key
                        elif selected.get('magic_key'):
                            self.magic = selected['magic_key']
            return  # skip normal input while menu is active

        # --- Normal gameplay input ---
        if not self.attacking:
            self.direction.x = 0
            self.direction.y = 0

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
                self.create_attack()

            #magic input – cast the spell selected in the ring menu
            if keys[pygame.K_LCTRL] and not self.attacking:
                self.attacking = True
                self.casting_magic = True
                self.attack_time = pygame.time.get_ticks()
                self.create_magic()

            if keys[pygame.K_RCTRL] and not self.attacking and self.can_switch_weapon:
                self.can_switch_weapon = False
                self.weapon_switch_time = pygame.time.get_ticks()
                self.weapon_index += 1
                if self.weapon_index >= len(weapon_data):
                    self.weapon_index = 0
                self.weapon = list(weapon_data.keys())[self.weapon_index]

    def cooldown(self):
        current_time = pygame.time.get_ticks()
        if self.attacking:
            if self.casting_magic:
                cd = magic_data[self.magic]['cooldown']
            else:
                cd = self.attack_cooldown
            if (current_time - self.attack_time) > cd:
                self.attacking = False
                self.attack_time = None
                if not self.casting_magic:
                    self.destroy_weapon()
                self.casting_magic = False
        if not self.can_switch_weapon:
            if (current_time - self.weapon_switch_time) > self.switch_duration_cooldown:
                self.can_switch_weapon = True
                self.weapon_switch_time = None

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

    def apply_knockback(self, direction):
        """Push the player away (called by Enemy on contact)."""
        if self.knockback_invuln > 0:
            return  # still invincible
        self.knockback_dir = direction
        self.knockback_timer = self.knockback_duration
        self.knockback_invuln = self.knockback_invuln_time

    def _process_knockback(self):
        """Apply knockback movement and tick invulnerability."""
        if self.knockback_timer > 0:
            self.knockback_timer -= 1
            self.hitbox.x += self.knockback_dir.x * self.knockback_speed
            self.collision('horizontal')
            self.hitbox.y += self.knockback_dir.y * self.knockback_speed
            self.collision('vertical')
            self.rect.center = self.hitbox.center
        if self.knockback_invuln > 0:
            self.knockback_invuln -= 1

    def update(self):
        self.input()
        self.cooldown()
        self.get_status()
        self.animate()
        self.move(self.speed)
        self._process_knockback()
        self.circular_menu.update()
