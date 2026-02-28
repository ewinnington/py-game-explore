import pygame
import math
from data import WIDTH, HEIGHT


class HUD:
    """Bottom-of-screen status bar showing HP, MP, XP, level, and equipped items."""

    BAR_HEIGHT = 52

    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font(None, 20)
        self.font_big = pygame.font.Font(None, 26)

    def draw(self, player):
        bar_y = HEIGHT - self.BAR_HEIGHT

        # Background bar
        bg = pygame.Surface((WIDTH, self.BAR_HEIGHT), pygame.SRCALPHA)
        bg.fill((12, 10, 8, 210))
        pygame.draw.line(bg, (100, 85, 55), (0, 0), (WIDTH, 0), 2)
        self.display_surface.blit(bg, (0, bar_y))

        # --- Level indicator ---
        lvl_text = self.font_big.render(f"Lv {player.level}", True, (255, 230, 140))
        self.display_surface.blit(lvl_text, (12, bar_y + 6))

        # --- HP bar ---
        hp_x = 80
        self._draw_bar(hp_x, bar_y + 6, 160, 14,
                       player.hp, player.max_hp,
                       (180, 35, 35), (60, 15, 15), "HP")

        # --- MP bar ---
        mp_x = 80
        self._draw_bar(mp_x, bar_y + 26, 160, 14,
                       player.mp, player.max_mp,
                       (40, 80, 200), (15, 25, 60), "MP")

        # --- XP bar (thin, below HP/MP) ---
        xp_x = 250
        self._draw_bar(xp_x, bar_y + 38, 120, 8,
                       player.xp, player.xp_to_next,
                       (180, 160, 40), (50, 45, 15), "XP")

        # --- Equipped weapon icon ---
        from player import weapon_data
        weap = weapon_data.get(player.weapon)
        equip_x = WIDTH - 120
        if weap:
            label = self.font.render("WPN", True, (160, 150, 120))
            self.display_surface.blit(label, (equip_x, bar_y + 4))
            icon = weap['graphic']
            scaled = pygame.transform.scale(icon, (28, 28))
            self.display_surface.blit(scaled, (equip_x + 36, bar_y + 2))

        # --- Equipped spell icon ---
        from magic import magic_data
        spell = magic_data.get(player.magic)
        spell_x = WIDTH - 56
        if spell and player.magic in player.collected_runes:
            label = self.font.render("MAG", True, (120, 130, 180))
            self.display_surface.blit(label, (spell_x, bar_y + 4))
            icon = spell.get('icon')
            if icon:
                scaled = pygame.transform.scale(icon, (28, 28))
                self.display_surface.blit(scaled, (spell_x + 36, bar_y + 2))

        # --- Kill count ---
        kill_text = self.font.render(f"Kills: {player.kills}", True, (200, 190, 160))
        self.display_surface.blit(kill_text, (390, bar_y + 8))

    def _draw_bar(self, x, y, w, h, current, maximum, fill_color, bg_color, label):
        """Draw a labeled resource bar."""
        # Label
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
