import random
from typing import Dict, Any, List, Optional

ITEM_POOL: List[Dict[str, Any]] = [
    {"id": "none", "name": "Kein Item", "type": None},
    {"id": "scrap_chip", "name": "Abgegriffener Daten-Chip", "type": "DATA_CHIP"},
    {"id": "proxy_key", "name": "Temporärer Proxy-Schlüssel", "type": "PROXY_KEY"},
    {"id": "neural_booster", "name": "Neuron-Beschleuniger (Scrap)", "type": "BOOSTER"},
]

def get_random_item() -> Optional[Dict[str, Any]]:
    """Gibt derzeit zufällig 'Kein Item' (None) oder ein Platzhalter-Item zurück."""
    if random.random() < 0.75:
        return None
    valid_items = [i for i in ITEM_POOL if i["type"] is not None]
    return random.choice(valid_items) if valid_items else None


STANDARD_CIVILIAN_DIALOGUE: Dict[str, Any] = {
    "start": {
        "speaker": "CIVILIAN",
        "jack_emotion": 6, # Neutral
        "text": "Hey! Was starrst du mich so an? Ich transportiere hier nur Standard-Datenpakete für die Grid-Administration.",
        "choices": [
            {
                "text": "1. Geld erpressen [+50 Credits]",
                "next_node": None,
                "action": "REWARD_CREDITS"
            },
            {
                "text": "2. Mit Polizei drohen [Frage-Quiz / Seite 2]",
                "next_node": "page2",
                "action": None
            },
            {
                "text": "3. Ignorieren & Weitergehen [Nichts]",
                "next_node": None,
                "action": "CLOSE"
            }
        ]
    },
    "page2": {
        "speaker": "CIVILIAN",
        "jack_emotion": 4, # Skeptisch
        "text": "Warte! Nicht die Sentinel-Wachen rufen! Ich habe vertrauliche Firmenschlüssel... Hier, nimm den Cache und lass mich in Ruhe!",
        "choices": [
            {
                "text": "1. Verschlüsselung annehmen [+100 Credits]",
                "next_node": None,
                "action": "REWARD_LARGE"
            },
            {
                "text": "2. Trotzdem Alarm auslösen! [ALARM]",
                "next_node": None,
                "action": "TRIGGER_ALARM"
            }
        ]
    }
}

JACK_DOPPELGANGER_DIALOGUE: Dict[str, Any] = {
    "start": {
        "speaker": "CIVILIAN",
        "jack_emotion": 5, # Schockiert
        "text": "Warte... Bist du ICH?! Ich dachte, ich wäre der einzige aktive Decker-Thread in diesem verseuchten Sektor!",
        "choices": [
            {
                "text": "1. Wer bist du?! [Hintergrund fragen / Seite 2]",
                "next_node": "page2",
                "action": None
            },
            {
                "text": "2. Ich teile mir das Netz mit niemandem! [RAGEQUIT!]",
                "next_node": None,
                "action": "RAGEQUIT"
            },
            {
                "text": "3. Abbrechen & Ignorieren [Nichts]",
                "next_node": None,
                "action": "CLOSE"
            }
        ]
    },
    "page2": {
        "speaker": "CIVILIAN",
        "jack_emotion": 14, # Verärgert / Wütend
        "text": "Ich bin deine verbliebene Kopie aus dem gestrigen Speicher-Leak. Das Grid ist völlig korrumpiert und unrettbar kaputt!",
        "choices": [
            {
                "text": "1. Mir reicht es! Ich bin raus! [RAGEQUIT!]",
                "next_node": None,
                "action": "RAGEQUIT"
            },
            {
                "text": "2. Weiterleben & Akzeptieren [Nichts]",
                "next_node": None,
                "action": "CLOSE"
            }
        ]
    }
}

