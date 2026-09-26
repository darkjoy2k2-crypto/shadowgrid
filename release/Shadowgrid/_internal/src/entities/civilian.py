import pygame
import random
from enum import IntEnum
from typing import List, Tuple, Optional, Dict, Any
from src.utils.pathfinding import a_star

class CivilState(IntEnum):
    SPAWNING = 0
    MOVING = 1
    DESPAWNING = 2
    DEAD = 3

class CivilNode:
    """
    Zivile Netzwerkknoten (Traffic & Datentransport).
    Jeder Zivilist hat einen Job & Persönlichkeit. Er spawnt an einem PC, entnimmt dort
    einen Datenanteil und bringt ihn zu einem Ziel-PC (Daten-Ausgleich).
    Wird er von Jack gehackt/ausgeraubt, flieht er zum nächsten Guard-Spot und ruft einen Sentinel herbei!
    """
    
    def __init__(self, source_pc: Any, target_pc: Any, profile: Dict[str, Any], grid: List[List[int]]) -> None:
        self.source_pc = source_pc
        self.target_pc = target_pc
        
        start_x = source_pc.grid_x
        start_y = source_pc.grid_y
        self.grid_x = start_x
        self.grid_y = start_y
        self.grid = grid
        
        self.fx = start_x << 16
        self.fy = start_y << 16
        
        self.target_path = []
        self.state = CivilState.SPAWNING
        self.alpha = 0.0
        
        # Unique Civilian Metadata aus der DB / XML
        self.civ_id = profile.get("id", 0)
        self.name = profile.get("name", "Unknown Node")
        self.gender = profile.get("gender", "Unknown")
        self.age_group = profile.get("age_group", "Unknown")
        self.origin = profile.get("origin", "Unknown")
        self.job = profile.get("job", "Data Courier")
        self.profile_pic = profile.get("image_path") or profile.get("profile_pic", "gfx/civilians/default.png")
        self.story = profile.get("story", "")
        self.comment_jack = profile.get("comment_jack", "")
        self.personality_traits = profile.get("personality_traits", "")
        self.category = profile.get("category", "STANDARD")
        self.dialogue_tree = profile.get("dialogue_tree", None)
        
        # Datentransport vom Quell-Computer
        take_amount = min(random.randint(1, 3), max(0, getattr(source_pc, 'data_count', 0)))
        if hasattr(source_pc, 'data_count'):
            source_pc.data_count = max(0, source_pc.data_count - take_amount)
        self.carried_data = take_amount
        
        self.spawn_sentinel_on_despawn = None
        self.is_robbed_retaliating = False
        
        self.is_pursued = False
        from src.utils.animations import TargetLockAnim
        self.lock_anim = TargetLockAnim((0, 255, 0), (0, 100, 0))
        
        self.is_suspicious = False
        self.suspicion_timer = 0.0
        self.is_robbed = False
        
        # Initialer Schritt: Vom PC-Spot auf dessen dock_tile treten
        if getattr(source_pc, 'dock_tile', None):
            self.target_path = [source_pc.dock_tile]
            
        self.target_dock_tile = target_pc.dock_tile if getattr(target_pc, 'dock_tile', None) else (target_pc.grid_x, target_pc.grid_y)
        self.has_entered_path = False
        self.last_passed_iots = set()

    def update(self, dt: float) -> None:
        if self.is_pursued:
            self.lock_anim.update(dt)
            
        match self.state:
            case CivilState.SPAWNING:
                self.alpha += dt * 255.0 * 2.0  # Fade-in 0.5s
                if self.alpha >= 255.0:
                    self.alpha = 255.0
                    self.state = CivilState.MOVING
                    
            case CivilState.MOVING:
                self._update_movement(dt)
                
            case CivilState.DESPAWNING:
                self.alpha -= dt * 255.0 * 2.0  # Fade-out 0.5s
                if self.alpha <= 0.0:
                    self.alpha = 0.0
                    self.state = CivilState.DEAD

    def _update_movement(self, dt: float) -> None:
        if self.is_suspicious:
            return
            
        if not self.target_path:
            if not self.has_entered_path:
                self.has_entered_path = True
                path = a_star(self.grid, (self.grid_x, self.grid_y), self.target_dock_tile)
                if path:
                    self.target_path = path
                else:
                    self.state = CivilState.DESPAWNING
                    return
            else:
                # Ziel-Knoten erreicht!
                if not self.is_robbed_retaliating and self.carried_data > 0 and hasattr(self.target_pc, 'data_count'):
                    # Daten beim Ziel-Computer ablegen
                    self.target_pc.data_count += self.carried_data
                    self.carried_data = 0
                self.state = CivilState.DESPAWNING
                return
                
        target_x, target_y = self.target_path[0]
        target_fx = target_x << 16
        target_fy = target_y << 16
        
        current_speed = getattr(self, 'speed', 6 << 16 if self.is_robbed_retaliating else 4 << 16)
        speed = int(current_speed * dt)

        if self.fx < target_fx: self.fx = min(self.fx + speed, target_fx)
        elif self.fx > target_fx: self.fx = max(self.fx - speed, target_fx)
            
        if self.fy < target_fy: self.fy = min(self.fy + speed, target_fy)
        elif self.fy > target_fy: self.fy = max(self.fy - speed, target_fy)
            
        if self.fx == target_fx and self.fy == target_fy:
            self.grid_x = target_x
            self.grid_y = target_y
            self.target_path.pop(0)
            
            if not self.target_path and self.has_entered_path:
                if not self.is_robbed_retaliating and self.carried_data > 0 and hasattr(self.target_pc, 'data_count'):
                    self.target_pc.data_count += self.carried_data
                    self.carried_data = 0
                self.state = CivilState.DESPAWNING

    def draw(self, surface: pygame.Surface, camera_offset_x: float, camera_offset_y: float, zoom: float, override_color: Optional[Tuple[int, int, int]] = None, show_target_anim: bool = True) -> None:
        if self.alpha <= 0:
            return
            
        screen_x = int((((self.fx * 8) >> 16) - camera_offset_x) * zoom)
        screen_y = int((((self.fy * 8) >> 16) - camera_offset_y) * zoom)
        radius = int(2.5 * zoom)
        if radius < 1: radius = 1
        
        temp_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        if override_color is not None:
            color = (override_color[0], override_color[1], override_color[2], int(self.alpha))
        else:
            if self.is_robbed_retaliating:
                color = (255, 50, 50, int(self.alpha))  # Rot alarmierter Zivilist flieht zum Guard Spot
            elif getattr(self, 'is_robbed', False):
                color = (100, 100, 100, int(self.alpha))
            else:
                color = (255, 255, 0, int(self.alpha))
        pygame.draw.circle(temp_surface, color, (radius, radius), radius)
        
        draw_x = screen_x + int(4 * zoom) - radius
        draw_y = screen_y + int(4 * zoom) - radius
        
        surface.blit(temp_surface, (draw_x, draw_y))
        
        if show_target_anim:
            if self.is_pursued:
                self.lock_anim.draw(surface, screen_x + int(4 * zoom), screen_y + int(4 * zoom), zoom)
            elif getattr(self, 'is_hovered', False):
                frame_size = int(12 * zoom)
                half = frame_size // 2
                pygame.draw.rect(surface, (0, 255, 0), (screen_x + int(4 * zoom) - half, screen_y + int(4 * zoom) - half, frame_size, frame_size), max(1, int(1 * zoom)))
