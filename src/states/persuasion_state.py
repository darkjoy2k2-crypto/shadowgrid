import os
import pygame
import random
import time
from typing import Any, List, Dict, Tuple, Optional

from src.core.state_machine import State
from src.utils.fade_controller import FadeController
from src.ui.nine_slice import NineSliceRenderer
from src.ui.font_manager import font_mgr
from src.utils.logger import logger
from src.ui.spell_manager import spell_registry, Spell
from src.utils.glitch_controller import GlitchPostProcessor

from src.states.persuasion.npc_profile import NPCProfile
from src.states.persuasion.persuasion_spells import PersuasionSpellEngine
from src.states.persuasion.persuasion_renderer import PersuasionRenderer
from src.states.persuasion.persuasion_config import (
    BANNER_CONFIG, ATTACK_TIERS, EMOTIONS, normalize_rating, get_npc_reaction_text, init_npcs, load_battle_icons
)
from src.states.persuasion.persuasion_layout import PersuasionLayout
from src.states.persuasion.persuasion_overlays import PersuasionOverlays

CANVAS_W = 1280
CANVAS_H = 720

class PersuasionState(State):
    """Cyberdeck Netrunner Combat Protocol state controller."""
    ACTION_NAMES = ["KORTEX", "CYBER", "COUNTER", "PSYCHO"]
    BANNER_CONFIG = BANNER_CONFIG
    ATTACK_TIERS = ATTACK_TIERS
    EMOTIONS = EMOTIONS

    def __init__(self, state_machine: Any) -> None:
        super().__init__(state_machine)
        self.fade_controller = FadeController()
        self.nineslice = NineSliceRenderer()
        self.persuasion_surface = pygame.Surface((CANVAS_W, CANVAS_H))
        self.credits = 500
        self.speechcraft_level = 45
        self.patience = 100.0
        self.patience_decay_rate = 1.2
        self.wedges: List[int] = [1, 2, 3, 4]
        self.used_in_round: List[bool] = [False, False, False, False]
        self.round_counter = 1
        self.hovered_action_idx: Optional[int] = None
        self.hovered_icon_idx: Optional[int] = None
        self.hovered_btn_idx: Optional[str] = None
        self.status_message = "NETRUNNER COMBAT ENGINE READY"
        self.last_delta_text = ""
        self.last_hovered_action_idx: Optional[int] = None
        self.last_played_voice_group: Optional[str] = None
        self.voice_channel: Optional[pygame.mixer.Channel] = None
        self.active_banner_anim: Optional[Dict[str, Any]] = None
        self.attack_icons: Dict[str, pygame.Surface] = {}
        self.spell_icons: Dict[str, pygame.Surface] = {}
        self._load_battle_icons()
        self.combat_finished: bool = False
        self.combat_result: Optional[str] = None
        self.npcs: List[NPCProfile] = []
        self.current_npc_idx = 0
        self.target_npc: Optional[NPCProfile] = None
        self.debug_mode: bool = True
        self.spell_registry = spell_registry
        self.inventory: Dict[str, int] = {}
        self.action_bar: List[Optional[str]] = [None] * 6
        self._init_default_inventory()
        self.dragged_item: Optional[Dict[str, Any]] = None
        self.hovered_spell_filename: Optional[str] = None
        self.hover_start_time: float = 0.0
        self.last_mouse_pos: Tuple[int, int] = (0, 0)
        self.last_mouse_move_time: float = time.time()
        self.inventory_active: bool = True
        self.inventory_window_pos: List[int] = [860, 435]
        self.dragging_inventory_window: bool = False
        self.inventory_window_drag_offset: Tuple[int, int] = (0, 0)
        self.directory_scroll_offset: int = 0
        self.dragging_slider: bool = False
        self.action_bar_pos: List[int] = [860, 595]
        self.dragging_action_bar: bool = False
        self.action_bar_drag_offset: Tuple[int, int] = (0, 0)
        self.boost_active: bool = False
        self.nerf_active: bool = False
        self.cpu_overclock_active: bool = False
        self.dizzy_active: bool = False
        self.dizzy_timer: float = 0.0
        self.dizzy_mode_timer: float = 0.0
        self.dizzy_inverted: bool = False
        self.virtual_mouse_pos: List[float] = [640.0, 360.0]
        self.cursor_img: Optional[pygame.Surface] = None
        self.data_corrupt_active: bool = False
        self.malware_injection_active: bool = False
        self.malware_spawn_timer: float = 0.0
        self.malware_popups: List[Dict[str, Any]] = []
        self.network_jam_active: bool = False
        self.signal_hijack_active: bool = False
        self.signal_hijack_timer: float = 0.0
        self.biohacker_flashing: bool = False

    def _spawn_single_malware_popup(self) -> None: PersuasionOverlays.spawn_single_malware_popup(self)

    def _init_default_inventory(self) -> None: PersuasionSpellEngine.init_default_inventory(self)
    def _get_sorted_inventory_files(self) -> List[Tuple[str, int]]: return PersuasionSpellEngine.get_sorted_inventory_files(self)
    def _equip_spell_to_next_free_slot(self, filename: str) -> bool: return PersuasionSpellEngine.equip_spell_to_next_free_slot(self, filename)
    def _activate_spell(self, filename: str, slot_idx: Optional[int] = None) -> None: PersuasionSpellEngine.activate_spell(self, filename, slot_idx)
    def _apply_counterspell_effect(self, sp: Spell) -> None: PersuasionSpellEngine.apply_counterspell_effect(self, sp)

    def _corrupt_text(self, text: str) -> str:
        if not self.data_corrupt_active or self.active_banner_anim is not None: return text
        return "".join(ch if ch in (" ", "\n", "\t", ":", "/", "[", "]", "(", ")") else random.choice("ॐअइकगचजतदनपबमरलवशसह§$%&#*+~") for ch in str(text))

    def _load_battle_icons(self) -> None:
        self.attack_icons, self.spell_icons = load_battle_icons()
        cp = os.path.join("src", "gfx", "cursor.png")
        if os.path.exists(cp):
            try: self.cursor_img = pygame.image.load(cp).convert_alpha()
            except Exception: pass

    def _normalize_rating(self, raw_rating: str) -> str: return normalize_rating(raw_rating)
    def _get_npc_reaction_text(self, pref_norm: str) -> str: return get_npc_reaction_text(pref_norm)

    def _init_npcs(self) -> None:
        self.npcs = init_npcs()
        self.current_npc_idx = 0
        if self.npcs: self.target_npc = self.npcs[0]

    def init(self) -> None:
        pygame.mouse.set_visible(False)
        self.persuasion_surface = pygame.Surface((CANVAS_W, CANVAS_H))
        self.sm.context["native_surface"] = self.persuasion_surface
        self._load_battle_icons()
        self._init_npcs()
        self._reset_round_wedges()
        self.patience = 100.0
        self.combat_finished = False
        self.combat_result = None
        self.status_message = "COMBAT ENGINE: Waehle ein Angriffsmuster oder Script."
        self.fade_controller.start_fade_in(duration=0.5)

    def _clear_all_counterspells_and_ungrab(self) -> None:
        self.dizzy_active = False; self.dizzy_inverted = False
        self.blinded_active = False; self.data_corrupt_active = False
        self.malware_injection_active = False; self.network_jam_active = False
        self.signal_hijack_active = False; self.hijack_stage = 0
        try: pygame.event.set_grab(False)
        except Exception: pass

    def is_dizzy_effective(self) -> bool:
        return bool(self.dizzy_active and self.dizzy_inverted and self.active_banner_anim is None and not self.combat_finished)

    def _reset_round_wedges(self) -> None:
        self.wedges = [random.randint(1, 4) for _ in range(4)]
        self.used_in_round = [False, False, False, False]
        self.boost_active = False; self.nerf_active = False; self.cpu_overclock_active = False
        self._clear_all_counterspells_and_ungrab()

    def get_native_mouse_pos(self) -> Tuple[int, int]:
        if not self.combat_finished and (self.is_dizzy_effective() or (self.signal_hijack_active and not self.active_banner_anim)):
            return (int(self.virtual_mouse_pos[0]), int(self.virtual_mouse_pos[1]))
        pos = PersuasionLayout.get_native_mouse_pos(self.sm.context.get("scaled_surface"), pygame.mouse.get_pos())
        self.virtual_mouse_pos[0], self.virtual_mouse_pos[1] = float(pos[0]), float(pos[1])
        return pos

    def get_action_rect(self, i: int) -> pygame.Rect: return PersuasionLayout.get_action_rect(i)
    def get_dir_box_rect(self) -> pygame.Rect: return PersuasionLayout.get_dir_box_rect(self.inventory_window_pos)
    def get_dir_item_rect(self, r_i: int) -> pygame.Rect: return PersuasionLayout.get_dir_item_rect(self.inventory_window_pos, r_i)
    def get_folder_icon_rect(self) -> pygame.Rect: return PersuasionLayout.get_folder_icon_rect()
    def get_action_bar_full_rect(self) -> pygame.Rect: return PersuasionLayout.get_action_bar_full_rect(self.action_bar_pos)
    def get_action_bar_header_rect(self) -> pygame.Rect: return PersuasionLayout.get_action_bar_header_rect(self.action_bar_pos)
    def get_action_bar_slot_rect(self, s_i: int) -> pygame.Rect: return PersuasionLayout.get_action_bar_slot_rect(self.action_bar_pos, s_i)
    def get_bottom_button_rect(self, b_id: str) -> pygame.Rect: return PersuasionLayout.get_bottom_button_rect(b_id)
    def wrap_text(self, text: str, max_chars: int = 36) -> List[str]: return PersuasionLayout.wrap_text(text, max_chars)
    def _get_smart_tooltip_pos(self, mx: int, my: int, tt_w: int, tt_h: int) -> Tuple[int, int]: return PersuasionRenderer.get_smart_tooltip_pos(mx, my, tt_w, tt_h)
    def _get_voice_group_for_preference(self, pref_norm: str) -> str: return "bad" if pref_norm == "WEAK" else ("good" if pref_norm == "RESIST" else "medium")

    def _calculate_negative_impact_severity(self, wedge_val: int, mult: float, pref_norm: str) -> int:
        if mult >= 0.0:
            return 0
        if pref_norm == "RESIST" or wedge_val >= 3:
            return -2
        return -1

    def _update_hover_voice_reaction(self, idx: int) -> None:
        if not self.target_npc or not self.target_npc.revealed_preferences[idx] or self.used_in_round[idx]:
            return
        pref_name, _ = self.target_npc.preferences[idx]
        pref_norm = self._normalize_rating(pref_name)
        vg = self._get_voice_group_for_preference(pref_norm)
        if self.last_played_voice_group != vg:
            self.last_played_voice_group = vg
            sound_manager = self.sm.context.get("sound_manager")
            if sound_manager and hasattr(sound_manager, "play_civ_voice"):
                sound_manager.play_civ_voice(self.target_npc.name, vg, base_volume=0.7)

    def _trigger_enemy_counterspell(self) -> None:
        if not self.target_npc or self.combat_finished:
            return
        counterspells = ["desync.py", "nerf.py", "blinded.py", "dizzy.py", "reduce_damage.py", "data_corrupt.py", "malware_injection.py", "network_jam.py", "signal_hijack.py"]
        chosen = random.choice(counterspells)
        sp = spell_registry.get_spell_by_filename(chosen)
        if sp:
            self._apply_counterspell_effect(sp)

    def _execute_action(self, idx: int) -> None:
        if not self.target_npc or self.combat_finished or self.used_in_round[idx]:
            return
        self.used_in_round[idx] = True
        self.target_npc.revealed_preferences[idx] = True
        wedge_val = self.wedges[idx]
        pref_name, mult = self.target_npc.preferences[idx]
        pref_norm = self._normalize_rating(pref_name)
        skill_factor = 1.0 + (self.speechcraft_level / 100.0) * 0.5
        delta = int(round(wedge_val * mult * skill_factor * 3.5))
        if self.boost_active:
            delta = int(delta * 1.5) if delta > 0 else delta
        if self.nerf_active:
            delta = int(delta * 0.5) if delta < 0 else delta
        self.target_npc.disposition = max(0, min(self.target_npc.max_disposition, self.target_npc.disposition + delta))
        severity = self._calculate_negative_impact_severity(wedge_val, mult, pref_norm)
        if severity < 0:
            gp = self.sm.context.get("glitch_processor")
            if gp:
                gp.trigger_negative_impact(severity, wedge_val=wedge_val)
        jack_msg = f"JACK // EXECUTE [{self.ACTION_NAMES[idx]}] TIER {wedge_val}"
        npc_msg = self._get_npc_reaction_text(pref_norm)
        self.active_banner_anim = {
            "jack_msg": jack_msg,
            "npc_msg": npc_msg,
            "pref_norm": pref_norm,
            "timer": 0.0,
            "dismissing": False,
            "dismiss_timer": 0.0
        }
        sound_manager = self.sm.context.get("sound_manager")
        if sound_manager and hasattr(sound_manager, "play_civ_voice"):
            vg = self._get_voice_group_for_preference(pref_norm)
            sound_manager.play_civ_voice(self.target_npc.name, vg, base_volume=0.8)
        if self.target_npc.disposition >= 95:
            self.combat_finished = True; self.combat_result = "VICTORY"; self.credits += 250
            self._clear_all_counterspells_and_ungrab()
        elif self.target_npc.disposition <= 0 or self.patience <= 0:
            self.combat_finished = True; self.combat_result = "DEFEAT"
            self._clear_all_counterspells_and_ungrab()
        elif all(self.used_in_round):
            self._reset_round_wedges()
            self.round_counter += 1
            if random.random() < 0.35:
                self._trigger_enemy_counterspell()

    def _restart_current_combat(self) -> None:
        if self.target_npc:
            self.target_npc.disposition = self.target_npc.base_disposition
            self.target_npc.revealed_preferences = [False, False, False, False]
        self.combat_finished = False; self.combat_result = None; self.patience = 100.0; self.round_counter = 1
        self.active_banner_anim = None
        self._reset_round_wedges()

    def _play_sfx(self, name: str, vol: float = 0.8) -> None:
        sm = self.sm.context.get("sound_manager")
        if sm: sm.play_spatial(name, 640, 360, 640, 360, base_volume=vol)

    def _exit_minigame(self) -> None:
        pygame.mouse.set_visible(True)
        self._clear_all_counterspells_and_ungrab()
        self._play_sfx("action_cancel", 0.8); self.sm.change_state("WORLD")

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.fade_controller.is_fading: return
        if self.combat_finished:
            self._clear_all_counterspells_and_ungrab()
        elif self.signal_hijack_active and not self.active_banner_anim:
            return
        if self.is_dizzy_effective() and event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._play_sfx("good 3", 0.9)
            if event.button == 1: event.button = 3
            elif event.button == 3: event.button = 1
        if event.type == pygame.MOUSEMOTION and self.is_dizzy_effective():
            rx, ry = getattr(event, "rel", (0, 0))
            dx, dy = ry, rx
            self.virtual_mouse_pos[0] = max(0.0, min(CANVAS_W, self.virtual_mouse_pos[0] + dx))
            self.virtual_mouse_pos[1] = max(0.0, min(CANVAS_H, self.virtual_mouse_pos[1] + dy))
        mx, my = self.get_native_mouse_pos()
        if event.type == pygame.MOUSEMOTION:
            if (mx, my) != self.last_mouse_pos:
                self.last_mouse_pos = (mx, my)
                self.last_mouse_move_time = time.time()
            if self.dragging_action_bar:
                self.action_bar_pos[0] = max(10, min(CANVAS_W - 420, mx - self.action_bar_drag_offset[0]))
                self.action_bar_pos[1] = max(10, min(CANVAS_H - 120, my - self.action_bar_drag_offset[1]))
            if self.dragging_inventory_window:
                self.inventory_window_pos[0] = max(10, min(CANVAS_W - 420, mx - self.inventory_window_drag_offset[0]))
                self.inventory_window_pos[1] = max(10, min(CANVAS_H - 160, my - self.inventory_window_drag_offset[1]))
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if PersuasionOverlays.handle_malware_click(self, mx, my): return
            if self.active_banner_anim and not self.active_banner_anim.get("dismissing", False):
                self.active_banner_anim["dismissing"] = True
                self.active_banner_anim["dismiss_timer"] = 0.0
                self.active_banner_anim["start_jack_x"] = self.active_banner_anim.get("current_jack_x", self.BANNER_CONFIG["jack_target_x"])
                self.active_banner_anim["start_npc_right_x"] = self.active_banner_anim.get("current_npc_right_x", self.BANNER_CONFIG["npc_target_right_x"])
                return
            if self.get_folder_icon_rect().collidepoint(mx, my):
                self.inventory_active = not self.inventory_active
                self._play_sfx("click_target", 0.8)
                return
            if self.get_action_bar_header_rect().collidepoint(mx, my):
                self.dragging_action_bar = True
                self.action_bar_drag_offset = (mx - self.action_bar_pos[0], my - self.action_bar_pos[1])
                return
            if self.inventory_active and self.get_dir_box_rect().collidepoint(mx, my):
                dir_files = self._get_sorted_inventory_files()
                for r_i in range(min(5, len(dir_files) + 1)):
                    item_rect = self.get_dir_item_rect(r_i)
                    if item_rect.collidepoint(mx, my):
                        item_idx = r_i + self.directory_scroll_offset
                        if item_idx == 0:
                            self.inventory_active = False
                            self._play_sfx("action_cancel", 0.6)
                        else:
                            file_i = item_idx - 1
                            if file_i < len(dir_files):
                                fn = dir_files[file_i][0]
                                self.dragged_item = {"filename": fn, "origin": "inventory"}
                                self._play_sfx("click_target", 0.8)
                        return
            for i in range(6):
                s_rect = self.get_action_bar_slot_rect(i)
                if s_rect.collidepoint(mx, my):
                    fn = self.action_bar[i]
                    if fn:
                        self.action_bar[i] = None
                        self.dragged_item = {"filename": fn, "origin": "action_bar", "slot_idx": i}
                        self._play_sfx("click_target", 0.8)
                    return
            if not self.combat_finished and not self.active_banner_anim:
                for i in range(4):
                    if self.get_action_rect(i).collidepoint(mx, my):
                        self._execute_action(i)
                        return
                for b_id in ["BRIBE", "NEXT_NPC", "EXIT"]:
                    if self.get_bottom_button_rect(b_id).collidepoint(mx, my):
                        if b_id == "BRIBE":
                            self.target_npc.disposition = 95
                            self.combat_finished = True
                            self.combat_result = "VICTORY"
                        elif b_id == "NEXT_NPC":
                            self.current_npc_idx = (self.current_npc_idx + 1) % len(self.npcs)
                            self.target_npc = self.npcs[self.current_npc_idx]
                            self._restart_current_combat()
                        elif b_id == "EXIT":
                            self._exit_minigame()
                        return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            for i in range(6):
                s_rect = self.get_action_bar_slot_rect(i)
                if s_rect.collidepoint(mx, my):
                    fn = self.action_bar[i]
                    if fn:
                        self.action_bar[i] = None
                        self.status_message = f"[{fn}] aus Slot #{i+1} entfernt."
                        self._play_sfx("action_cancel", 0.6)
                    return
        if event.type == pygame.MOUSEWHEEL and self.inventory_active:
            if self.get_dir_box_rect().collidepoint(mx, my):
                dir_files = self._get_sorted_inventory_files()
                total_entries = len(dir_files) + 1
                max_scroll = max(0, total_entries - 5)
                self.directory_scroll_offset = max(0, min(max_scroll, self.directory_scroll_offset - event.y))
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging_action_bar:
                self.dragging_action_bar = False
            if self.dragged_item:
                fn = self.dragged_item["filename"]
                origin = self.dragged_item.get("origin")
                orig_slot = self.dragged_item.get("slot_idx")
                target_slot = None
                for i in range(6):
                    if self.get_action_bar_slot_rect(i).collidepoint(mx, my):
                        target_slot = i
                        break
                if target_slot is not None:
                    if origin == "action_bar":
                        if target_slot == orig_slot:
                            self.action_bar[orig_slot] = fn
                            self._activate_spell(fn, orig_slot)
                        else:
                            existing = self.action_bar[target_slot]
                            self.action_bar[target_slot] = fn
                            if orig_slot is not None and existing:
                                self.action_bar[orig_slot] = existing
                    elif origin == "inventory":
                        if fn in self.action_bar:
                            self.status_message = f"[{fn.upper()}] ist bereits in der Action Bar ausgerüstet!"
                            self._play_sfx("action_cancel", 0.6)
                        else:
                            existing = self.action_bar[target_slot]
                            self.action_bar[target_slot] = fn
                            self.status_message = f"[{fn}] in Action Bar Slot #{target_slot+1} ausgerüstet."
                            self._play_sfx("click_target", 0.8)
                elif self.get_dir_box_rect().collidepoint(mx, my):
                    if origin == "action_bar":
                        self.status_message = f"[{fn}] zurück ins Inventar verschoben."
                    elif origin == "inventory":
                        self._equip_spell_to_next_free_slot(fn)
                else:
                    if origin == "action_bar" and orig_slot is not None:
                        self.action_bar[orig_slot] = fn
                self.dragged_item = None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._exit_minigame()
            elif event.key == pygame.K_r and self.combat_finished:
                self._restart_current_combat()
            elif event.key == pygame.K_n and self.combat_finished:
                self.current_npc_idx = (self.current_npc_idx + 1) % len(self.npcs)
                self.target_npc = self.npcs[self.current_npc_idx]
                self._restart_current_combat()
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                idx = event.key - pygame.K_1
                self._execute_action(idx)
            elif event.key in (pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0):
                slot_idx = 0 if event.key == pygame.K_0 else (event.key - pygame.K_5)
                if slot_idx < len(self.action_bar):
                    fn = self.action_bar[slot_idx]
                    if fn:
                        self._activate_spell(fn, slot_idx)

    def update(self, dt: float) -> None:
        self.fade_controller.update(dt)
        try: pygame.event.set_grab(self.is_dizzy_effective())
        except Exception: pass
        if not self.combat_finished and self.target_npc:
            self.patience = max(0.0, self.patience - self.patience_decay_rate * dt)
            if self.patience <= 0:
                self.combat_finished = True; self.combat_result = "DEFEAT"
                self._clear_all_counterspells_and_ungrab()
        if self.blinded_active:
            self.blinded_anim_timer = min(1.0, self.blinded_anim_timer + dt * 3.5)
        if self.is_dizzy_effective() and self.target_npc:
            self.target_npc.disposition = max(0.0, self.target_npc.disposition - 4.0 * dt)
        if self.network_jam_active and random.random() < 0.2:
            gp = self.sm.context.get("glitch_processor")
            if gp and hasattr(gp, "trigger_negative_impact"): gp.trigger_negative_impact(-1, 1)
        if self.malware_injection_active:
            self.malware_spawn_timer += dt
            if self.malware_spawn_timer >= 0.5:
                self.malware_spawn_timer = 0.0
                if len(self.malware_popups) < 5: self._spawn_single_malware_popup()
            if self.target_npc and not self.combat_finished:
                self.target_npc.disposition = max(0.0, self.target_npc.disposition - 4.0 * dt)
        if self.signal_hijack_active:
            PersuasionSpellEngine.update_signal_hijack(self, dt)
        if self.active_banner_anim:
            if not self.active_banner_anim.get("dismissing", False):
                self.active_banner_anim["timer"] += dt
            else:
                self.active_banner_anim["dismiss_timer"] += dt
                if self.active_banner_anim["dismiss_timer"] >= 0.25:
                    self.active_banner_anim = None
        mx, my = self.get_native_mouse_pos()
        self.hovered_action_idx = None
        self.hovered_icon_idx = None
        self.hovered_btn_idx = None
        self.hovered_spell_filename = None
        if not self.combat_finished and not self.active_banner_anim:
            for i in range(4):
                if self.get_action_rect(i).collidepoint(mx, my):
                    self.hovered_action_idx = i
                    self.hovered_icon_idx = i
                    self._update_hover_voice_reaction(i)
                    break
            for b_id in ["BRIBE", "NEXT_NPC", "EXIT"]:
                if self.get_bottom_button_rect(b_id).collidepoint(mx, my):
                    self.hovered_btn_idx = b_id
                    break
            if self.inventory_active:
                dir_files = self._get_sorted_inventory_files()
                for r_i in range(min(5, len(dir_files) + 1)):
                    item_rect = self.get_dir_item_rect(r_i)
                    if item_rect.collidepoint(mx, my):
                        item_idx = r_i + self.directory_scroll_offset
                        if item_idx > 0 and (item_idx - 1) < len(dir_files):
                            self.hovered_spell_filename = dir_files[item_idx - 1][0]
                        break
            for i in range(6):
                s_rect = self.get_action_bar_slot_rect(i)
                if s_rect.collidepoint(mx, my):
                    fn = self.action_bar[i]
                    if fn:
                        self.hovered_spell_filename = fn
                    break

    def draw(self, surface: pygame.Surface) -> None:
        PersuasionRenderer.render_ui(self, surface)

    def update_draw(self) -> None:
        self.draw(self.persuasion_surface)