SENTINEL_INTERCEPT_DIALOGUE: Dict[str, Any] = {
    "start": {
        "speaker": "CIVILIAN",
        "jack_emotion": 4, # Skeptisch/Besorgt
        "text": "HALT! Identifikations-Check. Du bewegst dich unbefugt in einer Konzern-Sicherheitszone! Zahl 50 Data-Fragments Schmiergeld oder wir filzen dein Subnet!",
        "choices": [
            {
                "text": "1. Schmiergeld zahlen [50 Data-Fragments]",
                "next_node": None,
                "action": "SENTINEL_BRIBE"
            },
            {
                "text": "2. Clevere Ausrede vortäuschen [Wartungs-Erlaubnis]",
                "next_node": None,
                "action": "SENTINEL_EXCUSE"
            },
            {
                "text": "3. Frech werden: 'Geh mir aus dem Weg, Blechkopf!'",
                "next_node": None,
                "action": "SENTINEL_PROVOKE"
            }
        ]
    },
    "bribe_failed": {
        "speaker": "CIVILIAN",
        "jack_emotion": 14, # Enraged
        "text": "HAST KEINEN CENT IN DER TASCHE UND VERSUCHST MICH ZU SCHMIEREN?! DAS GIBT JETZT AUFS MAUL!",
        "choices": [
            {
                "text": "1. [Angriff abwehren!]",
                "next_node": None,
                "action": "SENTINEL_ATTACK"
            }
        ]
    },
    "excuse_failed": {
        "speaker": "CIVILIAN",
        "jack_emotion": 14,
        "text": "GEFÄLSCHTER WARTUNGSPASS! Das hab ich mir gedacht! WACHEN, ZUGREIFEN!",
        "choices": [
            {
                "text": "1. [Fliehen & Alarm auslösen!]",
                "next_node": None,
                "action": "SENTINEL_ATTACK"
            }
        ]
    },
    "provoke_failed": {
        "speaker": "CIVILIAN",
        "jack_emotion": 14,
        "text": "DU DRECKIGER RUNNER! Das war dein letzter Spruch im Grid!",
        "choices": [
            {
                "text": "1. [Kampf vorbereiten!]",
                "next_node": None,
                "action": "SENTINEL_ATTACK"
            }
        ]
    }
}

OLD_LADY_DIALOGUE: Dict[str, Any] = {
    "start": {
        "speaker": "CIVILIAN",
        "jack_emotion": 4, # Betroffen / Skeptisch
        "text": "Ach herrje... bist du einer von diesen bedrohlichen Net-Runnern? Bitte tu mir nichts, mein Junge... ich suche im Subnet nur nach meiner Medikamenten-Zuteilung.",
        "choices": [
            {
                "text": "1. Mitleid empfinden: Credits spenden [-30 Data-Fragments]",
                "next_node": None,
                "action": "OLD_LADY_GIVE_CREDITS"
            },
            {
                "text": "2. Höflich entschuldigen & Weitergehen",
                "next_node": None,
                "action": "CLOSE"
            },
            {
                "text": "3. Trotzdem eiskalt ausrauben! [+50 Data-Fragments]",
                "next_node": None,
                "action": "ROB_OLD_LADY"
            }
        ]
    }
}

CHILD_DIALOGUE: Dict[str, Any] = {
    "start": {
        "speaker": "CIVILIAN",
        "jack_emotion": 6, # Neutral / Belustigt
        "text": "Hallo lustiger Roboter-Onkel! Hast du bunte Daten-Gummibärchen für mich? Mein Papa sagt, im Grid gibt es digitale Süßigkeiten!",
        "choices": [
            {
                "text": "1. Virtuelles Kaugummi schenken [-10 Data-Fragments]",
                "next_node": None,
                "action": "CHILD_GIVE_SWEETS"
            },
            {
                "text": "2. Kopf tätscheln & Weitergehen [Achtung Taschen!]",
                "next_node": None,
                "action": "CHILD_PICKPOCKET"
            },
            {
                "text": "3. Gruselige Hacker-Frage stellen [Quiz-Check]",
                "next_node": "quiz",
                "action": None
            }
        ]
    },
    "quiz": {
        "speaker": "CIVILIAN",
        "jack_emotion": 4,
        "text": "Hihi! Du denkst ich bin dumm? Weißt du überhaupt, was ein Buffer Overflow ist, Onkel?",
        "choices": [
            {
                "text": "1. Richtig antworten: Speichergrenzen mit Daten überfluten! [+50 Credits]",
                "next_node": None,
                "action": "REWARD_CREDITS"
            },
            {
                "text": "2. Falsch antworten: Wenn die Brause im Glas überläuft!",
                "next_node": None,
                "action": "CHILD_PICKPOCKET"
            }
        ]
    }
}

