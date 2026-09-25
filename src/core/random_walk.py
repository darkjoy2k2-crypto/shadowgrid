import random
from typing import List, Tuple

TILE_WALL = 1
TILE_FLOOR = 0
TILE_TERMINAL = 2

class MapGenerator:
    """
    Generiert die Macro-Topologie: Dichte Cluster (Hubs) verbunden durch Backbone-Traces.
    """
    
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.grid = [[TILE_WALL for _ in range(width)] for _ in range(height)]
        
    def generate_map(self, num_clusters: int = 6) -> None:
        """Generiert Hubs und verbindet sie."""
        clusters = []
        
        # 1. Cluster-Zentren platzieren
        for _ in range(num_clusters):
            cx = random.randint(10, self.width - 10)
            cy = random.randint(10, self.height - 10)
            cx = cx - (cx % 2)
            cy = cy - (cy % 2)
            clusters.append((cx, cy))
            
            # 2. Lokalen DFS (Micro-Cluster) pro Hub generieren
            self._generate_cluster(cx, cy, max_steps=random.randint(15, 40))
            
            # Markiere das Zentrum als Terminal
            self.grid[cy][cx] = TILE_TERMINAL
            
        # 3. Backbone-Verbindungen zwischen Clustern (Manhattan Paths)
        for i in range(len(clusters) - 1):
            self._connect_points(clusters[i], clusters[i+1])
            
        # Optional: Letztes mit erstem verbinden für Loop
        self._connect_points(clusters[-1], clusters[0])

    def _generate_cluster(self, start_x: int, start_y: int, max_steps: int) -> None:
        x, y = start_x, start_y
        self.grid[y][x] = TILE_FLOOR
        stack = [(x, y)]
        steps = 0
        directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]
        
        while stack and steps < max_steps:
            current_x, current_y = stack[-1]
            random.shuffle(directions)
            moved = False
            
            for dx, dy in directions:
                nx, ny = current_x + dx, current_y + dy
                
                if 2 <= nx < self.width - 2 and 2 <= ny < self.height - 2:
                    if self.grid[ny][nx] == TILE_WALL:
                        self.grid[current_y + dy // 2][current_x + dx // 2] = TILE_FLOOR
                        self.grid[ny][nx] = TILE_FLOOR
                        stack.append((nx, ny))
                        moved = True
                        steps += 1
                        break
                        
            if not moved:
                stack.pop()

    def _connect_points(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> None:
        """Zieht strikte, gerade Backbone-Linien (Manhattan) zwischen zwei Punkten."""
        x1, y1 = p1
        x2, y2 = p2
        
        # Erst Horizontal, dann Vertikal (oder zufällig)
        if random.choice([True, False]):
            self._draw_hline(x1, x2, y1)
            self._draw_vline(y1, y2, x2)
        else:
            self._draw_vline(y1, y2, x1)
            self._draw_hline(x1, x2, y2)

    def _draw_hline(self, x1: int, x2: int, y: int) -> None:
        start, end = min(x1, x2), max(x1, x2)
        for x in range(start, end + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.grid[y][x] = TILE_FLOOR

    def _draw_vline(self, y1: int, y2: int, x: int) -> None:
        start, end = min(y1, y2), max(y1, y2)
        for y in range(start, end + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.grid[y][x] = TILE_FLOOR

    def get_grid(self) -> List[List[int]]:
        return self.grid
