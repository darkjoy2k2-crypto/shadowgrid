import os
import sqlite3
import random
from typing import Dict, List, Any, Optional, Tuple

class JackDatabase:
    """
    Strukturierte SQLite-Datenbank für Jacks Erfahrungsspeicher, Phrase-Arsenale,
    Situations-Impulse und Selbst-Wahrnehmung (Anti-Repetitions-Historie).
    """
    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_path = os.path.join("src", "data", "jack_memory.db")
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(db_path)
            
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()
        self._seed_default_arsenals()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Table: Situations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS situations (
                    situation_key TEXT PRIMARY KEY,
                    dv REAL DEFAULT 0.0,
                    da REAL DEFAULT 0.0,
                    dh REAL DEFAULT 0.0,
                    portrait_base INT DEFAULT 6
                )
            """)
            
            # Table: Phrases (mit Frequency Tiering: 'RARE', 'FREQUENT', 'META_REPEAT')
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS phrases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    situation_key TEXT,
                    phrase TEXT NOT NULL,
                    tier TEXT DEFAULT 'FREQUENT',
                    use_count INT DEFAULT 0,
                    FOREIGN KEY(situation_key) REFERENCES situations(situation_key)
                )
            """)
            
            # Table: History (Jacks Selbstwahrnehmungs-Protokoll gesprochener Gedankentexte)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jack_speech_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    situation_key TEXT,
                    phrase TEXT NOT NULL
                )
            """)
            conn.commit()

    def _seed_default_arsenals(self) -> None:
        """Befüllt die DB mit strukturierten Phrasen-Arsenalen in Ich-Perspektive inkl. Gameplay-Tipps."""
        situations_data = [
            ("SESSION_START", 0.0, -10.0, 0.0, 6),
            ("EXPLORATION_SHORT", 2.0, 5.0, 0.0, 6),
            ("LONG_WALK", -15.0, 15.0, 0.0, 9),
            ("DIRECTION_CHANGE", -10.0, 20.0, 0.0, 10),
            ("CIVILIAN_ENCOUNTER", 10.0, 30.0, 0.0, 7),
            ("UI_INTERACTION", 5.0, 10.0, 0.0, 5),
            ("EQUIPMENT_MOUNT", 15.0, 15.0, 0.0, 11),
            ("EQUIPMENT_UNMOUNT", -15.0, 10.0, 0.0, 16),
            ("ALERT_TRIGGERED", -40.0, 70.0, 0.0, 15),
            ("PLAYER_CAUGHT", -60.0, 90.0, -20.0, 17),
            ("GAME_OVER", -100.0, 100.0, -100.0, 19),
            ("META_REPEAT", -5.0, 15.0, 0.0, 10),
            ("TRUMAN_FREAKOUT", -80.0, 90.0, 0.0, 18),
            ("SENTINEL_NEAR", -30.0, 60.0, 0.0, 14),
            ("IOT_AWARENESS", -20.0, 45.0, 0.0, 12),
            ("SCANNER_INTERCEPT", -35.0, 75.0, 0.0, 16),
            ("CAMERA_SPOTTED", -25.0, 55.0, 0.0, 13),
            ("SENTINEL_DISPATCHED", -40.0, 80.0, 0.0, 15),
            ("SENTINEL_EMPTIED_IOT", -20.0, 50.0, 0.0, 14),
            ("SENTINEL_BRIBE", 20.0, -20.0, 0.0, 11),
            ("BRIBE_FAILED", -50.0, 80.0, 0.0, 15),
            ("SENTINEL_EXCUSE_PASS", 15.0, -10.0, 0.0, 11),
            ("SENTINEL_EXCUSE_FAIL", -45.0, 85.0, 0.0, 15)
        ]
        
        phrases_data = {
            "SESSION_START": [
                ("Ich hab mich wieder im Shadowgrid eingeklinkt... Mein Deck läuft, aber der Grid ist gefährlich. Tipp: Mit 'disp.drv' sehe ich das Nebel-Raster!", "RARE"),
                ("Eingeklinkt im Grid! Wachen fangen mich erst ab Nervosität 50% ab. Ich sollte 50 Credits für Schmiergeld aufsparen.", "FREQUENT"),
                ("Ich stehe auf der Datentrasse. Zivilisten muss ich erst vollhacken (100% Progressbar), bevor der Dialog aufpoppt.", "FREQUENT"),
                ("Mein Cyberdeck ist online. Ich behalte mein Threat-Meter im Auge – bei 100% schlagen Sentinels direkt zu!", "FREQUENT")
            ],
            "SENTINEL_NEAR": [
                ("Schweres Wummern... Ein Sentinel nahebei! Sie sprechen mich ab 50-99% Nervosität an – ich halte 50 Credits Schmiergeld bereit!", "RARE"),
                ("Verdammt, der Sentinel kreist um mich! Ich kann versuchen ihn mit 50 Credits zu schmieren oder mit 'ner Ausrede zu blöffen.", "FREQUENT"),
                ("Wache in Reichweite! Bei 100% Threat greift er direkt an. Ohne Credits gibt's Saures, wenn er mich stellt!", "FREQUENT"),
                ("Die Sentinels patrouillieren. Ich sollte Abstand halten und Sichtkegel meiden.", "FREQUENT")
            ],
            "CAMERA_SPOTTED": [
                ("Verflucht, eine Kamera hat mich erfasst! Mein Threat-Meter steigt! Tipp: Mit 'ucam.drv' werden Kamerasichtkegel rot markiert.", "RARE"),
                ("Scheiße, Kamerasensor aktiviert! Raus aus dem Sichtkegel, sonst schlägt das Sicherheitssystem Alarm!", "FREQUENT")
            ],
            "SENTINEL_DISPATCHED": [
                ("Achtung! Eine Wache wurde zu meiner letzten bekannten Position geschickt! Ich muss sofort den Standort wechseln!", "RARE"),
                ("Der Sentinel untersucht die Alarmstelle. Ich darf hier nicht stehenbleiben!", "FREQUENT")
            ],
            "SENTINEL_EMPTIED_IOT": [
                ("Der Sentinel hat Kameradaten aus dem IoT-Node ausgelesen... Er kennt jetzt meine Frequenz!", "FREQUENT")
            ],
            "IOT_AWARENESS": [
                ("IoT-Überwachung im Sektor... Kameras und Mikrofone scannen die Trassen. Sichtkegel strikt meiden!", "RARE"),
                ("Überwachungskameras an den Wänden... Ein unbedachter Schritt treibt mein Bedrohungs-Level nach oben.", "FREQUENT")
            ],
            "SCANNER_INTERCEPT": [
                ("Verdammt! Ein Scanner-Node hat meine automatische Wegfindung blockiert! Ich muss über den Klick-Pfad ausweichen.", "RARE"),
                ("Scanner-Sperre! Der IoT-Node überprüft meine Pakete. Schneller Richtungswechsel über die Karte!", "FREQUENT")
            ],
            "EXPLORATION_SHORT": [
                ("Ich taste mich vorsichtig voran. Immer ein Auge auf die IoT-Kameras und Sentinel-Wachen halten.", "RARE"),
                ("Kurzer Blick um die Ecke...", "FREQUENT"),
                ("Ich rücke Schritt für Schritt vor...", "FREQUENT")
            ],
            "LONG_WALK": [
                ("Schon wieder kilometerlange Datenstränge laufen... Das treibt mein Deck-Risiko hoch!", "RARE"),
                ("Ich laufe durch das endlose Raster. Ich sollte öfter mal Pause in einer Proxy-Safezone machen.", "FREQUENT"),
                ("Meine Beine spüren zwar nichts, aber mein Deck wird heiß. Augen auf nach Wachen!", "FREQUENT"),
                ("Schritt für Schritt durch das Grid. Tipp: Zivilisten-Hacks schalten oft Nah-Shops und Quizzes frei.", "FREQUENT")
            ],
            "DIRECTION_CHANGE": [
                ("Ich ändere den Kurs. Zickzack-Laufen verwirrt zwar Verfolger, aber kostet auch Zeit.", "RARE"),
                ("Hektischer Richtungswechsel... Ich halte Ausschau nach unbewachten Trassen.", "FREQUENT")
            ],
            "CIVILIAN_ENCOUNTER": [
                ("Ein ziviler Node nahebei! Erst vollhacken (100%), dann öffnet sich der Dialog. Manche schenken Credits oder Quizzes!", "RARE"),
                ("Subroutine gesichtet! Beim Hacken vorsichtig sein: Zivilisten können auch Wachen rufen oder mich abziehen!", "FREQUENT"),
                ("Ich näher mich der zivilen Subroutine... Hoffentlich hat er lohnenswerten Loot geladen.", "FREQUENT")
            ],
            "UI_INTERACTION": [
                ("Ich werfe einen Blick in mein Systemfenster... Treiber und Daten prüfen.", "RARE"),
                ("Ich durchwühle mein Cyberdeck-Inventar. Welches Tool brauchen wir?", "FREQUENT")
            ],
            "EQUIPMENT_MOUNT": [
                ("Ich habe den Treiber montiert! Das erweitert meine Sicht und Systemübersicht im Grid.", "RARE"),
                ("Neuer Treiber aktiv. Mit 'disp.drv' sehe ich Nebel & PCB-Linien, mit 'ucam.drv' Kameras!", "FREQUENT")
            ],
            "EQUIPMENT_UNMOUNT": [
                ("Ich habe den Treiber wieder ausgeworfen. Ohne aktive Treiber fahre ich im Blindflug!", "RARE")
            ],
            "ALERT_TRIGGERED": [
                ("ALARM STUFE ROT! Mein Threat-Meter ist auf 100%! Die Sentinels hetzen mir nach – schnell weg!", "RARE"),
                ("Sicherheitssysteme schlagen an! Ich muss sofort in Deckung oder die Proxy-Zone erreichen!", "FREQUENT")
            ],
            "PLAYER_CAUGHT": [
                ("VERDAMMT! Ein Guardian hat mich gepackt! Der IC-Zugriff brennt sich durch meine Abschirmung!", "RARE")
            ],
            "GAME_OVER": [
                ("FLATLINE... Mein Cyberdeck ist komplett abgestürzt. System-Neustart erforderlich...", "RARE")
            ],
            "SENTINEL_BRIBE": [
                ("Ich drücke der Wache 50 Credits in die Hand. Sein Blick wird weich – Schmiergeld-Erfolg, er lässt mich in Ruhe!", "RARE")
            ],
            "BRIBE_FAILED": [
                ("Verdammt! Ich habe keine 50 Credits zum Schmieren! Die Wache schäumt vor Wut!", "RARE")
            ],
            "SENTINEL_EXCUSE_PASS": [
                ("Mein gefälschter Ausweis hat gesessen! Der Sentinel kauft die Story und lässt mich passieren.", "RARE")
            ],
            "SENTINEL_EXCUSE_FAIL": [
                ("Mist! Der Sentinel hat meine gefälschte Lizenz durchschaut – sofort Alarm!", "RARE")
            ],
            "META_REPEAT": [
                ("Warte mal... Das habe ich doch gerade erst gedacht!", "FREQUENT"),
                ("Ich merke selbst, wie ich mich wiederhole. Ich schalt mal lieber kurz einen Gang zurück.", "FREQUENT")
            ],
            "TRUMAN_FREAKOUT": [
                ("WAS IST DAS?! DAS SIND MEINE GEDANKEN... AUS EINEM FRÜHEREN LEBEN?! WER ZEICHNET DAS AUF?! WER SEID IHR?!", "RARE"),
                ("Warte... diese Log-Einträge... Das hab ich vor meinem letzten Flatline gedacht?! WIE KANN DAS SEIN?!", "FREQUENT"),
                ("DAS IST KEIN REALES CYBERDECK! DAS IST EIN SIMULIERTES GEFÄNGNIS! MEIN GANZER VERSTAND WIRD GELOGGT!", "FREQUENT")
            ]
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM phrases")
            cursor.execute("DELETE FROM situations")
            
            for sit in situations_data:
                cursor.execute(
                    "INSERT OR REPLACE INTO situations (situation_key, dv, da, dh, portrait_base) VALUES (?, ?, ?, ?, ?)",
                    sit
                )
            for sit_key, p_list in phrases_data.items():
                for phrase, tier in p_list:
                    cursor.execute(
                        "INSERT INTO phrases (situation_key, phrase, tier) VALUES (?, ?, ?)",
                        (sit_key, phrase, tier)
                    )
            conn.commit()

    def get_situation(self, situation_key: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM situations WHERE situation_key = ?", (situation_key,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def select_phrase(self, situation_key: str, occurrence_count: int = 1) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Wählt intelligent eine Phrase aus dem Arsenal:
        - Einmaliges Event (occurrence_count <= 2): Nutzt seltene/kurze Phrasen (Tier 'RARE').
        - Häufiges / Repetitives Event (occurrence_count > 2): Greift auf das volle Arsenal zu!
        - Verhindert Wiederholungen: Wenn alle Phrasen einer gewöhnlichen Situation kürzlich verwendet wurden,
          wird None zurückgegeben, um Spam zu verhindern.
        """
        sit = self.get_situation(situation_key) or {"dv": 0.0, "da": 0.0, "dh": 0.0, "portrait_base": 6}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Historie der letzten 15 Phrasen abrufen
            cursor.execute("SELECT phrase FROM jack_speech_history ORDER BY id DESC LIMIT 15")
            recent_history = set(row["phrase"] for row in cursor.fetchall())

            # Phrasen nach Tier filtern
            tier_filter = "RARE" if occurrence_count <= 2 else "FREQUENT"
            cursor.execute(
                "SELECT phrase, tier, use_count FROM phrases WHERE situation_key = ? AND tier = ?",
                (situation_key, tier_filter)
            )
            rows = cursor.fetchall()
            
            if not rows:
                cursor.execute("SELECT phrase, tier, use_count FROM phrases WHERE situation_key = ?", (situation_key,))
                rows = cursor.fetchall()

            if not rows:
                return None, sit

            # Gefilterter Vorrat ohne bereits gesprochene Phrasen
            candidates = [dict(r) for r in rows if r["phrase"] not in recent_history]

            if not candidates:
                if situation_key in ("TRUMAN_FREAKOUT", "GAME_OVER", "ALERT_TRIGGERED", "PLAYER_CAUGHT"):
                    candidates = [dict(r) for r in rows]
                elif situation_key != "META_REPEAT":
                    cursor.execute("SELECT phrase FROM jack_speech_history WHERE situation_key = 'META_REPEAT' ORDER BY id DESC LIMIT 5")
                    if not cursor.fetchall():
                        return self.select_phrase("META_REPEAT", occurrence_count=1)
                    candidates = [dict(r) for r in rows]
                else:
                    candidates = [dict(r) for r in rows]

            chosen = random.choice(candidates)
            phrase_text = chosen["phrase"]

            # Use count erhöhen & Historie eintragen
            cursor.execute("UPDATE phrases SET use_count = use_count + 1 WHERE situation_key = ? AND phrase = ?", (situation_key, phrase_text))
            cursor.execute("INSERT INTO jack_speech_history (timestamp, situation_key, phrase) VALUES (?, ?, ?)", (0.0, situation_key, phrase_text))
            conn.commit()

            return phrase_text, sit

    def get_speech_history(self) -> List[str]:
        """Gibt alle gesprochenen Phrasen in chronologischer Reihenfolge zurück."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT phrase FROM jack_speech_history ORDER BY id ASC")
            return [row["phrase"] for row in cursor.fetchall()]
