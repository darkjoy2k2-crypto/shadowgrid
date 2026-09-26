import pygame
import random
from enum import IntEnum
from typing import List, Tuple
from src.utils.pathfinding import a_star
from src.utils.animations import TargetLockAnim

SENTINEL_PROFILES = [
    {
        "id": "maya_cross",
        "name": "Grid-Overseer",
        "raw_name": "Maya Cross",
        "profile_pic": "src/gfx/faces/maya_cross.png",
        "job": "Grid Security Overseer",
        "story": "High-ranking Grid Overseer enforcing strict corporate access control.",
        "comment_jack": "JACK // GRID-OVERSEER. HIGH-GRADE SURVEILLANCE & COUNTER-MEASURES.",
        "gender": "Female",
        "age_group": "Adult (31-36)",
        "origin": "High-Rise Executive Sprawl",
        "personality_traits": "Stealthy, Lethal, Sharp"
    },
    {
        "id": "viktor_reyes",
        "name": "Konzern-Enforcer",
        "raw_name": "Viktor Reyes",
        "profile_pic": "src/gfx/faces/viktor_reyes.png",
        "job": "Konzern Security Enforcer",
        "story": "Brutal Konzern Enforcer specialized in sub-grid runner suppression.",
        "comment_jack": "JACK // KONZERN-ENFORCER. HEAVILY ARMORED AND LETHAL.",
        "gender": "Male",
        "age_group": "Veteran (45-50)",
        "origin": "Sector 7 Industrial",
        "personality_traits": "Careless, Exhausted, Ruthless"
    },
    {
        "id": "sora_takeda",
        "name": "Sentinel-Guard",
        "raw_name": "Sora Takeda",
        "profile_pic": "src/gfx/faces/sora_takeda.png",
        "job": "Tactical Patrol Guard",
        "story": "Tactical Sentinel Patrol Guard monitoring key network nodes.",
        "comment_jack": "JACK // SENTINEL-GUARD. FAST REACTION PATROL UNIT.",
        "gender": "Female",
        "age_group": "Young Adult (22-26)",
        "origin": "Chrome Bay District",
        "personality_traits": "Creative, Rebellious, Technical"
    }
]

_sentinel_profile_counter = 0

class GuardianState(IntEnum):
    PATROL = 0
    TRACE_TRACK = 1
    ALARM_ENGAGE = 2
    RETURN_DESPAWN = 3

