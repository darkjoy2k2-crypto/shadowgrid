import heapq
from typing import List, Tuple, Set

def a_star(grid: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
    """
    Berechnet den kürzesten Pfad auf dem PCB-Grid.
    0 = TILE_FLOOR (begehbar), andere = TILE_WALL.
    """
    if not grid or not grid[0]:
        return []
        
    height = len(grid)
    width = len(grid[0])
    
    if grid[start[1]][start[0]] not in (0, 2) or grid[goal[1]][goal[0]] not in (0, 2):
        return []
        
    frontier = []
    heapq.heappush(frontier, (0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}
    
    while frontier:
        _, current = heapq.heappop(frontier)
        
        if current == goal:
            break
            
        cx, cy = current
        # Von Neumann Nachbarschaft (Orthogonal)
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            
            if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] in (0, 2): # TILE_FLOOR oder TILE_TERMINAL
                new_cost = cost_so_far[current] + 1
                
                if (nx, ny) not in cost_so_far or new_cost < cost_so_far[(nx, ny)]:
                    cost_so_far[(nx, ny)] = new_cost
                    priority = new_cost + abs(goal[0] - nx) + abs(goal[1] - ny) # Manhattan heuristic
                    heapq.heappush(frontier, (priority, (nx, ny)))
                    came_from[(nx, ny)] = current
                    
    # Pfad rekonstruieren
    if goal not in came_from:
        return [] # Kein Pfad gefunden
        
    path = []
    curr = goal
    while curr != start:
        path.append(curr)
        curr = came_from[curr]
    path.reverse()
    
    # Pfad komprimieren (nur Ecken behalten)
    if len(path) <= 1:
        return path
        
    compressed_path = []
    current_dir = None
    
    for i in range(len(path)):
        if i == 0:
            current_dir = (path[i][0] - start[0], path[i][1] - start[1])
            continue
            
        next_dir = (path[i][0] - path[i-1][0], path[i][1] - path[i-1][1])
        if next_dir != current_dir:
            compressed_path.append(path[i-1])
            current_dir = next_dir
            
    compressed_path.append(path[-1]) # Letzter Knoten ist immer ein Ziel
    
    return compressed_path
