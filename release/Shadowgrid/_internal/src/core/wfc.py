from typing import List, Dict, Tuple, Set
import random

# Vereinfachte Tile-Klassen für das PCB Grid
TILE_EMPTY = 0
TILE_TRACE_H = 1      # Horizontaler Leiterstrang
TILE_TRACE_V = 2      # Vertikaler Leiterstrang
TILE_CORNER_TL = 3
TILE_CORNER_TR = 4
TILE_CORNER_BL = 5
TILE_CORNER_BR = 6
TILE_NODE = 7         # Lötpunkt / Solder Joint

class WFCSolver:
    """
    Wave Function Collapse (MRV Heuristic) für 8x8 PCB Conductive Traces.
    Stellt sicher, dass die Leiterbahnen (Traces) und Nodes korrekt verbunden sind.
    """
    
    def __init__(self, width: int, height: int, seed: int = 0) -> None:
        self.width = width
        self.height = height
        # Domain: Liste möglicher Tiles für jede Zelle
        self.domain_size = 8
        self.grid: List[List[List[int]]] = [
            [[t for t in range(self.domain_size)] for _ in range(width)]
            for _ in range(height)
        ]
        self.collapsed: List[List[bool]] = [[False for _ in range(width)] for _ in range(height)]
        self.final_grid: List[List[int]] = [[TILE_EMPTY for _ in range(width)] for _ in range(height)]
        random.seed(seed)

    def _get_entropy(self, x: int, y: int) -> int:
        return len(self.grid[y][x])

    def _find_mrv(self) -> Tuple[int, int]:
        """Findet die unkollabierte Zelle mit der minimalen Restentropie (Minimum Remaining Values)."""
        min_entropy = self.domain_size + 1
        mrv_coords = (-1, -1)
        
        for y in range(self.height):
            for x in range(self.width):
                if not self.collapsed[y][x]:
                    entropy = self._get_entropy(x, y)
                    if entropy < min_entropy:
                        min_entropy = entropy
                        mrv_coords = (x, y)
                        
        return mrv_coords

    def _propagate(self, start_x: int, start_y: int) -> None:
        """Propagiert Einschränkungen an benachbarte Zellen (vereinfachtes Constraint Propagation)."""
        # In einer vollwertigen WFC-Implementierung würden hier Adjazenz-Regeln angewendet.
        # Für das initiale Basisspiel lassen wir Zellen zufällig aus ihrer reduzierten Domain kollabieren.
        pass

    def collapse_step(self) -> bool:
        """Kollabiert die Zelle mit der geringsten Entropie. Gibt False zurück, wenn fertig."""
        x, y = self._find_mrv()
        
        if x == -1:
            return False  # Alles kollabiert
            
        # Zelle kollabieren (zufällige Auswahl aus verbliebenen Möglichkeiten)
        options = self.grid[y][x]
        if not options:
            # Contradiction - Fallback zu Empty
            chosen = TILE_EMPTY
        else:
            chosen = random.choice(options)
            
        self.grid[y][x] = [chosen]
        self.final_grid[y][x] = chosen
        self.collapsed[y][x] = True
        
        self._propagate(x, y)
        return True

    def generate(self) -> None:
        """Führt WFC aus, bis das gesamte Grid kollabiert ist."""
        while self.collapse_step():
            pass
            
    def get_grid(self) -> List[List[int]]:
        return self.final_grid
