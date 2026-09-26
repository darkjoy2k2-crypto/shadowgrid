import pygame
from src.ui.font_manager import font_mgr, RED_ALERT, WHITE_TEXT

class GameOverMenu:
    def __init__(self, font: pygame.font.Font = None) -> None:
        self.rect_retry = pygame.Rect(0, 0, 0, 0)
        
    def draw(self, surface: pygame.Surface) -> None:
        screen_w = surface.get_width()
        screen_h = surface.get_height()
        
        # Draw dark overlay
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        
        panel_w = 160
        panel_h = 80
        panel_x = (screen_w - panel_w) // 2
        panel_y = (screen_h - panel_h) // 2
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(surface, (15, 5, 5), panel_rect)
        pygame.draw.rect(surface, (255, 50, 50), panel_rect, 1)
        
        title_rect = pygame.Rect(panel_x, panel_y, panel_w, 16)
        pygame.draw.rect(surface, (100, 0, 0), title_rect)
        
        title = font_mgr.render("SYSTEM FAILURE", color=RED_ALERT, size="tiny")
        surface.blit(title, (panel_x + 4, panel_y + 2))
        
        msg = font_mgr.render("JACK WAS ELIMINATED", color=WHITE_TEXT, size="tiny")
        surface.blit(msg, (panel_x + 8, panel_y + 30))
        
        # Retry Button
        self.rect_retry = pygame.Rect(panel_x + 8, panel_y + 55, panel_w - 16, 18)
        pygame.draw.rect(surface, (100, 0, 0), self.rect_retry)
        retry_txt = font_mgr.render("RETRY", color=WHITE_TEXT, size="tiny")
        surface.blit(retry_txt, (self.rect_retry.x + 8, self.rect_retry.y + 3))

    def handle_click(self, mx: int, my: int) -> str:
        if self.rect_retry.collidepoint(mx, my):
            return "RETRY"
        return ""

