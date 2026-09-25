import enum
import math
import random
import os
from typing import Optional, Dict, Any, List
from src.utils.perception_logger import perception_logger
from src.core.jack_database import JackDatabase

class JackEmotion(enum.IntEnum):
    MANIC_LAUGH = 1       # 1. Manisches lachen.
    LAUGH = 2             # 2. Lachen
    GRIN = 3              # 3. Grinsen
    FRIENDLY = 4          # 4. Freundlicher Blick
    THINKING = 5          # 5. Überlegend, einschätzend
    NEUTRAL = 6           # 6. Neutraler Blick
    SURPRISED = 7         # 7. Überrascht
    UNDECIDED = 8         # 8. Unschlüssig
    GRUMPY = 9            # 9. Mürrisch
    QUESTIONING = 10      # 10. Fragend (neigend)
    COOL = 11             # 11. Cooler Blick
    EVALUATING = 12       # 12. Einschätzend/Bewertend
    BAD_MOOD = 13         # 13. Schlechte Laune
    ANGRY = 14            # 14. Zornig
    FURIOUS = 15          # 15. Wütend
    FRUSTRATED = 16       # 16. Frustriert
    AGGRESSIVE_PAIN = 17 # 17. Aggressiv oder schmerzhaft
    SCREAMING_PAIN = 18  # 18. Schreiend / extrem schmerzhaft
    DEAD = 19             # 19. Tot.

