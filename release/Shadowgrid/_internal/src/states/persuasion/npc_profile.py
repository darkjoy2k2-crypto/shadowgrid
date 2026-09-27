import random
import pygame
from typing import Dict, Tuple, Optional

class NPCProfile:
    """Repräsentiert ein gegnerisches Ziel aus der Shadowgrid-Datenbank für das Cyberdeck Combat Minigame."""
    def __init__(
        self,
        name: str,
        job: str,
        origin: str,
        category: str,
        image_path: str,
        face_surface: Optional[pygame.Surface],
        intelligence: int,
        intelligence_label: str,
        preferences: Dict[int, Tuple[str, float]],
        personality_traits: str = "Keine Angaben",
        comment_jack: str = "JACK // KEINE DATEN VORHANDEN.",
        base_disposition: int = 35
    ):
        self.name = name
        self.job = job
        self.origin = origin
        self.category = category
        self.image_path = image_path
        self.face_surface = face_surface
        self.intelligence = intelligence
        self.intelligence_label = intelligence_label
        self.preferences = preferences # 0..3 -> (RATING, MULTIPLIER)
        self.personality_traits = personality_traits
        self.comment_jack = comment_jack
        
        self.base_disposition = base_disposition
        self.disposition = base_disposition
        self.max_disposition = 100
        
        # Fog of War: [False, False, False, False] -> 4 Angriffskategorien
        self.revealed_preferences = [False, False, False, False]
