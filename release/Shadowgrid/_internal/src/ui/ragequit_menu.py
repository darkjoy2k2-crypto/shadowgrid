import pygame
from typing import List
from src.ui.font_manager import font_mgr, RED_ALERT, WHITE_TEXT, GREEN_TERMINAL

class RagequitMenu:
    """
    Ragequit UI-Panel für die Jack-Doppelgänger-Begegnung.
    Bietet sauberen Word-Wrap, dynamisches Padding und ein erweitertes Panel
    nach oben, um jeglichen Text-Overflow zu verhindern.
    """
    def __init__(self) -> None:
        self.rect_quit = pygame.Rect(0, 0, 0, 0)
        
    def _wrap_text_to_lines(self, text: str, max_chars_per_line: int) -> List[str]:
        words = text.split(" ")
        lines = []
        current_line = []
        current_len = 0
        
        for word in words:
            word_len = len(word)
            if current_len + word_len + (1 if current_line else 0) <= max_chars_per_line:
                current_line.append(word)
                current_len += word_len + (1 if current_line else 1)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_len = word_len
                
        if current_line:
            lines.append(" ".join(current_line))
            
        return lines

    def draw(self, surface: pygame.Surface) -> None:
        screen_w = surface.get_width()
        screen_h = surface.get_height()
        
        # Abdunkelndes Overlay mit rotem Glitch-Stich
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((20, 0, 0, 190))
        surface.blit(overlay, (0, 0))
        
        # Erweiterte Panel-Größe (nach oben verschoben für maximale Lesbarkeit)
        panel_w = 400
        panel_h = 180
        panel_x = (screen_w - panel_w) // 2
        panel_y = ((screen_h - panel_h) // 2) - 20 # Nach oben erweitert
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(surface, (15, 5, 5), panel_rect)
        pygame.draw.rect(surface, (255, 50, 50), panel_rect, 2)
        
        # Header Banner
        title_rect = pygame.Rect(panel_x, panel_y, panel_w, 24)
        pygame.draw.rect(surface, (120, 0, 0), title_rect)
        
        title = font_mgr.render("PARADOX OVERLOAD // RAGEQUIT", color=RED_ALERT, size="tiny")
        surface.blit(title, (panel_x + (panel_w - title.get_width()) // 2, panel_y + 5))
        
        # Text-Inhalt mit automatischem Word-Wrap
        story_text = "JACK: 'Zwei von mir in diesem verseuchten System?! Ein Klon, ein ungelöschter Thread... Das Grid ist komplett im Eimer. Ich habe die Schnauze voll!'"
        max_chars = (panel_w - 24) // 8 # 8px pro Zeichen in 8x8 font_mgr
        lines = self._wrap_text_to_lines(story_text, max_chars)
        
        y_text_start = panel_y + 36
        line_height = 14
        for i, line_str in enumerate(lines):
            # Erste Zeile weiß, restliche Zeilen in Rot für dramatischen Effekt
            text_color = WHITE_TEXT if i == 0 else RED_ALERT
            line_surf = font_mgr.render(line_str, color=text_color, size="tiny")
            surface.blit(line_surf, (panel_x + 12, y_text_start + i * line_height))
        
        # "Mir reicht es!" Button zentriert am unteren Rand des Panels
        btn_w = 160
        btn_h = 26
        btn_x = panel_x + (panel_w - btn_w) // 2
        btn_y = panel_y + panel_h - 38
        self.rect_quit = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        
        btn_color = (180, 20, 20)
        border_color = (255, 100, 100)
        
        pygame.draw.rect(surface, btn_color, self.rect_quit)
        pygame.draw.rect(surface, border_color, self.rect_quit, 1)
        
        btn_txt = font_mgr.render("Mir reicht es!", color=WHITE_TEXT, size="small")
        txt_x = self.rect_quit.x + (self.rect_quit.width - btn_txt.get_width()) // 2
        txt_y = self.rect_quit.y + (self.rect_quit.height - btn_txt.get_height()) // 2
        surface.blit(btn_txt, (txt_x, txt_y))

    def handle_click(self, mx: int, my: int) -> str:
        if self.rect_quit.collidepoint(mx, my):
            return "QUIT"
        return ""
