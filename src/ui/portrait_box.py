import os
import re
import pygame
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageSequence

class PortraitBox:
    """
    Shadowrun Genesis Portrait Frame.
    Verarbeitet Jack's Porträt-GIF (jack_portraits.gif) und die 19 Zustände aus jack_feels.txt.
    Rendert das aktive Cyberpunk-Decker Porträt im Metallrahmen.
    """
    def __init__(self, width: int = 48, height: int = 48) -> None:
        self.width = width
        self.height = height
        self.target_size = (width - 8, height - 8)
        
        self.emotions: Dict[int, str] = {}
        self.portrait_surfaces: Dict[int, pygame.Surface] = {}
        self.current_emotion: int = 6  # Standard: 6. Neutraler Blick
        
        self._load_jack_feels()
        self._load_jack_portraits_gif()

    def _load_jack_feels(self) -> None:
        """Liest jack_feels.txt ein und extrahiert die 19 Zustände."""
        txt_path = os.path.join("src", "gfx", "jack_feels.txt")
        if not os.path.isabs(txt_path):
            txt_path = os.path.abspath(txt_path)

        if os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    match = re.match(r'^(\d+)[\.\s]+(\d+[\.\s]+)?(.*)', line)
                    if match:
                        idx = int(match.group(1))
                        name = match.group(3).strip()
                        self.emotions[idx] = name

    def _load_jack_portraits_gif(self) -> None:
        """
        Lädt Jack's Porträt-Bilder direkt aus den Ressourcen im GFX-Ordner:
        1. Liest Einzelbilder aus src/gfx/jack_portraits/{emotion_id}.png.
        2. Liest Frames aus dem mehrrahmigen GIF src/gfx/jack_portraits.gif.
        """
        portraits_dir = os.path.join("src", "gfx", "jack_portraits")
        if not os.path.isabs(portraits_dir):
            portraits_dir = os.path.abspath(portraits_dir)

        # 1. Versuche Einzelbilder aus src/gfx/jack_portraits/{id}.png zu laden
        for emotion_id in range(1, 20):
            png_path = os.path.join(portraits_dir, f"{emotion_id}.png")
            if os.path.exists(png_path):
                try:
                    loaded = pygame.image.load(png_path).convert_alpha()
                    scaled = pygame.transform.scale(loaded, self.target_size)
                    self.portrait_surfaces[emotion_id] = scaled
                except Exception:
                    pass

        # Wenn alle 19 Zustände vollständig geladen wurden, sind wir fertig!
        if len(self.portrait_surfaces) >= 19:
            return

        # 2. Fallback / Ergänzung aus der GIF-Datei jack_portraits.gif
        gif_path = os.path.join("src", "gfx", "jack_portraits.gif")
        if not os.path.isabs(gif_path):
            gif_path = os.path.abspath(gif_path)

        if os.path.exists(gif_path):
            try:
                pil_img = Image.open(gif_path)
                frames = [f for f in ImageSequence.Iterator(pil_img)]
                for emotion_id in range(1, 20):
                    if emotion_id in self.portrait_surfaces:
                        continue
                    if len(frames) >= emotion_id:
                        f_rgba = frames[emotion_id - 1].convert('RGBA')
                        pg_surf = pygame.image.frombytes(f_rgba.tobytes(), f_rgba.size, 'RGBA')
                    elif len(frames) > 0:
                        f_rgba = frames[0].convert('RGBA')
                        pg_surf = pygame.image.frombytes(f_rgba.tobytes(), f_rgba.size, 'RGBA')
                    else:
                        pg_surf = self._generate_fallback_jack_base()

                    scaled = pygame.transform.scale(pg_surf, self.target_size)
                    self.portrait_surfaces[emotion_id] = scaled
            except Exception:
                pass

    def set_emotion(self, emotion_id: int) -> None:
        """Setzt den aktiven Porträt-Zustand (1 bis 19)."""
        self.current_emotion = max(1, min(19, emotion_id))

    def get_emotion_name(self) -> str:
        """Gibt den Namen des aktiven Zustands zurück."""
        return self.emotions.get(self.current_emotion, f"Zustand {self.current_emotion}")

    def draw(self, surface: pygame.Surface, x: int, y: int, flip_x: bool = False) -> None:
        """Blittet den Metallrahmen und das aktive Porträt an Position (x, y) mit optionalem Horizontal-Flip."""
        w, h = self.width, self.height

        # Metall-Rahmen Außen
        frame_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, (60, 70, 80), frame_rect)
        pygame.draw.rect(surface, (140, 150, 160), frame_rect, 1)
        pygame.draw.rect(surface, (15, 20, 25), (x + 1, y + 1, w - 2, h - 2), 1)

        # Porträt des aktuellen Zustands blitten
        portrait = self.portrait_surfaces.get(self.current_emotion)
        if portrait:
            if flip_x:
                portrait = pygame.transform.flip(portrait, True, False)
            inner_x = x + 4
            inner_y = y + 4
            surface.blit(portrait, (inner_x, inner_y))

        # Inner-Border Shadow
        pygame.draw.rect(surface, (0, 0, 0), (x + 4, y + 4, w - 8, h - 8), 1)
