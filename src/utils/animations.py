import pygame

class TargetLockAnim:
    """
    Rendert eine sich schließende, blinkende Rechteck-Animation (Target-Lock) 
    um einen spezifischen Screen-Punkt.
    """
    def __init__(self, color: tuple[int, int, int], blink_color: tuple[int, int, int], duration: float = 0.33) -> None:
        self.color = color
        self.blink_color = blink_color
        self.duration = duration
        
        self.anim_progress = 1.0
        self.blink_timer = 0.0
        self.active = False
        
    def trigger(self) -> None:
        """Startet die Animation neu."""
        self.anim_progress = 1.0
        self.blink_timer = 0.0
        self.active = True
        
    def stop(self) -> None:
        """Stoppt die Animation."""
        self.active = False
        
    def update(self, dt: float) -> None:
        if not self.active:
            return
            
        self.blink_timer += dt
        
        if self.anim_progress > 0.0:
            speed = 1.0 / self.duration
            self.anim_progress = max(0.0, self.anim_progress - dt * speed)
            
    def draw(self, surface: pygame.Surface, center_x: int, center_y: int, zoom: float) -> None:
        if not self.active:
            return
            
        # Full screen size is ~360 height, we lerp from 400 to 12
        target_size = int(12 * zoom)
        start_size = max(640, 360) # ~ screen size
        
        # Quadratischer LERP für schnellen Start und langsames Einrasten
        current_size = int(target_size + (start_size - target_size) * (self.anim_progress ** 2))
        
        # Blinkendes Target-Lock wenn animation fertig ist
        if self.anim_progress <= 0.0:
            if int(self.blink_timer * 8) % 2 == 0:
                draw_color = self.color
            else:
                draw_color = self.blink_color
        else:
            draw_color = self.color
            
        # Rechteck zeichnen (zentriert)
        half = current_size // 2
        pygame.draw.rect(surface, draw_color, (center_x - half, center_y - half, current_size, current_size), max(1, int(1 * zoom)))
