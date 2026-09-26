import os
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Token Map für KI-optimiertes High-Speed Logging
EVENT_TOKENS = {
    "SESSION_START": "S",
    "INPUT_CLICK": "M",
    "INPUT_KEY": "K",
    "PATH_STARTED": "P",
    "CIVILIAN_ENCOUNTER": "C",
    "EQUIPMENT_MOUNT": "EQ_M",
    "EQUIPMENT_UNMOUNT": "EQ_U",
    "ALERT_TRIGGERED": "A",
    "PLAYER_CAUGHT": "PC",
    "GAME_OVER": "G",
    "AUDIO_SFX": "SFX",
    "JACK_THOUGHT": "J"  # Jacks Selbst-Wahrnehmung!
}

class PerceptionLogger:
    """
    KI-optimierter, hochkompakter Wahrnehmungs-Logger.
    Speichert Events als tokenisierte JSON-Lines in `logs/perception/`.
    Niemals überschreibend, erfasst auch Jacks eigene Gedanken (Selbstwahrnehmung).
    """
    _instance: Optional['PerceptionLogger'] = None

    def __init__(self) -> None:
        self.session_id: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time: float = time.time()
        
        self.log_dir: str = os.path.join("logs", "perception")
        if not os.path.isabs(self.log_dir):
            self.log_dir = os.path.abspath(self.log_dir)
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.log_file_path: str = os.path.join(self.log_dir, f"perception_session_{self.session_id}.jsonl")
        self.session_log_path: str = os.path.join(self.log_dir, f"session_{self.session_id}.log")
        
        # Parallel zentrales session.log im logs Verzeichnis
        logs_root = os.path.dirname(self.log_dir)
        self.main_session_log: str = os.path.join(logs_root, "session.log")
        
        self.current_session_thoughts: list[str] = []
        self.last_event_signature: Optional[str] = None
        self.event_counter: int = 0
        
        self.log_event("SESSION_START", {
            "sid": self.session_id,
            "sys_t": datetime.now().isoformat()
        })

    @classmethod
    def get_instance(cls) -> 'PerceptionLogger':
        if cls._instance is None:
            cls._instance = PerceptionLogger()
        return cls._instance

    def log_event(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Protokolliert ein Ereignis sowohl im JSONL-Perception-Log als auch im lesbaren session.log.
        Verhindert mehrfache identische Aufrufe hintereinander (Anti-Duplicate).
        """
        token = EVENT_TOKENS.get(event_type, event_type)
        data_payload = data or {}
        
        # Duplikat-Filter: Ignoriere exakt identische Nachrichten unmittelbar in Folge
        signature = f"{token}:{json.dumps(data_payload, sort_keys=True)}"
        if signature == getattr(self, 'last_event_signature', None):
            return
        self.last_event_signature = signature
        self.event_counter = getattr(self, 'event_counter', 0) + 1

        session_elapsed = round(time.time() - self.start_time, 3)
        
        entry = {
            "t": session_elapsed,
            "e": token,
            "d": data_payload
        }
        
        # 1. JSONL Perception Log
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[PerceptionLogger Error] Failed to write perception log: {e}")

        # 2. Parallel lesbares session.log
        ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        if token in ("J", "JACK_THOUGHT"):
            log_line = f"[{ts_str}] [JACK] {data_payload.get('txt', '')}\n"
        else:
            log_line = f"[{ts_str}] [{token}] {json.dumps(data_payload, ensure_ascii=False)}\n"

        for path in (self.session_log_path, self.main_session_log):
            try:
                with open(path, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception as e:
                print(f"[PerceptionLogger Error] Failed to write session log: {e}")

    def clear_session_log(self) -> None:
        """Löscht/Zurücksetzt das aktuelle Session-Gedanken-Log (z. B. bei Tod / Neustart)."""
        self.current_session_thoughts = []
        self.log_event("SESSION_RESET", {"msg": "--- NEW LIFE STARTED ---"})

    def get_session_thought_logs(self) -> list[str]:
        """Gibt die Gedanken des aktuellen Lebens (Session) zurück."""
        if not hasattr(self, 'current_session_thoughts'):
            self.current_session_thoughts = []
        return list(self.current_session_thoughts)

    def is_thought_logged(self, thought_text: str) -> bool:
        """Prüft, ob ein Gedanke unmittelbar zuletzt gesprochen wurde (Anti-Repeat)."""
        session_thoughts = self.get_session_thought_logs()
        return bool(session_thoughts and session_thoughts[-1] == thought_text)

    def log_jack_thought(self, thought_text: str, situation_key: str) -> bool:
        """Protokolliert Jacks Gedanken im persistenten Perception-Log sowie im aktuellen Session-Log."""
        if not hasattr(self, 'current_session_thoughts'):
            self.current_session_thoughts = []

        # Anti-Duplikat für aufeinanderfolgende identische Gedanken im selben Leben
        if self.current_session_thoughts and self.current_session_thoughts[-1] == thought_text:
            return False

        self.current_session_thoughts.append(thought_text)

        self.log_event("JACK_THOUGHT", {
            "txt": thought_text,
            "sit": situation_key
        })
        return True

    def get_latest_events(self, limit: int = 50) -> list[Dict[str, Any]]:
        """Liest die jüngsten tokenisierten Einträge für In-Game Analysen / EE."""
        events = []
        if not os.path.exists(self.log_file_path):
            return events
            
        try:
            with open(self.log_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    line = line.strip()
                    if line:
                        events.append(json.loads(line))
        except Exception as e:
            print(f"[PerceptionLogger Error] Failed to read log: {e}")
            
        return events

    def get_all_past_thought_logs(self) -> list[str]:
        """
        Liest alle vergangenen Gedanken aus ALLEN Perception-Logs (.jsonl)
        sowie aus der SQLite-Historie, damit Jacks Gedanken über den Tod und Neustart
        hinaus zu 100% erhalten bleiben.
        """
        thoughts: list[str] = []
        search_dirs = [
            self.log_dir,
            os.path.join(self.log_dir, "evaluated")
        ]

        file_paths = []
        for d in search_dirs:
            if os.path.exists(d):
                for f in os.listdir(d):
                    if f.endswith(".jsonl"):
                        file_paths.append(os.path.join(d, f))

        file_paths.sort()

        for fp in file_paths:
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                            if entry.get("e") in ("J", "JACK_THOUGHT"):
                                data = entry.get("d", {})
                                txt = data.get("txt")
                                if txt and (not thoughts or thoughts[-1] != txt):
                                    thoughts.append(txt)
                        except Exception:
                            pass
            except Exception as e:
                print(f"[PerceptionLogger Error] Failed to read {fp}: {e}")

        # SQLite Historie abfragen
        try:
            from src.core.jack_database import JackDatabase
            db_thoughts = JackDatabase().get_speech_history()
            for t in db_thoughts:
                if t and (not thoughts or thoughts[-1] != t):
                    thoughts.append(t)
        except Exception:
            pass

        return thoughts

# Singleton Instanz
perception_logger = PerceptionLogger.get_instance()
