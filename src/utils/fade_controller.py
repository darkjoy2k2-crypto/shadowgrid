import pygame
from enum import IntEnum
from typing import Optional, Callable

class FadeState(IntEnum):
    IDLE = 0
    FADE_IN = 1
    FADE_OUT = 2

class FadeController:
    """
    Verwaltet sanftes Ein- und Ausblenden (Fade In / Fade Out) von Oberflächen,
    Bildern und Vollbild-Overlays in Shadowgrid.
    """
    def __init__(self) -> None:
        self.state = FadeState.IDLE
        self.progress = 0.0  # 0.0 = Schwarz/Unsichtbar, 1.0 = Voll sichtbar
        self.duration = 1.0
        self.on_complete: Optional[Callable[[], None]] = None

    def start_fade_in(self, duration: float = 1.0, on_complete: Optional[Callable[[], None]] = None) -> None:
        """Startet sanftes Einblenden (von Schwarz zu Motiv)."""
        self.state = FadeState.FADE_IN
        self.duration = max(0.01, duration)
        self.progress = 0.0
        self.on_complete = on_complete

    def start_fade_out(self, duration: float = 1.0, on_complete: Optional[Callable[[], None]] = None) -> None:
        """Startet sanftes Ausblenden (von Motiv zu Schwarz)."""
        self.state = FadeState.FADE_OUT
        self.duration = max(0.01, duration)
        self.progress = 1.0
        self.on_complete = on_complete

    def update(self, dt: float) -> None:
        if self.state == FadeState.IDLE:
            return

        step = dt / self.duration
        if self.state == FadeState.FADE_IN:
            self.progress = min(1.0, self.progress + step)
            if self.progress >= 1.0:
                self.state = FadeState.IDLE
                if self.on_complete:
                    cb = self.on_complete
                    self.on_complete = None
                    cb()
        elif self.state == FadeState.FADE_OUT:
            self.progress = max(0.0, self.progress - step)
            if self.progress <= 0.0:
                self.state = FadeState.IDLE
                if self.on_complete:
                    cb = self.on_complete
                    self.on_complete = None
                    cb()

    @property
    def is_fading(self) -> bool:
        return self.state != FadeState.IDLE

    @property
    def alpha(self) -> int:
        """Alpha-Wert (0..255) des sichtbaren Motivs."""
        return int(max(0.0, min(1.0, self.progress)) * 255)

    @property
    def overlay_alpha(self) -> int:
        """Alpha-Wert (0..255) des schwarzen Abdeck-Overlays."""
        return int((1.0 - max(0.0, min(1.0, self.progress))) * 255)

    def draw_overlay(self, surface: pygame.Surface) -> None:
        """Rendert ein schwarzes Fade-Overlay über die übergebene Oberfläche."""
        ov_alpha = self.overlay_alpha
        if ov_alpha > 0:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, ov_alpha))
            surface.blit(overlay, (0, 0))
