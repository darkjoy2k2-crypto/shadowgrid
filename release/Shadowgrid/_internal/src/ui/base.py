import pygame
from typing import Tuple, Optional

class UIElement:
    """
    Basisklasse für alle UI-Elemente in Shadowgrid.
    Inspiriert von pygame_gui's UIElement Hierarchy.
    """
    def __init__(self, x: int = 0, y: int = 0, width: int = 0, height: int = 0, z_index: int = 0) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.active = True
        self.visible = True
        self.z_index = z_index

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def handle_event(self, event: pygame.event.Event, mx: int, my: int) -> bool:
        """Gibt True zurück, wenn das Event verarbeitet/konsumiert wurde."""
        return False

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass


class UIWindow(UIElement):
    """
    Basisklasse für verschiebbare UI-Fenster / Container in Shadowgrid.
    Inspiriert von pygame_gui's UIWindow Stack.
    """
    def __init__(self, x: int = 0, y: int = 0, width: int = 0, height: int = 0, z_index: int = 10, titlebar_height: int = 16) -> None:
        super().__init__(x, y, width, height, z_index)
        self.titlebar_height = titlebar_height
        self.rect_title = pygame.Rect(self.x, self.y, self.width, self.titlebar_height)
        
        # Drag State
        self.is_dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0

    def get_title_rect(self) -> pygame.Rect:
        self.rect_title = pygame.Rect(self.x, self.y, self.width, self.titlebar_height)
        return self.rect_title

    def process_drag_mouse_down(self, mx: int, my: int) -> bool:
        """Prüft Kollision mit der Titelleiste und startet Dragging."""
        if not self.active or not self.visible:
            return False
        if self.get_title_rect().collidepoint(mx, my):
            self.is_dragging = True
            self.drag_offset_x = self.x - mx
            self.drag_offset_y = self.y - my
            return True
        return False

    def process_drag_mouse_motion(self, mx: int, my: int) -> None:
        """Aktualisiert die Fensterposition beim Verschieben."""
        if self.is_dragging:
            self.x = mx + self.drag_offset_x
            self.y = my + self.drag_offset_y

    def process_drag_mouse_up(self) -> None:
        """Beendet den Verschiebevorgang."""
        self.is_dragging = False
