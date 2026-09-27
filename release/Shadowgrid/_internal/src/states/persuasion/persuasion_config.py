import os
import random
import pygame
from typing import List, Dict, Tuple, Optional
from src.utils.logger import logger
from src.db.civilian_db import civilian_db
from src.ui.font_manager import GREEN_PHOSPHOR, GREEN_BRIGHT, AMBER_WARN, RED_ALERT, STEEL_GREY
from src.states.persuasion.npc_profile import NPCProfile

BANNER_CONFIG = {
    "jack_target_x": 80,
    "jack_start_x": -800,
    "jack_exit_x": 1600,
    "npc_target_right_x": 1200,
    "npc_start_right_x": 1600,
    "npc_exit_right_x": -800,
    "max_chars": 36,
    "banner_max_w": 700,
}

ATTACK_TIERS = {
    0: { # KORTEX
        1: ("Neural Lag", "Kortex-Latenz in gegnerische Synapsen-Schleife einspeisen.", "attack_kortex_neural_lag.png"),
        2: ("Memory Wipe", "Temporäre Löschung des gegnerischen Kurzzeitgedächtnisses.", "attack_kortex_memory_wipe.png"),
        3: ("Synaptic Burnout", "Hochfrequenz-Spannungsimpuls brennt kortikale Pfade aus.", "attack_kortex_synaptic_burnout.png"),
        4: ("Neural Flatline", "Vollständige Überlastung der neuronalen Bio-Schnittstelle.", "attack_kortex_neural_flatline.png")
    },
    1: { # CYBER
        1: ("Glitch Spike", "Kurzer Störimpuls überlastet Cyberware-Filter.", "attack_cyber_glitch_spike.png"),
        2: ("Kiroshi-Blinding", "Optische Cyber-Implantate temporär überblenden.", "attack_cyber_kiroshi_blinding.png"),
        3: ("Motor Seizure", "Motorisches Nervensystem der Implikate blockieren.", "attack_cyber_motor_seizure.png"),
        4: ("Cyberpsychosis-Induktion", "Systemgrenzen kollabieren lassen und Cyberpsychose auslösen.", "attack_cyber_psychosis_induction.png")
    },
    2: { # COUNTER
        1: ("Trace-Daemon", "Gegen-Daemon starten um gegnerische Standort-Traces zu verlangsamen.", "attack_counter_trace_daemon.png"),
        2: ("Range-Limiter", "Reichweiten-Drossel im lokalen Subnetz installieren.", "attack_counter_range_limiter.png"),
        3: ("Synchronity-Lagger", "Paketlaufzeiten des gegnerischen Decks künstlich verzögern.", "attack_counter_synchronitty_lagger.png"),
        4: ("Hunter-Feedback", "Aggressives Rücksignal direkt in das Deck des Gegners leiten.", "attack_counter_hunter_feedback.png")
    },
    3: { # PSYCHO
        1: ("Simstim-Flash", "Sensorischen Simstim-Impuls zur Desorientierung einspeisen.", "attack_psycho_simstim_flash.png"),
        2: ("AR-Phantasma", "Täuschende Augmented-Reality Phantasma-Knoten projizieren.", "attack_psycho_ar_phantasma.png"),
        3: ("Conditioning Daemon", "Konditionierungs-Routine zur Untergrabung der Kontrolle injizieren.", "attack_psycho_conditioning_daemon.png"),
        4: ("Engramm-Splice", "Fremdes Engramm-Segment in den aktiven Speicher-Grid kopieren.", "attack_psycho_engram_splice.png")
    }
}

EMOTIONS = {
    "WEAK": ("[ (v_v) WEAK (+2.0) ]", GREEN_BRIGHT),
    "RECEPTIVE": ("[ (^_^) RECEPTIVE (+1.0) ]", GREEN_PHOSPHOR),
    "HABITUAL": ("[ (-_-) HABITUAL (-1.0) ]", AMBER_WARN),
    "RESIST": ("[ (>_<) RESIST (-2.0) ]", RED_ALERT),
    "LOVE": ("[ (v_v) WEAK (+2.0) ]", GREEN_BRIGHT),
    "LIKE": ("[ (^_^) RECEPTIVE (+1.0) ]", GREEN_PHOSPHOR),
    "DISLIKE": ("[ (-_-) HABITUAL (-1.0) ]", AMBER_WARN),
    "HATE": ("[ (>_<) RESIST (-2.0) ]", RED_ALERT),
    "NEUTRAL": ("[ -_- NEUTRAL (0.0) ]", STEEL_GREY)
}

def normalize_rating(raw_rating: str) -> str:
    mapping = {"LOVE": "WEAK", "LIKE": "RECEPTIVE", "DISLIKE": "HABITUAL", "HATE": "RESIST"}
    return mapping.get(raw_rating.upper(), raw_rating.upper())

