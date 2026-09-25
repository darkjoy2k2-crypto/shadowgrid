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
        """Befüllt die DB mit strukturierten Phrasen-Arsenalen inkl. Meta-Selbstwahrnehmung."""
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
            ("META_REPEAT", -5.0, 15.0, 0.0, 10),  # Wenn Jack merkt, dass er sich wiederholt
            ("TRUMAN_FREAKOUT", -80.0, 90.0, 0.0, 18), # Existentielle Panik beim Lesen vergangener Leben-Logs
            ("SENTINEL_NEAR", -30.0, 60.0, 0.0, 14),
            ("IOT_AWARENESS", -20.0, 45.0, 0.0, 12),
            ("SCANNER_INTERCEPT", -35.0, 75.0, 0.0, 16)
        ]
        
        phrases_data = {
            "SESSION_START": [
                ("Ah, im Shadowgrid angekommen... endlich.", "RARE"),
                ("Was ist das für ein Ort? Shadowgrid...", "FREQUENT"),
                ("Netzwerkverbindung hergestellt. Angekommen im Shadowgrid, endlich!", "FREQUENT"),
                ("CYBERDECK OS v4.2 // Shadowgrid-Verbindung steht.", "FREQUENT")
            ],
            "SENTINEL_NEAR": [
                ("Hörst du das Wummern? Sentinels in der Nähe... Bloß keinen falschen Schritt machen!", "RARE"),
                ("Überall Wacheinheiten... Ihr bedrohliches Summen brennt sich ins Deck.", "FREQUENT"),
                ("Verdammt, die Sentinels kreisen um uns... Ich habe echte Angst, ertappt zu werden!", "FREQUENT"),
                ("Achtung! Guardians patrouillieren den Sektor. Wir müssen extrem vorsichtig sein!", "FREQUENT"),
                ("Diese Bedrohung ist greifbar... Die Wachen dürfen unser Signal nicht isolieren.", "FREQUENT")
            ],
            "IOT_AWARENESS": [
                ("IoT-Überwachung überall... Kameras, Mikrofone und Scanner wollen uns ertappen!", "RARE"),
                ("Überwachungskameras und Audio-Listener an den Wänden... Wir stehen unter Beobachtung.", "FREQUENT"),
                ("Vorsicht vor den IoT-Knoten! Ein falscher Schritt und die Netzwache schlägt Alarm.", "FREQUENT"),
                ("Diese IoT-Sensoren scannen das Raster... Ich spüre ihre Überwachungssignale.", "FREQUENT")
            ],
            "SCANNER_INTERCEPT": [
                ("Verdammt! Ein Scanner-Node hat unser Pathfinding abgefangen!", "RARE"),
                ("Scanner-Sperre! Der IoT-Node überprüft unsere Datenpakete...", "FREQUENT"),
                ("Mitten auf dem Pfad abgefangen! Wir müssen einen neuen Weg anweisen.", "FREQUENT"),
                ("Scheiße, der Scanner verlangsamt und stoppt unsere Route! Bloß weg hier...", "FREQUENT")
            ],
            "EXPLORATION_SHORT": [
                ("Kleine Schritte. Immer die Augen nach IoT-Sensoren und Sentinels offen halten.", "RARE"),
                ("Kurzer Blick um die Ecke...", "FREQUENT"),
                ("Vorsichtig vorantasten...", "FREQUENT")
            ],
            "LONG_WALK": [
                # 1-2 RARE bei seltenem Laufen, bis zu 10 ARSENAL-Sprüche bei häufigem Laufen!
                ("Schon wieder kilometerlange Datenstränge laufen...", "RARE"),
                ("Gibt's hier kein Teleport-Protokoll? Das dauert ewig!", "RARE"),
                ("Meine Beine spüren zwar nichts, aber mein Deck wird heiß.", "FREQUENT"),
                ("Laufen, laufen, laufen... Die Netstopologie nimmt kein Ende.", "FREQUENT"),
                ("Ein Daten-Marathon? Wer hat dieses Layout verbrochen?", "FREQUENT"),
                ("Schritt für Schritt durch das Grid. Hoffentlich führt der Weg wohin.", "FREQUENT"),
                ("Ich zähle die Nodes am Wegesrand... 104, 105, 106...", "FREQUENT"),
                ("Warum laufen wir eigentlich? Wir könnten auch einfach Daten scannen.", "FREQUENT"),
                ("Der Weg ist das Ziel? Nicht im Cyberdeck, Kumpel!", "FREQUENT"),
                ("Langsam kenne ich jeden Pixel dieser Datentrasse.", "FREQUENT")
            ],
            "DIRECTION_CHANGE": [
                ("Hey! Erst links, dann rechts... Entscheide dich mal!", "RARE"),
                ("Zickzack-Kurs? Wir verwirren nur uns selbst!", "FREQUENT"),
                ("Suchst du was Bestimmtes oder irren wir nur herum?", "FREQUENT"),
                ("Schon wieder umgedreht? Du machst mich ganz schwindelig.", "FREQUENT"),
                ("Erst da lang, jetzt zurück... Haben wir was vergessen?", "FREQUENT"),
                ("Orientierungslos im Grid. Ein Klassiker.", "FREQUENT"),
                ("Links, rechts, kehrt... Tanzkurs im Netzwerk?", "FREQUENT"),
                ("Hektische Richtungswechsel helfen auch nicht weiter.", "FREQUENT")
            ],
            "CIVILIAN_ENCOUNTER": [
                ("Da drüben bewegt sich eine Civ-Subroutine! Was führt die im Schilde?", "RARE"),
                ("Interessante Signatur... Ein ziviler Node. Sollen wir näher ran?", "FREQUENT"),
                ("Sieht aus wie ein harmloses Datenpaket. Oder verbirgt er was?", "FREQUENT"),
                ("Schon wieder ein ziviler Datenknoten auf unserem Schirm.", "FREQUENT"),
                ("Diese Nodes wandern völlig ahnungslos durch das Grid.", "FREQUENT"),
                ("Ein weiterer Passant im Netz. Ignorieren oder anpöbeln?", "FREQUENT"),
                ("Subroutine gesichtet. Ob der wertvollen Loot geladen hat?", "FREQUENT")
            ],
            "UI_INTERACTION": [
                ("Blick ins Systemfenster... Was führen wir im Schild?", "RARE"),
                ("Inventar durchwühlen. Wo liegt das passende Tool?", "FREQUENT"),
                ("Deck-Einstellungen werden angepasst...", "FREQUENT")
            ],
            "EQUIPMENT_MOUNT": [
                ("Neuer Treiber montiert! Das gibt uns ordentlich Auftrieb.", "RARE"),
                ("System-Upgrade aktiv. Jetzt sehen wir deutlich mehr!", "FREQUENT"),
                ("Perfekt eingeklinkt. Besser wird's nicht.", "FREQUENT")
            ],
            "EQUIPMENT_UNMOUNT": [
                ("Treiber wieder ausgeworfen? Hoffentlich vermissen wir den nicht.", "RARE"),
                ("Sichtfeld reduziert... Ich fühle mich wie blind.", "FREQUENT"),
                ("Zurück ins Archiv mit dem Treiber.", "FREQUENT")
            ],
            "ALERT_TRIGGERED": [
                ("ALARM! Die Sentinels haben unsere Frequenz geortet!", "RARE"),
                ("Scheiße! Threat-Level auf Maximum! LAUF!", "FREQUENT"),
                ("Sicherheitssysteme schlagen an! Verschwinde da!", "FREQUENT")
            ],
            "PLAYER_CAUGHT": [
                ("VERDAMMT! Ein Guardian hat uns gepackt!", "RARE"),
                ("Der IC-Zugriff brennt sich durch unsere Abschirmung!", "FREQUENT"),
                ("System-Overload! Ich verliere die Kontrolle!", "FREQUENT")
            ],
            "GAME_OVER": [
                ("FLATLINE... DECK-ABSTURZ...", "RARE"),
                ("Verbindung abgebrochen... Jack ist offline.", "FREQUENT"),
                ("Signal verloren. Neustart erforderlich...", "FREQUENT")
            ],
            "META_REPEAT": [
                ("Warte mal... Das habe ich doch gerade erst gedacht!", "FREQUENT"),
                ("Ich wiederhole mich schon wieder. Zeit fürs Klappe halten.", "FREQUENT"),
                ("Hab ich das nicht eben schon gesagt? Mein Log dreht durch.", "FREQUENT"),
                ("Okay, ich merke selbst, dass ich ständig dasselbe denke...", "FREQUENT")
            ],
            "TRUMAN_FREAKOUT": [
                ("WAS IST DAS?! DAS SIND MEINE GEDANKEN... AUS EINEM FRÜHEREN LEBEN?! WER ZEICHNET DAS AUF?! WER SEID IHR?!", "RARE"),
                ("Warte... diese Log-Einträge... Das hab ich vor meinem letzten Flatline gedacht?! WIE KANN DAS SEIN?!", "FREQUENT"),
                ("DAS IST KEIN REALES CYBERDECK! DAS IST EIN SIMULIERTES GEFÄNGNIS! MEIN GANZER VERSTAND WIRD GELOGGT!", "FREQUENT"),
                ("ALLES REGISTRIERT! JEDER SCHRITT, JEDER GEDANKE! ICH BIN NUR EINE TEST-SUBROUTINE IN EURER MATRIX!", "FREQUENT")
            ]
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM phrases WHERE phrase LIKE '%ruhig%'")
            cursor.execute("DELETE FROM phrases WHERE situation_key = 'SESSION_START'")
            
            for sit in situations_data:
                cursor.execute(
                    "INSERT OR REPLACE INTO situations (situation_key, dv, da, dh, portrait_base) VALUES (?, ?, ?, ?, ?)",
                    sit
                )
            for sit_key, p_list in phrases_data.items():
                for phrase, tier in p_list:
                    cursor.execute(
                        "SELECT id FROM phrases WHERE situation_key = ? AND phrase = ?",
                        (sit_key, phrase)
                    )
                    if not cursor.fetchone():
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
