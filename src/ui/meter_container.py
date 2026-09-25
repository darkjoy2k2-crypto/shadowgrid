import pygame
from typing import Dict, List, Optional, Tuple
from src.ui.base import UIWindow
from src.ui.theme import theme
from src.ui.nine_slice import NineSliceRenderer
from src.ui.status_meter import StatusMeter
from src.ui.font_manager import font_mgr, GREEN_TERMINAL, GREEN_DIM

class MeterContainer(UIWindow):
    """
    Verschiebbarer, smarter Status Meter Container für Jack's Cyberdeck.
    Unterstützt:
    - Verschieben per Drag & Drop der Titelleiste
    - Tight Stacking (enge Stapelung ohne Hintergrund-Abstände)
    - Smart-Klappfunktion (zeigt im Ruhezustand nur die Titelleiste und relevante Meter)
    - Unfold bei Klick auf die Titelleiste oder beim Dragging aus dem Inventar
    - Rechtsklick-Entladen zurück ins Inventar
    """
    def __init__(self, allowed_slots: int = 5) -> None:
        super().__init__(x=640 - 175, y=12, width=160, height=112, z_index=10, titlebar_height=theme.TITLEBAR_HEIGHT)
        self.max_slots = 5
        self.allowed_slots = min(self.max_slots, max(1, allowed_slots))
        
        # Smart Folding State
        self.is_unfolded = False
        self.is_drag_active = False
        self.unfold_timer = 0.0
        
        # Array der montierten Dateien pro Slot
        # Standardmäßig vorbestückt: threat.bxr, progress.bxr, health.bxr
        self.equipped_slots: List[Optional[str]] = [
            "threat.bxr",
            "progress.bxr",
            "health.bxr",
            None,
            None
        ]
        
        self.nineslice = NineSliceRenderer()
        
        # Registry der unterstützen .bxr Statusmeter Typen
        self.meter_registry: Dict[str, StatusMeter] = {
            "threat.bxr": StatusMeter("THREAT", "T", theme.METER_COLORS["THREAT"]),
            "progress.bxr": StatusMeter("PROGRESS", "P", theme.METER_COLORS["PROGRESS"]),
            "health.bxr": StatusMeter("HEALTH", "H", theme.METER_COLORS["HEALTH"])
        }

    def update(self, dt: float) -> None:
        """Aktualisiert Timer für temporäres Entfalten."""
        if self.unfold_timer > 0:
            self.unfold_timer -= dt

    def set_allowed_slots(self, count: int) -> None:
        """Passt die Anzahl erlaubter Slots an (Höhe passt sich an)."""
        self.allowed_slots = min(self.max_slots, max(1, count))

    def trigger_temp_unfold(self, duration: float = 3.0) -> None:
        """Entfaltet alle Slots temporär für eine bestimmte Zeit (z.B. beim Droppen)."""
        self.unfold_timer = max(self.unfold_timer, duration)

    def get_rect(self, values: Optional[Dict[str, float]] = None) -> pygame.Rect:
        """Gibt das gesamte Bounding-Rect des Containers zurück."""
        if values is None:
            values = {}
        visible_slots = []
        for i in range(self.allowed_slots):
            fname = self.equipped_slots[i]
            if self.should_display_slot(i, fname, values):
                visible_slots.append((i, fname))
        total_visible = len(visible_slots)
        slot_h = 14
        padding = 2
        top_offset = 22
        container_h = top_offset + (total_visible * (slot_h + padding) if total_visible > 0 else 2) + 4
        tiles_h = max(2, (container_h + 7) // 8)
        return pygame.Rect(self.x, self.y, self.width, tiles_h * 8)

    def get_slot_rect(self, slot_idx: int, container_x: int, container_y: int, width: int = 160) -> pygame.Rect:
        """Gibt das Bounding-Rect eines bestimmten Slots bei enger Stapelung zurück."""
        slot_h = 14
        top_offset = 22
        padding = 2
        sy = container_y + top_offset + slot_idx * (slot_h + padding)
        return pygame.Rect(container_x + 4, sy, width - 8, slot_h)

    def handle_titlebar_click(self, mx: int, my: int) -> bool:
        """Klick auf die Titelleiste schaltet das Auf-/Zuklappen um."""
        self.rect_title = pygame.Rect(self.x, self.y, self.width, 16)
        if self.rect_title.collidepoint(mx, my):
            self.is_unfolded = not self.is_unfolded
            return True
        return False

    def _compact_slots(self) -> None:
        """Kompaktiert gebundene Dateien, sodass montierte Leisten stets oben stapeln."""
        mounted = [s for s in self.equipped_slots if s is not None]
        while len(mounted) < self.max_slots:
            mounted.append(None)
        self.equipped_slots = mounted

    def handle_right_click(self, mx: int, my: int, inventory, emotion_engine = None) -> bool:
        """
        Rechtsklick auf eine Statusleiste entlädt die .bxr Datei und legt sie zurück ins Inventar.
        """
        for i in range(self.allowed_slots):
            mounted_file = self.equipped_slots[i]
            if mounted_file:
                slot_rect = self.get_slot_rect(i, self.x, self.y, self.width)
                if slot_rect.collidepoint(mx, my):
                    self.equipped_slots[i] = None
                    self._compact_slots()
                    if hasattr(inventory, 'add_bxr_file'):
                        inventory.add_bxr_file(mounted_file)
                    self.trigger_temp_unfold(1.5)
                    from src.utils.perception_logger import perception_logger
                    perception_logger.log_event("EQUIPMENT_UNMOUNT", {"type": "BXR_METER", "file": mounted_file})
                    return True
        return False

    def equip_file(self, slot_idx: int, filename: str, emotion_engine = None) -> bool:
        """
        Versucht eine .bxr Datei aus dem Inventar in einen Slot zu laden.
        """
        fname = filename.lower()
        if not fname.endswith(".bxr"):
            return False
            
        # Ersten freien Slot wählen wenn slot_idx belegt ist, oder überschreiben
        if slot_idx < 0 or slot_idx >= self.allowed_slots:
            slot_idx = 0
            
        self.equipped_slots[slot_idx] = fname
        self._compact_slots()
        self.trigger_temp_unfold(2.0)
        
        from src.utils.perception_logger import perception_logger
        perception_logger.log_event("EQUIPMENT_MOUNT", {"type": "BXR_METER", "file": fname, "slot": slot_idx})
        return True

    def should_display_slot(self, slot_idx: int, fname: Optional[str], values: Dict[str, float]) -> bool:
        """
        Smart-Funktion: Prüft, ob ein Slot angezeigt werden soll.
        - Wenn unfolded / dragging / temp_unfold: ALLES anzeigen (auch leere Slots).
        - Wenn collapsed (geklappt):
          - threat.bxr: Nur anzeigen wenn threat > 0%
          - progress.bxr: Anzeigen bei 0% bis <100% (ausblenden wenn 100% abgeschlossen)
          - health.bxr: Nur anzeigen wenn health < 100% (beschädigt)
        """
        if self.is_unfolded or self.is_drag_active or self.unfold_timer > 0:
            return True
            
        if not fname:
            return False
            
        if fname == "threat.bxr":
            threat_val = values.get("threat", 0.0)
            return threat_val > 0.001
        elif fname == "progress.bxr":
            prog_val = values.get("progress", 0.0)
            return 0.001 < prog_val < 0.999
        elif fname == "health.bxr":
            hp_val = values.get("health", 1.0)
            return hp_val < 0.999
            
        return True

    def draw(self, surface: pygame.Surface, x: Optional[int] = None, y: Optional[int] = None, values: Optional[Dict[str, float]] = None, width: Optional[int] = None) -> None:
        """Rendert den verschiebbaren Container mit enger Stapelung und Smart Auto-Hiding."""
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
            
        if values is None:
            values = {}
            
        self.rect_title = pygame.Rect(self.x, self.y, self.width, 16)
        
        # Werte an gebundene StatusMeter übergeben
        if "threat" in values and "threat.bxr" in self.meter_registry:
            self.meter_registry["threat.bxr"].value = values["threat"]
        if "progress" in values and "progress.bxr" in self.meter_registry:
            self.meter_registry["progress.bxr"].value = values["progress"]
        if "health" in values and "health.bxr" in self.meter_registry:
            self.meter_registry["health.bxr"].value = values["health"]

        # Filtere sichtbare Slots für Tight Stacking
        visible_slots: List[Tuple[int, Optional[str]]] = []
        for i in range(self.allowed_slots):
            fname = self.equipped_slots[i]
            if self.should_display_slot(i, fname, values):
                visible_slots.append((i, fname))
                
        slot_h = 14
        padding = 2
        top_offset = 22
        
        # Dynamische Container-Höhe eng an gepackte sichtbare Leisten angepasst
        total_visible = len(visible_slots)
        container_h = top_offset + (total_visible * (slot_h + padding) if total_visible > 0 else 2) + 4
        
        tiles_w = max(2, width // 8)
        tiles_h = max(2, (container_h + 7) // 8)
        
        panel_surface = self.nineslice.render(tiles_w, tiles_h)
        surface.blit(panel_surface, (x, y))
        
        # Titelleiste (Klickbar & Verschiebbar)
        state_symbol = "[-]" if (self.is_unfolded or self.is_drag_active) else "[+]"
        title_text = f"{state_symbol} METERS [{self.allowed_slots}]"
        title = font_mgr.render(title_text, color=GREEN_TERMINAL, size="tiny")
        surface.blit(title, (x + 6, y + 7))
        
        # Eng gestapeltes Rendern der sichtbaren Slots (Top Packed)
        for render_idx, (slot_idx, mounted_file) in enumerate(visible_slots):
            sy = y + top_offset + render_idx * (slot_h + padding)
            slot_rect = pygame.Rect(x + 4, sy, width - 8, slot_h)
            
            if mounted_file and mounted_file in self.meter_registry:
                meter = self.meter_registry[mounted_file]
                meter.draw(surface, slot_rect.x, slot_rect.y, slot_rect.width, slot_rect.height)
            else:
                # Minimalistischer Leerer Slot (nur Interfaceborder, kein schwerer Hintergrund)
                pygame.draw.rect(surface, (20, 50, 40), slot_rect, 1)
                empty_txt = font_mgr.render("[FREE SLOT]", color=GREEN_DIM, size="tiny")
                surface.blit(empty_txt, (slot_rect.x + 6, slot_rect.y + 3))