def get_npc_reaction_text(pref_norm: str) -> str:
    if pref_norm == "WEAK":
        lines = [
            "\"System-Widerstand gebrochen! Kortex-Kollaps!\"",
            "\"Kritischer Treffer! Meine Firewall brennt aus!\"",
            "\"ICE zerstört! Subnetz-Kontrolle verloren!\""
        ]
    elif pref_norm == "RECEPTIVE":
        lines = [
            "\"Warnung: Subnetz-Integrität schwindet!\"",
            "\"Starker Impuls! Deck leitet Gegenmaßnahmen ein.\"",
            "\"Systemüberlastung bei 75%!\""
        ]
    elif pref_norm == "HABITUAL":
        lines = [
            "\"Standard-Spike erkannt... vernachlässigbar.\"",
            "\"Routine-Angriff abgefedert. Keine Schäden.\"",
            "\"Mäßige Wirkung, ICE stabilisiert sich.\""
        ]
    else:
        lines = [
            "\"Gegenfeuer aktiv! Angriff wirkungslos abgewehrt!\"",
            "\"Resistenz-Matrix greift! Mein Deck übernimmt Kontrolle!\"",
            "\"Nutzloser Versuch! Gegenschlag eingeleitet!\""
        ]
    return random.choice(lines)

def init_npcs() -> List[NPCProfile]:
    db_profiles = civilian_db.get_all_persuasion_profiles()
    npcs = []
    
    for p in db_profiles:
        img_path = p.get("image_path", "")
        name = p.get("name", "Unbekannt")
        
        face_surf = None
        if img_path:
            paths_to_check = [
                img_path,
                os.path.join("src", "gfx", "faces", os.path.basename(img_path)),
                os.path.join("src", "gfx", "faces", f"{name.lower().replace(' ', '_')}.png")
            ]
            for path in paths_to_check:
                if os.path.exists(path):
                    try:
                        raw = pygame.image.load(path).convert_alpha()
                        face_surf = pygame.transform.smoothscale(raw, (180, 180))
                        break
                    except Exception as e:
                        logger.warning(f"Could not load face image {path}: {e}")

        pers = p.get("persuasion", {})
        prefs_raw = pers.get("preferences", {
            0: ("RECEPTIVE", 1.0),
            1: ("WEAK", 2.0),
            2: ("HABITUAL", -1.0),
            3: ("RESIST", -2.0)
        })

        preferences = {}
        for k, v in prefs_raw.items():
            idx = int(k)
            norm_rating = normalize_rating(str(v[0]))
            preferences[idx] = (norm_rating, float(v[1]))

        intel_score = pers.get("intelligence", 5)
        intel_label = pers.get("intelligence_label", "Durchschnittlich")

        npc = NPCProfile(
            name=name,
            job=p.get("job", "Data Courier"),
            origin=p.get("origin", "Neo-Tokyo Sub-Net"),
            category=p.get("category", "STANDARD"),
            image_path=img_path,
            face_surface=face_surf,
            intelligence=intel_score,
            intelligence_label=intel_label,
            preferences=preferences,
            personality_traits=p.get("personality_traits", "Keine Angaben"),
            comment_jack=p.get("comment_jack", "JACK // KEINE DATEN VORHANDEN."),
            base_disposition=random.randint(25, 45)
        )
        npcs.append(npc)

        if not npcs:
            npcs = [
                NPCProfile(
                    name="Aria Sterling",
                    job="Holographic Interface Designer",
                    origin="Neo-Tokyo Sub-Net",
                    category="STANDARD",
                    image_path="",
                    face_surface=None,
                    intelligence=8,
                    intelligence_label="Schlau / Redegewandt",
                    preferences={0: ("WEAK", 2.0), 1: ("RECEPTIVE", 1.0), 2: ("HABITUAL", -0.5), 3: ("RESIST", -1.0)},
                    personality_traits="Creative, Vibrant",
                    comment_jack="JACK // VISUAL ARTIST WITH A HACKING HABIT."
                )
            ]

    return npcs

def load_battle_icons() -> Tuple[Dict[str, pygame.Surface], Dict[str, pygame.Surface]]:
    icons_dir = os.path.join("media", "images", "battle_icons")
    if not os.path.exists(icons_dir):
        icons_dir = os.path.abspath(os.path.join(os.getcwd(), "media", "images", "battle_icons"))
    attack_icons = {}
    spell_icons = {}
    if not os.path.exists(icons_dir):
        logger.warning(f"[PersuasionState] Battle icons directory not found at {icons_dir}")
        return attack_icons, spell_icons
    for fname in os.listdir(icons_dir):
        if not fname.endswith(".png"):
            continue
        fpath = os.path.join(icons_dir, fname)
        try:
            raw_surf = pygame.image.load(fpath).convert_alpha()
            if fname.startswith("attack_"):
                attack_icons[fname] = pygame.transform.smoothscale(raw_surf, (72, 72))
            elif fname.startswith("spell_"):
                key_name = fname.replace("spell_", "").replace(".png", "")
                spell_icons[key_name] = pygame.transform.smoothscale(raw_surf, (48, 48))
        except Exception as e:
            logger.warning(f"[PersuasionState] Failed to load icon {fname}: {e}")
    logger.info(f"[PersuasionState] Loaded {len(attack_icons)} attack icons and {len(spell_icons)} spell icons.")
    return attack_icons, spell_icons