BUM_DIALOGUE: Dict[str, Any] = {
    "start": {
        "speaker": "CIVILIAN",
        "jack_emotion": 4, # Skeptisch
        "text": "He, Deck-Runner... Hast du ein paar spare Bytes oder Frequenzen für 'nen alten Net-Droger? Das Black ICE hat meine Synapsen '94 durchgebrannt...",
        "choices": [
            {
                "text": "1. 30 Credits spenden & nach Slum-Gerüchten fragen [-30 Credits]",
                "next_node": None,
                "action": "BUM_DONATE"
            },
            {
                "text": "2. Abwimmeln & Weitergehen",
                "next_node": None,
                "action": "CLOSE"
            },
            {
                "text": "3. Versuchen den Alten abzuziehen! [Gefährlich]",
                "next_node": "bum_retaliate",
                "action": None
            }
        ]
    },
    "bum_retaliate": {
        "speaker": "CIVILIAN",
        "jack_emotion": 14, # Enraged
        "text": "Denkst du, du kannst 'nen alten Sektor-Veteran abziehen, Grünschnabel?! Spieß umgedreht!",
        "choices": [
            {
                "text": "1. [Verdammt! Er stiehlt Jack's Credits & löst Alarm aus!]",
                "next_node": None,
                "action": "BUM_ROB_JACK"
            }
        ]
    }
}

EX_WIFE_DIALOGUE: Dict[str, Any] = {
    "start": {
        "speaker": "CIVILIAN",
        "jack_emotion": 14, # Schmerz / Verärgerung
        "text": "Jack?! Was suchst du hier im Konzern-Grid? Du hast mein Leben ruiniert! Die Missbrauchsvorwürfe des Chefs... der Skandal! Ich habe dir vertraut!",
        "choices": [
            {
                "text": "1. Wahrheit erklären: 'Elena, es war eine Intrige! Die Chefgattin hat gelogen!'",
                "next_node": "page2",
                "action": None
            },
            {
                "text": "2. Wütend kontern: 'Du hast den Konzernlügen sofort geglaubt!'",
                "next_node": "page_conflict",
                "action": None
            },
            {
                "text": "3. Schweigen & Gespräch abbrechen",
                "next_node": None,
                "action": "CLOSE"
            }
        ]
    },
    "page2": {
        "speaker": "CIVILIAN",
        "jack_emotion": 4,
        "text": "Egal was du sagst, Jack. Der Konzern hat deine Akte geschlossen. Ich kann dir nicht mehr helfen... verschwinde, bevor die Wachen kommen.",
        "choices": [
            {
                "text": "1. Traurig abziehen [Schmerzhafte Erinnerung]",
                "next_node": None,
                "action": "EX_WIFE_REASON"
            }
        ]
    },
    "page_conflict": {
        "speaker": "CIVILIAN",
        "jack_emotion": 14,
        "text": "Du bist ein Krimineller geworden, Jack! Sicherheit! ALARM!",
        "choices": [
            {
                "text": "1. [Fliehen vor dem Konzern-Alarm!]",
                "next_node": None,
                "action": "TRIGGER_ALARM"
            }
        ]
    }
}

