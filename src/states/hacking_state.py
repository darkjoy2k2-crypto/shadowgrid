import pygame
from src.core.state_machine import State
from typing import Any
import random

class HackingState(State):
    """
    Minispiel: Trace-Breaker (Bulls-Eye Match / Timing-Puzzle).
    Legt sich visuell über den HubState (via Parent-Rendering).
    """
    
    def init(self) -> None:
        self.font_large = pygame.font.SysFont(None, 24)
        self.font_small = pygame.font.SysFont(None, 16)
        
        self.cursor_x = 0.0
        self.cursor_speed = 300.0 # Pixel pro Sekunde
        self.direction = 1
        
        # Target Zone
        self.target_center = random.randint(50, 250)
        self.target_width = 30
        
        self.bar_width = 300
        self.bar_x = (640 - self.bar_width) // 2
        self.bar_y = 180
        
        self.result = 0 # 0=Running, 1=Success, -1=Fail
        self.timer = 0.0
        
    def handle_event(self, event: Any) -> None:
        if self.result != 0:
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                self.sm.change_state("HUBGAME")
            return
            
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self._attempt_hack()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._attempt_hack()
            
    def _attempt_hack(self) -> None:
        # Prüfe ob Cursor in der Target-Zone ist
        dist = abs(self.cursor_x - self.target_center)
        hub = self.sm.states.get("HUBGAME")
        
        if dist <= self.target_width // 2:
            self.result = 1 # Success
            if hub:
                hub.data_fragments += 1
                # Terminal "leersaugen" und neues spawnen
                hub.grid[hub.player.grid_y][hub.player.grid_x] = 0
                hub.spawn_terminal()
        else:
            self.result = -1 # Fail
            if hub:
                # Drastische Alarm-Eskalation (+30% sofort)
                hub.threat_level = min(100.0, hub.threat_level + 30.0)
                # Alle Sentinels auf den Ursprung des Hacks aufmerksam machen
                for g in hub.sentinels:
                    g.on_trace_detected(hub.player.grid_x, hub.player.grid_y)

    def update(self, dt: float) -> None:
        if self.result != 0:
            return
            
        self.cursor_x += self.cursor_speed * self.direction * dt
        if self.cursor_x >= self.bar_width:
            self.cursor_x = self.bar_width
            self.direction = -1
        elif self.cursor_x <= 0:
            self.cursor_x = 0
            self.direction = 1
            
    def update_draw(self) -> None:
        surface = self.sm.context.get("native_surface")
        if not surface:
            return
            
        hub = self.sm.states.get("HUBGAME")
        if hub: 
            hub.update_draw()
        
        # Dark Overlay
        overlay = pygame.Surface((640, 360), pygame.SRCALPHA)
        overlay.fill((0, 5, 10, 200))
        surface.blit(overlay, (0, 0))
        
        # UI Rahmen
        pygame.draw.rect(surface, (0, 255, 150), (self.bar_x - 10, self.bar_y - 40, self.bar_width + 20, 80), 1)
        
        title = self.font_large.render("SYSTEM OVERRIDE", False, (0, 255, 200))
        surface.blit(title, (self.bar_x, self.bar_y - 30))
        
        # Base Bar
        pygame.draw.rect(surface, (50, 50, 50), (self.bar_x, self.bar_y, self.bar_width, 20))
        
        # Target Zone
        target_rect = (self.bar_x + self.target_center - self.target_width // 2, self.bar_y, self.target_width, 20)
        pygame.draw.rect(surface, (255, 150, 0), target_rect)
        
        # Cursor
        cursor_rect = (self.bar_x + int(self.cursor_x) - 2, self.bar_y - 5, 4, 30)
        pygame.draw.rect(surface, (255, 255, 255), cursor_rect)
        
        if self.result == 1:
            res_txt = self.font_large.render("ACCESS GRANTED - DATEN EXTRAHIERT", False, (0, 255, 0))
            surface.blit(res_txt, (self.bar_x, self.bar_y + 30))
        elif self.result == -1:
            res_txt = self.font_large.render("ACCESS DENIED - TRACE ESCALATED", False, (255, 0, 0))
            surface.blit(res_txt, (self.bar_x, self.bar_y + 30))
