from enum import IntEnum
import pygame

class PlayerState(IntEnum):
    INIT = 0
    SPAWN = 1
    MOVING = 2
    PHREAKING = 3
    ISHUNTED = 4
    ISDEAD = 5

class PlayerController:
    """
    Kapselt den Spielerzustand und die Grid-Navigation.
    Visual: Pulsing Cyan Node (8x8 px).
    """
    def __init__(self, start_x: int, start_y: int) -> None:
        self.grid_x = start_x
        self.grid_y = start_y
        self.state = PlayerState.INIT
        
        # Sub-pixel interpolation coordinates (Q16.16)
        self.fx = start_x << 16
        self.fy = start_y << 16
        
        self.target_path = []
        self.speed = 20 << 16
        
        from src.utils.animations import TargetLockAnim
        self.move_marker = TargetLockAnim((0, 255, 0), (0, 100, 0))
        
    def init(self) -> None:
        self.state = PlayerState.SPAWN
        
    def set_path(self, path: list[tuple[int, int]]) -> None:
        """Legt einen neuen Navigationspfad fest."""
        self.target_path = path
        if self.target_path:
            self.state = PlayerState.MOVING
            self.move_marker.trigger()
            
    def update(self, dt: float) -> None:
        self.move_marker.update(dt)
        if self.state == PlayerState.MOVING:
            self._update_movement(dt)
            
    def _update_movement(self, dt: float) -> None:
        if not self.target_path:
            self.state = PlayerState.INIT
            self.move_marker.stop()
            return
            
        target_x, target_y = self.target_path[0]
        
        target_fx = target_x << 16
        target_fy = target_y << 16
        
        speed = int(self.speed * dt)

        # Annäherung X
        if self.fx < target_fx:
            self.fx = min(self.fx + speed, target_fx)
        elif self.fx > target_fx:
            self.fx = max(self.fx - speed, target_fx)
            
        # Annäherung Y
        if self.fy < target_fy:
            self.fy = min(self.fy + speed, target_fy)
        elif self.fy > target_fy:
            self.fy = max(self.fy - speed, target_fy)
            
        # Wenn Ziel erreicht, nächster Wegpunkt
        if self.fx == target_fx and self.fy == target_fy:
            self.grid_x = target_x
            self.grid_y = target_y
            self.target_path.pop(0)

    def draw(self, surface: pygame.Surface, camera_offset_x: int, camera_offset_y: int, zoom: float = 1.0, show_target_anim: bool = True) -> None:
        # Visual: 8x8 Cyan Circle interpolated, adjusted for zoom
        screen_x = int((((self.fx * 8) >> 16) - camera_offset_x) * zoom)
        screen_y = int((((self.fy * 8) >> 16) - camera_offset_y) * zoom)
        radius = int(4 * zoom)
        if radius < 1: radius = 1
        pygame.draw.circle(surface, (0, 255, 255), (screen_x + radius, screen_y + radius), radius)
        
        if self.target_path and show_target_anim:
            final_x, final_y = self.target_path[-1]
            final_screen_x = int((final_x * 8 - camera_offset_x) * zoom)
            final_screen_y = int((final_y * 8 - camera_offset_y) * zoom)
            self.move_marker.draw(surface, final_screen_x + int(4 * zoom), final_screen_y + int(4 * zoom), zoom)