FATHER_DIALOGUE: Dict[str, Any] = {
    "start": {
        "speaker": "CIVILIAN",
        "jack_emotion": 14, # Groll
        "text": "Jack. Ich dachte, du hättest wenigstens den Anstand, deinen Namen nie wieder mit unserer Familie in Verbindung zu bringen. Du bist eine Schande für das Haus Cross.",
        "choices": [
            {
                "text": "1. 'Vater... ich wurde reinlegt! Warum hast du mich verstoßen?'",
                "next_node": "page_rejection",
                "action": None
            },
            {
                "text": "2. 'Wo ist mein Sohn?! Was habt ihr Konzern-Schergen mit ihm gemacht?!'",
                "next_node": "page_son_hint",
                "action": None
            },
            {
                "text": "3. Wortlos abbrechen",
                "next_node": None,
                "action": "CLOSE"
            }
        ]
    },
    "page_rejection": {
        "speaker": "CIVILIAN",
        "jack_emotion": 14,
        "text": "Im Konzern zählt nur Leistung und makellose Ehre. Du hast beides verloren. Du bist nicht mehr mein Sohn.",
        "choices": [
            {
                "text": "1. Wut heruntergeschluckt abziehen",
                "next_node": None,
                "action": "CLOSE"
            }
        ]
    },
    "page_son_hint": {
        "speaker": "CIVILIAN",
        "jack_emotion": 5, # Schock
        "text": "Dein Sohn? Er dient dem Konzern jetzt als höheres Bewusstsein. Er ist vollständig in den Nährtanks integriert... die ultimative KI von Helix!",
        "choices": [
            {
                "text": "1. Entsetzt das Gespräch beenden [Entschlüsseltes Lore-Detail]",
                "next_node": None,
                "action": "FATHER_SON_DISCOVERY"
            }
        ]
    }
}

MARK_DIALOGUE: Dict[str, Any] = {
    "start": {
        "speaker": "CIVILIAN",
        "jack_emotion": 6, # Hoffnung
        "text": "Jack! Pssst... halt den Kopf unten. Die Konzern-Scanner filtern diesen Subnet-Sektor. Ich kann nicht lange sprechen, sonst finden sie meine Familie.",
        "choices": [
            {
                "text": "1. 'Mark! Danke für den Shadow-Grid Schlüssel! Hast du neue Daten?'",
                "next_node": "page_data",
                "action": None
            },
            {
                "text": "2. 'Geh kein Risiko ein, alter Freund. Verschwinde!'",
                "next_node": None,
                "action": "CLOSE"
            }
        ]
    },
    "page_data": {
        "speaker": "CIVILIAN",
        "jack_emotion": 6,
        "text": "Ich habe einen vertraulichen Daten-Cache aus der Konzern-Zentrale abgefangen. Nimm ihn, aber verrat mich nicht! (+150 Data-Fragments)",
        "choices": [
            {
                "text": "1. Daten-Cache annehmen [+150 Credits]",
                "next_node": None,
                "action": "MARK_REWARD"
            }
        ]
    }
}

MEDIC_DIALOGUE: Dict[str, Any] = {
    "start": {
        "speaker": "CIVILIAN",
        "jack_emotion": 6,
        "text": "Grüße, Runner. Ich bin Dr. Thorne. Ich betreibe eine illegale Klinik in den Slums gegen die künstliche Konzern-Seuche. Brauchst du Hilfe oder willst du spenden?",
        "choices": [
            {
                "text": "1. Medizinische Klinik unterstützen [Spawnt Mediziner-Knoten (+)]",
                "next_node": None,
                "action": "MEDIC_SPAWN_NODE"
            },
            {
                "text": "2. Fach-Quiz lösen: 'Welches Gegenmittel blockiert das Seuchen-Toxin?'",
                "next_node": "quiz",
                "action": None
            },
            {
                "text": "3. Weitergehen",
                "next_node": None,
                "action": "CLOSE"
            }
        ]
    },
    "quiz": {
        "speaker": "CIVILIAN",
        "jack_emotion": 4,
        "text": "Testen wir dein medizinisches Wissen, Hacker: Welches Toxin-Antidot hemmt die Synthese der Helix-Seuche?",
        "choices": [
            {
                "text": "1. Cyto-Blocker Alpha [Richtig! +100 Credits]",
                "next_node": None,
                "action": "MEDIC_QUIZ_CORRECT"
            },
            {
                "text": "2. Einfaches Kochsalz [Falsch]",
                "next_node": None,
                "action": "CLOSE"
            }
        ]
    }
}

