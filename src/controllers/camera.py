import pygame

class CameraController:
    """
    Kamera-Controller für smooth tracking und zoom.
    """
    def __init__(self, viewport_width: int, viewport_height: int) -> None:
        self.width = viewport_width
        self.height = viewport_height
        
        # Kamera-Zentrum in Sub-Pixeln (Q16.16)
        self.center_fx = 0
        self.center_fy = 0
        self.zoom = 1.0
        self.target_zoom = 1.0
        
    def update_target(self, dt: float, target_x: int, target_y: int) -> None:
        """Zentriert die Kamera smooth auf das Target."""
        target_cam_fx = int(target_x * 65536)
        target_cam_fy = int(target_y * 65536)
        
        lerp_speed = 5.0
        self.center_fx += int((target_cam_fx - self.center_fx) * lerp_speed * dt)
        self.center_fy += int((target_cam_fy - self.center_fy) * lerp_speed * dt)
        
        zoom_speed = 10.0
        self.zoom += (self.target_zoom - self.zoom) * zoom_speed * dt
        
    def update_edge_scroll(self, dt: float, mouse_x: int, mouse_y: int) -> None:
        """Pannnt die Kamera über Edge-Scrolling im Window-Space."""
        scroll_speed = int((500 / self.zoom) * 65536 * dt) # Skaliert mit zoom
        boundary = 20
        
        if mouse_x <= boundary:
            self.center_fx -= scroll_speed
        elif mouse_x >= self.width - boundary:
            self.center_fx += scroll_speed
            
        if mouse_y <= boundary:
            self.center_fy -= scroll_speed
        elif mouse_y >= self.height - boundary:
            self.center_fy += scroll_speed
            
        # Zoom immer updaten
        zoom_speed = 10.0
        self.zoom += (self.target_zoom - self.zoom) * zoom_speed * dt
        
    def handle_scroll(self, y: int) -> None:
        """Ändert den Zoom-Faktor durch das Mausrad."""
        if y > 0:
            self.target_zoom *= 1.2
        elif y < 0:
            self.target_zoom /= 1.2
            
        self.target_zoom = max(0.05, min(self.target_zoom, 4.0))

    def get_offset(self) -> tuple[float, float]:
        """
        Gibt die Top-Left Draw-Offsets (in World-Space Pixeln) zurück.
        Wird für das Rendering gebraucht: (x - offset) * zoom.
        """
        center_x = self.center_fx / 65536.0
        center_y = self.center_fy / 65536.0
        view_w = self.width / self.zoom
        view_h = self.height / self.zoom
        return (center_x - view_w / 2.0, center_y - view_h / 2.0)
