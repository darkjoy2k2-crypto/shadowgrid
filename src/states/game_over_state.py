import pygame
from src.core.state_machine import State

class GameOverState(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.font_large = pygame.font.SysFont(None, 48)
        self.font_small = pygame.font.SysFont(None, 24)
        
        # Center button on 640x360 native canvas
        self.btn_rect = pygame.Rect(320 - 75, 210, 150, 36)
        
    def init(self):
        pass
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            screen = pygame.display.get_surface()
            if screen and screen.get_width() > 0 and screen.get_height() > 0:
                native_mx = int(mx * 640 / screen.get_width())
                native_my = int(my * 360 / screen.get_height())
            else:
                native_mx, native_my = mx // 2, my // 2
            
            if self.btn_rect.collidepoint(native_mx, native_my):
                self.sm.change_state("HUBGAME")
                
    def update(self, dt):
        pass
        
    def update_draw(self):
        surface = self.sm.context.get("native_surface")
        if not surface:
            return
            
        surface.fill((20, 0, 0)) # Dark red bg
        
        text = self.font_large.render("YOU FAILED", False, (255, 50, 50))
        surface.blit(text, (320 - text.get_width() // 2, 110))
        
        # Button
        pygame.draw.rect(surface, (100, 20, 20), self.btn_rect)
        pygame.draw.rect(surface, (255, 100, 100), self.btn_rect, 1)
        
        btn_text = self.font_small.render("TRY AGAIN", False, (255, 255, 255))
        surface.blit(btn_text, (self.btn_rect.x + (self.btn_rect.width - btn_text.get_width()) // 2, self.btn_rect.y + 10))