class GuardianAI:
    """
    State-Machine für Security Sentinels (Guardians).
    Visual: Roter blinkender 8x8 Node.
    """
    
    def __init__(self, start_x: int, start_y: int, grid: List[List[int]], spawn_guard_node: Optional[Any] = None) -> None:
        global _sentinel_profile_counter
        prof = SENTINEL_PROFILES[_sentinel_profile_counter % len(SENTINEL_PROFILES)]
        _sentinel_profile_counter += 1

        self.grid_x = start_x
        self.grid_y = start_y
        self.state = GuardianState.PATROL
        self.grid = grid
        self.spawn_guard_node = spawn_guard_node
        
        self.fx = start_x << 16
        self.fy = start_y << 16
        
        self.target_path = []
        self.target_dock_node = None
        self.should_despawn = False
        self.blink_timer = 0.0
        
        self.is_investigating = False
        self.investigate_target = None
        
        # Sentinel Abstract Metadata & Intercept Timer
        self.is_sentinel = True
        self.ignore_timer = 0.0
        self.nervousness_level = float(random.randint(50, 99))
        self.name = prof["name"]
        self.raw_name = prof["raw_name"]
        self.profile_pic = prof["profile_pic"]
        self.job = prof["job"]
        self.story = prof["story"]
        self.comment_jack = prof["comment_jack"]
        self.gender = prof["gender"]
        self.age_group = prof["age_group"]
        self.origin = prof["origin"]
        self.personality_traits = prof["personality_traits"]
        
        # Data Collection & Sightings
        self.carried_data = 0
        self.has_jack_sighting = False
        self.delivered_jack_sighting = False
        
        # Target Lock Animation (Rot)
        self.in_view = False
        self.lock_anim = TargetLockAnim((255, 0, 0), (100, 0, 0))

    def update(self, dt: float, docked_nodes: Optional[List[Any]] = None) -> None:
        """Logik-Zyklus der Sentinel State-Machine."""
        self.blink_timer += dt
        self.lock_anim.update(dt)
        if self.ignore_timer > 0:
            self.ignore_timer -= dt
            
        match self.state:
            case GuardianState.PATROL:
                self._update_patrol(dt, docked_nodes)
            case GuardianState.TRACE_TRACK:
                pass
            case GuardianState.ALARM_ENGAGE:
                pass
            case GuardianState.RETURN_DESPAWN:
                pass
                
    def _update_patrol(self, dt: float, docked_nodes: Optional[List[Any]] = None) -> None:
        if self.should_despawn:
            return

        # Wenn kein Pfad vorhanden ist, verarbeite das gerade erreichte Ziel oder wähle ein neues
        if not self.target_path:
            if self.is_investigating:
                self.is_investigating = False
                self.investigate_target = None
                self.target_dock_node = None

            # Prüfen ob wir gerade ein Ziel-Node (IoT oder Guard) erreicht haben
            if self.target_dock_node is not None:
                dev_type = getattr(self.target_dock_node, 'device_type', None)
                if dev_type in ("watcher", "listener"):
                    # IoT leeren und Daten/Sichtungen übernehmen
                    stolen = getattr(self.target_dock_node, 'data_count', 0)
                    self.carried_data += stolen
                    self.target_dock_node.data_count = 0
                    had_sighting = False
                    if dev_type == "watcher" and getattr(self.target_dock_node, 'jack_detected', False):
                        self.has_jack_sighting = True
                        self.target_dock_node.jack_detected = False
                        had_sighting = True
                    
                    from src.utils.perception_logger import perception_logger
                    perception_logger.log_event("SENTINEL_EMPTIED_IOT", {
                        "iot": dev_type,
                        "stolen_data": stolen,
                        "had_jack_sighting": had_sighting,
                        "node": (self.target_dock_node.grid_x, self.target_dock_node.grid_y)
                    })
                    if had_sighting:
                        perception_logger.log_jack_thought(f"JACK // Achtung! Der Sentinel hat Kameradaten aus [{self.target_dock_node.grid_x}, {self.target_dock_node.grid_y}] ausgelesen und marschiert zum Guard Spot!", "SIGHTING_RETRIEVED")
                elif dev_type == "guard":
                    # Daten / Jack-Sichtung an der Wache abliefern
                    if self.has_jack_sighting:
                        self.delivered_jack_sighting = True
                        self.has_jack_sighting = False
                    self.carried_data = 0
                    self.should_despawn = True
                    return
                self.target_dock_node = None

            if docked_nodes:
                if self.carried_data > 0 or self.has_jack_sighting:
                    # Trägt Daten / Sichtung -> Ziel: Nahegelegener Guard Spot!
                    guards = [n for n in docked_nodes if getattr(n, 'device_type', None) == "guard" and getattr(n, 'dock_tile', None) is not None]
                    if self.spawn_guard_node and self.spawn_guard_node in guards:
                        target_node = self.spawn_guard_node
                    elif guards:
                        target_node = min(guards, key=lambda g: abs(g.grid_x - self.grid_x) + abs(g.grid_y - self.grid_y))
                    else:
                        target_node = None
                else:
                    # Sucht Daten -> Priorisiere IoTs (Watcher/Listener) mit Daten oder Jack-Sichtung
                    priority_iots = [n for n in docked_nodes if getattr(n, 'device_type', None) in ("watcher", "listener") and getattr(n, 'dock_tile', None) is not None and (getattr(n, 'data_count', 0) > 0 or getattr(n, 'jack_detected', False))]
                    if priority_iots:
                        target_node = random.choice(priority_iots)
                    else:
                        candidates = [n for n in docked_nodes if getattr(n, 'dock_tile', None) is not None and getattr(n, 'device_type', None) in ("watcher", "listener", "pc")]
                        target_node = random.choice(candidates) if candidates else None

                if target_node:
                    self.target_dock_node = target_node
                    dock_x, dock_y = target_node.dock_tile
                    start_node = (self.grid_x, self.grid_y)
                    path = a_star(self.grid, start_node, (dock_x, dock_y))
                    if path:
                        self.target_path = path
                    else:
                        return
                else:
                    return
            else:
                return
                
        target_x, target_y = self.target_path[0]
        target_fx = target_x << 16
        target_fy = target_y << 16
        
        if not hasattr(self, 'speed'):
            self.speed = 4 << 16
            
        speed = int(self.speed * dt)

        if self.fx < target_fx: self.fx = min(self.fx + speed, target_fx)
        elif self.fx > target_fx: self.fx = max(self.fx - speed, target_fx)
            
        if self.fy < target_fy: self.fy = min(self.fy + speed, target_fy)
        elif self.fy > target_fy: self.fy = max(self.fy - speed, target_fy)
            
        if self.fx == target_fx and self.fy == target_fy:
            self.grid_x = target_x
            self.grid_y = target_y
            self.target_path.pop(0)
            
            # Sub-check: Wenn Ziel-Guard-Spot Pfad komplett abgelaufen ist -> Despawn
            if not self.target_path and self.target_dock_node and getattr(self.target_dock_node, 'device_type', None) == "guard":
                self.should_despawn = True
        
    def on_trace_detected(self, trace_x: int, trace_y: int) -> None:
        if self.state == GuardianState.PATROL:
            self.state = GuardianState.TRACE_TRACK
            path = a_star(self.grid, (self.grid_x, self.grid_y), (trace_x, trace_y))
            if path:
                self.target_path = path

    def draw(self, surface: pygame.Surface, camera_offset_x: float, camera_offset_y: float, zoom: float, override_color: Optional[Tuple[int, int, int]] = None, show_target_anim: bool = True) -> None:
        screen_x = int((((self.fx * 8) >> 16) - camera_offset_x) * zoom)
        screen_y = int((((self.fy * 8) >> 16) - camera_offset_y) * zoom)
        
        # Viewport check (640x360 native)
        # We consider it in view if it's within the screen bounds
        if 0 <= screen_x <= 640 and 0 <= screen_y <= 360:
            if not self.in_view:
                self.in_view = True
                if show_target_anim:
                    self.lock_anim.trigger()
        else:
            if self.in_view:
                self.in_view = False
                self.lock_anim.stop()
            
        radius = int(3 * zoom)
        if radius < 1: radius = 1
        
        # Blink effekt (sinus-basiert oder simpler Timer)
        if override_color is not None:
            color = override_color
        elif int(self.blink_timer * 4) % 2 == 0:
            color = (255, 50, 50)
        else:
            color = (150, 0, 0)
            
        pygame.draw.circle(surface, color, (screen_x + int(4 * zoom), screen_y + int(4 * zoom)), radius)
        
        if getattr(self, 'has_jack_sighting', False):
            from src.ui.font_manager import font_mgr
            sig_txt = font_mgr.render("[!]", color=(255, 0, 0), size="tiny")
            surface.blit(sig_txt, (screen_x + int(4 * zoom) - sig_txt.get_width() // 2, screen_y - int(10 * zoom)))
        
        # Target Lock Animation zeichnen
        if show_target_anim:
            self.lock_anim.draw(surface, screen_x + int(4 * zoom), screen_y + int(4 * zoom), zoom)
