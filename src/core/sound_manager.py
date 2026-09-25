import pygame
import os
import random
import math
try:
    import numpy as np
except ImportError:
    np = None

# SOUND MAPPING TABELLE
# Hier kannst du jederzeit anpassen, welche .wav Datei für welches In-Game Event abgespielt werden soll.
# Links steht der interne Event-Name, rechts der Dateiname (ohne .wav/.ogg) im src/sfx Ordner.
SOUND_MAP = {
    "player_move": "player",
    "click_target": "set mark",
    "guardian_move": "guardian",
    "civ_move_1": "move 1",
    "civ_move_2": "move 2",
    "infiltrate_1": "infiltrate 1",
    "infiltrate_2": "infiltrate 2",
    "hack_success": "success",
    "alert_trigger": "alert",
    "game_over": "death",
    "action_cancel": "fail",
    "threat_pulse": "thread"
}

class SoundManager:
    """
    Spatial Audio Manager für Pygame.
    Unterstützt 2D-Panning (Links/Rechts), Distance-Volume und Pitch-Variationen.
    """
    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(32) # Genug Kanäle für viele SFX
        
        self.sounds = {}
        self.max_distance = 320.0 # Halbe Bildschirmbreite (640 / 2)
        
        self._load_sounds()
        
    def _load_sounds(self):
        import sys
        if hasattr(sys, '_MEIPASS'):
            sfx_dir = os.path.join(sys._MEIPASS, "src", "sfx")
        else:
            sfx_dir = os.path.join("src", "sfx")
            
        if not os.path.exists(sfx_dir):
            return
            
        for file in os.listdir(sfx_dir):
            if file.endswith(('.wav', '.ogg')):
                name = os.path.splitext(file)[0]
                path = os.path.join(sfx_dir, file)
                try:
                    base_sound = pygame.mixer.Sound(path)
                    # Erzeuge Variationen für weniger Audio Fatigue
                    self.sounds[name] = self._generate_pitch_variations(base_sound)
                except Exception as e:
                    print(f"Failed to load sound {path}: {e}")
                    
    def _generate_pitch_variations(self, base_sound: pygame.mixer.Sound, num_variations: int = 3):
        """Erzeugt leicht gepitchte Versionen des Sounds."""
        variations = [base_sound]
        
        if np is None:
            # Fallback wenn numpy nicht installiert ist: Einfach gleicher Sound
            return variations * num_variations
            
        try:
            # Pygame Sound zu Numpy Array
            array = pygame.sndarray.array(base_sound)
            
            pitches = [0.95, 1.05] # Leichter Pitch nach unten und oben
            
            for pitch in pitches:
                # Einfaches Resampling
                old_indices = np.arange(0, len(array))
                new_length = int(len(array) / pitch)
                new_indices = np.linspace(0, len(array) - 1, new_length)
                
                # Resample für linke und rechte Spur
                if len(array.shape) > 1:
                    resampled = np.zeros((new_length, array.shape[1]), dtype=array.dtype)
                    for channel in range(array.shape[1]):
                        resampled[:, channel] = np.interp(new_indices, old_indices, array[:, channel])
                else:
                    resampled = np.interp(new_indices, old_indices, array).astype(array.dtype)
                    
                new_sound = pygame.sndarray.make_sound(resampled)
                variations.append(new_sound)
                
        except Exception as e:
            print(f"Pitch variation failed: {e}")
            
        return variations
        
    def play_spatial(self, event_name: str, source_x: float, source_y: float, listener_x: float, listener_y: float, base_volume: float = 1.0):
        """
        Spielt einen Sound räumlich ab.
        source_x/y und listener_x/y sollten in Screen- oder Welt-Pixeln sein.
        """
        file_key = SOUND_MAP.get(event_name, event_name)
        if file_key not in self.sounds or not self.sounds[file_key]:
            return
            
        dx = source_x - listener_x
        dy = source_y - listener_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Culling: Wenn zu weit weg (mehr als halbe Screen-Width), gar nicht spielen
        if distance > self.max_distance:
            return
            
        # Volume Falloff (Linear)
        distance_vol = 1.0 - (distance / self.max_distance)
        
        # Panning (-1 = ganz links, 1 = ganz rechts)
        # Wir klemmen dx auf max_distance, um pan zwischen -1 und 1 zu halten
        clamped_dx = max(-self.max_distance, min(self.max_distance, dx))
        pan = clamped_dx / self.max_distance
        
        # Dolby-Trick Approximation: 
        # Töne von hinten/unten (dy > 0) dämpfen wir leicht (Lowpass Simulation durch Volume-Cut)
        if dy > 0:
            distance_vol *= 0.8
            
        final_vol = base_volume * distance_vol
        
        # Verbessertes Panning: Zentrum spielt auf beiden Kanälen mit voller final_vol
        left_vol = final_vol * min(1.0, 1.0 - pan)
        right_vol = final_vol * min(1.0, 1.0 + pan)
        
        # Spiele eine zufällige Pitch-Variation ab
        sound = random.choice(self.sounds[file_key])
        
        channel = pygame.mixer.find_channel()
        if channel:
            channel.set_volume(left_vol, right_vol)
            channel.play(sound)
            from src.utils.perception_logger import perception_logger
            perception_logger.log_event("AUDIO_SFX", {
                "sound": event_name,
                "volume": round(final_vol, 2)
            })
