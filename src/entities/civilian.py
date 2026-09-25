import pygame
import random
from enum import IntEnum
from typing import List, Tuple
from src.utils.pathfinding import a_star

class CivilState(IntEnum):
    SPAWNING = 0
    MOVING = 1
    DESPAWNING = 2
    DEAD = 3

class CivilNode:
    """
    Zivile Netzwerkknoten (Traffic).
    Sie spawnen (Fade-In), bewegen sich zu 3 zufälligen Zielen und despawnen (Fade-Out).
    Visual: Weißer/Grauer kleiner Node (z.B. 6x6 px) ohne Target-Animation.
    """
    
    def __init__(self, start_x: int, start_y: int, grid: List[List[int]]) -> None:
        self.grid_x = start_x
        self.grid_y = start_y
        self.grid = grid
        
        self.fx = start_x << 16
        self.fy = start_y << 16
        
        self.target_path = []
        self.state = CivilState.SPAWNING
        
        self.alpha = 0.0
        self.moves_left = 3
        
        self.is_pursued = False
        from src.utils.animations import TargetLockAnim
        self.lock_anim = TargetLockAnim((0, 255, 0), (0, 100, 0))
        
        self.is_suspicious = False
        self.suspicion_timer = 0.0
        
        # Cache valid floor tiles
        self.floor_tiles = []
        for y in range(len(grid)):
            for x in range(len(grid[0])):
                if grid[y][x] in (0, 2):
                    self.floor_tiles.append((x, y))

    def update(self, dt: float) -> None:
        if self.is_pursued:
            self.lock_anim.update(dt)
            
        match self.state:
            case CivilState.SPAWNING:
                self.alpha += dt * 255.0 * 2.0 # Fade in 0.5s
                if self.alpha >= 255.0:
                    self.alpha = 255.0
                    self.state = CivilState.MOVING
                    
            case CivilState.MOVING:
                self._update_movement(dt)
                
            case CivilState.DESPAWNING:
                self.alpha -= dt * 255.0 * 2.0 # Fade out 0.5s
                if self.alpha <= 0.0:
                    self.alpha = 0.0
                    self.state = CivilState.DEAD

    def _update_movement(self, dt: float) -> None:
        if self.is_suspicious:
            # Stoppt sofort, wenn misstrauisch
            return
            
        if not self.target_path:
            if self.moves_left <= 0:
                self.state = CivilState.DESPAWNING
                return
                
            if not self.floor_tiles:
                self.state = CivilState.DESPAWNING
                return
                
            goal = random.choice(self.floor_tiles)
            start_node = (self.grid_x, self.grid_y)
            path = a_star(self.grid, start_node, goal)
            
            if path:
                self.target_path = path
                self.moves_left -= 1
            else:
                # If no path found, try again next frame or just despawn
                self.moves_left -= 1
                return
                
        target_x, target_y = self.target_path[0]
        target_fx = target_x << 16
        target_fy = target_y << 16
        
        # Geschwindigkeit wie Sentinels (4 tiles/s), anpassbar durch Scanners
        current_speed = getattr(self, 'speed', 4 << 16)
        speed = int(current_speed * dt)

        if self.fx < target_fx: self.fx = min(self.fx + speed, target_fx)
        elif self.fx > target_fx: self.fx = max(self.fx - speed, target_fx)
            
        if self.fy < target_fy: self.fy = min(self.fy + speed, target_fy)
        elif self.fy > target_fy: self.fy = max(self.fy - speed, target_fy)
            
        if self.fx == target_fx and self.fy == target_fy:
            self.grid_x = target_x
            self.grid_y = target_y
            self.target_path.pop(0)

    def draw(self, surface: pygame.Surface, camera_offset_x: float, camera_offset_y: float, zoom: float, override_color: Optional[Tuple[int, int, int]] = None, show_target_anim: bool = True) -> None:
        if self.alpha <= 0:
            return
            
        screen_x = int((((self.fx * 8) >> 16) - camera_offset_x) * zoom)
        screen_y = int((((self.fy * 8) >> 16) - camera_offset_y) * zoom)
        radius = int(2.5 * zoom)
        if radius < 1: radius = 1
        
        # Rendern mit Alpha Channel
        temp_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        if override_color is not None:
            color = (override_color[0], override_color[1], override_color[2], int(self.alpha))
        else:
            color = (100, 100, 100, int(self.alpha)) if getattr(self, 'is_robbed', False) else (255, 255, 0, int(self.alpha))
        pygame.draw.circle(temp_surface, color, (radius, radius), radius)
        
        # Center coordinates
        draw_x = screen_x + int(4 * zoom) - radius
        draw_y = screen_y + int(4 * zoom) - radius
        
        surface.blit(temp_surface, (draw_x, draw_y))
        
        if show_target_anim:
            if self.is_pursued:
                self.lock_anim.draw(surface, screen_x + int(4 * zoom), screen_y + int(4 * zoom), zoom)
            elif getattr(self, 'is_hovered', False):
                # Einfacher grüner Rahmen ohne Animation
                frame_size = int(12 * zoom)
                half = frame_size // 2
                pygame.draw.rect(surface, (0, 255, 0), (screen_x + int(4 * zoom) - half, screen_y + int(4 * zoom) - half, frame_size, frame_size), max(1, int(1 * zoom)))
