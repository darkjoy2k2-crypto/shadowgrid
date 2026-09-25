import pygame
import random
from enum import IntEnum
from typing import List, Tuple
from src.utils.pathfinding import a_star
from src.utils.animations import TargetLockAnim

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
    
    def __init__(self, start_x: int, start_y: int, grid: List[List[int]]) -> None:
        self.grid_x = start_x
        self.grid_y = start_y
        self.state = GuardianState.PATROL
        self.grid = grid
        
        self.fx = start_x << 16
        self.fy = start_y << 16
        
        self.target_path = []
        self.blink_timer = 0.0
        
        # Target Lock Animation (Rot)
        self.in_view = False
        self.lock_anim = TargetLockAnim((255, 0, 0), (100, 0, 0))
        
        # Cache valid floor tiles for random destination picking
        self.floor_tiles = []
        for y in range(len(grid)):
            for x in range(len(grid[0])):
                if grid[y][x] in (0, 2):
                    self.floor_tiles.append((x, y))

    def update(self, dt: float) -> None:
        """Logik-Zyklus der Sentinel State-Machine."""
        self.blink_timer += dt
        self.lock_anim.update(dt)
            
        match self.state:
            case GuardianState.PATROL:
                self._update_patrol(dt)
            case GuardianState.TRACE_TRACK:
                pass
            case GuardianState.ALARM_ENGAGE:
                pass
            case GuardianState.RETURN_DESPAWN:
                pass
                
    def _update_patrol(self, dt: float) -> None:
        # Wenn kein Pfad vorhanden ist, wähle ein neues zufälliges Ziel und nutze A*
        if not self.target_path:
            if not self.floor_tiles:
                return
            
            # Wähle ein Ziel in der Nähe oder fernab
            goal = random.choice(self.floor_tiles)
            start_node = (self.grid_x, self.grid_y)
            path = a_star(self.grid, start_node, goal)
            
            if path:
                self.target_path = path
            else:
                return
                
        target_x, target_y = self.target_path[0]
        target_fx = target_x << 16
        target_fy = target_y << 16
        
        # Initialize speed if not exists
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
        
        # Target Lock Animation zeichnen
        if show_target_anim:
            self.lock_anim.draw(surface, screen_x + int(4 * zoom), screen_y + int(4 * zoom), zoom)
