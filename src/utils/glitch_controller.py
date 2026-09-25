import pygame
import random
import math
from typing import Optional

class GlitchPostProcessor:
    """
    Vault66-inspiriertes CRT Post-Processing:
    - Phosphor Glow (additive grüne Aura um UI & Schrift)
    - Effekte flashen/blitzen NICHT mehr abrupt, sondern wabern langsam von 0 auf 0.5 und zurück auf 0
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
        self.ambient_glitch_timer = random.uniform(4.0, 7.0)
        self.active_slices: list[dict] = []
        self.active_rgb_shift: int = 0
        
        # Langsame Waber-Steuerung (0.0 -> 0.5 -> 0.0)
        self.waber_timer = 0.0
        self.waber_duration = 1.6 # 1.6 Sekunden langes, langsames Auf- und Ab-Wabern
        
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
        """Startet das langsame Wabern des Effekts von 0 auf 0.5."""
        self._trigger_micro_glitch(force_burst=True)

    def _trigger_micro_glitch(self, force_burst: bool = False) -> None:
        """Startet das langsame Wabern (1.6 Sekunden Gesamtdauer, ohne Blitze)."""
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
        
        # Waber-Timer Fortschritt (1.6s -> 0s)
        if self.waber_timer > 0:
            self.waber_timer = max(0.0, self.waber_timer - dt)
            if self.waber_timer <= 0:
                self.active_slices = []
                self.active_rgb_shift = 0
        
        # Sporadische Trigger über Timer
        self.ambient_glitch_timer -= dt
        if self.ambient_glitch_timer <= 0:
            self.ambient_glitch_timer = random.uniform(5.0, 9.0)
            self._trigger_micro_glitch()

    def process(self, surface: pygame.Surface, disabled: bool = False) -> None:
        """Appliziert CRT Post-Processing. Wenn disabled=True, bleiben Glitches aus."""
        if disabled:
            scroll_y = int((self.time * 3.0) % self.height)
            surface.blit(self.scanline_surf, (0, scroll_y - self.height))
            surface.blit(self.scanline_surf, (0, scroll_y))
            surface.blit(self.vignette_surf, (0, 0))
            return

        # Berechne den langsamen Waber-Wert (0.0 -> 0.5 -> 0.0) während des Effekts
        waber_val = 0.0
        if self.waber_timer > 0:
            progress = (self.waber_duration - self.waber_timer) / self.waber_duration
            waber_val = math.sin(progress * math.pi) * 0.5 # Woget langsam von 0 auf max 0.5 und zurück auf 0

        # -------------------------------------------------------------
        # 1. Echter Phosphor Glow (Stabile grüne Aura um UI & Schrift)
        # -------------------------------------------------------------
        small_w = max(10, int(self.width * 0.40))
        small_h = max(10, int(self.height * 0.40))
        
        small_surf = pygame.transform.smoothscale(surface, (small_w, small_h))
        bloom_surf = pygame.transform.smoothscale(small_surf, (self.width, self.height))
        
        # Phosphor-Grün Tönung (#00E676)
        bloom_tint = pygame.Surface((self.width, self.height))
        bloom_tint.fill((0, 210, 110))
        bloom_surf.blit(bloom_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        
        # Glow Alpha mit ruhiger konstanter Grundtönung + weichem Waber-Einfluss
        glow_alpha = int(14 + waber_val * 20) # Grundwert 14, steigt beim Wabern sanft auf max 24
        bloom_surf.set_alpha(glow_alpha)
        surface.blit(bloom_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # -------------------------------------------------------------
        # 2. Langsam wabernder RGB Shift (NUR aktiv wenn waber_val > 0)
        # -------------------------------------------------------------
        if self.active_rgb_shift > 0 and waber_val > 0.01:
            rgb_sub = surface.copy()
            rgb_sub.set_alpha(int(waber_val * 40)) # steigt langsam auf max 20 Alpha
            surface.blit(rgb_sub, (self.active_rgb_shift, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # -------------------------------------------------------------
        # 3. Langsam wabernde Subtile Slice Verschiebung (NUR aktiv wenn waber_val > 0)
        # -------------------------------------------------------------
        if self.active_slices and waber_val > 0.01:
            temp_copy = surface.copy()
            for s in self.active_slices:
                y = s["y"]
                h = s["h"]
                # Versatz moduliert mit dem Waber-Wert
                dx = round(s["dx"] * (waber_val * 2.0))
                if dx != 0:
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
