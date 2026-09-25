import pygame
from typing import List, Optional, Tuple, Dict, Any
from src.ui.base import UIWindow
from src.ui.theme import theme
from src.ui.nine_slice import NineSliceRenderer
from src.ui.font_manager import font_mgr, GREEN_TERMINAL, GREEN_BRIGHT, GREEN_DIM, RED_ALERT

class InventoryWindow(UIWindow):
    """
    Jack's Cyberdeck Directory Inventory.
    Unterstützt:
    - Pfad-Navigation in Jack's virtueller Cyberdeck-Ordnerhierarchie (/sys/deck/files/ etc.)
    - Merken des letzten Pfads beim Öffnen / Schließen
    - Alphabetische Sortierung: /.. oben, Ordner mit '/' davor, Dateien darunter
    - Kein störendes [FILE]-Text-Overlap für reguläre Dateien
    - Cyber-Fantasie-Systemdateien (.bin, .dat, .sys, .enc, .log)
    - Grüner Scrollbar-Slider & Mausrad-Scrolling
    """
    def __init__(self) -> None:
        super().__init__(x=440, y=180, width=180, height=140, z_index=20, titlebar_height=22)
        self.active = False
        self.nineslice = NineSliceRenderer()
        
        # Aktueller Verzeichnispfad (Standard: /sys/deck/files/sensors)
        self.current_path = "/sys/deck/files/sensors"
        self.scroll_offset = 0
        self.max_visible_items = 5
        
        # Virtuelles Dateisystem von Jack's Cyberdeck
        self.fs_tree: Dict[str, Dict[str, List[str]]] = {
            "/": {
                "dirs": ["net", "sys", "usr"],
                "files": ["readme.txt"]
            },
            "/net": {
                "dirs": [],
                "files": ["chiba_node.tap", "grid_gateway.soc"]
            },
            "/sys": {
                "dirs": ["deck", "kernel"],
                "files": ["boot.config", "mem_dump.hex"]
            },
            "/sys/kernel": {
                "dirs": [],
                "files": ["core_patch.bin", "vmm_swap.sys"]
            },
            "/sys/deck": {
                "dirs": ["drivers", "files"],
                "files": ["deck_os.sys"]
            },
            "/sys/deck/drivers": {
                "dirs": [],
                "files": ["com_chip.drv", "optic_link.sys"]
            },
            "/sys/deck/files": {
                "dirs": ["cache", "logs", "sensors"],
                "files": ["kernel_patch.bin", "system_log.dat", "ice_breaker.exe", "shadowrun_data.enc"]
            },
            "/sys/deck/files/cache": {
                "dirs": [],
                "files": ["temp_buffer.tmp"]
            },
            "/sys/deck/files/logs": {
                "dirs": [],
                "files": ["port_scan.log", "trace_decay.log"]
            },
            "/sys/deck/files/sensors": {
                "dirs": [],
                "files": []
            },
            "/usr": {
                "dirs": ["jack"],
                "files": ["contacts.db"]
            },
            "/usr/jack": {
                "dirs": [],
                "files": ["deck_key.pem", "jack_portrait.bmp", "matrix_journal.log"]
            }
        }
        
        # Dynamische BXR-Meter-Dateien im Sensor-Verzeichnis
        self.dynamic_bxr_files: List[str] = []
        
        # Dynamische DRV-Treiber-Dateien im Treiber-Verzeichnis (/sys/deck/drivers)
        self.dynamic_drv_files: List[str] = ["ucam.drv"]
        
        # Drag State für Items
        self.dragged_file: Optional[str] = None
        self.drag_mx = 0
        self.drag_my = 0

    def add_bxr_file(self, filename: str) -> None:
        """Fügt eine entladene BXR-Datei in Jack's Sensor-Verzeichnis (/sys/deck/files/sensors) ein."""
        if filename and filename not in self.dynamic_bxr_files:
            self.dynamic_bxr_files.append(filename)

    def add_drv_file(self, filename: str) -> None:
        """Fügt eine entladene DRV-Datei in Jack's Treiber-Verzeichnis (/sys/deck/drivers) ein."""
        if filename and filename not in self.dynamic_drv_files:
            self.dynamic_drv_files.append(filename)

    @property
    def files(self) -> List[str]:
        """Gibt alle Dateien im aktuellen Verzeichnis inklusive gebundener BXR/DRV-Dateien zurück."""
        node = self.fs_tree.get(self.current_path, {"dirs": [], "files": []})
        reg_files = list(node["files"])
        if self.current_path == "/sys/deck/files/sensors":
            for bxr in self.dynamic_bxr_files:
                if bxr not in reg_files:
                    reg_files.append(bxr)
        elif self.current_path == "/sys/deck/drivers":
            for drv in self.dynamic_drv_files:
                if drv not in reg_files:
                    reg_files.append(drv)
        return reg_files

    @property
    def is_window_dragging(self) -> bool:
        return self.is_dragging

    @is_window_dragging.setter
    def is_window_dragging(self, value: bool) -> None:
        self.is_dragging = value

    def toggle(self) -> None:
        """Schaltet das Inventarfenster ein/aus (behält den Pfad bei)."""
        self.active = not self.active
        if not self.active:
            self.dragged_file = None
            self.is_window_dragging = False

    def get_entries(self) -> List[Tuple[str, str]]:
        """
        Erstellt die sortierte Eintragsliste für das aktuelle Verzeichnis:
        1. /.. (falls nicht im Root-Verzeichnis)
        2. Unterverzeichnisse (alphabetisch)
        3. Dateien (alphabetisch)
        Format: (entry_type, display_name) -> ('UP', '/..'), ('DIR', '/logs'), ('FILE', 'system.dat')
        """
        entries: List[Tuple[str, str]] = []
        
        # 1. Parent-Verzeichnis /..
        if self.current_path != "/":
            entries.append(("UP", "/.."))
            
        # 2. Subverzeichnisse (alphabetisch)
        node = self.fs_tree.get(self.current_path, {"dirs": [], "files": []})
        for d in sorted(node["dirs"]):
            entries.append(("DIR", f"/{d}"))
            
        # 3. Dateien (alphabetisch, inklusive BXR-Dateien)
        current_files = self.files
        for f in sorted(current_files):
            entries.append(("FILE", f))
            
        return entries

    def handle_scroll(self, y_offset: int) -> None:
        """Scrollt die Liste nach oben / unten per Mausrad."""
        if not self.active:
            return
        entries = self.get_entries()
        max_scroll = max(0, len(entries) - self.max_visible_items)
        if y_offset > 0:
            self.scroll_offset = max(0, self.scroll_offset - 1)
        elif y_offset < 0:
            self.scroll_offset = min(max_scroll, self.scroll_offset + 1)

    def navigate_to_parent(self) -> None:
        """Navigiert eine Ebene im Verzeichnisbaum nach oben."""
        if self.current_path == "/":
            return
        parts = [p for p in self.current_path.split("/") if p]
        if parts:
            parts.pop()
            self.current_path = "/" + "/".join(parts) if parts else "/"
        else:
            self.current_path = "/"
        self.scroll_offset = 0

    def navigate_into(self, dir_name: str) -> None:
        """Navigiert in ein Unterverzeichnis."""
        clean_name = dir_name.lstrip("/")
        new_path = f"{self.current_path}/{clean_name}".replace("//", "/")
        if new_path in self.fs_tree:
            self.current_path = new_path
            self.scroll_offset = 0

    def get_file_rect(self, render_index: int) -> pygame.Rect:
        """Gibt das Bounding-Rect eines sichtbaren Eintrags zurück."""
        item_h = 18
        top_offset = 28
        return pygame.Rect(self.x + 8, self.y + top_offset + render_index * item_h, self.width - 24, item_h)

    def handle_mouse_down(self, mx: int, my: int, container = None, driver_container = None, text_log_modal = None, emotion_engine = None) -> bool:
        """Prüft Klicks auf Ordner, /.., Dateien oder Fenster-Titelleiste."""
        if not self.active:
            return False
            
        self.rect_title = pygame.Rect(self.x, self.y, self.width, 22)
        entries = self.get_entries()
        visible_entries = entries[self.scroll_offset : self.scroll_offset + self.max_visible_items]
        
        # 1. Eintrags-Klicks prüfen
        for idx, (entry_type, name) in enumerate(visible_entries):
            rect = self.get_file_rect(idx)
            if rect.collidepoint(mx, my):
                if entry_type == "UP":
                    self.navigate_to_parent()
                    return True
                elif entry_type == "DIR":
                    self.navigate_into(name)
                    return True
                elif entry_type == "FILE":
                    if (name.endswith(".log") or name.endswith(".dat")) and text_log_modal:
                        from src.utils.perception_logger import perception_logger
                        thoughts = perception_logger.get_all_past_thought_logs()
                        full_file_path = f"{self.current_path}/{name}".replace("//", "/")
                        text_log_modal.open_log(f"LOG: {full_file_path}", thoughts)
                        if emotion_engine:
                            emotion_engine.trigger_existential_freakout()
                        return True

                    self.dragged_file = name
                    self.drag_mx = mx
                    self.drag_my = my
                    if container:
                        container.is_drag_active = True
                    if driver_container:
                        driver_container.is_drag_active = True
                    return True
                    
        # 2. Titelleiste zum Verschieben prüfen
        if self.rect_title.collidepoint(mx, my):
            self.is_window_dragging = True
            self.drag_offset_x = self.x - mx
            self.drag_offset_y = self.y - my
            return True
            
        return False

    def handle_right_click(self, mx: int, my: int, container, error_modal, driver_container = None, emotion_engine = None) -> bool:
        """
        Rechtsklick-Handling:
        - .bxr -> MeterContainer (Sensoren)
        - .drv -> DriverContainer (Treiber, Stärkster ersetzt existierende)
        - Sonstige -> Silent No-Op
        """
        if not self.active:
            return False
            
        entries = self.get_entries()
        visible_entries = entries[self.scroll_offset : self.scroll_offset + self.max_visible_items]
        
        for idx, (entry_type, name) in enumerate(visible_entries):
            rect = self.get_file_rect(idx)
            if rect.collidepoint(mx, my):
                if entry_type in ("UP", "DIR"):
                    return True
                    
                if name.endswith(".bxr") and container:
                    free_slot = -1
                    for s_idx in range(container.allowed_slots):
                        if container.equipped_slots[s_idx] is None:
                            free_slot = s_idx
                            break
                            
                    if free_slot != -1:
                        container.equip_file(free_slot, name, emotion_engine=emotion_engine)
                        if name in self.dynamic_bxr_files:
                            self.dynamic_bxr_files.remove(name)
                    else:
                        error_modal.trigger("NO FREE SLOT IN DECK METERS CONTAINER!")
                    return True

                elif name.endswith(".drv") and driver_container:
                    success, replaced_driver = driver_container.equip_file(0, name, self, emotion_engine=emotion_engine)
                    if success:
                        if name in self.dynamic_drv_files:
                            self.dynamic_drv_files.remove(name)
                        if replaced_driver:
                            self.add_drv_file(replaced_driver)
                    return True
                    
                return True
        return False

    def handle_mouse_motion(self, mx: int, my: int) -> None:
        """Aktualisiert Drag-Mauskoordinaten."""
        if self.dragged_file:
            self.drag_mx = mx
            self.drag_my = my
        if self.is_window_dragging:
            self.x = mx + self.drag_offset_x
            self.y = my + self.drag_offset_y

    def handle_mouse_up(self, mx: int, my: int, container, error_modal, driver_container = None, emotion_engine = None) -> bool:
        """Beendet den Drag-Vorgang und prüft BXR / DRV Dropping."""
        self.is_window_dragging = False
        if container:
            container.is_drag_active = False
        if driver_container:
            driver_container.is_drag_active = False
            
        if not self.dragged_file:
            return False
            
        dropped_file = self.dragged_file
        self.dragged_file = None
        
        # 1. Kollision mit MeterContainer Slots (.bxr)
        if container and dropped_file.endswith(".bxr"):
            for i in range(container.allowed_slots):
                slot_rect = container.get_slot_rect(i, container.x, container.y, container.width)
                if slot_rect.collidepoint(mx, my):
                    prev_file = container.equipped_slots[i]
                    success = container.equip_file(i, dropped_file, emotion_engine=emotion_engine)
                    if success:
                        if dropped_file in self.dynamic_bxr_files:
                            self.dynamic_bxr_files.remove(dropped_file)
                        if prev_file and prev_file.endswith(".bxr"):
                            self.add_bxr_file(prev_file)
                    return True

        # 2. Kollision mit DriverContainer Slots (.drv)
        if driver_container and dropped_file.endswith(".drv"):
            for i in range(driver_container.allowed_slots):
                slot_rect = driver_container.get_slot_rect(i, driver_container.x, driver_container.y, driver_container.width)
                if slot_rect.collidepoint(mx, my):
                    success, replaced_driver = driver_container.equip_file(i, dropped_file, self, emotion_engine=emotion_engine)
                    if success:
                        if dropped_file in self.dynamic_drv_files:
                            self.dynamic_drv_files.remove(dropped_file)
                        if replaced_driver:
                            self.add_drv_file(replaced_driver)
                    return True
                
        return False

    def draw(self, surface: pygame.Surface) -> None:
        """Rendert das Verzeichnis-Fenster mit sauberer Pfad-Header, Eintragsliste & Scrollbar."""
        if self.active:
            tiles_w = max(2, self.width // 8)
            tiles_h = max(2, self.height // 8)
            panel_surface = self.nineslice.render(tiles_w, tiles_h)
            surface.blit(panel_surface, (self.x, self.y))
            
            # Pfad-Header (in Phosphor Grün)
            path_display = self.current_path.upper()
            if len(path_display) > 23:
                path_display = f"..{path_display[-20:]}"
            header_txt = font_mgr.render(path_display, color=GREEN_TERMINAL, size="tiny")
            surface.blit(header_txt, (self.x + 8, self.y + 5))
            
            pygame.draw.line(surface, (0, 150, 100), (self.x + 8, self.y + 22), (self.x + self.width - 8, self.y + 22), 1)
            
            entries = self.get_entries()
            visible_entries = entries[self.scroll_offset : self.scroll_offset + self.max_visible_items]
            
            # Einträge rendern
            for idx, (entry_type, name) in enumerate(visible_entries):
                rect = self.get_file_rect(idx)
                
                pygame.draw.rect(surface, (10, 25, 20), rect)
                pygame.draw.rect(surface, (20, 55, 45), rect, 1)
                
                if entry_type == "UP":
                    txt = font_mgr.render(name, color=GREEN_TERMINAL, size="tiny")
                    surface.blit(txt, (rect.x + 6, rect.y + 3))
                elif entry_type == "DIR":
                    txt = font_mgr.render(f"{name}/", color=(0, 220, 255), size="tiny")
                    surface.blit(txt, (rect.x + 6, rect.y + 3))
                elif entry_type == "FILE":
                    is_bxr = name.endswith(".bxr")
                    color = GREEN_BRIGHT if is_bxr else (160, 170, 175)
                    fn_txt = font_mgr.render(name, color=color, size="tiny")
                    surface.blit(fn_txt, (rect.x + 6, rect.y + 3))

            # Grüner Scrollbar-Slider Indicator auf der rechten Seite
            total_items = len(entries)
            if total_items > self.max_visible_items:
                track_x = self.x + self.width - 12
                track_y = self.y + 28
                track_h = self.max_visible_items * 18
                
                # Scroll-Schiene (dunkler Strich)
                pygame.draw.line(surface, (0, 60, 50), (track_x + 1, track_y), (track_x + 1, track_y + track_h), 2)
                
                # Slider Thumb
                max_scroll = max(1, total_items - self.max_visible_items)
                thumb_h = max(8, int(track_h * (self.max_visible_items / total_items)))
                thumb_y = track_y + int((self.scroll_offset / max_scroll) * (track_h - thumb_h))
                
                thumb_rect = pygame.Rect(track_x, thumb_y, 4, thumb_h)
                pygame.draw.rect(surface, (0, 255, 120), thumb_rect)

        # Schwebendes Drag-Icon rendern (beim Ziehen)
        if self.dragged_file:
            ghost_w, ghost_h = 110, 20
            gx = self.drag_mx - ghost_w // 2
            gy = self.drag_my - ghost_h // 2
            
            ghost_surface = pygame.Surface((ghost_w, ghost_h), pygame.SRCALPHA)
            ghost_surface.fill((0, 40, 35, 220))
            pygame.draw.rect(ghost_surface, (0, 255, 200), (0, 0, ghost_w, ghost_h), 1)
            
            is_bxr = self.dragged_file.endswith(".bxr")
            txt_color = GREEN_BRIGHT if is_bxr else RED_ALERT
            
            txt = font_mgr.render(self.dragged_file, color=txt_color, size="tiny")
            ghost_surface.blit(txt, (4, 3))
            
            surface.blit(ghost_surface, (gx, gy))
