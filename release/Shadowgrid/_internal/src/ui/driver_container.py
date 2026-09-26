import pygame
from typing import Dict, List, Optional, Tuple
from src.ui.base import UIWindow
from src.ui.theme import theme
from src.ui.nine_slice import NineSliceRenderer
from src.ui.font_manager import font_mgr, GREEN_TERMINAL, GREEN_DIM

class DriverStatusMeter:
    """Rendert Treiber-Slots im Drivers Container."""
    def __init__(self, label: str, icon_letter: str, color: Tuple[int, int, int], category: str = "CAMERA") -> None:
        self.label = label.upper()
        self.icon_letter = icon_letter.upper()[:1]
        self.color = color
        self.category = category # "CAMERA", "NETWORK", etc.

    def draw(self, surface: pygame.Surface, x: int, y: int, width: int = 140, height: int = 14) -> None:
        icon_size = 12
        icon_x = x + 2
        icon_y = y + 1
        
        pygame.draw.rect(surface, self.color, (icon_x, icon_y, icon_size, icon_size), 1)
        icon_txt = font_mgr.render(self.icon_letter, color=self.color, size="tiny")
        surface.blit(icon_txt, (icon_x + (icon_size - icon_txt.get_width()) // 2, icon_y + (icon_size - icon_txt.get_height()) // 2))
        
        label_x = icon_x + icon_size + 4
        label_y = y + 2
        label_txt = font_mgr.render(self.label, color=GREEN_TERMINAL, size="tiny")
        surface.blit(label_txt, (label_x, label_y))


class DriverContainer(UIWindow):
    """
    Verschiebbarer Drivers-Container auf der linken Seite.
    Unterstützt .drv Treiber-Dateien (z.B. disp.drv, ucam.drv).
    Regel: Es darf stets nur EIN Kamera-Treiber im System montiert sein!
    """
    def __init__(self, allowed_slots: int = 5) -> None:
        super().__init__(x=16, y=12, width=160, height=112, z_index=10, titlebar_height=theme.TITLEBAR_HEIGHT)
        self.max_slots = 5
        self.allowed_slots = min(self.max_slots, max(1, allowed_slots))
        
        # Folding State
        self.is_unfolded = False
        self.is_drag_active = False
        self.unfold_timer = 0.0
        
        # Initial gestartet mit dem Basis Display-Treiber disp.drv
        self.equipped_slots: List[Optional[str]] = [
            "disp.drv",
            None,
            None,
            None,
            None
        ]
        
        self.nineslice = NineSliceRenderer()
        
        # Registry der unterstützten .drv Treiber-Dateien
        self.driver_registry: Dict[str, DriverStatusMeter] = {
            "disp.drv": DriverStatusMeter("DISP.DRV [LOW]", "C", (0, 200, 255), category="CAMERA"),
            "ucam.drv": DriverStatusMeter("UCAM.DRV [MAX]", "U", (0, 255, 120), category="CAMERA")
        }

    def _compact_slots(self) -> None:
        """Kompaktiert montierte Treiber-Dateien nach oben."""
        mounted = [s for s in self.equipped_slots if s is not None]
        while len(mounted) < self.max_slots:
            mounted.append(None)
        self.equipped_slots = mounted

    def get_active_camera_driver(self) -> Optional[str]:
        """Gibt den aktuell montierten Kamera-Treiber zurück (disp.drv, ucam.drv oder None)."""
        for fname in self.equipped_slots:
            if fname and fname in self.driver_registry:
                if self.driver_registry[fname].category == "CAMERA":
                    return fname
        return None

    def trigger_temp_unfold(self, duration: float = 2.0) -> None:
        self.unfold_timer = max(self.unfold_timer, duration)

    def get_slot_rect(self, slot_idx: int, container_x: int, container_y: int, width: int = 160) -> pygame.Rect:
        slot_h = 14
        top_offset = 22
        padding = 2
        sy = container_y + top_offset + slot_idx * (slot_h + padding)
        return pygame.Rect(container_x + 4, sy, width - 8, slot_h)

    def handle_titlebar_click(self, mx: int, my: int) -> bool:
        if self.get_title_rect().collidepoint(mx, my):
            self.is_unfolded = not self.is_unfolded
            return True
        return False

    def handle_right_click(self, mx: int, my: int, inventory, emotion_engine = None) -> bool:
        """Rechtsklick entlädt einen Treiber zurück nach /sys/deck/drivers/."""
        for i in range(self.allowed_slots):
            mounted_file = self.equipped_slots[i]
            if mounted_file:
                slot_rect = self.get_slot_rect(i, self.x, self.y, self.width)
                if slot_rect.collidepoint(mx, my):
                    self.equipped_slots[i] = None
                    self._compact_slots()
                    if hasattr(inventory, 'add_drv_file'):
                        inventory.add_drv_file(mounted_file)
                    from src.utils.perception_logger import perception_logger
                    perception_logger.log_event("EQUIPMENT_UNMOUNT", {"type": "DRIVER", "file": mounted_file})
                    return True
        return False

    def equip_file(self, slot_idx: int, filename: str, inventory = None, emotion_engine = None) -> Tuple[bool, Optional[str]]:
        """
        Lädt eine .drv Datei.
        Garantiert: Es darf nur EIN Kamera-Treiber montiert sein.
        Falls bereits ein Kamera-Treiber steckt, wird dieser ersetzt und zurückgelegt.
        """
        fname = filename.lower()
        if not fname.endswith(".drv") or fname not in self.driver_registry:
            return False, None
            
        driver_obj = self.driver_registry[fname]
        replaced_driver: Optional[str] = None
        
        # Ersetze existierenden Kamera-Treiber falls gleicher Typ
        if driver_obj.category == "CAMERA":
            current_cam = self.get_active_camera_driver()
            if current_cam:
                for idx, slot in enumerate(self.equipped_slots):
                    if slot == current_cam:
                        self.equipped_slots[idx] = None
                        replaced_driver = current_cam
                        break

        # Ersten freien Slot wählen
        free_slot = -1
        for idx in range(self.allowed_slots):
            if self.equipped_slots[idx] is None:
                free_slot = idx
                break
                
        if free_slot != -1:
            self.equipped_slots[free_slot] = fname
        else:
            self.equipped_slots[0] = fname
            
        self._compact_slots()
        self.trigger_temp_unfold(2.0)
        
        from src.utils.perception_logger import perception_logger
        perception_logger.log_event("EQUIPMENT_MOUNT", {"type": "DRIVER", "file": fname, "replaced": replaced_driver})
        return True, replaced_driver

    def update(self, dt: float) -> None:
        if self.unfold_timer > 0:
            self.unfold_timer -= dt

    def should_display_slot(self, slot_idx: int, fname: Optional[str]) -> bool:
        if self.is_unfolded or self.is_drag_active or self.unfold_timer > 0:
            return True
        return fname is not None

    def draw(self, surface: pygame.Surface, x: Optional[int] = None, y: Optional[int] = None, width: Optional[int] = None) -> None:
        if x is not None:
            self.x = x
        else:
            x = self.x
        if y is not None:
            self.y = y
        else:
            y = self.y
        if width is not None:
            self.width = width
        else:
            width = self.width

        visible_slots: List[Tuple[int, Optional[str]]] = []
        for i in range(self.allowed_slots):
            fname = self.equipped_slots[i]
            if self.should_display_slot(i, fname):
                visible_slots.append((i, fname))

        slot_h = 14
        padding = 2
        top_offset = 22
        total_visible = len(visible_slots)
        container_h = top_offset + (total_visible * (slot_h + padding) if total_visible > 0 else 2) + 4
        tiles_w = max(2, width // 8)
        tiles_h = max(2, (container_h + 7) // 8)

        panel_surface = self.nineslice.render(tiles_w, tiles_h)
        surface.blit(panel_surface, (x, y))

        state_symbol = "[-]" if (self.is_unfolded or self.is_drag_active) else "[+]"
        title_text = f"{state_symbol} DRIVERS [{self.allowed_slots}]"
        title = font_mgr.render(title_text, color=GREEN_TERMINAL, size="tiny")
        surface.blit(title, (x + 6, y + 7))

        for render_idx, (slot_idx, mounted_file) in enumerate(visible_slots):
            sy = y + top_offset + render_idx * (slot_h + padding)
            slot_rect = pygame.Rect(x + 4, sy, width - 8, slot_h)

            if mounted_file and mounted_file in self.driver_registry:
                driver = self.driver_registry[mounted_file]
                driver.draw(surface, slot_rect.x, slot_rect.y, slot_rect.width, slot_rect.height)
            else:
                pygame.draw.rect(surface, (20, 50, 40), slot_rect, 1)
                empty_txt = font_mgr.render("[FREE SLOT]", color=GREEN_DIM, size="tiny")
                surface.blit(empty_txt, (slot_rect.x + 6, slot_rect.y + 3))
