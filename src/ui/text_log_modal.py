import pygame
from typing import List, Optional, Tuple, Dict, Any
from src.ui.base import UIWindow
from src.ui.nine_slice import NineSliceRenderer
from src.ui.font_manager import font_mgr, GREEN_PHOSPHOR, GREEN_BRIGHT, GREEN_DIM, RED_ALERT

class TextLogModal(UIWindow):
    """
    Wiederverwendbares, großes Lese-UI-Fenster (Template) für Log-Dateien & Gedankentexte.
    Eigenschaften:
    - Großes Cyberpunk Nine-Slice Fenster
    - Oben fixierte Titelzeile (z. B. Log-Dateiname)
    - Rechte Seite: Grüner Scrollbar-Slider (Ziehbar)
    - Mausrad-Scrolling (Up/Down)
    - Beim Öffnen automatisch ganz nach unten gescrollt (letzter Eintrag)
    - 1 Zeile Absatz zwischen Einträgen
    - Keine Zeitstempel-Anzeige
    - Blochiert Durchklicken (Kein Click-Through)
    """
    def __init__(self, width: int = 500, height: int = 280) -> None:
        # Zentriert auf 640x360 Canvas
        x = (640 - width) // 2
        y = (360 - height) // 2
        super().__init__(x=x, y=y, width=width, height=height, z_index=50, titlebar_height=24)
        
        self.active = False
        self.nineslice = NineSliceRenderer()
        self.log_title: str = "THOUGHT LOG // SESSION_READOUT"
        self.entries: List[str] = []
        
        self.scroll_offset: int = 0
        self.line_height: int = 12
        self.content_y_start: int = y + 28
        self.content_h: int = height - 36
        self.max_visible_lines: int = self.content_h // self.line_height
        
        self.is_slider_dragging: bool = False
        self.drag_start_y: int = 0
        self.drag_start_scroll: int = 0

    def open_log(self, title: str, entries: List[str]) -> None:
        """Öffnet das Lese-UI-Fenster mit dem angegebenen Titel und den Einträgen."""
        self.log_title = title.upper()
        self.entries = [e for e in entries if e and e.strip()]
        self.active = True
        
        # Aufbereitete Zeilen inklusive 1 Leerzeile Absatz zwischen den Einträgen
        self.formatted_lines: List[str] = []
        max_line_w = self.width - 32 # 32px Platz für Ränder und Scrollbar
        
        for idx, entry in enumerate(self.entries):
            wrapped = self._wrap_text(entry, max_width=max_line_w)
            self.formatted_lines.extend(wrapped)
            if idx < len(self.entries) - 1:
                self.formatted_lines.append("") # 1 Zeile Absatz
                
        # Beim Öffnen immer ganz nach unten scrollen (letzter Eintrag!)
        total_lines = len(self.formatted_lines)
        if total_lines > self.max_visible_lines:
            self.scroll_offset = total_lines - self.max_visible_lines
        else:
            self.scroll_offset = 0

    def close(self) -> None:
        """Schließt das Lese-UI-Fenster."""
        self.active = False
        self.is_slider_dragging = False

    def toggle(self, title: str = "", entries: Optional[List[str]] = None) -> None:
        if self.active:
            self.close()
        else:
            if entries is not None:
                self.open_log(title or self.log_title, entries)

    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """Bricht Text an Leerzeichen/Satzzeichen um oder zeichenweise mitten im Wort."""
        words = text.split(" ")
        lines: List[str] = []
        current_line = ""

        for word in words:
            test_line = (current_line + " " + word).strip() if current_line else word
            if font_mgr.render(test_line, size="tiny").get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                
                if font_mgr.render(word, size="tiny").get_width() > max_width:
                    char_line = ""
                    for char in word:
                        test_char = char_line + char
                        if font_mgr.render(test_char, size="tiny").get_width() <= max_width:
                            char_line = test_char
                        else:
                            lines.append(char_line)
                            char_line = char
                    if char_line:
                        current_line = char_line
                else:
                    current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def handle_scroll(self, scroll_y: int) -> bool:
        """Mausrad scrollt hoch (scroll_y > 0) und runter (scroll_y < 0)."""
        if not self.active:
            return False
            
        total_lines = getattr(self, 'formatted_lines', [])
        max_scroll = max(0, len(total_lines) - self.max_visible_lines)
        
        if scroll_y > 0: # Nach oben scrollen
            self.scroll_offset = max(0, self.scroll_offset - 2)
        elif scroll_y < 0: # Nach unten scrollen
            self.scroll_offset = min(max_scroll, self.scroll_offset + 2)
            
        return True

    def handle_click(self, mx: int, my: int) -> bool:
        """Prüft Klicks auf Schließen-Button oder Fensterbereich (kein Click-Through)."""
        if not self.active:
            return False
            
        rect = self.get_rect()
        if not rect.collidepoint(mx, my):
            # Klick außerhalb schließt das Fenster
            self.close()
            return True
            
        # Klick auf [X] Schließen-Button oben rechts
        close_rect = pygame.Rect(self.x + self.width - 24, self.y + 4, 18, 16)
        if close_rect.collidepoint(mx, my):
            self.close()
            return True
            
        return True # Blockiert Klick für Spielwelt

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface: pygame.Surface) -> None:
        """Rendert das große Lese-UI-Fenster mit Titel, Zeilen und rechteckigem Scrollbar-Slider."""
        if not self.active:
            return
            
        tiles_w = max(2, self.width // 8)
        tiles_h = max(2, self.height // 8)
        panel_surface = self.nineslice.render(tiles_w, tiles_h)
        surface.blit(panel_surface, (self.x, self.y))
        
        # 1. Oben fixierter Header-Titel (Linksbündig)
        title_str = self.log_title
        if len(title_str) > 55:
            title_str = title_str[:52] + "..."
        title_txt = font_mgr.render(title_str, color=GREEN_BRIGHT, size="tiny")
        surface.blit(title_txt, (self.x + 10, self.y + 6))
        
        # Schließen-Button [X] oben rechts
        close_rect = pygame.Rect(self.x + self.width - 22, self.y + 5, 14, 14)
        pygame.draw.rect(surface, (40, 15, 15), close_rect)
        pygame.draw.rect(surface, (180, 50, 50), close_rect, 1)
        x_txt = font_mgr.render("X", color=RED_ALERT, size="tiny")
        surface.blit(x_txt, (close_rect.x + 4, close_rect.y + 2))
        
        # Trennlinie unter dem Header
        pygame.draw.line(surface, (0, 150, 100), (self.x + 8, self.y + 22), (self.x + self.width - 8, self.y + 22), 1)
        
        # 2. Textzeilen rendern
        formatted_lines = getattr(self, 'formatted_lines', [])
        visible_lines = formatted_lines[self.scroll_offset : self.scroll_offset + self.max_visible_lines]
        
        for idx, line_str in enumerate(visible_lines):
            line_y = self.content_y_start + idx * self.line_height
            if line_str:
                txt_surf = font_mgr.render(line_str, color=GREEN_PHOSPHOR, size="tiny")
                surface.blit(txt_surf, (self.x + 12, line_y))
                
        # 3. Rechte Seite: Grüner Scrollbar-Slider Indicator
        total_lines = len(formatted_lines)
        if total_lines > self.max_visible_lines:
            track_x = self.x + self.width - 12
            track_y = self.content_y_start
            track_h = self.content_h
            
            # Schiene
            pygame.draw.line(surface, (0, 60, 50), (track_x + 1, track_y), (track_x + 1, track_y + track_h), 2)
            
            # Slider Thumb Berechnung
            ratio = self.max_visible_lines / float(total_lines)
            thumb_h = max(12, int(track_h * ratio))
            max_scroll = total_lines - self.max_visible_lines
            scroll_ratio = self.scroll_offset / float(max_scroll) if max_scroll > 0 else 0
            thumb_y = track_y + int((track_h - thumb_h) * scroll_ratio)
            
            thumb_rect = pygame.Rect(track_x - 1, thumb_y, 4, thumb_h)
            pygame.draw.rect(surface, GREEN_BRIGHT, thumb_rect)
