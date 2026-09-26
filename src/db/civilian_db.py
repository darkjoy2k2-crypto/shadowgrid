import os
import sqlite3
import random
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional

class CivilianDatabase:
    """
    SQLite-basierte Datenbank für zivile Persönlichkeiten, Jobs, Biografien,
    Jack-Kommentare und Profil-Metadaten. Synchronisiert mit XML-Profilen.
    """
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "civilians.db")
            
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Erstellt die Tabelle `civilians`, falls sie noch nicht existiert, und lädt XML-Profile."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS civilians (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    gender TEXT,
                    age_group TEXT,
                    origin TEXT,
                    job TEXT DEFAULT 'Data Courier',
                    profile_pic TEXT,
                    story TEXT,
                    comment_jack TEXT,
                    personality_traits TEXT
                )
            """)
            
            # Prüfen ob Spalten existieren (für bestehende DBs)
            cursor.execute("PRAGMA table_info(civilians)")
            existing_cols = {row["name"] for row in cursor.fetchall()}
            needed_cols = {
                "gender": "TEXT",
                "age_group": "TEXT",
                "origin": "TEXT",
                "job": "TEXT DEFAULT 'Data Courier'",
                "profile_pic": "TEXT",
                "story": "TEXT",
                "comment_jack": "TEXT",
                "personality_traits": "TEXT",
                "category": "TEXT DEFAULT 'STANDARD'",
                "dialogue_json": "TEXT"
            }
            for col, col_def in needed_cols.items():
                if col not in existing_cols:
                    cursor.execute(f"ALTER TABLE civilians ADD COLUMN {col} {col_def}")
        # XML profiles synchronisieren (nur wenn DB leer ist oder Update erzwungen wird)
        if self.get_count() == 0:
            self._load_xml_profiles()

    def _load_xml_profiles(self, force: bool = False) -> None:
        """Scannt das `src/data/profiles` Verzeichnis und lädt alle XML-Profil-Dateien in die Datenbank."""
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        profiles_dir = os.path.join(src_dir, "data", "profiles")
        if not os.path.exists(profiles_dir):
            profiles_dir = os.path.abspath(os.path.join(os.getcwd(), "data", "profiles"))
            if not os.path.exists(profiles_dir):
                return

        xml_files = [f for f in os.listdir(profiles_dir) if f.endswith(".xml")]
        if not xml_files:
            return

        import json
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for fname in xml_files:
                fpath = os.path.join(profiles_dir, fname)
                try:
                    tree = ET.parse(fpath)
                    root = tree.getroot()
                    
                    name = root.findtext("name", "Unknown")
                    category = root.findtext("category", "STANDARD")
                    gender = root.findtext("gender", "Unknown")
                    age_group = root.findtext("age_group", "Unknown")
                    origin = root.findtext("origin", "Unknown")
                    job = root.findtext("job", "Data Courier")
                    image_path = root.findtext("image_path", "src/gfx/faces/default.png")
                    story = root.findtext("story", "")
                    comment_jack = root.findtext("comment_jack", "")
                    personality_traits = root.findtext("personality_traits", "")

                    # XML <dialogue> Struktur parsen
                    dialogue_tree = {}
                    dialogue_elem = root.find("dialogue")
                    if dialogue_elem is not None:
                        for node in dialogue_elem.findall("node"):
                            node_id = node.get("id", "start")
                            speaker = node.findtext("speaker", "CIVILIAN")
                            jack_emotion = int(node.findtext("jack_emotion", "6"))
                            text = node.findtext("text", "")
                            choices = []
                            choices_elem = node.find("choices")
                            if choices_elem is not None:
                                for choice in choices_elem.findall("choice"):
                                    c_text = choice.findtext("text", "")
                                    c_next = choice.findtext("next_node", "") or None
                                    c_act = choice.findtext("action", "") or None
                                    choices.append({
                                        "text": c_text,
                                        "next_node": c_next,
                                        "action": c_act
                                    })
                            dialogue_tree[node_id] = {
                                "speaker": speaker,
                                "jack_emotion": jack_emotion,
                                "text": text,
                                "choices": choices
                            }
                    dialogue_json = json.dumps(dialogue_tree) if dialogue_tree else None

                    cursor.execute("""
                        INSERT INTO civilians (name, category, gender, age_group, origin, job, profile_pic, story, comment_jack, personality_traits, dialogue_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(name) DO UPDATE SET
                            category=excluded.category,
                            gender=excluded.gender,
                            age_group=excluded.age_group,
                            origin=excluded.origin,
                            job=excluded.job,
                            profile_pic=excluded.profile_pic,
                            story=excluded.story,
                            comment_jack=excluded.comment_jack,
                            personality_traits=excluded.personality_traits,
                            dialogue_json=excluded.dialogue_json
                    """, (name, category, gender, age_group, origin, job, image_path, story, comment_jack, personality_traits, dialogue_json))
                except Exception as e:
                    print(f"[CivilianDatabase] Error parsing {fname}: {e}")
            conn.commit()

    def get_count(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM civilians")
            return cursor.fetchone()[0]

    def get_random_profile(self) -> Dict[str, Any]:
        import json
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM civilians WHERE name NOT IN ('Maya Cross', 'Viktor Reyes', 'Sora Takeda', 'Jack') ORDER BY RANDOM() LIMIT 1")
            row = cursor.fetchone()
            if row:
                res = dict(row)
                res["image_path"] = res.get("profile_pic", "")
                if res.get("dialogue_json"):
                    try:
                        res["dialogue_tree"] = json.loads(res["dialogue_json"])
                    except Exception:
                        res["dialogue_tree"] = None
                return res
            return {
                "id": 1,
                "name": "Unknown Civ Node",
                "gender": "Unknown",
                "age_group": "Unknown",
                "origin": "Unknown",
                "job": "Data Courier",
                "profile_pic": "gfx/civilians/default.png",
                "image_path": "gfx/civilians/default.png",
                "story": "Unindexed civil traffic node.",
                "comment_jack": "JACK // UNINDEXED NODE. LOW THREAT VALUE.",
                "personality_traits": "Unknown"
            }

    def get_profile_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        import json
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM civilians WHERE name LIKE ?", (f"%{name}%",))
            row = cursor.fetchone()
            if row:
                res = dict(row)
                res["image_path"] = res.get("profile_pic", "")
                if res.get("dialogue_json"):
                    try:
                        res["dialogue_tree"] = json.loads(res["dialogue_json"])
                    except Exception:
                        res["dialogue_tree"] = None
                return res
            return None

    def update_comment_jack(self, civ_id: int, new_comment: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE civilians SET comment_jack = ? WHERE id = ?", (new_comment, civ_id))
            conn.commit()

civilian_db = CivilianDatabase()

