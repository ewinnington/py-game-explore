import pygame
import os
from data import *
from support import *
from dual_ring_menu import DualRingMenu
from magic import magic_data
from sounds import SoundManager
from player_sprite import build_player_animations, build_player_icon
from weapon_sprites import make_weapon_icon

weapon_data = {
    'sword': { 'cooldown':100, 'damage':10, 'graphic': make_weapon_icon('sword') },
    'spear': { 'cooldown':120, 'damage':10, 'graphic': make_weapon_icon('spear') },
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
        self.image = build_player_icon()
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
        self.armour = 0                # damage reduction (chainmail = 1)
        self.has_chainmail = False     # whether chainmail has been picked up

        # --- Knockback (enemy bump) ---
        self.knockback_dir = pygame.math.Vector2(0, 0)
        self.knockback_timer = 0        # frames remaining
        self.knockback_duration = 12    # frames (~0.2 s at 60 fps)
        self.knockback_speed = 14
        self.knockback_invuln = 0       # invulnerability frames remaining
        self.knockback_invuln_time = 36 # frames (~0.6 s)

        # --- Dual ring menu (Secret of Mana style) ---
        # Start with only sword; other items found as runes
        weapon_items = [
            {'name': 'Sword', 'icon': weapon_data['sword']['graphic'], 'weapon_key': 'sword'},
        ]
        self.circular_menu = DualRingMenu(
            weapon_items=weapon_items,
            magic_items=[],   # empty until player finds magic runes
            radius=80,
        )

        # Track which runes have been collected
        self.collected_runes = set()  # e.g. {'spear', 'fire_cone', ...}

        # --- Gamepad ---
        self.joystick = None
        self._prev_gp = {}  # previous frame button state for edge detection
        self._init_joystick()

    def _init_joystick(self):
        """Detect and initialize the first available gamepad."""
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Gamepad detected: {self.joystick.get_name()}")

    def import_player_assets(self):
        self.animations = build_player_animations()

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

    def _read_gamepad(self):
        """Read gamepad state, return (move_x, move_y, attack, magic, menu, left, right, up, down, select)."""
        if not self.joystick:
            return 0, 0, False, False, False, False, False, False, False, False

        # Left stick or D-pad
        deadzone = 0.3
        ax_x = self.joystick.get_axis(0)  # left stick X
        ax_y = self.joystick.get_axis(1)  # left stick Y
        move_x = ax_x if abs(ax_x) > deadzone else 0
        move_y = ax_y if abs(ax_y) > deadzone else 0

        # D-pad (hat)
        if self.joystick.get_numhats() > 0:
            hat = self.joystick.get_hat(0)
            if hat[0] != 0:
                move_x = hat[0]
            if hat[1] != 0:
                move_y = -hat[1]  # hat Y is inverted

        # Buttons (standard Logitech mapping)
        # Button 0 = A (attack), 1 = B (magic), 2 = X (menu), 3 = Y (select)
        # Button 4 = L1 (switch ring up), 5 = R1 (switch ring down)
        num_buttons = self.joystick.get_numbuttons()
        btn = lambda i: self.joystick.get_button(i) if i < num_buttons else False

        attack = btn(0)        # A = attack
        magic = btn(1)         # B = magic
        menu = btn(2)          # X = open menu

        # Edge-detect menu buttons (only fire on rising edge: was False, now True)
        raw_select = btn(3)    # Y = select in menu
        raw_left = btn(4)      # L1 = navigate left
        raw_right = btn(5)     # R1 = navigate right

        select = raw_select and not self._prev_gp.get(3, False)
        pad_left = raw_left and not self._prev_gp.get(4, False)
        pad_right = raw_right and not self._prev_gp.get(5, False)

        # Store current state for next frame
        self._prev_gp[3] = raw_select
        self._prev_gp[4] = raw_left
        self._prev_gp[5] = raw_right

        return move_x, move_y, attack, magic, menu, pad_left, pad_right, False, False, select

    def input(self):
        keys = pygame.key.get_pressed()
        gp_mx, gp_my, gp_attack, gp_magic, gp_menu, gp_left, gp_right, gp_up, gp_down, gp_select = self._read_gamepad()

        # --- Ring menu controls ---
        # TAB or gamepad X = menu toggle
        menu_btn = keys[pygame.K_TAB] or gp_menu
        if menu_btn:
            if not self.circular_menu.active:
                self.circular_menu.open()
        else:
            if self.circular_menu.active:
                self.circular_menu.close()
            self.circular_menu.dismissed_by_select = False

        if self.circular_menu.active:
            self.direction.x = 0
            self.direction.y = 0

            if self.circular_menu.is_interactive:
                # Navigate within current ring
                if keys[pygame.K_LEFT] or gp_left:
                    self.circular_menu.navigate_left()
                if keys[pygame.K_RIGHT] or gp_right:
                    self.circular_menu.navigate_right()

                # Switch between weapon/magic rings (use D-pad up/down or stick)
                if keys[pygame.K_UP] or gp_my < -0.5:
                    self.circular_menu.switch_ring_up()
                if keys[pygame.K_DOWN] or gp_my > 0.5:
                    self.circular_menu.switch_ring_down()

                # Select current item
                if keys[pygame.K_SPACE] or gp_select:
                    selected = self.circular_menu.select()
                    if selected:
                        if selected.get('weapon_key'):
                            weapon_key = selected['weapon_key']
                            if weapon_key in weapon_data:
                                self.weapon_index = list(weapon_data.keys()).index(weapon_key)
                                self.weapon = weapon_key
                        elif selected.get('magic_key'):
                            self.magic = selected['magic_key']
            return

        # --- Normal gameplay input ---
        if not self.attacking:
            self.direction.x = 0
            self.direction.y = 0

            # Movement: keyboard or gamepad
            if keys[pygame.K_LEFT] or gp_mx < -0.3:
                self.direction.x = -1
                self.status = 'left'
            if keys[pygame.K_RIGHT] or gp_mx > 0.3:
                self.direction.x = 1
                self.status = 'right'
            if keys[pygame.K_UP] or gp_my < -0.3:
                self.direction.y = -1
                self.status = 'up'
            if keys[pygame.K_DOWN] or gp_my > 0.3:
                self.direction.y = 1
                self.status = 'down'

            # Attack: Space or gamepad A
            if (keys[pygame.K_SPACE] or gp_attack) and not self.attacking:
                self.attacking = True
                self.attack_time = pygame.time.get_ticks()
                self.create_attack()

            # Magic: LCtrl or gamepad B
            if (keys[pygame.K_LCTRL] or gp_magic) and not self.attacking and self.magic in self.collected_runes:
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
        effective = max(1, amount - self.armour)
        self.hp = max(0, self.hp - effective)
        SoundManager.get().play('player_hurt')
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

    def collect_rune(self, rune_type):
        """Add a weapon or spell to the appropriate ring menu."""
        if rune_type in self.collected_runes:
            return  # already have it
        self.collected_runes.add(rune_type)

        if rune_type in weapon_data:
            self.circular_menu.add_weapon({
                'name': rune_type.capitalize(),
                'icon': weapon_data[rune_type]['graphic'],
                'weapon_key': rune_type,
            })
        elif rune_type in magic_data:
            self.circular_menu.add_magic({
                'name': magic_data[rune_type].get('name', rune_type.replace('_', ' ').title()),
                'icon': magic_data[rune_type]['icon'],
                'magic_key': rune_type,
            })
            # Set as active magic if it's the first one
            if self.magic not in self.collected_runes or not any(
                r in self.collected_runes for r in magic_data if r != rune_type
            ):
                self.magic = rune_type
        print(f"Collected rune: {rune_type}!")

    def _level_up(self):
        """Increase level, boost max HP and MP."""
        SoundManager.get().play('level_up')
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
            # Move in small steps to prevent clipping through walls
            steps = max(1, int(self.knockback_speed / 4))
            step_size = self.knockback_speed / steps
            for _ in range(steps):
                self.hitbox.x += self.knockback_dir.x * step_size
                self.collision('horizontal')
                self.hitbox.y += self.knockback_dir.y * step_size
                self.collision('vertical')
            self.rect.center = self.hitbox.center
        if self.knockback_invuln > 0:
            self.knockback_invuln -= 1

    def _clamp_to_world(self):
        """Ensure player is always within the playable area. Runs every frame."""
        margin = TILESIZE + 4
        world = pygame.Rect(margin, margin,
                            20 * TILESIZE - 2 * margin,
                            20 * TILESIZE - 2 * margin)
        clamped = False
        if self.hitbox.left < world.left:
            self.hitbox.left = world.left
            clamped = True
        if self.hitbox.right > world.right:
            self.hitbox.right = world.right
            clamped = True
        if self.hitbox.top < world.top:
            self.hitbox.top = world.top
            clamped = True
        if self.hitbox.bottom > world.bottom:
            self.hitbox.bottom = world.bottom
            clamped = True
        if clamped:
            self.rect.center = self.hitbox.center

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
        self._clamp_to_world()
        self._regen_mp(1.0 / FPS)
        self.circular_menu.update()
