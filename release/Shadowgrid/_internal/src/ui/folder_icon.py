import pygame
from src.ui.base import UIElement
from src.ui.font_manager import font_mgr, GREEN_PHOSPHOR, GREEN_DIM

class FolderIcon(UIElement):
    """
    Interaktives 16-Bit Cyberpunk Ordner-Icon unten rechts im HUD.
    Ein Klick darauf schaltet Jack's Cyberdeck Verzeichnis-Inventar ein / aus.
    """
    def __init__(self) -> None:
        width = 36
        height = 28
        x = 640 - width - 16
        y = 360 - height - 16
        super().__init__(x=x, y=y, width=width, height=height, z_index=15)
        self.is_hovered = False

    def handle_click(self, mx: int, my: int, inventory) -> bool:
        if self.get_rect().collidepoint(mx, my):
            inventory.toggle()
            return True
        return False

    def handle_mouse_motion(self, mx: int, my: int) -> None:
        self.is_hovered = self.get_rect().collidepoint(mx, my)

    def draw(self, surface: pygame.Surface, is_active: bool = False) -> None:
        rect = self.get_rect()
        
        # Cyberpunk Bevel Button Box unten rechts
        bg_color = (15, 45, 30) if (self.is_hovered or is_active) else (5, 20, 15)
        border_color = (0, 255, 160) if (self.is_hovered or is_active) else (0, 140, 90)
        
        pygame.draw.rect(surface, bg_color, rect)
        pygame.draw.rect(surface, border_color, rect, 1)
        
        # 16-Bit Ordner Icon Rendering
        folder_color = GREEN_PHOSPHOR if (self.is_hovered or is_active) else (0, 200, 120)
        
        # Ordner Tab (oben links)
        tab_rect = pygame.Rect(rect.x + 4, rect.y + 4, 10, 4)
        pygame.draw.rect(surface, folder_color, tab_rect)
        
        # Ordner Body (Hauptkasten)
        body_rect = pygame.Rect(rect.x + 4, rect.y + 7, 28, 15)
        pygame.draw.rect(surface, (8, 28, 20), body_rect)
        pygame.draw.rect(surface, folder_color, body_rect, 1)
        
        # Laschen-Linie
        pygame.draw.line(surface, folder_color, (rect.x + 6, rect.y + 11), (rect.x + 28, rect.y + 11), 1)
