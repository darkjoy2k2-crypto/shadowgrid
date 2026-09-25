import pygame
from typing import Dict, Tuple, List

# Shadowrun Genesis Palette
GREEN_PHOSPHOR = (0, 255, 0)
GREEN_TERMINAL = GREEN_PHOSPHOR
GREEN_BRIGHT = GREEN_PHOSPHOR
GREEN_DIM = (0, 180, 0)
RED_ALERT = (255, 50, 50)
AMBER_WARN = (255, 160, 0)
WHITE_TEXT = (255, 255, 255)
STEEL_GREY = (160, 160, 160)

# 8x8 Pixel Glyph Definitions for authentic Sega Genesis Retro Font
GLYPH_DATA: Dict[str, List[str]] = {
    'A': [
        "  ###   ",
        " #   #  ",
        " #   #  ",
        " #####  ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        "        "
    ],
    'B': [
        " ####   ",
        " #   #  ",
        " #   #  ",
        " ####   ",
        " #   #  ",
        " #   #  ",
        " ####   ",
        "        "
    ],
    'C': [
        "  ####  ",
        " #    # ",
        " #      ",
        " #      ",
        " #      ",
        " #    # ",
        "  ####  ",
        "        "
    ],
    'D': [
        " ####   ",
        " #   #  ",
        " #    # ",
        " #    # ",
        " #    # ",
        " #   #  ",
        " ####   ",
        "        "
    ],
    'E': [
        " #####  ",
        " #      ",
        " #      ",
        " ####   ",
        " #      ",
        " #      ",
        " #####  ",
        "        "
    ],
    'F': [
        " #####  ",
        " #      ",
        " #      ",
        " ####   ",
        " #      ",
        " #      ",
        " #      ",
        "        "
    ],
    'G': [
        "  ####  ",
        " #    # ",
        " #      ",
        " #  ### ",
        " #    # ",
        " #    # ",
        "  ####  ",
        "        "
    ],
    'H': [
        " #   #  ",
        " #   #  ",
        " #   #  ",
        " #####  ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        "        "
    ],
    'I': [
        " ###    ",
        "  #     ",
        "  #     ",
        "  #     ",
        "  #     ",
        "  #     ",
        " ###    ",
        "        "
    ],
    'J': [
        "   ###  ",
        "    #   ",
        "    #   ",
        "    #   ",
        "    #   ",
        " #  #   ",
        "  ##    ",
        "        "
    ],
    'K': [
        " #   #  ",
        " #  #   ",
        " # #    ",
        " ##     ",
        " # #    ",
        " #  #   ",
        " #   #  ",
        "        "
    ],
    'L': [
        " #      ",
        " #      ",
        " #      ",
        " #      ",
        " #      ",
        " #      ",
        " #####  ",
        "        "
    ],
    'M': [
        " #   #  ",
        " ## ##  ",
        " # # #  ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        "        "
    ],
    'N': [
        " #   #  ",
        " ##  #  ",
        " # # #  ",
        " #  ##  ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        "        "
    ],
    'O': [
        "  ###   ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        "  ###   ",
        "        "
    ],
    'P': [
        " ####   ",
        " #   #  ",
        " #   #  ",
        " ####   ",
        " #      ",
        " #      ",
        " #      ",
        "        "
    ],
    'Q': [
        "  ###   ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        " # # #  ",
        " #  #   ",
        "  ## #  ",
        "        "
    ],
    'R': [
        " ####   ",
        " #   #  ",
        " #   #  ",
        " ####   ",
        " # #    ",
        " #  #   ",
        " #   #  ",
        "        "
    ],
    'S': [
        "  ####  ",
        " #      ",
        " #      ",
        "  ###   ",
        "     #  ",
        "     #  ",
        " ####   ",
        "        "
    ],
    'T': [
        " #####  ",
        "   #    ",
        "   #    ",
        "   #    ",
        "   #    ",
        "   #    ",
        "   #    ",
        "        "
    ],
    'U': [
        " #   #  ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        "  ###   ",
        "        "
    ],
    'V': [
        " #   #  ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        "  # #   ",
        "  # #   ",
        "   #    ",
        "        "
    ],
    'W': [
        " #   #  ",
        " #   #  ",
        " #   #  ",
        " # # #  ",
        " # # #  ",
        " ## ##  ",
        " #   #  ",
        "        "
    ],
    'X': [
        " #   #  ",
        " #   #  ",
        "  # #   ",
        "   #    ",
        "  # #   ",
        " #   #  ",
        " #   #  ",
        "        "
    ],
    'Y': [
        " #   #  ",
        " #   #  ",
        "  # #   ",
        "   #    ",
        "   #    ",
        "   #    ",
        "   #    ",
        "        "
    ],
    'Z': [
        " #####  ",
        "     #  ",
        "    #   ",
        "   #    ",
        "  #     ",
        " #      ",
        " #####  ",
        "        "
    ],
    '0': [
        "  ###   ",
        " #   #  ",
        " #  ##  ",
        " # # #  ",
        " ##  #  ",
        " #   #  ",
        "  ###   ",
        "        "
    ],
    '1': [
        "   #    ",
        "  ##    ",
        "   #    ",
        "   #    ",
        "   #    ",
        "   #    ",
        "  ###   ",
        "        "
    ],
    '2': [
        "  ###   ",
        " #   #  ",
        "     #  ",
        "   ##   ",
        "  #     ",
        " #      ",
        " #####  ",
        "        "
    ],
    '3': [
        " #####  ",
        "     #  ",
        "    #   ",
        "   ##   ",
        "     #  ",
        " #   #  ",
        "  ###   ",
        "        "
    ],
    '4': [
        "   #    ",
        "  ##    ",
        " # #    ",
        " # #    ",
        " #####  ",
        "   #    ",
        "   #    ",
        "        "
    ],
    '5': [
        " #####  ",
        " #      ",
        " ####   ",
        "     #  ",
        "     #  ",
        " #   #  ",
        "  ###   ",
        "        "
    ],
    '6': [
        "  ###   ",
        " #      ",
        " #      ",
        " ####   ",
        " #   #  ",
        " #   #  ",
        "  ###   ",
        "        "
    ],
    '7': [
        " #####  ",
        "     #  ",
        "    #   ",
        "   #    ",
        "  #     ",
        "  #     ",
        "  #     ",
        "        "
    ],
    '8': [
        "  ###   ",
        " #   #  ",
        " #   #  ",
        "  ###   ",
        " #   #  ",
        " #   #  ",
        "  ###   ",
        "        "
    ],
    '9': [
        "  ###   ",
        " #   #  ",
        " #   #  ",
        "  ####  ",
        "     #  ",
        "     #  ",
        "  ###   ",
        "        "
    ],
    ':': [
        "        ",
        "  ##    ",
        "  ##    ",
        "        ",
        "  ##    ",
        "  ##    ",
        "        ",
        "        "
    ],
    '.': [
        "        ",
        "        ",
        "        ",
        "        ",
        "        ",
        "  ##    ",
        "  ##    ",
        "        "
    ],
    ',': [
        "        ",
        "        ",
        "        ",
        "        ",
        "  ##    ",
        "  ##    ",
        " #      ",
        "        "
    ],
    '[': [
        "  ###   ",
        "  #     ",
        "  #     ",
        "  #     ",
        "  #     ",
        "  #     ",
        "  ###   ",
        "        "
    ],
    ']': [
        "  ###   ",
        "    #   ",
        "    #   ",
        "    #   ",
        "    #   ",
        "    #   ",
        "  ###   ",
        "        "
    ],
    '>': [
        " #      ",
        "  #     ",
        "   #    ",
        "    #   ",
        "   #    ",
        "  #     ",
        " #      ",
        "        "
    ],
    '<': [
        "    #   ",
        "   #    ",
        "  #     ",
        " #      ",
        "  #     ",
        "   #    ",
        "    #   ",
        "        "
    ],
    '/': [
        "     #  ",
        "    #   ",
        "   #    ",
        "  #     ",
        " #      ",
        "#       ",
        "        ",
        "        "
    ],
    '-': [
        "        ",
        "        ",
        " #####  ",
        "        ",
        "        ",
        "        ",
        "        ",
        "        "
    ],
    '_': [
        "        ",
        "        ",
        "        ",
        "        ",
        "        ",
        "        ",
        " #####  ",
        "        "
    ],
    '!': [
        "   #    ",
        "   #    ",
        "   #    ",
        "   #    ",
        "   #    ",
        "        ",
        "   #    ",
        "        "
    ],
    '?': [
        "  ###   ",
        " #   #  ",
        "     #  ",
        "   ##   ",
        "   #    ",
        "        ",
        "   #    ",
        "        "
    ],
    "'": [
        "  ##    ",
        "  ##    ",
        "  #     ",
        "        ",
        "        ",
        "        ",
        "        ",
        "        "
    ],
    '+': [
        "        ",
        "   #    ",
        "   #    ",
        " #####  ",
        "   #    ",
        "   #    ",
        "        ",
        "        "
    ],
    'Ä': [
        " #   #  ",
        "  ###   ",
        " #   #  ",
        " #   #  ",
        " #####  ",
        " #   #  ",
        " #   #  ",
        "        "
    ],
    'Ö': [
        " #   #  ",
        "  ###   ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        "  ###   ",
        "        "
    ],
    'Ü': [
        " #   #  ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        "  ###   ",
        "        "
    ],
    'ß': [
        " ####   ",
        " #   #  ",
        " #   #  ",
        " ####   ",
        " #   #  ",
        " #   #  ",
        " #   #  ",
        "        "
    ],
    ' ': [
        "        ",
        "        ",
        "        ",
        "        ",
        "        ",
        "        ",
        "        ",
        "        "
    ]
}

