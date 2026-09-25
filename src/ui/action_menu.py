import pygame
from src.ui.base import UIWindow
from src.ui.font_manager import font_mgr, GREEN_TERMINAL, WHITE_TEXT

class ActionMenu(UIWindow):
    def __init__(self, font: pygame.font.Font = None) -> None:
        super().__init__(x=0, y=0, width=120, height=60, z_index=30, titlebar_height=16)
        self.active = False
        
        # State: "OPTIONS" (Infiltrate / Hijack) or "INFILTRATING"
        self.state = "OPTIONS"
        
        # Infiltration state
        self.progress = 0.0
        self.is_paused = False
        
        # Button bounding boxes (Screen relative)
        self.rect_infiltrate = pygame.Rect(0, 0, 0, 0)
        self.rect_hijack = pygame.Rect(0, 0, 0, 0)
        self.rect_pause = pygame.Rect(0, 0, 0, 0)
        self.rect_cancel = pygame.Rect(0, 0, 0, 0)
        
    def open(self, x: int, y: int) -> None:
        if not self.active:
            self.active = True
            if not getattr(self, 'has_been_dragged', False):
                self.x = x
                self.y = y
            self.state = "OPTIONS"
            self.progress = 0.0
            self.is_paused = False
            
    def update_position(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
            
    def close(self) -> None:
        self.active = False
        
    def get_rect(self) -> pygame.Rect:
        """Gibt das Bounding-Rect des Action-Menüs zurück."""
        return pygame.Rect(self.x, self.y, 120, 60)
        
    def handle_click(self, mx: int, my: int) -> str:
        if not self.active:
            return ""
            
        if self.state == "OPTIONS":
            if self.rect_infiltrate.collidepoint(mx, my):
                self.state = "INFILTRATING"
                self.progress = 0.0
                self.is_paused = False
                return "INFILTRATE_START"
            elif self.rect_hijack.collidepoint(mx, my):
                return "HIJACK"
                
        elif self.state == "INFILTRATING":
            if self.rect_pause.collidepoint(mx, my):
                self.is_paused = not self.is_paused
                return "PAUSE_TOGGLED"
            elif self.rect_cancel.collidepoint(mx, my):
                self.close()
                return "CANCEL"
                
        return ""

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return
            
        # Draw a cyberpunk styled panel
        panel_rect = pygame.Rect(self.x, self.y, 120, 60)
        pygame.draw.rect(surface, (10, 20, 20), panel_rect)
        pygame.draw.rect(surface, (0, 255, 200), panel_rect, 1)
        
        self.rect_title = pygame.Rect(self.x, self.y, 120, 16)
        pygame.draw.rect(surface, (0, 100, 80), self.rect_title)
        
        title = font_mgr.render("ACTION", color=GREEN_TERMINAL, size="tiny")
        surface.blit(title, (self.x + 4, self.y + 2))
        
        if self.state == "OPTIONS":
            # Infiltrate Button
            self.rect_infiltrate = pygame.Rect(panel_rect.x + 4, panel_rect.y + 20, 112, 16)
            pygame.draw.rect(surface, (0, 100, 80), self.rect_infiltrate)
            inf_txt = font_mgr.render("INFILTRATE", color=WHITE_TEXT, size="tiny")
            surface.blit(inf_txt, (self.rect_infiltrate.x + 4, self.rect_infiltrate.y + 2))
            
            # Hijack Button
            self.rect_hijack = pygame.Rect(panel_rect.x + 4, panel_rect.y + 40, 112, 16)
            pygame.draw.rect(surface, (100, 0, 0), self.rect_hijack)
            hij_txt = font_mgr.render("HIJACK", color=WHITE_TEXT, size="tiny")
            surface.blit(hij_txt, (self.rect_hijack.x + 4, self.rect_hijack.y + 2))
            
        elif self.state == "INFILTRATING":
            # Status text instead of progress bar (progress is handled by MeterContainer progress.bxr)
            inf_txt = font_mgr.render("INFILTRATING...", color=GREEN_TERMINAL, size="tiny")
            surface.blit(inf_txt, (panel_rect.x + 4, panel_rect.y + 24))
            
            # Pause Button
            self.rect_pause = pygame.Rect(panel_rect.x + 78, panel_rect.y + 20, 18, 18)
            pause_color = (200, 150, 0) if not self.is_paused else (100, 100, 100)
            pygame.draw.rect(surface, pause_color, self.rect_pause)
            pause_txt = font_mgr.render("II", color=WHITE_TEXT, size="tiny")
            surface.blit(pause_txt, (self.rect_pause.x + 4, self.rect_pause.y + 2))
            
            # Cancel Button
            self.rect_cancel = pygame.Rect(panel_rect.x + 100, panel_rect.y + 20, 18, 18)
            pygame.draw.rect(surface, (200, 50, 50), self.rect_cancel)
            cancel_txt = font_mgr.render("X", color=WHITE_TEXT, size="tiny")
            surface.blit(cancel_txt, (self.rect_cancel.x + 5, self.rect_cancel.y + 2))

