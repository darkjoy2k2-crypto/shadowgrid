import os
import pygame
import math
import random
from typing import Optional, Tuple, Dict
from src.utils.animations import TargetLockAnim

# Sprite Cache für 16x16 PNG-Icons aus src/gfx/
_IOT_SPRITES: Dict[str, Optional[pygame.Surface]] = {}

def _get_iot_sprite(device_type: str) -> Optional[pygame.Surface]:
    if device_type not in _IOT_SPRITES:
        filename = f"{device_type}.png"
        path = os.path.join("src", "gfx", filename)
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        if os.path.exists(path):
            try:
                _IOT_SPRITES[device_type] = pygame.image.load(path).convert_alpha()
            except Exception as e:
                print(f"[IoTNode] Failed to load sprite {path}: {e}")
                _IOT_SPRITES[device_type] = None
        else:
            _IOT_SPRITES[device_type] = None
    return _IOT_SPRITES[device_type]

class IoTNode:
    """
    IoT Surveillance Devices (16x16 px Sprites):
    - Watcher (watcher.png): Gedockt am Grid-Rand mit 1 Spurbreite Abstand zum Pfad.
    - Listener (listener.png): Gedockt am Grid-Rand mit 1 Spurbreite Abstand zum Pfad.
    - Scanner (scanner.png): Liegt mitten auf dem Weg (Pfad-Tile) und verlangsamt passierende Entitäten.
    """
    def __init__(self, grid_x: int, grid_y: int, device_type: str = "watcher", dock_tile: Optional[Tuple[int, int]] = None, dock_dir: Optional[Tuple[int, int]] = None) -> None:
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.fx = grid_x << 16
        self.fy = grid_y << 16
        self.dock_tile = dock_tile  # (dock_x, dock_y) Pfad-Tile
        self.dock_dir = dock_dir    # (dx, dy) Vektor vom Pfad zum IoT
        
        dev = device_type.lower()
        if dev in ("camera", "watcher"):
            self.device_type = "watcher"
        elif dev in ("audio", "microphone", "listener"):
            self.device_type = "listener"
        else:
            self.device_type = "scanner"
            
        self.target_path = []
        self.state = 1
        self.alpha = 255.0
        
        self.is_hackable = (self.device_type != "scanner")
        self.is_pursued = False
        self.lock_anim = TargetLockAnim((0, 255, 0), (0, 100, 0))
        
        self.is_suspicious = False
        self.suspicion_timer = 0.0
        self.is_robbed = False  # Same flag as civs for completion state
        self.is_hacked = False
        self.is_hovered = False
        self.pulse_timer = random.uniform(0.0, 3.14)

    def update(self, dt: float) -> None:
        self.pulse_timer += dt * 3.0
        if self.is_pursued:
            self.lock_anim.update(dt)

    def draw(self, surface: pygame.Surface, camera_offset_x: float, camera_offset_y: float, zoom: float, override_color: Optional[Tuple[int, int, int]] = None, show_target_anim: bool = True) -> None:
        if self.alpha <= 0:
            return
            
        screen_x = int((((self.fx * 8) >> 16) - camera_offset_x) * zoom)
        screen_y = int((((self.fy * 8) >> 16) - camera_offset_y) * zoom)
        
        cx = screen_x + int(4 * zoom)
        cy = screen_y + int(4 * zoom)
        
        # 1. Trace-Stub Verbindung zeichnen (führt vom Pfad exakt an den RAND des 16x16 IoTs)
        if self.dock_tile and self.dock_dir and self.device_type in ("watcher", "listener"):
            dock_x, dock_y = self.dock_tile
            dx, dy = self.dock_dir
            
            dock_cx = int(((dock_x * 8 - camera_offset_x) + 4) * zoom)
            dock_cy = int(((dock_y * 8 - camera_offset_y) + 4) * zoom)
            
            half_sprite = int(8 * zoom)
            edge_x = cx - dx * half_sprite
            edge_y = cy - dy * half_sprite
            
            stub_color = (0, 150, 100) if override_color is None else override_color
            if self.is_robbed or self.is_hacked:
                stub_color = (60, 60, 60)
            pygame.draw.line(surface, stub_color, (dock_cx, dock_cy), (edge_x, edge_y), max(1, int(1.5 * zoom)))

        # 2. Render 16x16 Sprite
        sprite = _get_iot_sprite(self.device_type)
        sprite_size = max(1, int(16 * zoom))
        
        if sprite:
            if zoom != 1.0:
                scaled_sprite = pygame.transform.scale(sprite, (sprite_size, sprite_size)).convert_alpha()
            else:
                scaled_sprite = sprite.copy()
                
            if self.is_robbed or self.is_hacked:
                dark_overlay = pygame.Surface(scaled_sprite.get_size(), pygame.SRCALPHA)
                dark_overlay.fill((80, 80, 80, 200))
                scaled_sprite.blit(dark_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            elif override_color is not None:
                color_overlay = pygame.Surface(scaled_sprite.get_size(), pygame.SRCALPHA)
                color_overlay.fill((override_color[0], override_color[1], override_color[2], 255))
                scaled_sprite.blit(color_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
            surface.blit(scaled_sprite, (cx - sprite_size // 2, cy - sprite_size // 2))
        else:
            pulse = math.sin(self.pulse_timer) * 0.5 + 0.5
            box_sz = max(10, int(16 * zoom))
            half = box_sz // 2
            color = override_color if override_color is not None else (0, 220, 255)
            if self.is_robbed or self.is_hacked:
                color = (100, 100, 100)
            pygame.draw.rect(surface, color, (cx - half, cy - half, box_sz, box_sz), max(1, int(2 * zoom)))

        # 3. Ziel- / Hover-Anzeige (nur wenn hackbar)
        if show_target_anim and self.is_hackable:
            if self.is_pursued:
                self.lock_anim.draw(surface, cx, cy, zoom)
            elif self.is_hovered and not (self.is_robbed or self.is_hacked):
                frame_size = int(20 * zoom)
                half = frame_size // 2
                pygame.draw.rect(surface, (0, 255, 0), (cx - half, cy - half, frame_size, frame_size), max(1, int(1.5 * zoom)))