class EmotionEngine:
    """
    Mathematischer Emotions-Synthesizer mit Anbindung an:
    - Strukturierte SQLite Datenbank (src/data/jack_memory.db)
    - KI-optimiertes Token-PerceptionLog (inkl. Jacks Selbst-Wahrnehmung "J")
    - Arsenale für seltene vs. häufige/repetitive Events
    - Anti-Repetitions-Mechanik & Cooldown gegen 10x Nachrichten-Spam
    """
    def __init__(self) -> None:
        self.v: float = 0.0      # Valenz (-100 bis +100)
        self.a: float = 10.0     # Arousal (0 bis 100)
        self.h: float = 100.0    # Integrität (0 bis 100)

        self.v_base: float = 0.0
        self.a_base: float = 10.0

        self.decay_v_rate: float = 0.4
        self.decay_a_rate: float = 0.4

        self.current_emotion: int = JackEmotion.NEUTRAL
        self.is_flipped: bool = False
        
        self.thought_text: str = "JACK // ONLINE"
        self.speech_cooldown: float = 0.0  # Verhindert mehrfaches Sprechen in kurzer Zeit
        
        # SQLite Datenbank
        self.db = JackDatabase()
        self.situation_counters: Dict[str, int] = {}
        self.last_processed_time: float = -1.0

    def init_spawn(self) -> None:
        """Initialisiert Jack's Vektor und setzt das Session-Log bei neuem Spawn/Tod zurück."""
        self.v = 0.0
        self.a = 10.0
        self.h = 100.0
        self.current_emotion = JackEmotion.NEUTRAL
        self.is_flipped = False
        self.thought_text = "JACK // ONLINE"
        self.speech_cooldown = 0.0
        self.last_processed_time = -1.0
        self.situation_counters.clear()
        perception_logger.clear_session_log()

    def apply_impulse(self, dv: float, da: float, dh: float = 0.0) -> None:
        """Beaufschlagt den 3D-Vektor mit einem Impuls (ΔV, ΔA, ΔH)."""
        self.v = max(-100.0, min(100.0, self.v + dv))
        self.a = max(0.0, min(100.0, self.a + da))
        self.h = max(0.0, min(100.0, self.h + dh))

    def set_thought_text(self, text: str, situation_key: str = "GENERAL", cooldown: float = 6.0) -> None:
        """Setzt den Gedankentext, aktiviert Cooldown und protokolliert einmalig Selbstwahrnehmung (J)."""
        self.thought_text = text
        self.speech_cooldown = cooldown
        perception_logger.log_jack_thought(text, situation_key)

    def get_thought_text(self) -> str:
        """Liest den aktuellen Gedankentext für die UI-Ausgabe (bleibt dauerhaft stehen)."""
        return self.thought_text

    def set_portrait(self, emotion_id: int, is_flipped: bool = False) -> None:
        """Setzt explizit Jack's Porträt-Frame (1..19) und Blickrichtung."""
        self.current_emotion = max(1, min(19, emotion_id))
        self.is_flipped = is_flipped

    def trigger_existential_freakout(self) -> str:
        """
        Löst einen existentiellen Truman-Show-Ausraster aus, wenn Jack/Spieler
        seine vergangenen Log-Dateien liest.
        Effekte:
        - Vektor-Impuls: ΔV = -80.0, ΔA = +90.0
        - Porträt-Shift: SCREAMING_PAIN (18) oder FURIOUS (15)
        - Sprachausgabe & Selbstwahrnehmung
        """
        phrase, _ = self.db.select_phrase("TRUMAN_FREAKOUT", occurrence_count=10)
        self.apply_impulse(dv=-80.0, da=90.0, dh=0.0)
        chosen_portrait = JackEmotion.SCREAMING_PAIN if random.random() < 0.5 else JackEmotion.FURIOUS
        self.set_portrait(chosen_portrait, is_flipped=False)
        self.set_thought_text(phrase, situation_key="TRUMAN_FREAKOUT", cooldown=10.0)
        return phrase

    def read_perception_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Liest die jüngsten Ereignisse aus dem Wahrnehmungs-Log."""
        return perception_logger.get_latest_events(limit=limit)

    def process_perception_events(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Verarbeitet neue Perception-Events. Wendet Impulse sofort an,
        triggert Sprache jedoch nur bei Ablauf des Cooldowns oder kritischen Events.
        """
        recent_events = perception_logger.get_latest_events(limit=25)
        new_events = [e for e in recent_events if e["t"] > self.last_processed_time]
        
        for ev in new_events:
            self.last_processed_time = max(self.last_processed_time, ev["t"])
            event_token = ev.get("e", "")
            data = ev.get("d", {})
            
            situation_key: Optional[str] = None
            is_critical: bool = False
            
            if event_token in ("SESSION_START", "S"):
                situation_key = "SESSION_START"
                is_critical = True
            elif event_token in ("SCANNER_INTERCEPT", "SI"):
                situation_key = "SCANNER_INTERCEPT"
                is_critical = True
            elif event_token in ("CIVILIAN_ENCOUNTER", "C"):
                situation_key = "CIVILIAN_ENCOUNTER"
                if random.random() < 0.5:
                    self.is_flipped = not self.is_flipped
            elif event_token in ("PATH_STARTED", "P"):
                length = data.get("length", 1)
                is_dir_change = data.get("is_direction_change", False)

                min_sentinel_dist = context.get("min_sentinel_dist", 999.0) if context else 999.0
                threat_lvl = context.get("threat_level", 0.0) if context else 0.0
                is_on_scanner = context.get("is_on_scanner", False) if context else False

                if threat_lvl > 15.0 or min_sentinel_dist <= 5.0:
                    situation_key = "SENTINEL_NEAR"
                    is_critical = True
                elif is_on_scanner:
                    situation_key = "IOT_AWARENESS"
                    is_critical = True
                elif is_dir_change:
                    situation_key = "DIRECTION_CHANGE"
                    self.is_flipped = not self.is_flipped
                elif length >= 15:
                    situation_key = "LONG_WALK"
                else:
                    situation_key = "EXPLORATION_SHORT"
            elif event_token in ("INPUT_CLICK", "M") and data.get("ui_clicked"):
                situation_key = "UI_INTERACTION"
            elif event_token in ("EQUIPMENT_MOUNT", "EQ_M"):
                situation_key = "EQUIPMENT_MOUNT"
                is_critical = True
            elif event_token in ("EQUIPMENT_UNMOUNT", "EQ_U"):
                situation_key = "EQUIPMENT_UNMOUNT"
                is_critical = True
            elif event_token in ("ALERT_TRIGGERED", "A"):
                situation_key = "ALERT_TRIGGERED"
                is_critical = True
            elif event_token in ("PLAYER_CAUGHT", "PC"):
                situation_key = "PLAYER_CAUGHT"
                is_critical = True
            elif event_token in ("GAME_OVER", "G"):
                situation_key = "GAME_OVER"
                is_critical = True
            elif event_token in ("JACK_THOUGHT", "J"):
                continue
                
            if situation_key:
                count = self.situation_counters.get(situation_key, 0) + 1
                self.situation_counters[situation_key] = count
                
                phrase, sit_info = self.db.select_phrase(situation_key, occurrence_count=count)
                
                # Vektor-Impuls stets sofort anwenden
                self.apply_impulse(
                    dv=sit_info.get("dv", 0.0),
                    da=sit_info.get("da", 0.0),
                    dh=sit_info.get("dh", 0.0)
                )
                
                # Sprache NUR auslösen wenn Phrase existiert und Cooldown abgelaufen ist!
                if phrase and (is_critical or self.speech_cooldown <= 0):
                    self.set_thought_text(phrase, situation_key=situation_key, cooldown=6.0)
                    break # Nur 1 Gedanke pro Frame-Verarbeitungszyklus!

        # Context-basierte Spontan-Gedanken, z.B. wenn Sentinels nah sind oder Scanner aktiv ist und Jack schweigend da steht
        if self.speech_cooldown <= 0 and context:
            min_dist = context.get("min_sentinel_dist", 999.0)
            threat_lvl = context.get("threat_level", 0.0)
            is_on_scanner = context.get("is_on_scanner", False)
            
            if min_dist <= 5.0 or threat_lvl > 15.0:
                count = self.situation_counters.get("SENTINEL_NEAR", 0) + 1
                phrase, sit_info = self.db.select_phrase("SENTINEL_NEAR", occurrence_count=count)
                if phrase:
                    self.situation_counters["SENTINEL_NEAR"] = count
                    self.apply_impulse(dv=sit_info.get("dv", -30.0), da=sit_info.get("da", 60.0), dh=0.0)
                    self.set_thought_text(phrase, situation_key="SENTINEL_NEAR", cooldown=7.0)
            elif is_on_scanner:
                count = self.situation_counters.get("IOT_AWARENESS", 0) + 1
                phrase, sit_info = self.db.select_phrase("IOT_AWARENESS", occurrence_count=count)
                if phrase:
                    self.situation_counters["IOT_AWARENESS"] = count
                    self.apply_impulse(dv=sit_info.get("dv", -20.0), da=sit_info.get("da", 45.0), dh=0.0)
                    self.set_thought_text(phrase, situation_key="IOT_AWARENESS", cooldown=7.0)

    def update(self, dt: float, context: Optional[Dict[str, Any]] = None) -> int:
        """
        Verarbeitet neue Perception-Events, senkt Cooldown/Decay und evaluiert das Porträt.
        """
        if self.speech_cooldown > 0:
            self.speech_cooldown -= dt

        self.process_perception_events(context)

        decay_v_factor = 1.0 - math.exp(-self.decay_v_rate * dt)
        decay_a_factor = 1.0 - math.exp(-self.decay_a_rate * dt)
        self.v += (self.v_base - self.v) * decay_v_factor
        self.a += (self.a_base - self.a) * decay_a_factor

        if context:
            if context.get("is_game_over", False):
                self.h = 0.0

        self.current_emotion = self.evaluate_frame()
        return self.current_emotion

    def evaluate_frame(self) -> int:
        """2-Stufen-Projektion vom 3D-Vektor (V, A, H) auf das 19-Porträt-Set."""
        if self.h <= 0.0:
            return JackEmotion.DEAD # 19. Tot.

        if self.h < 15.0:
            return JackEmotion.SCREAMING_PAIN # 18. Schreiend
        if self.h < 35.0:
            return JackEmotion.AGGRESSIVE_PAIN # 17. Schmerzhaft

        high_arousal = (self.a > 45.0)
        very_high_arousal = (self.a > 75.0)

        if self.v > 50.0:
            return JackEmotion.MANIC_LAUGH if very_high_arousal else (JackEmotion.LAUGH if high_arousal else JackEmotion.GRIN)
        elif self.v > 15.0:
            return JackEmotion.COOL if high_arousal else JackEmotion.FRIENDLY
        elif self.v >= -15.0:
            if very_high_arousal:
                return JackEmotion.SURPRISED
            elif high_arousal:
                return JackEmotion.QUESTIONING
            elif self.v < -5.0:
                return JackEmotion.THINKING
            else:
                return JackEmotion.NEUTRAL # 6. Neutraler Blick
        elif self.v >= -50.0:
            return JackEmotion.FRUSTRATED if very_high_arousal else (JackEmotion.GRUMPY if high_arousal else JackEmotion.EVALUATING)
        else:
            return JackEmotion.FURIOUS if very_high_arousal else (JackEmotion.ANGRY if high_arousal else JackEmotion.BAD_MOOD)