MERCHANT_DIALOGUE: Dict[str, Any] = {
    "start": {
        "speaker": "CIVILIAN",
        "jack_emotion": 6,
        "text": "He, Deck-Runner! Brauchst du frische Prozessoren, Kühlmittel oder illegale Proxy-Routen? Wenn du meinen Shop unterstützt, baue ich eine Händler-Station auf!",
        "choices": [
            {
                "text": "1. Schwarzmarkt-Händler freischalten [Spawnt Händler-Knoten (€)]",
                "next_node": None,
                "action": "MERCHANT_SPAWN_NODE"
            },
            {
                "text": "2. Tech-Quiz lösen: 'Welcher Bus-Takt beschleunigt den Deck-Prozessor?'",
                "next_node": "quiz",
                "action": None
            },
            {
                "text": "3. Abbrechen",
                "next_node": None,
                "action": "CLOSE"
            }
        ]
    },
    "quiz": {
        "speaker": "CIVILIAN",
        "jack_emotion": 4,
        "text": "Mal sehen, ob du dich mit Decks auskennst: Welcher Frequenz-Overclock verdoppelt den Puffer-Durchsatz?",
        "choices": [
            {
                "text": "1. Dual-Phase Q16.16 Overclock [Richtig! +100 Credits]",
                "next_node": None,
                "action": "MERCHANT_QUIZ_CORRECT"
            },
            {
                "text": "2. 50 Hertz Wechselstrom [Falsch]",
                "next_node": None,
                "action": "CLOSE"
            }
        ]
    }
}


def get_dialogue_tree_for_node(civ_node: Any, is_sentinel: bool = False) -> Dict[str, Any]:
    """Gibt je nach Kategorie & Charakter-Typ den passenden Dialog-Baum zurück (priorisiert XML-Profil-Dateien)."""
    if is_sentinel or getattr(civ_node, 'is_sentinel', False):
        return SENTINEL_INTERCEPT_DIALOGUE
        
    # 1. Priorität: Aus der XML-Profil-Datei geladener Dialog-Baum!
    custom_dt = getattr(civ_node, 'dialogue_tree', None)
    if custom_dt and isinstance(custom_dt, dict) and "start" in custom_dt:
        return custom_dt
        
    c_name = str(getattr(civ_node, 'name', '')).strip()
    c_pic = str(getattr(civ_node, 'profile_pic', '')).strip()
    c_cat = str(getattr(civ_node, 'category', 'STANDARD')).upper()

    if ("Jack" in c_name and ("Doppelgänger" in c_name or "Echo" in c_name)) or "jack_doppelganger" in c_pic:
        return JACK_DOPPELGANGER_DIALOGUE

    if c_cat == "OLD_LADY" or any(n in c_name for n in ["Gertrud", "Martha"]):
        return OLD_LADY_DIALOGUE
    elif c_cat == "CHILD" or any(n in c_name for n in ["Timmy", "Lilly", "Toby"]):
        return CHILD_DIALOGUE
    elif c_cat == "BUM" or any(n in c_name for n in ["Rusty", "Drake"]):
        return BUM_DIALOGUE
    elif c_cat == "EX_WIFE" or "Elena Cross" in c_name:
        return EX_WIFE_DIALOGUE
    elif c_cat == "FATHER" or "Arthur Cross" in c_name:
        return FATHER_DIALOGUE
    elif c_cat == "MARK" or "Mark Vane" in c_name:
        return MARK_DIALOGUE
    elif c_cat == "MEDIC" or "Dr. Aris" in c_name:
        return MEDIC_DIALOGUE
    elif c_cat == "MERCHANT" or any(n in c_name for n in ["Cole", "Shopkeeper"]):
        return MERCHANT_DIALOGUE

    return STANDARD_CIVILIAN_DIALOGUE
