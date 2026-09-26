import pygame
import random
import math
from typing import Optional

class GlitchPostProcessor:
    """
    Vault66-inspiriertes CRT Post-Processing:
    - Echter Phosphor Glow (additive grüne Aura um UI & Schrift)
    - 100% stufenloses Alpha-Fading über Sinus-Wellen (self.time & dt)
    - Relevante Effekte bewegen sich stufenlos zwischen 20% (0.20) und 60% (0.60)
    - Schnellerer, geschmeidiger Wechsel (0.9s Dauer)
    - NUR die feinen Interlace-Scanlines scrollen ultra-langsam (3px/s)
    - CRT Corner Vignette (Vault66 Style)
    - Vollständig deaktivierbar im Death-Screen
    """
    def __init__(self, width: int = 640, height: int = 360) -> None:
        self.width = width
        self.height = height
        
        self.intensity = 0.08
        self.target_intensity = 0.08
        self.burst_intensity = 0.0
        
        self.time = 0.0
        self.ambient_glitch_timer = random.uniform(3.0, 5.0)
        self.active_slices: list[dict] = []
        self.active_rgb_shift: int = 1
        
        # Schnellerer Wechsel (0.9 Sekunden Gesamtdauer)
        self.waber_timer = 0.0
        self.waber_duration = 0.9 # 0.9s für zügigeren, geschmeidigen Wechsel
        
        # Pre-calculated Scanlines mit geviertelter Wirkungsstärke (21/255)
        self.scanline_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        for y in range(0, height, 2):
            pygame.draw.line(self.scanline_surf, (0, 0, 0, 21), (0, y), (width, y))

        # Pre-calculated CRT Corner Vignette (Vault66 Style)
        self.vignette_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        self._build_crt_vignette()

    def _build_crt_vignette(self) -> None:
        """Erzeugt eine abgerundete CRT-Monitor-Vignette für die Bildschirmecken."""
        cx, cy = self.width / 2.0, self.height / 2.0
        
        for y in range(0, self.height, 4):
            for x in range(0, self.width, 4):
                dx = (x - cx) / cx
                dy = (y - cy) / cy
                dist = (dx*dx*dx*dx + dy*dy*dy*dy) ** 0.5
                if dist > 0.6:
                    alpha = int(min(180, ((dist - 0.6) / 0.4) ** 2 * 180))
                    rect = pygame.Rect(x, y, 4, 4)
                    pygame.draw.rect(self.vignette_surf, (0, 0, 0, alpha), rect)

    def set_intensity(self, target: float) -> None:
        """Setzt die Ziel-Intensität (0.0 bis 1.0)."""
        self.target_intensity = max(0.05, min(1.0, target))

    def add_burst(self, amount: float = 0.5) -> None:
        """Startet das schnelle, stufenlose Sinus-Wabern des Effekts."""
        self._trigger_micro_glitch(force_burst=True)

    def _trigger_micro_glitch(self, force_burst: bool = False) -> None:
        """Generiert Slice-Positionen für das sanfte Sinus-Fading."""
        self.waber_timer = self.waber_duration
        
        self.active_slices = []
        num_slices = random.randint(1, 2)
        for _ in range(num_slices):
            h = random.randint(3, 6)
            y = random.randint(0, self.height - h)
            shift_dx = random.choice([-2, -1, 1, 2])
            self.active_slices.append({
                "y": y,
                "h": h,
                "dx": shift_dx
            })
            
        self.active_rgb_shift = random.randint(1, 2)

    def update(self, dt: float) -> None:
        self.time += dt
        
        # Smooth Intensität
        self.intensity += (self.target_intensity - self.intensity) * 4.0 * dt
        
        # Waber-Timer Fortschritt (0.9s -> 0s)
        if self.waber_timer > 0:
            self.waber_timer = max(0.0, self.waber_timer - dt)
        
        # Sporadische Trigger über Timer
        self.ambient_glitch_timer -= dt
        if self.ambient_glitch_timer <= 0:
            self.ambient_glitch_timer = random.uniform(3.5, 6.0)
            self._trigger_micro_glitch()

    def process(self, surface: pygame.Surface, disabled: bool = False) -> None:
        """Appliziert CRT Post-Processing. Wenn disabled=True, bleiben Glitches aus."""
        if disabled:
            scroll_y = int((self.time * 3.0) % self.height)
            surface.blit(self.scanline_surf, (0, scroll_y - self.height))
            surface.blit(self.scanline_surf, (0, scroll_y))
            surface.blit(self.vignette_surf, (0, 0))
            return

        # Continuous Sinus-Waber-Wert exakt zwischen 20% (0.20) und 60% (0.60)
        if self.waber_timer > 0:
            progress = (self.waber_duration - self.waber_timer) / self.waber_duration
            sin_val = math.sin(progress * math.pi)
            effective_intensity = 0.20 + sin_val * 0.40  # 0.20 bis max 0.60
        else:
            effective_intensity = 0.20  # Mindestens 20% Grund-Effekt

        # -------------------------------------------------------------
        # 1. Echter Phosphor Glow (Exakt 20% bis 60% Intensität)
        # -------------------------------------------------------------
        small_w = max(10, int(self.width * 0.40))
        small_h = max(10, int(self.height * 0.40))
        
        small_surf = pygame.transform.smoothscale(surface, (small_w, small_h))
        bloom_surf = pygame.transform.smoothscale(small_surf, (self.width, self.height))
        
        # Farbtönung skaliert stufenlos von 20% bis 60% (tint_g von ~42 bis ~126)
        tint_g = int(210 * effective_intensity)
        tint_b = int(110 * effective_intensity)
        bloom_tint = pygame.Surface((self.width, self.height))
        bloom_tint.fill((0, tint_g, tint_b))
        bloom_surf.blit(bloom_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        
        surface.blit(bloom_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        # -------------------------------------------------------------
        # 2. Smooth Ein- und Ausblendender RGB Shift (20% bis 60% Scale)
        # -------------------------------------------------------------
        if self.active_rgb_shift > 0:
            shift_g = int(180 * effective_intensity) # 36 (20%) bis 108 (60%)
            if shift_g > 0:
                rgb_tint = pygame.Surface((self.width, self.height))
                rgb_tint.fill((0, shift_g, shift_g // 2))
                rgb_surf = surface.copy()
                rgb_surf.blit(rgb_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
                surface.blit(rgb_surf, (self.active_rgb_shift, 0), special_flags=pygame.BLEND_RGB_ADD)

        # -------------------------------------------------------------
        # 3. Smooth Ein- und Ausblendende Slice Verschiebung (20% bis 60% Alpha)
        # -------------------------------------------------------------
        if self.active_slices:
            slice_alpha = int(effective_intensity * 255) # 51 (20%) bis 153 (60%)
            if slice_alpha > 0:
                temp_copy = surface.copy()
                for s in self.active_slices:
                    y = s["y"]
                    h = s["h"]
                    dx = s["dx"]
                    
                    slice_rect = pygame.Rect(0, y, self.width, h)
                    slice_surf = pygame.Surface((self.width, h), pygame.SRCALPHA)
                    slice_surf.blit(temp_copy.subsurface(slice_rect), (0, 0))
                    
                    # Echte Per-Pixel Transparenz für stufenloses Faden der Slices
                    alpha_tint = pygame.Surface((self.width, h), pygame.SRCALPHA)
                    alpha_tint.fill((255, 255, 255, slice_alpha))
                    slice_surf.blit(alpha_tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    
                    surface.blit(slice_surf, (dx, y))

        # -------------------------------------------------------------
        # 4. Scanlines (3px/s) & CRT Vignette
        # -------------------------------------------------------------
        scroll_y = int((self.time * 3.0) % self.height)
        surface.blit(self.scanline_surf, (0, scroll_y - self.height))
        surface.blit(self.scanline_surf, (0, scroll_y))
        surface.blit(self.vignette_surf, (0, 0))
