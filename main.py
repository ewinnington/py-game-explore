import pygame, sys
from data import * 
from level import Level
import cProfile as profile

class Game: 
    def __init__(self): 

        # General setup 
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH,HEIGHT))
        pygame.display.set_caption(CAPTION)
        self.clock = pygame.time.Clock()

        self.level = Level()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:
                        self.level.player.circular_menu.toggle()
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_TAB:
                        self.level.player.circular_menu.toggle()

            self.screen.fill('dark green')
            self.level.run()
            self.level.player.circular_menu.draw(self.screen)
            pygame.display.update()
            self.clock.tick(FPS)
            
if __name__ == '__main__':
    game = Game()
    # profile.run('game.run()')
    game.run()