import pygame
from typing import List, Dict, Optional, Any
from src.ui.base import UIElement, UIWindow

class UIManager:
    """
    Zentraler UI-Controller für Shadowgrid.
    Direkt inspiriert von pygame_gui's UIManager:
    - Bündelt Event-Verarbeitung, Drag & Drop, Hit-Testing und Rendering aller UI-Elemente.
    - Garantiert striktes Z-Indexing und verhindert Durchklicken auf die Spielwelt.
    """
    def __init__(self) -> None:
        self.elements: List[UIElement] = []

    def register_element(self, element: UIElement) -> None:
        """Registriert ein UI-Element beim Manager."""
        if element not in self.elements:
            self.elements.append(element)
            self._sort_elements()

    def unregister_element(self, element: UIElement) -> None:
        """Entfernt ein UI-Element aus dem Manager."""
        if element in self.elements:
            self.elements.remove(element)

    def _sort_elements(self) -> None:
        """Sortiert UI-Elemente nach ihrem Z-Index (höhere Werte werden im Vordergrund gezeichnet/gehandhabt)."""
        self.elements.sort(key=lambda el: el.z_index)

    def bring_to_front(self, window: UIWindow) -> None:
        """Bringt ein Fenster in den Vordergrund (wie pygame_gui Window Stacking)."""
        max_z = max([el.z_index for el in self.elements], default=10)
        window.z_index = max_z + 1
        self._sort_elements()

    def is_ui_clicked(self, mx: int, my: int) -> bool:
        """
        Prüft, ob die Mausposition auf einem beliebigen aktiven UI-Element liegt.
        Verhindert Durchklicken auf die Tile-Map.
        """
        for el in reversed(self.elements):
            if el.active and el.visible:
                if el.get_rect().collidepoint(mx, my):
                    return True
        return False

    def process_events(self, event: pygame.event.Event, mx: int, my: int) -> bool:
        """
        Verarbeitet ein Pygame Event zentral durch alle registrierten UI-Elemente.
        Gibt True zurück, wenn das Event von einem UI-Element konsumiert wurde.
        """
        # Event in absteigender Z-Order durchreichen (Vordergrund zuerst)
        for el in reversed(self.elements):
            if el.active and el.visible:
                consumed = el.handle_event(event, mx, my)
                if consumed:
                    return True
                    
        # Event konsumieren wenn geklickt wurde und Hit Test positiv ist
        if event.type == pygame.MOUSEBUTTONDOWN and self.is_ui_clicked(mx, my):
            return True
            
        return False

    def update(self, dt: float) -> None:
        """Aktualisiert alle registrierten UI-Elemente."""
        for el in self.elements:
            if el.active:
                el.update(dt)

    def draw(self, surface: pygame.Surface, values: Optional[Dict[str, float]] = None) -> None:
        """Rendert alle sichtbaren UI-Elemente geordnet nach Z-Index."""
        for el in self.elements:
            if el.active and el.visible:
                # Unterstützung für dynamische Parameter z.B. values bei MeterContainer
                if hasattr(el, 'draw_with_values'):
                    el.draw_with_values(surface, values or {})
                else:
                    el.draw(surface)
