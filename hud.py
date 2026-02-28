import pygame
import math
from data import WIDTH, HEIGHT


class HUD:
    """Bottom-of-screen status bar showing HP, MP, XP, level, portrait, equipped items, armour."""

    BAR_HEIGHT = 52

    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font(None, 20)
        self.font_big = pygame.font.Font(None, 26)
        self._portrait = None  # lazy-built player portrait

    def _get_portrait(self):
        """Build a small portrait card once on first use."""
        if self._portrait is None:
            from player_sprite import build_player_icon
            raw = build_player_icon()
            # Scale to fit inside a 42x42 area
            self._portrait = pygame.transform.smoothscale(raw, (42, 42))
        return self._portrait

    def draw(self, player):
        bar_y = HEIGHT - self.BAR_HEIGHT

        # Background bar
        bg = pygame.Surface((WIDTH, self.BAR_HEIGHT), pygame.SRCALPHA)
        bg.fill((12, 10, 8, 210))
        pygame.draw.line(bg, (100, 85, 55), (0, 0), (WIDTH, 0), 2)
        self.display_surface.blit(bg, (0, bar_y))

        # --- Hero portrait card (left edge) ---
        portrait = self._get_portrait()
        card_x, card_y = 6, bar_y + 4
        card_w, card_h = 48, 46
        # Golden border
        pygame.draw.rect(self.display_surface, (180, 150, 60),
                         (card_x, card_y, card_w, card_h), border_radius=4)
        pygame.draw.rect(self.display_surface, (220, 190, 80),
                         (card_x, card_y, card_w, card_h), 2, border_radius=4)
        # Inner dark background
        inner = pygame.Rect(card_x + 3, card_y + 3, card_w - 6, card_h - 6)
        pygame.draw.rect(self.display_surface, (20, 18, 15), inner)
        # Portrait
        self.display_surface.blit(portrait, portrait.get_rect(center=inner.center))

        # --- Level indicator (right of portrait) ---
        lvl_text = self.font_big.render(f"Lv {player.level}", True, (255, 230, 140))
        self.display_surface.blit(lvl_text, (60, bar_y + 6))

        # --- HP bar ---
        hp_x = 110
        self._draw_bar(hp_x, bar_y + 6, 150, 14,
                       player.hp, player.max_hp,
                       (180, 35, 35), (60, 15, 15), "HP")

        # --- MP bar ---
        self._draw_bar(hp_x, bar_y + 26, 150, 14,
                       player.mp, player.max_mp,
                       (40, 80, 200), (15, 25, 60), "MP")

        # --- XP bar (thin) ---
        xp_x = 290
        self._draw_bar(xp_x, bar_y + 38, 100, 8,
                       player.xp, player.xp_to_next,
                       (180, 160, 40), (50, 45, 15), "XP")

        # --- Kill count ---
        kill_text = self.font.render(f"Kills: {player.kills}", True, (200, 190, 160))
        self.display_surface.blit(kill_text, (400, bar_y + 8))

        # --- Equipped weapon icon (center area) ---
        from player import weapon_data
        weap = weapon_data.get(player.weapon)
        equip_x = WIDTH // 2 - 60
        if weap:
            label = self.font.render("WPN", True, (160, 150, 120))
            self.display_surface.blit(label, (equip_x, bar_y + 4))
            icon = weap['graphic']
            scaled = pygame.transform.scale(icon, (28, 28))
            self.display_surface.blit(scaled, (equip_x + 36, bar_y + 2))

        # --- Equipped spell icon (center area, right of weapon) ---
        from magic import magic_data
        spell = magic_data.get(player.magic)
        spell_x = WIDTH // 2 + 20
        if spell and player.magic in player.collected_runes:
            label = self.font.render("MAG", True, (120, 130, 180))
            self.display_surface.blit(label, (spell_x, bar_y + 4))
            icon = spell.get('icon')
            if icon:
                scaled = pygame.transform.scale(icon, (28, 28))
                self.display_surface.blit(scaled, (spell_x + 36, bar_y + 2))

        # --- Armour indicator (right side) ---
        if player.armour > 0:
            ar_x = WIDTH - 100
            # Small shield icon
            shield_pts = [
                (ar_x + 8, bar_y + 6),
                (ar_x + 20, bar_y + 6),
                (ar_x + 22, bar_y + 16),
                (ar_x + 14, bar_y + 26),
                (ar_x + 6, bar_y + 16),
            ]
            pygame.draw.polygon(self.display_surface, (140, 150, 170), shield_pts)
            pygame.draw.polygon(self.display_surface, (180, 190, 210), shield_pts, 2)
            # Cross on shield
            pygame.draw.line(self.display_surface, (210, 215, 225),
                             (ar_x + 14, bar_y + 8), (ar_x + 14, bar_y + 22), 2)
            pygame.draw.line(self.display_surface, (210, 215, 225),
                             (ar_x + 9, bar_y + 14), (ar_x + 19, bar_y + 14), 2)
            # Text
            ar_text = self.font.render(f"AR {player.armour}", True, (180, 190, 210))
            self.display_surface.blit(ar_text, (ar_x + 26, bar_y + 10))

    def _draw_bar(self, x, y, w, h, current, maximum, fill_color, bg_color, label):
        """Draw a labeled resource bar."""
        lbl = self.font.render(label, True, (180, 170, 140))
        self.display_surface.blit(lbl, (x, y))
        bx = x + 24

        # Background
        pygame.draw.rect(self.display_surface, bg_color, (bx, y, w, h), border_radius=3)
        # Fill
        ratio = max(0, min(1, current / max(1, maximum)))
        fw = int(w * ratio)
        if fw > 0:
            pygame.draw.rect(self.display_surface, fill_color, (bx, y, fw, h), border_radius=3)
        # Border
        pygame.draw.rect(self.display_surface, (120, 110, 80), (bx, y, w, h), 1, border_radius=3)
        # Value text
        val = self.font.render(f"{int(current)}/{int(maximum)}", True, (255, 255, 255))
        val_rect = val.get_rect(center=(bx + w // 2, y + h // 2))
        self.display_surface.blit(val, val_rect)
