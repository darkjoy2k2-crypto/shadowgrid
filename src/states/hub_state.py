import pygame
import random
from src.core.state_machine import State
from src.controllers.camera import CameraController
from src.entities.player import PlayerController
from src.entities.guardian import GuardianAI
from src.core.random_walk import MapGenerator
from src.ui.hud import HUD
from typing import Any
from src.utils.pathfinding import a_star

class HubState(State):
    """
    Zentraler Gameplay-State für die Netzwerktopologie (Shadowgrid).
    Integriert Player, Camera und WFC-Map.
    """
    
    def spawn_terminal(self) -> None:
        floors = [(x, y) for y in range(self.map_height) for x in range(self.map_width) if self.grid[y][x] == 0]
        if floors:
            tx, ty = random.choice(floors)
            self.grid[ty][tx] = 2
            
    def init(self) -> None:
        self.map_width = 250
        self.map_height = 150
        
        self.walker = MapGenerator(self.map_width, self.map_height)
        self.threat_level = 0.0
        self.game_over_ui = False
        self.is_caught = False
        self.alert_triggered = False
        self.alert_timer = 0.0
        
        import os
        from src.utils.fade_controller import FadeController
        self.death_fade = FadeController()
        self.intro_fade = FadeController()
        self.intro_fade.start_fade_in(duration=0.5)
        
        dead_path = os.path.join("src", "gfx", "dead.png")
        if not os.path.isabs(dead_path):
            dead_path = os.path.abspath(dead_path)
            
        if os.path.exists(dead_path):
            loaded = pygame.image.load(dead_path).convert_alpha()
            self.dead_img = pygame.transform.scale(loaded, (640, 360))
        else:
            self.dead_img = None
            
        # Parallax Layer Initialisierung (Backdrop & Pulsing Grid)
        self.parallax_time = 0.0
        self.backdrop_surf = None
        
        from src.ui.cyber_terminal_feed import CyberTerminalFeed
        self.terminal_feed = CyberTerminalFeed()
        backdrop_path = r"C:\Users\peter\Documents\_shadowgrid\media\images\backdrop.png"
        if not os.path.exists(backdrop_path):
            backdrop_path = os.path.abspath(os.path.join("media", "images", "backdrop.png"))

        if os.path.exists(backdrop_path):
            try:
                raw_backdrop = pygame.image.load(backdrop_path)
                if pygame.display.get_surface():
                    raw_backdrop = raw_backdrop.convert()
                self.backdrop_surf = raw_backdrop.copy()
                dim_overlay = pygame.Surface(self.backdrop_surf.get_size(), pygame.SRCALPHA)
                dim_overlay.fill((0, 8, 12, 200)) # Abgedunkelt für beste Lesbarkeit der Karte
                self.backdrop_surf.blit(dim_overlay, (0, 0))
            except Exception as e:
                print(f"Failed to load backdrop image: {e}")
                self.backdrop_surf = None
        
        # Keep fragments across resets
        if not hasattr(self, 'data_fragments'):
            self.data_fragments = 0
            
        from src.core.emotions import EmotionEngine
        self.emotion_engine = EmotionEngine()
        self.emotion_engine.init_spawn()
        self.walker.generate_map(num_clusters=8)
        self.grid = self.walker.get_grid()
        
        # Spawne Sentinels an zufälligen Floor-Tiles
        self.sentinels = []
        from src.entities.civilian import CivilNode, CivilState
        self.civilians = []
        
        # Cache floors
        self.floor_cache = []
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.grid[y][x] == 0:
                    self.floor_cache.append((x, y))
                    
        # Player auf erstem verfügbaren Knoten starten
        px, py = self.floor_cache[0] if self.floor_cache else (self.map_width // 2, self.map_height // 2)
        self.player = PlayerController(px, py)
        self.player.init()
                    
        for _ in range(5):
            if self.floor_cache:
                sx, sy = random.choice(self.floor_cache)
                self.sentinels.append(GuardianAI(sx, sy, self.grid))
                
        # Spawne initial 20 Civil Nodes
        for _ in range(20):
            if self.floor_cache:
                cx, cy = random.choice(self.floor_cache)
                self.civilians.append(CivilNode(cx, cy, self.grid))
        
        # Spawne IoT Surveillance Nodes: Watcher (Kamera), Listener (Audio), Scanner (Weg)
        from src.entities.iot_device import IoTNode
        self.iot_devices = []
        
        # Candidate docking tiles: Wall tile (ix, iy) mit 1 Spurbreite Abstand (gx, gy) zum Pfad (x, y)
        dock_candidates = []
        for y in range(2, self.map_height - 2):
            for x in range(2, self.map_width - 2):
                if self.grid[y][x] in (0, 2):  # Floor path tile
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        gx, gy = x + dx, y + dy
                        ix, iy = x + dx * 2, y + dy * 2
                        if (0 <= ix < self.map_width and 0 <= iy < self.map_height and
                            self.grid[gy][gx] == 1 and self.grid[iy][ix] == 1):
                            dock_candidates.append(((ix, iy), (x, y), (dx, dy)))
                            
        random.shuffle(dock_candidates)
        used_wall_tiles = set()
        
        # 6 Watcher (Kameras) - gedockt mit 1 Spurbreite Abstand
        for _ in range(6):
            if not dock_candidates: break
            (wx, wy), dock_tile, dock_dir = dock_candidates.pop()
            if (wx, wy) not in used_wall_tiles:
                used_wall_tiles.add((wx, wy))
                self.iot_devices.append(IoTNode(wx, wy, "watcher", dock_tile=dock_tile, dock_dir=dock_dir))
                
        # 6 Listener (Audio) - gedockt mit 1 Spurbreite Abstand
        for _ in range(6):
            if not dock_candidates: break
            (lx, ly), dock_tile, dock_dir = dock_candidates.pop()
            if (lx, ly) not in used_wall_tiles:
                used_wall_tiles.add((lx, ly))
                self.iot_devices.append(IoTNode(lx, ly, "listener", dock_tile=dock_tile, dock_dir=dock_dir))
                
        # 6 Scanner - mitten auf den Wegen (Floor Tiles)
        if self.floor_cache:
            used_floor_tiles = set()
            for _ in range(6):
                sx, sy = random.choice(self.floor_cache)
                if (sx, sy) not in used_floor_tiles and (sx, sy) != (px, py):
                    used_floor_tiles.add((sx, sy))
                    self.iot_devices.append(IoTNode(sx, sy, "scanner", dock_tile=None))
        
        self.camera = CameraController(640, 360)
        self.camera.center_fx = self.player.fx * 8
        self.camera.center_fy = self.player.fy * 8
        
        self.hud = HUD()
        from src.ui.action_menu import ActionMenu
        self.action_menu = ActionMenu()
        
        from src.ui.game_over_menu import GameOverMenu
        self.game_over_menu = GameOverMenu()
        
        self.alert_triggered = False
        self.alert_timer = 0.0

        # Fog of War exploration grid
        self.explored_grid = [[False for _ in range(self.map_width)] for _ in range(self.map_height)]
        self._update_fog_of_war()
        from src.utils.perception_logger import perception_logger
        perception_logger.log_event("SESSION_START", {"map": "Shadowgrid"})

    def _update_fog_of_war(self) -> None:
        """Aktualisiert die 5-Tile Sichtbarkeits- und Erkundungs-Matrix um die aktuelle Spieler-Position."""
        px_tile = self.player.fx >> 16
        py_tile = self.player.fy >> 16
        self.player.grid_x = px_tile
        self.player.grid_y = py_tile
        for y in range(max(0, py_tile - 5), min(self.map_height, py_tile + 6)):
            for x in range(max(0, px_tile - 5), min(self.map_width, px_tile + 6)):
                if (x - px_tile)**2 + (y - py_tile)**2 <= 25:
                    self.explored_grid[y][x] = True

    def get_native_mouse_pos(self) -> tuple[int, int]:
        mx, my = pygame.mouse.get_pos()
        screen = pygame.display.get_surface()
        if screen:
            sw, sh = screen.get_size()
            if sw > 0 and sh > 0:
                return int(mx * 640 / sw), int(my * 360 / sh)
        return mx // 2, my // 2

    def is_ui_clicked(self, mx: int, my: int) -> bool:
        """Prüft, ob die Mausposition auf einem aktiven UI-Element liegt (verhindert Durchklicken)."""
        if self.hud.text_log_modal.active:
            return True

        if self.hud.error_modal.active:
            return True
            
        if self.hud.folder_icon.get_rect().collidepoint(mx, my):
            return True

        if self.hud.inventory.active:
            if self.hud.inventory.get_rect().collidepoint(mx, my):
                return True
                
        if self.hud.driver_container.get_rect().collidepoint(mx, my):
            return True
                
        values = {
            "threat": max(0.0, min(1.0, self.threat_level / 100.0)),
            "progress": (max(0.0, min(1.0, self.action_menu.progress / 100.0)) if self.action_menu.active else 0.0),
            "health": 1.0
        }
        if self.hud.meter_container.get_rect(values).collidepoint(mx, my):
            return True
            
        if self.action_menu.active:
            if self.action_menu.get_rect().collidepoint(mx, my):
                return True
                
        term_y = 360 - 80 - 16
        term_rect = pygame.Rect(16, term_y, 288, 80)
        if term_rect.collidepoint(mx, my):
            return True
            
        data_rect = pygame.Rect(16, 8, 160, 16)
        if data_rect.collidepoint(mx, my):
            return True
            
        return False

    def handle_event(self, event: Any) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i:
                self.hud.inventory.toggle()
                from src.utils.perception_logger import perception_logger
                perception_logger.log_event("INPUT_KEY", {"key": "I", "inventory_active": self.hud.inventory.active})
                return

        if event.type == pygame.MOUSEWHEEL:
            native_mx, native_my = self.get_native_mouse_pos()
            if self.hud.text_log_modal.active:
                self.hud.text_log_modal.handle_scroll(event.y)
                return
            if self.hud.inventory.active and self.hud.inventory.get_rect().collidepoint(native_mx, native_my):
                self.hud.inventory.handle_scroll(event.y)
                return
            self.camera.handle_scroll(event.y)
            
        if getattr(self, 'game_over_ui', False):
            return
            
        native_mx, native_my = self.get_native_mouse_pos()
        container = self.hud.meter_container
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            from src.utils.perception_logger import perception_logger
            perception_logger.log_event("INPUT_CLICK", {"button": event.button, "pos": (native_mx, native_my), "ui_clicked": self.is_ui_clicked(native_mx, native_my)})
            
            if self.hud.text_log_modal.active:
                if self.hud.text_log_modal.handle_click(native_mx, native_my):
                    return

            if event.button == 1: # Links-Klick
                # Check Skalierungs-Buttons [+] und [i] unter Jacks Porträt
                if self.hud.handle_scale_button_click(native_mx, native_my):
                    return

                # Check Terminal Klick (öffnet ladefähiges TextLogModal)
                term_y = 360 - 80 - 16
                term_rect = pygame.Rect(16, term_y, 288, 80)
                if term_rect.collidepoint(native_mx, native_my):
                    import os
                    from src.utils.perception_logger import perception_logger
                    history = perception_logger.get_session_thought_logs()
                    title = f"LOG: SESSION_{perception_logger.session_id}.DAT"
                    self.hud.text_log_modal.open_log(title, history)
                    return

                if self.hud.error_modal.handle_click(native_mx, native_my):
                    return
                if self.hud.folder_icon.handle_click(native_mx, native_my, self.hud.inventory):
                    return
                if self.hud.inventory.handle_mouse_down(native_mx, native_my, container, self.hud.driver_container, text_log_modal=self.hud.text_log_modal, emotion_engine=self.emotion_engine):
                    return
                if container.rect_title.collidepoint(native_mx, native_my):
                    container.is_dragging = True
                    container.drag_offset_x = container.x - native_mx
                    container.drag_offset_y = container.y - native_my
                    container.handle_titlebar_click(native_mx, native_my)
                    return
                if self.hud.driver_container.rect_title.collidepoint(native_mx, native_my):
                    self.hud.driver_container.is_dragging = True
                    self.hud.driver_container.drag_offset_x = self.hud.driver_container.x - native_mx
                    self.hud.driver_container.drag_offset_y = self.hud.driver_container.y - native_my
                    self.hud.driver_container.handle_titlebar_click(native_mx, native_my)
                    return
                if self.action_menu.active:
                    if self.action_menu.rect_title.collidepoint(native_mx, native_my):
                        self.action_menu.is_dragging = True
                        self.action_menu.has_been_dragged = True
                        self.action_menu.drag_offset_x = self.action_menu.x - native_mx
                        self.action_menu.drag_offset_y = self.action_menu.y - native_my
            elif event.button == 3: # Rechts-Klick (Auto-Mount ins Deck / Entladen ins Inventar)
                if self.hud.inventory.handle_right_click(native_mx, native_my, container, self.hud.error_modal, self.hud.driver_container, emotion_engine=self.emotion_engine):
                    return
                if container.handle_right_click(native_mx, native_my, self.hud.inventory, emotion_engine=self.emotion_engine):
                    return
                if self.hud.driver_container.handle_right_click(native_mx, native_my, self.hud.inventory, emotion_engine=self.emotion_engine):
                    return

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            container.is_dragging = False
            self.hud.driver_container.is_dragging = False
            self.hud.inventory.handle_mouse_up(native_mx, native_my, container, self.hud.error_modal, self.hud.driver_container, emotion_engine=self.emotion_engine)
            if self.action_menu.active:
                self.action_menu.is_dragging = False
                
        elif event.type == pygame.MOUSEMOTION:
            self.hud.folder_icon.handle_mouse_motion(native_mx, native_my)
            self.hud.inventory.handle_mouse_motion(native_mx, native_my)
            if container.is_dragging:
                container.x = max(0, min(640 - container.width, native_mx + container.drag_offset_x))
                container.y = max(0, min(360 - 40, native_my + container.drag_offset_y))
            if self.hud.driver_container.is_dragging:
                self.hud.driver_container.x = max(0, min(640 - self.hud.driver_container.width, native_mx + self.hud.driver_container.drag_offset_x))
                self.hud.driver_container.y = max(0, min(360 - 40, native_my + self.hud.driver_container.drag_offset_y))
            if self.action_menu.active and self.action_menu.is_dragging:
                self.action_menu.x = max(0, min(640 - self.action_menu.width, native_mx + self.action_menu.drag_offset_x))
                self.action_menu.y = max(0, min(360 - self.action_menu.height, native_my + self.action_menu.drag_offset_y))

    def update(self, dt: float) -> None:
        self.parallax_time = getattr(self, 'parallax_time', 0.0) + dt
        if hasattr(self, 'intro_fade') and self.intro_fade.is_fading:
            self.intro_fade.update(dt)
            
        if hasattr(self, 'terminal_feed'):
            self.terminal_feed.update(dt, {"threat_level": getattr(self, 'threat_level', 0.0)})
            
        glitch_proc = self.sm.context.get("glitch_processor")
        if glitch_proc:
            if getattr(self, 'game_over_ui', False):
                glitch_proc.set_intensity(1.0)
            elif getattr(self, 'is_caught', False):
                glitch_proc.set_intensity(0.9)
            elif getattr(self, 'alert_triggered', False):
                glitch_proc.set_intensity(0.7)
            else:
                threat_ratio = max(0.0, min(1.0, getattr(self, 'threat_level', 0.0) / 100.0))
                glitch_proc.set_intensity(0.05 + threat_ratio * 0.45)
        self.hud.error_modal.update(dt)
        self.hud.meter_container.update(dt)
        self.hud.driver_container.update(dt)
        self._update_fog_of_war()
        if getattr(self, 'game_over_ui', False) or (hasattr(self, 'death_fade') and self.death_fade.is_fading):
            if hasattr(self, 'death_fade'):
                self.death_fade.update(dt)
            if self.game_over_ui:
                self.hud.portrait.set_emotion(19) # 19. Tot.
                native_mx, native_my = self.get_native_mouse_pos()
                
                buttons = pygame.mouse.get_pressed()
                just_pressed = False
                if buttons[0] and not getattr(self, 'mouse_down_last_frame', False):
                    just_pressed = True
                self.mouse_down_last_frame = buttons[0]
                
                if just_pressed:
                    if self.game_over_menu.handle_click(native_mx, native_my) == "RETRY":
                        self.game_over_ui = False
                        sm = self.sm.context.get("sound_manager")
                        if sm:
                            sm.play_spatial("hack_success", 320, 180, 320, 180, base_volume=0.8)
                        if hasattr(self, 'death_fade'):
                            self.death_fade.start_fade_out(duration=0.8, on_complete=self.init)
                        else:
                            self.init()
            return
            
        # Update IoT devices & active scanners
        for iot in self.iot_devices:
            iot.update(dt)
            
        active_scanners = {(iot.grid_x, iot.grid_y) for iot in self.iot_devices if iot.device_type == "scanner"}
        is_player_on_scanner = (self.player.grid_x, self.player.grid_y) in active_scanners

        # Calculate sentinel proximity
        min_sentinel_dist = float('inf')
        for g in self.sentinels:
            dx = (self.player.fx - g.fx) >> 16
            dy = (self.player.fy - g.fy) >> 16
            dist = (dx*dx + dy*dy) ** 0.5
            if dist < min_sentinel_dist:
                min_sentinel_dist = dist

        # Update EmotionEngine mit umfassendem Gameplay-Kontext
        context = {
            "is_game_over": getattr(self, 'game_over_ui', False) or (hasattr(self, 'death_fade') and self.death_fade.is_fading),
            "is_caught": getattr(self, 'is_caught', False),
            "alert_triggered": getattr(self, 'alert_triggered', False),
            "threat_level": self.threat_level,
            "is_moving": bool(self.player.target_path),
            "is_pursuing": hasattr(self, 'pursuit_target') and self.pursuit_target is not None,
            "is_infiltrating": self.action_menu.active and self.action_menu.state == "INFILTRATING",
            "infiltrate_progress": self.action_menu.progress if self.action_menu.active else 0.0,
            "min_sentinel_dist": min_sentinel_dist,
            "is_on_scanner": is_player_on_scanner
        }
        active_emotion = self.emotion_engine.update(dt, context)
        self.hud.portrait.set_emotion(active_emotion)

        # Restore standard speeds (no speed-down)
        if not (hasattr(self, 'pursuit_target') and self.pursuit_target and abs((self.player.fx >> 16) - (self.pursuit_target.fx >> 16)) + abs((self.player.fy >> 16) - (self.pursuit_target.fy >> 16)) <= 2):
            self.player.speed = 20 << 16

        for civ in self.civilians:
            civ.speed = 4 << 16

        for sentinel in self.sentinels:
            if not self.alert_triggered:
                sentinel.speed = 4 << 16
            
        was_moving = bool(self.player.target_path)
        prev_grid_pos = (self.player.grid_x, self.player.grid_y)
        self.player.update(dt)
        curr_grid_pos = (self.player.grid_x, self.player.grid_y)
        is_moving = bool(self.player.target_path)

        # Scanner Intercept: Wenn der Spieler ein neues Scanner-Feld betritt, wird das Pathfinding abgebrochen
        if prev_grid_pos != curr_grid_pos and curr_grid_pos in active_scanners:
            if self.player.target_path:
                self.player.target_path = []
                is_moving = False
                sound_manager = self.sm.context.get("sound_manager")
                if sound_manager:
                    px = (self.player.fx * 8) >> 16
                    py = (self.player.fy * 8) >> 16
                    sound_manager.play_spatial("node_connect", px, py, px, py, base_volume=0.6)
                from src.utils.perception_logger import perception_logger
                perception_logger.log_event("SCANNER_INTERCEPT", {"tile": curr_grid_pos})
        
        # Trigger Hacking wenn Player stoppt und auf einem Terminal steht
        if was_moving and not is_moving:
            if self.grid[self.player.grid_y][self.player.grid_x] == 2:
                # Terminal reached!
                self.sm.change_state("HACKING")
                
        # Player Sound
        if is_moving:
            if not hasattr(self.player, 'footstep_timer'):
                self.player.footstep_timer = 0.0
            self.player.footstep_timer -= dt
            if self.player.footstep_timer <= 0:
                sound_manager = self.sm.context.get("sound_manager")
                if sound_manager:
                    px = (self.player.fx * 8) >> 16
                    py = (self.player.fy * 8) >> 16
                    # Sound is now much better audible due to fixed panning math
                    sound_manager.play_spatial("player_move", px, py, px, py, base_volume=0.4)
                self.player.footstep_timer = 0.3 # 300ms intervall
        
        px = (self.player.fx * 8) >> 16
        py = (self.player.fy * 8) >> 16
        sound_manager = self.sm.context.get("sound_manager")

        for sentinel in self.sentinels:
            sentinel.update(dt)
            if sound_manager and getattr(sentinel, 'target_path', False):
                if not hasattr(sentinel, 'sound_timer'):
                    sentinel.sound_timer = random.uniform(0.0, 0.6)
                sentinel.sound_timer -= dt
                if sentinel.sound_timer <= 0:
                    sx = (sentinel.fx * 8) >> 16
                    sy = (sentinel.fy * 8) >> 16
                    sound_manager.play_spatial("guardian_move", sx, sy, px, py, base_volume=0.4)
                    sentinel.sound_timer = 0.6
            
        from src.entities.civilian import CivilNode, CivilState
        for civ in self.civilians:
            civ.update(dt)
            if sound_manager and getattr(civ, 'target_path', False) and civ.state != CivilState.DEAD:
                if not hasattr(civ, 'footstep_timer'):
                    civ.footstep_timer = random.uniform(0.0, 0.4)
                    civ.move_sound = random.choice(["civ_move_1", "civ_move_2"])
                civ.footstep_timer -= dt
                if civ.footstep_timer <= 0:
                    cx = (civ.fx * 8) >> 16
                    cy = (civ.fy * 8) >> 16
                    sound_manager.play_spatial(civ.move_sound, cx, cy, px, py, base_volume=0.3)
                    civ.footstep_timer = 0.4
            
        # Remove dead civilians and respawn
        alive_civs = [c for c in self.civilians if c.state != CivilState.DEAD]
        if len(alive_civs) < 20 and self.floor_cache:
            while len(alive_civs) < 20:
                cx, cy = random.choice(self.floor_cache)
                alive_civs.append(CivilNode(cx, cy, self.grid))
        self.civilians = alive_civs

        # Check civilian encounters
        px_tile = self.player.grid_x
        py_tile = self.player.grid_y
        if not hasattr(self, 'civ_encounter_cooldown'):
            self.civ_encounter_cooldown = 0.0
        self.civ_encounter_cooldown -= dt
        if self.civ_encounter_cooldown <= 0.0:
            for civ in self.civilians:
                cx = civ.fx >> 16
                cy = civ.fy >> 16
                if (px_tile - cx)**2 + (py_tile - cy)**2 <= 4:
                    from src.utils.perception_logger import perception_logger
                    perception_logger.log_event("CIVILIAN_ENCOUNTER", {"civ_pos": (cx, cy)})
                    self.civ_encounter_cooldown = 2.5
                    break
            
        # Threat Level berechnen
        is_suspicious_active = hasattr(self, 'pursuit_target') and self.pursuit_target and self.pursuit_target.is_suspicious and not self.action_menu.is_paused
        
        min_dist = float('inf')
        for g in self.sentinels:
            dx = (self.player.fx - g.fx) >> 16
            dy = (self.player.fy - g.fy) >> 16
            dist = (dx*dx + dy*dy) ** 0.5
            if dist < min_dist:
                min_dist = dist
                
        is_infiltrating = (self.action_menu.active and self.action_menu.state == "INFILTRATING")
        
        # Determine if player was just caught infiltrating
        if min_dist <= 5.0 and is_infiltrating and not getattr(self, 'is_caught', False):
            self.is_caught = True
            glitch_proc = self.sm.context.get("glitch_processor")
            if glitch_proc:
                glitch_proc.add_burst(0.7)
            self.action_menu.close()
            self.player.target_path = []
            
            # Find the closest sentinel to act as the catcher
            closest_sentinel = min(self.sentinels, key=lambda g: abs((g.fx >> 16) - (self.player.fx >> 16)) + abs((g.fy >> 16) - (self.player.fy >> 16)))
            self.investigating_sentinel = closest_sentinel
            
        # Dist = 0 Game Over check (only deadly during ALERT or when caught)
        if self.alert_triggered or self.threat_level >= 100.0 or getattr(self, 'is_caught', False):
            for g in self.sentinels:
                gx, gy = g.fx >> 16, g.fy >> 16
                px, py = self.player.fx >> 16, self.player.fy >> 16
                dist = abs(gx - px) + abs(gy - py)
                if dist == 0:
                    if sound_manager and not getattr(self, 'game_over_ui', False):
                        px = (self.player.fx * 8) >> 16
                        py = (self.player.fy * 8) >> 16
                        sound_manager.play_spatial("game_over", px, py, px, py, base_volume=1.0)
                    if not self.game_over_ui:
                        self.game_over_ui = True
                        if hasattr(self, 'death_fade'):
                            self.death_fade.start_fade_in(duration=1.0)
                    self.player.target_path = []
                    self.player.speed = 0
                    return
                
        is_tailing = (hasattr(self, 'pursuit_target') and self.pursuit_target and 
                      getattr(self.pursuit_target, 'is_pursued', False) and 
                      (abs((self.player.fx >> 16) - (self.pursuit_target.fx >> 16)) + 
                       abs((self.player.fy >> 16) - (self.pursuit_target.fy >> 16)) <= 2))

        is_player_on_scanner = (self.player.grid_x, self.player.grid_y) in active_scanners

        if getattr(self, 'is_caught', False):
            self.threat_level = min(100.0, self.threat_level + 150.0 * dt)
        elif is_player_on_scanner:
            # Langsame Steigerung der Bedrohung beim Gescanntwerden (+6.0 Threat / Sekunde)
            self.threat_level = min(100.0, self.threat_level + 6.0 * dt)
        elif min_dist <= 4.0 or is_suspicious_active:
            if is_suspicious_active:
                self.threat_level = min(100.0, self.threat_level + 25.0 * dt)
            elif min_dist <= 2.0:
                # Sehr nah (Vorbeigehen): starker Anstieg (+20/s)
                self.threat_level = min(100.0, self.threat_level + 20.0 * dt)
            else:
                # In der Nähe (3-4 Tiles): leichter Anstieg (+5/s)
                self.threat_level = min(100.0, self.threat_level + 5.0 * dt)
        elif is_tailing:
            # An Zivilist kleben / Verfolgen: minimaler Anstieg (+3/s)
            self.threat_level = min(100.0, self.threat_level + 3.0 * dt)
        else:
            if self.alert_timer > 0.0:
                self.threat_level = 100.0
            else:
                self.threat_level = max(0.0, self.threat_level - 12.5 * dt) # Sinkt nur noch halb so schnell
                
        # Threat Audio Feedback Loop (gestaffelt in 10% Stufen)
        if sound_manager and self.threat_level > 0:
            if not hasattr(self, 'threat_pulse_timer'):
                self.threat_pulse_timer = 0.0
            self.threat_pulse_timer -= dt
            if self.threat_pulse_timer <= 0:
                step = min(9, max(1, int(self.threat_level // 10)))
                # 10% -> 0.9s Intervall, 50% -> 0.5s Intervall, 90% -> 0.1s ("rattert")
                interval = max(0.08, 1.0 - (step * 0.1))
                px = (self.player.fx * 8) >> 16
                py = (self.player.fy * 8) >> 16
                vol = 0.3 + (self.threat_level / 100.0) * 0.4
                sound_manager.play_spatial("threat_pulse", px, py, px, py, base_volume=vol)
                self.threat_pulse_timer = interval
                
        if self.threat_level >= 100.0:
            if not self.alert_triggered:
                self.alert_triggered = True
                self.alert_timer = 10.0 # Alert hält mindestens 10 Sekunden an
                if sound_manager:
                    px = (self.player.fx * 8) >> 16
                    py = (self.player.fy * 8) >> 16
                    sound_manager.play_spatial("alert_trigger", px, py, px, py, base_volume=1.0)
                    self.alert_sound_timer = 2.0
                if self.sentinels and not getattr(self, 'is_caught', False):
                    random_sentinel = random.choice(self.sentinels)
                    self.investigating_sentinel = random_sentinel
                    px = self.player.fx >> 16
                    py = self.player.fy >> 16
                    self.crime_scene = (px, py)
                    path = a_star(self.grid, (random_sentinel.fx >> 16, random_sentinel.fy >> 16), (px, py))
                    if path:
                        random_sentinel.target_path = path
                elif getattr(self, 'is_caught', False):
                    px = self.player.fx >> 16
                    py = self.player.fy >> 16
                    self.crime_scene = (px, py)

            self.alert_timer -= dt
            
            if sound_manager:
                if not hasattr(self, 'alert_sound_timer'):
                    self.alert_sound_timer = 0.0
                self.alert_sound_timer -= dt
                if self.alert_sound_timer <= 0:
                    px = (self.player.fx * 8) >> 16
                    py = (self.player.fy * 8) >> 16
                    sound_manager.play_spatial("alert_trigger", px, py, px, py, base_volume=1.0)
                    self.alert_sound_timer = 2.0

            # Check distances to all guardians for buff and Game Over
            for g in self.sentinels:
                gx, gy = g.fx >> 16, g.fy >> 16
                px, py = self.player.fx >> 16, self.player.fy >> 16
                dist = abs(gx - px) + abs(gy - py)
                
                # Check collision -> Game Over handled separately now!
                
                # Check buff range (5 tiles)
                if dist <= 5:
                    g.speed = int((4 << 16) * 1.25)
                    # actively path to player's current position if needed
                    if not g.target_path or g.target_path[-1] != (px, py):
                        path = a_star(self.grid, (gx, gy), (px, py))
                        if path:
                            g.target_path = path
                else:
                    if getattr(self, 'investigating_sentinel', None) == g:
                        g.speed = int((4 << 16) * 1.25)
                        cx, cy = getattr(self, 'crime_scene', (px, py))
                        if not g.target_path or g.target_path[-1] != (cx, cy):
                            if (gx, gy) != (cx, cy):
                                path = a_star(self.grid, (gx, gy), (cx, cy))
                                if path:
                                    g.target_path = path
                    else:
                        g.speed = 4 << 16 # Reset to normal
        else:
            self.alert_triggered = False
            for g in self.sentinels:
                g.speed = 4 << 16
                gx, gy = g.fx >> 16, g.fy >> 16
                px, py = self.player.fx >> 16, self.player.fy >> 16
                dist = abs(gx - px) + abs(gy - py)
                detection_radius = 25 if is_infiltrating else 3
                if dist <= detection_radius and not getattr(self, 'is_caught', False):
                    # Sentinel schlägt die Richtung des Spielers ein
                    if not g.target_path or g.target_path[-1] != (px, py):
                        path = a_star(self.grid, (gx, gy), (px, py))
                        if path:
                            g.target_path = path
        
        
        native_mx, native_my = self.get_native_mouse_pos()
        
        # Kamera-Logik: ucam.drv erlaubt Free-Look Edge Scroll. disp.drv oder kein Treiber zwingt Kamera-Tracking auf den Player.
        active_driver = self.hud.driver_container.get_active_camera_driver()
        if active_driver == "ucam.drv":
            if self.player.target_path:
                px = (self.player.fx * 8) >> 16
                py = (self.player.fy * 8) >> 16
                self.camera.update_target(dt, px, py)
            elif pygame.mouse.get_focused():
                self.camera.update_edge_scroll(dt, native_mx, native_my)
        else:
            px = (self.player.fx * 8) >> 16
            py = (self.player.fy * 8) >> 16
            self.camera.update_target(dt, px, py)
        
        buttons = pygame.mouse.get_pressed()
        just_pressed = False
        if buttons[0] and not getattr(self, 'mouse_down_last_frame', False):
            just_pressed = True
        self.mouse_down_last_frame = buttons[0]
        
        if just_pressed:
            if self.is_ui_clicked(native_mx, native_my):
                # Check ActionMenu clicks if ActionMenu is active
                if self.action_menu.active:
                    action = self.action_menu.handle_click(native_mx, native_my)
                    if action == "INFILTRATE_START":
                        self.pursuit_target.is_suspicious = False
                        self.pursuit_target.suspicion_timer = 0.0
                    elif action == "PAUSE_TOGGLED":
                        pass
                    elif action == "CANCEL":
                        if hasattr(self, 'pursuit_target') and self.pursuit_target:
                            self.pursuit_target.is_pursued = False
                            self.pursuit_target = None
                        self.action_menu.close()
                        sm = self.sm.context.get("sound_manager")
                        if sm:
                            px = (self.player.fx * 8) >> 16
                            py = (self.player.fy * 8) >> 16
                            sm.play_spatial("action_cancel", px, py, px, py, base_volume=1.0)
                    elif action == "HIJACK":
                        pass
                return # Block click from propagating to world map
                
            cam_x, cam_y = self.camera.get_offset()
            zoom = self.camera.zoom
            
            world_x = (native_mx / zoom) + cam_x
            world_y = (native_my / zoom) + cam_y
            
            tile_x = int(world_x) // 8
            tile_y = int(world_y) // 8
            
            if 0 <= tile_x < self.map_width and 0 <= tile_y < self.map_height:
                if self.grid[tile_y][tile_x] in (0, 2):
                    # Check if civilian or IoT device clicked
                    clicked_civ = None
                    for civ in self.civilians:
                        if getattr(civ, 'is_robbed', False):
                            continue
                        civ_tx = civ.fx >> 16
                        civ_ty = civ.fy >> 16
                        if abs(civ_tx - tile_x) <= 1 and abs(civ_ty - tile_y) <= 1:
                            clicked_civ = civ
                            break
                            
                    if not clicked_civ:
                        for iot in self.iot_devices:
                            if not getattr(iot, 'is_hackable', True) or getattr(iot, 'is_robbed', False) or getattr(iot, 'is_hacked', False):
                                continue
                            iot_tx = iot.fx >> 16
                            iot_ty = iot.fy >> 16
                            is_hit = (abs(iot_tx - tile_x) <= 1 and abs(iot_ty - tile_y) <= 1)
                            if not is_hit and getattr(iot, 'dock_tile', None):
                                dtx, dty = iot.dock_tile
                                is_hit = (abs(dtx - tile_x) <= 1 and abs(dty - tile_y) <= 1)
                            if is_hit:
                                clicked_civ = iot
                                break
                            
                    if clicked_civ:
                        self.pursuit_target = clicked_civ
                        clicked_civ.is_pursued = True
                        clicked_civ.lock_anim.trigger()
                        
                        sm = self.sm.context.get("sound_manager")
                        if sm:
                            px = (self.player.fx * 8) >> 16
                            py = (self.player.fy * 8) >> 16
                            sm.play_spatial("click_target", world_x, world_y, px, py, base_volume=1.0)
                    else:
                        # Clear pursuit if clicked elsewhere
                        if hasattr(self, 'pursuit_target') and self.pursuit_target:
                            self.pursuit_target.is_pursued = False
                            self.pursuit_target.is_suspicious = False
                            self.pursuit_target = None
                            self.player.speed = 20 << 16
                            self.action_menu.close()
                            
                            sm = self.sm.context.get("sound_manager")
                            if sm:
                                px = (self.player.fx * 8) >> 16
                                py = (self.player.fy * 8) >> 16
                                sm.play_spatial("action_cancel", px, py, px, py, base_volume=1.0)
                            
                        start_node = (self.player.grid_x, self.player.grid_y)
                        goal_node = (tile_x, tile_y)
                        path = a_star(self.grid, start_node, goal_node)
                        if path:
                            from src.utils.perception_logger import perception_logger
                            perception_logger.log_event("PATH_STARTED", {
                                "start": start_node,
                                "goal": goal_node,
                                "length": len(path),
                                "is_direction_change": bool(self.player.target_path and len(self.player.target_path) > 1)
                            })
                            self.player.set_path(path)
                            
                            sm = self.sm.context.get("sound_manager")
                            if sm:
                                px = (self.player.fx * 8) >> 16
                                py = (self.player.fy * 8) >> 16
                                sm.play_spatial("click_target", world_x, world_y, px, py, base_volume=1.0)
                            
        # Hover & Pursuit
        self.hovered_civ = None
        
        # Maus Position in Welt-Koordinaten umrechnen
        cam_x, cam_y = self.camera.get_offset()
        zoom = self.camera.zoom
        world_x = (native_mx / zoom) + cam_x
        world_y = (native_my / zoom) + cam_y
        tile_x = int(world_x) // 8
        tile_y = int(world_y) // 8
        
        for civ in self.civilians:
            if getattr(civ, 'is_robbed', False):
                civ.is_hovered = False
                continue
                
            civ_tx = civ.fx >> 16
            civ_ty = civ.fy >> 16
            if abs(civ_tx - tile_x) <= 1 and abs(civ_ty - tile_y) <= 1:
                civ.is_hovered = True
                self.hovered_civ = civ
            else:
                civ.is_hovered = False

        for iot in self.iot_devices:
            if not getattr(iot, 'is_hackable', True) or getattr(iot, 'is_robbed', False) or getattr(iot, 'is_hacked', False):
                iot.is_hovered = False
                continue
                
            iot_tx = iot.fx >> 16
            iot_ty = iot.fy >> 16
            is_hover = (abs(iot_tx - tile_x) <= 1 and abs(iot_ty - tile_y) <= 1)
            if not is_hover and getattr(iot, 'dock_tile', None):
                dtx, dty = iot.dock_tile
                is_hover = (abs(dtx - tile_x) <= 1 and abs(dty - tile_y) <= 1)
            if is_hover:
                iot.is_hovered = True
                self.hovered_civ = iot
            else:
                iot.is_hovered = False
                
        # Handle Pursuit
        if hasattr(self, 'pursuit_target') and self.pursuit_target:
            from src.entities.civilian import CivilState
            if getattr(self.pursuit_target, 'state', None) == CivilState.DEAD or getattr(self.pursuit_target, 'alpha', 1.0) <= 0:
                self.pursuit_target = None
                self.player.speed = 20 << 16
                self.action_menu.close()
            else:
                ptx, pty = self.player.fx >> 16, self.player.fy >> 16
                ctx, cty = self.pursuit_target.fx >> 16, self.pursuit_target.fy >> 16
                
                dock_tile = getattr(self.pursuit_target, 'dock_tile', None)
                if dock_tile:
                    gtx, gty = dock_tile
                else:
                    gtx, gty = ctx, cty
                
                dx = abs(ptx - gtx)
                dy = abs(pty - gty)
                
                if dx + dy > 1:
                    self.action_menu.close()
                    # Catch-up phase
                    self.player.speed = 20 << 16
                    recalc = False
                    if not self.player.target_path:
                        recalc = True
                    else:
                        final_x, final_y = self.player.target_path[-1]
                        if abs(final_x - gtx) + abs(final_y - gty) > 0:
                            recalc = True
                        
                    if recalc:
                        path = a_star(self.grid, (ptx, pty), (gtx, gty))
                        if path:
                            self.player.set_path(path)
                            self.player.move_marker.stop()
                else:
                    # Sync phase
                    if self.pursuit_target.target_path:
                        civ_next = self.pursuit_target.target_path[0]
                        
                        player_dist_to_goal = abs(ptx - civ_next[0]) + abs(pty - civ_next[1])
                        civ_dist_to_goal = abs(ctx - civ_next[0]) + abs(cty - civ_next[1])
                        
                        # Wenn der Spieler näher am Ziel ist als der Zivilist, ist er ZU WEIT VORNE. -> Warten!
                        if player_dist_to_goal < civ_dist_to_goal:
                            self.player.speed = 0
                            # Pfad kann bleiben, wir warten einfach, bis der Zivilist uns überholt.
                        else:
                            # Berechne exakte Subpixel-Distanz (Manhattan)
                            dist_sub = abs(self.player.fx - self.pursuit_target.fx) + abs(self.player.fy - self.pursuit_target.fy)
                            target_dist = 65536 # 1.0 Tile (8 Pixel) in Q16.16
                            
                            if dist_sub < target_dist:
                                self.player.speed = 0 # Pausieren wenn zu nah
                            else:
                                excess = dist_sub - target_dist
                                self.player.speed = (4 << 16) + int(excess * 2.0)
                                
                            # A* benutzen um Ecken-Schneiden (Diagonalbewegung) zu verhindern
                            if not self.player.target_path or self.player.target_path[-1] != civ_next:
                                path = a_star(self.grid, (ptx, pty), civ_next)
                                if path:
                                    self.player.set_path(path)
                                    self.player.move_marker.stop()
                    else:
                        self.player.target_path = []
                        self.player.state = 0
                        
                    # Minigame / Menu logic
                    cam_x, cam_y = self.camera.get_offset()
                    zoom = self.camera.zoom
                    screen_x = int((((self.pursuit_target.fx * 8) >> 16) - cam_x) * zoom)
                    screen_y = int((((self.pursuit_target.fy * 8) >> 16) - cam_y) * zoom)
                    
                    self.action_menu.open(screen_x + 10, screen_y)
                    
                    if self.action_menu.state == "INFILTRATING":
                        # Random suspicion check
                        if not self.pursuit_target.is_suspicious and not self.action_menu.is_paused and random.random() < 0.005:
                            self.pursuit_target.is_suspicious = True
                            self.pursuit_target.suspicion_timer = 2.0
                            
                        if self.pursuit_target.is_suspicious and self.action_menu.is_paused:
                            self.pursuit_target.suspicion_timer -= dt
                            self.action_menu.progress = max(0.0, self.action_menu.progress - 15.0 * dt)
                            if self.pursuit_target.suspicion_timer <= 0:
                                self.pursuit_target.is_suspicious = False
                        elif not self.action_menu.is_paused:
                            self.action_menu.progress += 33.3 * dt
                            
                            # Sound loop
                            if not hasattr(self, 'infiltrate_timer'):
                                self.infiltrate_timer = 0.0
                            self.infiltrate_timer -= dt
                            if self.infiltrate_timer <= 0:
                                sm_instance = self.sm.context.get("sound_manager")
                                if sm_instance:
                                    snd = random.choice(["infiltrate 1", "infiltrate 2"])
                                    sm_instance.play_spatial(snd, px, py, px, py, base_volume=0.5)
                                self.infiltrate_timer = 0.4
                                
                        if self.action_menu.progress >= 100.0:
                            # Success!
                            sm_instance = self.sm.context.get("sound_manager")
                            if sm_instance:
                                sm_instance.play_spatial("hack_success", px, py, px, py, base_volume=1.0)
                            self.data_fragments += 3
                            self.pursuit_target.is_robbed = True
                            if hasattr(self.pursuit_target, 'is_hacked'):
                                self.pursuit_target.is_hacked = True
                            self.pursuit_target.is_pursued = False
                            self.pursuit_target = None
                            self.player.target_path = []
                            self.player.state = 0
                            self.player.speed = 20 << 16
                            self.action_menu.close()

        self._update_fog_of_war()

    def update_draw(self) -> None:
        surface = self.sm.context.get("native_surface")
        if not surface:
            return
            
        active_driver = self.hud.driver_container.get_active_camera_driver()
        
        # 1. Kein Kamera-Treiber montiert -> Pitch Black Screen
        if active_driver is None:
            surface.fill((5, 5, 5))
            from src.ui.font_manager import font_mgr, GREEN_TERMINAL
            txt1 = font_mgr.render("NO CAMERA DRIVER DETECTED", color=(255, 50, 50), size="small")
            txt2 = font_mgr.render("EQUIP CAMERA DRIVER IN [/sys/deck/drivers]", color=GREEN_TERMINAL, size="tiny")
            surface.blit(txt1, ((640 - txt1.get_width()) // 2, 150))
            surface.blit(txt2, ((640 - txt2.get_width()) // 2, 170))
            self._draw_hud_scaled(surface)
            return

        # Parallax Background Layer 2 (Backdrop) & Layer 1 (Coarse Pulsating Grid)
        self._draw_parallax_background(surface)
        cam_x, cam_y = self.camera.get_offset()
        zoom = self.camera.zoom
        
        px_tile = self.player.grid_x
        py_tile = self.player.grid_y
        
        # 2. Zeichne das Grid (PCB Traces - 1px Linien, skaliert)
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.grid[y][x] in (0, 2):
                    if active_driver == "disp.drv":
                        # Exploration / Fog Check
                        if not self.explored_grid[y][x]:
                            continue # Unexplored in disp.drv remains black
                        is_active_vision = ((x - px_tile)**2 + (y - py_tile)**2 <= 25)
                    else:
                        is_active_vision = True
                        
                    cx = int(((x * 8) - cam_x + 4) * zoom)
                    cy = int(((y * 8) - cam_y + 4) * zoom)
                    
                    line_color = (0, 150, 100) if is_active_vision else (0, 45, 30)
                    
                    if x < self.map_width - 1 and self.grid[y][x+1] in (0, 2):
                        if active_driver != "disp.drv" or self.explored_grid[y][x+1]:
                            nx = int(((x * 8 + 8) - cam_x + 4) * zoom)
                            pygame.draw.line(surface, line_color, (cx, cy), (nx, cy), max(1, int(1 * zoom)))
                    if y < self.map_height - 1 and self.grid[y+1][x] in (0, 2):
                        if active_driver != "disp.drv" or self.explored_grid[y+1][x]:
                            ny = int(((y * 8 + 8) - cam_y + 4) * zoom)
                            pygame.draw.line(surface, line_color, (cx, cy), (cx, ny), max(1, int(1 * zoom)))
                    
                    if active_driver == "disp.drv":
                        node_color = (0, 150, 100) if is_active_vision else (0, 55, 35)
                        pygame.draw.circle(surface, node_color, (cx, cy), max(1, int(1.5 * zoom)))
                    else:
                        if self.grid[y][x] == 2:
                            pygame.draw.circle(surface, (255, 150, 0), (cx, cy), max(1, int(3 * zoom)))
                            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), max(1, int(1 * zoom)))
                        else:
                            pygame.draw.circle(surface, (0, 200, 150), (cx, cy), max(1, int(1.5 * zoom)))
                    
        show_target_anim = (active_driver == "ucam.drv")
        
        # 3. Zivilisten rendern
        for civ in self.civilians:
            cx_tile = civ.fx >> 16
            cy_tile = civ.fy >> 16
            if active_driver == "disp.drv":
                if (cx_tile - px_tile)**2 + (cy_tile - py_tile)**2 <= 25:
                    civ.draw(surface, cam_x, cam_y, zoom, override_color=(0, 150, 100), show_target_anim=show_target_anim)
            else:
                civ.draw(surface, cam_x, cam_y, zoom, show_target_anim=show_target_anim)
            
        # 3.5 IoT Surveillance Nodes rendern
        for iot in self.iot_devices:
            iot_x_tile = iot.fx >> 16
            iot_y_tile = iot.fy >> 16
            if active_driver == "disp.drv":
                if (iot_x_tile - px_tile)**2 + (iot_y_tile - py_tile)**2 <= 25:
                    iot.draw(surface, cam_x, cam_y, zoom, override_color=(0, 150, 100), show_target_anim=show_target_anim)
            else:
                iot.draw(surface, cam_x, cam_y, zoom, show_target_anim=show_target_anim)
            
        # 4. Sentinels rendern
        for sentinel in self.sentinels:
            sx_tile = sentinel.fx >> 16
            sy_tile = sentinel.fy >> 16
            if active_driver == "disp.drv":
                if (sx_tile - px_tile)**2 + (sy_tile - py_tile)**2 <= 25:
                    sentinel.draw(surface, cam_x, cam_y, zoom, override_color=(0, 150, 100), show_target_anim=show_target_anim)
            else:
                sentinel.draw(surface, cam_x, cam_y, zoom, show_target_anim=show_target_anim)
            
        self.player.draw(surface, cam_x, cam_y, zoom, show_target_anim=show_target_anim)
        
        self._draw_hud_scaled(surface)
        
        # 5. Game Over dead.png Fade Overlay (game world & interface fade out into dead.png)
        from src.utils.fade_controller import FadeState
        if hasattr(self, 'death_fade') and getattr(self, 'dead_img', None) and (self.game_over_ui or self.death_fade.is_fading or self.death_fade.progress > 0):
            dead_surf = self.dead_img.copy()
            dead_surf.set_alpha(self.death_fade.alpha)
            surface.blit(dead_surf, (0, 0))
            
        # 6. Death Message Box with RETRY Button (NOT FADED OUT! Rendered crisp on top of dead.png)
        if getattr(self, 'game_over_ui', False):
            self.game_over_menu.draw(surface)
            
        # 7. If restarting (FADE_OUT), apply overlay fading dead.png to black
        if not self.game_over_ui and hasattr(self, 'death_fade') and self.death_fade.state == FadeState.FADE_OUT:
            self.death_fade.draw_overlay(surface)
            
        # 8. Intro Fade-In Overlay beim Start von HUBGAME
        if hasattr(self, 'intro_fade') and self.intro_fade.is_fading:
            self.intro_fade.draw_overlay(surface)
        
    def _draw_hud_scaled(self, surface: pygame.Surface) -> None:
        values = {
            "threat": max(0.0, min(1.0, self.threat_level / 100.0)),
            "progress": (max(0.0, min(1.0, self.action_menu.progress / 100.0)) if self.action_menu.active else 0.0),
            "health": 1.0
        }
        feed_lines = self.terminal_feed.get_recent_lines(2) if hasattr(self, 'terminal_feed') else None
        self.hud.draw(surface, values, flip_x=self.emotion_engine.is_flipped, thought_text=self.emotion_engine.get_thought_text(), feed_lines=feed_lines)
        
        self.action_menu.draw(surface)
        
        # Datastore Anzeige (Oben Links)
        from src.ui.font_manager import font_mgr, GREEN_TERMINAL
        data_label = font_mgr.render(f"DATA FRAGMENTS: {self.data_fragments}", color=GREEN_TERMINAL, size="tiny")
        surface.blit(data_label, (16, 8))

    def _draw_parallax_background(self, surface: pygame.Surface) -> None:
        """
        Rendert zwei Parallax-Hintergrundebenen hinter der Spielkarte:
        - Layer 2 (Tiefste Ebene): backdrop.png, endlos wiederholend, schwache Farben, langsamste Bewegung (Factor 0.20)
        - Layer 1 (Mittlere Ebene): Grobmaschiges, pulsierendes Quadrat-Grid, endlos wiederholend (Factor 0.45)
        Der Ankerpunkt aller Ebenen liegt im Bildschirmzentrum (320, 180), damit beim Zoom
        realistisch aus der Mitte heraus skaliert wird.
        """
        import math
        center_x = self.camera.center_fx / 65536.0
        center_y = self.camera.center_fy / 65536.0
        zoom = self.camera.zoom

        screen_center_x = 320.0
        screen_center_y = 180.0

        # Basis-Hintergrundton (sehr dunkel, damit das Spiel gut lesbar bleibt)
        surface.fill((3, 6, 5))

        # -------------------------------------------------------------
        # Layer 2: Backdrop PNG (Endlos wiederholend, schwache Farben, Parallax factor 0.20)
        # -------------------------------------------------------------
        if getattr(self, 'backdrop_surf', None):
            bg_w = self.backdrop_surf.get_width()
            bg_h = self.backdrop_surf.get_height()

            bg_center_x = center_x * 0.20
            bg_center_y = center_y * 0.20

            phase_x_bg = (bg_center_x * zoom) % bg_w
            phase_y_bg = (bg_center_y * zoom) % bg_h

            start_x_bg = screen_center_x - phase_x_bg
            while start_x_bg > 0:
                start_x_bg -= bg_w
            start_y_bg = screen_center_y - phase_y_bg
            while start_y_bg > 0:
                start_y_bg -= bg_h

            y = int(start_y_bg)
            while y < 360:
                x = int(start_x_bg)
                while x < 640:
                    surface.blit(self.backdrop_surf, (x, y))
                    x += bg_w
                y += bg_h

        # -------------------------------------------------------------
        # Layer 1: Grobmaschiges Pulsierendes Quadrat-Grid (Parallax factor 0.45)
        # -------------------------------------------------------------
        p_time = getattr(self, 'parallax_time', 0.0)
        pulse = (math.sin(p_time * 2.0) + 1.0) / 2.0

        # Subtile, abgeschwächte Farbe
        r = 0
        g = int(14 + 18 * pulse)
        b = int(12 + 15 * pulse)
        grid_color = (r, g, b)

        grid_spacing = 48.0
        scaled_spacing = max(12.0, grid_spacing * zoom)

        grid_center_x = center_x * 0.45
        grid_center_y = center_y * 0.45

        phase_x_grid = (grid_center_x * zoom) % scaled_spacing
        phase_y_grid = (grid_center_y * zoom) % scaled_spacing

        start_x_grid = screen_center_x - phase_x_grid
        while start_x_grid > 0:
            start_x_grid -= scaled_spacing
        start_y_grid = screen_center_y - phase_y_grid
        while start_y_grid > 0:
            start_y_grid -= scaled_spacing

        gx = start_x_grid
        while gx < 640:
            if gx >= -1:
                pygame.draw.line(surface, grid_color, (int(gx), 0), (int(gx), 360), 1)
            gx += scaled_spacing

        gy = start_y_grid
        while gy < 360:
            if gy >= -1:
                pygame.draw.line(surface, grid_color, (0, int(gy)), (640, int(gy)), 1)
            gy += scaled_spacing
