import pygame
from src.ui.base import UIElement
from src.ui.font_manager import font_mgr, RED_ALERT

class ErrorModal(UIElement):
    """
    Roter Cyberpunk Rejection Error Popup Modal.
    Wird angezeigt, wenn eine falsche / ungültige Datei in die Statusleiste gezogen wird.
    """
    def __init__(self, font: pygame.font.Font = None) -> None:
        super().__init__(x=0, y=0, width=640, height=360, z_index=100)
        self.active = False
        self.title_text = "ACCESS REJECTED"
        self.message_text = "ONLY .BXR METERS CAN BE MOUNTED TO DECK"
        self.timer = 0.0
        
    def trigger(self, message: str = "ONLY .BXR METERS CAN BE MOUNTED TO DECK") -> None:
        """Aktiviert das Error-Modal mit einer Fehlermeldung."""
        self.active = True
        self.message_text = message
        self.timer = 2.5 # 2.5 Sekunden Auto-Close
        
    def update(self, dt: float) -> None:
        if self.active:
            self.timer -= dt
            if self.timer <= 0:
                self.active = False
                
    def handle_click(self, mx: int, my: int) -> bool:
        if self.active:
            self.active = False
            return True
        return False
        
    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return
            
        screen_w = surface.get_width()
        screen_h = surface.get_height()
        
        # Dunkelrotes semi-transparentes Overlay
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((40, 0, 0, 160))
        surface.blit(overlay, (0, 0))
        
        panel_w = 260
        panel_h = 70
        panel_x = (screen_w - panel_w) // 2
        panel_y = (screen_h - panel_h) // 2
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(surface, (25, 5, 5), panel_rect)
        pygame.draw.rect(surface, (255, 40, 40), panel_rect, 2)
        
        # Rote Header Bar
        header_rect = pygame.Rect(panel_x, panel_y, panel_w, 18)
        pygame.draw.rect(surface, (150, 10, 10), header_rect)
        
        title_txt = font_mgr.render(f"[!] {self.title_text}", color=(255, 220, 220), size="small")
        surface.blit(title_txt, (panel_x + 6, panel_y + 2))
        
        msg_txt = font_mgr.render(self.message_text, color=RED_ALERT, size="tiny")
        surface.blit(msg_txt, (panel_x + 8, panel_y + 28))
        
        sub_txt = font_mgr.render("CLICK OR WAIT TO DISMISS", color=(180, 180, 180), size="tiny")
        surface.blit(sub_txt, (panel_x + 8, panel_y + 48))

