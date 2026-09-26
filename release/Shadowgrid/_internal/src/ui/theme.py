import pygame
from typing import Tuple, Dict, Any

class UITheme:
    """
    Shadowgrid Cyberpunk / Sega Genesis 16-Bit UI Theme Engine.
    Inspiriert von pygame-gui's JSON Theme Engine: Trennt visuelles Styling von der Komponenten-Logik.
    """
    # Palette
    COLOR_PHOSPHOR_GREEN: Tuple[int, int, int] = (0, 255, 0)
    COLOR_TERMINAL_GREEN: Tuple[int, int, int] = (0, 255, 0)
    COLOR_DIM_GREEN: Tuple[int, int, int] = (0, 180, 0)
    COLOR_RED_ALERT: Tuple[int, int, int] = (255, 50, 50)
    COLOR_AMBER_WARN: Tuple[int, int, int] = (255, 160, 0)
    COLOR_WHITE_TEXT: Tuple[int, int, int] = (255, 255, 255)
    COLOR_STEEL_GREY: Tuple[int, int, int] = (160, 160, 160)
    
    # Viewport & Panel Backgrounds
    COLOR_VIEWPORT_BG: Tuple[int, int, int] = (0, 0, 0)
    COLOR_FRAME_OUTER_BEVEL: Tuple[int, int, int] = (140, 150, 160)
    COLOR_FRAME_MID_BODY: Tuple[int, int, int] = (50, 60, 70)
    COLOR_FRAME_INNER_BEVEL: Tuple[int, int, int] = (20, 25, 30)
    COLOR_RIVET_LIGHT: Tuple[int, int, int] = (180, 190, 200)
    COLOR_RIVET_DARK: Tuple[int, int, int] = (20, 25, 30)
    
    # Geometry & Padding
    CONTAINER_SLOT_HEIGHT: int = 14
    CONTAINER_SLOT_PADDING: int = 2
    CONTAINER_TOP_OFFSET: int = 22
    TITLEBAR_HEIGHT: int = 16
    
    # Meter Colors
    METER_COLORS: Dict[str, Tuple[int, int, int]] = {
        "THREAT": (255, 60, 60),
        "PROGRESS": (0, 255, 120),
        "HEALTH": (0, 200, 255)
    }

theme = UITheme()
