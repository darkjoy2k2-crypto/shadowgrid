import pygame
import sys
import argparse
from typing import Optional
from src.core.state_machine import StateMachine
from src.utils.logger import logger

# Konstanten für Rendering und Skalierung
NATIVE_WIDTH = 640
NATIVE_HEIGHT = 360
TARGET_FPS = 60

class GameApp:
    """
    Hauptklasse der Shadowgrid-Anwendung.
    Verwaltet Pygame-Initialisierung, Main-Loop, nativen 640x360 Canvas,
    saubere Desktop-Vollbildskalierung und absturzsicheren Shutdown.
    """
    def __init__(self, target_width: int, target_height: int, display_index: int, fullscreen: bool) -> None:
        logger.info(f"Initializing GameApp: {target_width}x{target_height}, Display {display_index}, Fullscreen: {fullscreen}")
        pygame.init()
        pygame.display.set_caption("Shadowgrid - Terminal OS")
        
        self.display_index = display_index
        self.is_fullscreen = fullscreen
        
        # Bestimme native Desktop-Auflösung um schädliche Hardware-Res-Switches & Windows-Freezes zu verhindern
        self.desktop_width = target_width
        self.desktop_height = target_height
        
        try:
            desktop_sizes = pygame.display.get_desktop_sizes()
            if desktop_sizes and 0 <= display_index < len(desktop_sizes):
                self.desktop_width, self.desktop_height = desktop_sizes[display_index]
            else:
                info = pygame.display.Info()
                if info.current_w > 0 and info.current_h > 0:
                    self.desktop_width, self.desktop_height = info.current_w, info.current_h
        except Exception as e:
            logger.warning(f"Could not query desktop sizes: {e}")

        # Setze Zielauflösung
        if self.is_fullscreen:
            self.screen_width = self.desktop_width
            self.screen_height = self.desktop_height
        else:
            self.screen_width = target_width
            self.screen_height = target_height

        self.screen: Optional[pygame.Surface] = None
        self._set_display_mode()

        # Native Surface für alle 640x360 Render-Aufrufe
        self.native_surface = pygame.Surface((NATIVE_WIDTH, NATIVE_HEIGHT))
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Initialisiere StateMachine
        self.sm = StateMachine()
        self.sm.context["native_surface"] = self.native_surface
        
        # Initialisiere GlitchPostProcessor für globale CRT Phosphor/Glitch-Effekte
        from src.utils.glitch_controller import GlitchPostProcessor
        self.glitch_processor = GlitchPostProcessor(NATIVE_WIDTH, NATIVE_HEIGHT)
        self.sm.context["glitch_processor"] = self.glitch_processor

        from src.core.sound_manager import SoundManager
        self.sm.context["sound_manager"] = SoundManager()
        
        from src.states.title_state import TitleState
        from src.states.hub_state import HubState
        from src.states.hacking_state import HackingState
        from src.states.game_over_state import GameOverState
        
        self.sm.register_state("TITLE", TitleState(self.sm))
        self.sm.register_state("HUBGAME", HubState(self.sm))
        self.sm.register_state("HACKING", HackingState(self.sm))
        self.sm.register_state("GAMEOVER", GameOverState(self.sm))
        self.sm.change_state("TITLE")

    def _set_display_mode(self) -> None:
        """Setzt den Pygame Display-Modus sicher und ohne Windows Hardware-Lockups."""
        flags = pygame.DOUBLEBUF | pygame.HWSURFACE
        if self.is_fullscreen:
            flags |= pygame.FULLSCREEN
            w, h = self.desktop_width, self.desktop_height
        else:
            w, h = self.screen_width, self.screen_height

        try:
            self.screen = pygame.display.set_mode((w, h), flags=flags, display=self.display_index)
        except Exception as e:
            logger.error(f"Failed to set display mode (fullscreen={self.is_fullscreen}): {e}")
            # Fallback auf Fenster-Modus
            self.is_fullscreen = False
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), display=self.display_index)

    def toggle_fullscreen(self) -> None:
        """Wechselt fließend zwischen Vollbild und Fenster-Modus (F11 / Alt+Enter)."""
        self.is_fullscreen = not self.is_fullscreen
        self._set_display_mode()

    def handle_events(self) -> None:
        """Verarbeitet globale Pygame-Events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_F11 or (event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT)):
                    self.toggle_fullscreen()
            self.sm.handle_event(event)

    def update(self, dt: float) -> None:
        self.glitch_processor.update(dt)
        self.sm.update(dt)

    def update_draw(self) -> None:
        self.sm.update_draw()

    def run(self) -> None:
        """Hauptschleife (Main-Loop) mit try...finally Absicherung für sauberen Shutdown."""
        try:
            while self.running:
                dt = self.clock.tick(TARGET_FPS) / 1000.0
                
                self.handle_events()
                self.update(dt)
                self.update_draw()
                
                # Glitch Post-Processing auf native 640x360 Surface anwenden
                self.glitch_processor.process(self.native_surface)
                
                # Skalierung der nativen 640x360 Surface auf die Fenster-/Bildschirmgröße
                if self.screen:
                    scaled_surface = pygame.transform.scale(self.native_surface, self.screen.get_size())
                    self.screen.blit(scaled_surface, (0, 0))
                    pygame.display.flip()
        except Exception as e:
            logger.critical(f"Unhandled exception in GameApp main loop: {e}", exc_info=True)
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Schließt alle Ressourcen, gibt Display-Locks frei und beendet den Prozess sauber."""
        logger.info("Shutting down Shadowgrid cleanly.")
        self.running = False
        try:
            pygame.event.set_grab(False)
            pygame.mouse.set_visible(True)
            pygame.display.quit()
            pygame.quit()
        except Exception as e:
            logger.warning(f"Error during shutdown: {e}")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Shadowgrid Game Engine")
    parser.add_argument("--width", type=int, default=1280, help="Target window width")
    parser.add_argument("--height", type=int, default=720, help="Target window height")
    parser.add_argument("--display", type=int, default=0, help="Monitor index")
    parser.add_argument("--fullscreen", action="store_true", help="Enable fullscreen mode")
    args = parser.parse_args()
    
    app = GameApp(args.width, args.height, args.display, args.fullscreen)
    app.run()
