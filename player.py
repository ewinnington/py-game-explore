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

        # --- Hero Stats ---
        self.level = 1
        self.xp = 0
        self.xp_to_next = 20          # XP needed for next level
        self.max_hp = 50
        self.hp = self.max_hp
        self.max_mp = 10
        self.mp = self.max_mp
        self.mp_regen_rate = 0.8       # MP per second
        self._mp_regen_accum = 0.0     # fractional MP accumulator
        self.alive_flag = True         # False when HP <= 0
        self.death_timer = 0
        self.death_duration = 90       # frames for death animation (~1.5s)
        self.kills = 0                 # total kill count
        self.kill_counts = {}          # per-type kill counts e.g. {'demon': 3}

        # --- Knockback (enemy bump) ---
        self.knockback_dir = pygame.math.Vector2(0, 0)
        self.knockback_timer = 0        # frames remaining
        self.knockback_duration = 12    # frames (~0.2 s at 60 fps)
        self.knockback_speed = 14
        self.knockback_invuln = 0       # invulnerability frames remaining
        self.knockback_invuln_time = 36 # frames (~0.6 s)

        # --- Circular ring menu (Secret of Mana style) ---
        # Start with only sword; other items found as runes
        menu_items = [
            {'name': 'Sword', 'icon': weapon_data['sword']['graphic'], 'weapon_key': 'sword'},
        ]
        self.circular_menu = CircularMenu(items=menu_items, radius=80)
        self.circular_menu.item_pool = []

        # Track which runes have been collected
        self.collected_runes = set()  # e.g. {'spear', 'fire_cone', ...}

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

            #magic input – cast the spell selected in the ring menu (costs MP)
            if keys[pygame.K_LCTRL] and not self.attacking:
                mp_cost = magic_data.get(self.magic, {}).get('mp_cost', 0)
                if self.mp >= mp_cost:
                    self.mp -= mp_cost
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

    def take_damage(self, amount):
        """Reduce HP by amount. Called when enemy bumps player."""
        if self.knockback_invuln > 0 or not self.alive_flag:
            return
        self.hp = max(0, self.hp - amount)
        if self.hp <= 0:
            self.alive_flag = False
            self.death_timer = 0

    def heal(self, amount):
        """Restore HP up to max."""
        self.hp = min(self.max_hp, self.hp + amount)

    def gain_xp(self, amount, enemy_type='unknown'):
        """Add XP from a kill, check for level up."""
        self.xp += amount
        self.kills += 1
        self.kill_counts[enemy_type] = self.kill_counts.get(enemy_type, 0) + 1
        while self.xp >= self.xp_to_next:
            self._level_up()

    def _level_up(self):
        """Increase level, boost max HP and MP."""
        self.xp -= self.xp_to_next
        self.level += 1
        self.xp_to_next = int(self.xp_to_next * 1.5)
        # Stat gains per level
        hp_gain = 10
        mp_gain = 3
        self.max_hp += hp_gain
        self.hp = self.max_hp  # full heal on level up
        self.max_mp += mp_gain
        self.mp = self.max_mp  # full MP restore on level up
        print(f"LEVEL UP! Now level {self.level} (HP:{self.max_hp} MP:{self.max_mp})")

    def _regen_mp(self, dt):
        """Regenerate MP over time."""
        if self.mp < self.max_mp:
            self._mp_regen_accum += self.mp_regen_rate * dt
            if self._mp_regen_accum >= 1.0:
                restore = int(self._mp_regen_accum)
                self.mp = min(self.max_mp, self.mp + restore)
                self._mp_regen_accum -= restore

    def apply_knockback(self, direction):
        """Push the player away (called by Enemy on contact)."""
        if self.knockback_invuln > 0 or not self.alive_flag:
            return  # still invincible or dead
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
        if not self.alive_flag:
            self.death_timer += 1
            # Fade out during death
            alpha = max(0, 255 - int(255 * self.death_timer / self.death_duration))
            self.image.set_alpha(alpha)
            return

        self.input()
        self.cooldown()
        self.get_status()
        self.animate()
        self.move(self.speed)
        self._process_knockback()
        self._regen_mp(1.0 / FPS)
        self.circular_menu.update()