# Duplicate lowercase glyphs to uppercase templates for crisp 8x8 Genesis rendering
for char in "abcdefghijklmnopqrstuvwxyz":
    GLYPH_DATA[char] = GLYPH_DATA[char.upper()]

GLYPH_DATA['ä'] = GLYPH_DATA['Ä']
GLYPH_DATA['ö'] = GLYPH_DATA['Ö']
GLYPH_DATA['ü'] = GLYPH_DATA['Ü']


class FontManager:
    """
    Authentische 8x8 Genesis Pixel Font Engine für Shadowgrid.
    Erzeugt knackige 16-bit Bitmap-Texte im Shadowrun Genesis Phosphor-Grün.
    """
    def __init__(self) -> None:
        self.char_cache: Dict[Tuple[str, Tuple[int, int, int]], pygame.Surface] = {}

    def _render_char(self, char: str, color: Tuple[int, int, int]) -> pygame.Surface:
        key = (char, color)
        if key in self.char_cache:
            return self.char_cache[key]
            
        surface = pygame.Surface((8, 8), pygame.SRCALPHA)
        glyph = GLYPH_DATA.get(char, GLYPH_DATA.get(char.upper(), GLYPH_DATA['?']))
        
        for y, row in enumerate(glyph):
            for x, cell in enumerate(row):
                if cell == '#':
                    surface.set_at((x, y), color)
                    
        self.char_cache[key] = surface
        return surface

    def render(self, text: str, color: Tuple[int, int, int] = GREEN_PHOSPHOR, size: str = "small") -> pygame.Surface:
        """
        Rendert Text in 8x8 Genesis Pixel-Grafik ohne Anti-Aliasing.
        """
        text_str = str(text)
        if not text_str:
            return pygame.Surface((1, 8), pygame.SRCALPHA)
            
        w = len(text_str) * 8
        h = 8
        surface = pygame.Surface((w, h), pygame.SRCALPHA)
        
        for i, char in enumerate(text_str):
            char_surf = self._render_char(char, color)
            surface.blit(char_surf, (i * 8, 0))
            
        if size == "large":
            return pygame.transform.scale(surface, (w * 2, h * 2))
        return surface

    def render_green(self, text: str, size: str = "small") -> pygame.Surface:
        """Rendert Text im echten Shadowrun Genesis Phosphor-Grün."""
        return self.render(text, color=GREEN_PHOSPHOR, size=size)

# Globale FontManager Instanz
font_mgr = FontManager()
