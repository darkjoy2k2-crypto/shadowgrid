import os
import pygame
from typing import Dict, Any, List, Optional, Tuple

class Spell:
    """Repräsentiert ein Netrunner-Script / Spell im Cyberdeck Combat Minigame."""
    def __init__(
        self,
        spell_id: str,
        name: str,
        filename: str,
        description: str,
        is_counterspell: bool = False,
        icon_key: str = "",
        jack_cinematic_line: str = "",
        civ_cinematic_line: str = ""
    ):
        self.spell_id = spell_id
        self.name = name
        self.filename = filename # z.B. "sync.py"
        self.description = description
        self.is_counterspell = is_counterspell
        self.icon_key = icon_key or spell_id
        self.jack_cinematic_line = jack_cinematic_line
        self.civ_cinematic_line = civ_cinematic_line

class SpellRegistry:
    """Verwaltet alle 16 Spells & Counterspells des Netrunner Combat Protocols."""
    def __init__(self) -> None:
        self.spells: Dict[str, Spell] = {}
        self._register_default_spells()

    def _register_default_spells(self) -> None:
        defaults = [
            Spell(
                spell_id="sync",
                name="SYNC",
                filename="sync.py",
                description="Richtet alle Keile so aus, dass Jack einen idealen Spielzug erhält.",
                is_counterspell=False,
                icon_key="sync",
                jack_cinematic_line="[SYNC.PY] SYNAPSERN-TAKTRATE RIGID OPTIMIERT!",
                civ_cinematic_line="\"Was ist das für eine Taktrate?! Meine Puffer kollabieren!\""
            ),
            Spell(
                spell_id="desync",
                name="DESYNC",
                filename="desync.py",
                description="Gegenspell: Mischt die Keile so um, dass Jack die schlechtmöglichste Ausgangslage hat.",
                is_counterspell=True,
                icon_key="desync",
                jack_cinematic_line="VERDAMMT! Mein Taktgeber de-synchronisiert!",
                civ_cinematic_line="\"DE-SYNCHRONISATION! DEINE TAKTFREQUENZ GEHÖRT MIR!\""
            ),
            Spell(
                spell_id="boost",
                name="BOOST",
                filename="boost.py",
                description="Setzt alle Schwächen des Gegners auf Tier 4 und alle Vorteile auf Tier 1.",
                is_counterspell=False,
                icon_key="boost",
                jack_cinematic_line="[BOOST.PY] LEISTUNGS-DOPLER VOLL AUSGEFAHREN!",
                civ_cinematic_line="\"Warnung: Massiver Angriffsimpuls auf verletzliche System-Knoten!\""
            ),
            Spell(
                spell_id="nerf",
                name="NERF",
                filename="nerf.py",
                description="Gegenspell: Setzt alle Schwächen des Gegners auf Tier 1 und Vorteile auf Tier 4.",
                is_counterspell=True,
                icon_key="nerf",
                jack_cinematic_line="SCHOCK! Meine Angriffspfade wurden gedrosselt!",
                civ_cinematic_line="\"SYSTEM NERF! DEINE WAPEN-EFFEKTIVITÄT WURDE HALBIERT!\""
            ),
            Spell(
                spell_id="blinded",
                name="BLINDED",
                filename="blinded.py",
                description="Gegenspell: Profilbilder des Gegners verdecken für 1 Runde alle Tier-Zahlen.",
                is_counterspell=True,
                icon_key="blinded",
                jack_cinematic_line="SCHEISSE! Optische Implantate komplett überblendet!",
                civ_cinematic_line="\"VISUELLE BLOCKADE! SCHAU IN MEIN GESICHT UND ERBLINDE!\""
            ),
            Spell(
                spell_id="dizzy",
                name="DIZZY",
                filename="dizzy.py",
                description="Gegenspell: Override sinkt schneller, Mausbewegung wird alle 2s invertiert & Tasten vertauscht.",
                is_counterspell=True,
                icon_key="dizzy",
                jack_cinematic_line="ARGH! Mein Gleichgewichtssinn kollabiert im Subnetz!",
                civ_cinematic_line="\"DIZZY DAEMON! DEINE SENSORIK LÄUFT NUN RÜCKWÄRTS!\""
            ),
            Spell(
                spell_id="reduce_damage",
                name="REDUCE DAMAGE",
                filename="reduce_damage.py",
                description="Gegenspell: Senkt den System-Override sofort um 25% (mindestens 5% bleiben).",
                is_counterspell=True,
                icon_key="reduce_damage",
                jack_cinematic_line="WARNUNG! Übernahme-Fortschritt wurde massiv zurückgeschlagen!",
                civ_cinematic_line="\"SYSTEM REPARATUR! HACKER-EINFLUSS UM 25% REDUZIERT!\""
            ),
            Spell(
                spell_id="apply_damage",
                name="ALLY DAMAGE",
                filename="ally_damage.py",
                description="Erhöht den System-Override sofort um 25% (maximal bis 95%).",
                is_counterspell=False,
                icon_key="apply_damage",
                jack_cinematic_line="[ALLY_DAMAGE.PY] MASSIVER SUB-NET OVERRIDE IMPULS!",
                civ_cinematic_line="\"Kritischer Einbruch! 25% der Systemkontrolle verloren!\""
            ),
            Spell(
                spell_id="firewall_breach",
                name="FIREWALL BREACH",
                filename="firewall_breach.py",
                description="Deckt sofort alle 4 System-Affinitäten des Gegners vollständig auf.",
                is_counterspell=False,
                icon_key="firewall_breach",
                jack_cinematic_line="[FIREWALL_BREACH.PY] VOLLE SYSTEM-OFFENLEGUNG!",
                civ_cinematic_line="\"ALARM! Alle System-Widerstände wurden gecrackt!\""
            ),
            Spell(
                spell_id="system_hack",
                name="SYSTEM HACK",
                filename="system_hack.py",
                description="Gegenspell: Deckt alle Affinitäten zu und mischt sie für diese Partie neu.",
                is_counterspell=True,
                icon_key="system_hack",
                jack_cinematic_line="MIST! Gegner hat die Resistenzen getarnt und neu gewürfelt!",
                civ_cinematic_line="\"SYSTEM HACK COUNTER! ALLE PROFILE NEU VERSCHLÜSSELT!\""
            ),
            Spell(
                spell_id="data_corrupt",
                name="DATA CORRUPT",
                filename="data_corrupt.py",
                description="Gegenspell: Ersetzt alle UI-Texte & Zahlen für 1 Runde durch Kryptik-Sanskrit.",
                is_counterspell=True,
                icon_key="data_corrupt",
                jack_cinematic_line="VERFLUCHT! Sämtliche System-Glyphen sind korrumpiert!",
                civ_cinematic_line="\"DATA CORRUPT! LIES DEINE EIGENEN CODES WENN DU KANNST!\""
            ),
            Spell(
                spell_id="malware_injection",
                name="MALWARE INJECTION",
                filename="malware_injection.py",
                description="Gegenspell: Schnellerer Override-Abfall & störende Popups blockieren das UI.",
                is_counterspell=True,
                icon_key="malware_injection",
                jack_cinematic_line="NOTFALL! Störende Malware-Popups überfluten meinen Schirm!",
                civ_cinematic_line="\"MALWARE INJEKTION! GENIESSE DIE TROJANER-FLUT!\""
            ),
            Spell(
                spell_id="cpu_overclock",
                name="CPU OVERCLOCK",
                filename="cpu_overclock.py",
                description="Verdoppelt alle Tier-Werte für 1 Runde exponentiell (1-2-4-8).",
                is_counterspell=False,
                icon_key="cpu_overclock",
                jack_cinematic_line="[CPU_OVERCLOCK.PY] FREQUENZ-VERDOPPLUNG AUF MAXIMUM!",
                civ_cinematic_line="\"Warnung: Verdoppelte Angriffs-Spannung registriert!\""
            ),
            Spell(
                spell_id="network_jam",
                name="NETWORK JAM",
                filename="network_jam.py",
                description="Gegenspell: Erzeugt heftigen Screenshake, Glitches & Flackern bis Rundenende.",
                is_counterspell=True,
                icon_key="network_jam",
                jack_cinematic_line="KOPFSCHMERZEN! Das ganze Subnetz flackert und erzittert!",
                civ_cinematic_line="\"NETWORK JAMMER! DEIN ANZEIGE-TERMINAL COLLAPSED!\""
            ),
            Spell(
                spell_id="signal_hijack",
                name="SIGNAL HIJACK",
                filename="signal_hijack.py",
                description="Gegenspell: Gegner übernimmt Jack's Maus für 1 Zug und klickt sein bestes Feld.",
                is_counterspell=True,
                icon_key="signal_hijack",
                jack_cinematic_line="MEINE HAND! Der Gegner steuert meinen Zeiger!",
                civ_cinematic_line="\"SIGNAL HIJACK! DIESEN SPIELZUG MACHE ICH FÜR DICH!\""
            ),
            Spell(
                spell_id="biohacker",
                name="BIOHACKER",
                filename="biohacker.py",
                description="Blinkt wenn Tier 4 auf WEAK ausgelöst wurde. Aktivieren = SOFORTIGER SIEG! Ohne Bereitschaft = SOFORTIGE NIEDERLAGE!",
                is_counterspell=False,
                icon_key="biohacker",
                jack_cinematic_line="[BIOHACKER.PY] ULTRA-CHIP INJEKTION VORBEREITET!",
                civ_cinematic_line="\"Bio-Hack Sequenz abgefangen... Bist du bereit für das Risiko?!\""
            )
        ]
        for sp in defaults:
            self.spells[sp.spell_id] = sp

    def get_spell(self, spell_id: str) -> Optional[Spell]:
        return self.spells.get(spell_id)

    def get_spell_by_filename(self, filename: str) -> Optional[Spell]:
        fn = filename.lower()
        for sp in self.spells.values():
            if sp.filename.lower() == fn:
                return sp
        return None

    def get_all_spells(self) -> List[Spell]:
        return list(self.spells.values())

spell_registry = SpellRegistry()
