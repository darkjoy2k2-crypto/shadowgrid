import pygame
from typing import Tuple

class NineSliceRenderer:
    """
    Shadowrun Genesis Metall-Frame Renderer.
    Erzeugt 16-bit Cyberdeck Metall-Panels mit 45-Grad gekappten Ecken (Chamfer),
    doppelter Metall-Fase (Bevel), Nieten/Riffel-Einkerbungen und tiefschwarzem Innenbereich.
    """
    def __init__(self) -> None:
        self.tile_size = 8
        self.metal_dark = (25, 30, 35)
        self.metal_light = (140, 150, 160)
        self.metal_mid = (70, 80, 90)
        self.metal_shadow = (15, 20, 25)
        self.inner_black = (0, 0, 0)
        
    def render(self, width_tiles: int, height_tiles: int) -> pygame.Surface:
        """Erzeugt ein gecachtes Shadowrun Genesis Metall-Panel Surface."""
        w = max(16, width_tiles * self.tile_size)
        h = max(16, height_tiles * self.tile_size)
        
        surface = pygame.Surface((w, h), pygame.SRCALPHA)
        
        # Outer Chamfer Polygon Points (45-Grad Ecken oben-links und oben-rechts gekappt)
        c = 6 # Chamfer offset
        polygon_pts = [
            (c, 0),
            (w - c, 0),
            (w, c),
            (w, h),
            (0, h),
            (0, c)
        ]
        
        # Metall-Grundfläche füllen
        pygame.draw.polygon(surface, self.metal_dark, polygon_pts)
        
        # Äußere metallische Highlights (Bevel Top & Left)
        pygame.draw.line(surface, self.metal_light, (c, 1), (w - c, 1), 2)
        pygame.draw.line(surface, self.metal_light, (1, c), (1, h - 2), 2)
        pygame.draw.line(surface, self.metal_light, (1, c), (c, 1), 2)
        
        # Äußere metallische Schatten (Bevel Bottom & Right)
        pygame.draw.line(surface, self.metal_shadow, (w - 1, c), (w - 1, h - 1), 2)
        pygame.draw.line(surface, self.metal_shadow, (1, h - 1), (w - 1, h - 1), 2)
        pygame.draw.line(surface, self.metal_mid, (w - c, 1), (w - 1, c), 2)
        
        # Metallische Nieten/Riffel-Einkerbungen entlang der Rahmenleisten
        rivet_color = (15, 20, 25)
        rivet_highlight = (110, 120, 130)
        
        # Horizontale Nieten oben/unten
        for rx in range(16, w - 16, 16):
            pygame.draw.line(surface, rivet_color, (rx, 1), (rx, 5), 1)
            pygame.draw.line(surface, rivet_highlight, (rx + 1, 1), (rx + 1, 5), 1)
            
            pygame.draw.line(surface, rivet_color, (rx, h - 6), (rx, h - 2), 1)
            pygame.draw.line(surface, rivet_highlight, (rx + 1, h - 6), (rx + 1, h - 2), 1)

        # Vertikale Nieten links/rechts
        for ry in range(16, h - 16, 16):
            pygame.draw.line(surface, rivet_color, (1, ry), (5, ry), 1)
            pygame.draw.line(surface, rivet_highlight, (1, ry + 1), (5, ry + 1), 1)
            
            pygame.draw.line(surface, rivet_color, (w - 6, ry), (w - 2, ry), 1)
            pygame.draw.line(surface, rivet_highlight, (w - 6, ry + 1), (w - 2, ry + 1), 1)

        # Innenbereich: Tiefschwarze Screen-Area (Pure Black #000000 wie in Shadowrun Genesis)
        margin = 6
        inner_rect = pygame.Rect(margin, margin, w - margin * 2, h - margin * 2)
        pygame.draw.rect(surface, self.inner_black, inner_rect)
        
        # Innenrand Bevel (Licht-Effekt der Röhre/des Bildschirms)
        pygame.draw.rect(surface, (40, 50, 60), inner_rect, 1)
        pygame.draw.line(surface, (10, 15, 20), (margin, margin), (w - margin, margin), 1)
        pygame.draw.line(surface, (10, 15, 20), (margin, margin), (margin, h - margin), 1)

        return surface
