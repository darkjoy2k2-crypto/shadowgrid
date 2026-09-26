import pygame
import re
from typing import Dict, List
from src.ui.nine_slice import NineSliceRenderer
from src.ui.portrait_box import PortraitBox
from src.ui.meter_container import MeterContainer
from src.ui.driver_container import DriverContainer
from src.ui.inventory_window import InventoryWindow
from src.ui.error_modal import ErrorModal
from src.ui.folder_icon import FolderIcon
from src.ui.ui_manager import UIManager
from src.ui.font_manager import font_mgr, GREEN_PHOSPHOR, GREEN_BRIGHT, GREEN_DIM

class HUD:
    """Verwaltet und zeichnet das Heads-Up-Display im Shadowrun Genesis Cyberdeck-Stil."""
    
    def __init__(self) -> None:
        self.nineslice = NineSliceRenderer()
        self.portrait = PortraitBox(width=48, height=48)
        
        # Shadowrun Dialogue Panel Cache (36x10 Tiles = 288x80 px auf 640x360 Canvas)
        self.terminal_bg = self.nineslice.render(36, 10)
        
        # UI Skalierungs-Stufen (4 Schritte: 1.0x, 1.15x, 1.3x, 1.5x)
        self.scale_step: int = 1
        self.scale_factors: List[float] = [1.0, 1.15, 1.3, 1.5]
        
        # Modular Deck Systems
        self.meter_container = MeterContainer(allowed_slots=5) # Sensors (Oben Rechts)
        self.driver_container = DriverContainer(allowed_slots=5) # Drivers (Oben Links)
        self.inventory = InventoryWindow()
        self.error_modal = ErrorModal()
        self.folder_icon = FolderIcon()
        
        from src.ui.text_log_modal import TextLogModal
        self.text_log_modal = TextLogModal(width=500, height=280)
        
        # Centralized Pygame-GUI inspired UI Controller Manager
        self.ui_manager = UIManager()
        self.ui_manager.register_element(self.meter_container)
        self.ui_manager.register_element(self.driver_container)
        self.ui_manager.register_element(self.inventory)
        self.ui_manager.register_element(self.folder_icon)
        self.ui_manager.register_element(self.error_modal)
        self.ui_manager.register_element(self.text_log_modal)
        
        # Container Position (Oben Rechts)
        self.container_x = 640 - 175
        self.container_y = 12
        self.container_w = 160

    def get_current_scale_factor(self) -> float:
        return self.scale_factors[self.scale_step - 1]

    def clamp_all_ui_elements(self) -> None:
        """Garantiert, dass JEDES UI-Element strikt innerhalb der 640x360 Bildschirmgrenzen liegt (Kein Out-of-Bounds)."""
        # Meter Container
        self.meter_container.x = max(0, min(640 - self.meter_container.width, self.meter_container.x))
        self.meter_container.y = max(0, min(360 - 40, self.meter_container.y))
        
        # Driver Container
        self.driver_container.x = max(0, min(640 - self.driver_container.width, self.driver_container.x))
        self.driver_container.y = max(0, min(360 - 40, self.driver_container.y))
        
        # Inventory Window
        self.inventory.x = max(0, min(640 - self.inventory.width, self.inventory.x))
        self.inventory.y = max(0, min(360 - self.inventory.height, self.inventory.y))

    def handle_scale_button_click(self, mx: int, my: int) -> bool:
        """
        Interaktion mit [+] und [i] Buttons unterhalb von Jacks Porträt:
        - [+] schaltet durch die 4 Skalierungsstufen (1.0x -> 1.15x -> 1.3x -> 1.5x -> 1.0x).
        - [i] setzt die Skalierung zurück oder schaltet direkt auf 1.5x.
        """
        h = 360
        term_x = 16
        term_y = h - 80 - 16
        
        btn_plus_rect = pygame.Rect(term_x + 10, term_y + 65, 22, 11)
        btn_info_rect = pygame.Rect(term_x + 36, term_y + 65, 22, 11)
        
        if btn_plus_rect.collidepoint(mx, my):
            self.scale_step = (self.scale_step % 4) + 1
            self.clamp_all_ui_elements()
            return True
            
        if btn_info_rect.collidepoint(mx, my):
            self.scale_step = 4 if self.scale_step < 4 else 1
            self.clamp_all_ui_elements()
            return True
            
        return False

    def _wrap_text_to_lines(self, text: str, max_width: int, max_lines: int = 3) -> List[str]:
        """Bricht Gedankentexte automatisch an Leerzeichen/Satzzeichen oder mitten im Wort um."""
        if not text:
            return []

        words = text.split(" ")
        lines: List[str] = []
        current_line = ""

        for word in words:
            test_line = (current_line + " " + word).strip() if current_line else word
            test_surf = font_mgr.render(test_line)
            
            if test_surf.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    if len(lines) >= max_lines:
                        break
                    current_line = ""
                
                word_surf = font_mgr.render(word)
                if word_surf.get_width() > max_width:
                    char_line = ""
                    for char in word:
                        test_char = char_line + char
                        if font_mgr.render(test_char).get_width() <= max_width:
                            char_line = test_char
                        else:
                            lines.append(char_line)
                            if len(lines) >= max_lines:
                                break
                            char_line = char
                    if len(lines) < max_lines and char_line:
                        current_line = char_line
                else:
                    current_line = word

        if current_line and len(lines) < max_lines:
            lines.append(current_line)

        return lines[:max_lines]

    def draw(self, surface: pygame.Surface, values: Dict[str, float], flip_x: bool = False, thought_text: str = "JACK // ONLINE", feed_lines: Optional[List[str]] = None) -> None:
        """Rendert das Terminal, Buttons, Deck Meters, Inventar und Modals mit strikter Grenzen-Sicherung."""
        self.clamp_all_ui_elements()
        h = surface.get_height()
        
        # Shadowrun Terminal Fenster (Unten Links)
        term_w = 36 * 8   # 288 px
        term_h = 10 * 8   # 80 px
        term_x = 16
        term_y = h - term_h - 16
        
        surface.blit(self.terminal_bg, (term_x, term_y))
        
        # Jack's Portrait Box auf der linken Seite des Terminals
        self.portrait.draw(surface, term_x + 10, term_y + 16, flip_x=flip_x)
        
        # --- Unterhalb von Jacks Porträt: [+] und [i] Buttons für Skalierung ---
        btn_plus_rect = pygame.Rect(term_x + 10, term_y + 65, 22, 11)
        btn_info_rect = pygame.Rect(term_x + 36, term_y + 65, 22, 11)
        
        # Button [+]
        pygame.draw.rect(surface, (15, 30, 25), btn_plus_rect)
        pygame.draw.rect(surface, (0, 180, 120), btn_plus_rect, 1)
        plus_txt = font_mgr.render("+", color=GREEN_BRIGHT, size="tiny")
        surface.blit(plus_txt, (btn_plus_rect.x + 7, btn_plus_rect.y + 1))
        
        # Button [i]
        pygame.draw.rect(surface, (15, 30, 25), btn_info_rect)
        pygame.draw.rect(surface, (0, 180, 120), btn_info_rect, 1)
        info_txt = font_mgr.render("i", color=GREEN_PHOSPHOR, size="tiny")
        surface.blit(info_txt, (btn_info_rect.x + 8, btn_info_rect.y + 1))
        
        # Shadowrun 8x8 Phosphor-Grüner Log-Text & Matrix C# Fantasie Feed
        text_x = term_x + 66
        text_y = term_y + 12
        max_text_w = term_w - 76 # 212 px Breite für Text
        
        lines = self._wrap_text_to_lines(thought_text, max_width=max_text_w, max_lines=2)
        
        for idx, line_str in enumerate(lines):
            line_surf = font_mgr.render(line_str, color=GREEN_PHOSPHOR)
            surface.blit(line_surf, (text_x, text_y + idx * 12))
        
        # Status Meter Container (Oben Rechts)
        self.meter_container.draw(surface, self.meter_container.x, self.meter_container.y, values, self.meter_container.width)
        
        # Driver Container (Oben Links)
        self.driver_container.draw(surface, self.driver_container.x, self.driver_container.y, self.driver_container.width)
        
        # Directory Inventory Window
        self.inventory.draw(surface)
        
        # Folder Icon Button (Unten Rechts)
        self.folder_icon.draw(surface, is_active=self.inventory.active)
        
        # Error Modal Overlay (falls aktiv)
        self.error_modal.draw(surface)
        
        # Text Log Modal Overlay (falls aktiv)
        self.text_log_modal.draw(surface)
