import pygame
import random
import math
from typing import Optional

class GlitchPostProcessor:
    """
    Vault66-inspiriertes CRT Post-Processing:
    - Smooth auf- und ableuchtender Phosphor Glow (strikt zwischen 0.1 und 0.5)
    - Keine harten 0-1-0 Blitze oder Schirmeffekte
    - Feine Interlace-Scanlines scrollen ultra-langsam (3px/s)
    - Isolierte subtile Slice-Verschiebungen bei Bedrohung
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
        self.ambient_glitch_timer = random.uniform(3.0, 6.0)
        self.active_slices: list[dict] = []
        self.active_rgb_shift: int = 0
        self.glitch_duration_timer = 0.0
        
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
        """Fügt einen spontanen Glitch-Impuls hinzu."""
        self.burst_intensity = min(0.5, self.burst_intensity + amount * 0.3)
        self._trigger_micro_glitch(force_burst=True)

    def _trigger_micro_glitch(self, force_burst: bool = False) -> None:
        """Erzeugt sporadische Bildversätze ohne harte Licht-Blitze."""
        current = min(0.5, max(0.1, self.intensity + self.burst_intensity))
        self.glitch_duration_timer = random.uniform(0.05, 0.12) if not force_burst else 0.20
        
        num_slices = 1 if current < 0.25 else random.randint(1, 2)
        self.active_slices = []
        for _ in range(num_slices):
            h = random.randint(2, 4) if current < 0.25 else random.randint(3, 8)
            y = random.randint(0, self.height - h)
            shift_dx = random.choice([-1, 1]) if current < 0.25 else random.randint(-4, 4)
            self.active_slices.append({
                "y": y,
                "h": h,
                "dx": shift_dx
            })
            
        self.active_rgb_shift = 1 if current < 0.3 else random.randint(1, 2)

    def update(self, dt: float) -> None:
        self.time += dt
        
        # Smooth Intensität
        self.intensity += (self.target_intensity - self.intensity) * 4.0 * dt
        
        if self.burst_intensity > 0:
            self.burst_intensity = max(0.0, self.burst_intensity - 2.5 * dt)
            
        current = min(0.5, max(0.1, self.intensity + self.burst_intensity))
        
        # Sporadische Glitch-Trigger über Timer
        self.ambient_glitch_timer -= dt
        if self.ambient_glitch_timer <= 0:
            interval = max(0.5, random.uniform(3.0, 6.0) - current * 3.0)
            self.ambient_glitch_timer = interval
            self._trigger_micro_glitch()

        if self.glitch_duration_timer > 0:
            self.glitch_duration_timer -= dt
            if self.glitch_duration_timer <= 0:
                self.active_slices = []
                self.active_rgb_shift = 0

    def process(self, surface: pygame.Surface, disabled: bool = False) -> None:
        """Appliziert CRT Post-Processing. Wenn disabled=True, bleiben Glitches aus."""
        if disabled:
            scroll_y = int((self.time * 3.0) % self.height)
            surface.blit(self.scanline_surf, (0, scroll_y - self.height))
            surface.blit(self.scanline_surf, (0, scroll_y))
            surface.blit(self.vignette_surf, (0, 0))
            return

        # -------------------------------------------------------------
        # 1. Smooth Auf- und Ableuchtender Phosphor Glow (Strikt 0.1 bis 0.5)
        # -------------------------------------------------------------
        smooth_wave = 0.10 + 0.40 * (0.5 + 0.5 * math.sin(self.time * 1.5))
        
        small_w = max(10, int(self.width * 0.40))
        small_h = max(10, int(self.height * 0.40))
        
        small_surf = pygame.transform.smoothscale(surface, (small_w, small_h))
        bloom_surf = pygame.transform.smoothscale(small_surf, (self.width, self.height))
        
        # Phosphor-Grün Tönung (#00E676)
        bloom_tint = pygame.Surface((self.width, self.height))
        bloom_tint.fill((0, 210, 110))
        bloom_surf.blit(bloom_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        
        # Glow Alpha skaliert sanft & fließend mit smooth_wave (strikt 0.1 .. 0.5)
        glow_alpha = int(8 + smooth_wave * 28)
        bloom_surf.set_alpha(glow_alpha)
        surface.blit(bloom_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # -------------------------------------------------------------
        # 2. Dezent gesteuerter RGB Shift
        # -------------------------------------------------------------
        if self.active_rgb_shift > 0:
            rgb_sub = surface.copy()
            rgb_sub.set_alpha(int(12 + smooth_wave * 20))
            surface.blit(rgb_sub, (self.active_rgb_shift, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # -------------------------------------------------------------
        # 3. Subtile Slice Verschiebung (OHNE helle Licht-Blitze)
        # -------------------------------------------------------------
        if self.active_slices:
            temp_copy = surface.copy()
            for s in self.active_slices:
                y = s["y"]
                h = s["h"]
                dx = s["dx"]
                
                slice_rect = pygame.Rect(0, y, self.width, h)
                sub = temp_copy.subsurface(slice_rect).copy()
                surface.blit(sub, (dx, y))

        # -------------------------------------------------------------
        # 4. Scanlines (3px/s) & CRT Vignette
        # -------------------------------------------------------------
        scroll_y = int((self.time * 3.0) % self.height)
        surface.blit(self.scanline_surf, (0, scroll_y - self.height))
        surface.blit(self.scanline_surf, (0, scroll_y))
        surface.blit(self.vignette_surf, (0, 0))
