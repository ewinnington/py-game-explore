import pygame
import math
from data import WIDTH, HEIGHT, FPS
from level import Level
from level_data import LEVELS
from sounds import SoundManager


class GameState:
    """Manages game states: title, gameplay, level_transition, game_over, victory."""

    TITLE = 'title'
    GAMEPLAY = 'gameplay'
    LEVEL_TRANSITION = 'level_transition'
    GAME_OVER = 'game_over'
    VICTORY = 'victory'

    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.state = self.TITLE
        self.current_level_index = 0
        self.level = None
        self.player = None

        # Fonts
        self._title_font = pygame.font.Font(None, 64)
        self._subtitle_font = pygame.font.Font(None, 28)
        self._prompt_font = pygame.font.Font(None, 24)

        # Transition timer
        self._transition_start = 0
        self._transition_duration = 2000  # ms
        self._next_level_index = 0

        # Prevent input bounce
        self._last_key_time = 0

        # Story crawl (lazy init after idle on title screen)
        self._title_enter_tick = 0
        self._crawl = None

        # Gamepad
        pygame.joystick.init()
        self._joystick = None
        if pygame.joystick.get_count() > 0:
            self._joystick = pygame.joystick.Joystick(0)
            self._joystick.init()

    def _start_level(self, level_index):
        """Initialize a level from LEVELS data."""
        self.current_level_index = level_index
        cfg = LEVELS[level_index]
        self.level = Level(cfg, player=self.player)
        self.player = self.level.player
        self.state = self.GAMEPLAY
        SoundManager.get().start_bgm()

    def update(self):
        """Call once per frame. Returns False to quit."""
        if self.state == self.TITLE:
            return self._update_title()
        elif self.state == self.GAMEPLAY:
            return self._update_gameplay()
        elif self.state == self.LEVEL_TRANSITION:
            return self._update_transition()
        elif self.state == self.GAME_OVER:
            return self._update_game_over()
        elif self.state == self.VICTORY:
            return self._update_victory()
        return True

    # ------------------------------------------------------------------
    # Title screen
    # ------------------------------------------------------------------

    def _update_title(self):
        self.display_surface.fill((8, 6, 12))

        tick = pygame.time.get_ticks()

        # Initialize crawl timer on first frame of title state
        if self._title_enter_tick == 0:
            self._title_enter_tick = tick

        # After 5 seconds idle, activate story crawl
        crawl_active = tick - self._title_enter_tick > 5000
        if crawl_active:
            if self._crawl is None:
                from title_crawl import TitleCrawl
                self._crawl = TitleCrawl()
            self._crawl.update()
            self._crawl.draw(self.display_surface)

        # Calculate fade alpha — once crawl starts, fade text to ~40% over 2s
        if crawl_active:
            crawl_elapsed = tick - self._title_enter_tick - 5000
            fade_alpha = max(100, 255 - int(155 * min(1.0, crawl_elapsed / 2000.0)))
        else:
            fade_alpha = 255

        # Semi-transparent overlay behind title area for readability
        if crawl_active:
            overlay = pygame.Surface((WIDTH, 100), pygame.SRCALPHA)
            overlay.fill((8, 6, 12, int(180 * fade_alpha / 255)))
            self.display_surface.blit(overlay, (0, HEIGHT // 3 - 40))

        # Title
        title = self._title_font.render("DemoBlade", True, (255, 210, 60))
        title.set_alpha(fade_alpha)
        self.display_surface.blit(title,
            title.get_rect(center=(WIDTH // 2, HEIGHT // 3)))

        # Subtitle
        sub = self._subtitle_font.render("A Secret of Mana Tribute", True, (180, 160, 120))
        sub.set_alpha(fade_alpha)
        self.display_surface.blit(sub,
            sub.get_rect(center=(WIDTH // 2, HEIGHT // 3 + 50)))

        # Prompt (blinking)
        if (tick // 600) % 2 == 0:
            prompt = self._prompt_font.render("Press SPACE or A to begin", True, (200, 200, 180))
            prompt.set_alpha(fade_alpha)
            self.display_surface.blit(prompt,
                prompt.get_rect(center=(WIDTH // 2, HEIGHT * 2 // 3)))

        # Controls hint
        hints = [
            "Arrow keys: Move    Space: Attack    LCtrl: Cast spell",
            "TAB: Open ring menu    UP/DOWN: Switch rings    LEFT/RIGHT: Navigate",
            "Gamepad: Stick/D-pad: Move  A: Attack  B: Magic  X: Menu  Y: Select",
        ]
        for i, h in enumerate(hints):
            ht = self._prompt_font.render(h, True, (120, 110, 100))
            ht.set_alpha(fade_alpha)
            self.display_surface.blit(ht,
                ht.get_rect(center=(WIDTH // 2, HEIGHT * 2 // 3 + 50 + i * 24)))

        # Decorative border (fades with text)
        self._draw_border((180, 150, 80), fade_alpha)

        if self._confirm_pressed():
            self._start_level(0)

        return True

    # ------------------------------------------------------------------
    # Gameplay
    # ------------------------------------------------------------------

    def _update_gameplay(self):
        signal = self.level.run()

        if signal == 'next_level':
            next_idx = self.level.config.get('next_level')
            if next_idx is not None and next_idx < len(LEVELS):
                self._next_level_index = next_idx
                self._transition_start = pygame.time.get_ticks()
                self.state = self.LEVEL_TRANSITION
            else:
                SoundManager.get().stop_bgm()
                self.state = self.VICTORY
        elif signal == 'player_dead':
            SoundManager.get().stop_bgm()
            self.state = self.GAME_OVER

        return True

    # ------------------------------------------------------------------
    # Level transition
    # ------------------------------------------------------------------

    def _update_transition(self):
        elapsed = pygame.time.get_ticks() - self._transition_start
        progress = min(1.0, elapsed / self._transition_duration)

        # Fade to black
        self.display_surface.fill((8, 6, 12))

        if progress < 0.5:
            # Show "Level Complete" fading out
            alpha = int(255 * (1.0 - progress * 2))
            name = LEVELS[self.current_level_index].get('name', '')
            text = self._subtitle_font.render(f"{name} - Complete!", True, (100, 255, 140))
            text.set_alpha(alpha)
            self.display_surface.blit(text,
                text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        else:
            # Show next level name fading in
            alpha = int(255 * ((progress - 0.5) * 2))
            name = LEVELS[self._next_level_index].get('name', '')
            text = self._subtitle_font.render(name, True, (255, 230, 160))
            text.set_alpha(alpha)
            self.display_surface.blit(text,
                text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        if elapsed >= self._transition_duration:
            self._start_level(self._next_level_index)

        return True

    # ------------------------------------------------------------------
    # Game Over
    # ------------------------------------------------------------------

    def _update_game_over(self):
        self.display_surface.fill((20, 5, 5))

        title = self._title_font.render("Game Over", True, (200, 40, 40))
        self.display_surface.blit(title,
            title.get_rect(center=(WIDTH // 2, HEIGHT // 3)))

        # Stats
        if self.player:
            stats = [
                f"Level reached: {self.player.level}",
                f"Total kills: {self.player.kills}",
                f"Stage: {LEVELS[self.current_level_index].get('name', '?')}",
            ]
            for i, s in enumerate(stats):
                st = self._prompt_font.render(s, True, (180, 150, 140))
                self.display_surface.blit(st,
                    st.get_rect(center=(WIDTH // 2, HEIGHT // 2 + i * 28)))

        # Prompt
        tick = pygame.time.get_ticks()
        if (tick // 600) % 2 == 0:
            prompt = self._prompt_font.render("Press SPACE to try again", True, (200, 180, 160))
            self.display_surface.blit(prompt,
                prompt.get_rect(center=(WIDTH // 2, HEIGHT * 3 // 4)))

        self._draw_border((120, 30, 30))

        if self._confirm_pressed():
            self.player = None
            self._title_enter_tick = 0
            self._crawl = None
            self.state = self.TITLE

        return True

    # ------------------------------------------------------------------
    # Victory
    # ------------------------------------------------------------------

    def _update_victory(self):
        self.display_surface.fill((5, 10, 20))

        title = self._title_font.render("Victory!", True, (255, 230, 80))
        self.display_surface.blit(title,
            title.get_rect(center=(WIDTH // 2, HEIGHT // 4)))

        sub = self._subtitle_font.render("You have vanquished all evil!", True, (200, 200, 180))
        self.display_surface.blit(sub,
            sub.get_rect(center=(WIDTH // 2, HEIGHT // 4 + 50)))

        # Stats
        if self.player:
            stats = [
                f"Hero Level: {self.player.level}",
                f"Total Kills: {self.player.kills}",
            ]
            # Per-type kills
            for etype, count in sorted(self.player.kill_counts.items()):
                stats.append(f"  {etype.capitalize()}s: {count}")

            for i, s in enumerate(stats):
                st = self._prompt_font.render(s, True, (180, 200, 180))
                self.display_surface.blit(st,
                    st.get_rect(center=(WIDTH // 2, HEIGHT // 2 + i * 26)))

        # Prompt
        tick = pygame.time.get_ticks()
        if (tick // 600) % 2 == 0:
            prompt = self._prompt_font.render("Press SPACE to play again", True, (200, 200, 160))
            self.display_surface.blit(prompt,
                prompt.get_rect(center=(WIDTH // 2, HEIGHT * 3 // 4 + 20)))

        self._draw_border((80, 140, 200))

        if self._confirm_pressed():
            self.player = None
            self._title_enter_tick = 0
            self._crawl = None
            self.state = self.TITLE

        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _confirm_pressed(self):
        """Check if Space (keyboard) or button 0 (gamepad) is pressed, with debounce."""
        now = pygame.time.get_ticks()
        if now - self._last_key_time < 300:
            return False
        keys = pygame.key.get_pressed()
        gp_btn = False
        if self._joystick and self._joystick.get_numbuttons() > 0:
            gp_btn = self._joystick.get_button(0)  # A button
        if keys[pygame.K_SPACE] or gp_btn:
            self._last_key_time = now
            return True
        return False

    def _draw_border(self, color, alpha=255):
        """Decorative border around the screen."""
        if alpha < 255:
            border_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            r = pygame.Rect(20, 20, WIDTH - 40, HEIGHT - 40)
            c = (*color, alpha)
            pygame.draw.rect(border_surf, c, r, 2, border_radius=8)
            for cx, cy in [(28, 28), (WIDTH - 28, 28), (28, HEIGHT - 28), (WIDTH - 28, HEIGHT - 28)]:
                pygame.draw.circle(border_surf, c, (cx, cy), 3)
            self.display_surface.blit(border_surf, (0, 0))
        else:
            r = pygame.Rect(20, 20, WIDTH - 40, HEIGHT - 40)
            pygame.draw.rect(self.display_surface, color, r, 2, border_radius=8)
            for cx, cy in [(28, 28), (WIDTH - 28, 28), (28, HEIGHT - 28), (WIDTH - 28, HEIGHT - 28)]:
                pygame.draw.circle(self.display_surface, color, (cx, cy), 3)
