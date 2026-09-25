import pygame
from typing import Tuple
from src.ui.font_manager import font_mgr, GREEN_TERMINAL

class StatusMeter:
    """
    Minimalistische Cyberpunk-Statusleiste für Jack's Deck Interface.
    Unterstützt konfigurierbare Labels, Farben, Icon-Buchstaben und Füllstände.
    Rendert direkt auf dem Container-Panel ohne verschachtelten Hintergrund.
    """
    def __init__(self, label: str, icon_letter: str, color: Tuple[int, int, int]) -> None:
        self.label = label.upper()
        self.icon_letter = icon_letter.upper()[:1]
        self.color = color
        self.value = 0.0  # 0.0 bis 1.0
        
    def draw(self, surface: pygame.Surface, x: int, y: int, width: int = 140, height: int = 14) -> None:
        """Rendert die Statusleiste direkt ohne verschachtelten Hintergrund."""
        # Icon Box (kleiner Quadrat-Kasten links mit erstem Buchstaben)
        icon_size = 12
        icon_x = x + 2
        icon_y = y + 1
        
        # Icon Box (kleiner Quadrat-Kasten links mit erstem Buchstaben, nur Border)
        pygame.draw.rect(surface, self.color, (icon_x, icon_y, icon_size, icon_size), 1)
        
        icon_txt = font_mgr.render(self.icon_letter, color=self.color, size="tiny")
        surface.blit(icon_txt, (icon_x + (icon_size - icon_txt.get_width()) // 2, icon_y + (icon_size - icon_txt.get_height()) // 2))
        
        # Label Text (eng nebeneinander)
        label_x = icon_x + icon_size + 4
        label_y = y
        label_txt = font_mgr.render(self.label, color=GREEN_TERMINAL, size="tiny")
        surface.blit(label_txt, (label_x, label_y))
        
        # Untere Meter-Linie direkt unter dem Font (eng aneinander)
        line_x = label_x
        line_y = y + 10
        max_line_w = (x + width - 4) - line_x
        
        if max_line_w > 0:
            # Hintergrund-Schienenlinie
            pygame.draw.line(surface, (25, 45, 40), (line_x, line_y), (line_x + max_line_w, line_y), 2)
            
            # Gefüllter Balkenanteil
            fill_w = int(max_line_w * max(0.0, min(1.0, self.value)))
            if fill_w > 0:
                pygame.draw.line(surface, self.color, (line_x, line_y), (line_x + fill_w, line_y), 2)
