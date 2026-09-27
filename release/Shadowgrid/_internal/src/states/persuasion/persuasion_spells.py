import random
import pygame
from typing import Any, Dict, List, Tuple, Optional
from src.ui.spell_manager import Spell, spell_registry

class PersuasionSpellEngine:
    """Verwaltet Inventar-Seeding, Spell-Equipping, Unikats-Regeln und Spell-Ausführungen."""

    @staticmethod
    def init_default_inventory(state: Any) -> None:
        if state.debug_mode:
            state.inventory = {
                "break_connections.py": 1,
                "sync.py": 1,
                "desync.py": 1,
                "boost.py": 1,
                "nerf.py": 1,
                "blinded.py": 1,
                "dizzy.py": 1,
                "reduce_damage.py": 1,
                "ally_damage.py": 1,
                "firewall_breach.py": 1,
                "system_hack.py": 1,
                "data_corrupt.py": 1,
                "malware_injection.py": 1,
                "cpu_overclock.py": 1,
                "network_jam.py": 1,
                "signal_hijack.py": 1,
                "biohacker.py": 1
            }
        else:
            state.inventory = {
                "break_connections.py": 1,
                "sync.py": 1,
                "boost.py": 1,
                "ally_damage.py": 1,
                "firewall_breach.py": 1,
                "cpu_overclock.py": 1,
                "biohacker.py": 1
            }
        state.action_bar = [
            "break_connections.py",
            "sync.py",
            "boost.py",
            "firewall_breach.py",
            "ally_damage.py",
            "biohacker.py"
        ]

    @staticmethod
    def get_sorted_inventory_files(state: Any) -> List[Tuple[str, int]]:
        files = []
        if "break_connections.py" in state.inventory:
            files.append(("break_connections.py", state.inventory["break_connections.py"]))
        sorted_spells = sorted([k for k in state.inventory.keys() if k != "break_connections.py"])
        for fn in sorted_spells:
            sp = spell_registry.get_spell_by_filename(fn)
            if sp and sp.is_counterspell and not state.debug_mode:
                continue
            files.append((fn, state.inventory[fn]))
        return files

    @staticmethod
    def equip_spell_to_next_free_slot(state: Any, filename: str) -> bool:
        sp = spell_registry.get_spell_by_filename(filename)
        if sp and sp.is_counterspell and not state.debug_mode:
            state.status_message = "Gegner-Counterspells können nur im Debug Modus ausgerüstet werden!"
            return False

        if filename in state.action_bar:
            state.status_message = f"[{filename.upper()}] ist bereits in der Action Bar ausgerüstet!"
            sound_manager = state.sm.context.get("sound_manager")
            if sound_manager:
                sound_manager.play_spatial("action_cancel", 640, 360, 640, 360, base_volume=0.6)
            return False

        for i in range(len(state.action_bar)):
            if state.action_bar[i] is None:
                state.action_bar[i] = filename
                sound_manager = state.sm.context.get("sound_manager")
                if sound_manager:
                    sound_manager.play_spatial("click_target", 640, 360, 640, 360, base_volume=0.8)
                state.status_message = f"[{filename}] in Action Bar Slot #{i+1} ausgerüstet."
                return True
        state.status_message = "Action Bar ist voll! (Rechtsklick auf Slot zum Freimachen)"
        return False

    @staticmethod
    def activate_spell(state: Any, filename: str, slot_idx: Optional[int] = None) -> None:
        if not state.target_npc or state.combat_finished or state.active_banner_anim is not None:
            return

        if filename == "break_connections.py":
            state.status_message = "BREAK_CONNECTIONS.PY: Verbindung wird sofort getrennt!"
            state._exit_minigame()
            return

        sp = spell_registry.get_spell_by_filename(filename)
        if not sp:
            return

        if sp.is_counterspell:
            if not state.debug_mode:
                state.status_message = "Gegner-Counterspells sind im regulären Spiel nicht für Jack verfügbar!"
                return
            else:
                PersuasionSpellEngine.apply_counterspell_effect(state, sp)
                return

        if filename in state.inventory:
            if state.inventory[filename] > 1:
                state.inventory[filename] -= 1
            else:
                del state.inventory[filename]
                for i in range(len(state.action_bar)):
                    if state.action_bar[i] == filename:
                        state.action_bar[i] = None
        else:
            for i in range(len(state.action_bar)):
                if state.action_bar[i] == filename:
                    state.action_bar[i] = None

        all_revealed = all(state.target_npc.revealed_preferences)
        jack_msg = sp.jack_cinematic_line
        npc_msg = sp.civ_cinematic_line
        sfx_key = "hack_success"

        if sp.spell_id == "sync":
            if not all_revealed:
                state.status_message = "⚠️ [SYNC.PY] FEHLER: UNVOLLSTÄNDIGE MATRIX! Alle 4 Resistenzen müssen aufgedeckt sein!"
                jack_msg = "[SYNC.PY] FEHLER: UNVOLLSTÄNDIGE MATRIX!"
                npc_msg = "\"SYNC FEHLGESCHLAGEN! UNENTDECKTE SCHWÄCHEN KÖNNEN NICHT SYNCHRONISIERT WERDEN!\""
                sfx_key = "action_cancel"
            else:
                best_order = [1, 2, 3, 4]
                for act_i in range(4):
                    pref_name, mult = state.target_npc.preferences[act_i]
                    pref_norm = state._normalize_rating(pref_name)
                    if pref_norm == "WEAK":
                        best_order[act_i] = 4
                    elif pref_norm == "RECEPTIVE":
                        best_order[act_i] = 3
                    elif pref_norm == "HABITUAL":
                        best_order[act_i] = 2
                    else:
                        best_order[act_i] = 1
                state.wedges = best_order
                state.status_message = "[SYNC.PY] OPTIMALE KEIL-TAKTRATE AUSGERICHTET!"

        elif sp.spell_id == "boost":
            if not all_revealed:
                state.status_message = "⚠️ [BOOST.PY] FEHLER: UNVOLLSTÄNDIGE MATRIX! Alle 4 Resistenzen müssen aufgedeckt sein!"
                jack_msg = "[BOOST.PY] FEHLER: UNVOLLSTÄNDIGE MATRIX!"
                npc_msg = "\"BOOST FEHLGESCHLAGEN! OHNE ANALYSE ALLER SCHWÄCHEN WIRKUNGSLOS!\""
                sfx_key = "action_cancel"
            else:
                state.boost_active = True
                state.status_message = "[BOOST.PY] ALLE SCHWÄCHEN AUF MAXIMUM ERHÖHT!"

        elif sp.spell_id == "apply_damage":
            gain = int(state.target_npc.max_disposition * 0.25)
            state.target_npc.disposition = min(95, state.target_npc.disposition + gain)
            state.status_message = f"[ALLY_DAMAGE.PY] OVERRIDE SOFORT UM +{gain}% ERHÖHT!"

        elif sp.spell_id == "firewall_breach":
            state.target_npc.revealed_preferences = [True, True, True, True]
            state.status_message = "[FIREWALL_BREACH.PY] ALLE SYSTEM-RESISTENZEN OFFENGELEGT!"

        elif sp.spell_id == "cpu_overclock":
            state.cpu_overclock_active = True
            state.status_message = "[CPU_OVERCLOCK.PY] ANGRIPPS-TIERS FÜR 1 RUNDE EXPONENTIELL VERDOPPELT!"

        elif sp.spell_id == "biohacker":
            if state.biohacker_flashing:
                state.combat_finished = True
                state.combat_result = "VICTORY"
                state.credits += 250
                state.target_npc.disposition = state.target_npc.max_disposition
                state.status_message = "🏆 BIOHACKER ULTRA-CHIP INJEKTION ERFOLGREICH! SOFORTIGER SIEG! (+250 Cr)"
            else:
                state.combat_finished = True
                state.combat_result = "DEFEAT"
                state.target_npc.disposition = 0
                state.status_message = "💀 BIOHACKER FEHLGESCHLAGEN! OHNE BEREITSCHAFT INJIZIERT - SOFORTIGE NIEDERLAGE!"

        state.active_banner_anim = {
            "idx": -1,
            "is_counterspell": False,
            "wedge_val": 4 if sfx_key == "hack_success" else 1,
            "mult": 2.0 if sfx_key == "hack_success" else -1.0,
            "pref_norm": "WEAK" if sfx_key == "hack_success" else "RESIST",
            "actual_delta": 25 if sfx_key == "hack_success" else 0,
            "jack_msg": jack_msg,
            "npc_msg": npc_msg,
            "timer": 0.0,
            "sfx_played": False,
            "dissolve_alpha": 255
        }

        sound_manager = state.sm.context.get("sound_manager")
        if sound_manager:
            sound_manager.play_spatial(sfx_key, 640, 360, 640, 360, base_volume=0.9)

    @staticmethod
    def apply_counterspell_effect(state: Any, cs: Spell) -> None:
        if not state.target_npc or state.combat_finished:
            return

        if cs.spell_id == "desync":
            worst_order = [4, 3, 2, 1]
            random.shuffle(worst_order)
            state.wedges = worst_order
            state.status_message = "⚠️ COUNTERSPELL: [DESYNC.PY] KEILE UMGESCHMUTZT!"

        elif cs.spell_id == "nerf":
            state.nerf_active = True
            state.status_message = "⚠️ COUNTERSPELL: [NERF.PY] ANGRIPFS-PFFADE GEDROSSELT!"

        elif cs.spell_id == "blinded":
            state.blinded_active = True
            state.blinded_anim_timer = 0.0
            state.status_message = "⚠️ COUNTERSPELL: [BLINDED.PY] OPTIK ÜBERBLENDET!"

        elif cs.spell_id == "dizzy":
            state.dizzy_active = True
            state.dizzy_timer = 0.0
            state.dizzy_mode_timer = 0.0
            state.dizzy_inverted = True
            state.status_message = "⚠️ COUNTERSPELL: [DIZZY.PY] SENSORIK COLLAPSED // MAUS VERWIRRT!"

        elif cs.spell_id == "reduce_damage":
            loss = int(state.target_npc.max_disposition * 0.25)
            state.target_npc.disposition = max(5, state.target_npc.disposition - loss)
            state.status_message = f"⚠️ COUNTERSPELL: [REDUCE_DAMAGE] OVERRIDE UM -{loss}% GESENKT!"

        elif cs.spell_id == "system_hack":
            state.target_npc.revealed_preferences = [False, False, False, False]
            prefs = list(state.target_npc.preferences.values())
            random.shuffle(prefs)
            for i in range(4):
                state.target_npc.preferences[i] = prefs[i]
            state.status_message = "⚠️ COUNTERSPELL: [SYSTEM_HACK] RESISTENZEN NEU VERSCHLÜSSELT!"

        elif cs.spell_id == "data_corrupt":
            state.data_corrupt_active = True
            state.status_message = "⚠️ COUNTERSPELL: [DATA_CORRUPT] SYSTEM-GLYPHEN KORRUMPIERT!"

        elif cs.spell_id == "malware_injection":
            state.malware_injection_active = True
            state.malware_spawn_timer = 0.0
            if hasattr(state, "_spawn_single_malware_popup"):
                for _ in range(3):
                    state._spawn_single_malware_popup()
            state.status_message = "⚠️ COUNTERSPELL: [MALWARE_INJECTION] POPUP-TROJANER INJIZIERT!"

        elif cs.spell_id == "network_jam":
            state.network_jam_active = True
            glitch_proc = state.sm.context.get("glitch_processor")
            if glitch_proc and hasattr(glitch_proc, "trigger_negative_impact"):
                glitch_proc.trigger_negative_impact(-1, 2)
            state.status_message = "⚠️ COUNTERSPELL: [NETWORK_JAM] TERMINAL ERZITTERT!"

        elif cs.spell_id == "signal_hijack":
            state.signal_hijack_active = True
            state.hijack_stage = 0
            state.hijack_timer = 0.0
            state.hijack_inspect_idx = 0
            state.hijack_target_idx = 0
            state.status_message = "⚠️ COUNTERSPELL: [SIGNAL_HIJACK] GEGNER ÜBERNIMMT ZEIGER!"

        state.active_banner_anim = {
            "idx": -1,
            "is_counterspell": True,
            "wedge_val": 1,
            "mult": -2.0,
            "pref_norm": "RESIST",
            "actual_delta": -15,
            "jack_msg": cs.jack_cinematic_line,
            "npc_msg": cs.civ_cinematic_line,
            "timer": 0.0,
            "sfx_played": False,
            "dissolve_alpha": 255
        }

    @staticmethod
    def update_signal_hijack(state: Any, dt: float) -> None:
        if not getattr(state, "signal_hijack_active", False) or state.active_banner_anim or state.combat_finished:
            return

        if not hasattr(state, "hijack_stage"):
            state.hijack_stage = 0
            state.hijack_timer = 0.0
            state.hijack_inspect_idx = 0
            state.hijack_target_idx = 0

        state.hijack_timer += dt

        if state.hijack_stage == 0:
            if state.hijack_inspect_idx < 4:
                rect = state.get_action_rect(state.hijack_inspect_idx)
                tx, ty = float(rect.centerx), float(rect.centery)
                state.virtual_mouse_pos[0] += (tx - state.virtual_mouse_pos[0]) * min(1.0, dt * 6.0)
                state.virtual_mouse_pos[1] += (ty - state.virtual_mouse_pos[1]) * min(1.0, dt * 6.0)
                state.hovered_action_idx = state.hijack_inspect_idx
                state.hovered_icon_idx = state.hijack_inspect_idx
                if state.hijack_timer >= 0.5:
                    state.hijack_timer = 0.0
                    state.hijack_inspect_idx += 1
            else:
                state.hijack_stage = 1
                state.hijack_timer = 0.0

        elif state.hijack_stage == 1:
            if state.hijack_timer >= 0.6:
                best_idx = 0
                min_delta = 9999
                if state.target_npc:
                    for i in range(4):
                        if not state.used_in_round[i]:
                            wedge_val = state.wedges[i]
                            pref_name, mult = state.target_npc.preferences[i]
                            pref_norm = state._normalize_rating(pref_name)
                            skill_factor = 1.0 + (state.speechcraft_level / 100.0) * 0.5
                            delta = int(round(wedge_val * mult * skill_factor * 3.5))
                            if delta < min_delta:
                                min_delta = delta
                                best_idx = i
                state.hijack_target_idx = best_idx
                state.hijack_stage = 2
                state.hijack_timer = 0.0

        elif state.hijack_stage == 2:
            rect = state.get_action_rect(state.hijack_target_idx)
            tx, ty = float(rect.centerx), float(rect.centery)
            state.virtual_mouse_pos[0] += (tx - state.virtual_mouse_pos[0]) * min(1.0, dt * 5.0)
            state.virtual_mouse_pos[1] += (ty - state.virtual_mouse_pos[1]) * min(1.0, dt * 5.0)
            state.hovered_action_idx = state.hijack_target_idx
            state.hovered_icon_idx = state.hijack_target_idx
            if state.hijack_timer >= 0.7:
                state.hijack_stage = 3
                state.hijack_timer = 0.0

        elif state.hijack_stage == 3:
            target = state.hijack_target_idx
            state.signal_hijack_active = False
            state.hijack_stage = 0
            state._execute_action(target)

    @staticmethod
    def trigger_enemy_counterspell(state: Any) -> None:
        counterspells = [s for s in spell_registry.get_all_spells() if s.is_counterspell]
        if counterspells:
            PersuasionSpellEngine.apply_counterspell_effect(state, random.choice(counterspells))
