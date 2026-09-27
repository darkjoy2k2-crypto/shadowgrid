import time
import pygame
from typing import Any, Tuple
from src.ui.font_manager import font_mgr, GREEN_PHOSPHOR, GREEN_BRIGHT, GREEN_DIM, GREEN_TERMINAL, RED_ALERT, AMBER_WARN, WHITE_TEXT, STEEL_GREY
from src.states.persuasion.persuasion_overlays import PersuasionOverlays

CANVAS_W = 1280
CANVAS_H = 720

class PersuasionRenderer:
    """Rendert die Benutzeroberfläche des Cyberdeck Combat Minigames."""

    @staticmethod
    def get_smart_tooltip_pos(mx: int, my: int, tt_w: int, tt_h: int) -> Tuple[int, int]:
        return PersuasionOverlays.get_smart_tooltip_pos(mx, my, tt_w, tt_h)

    @staticmethod
    def render_ui(state: Any, surface: pygame.Surface) -> None:
        if not surface or not state.target_npc:
            return

        mx, my = state.get_native_mouse_pos()
        surface.fill((8, 14, 12))

        # 1. HEADER PANEL
        header_panel = state.nineslice.render(158, 10)
        surface.blit(header_panel, (10, 10))

        t_surf = font_mgr.render(state._corrupt_text("CYBERDECK // COMBAT PROTOCOL"), color=GREEN_BRIGHT, size="large")
        surface.blit(t_surf, (24, 18))

        status_lbl = state._corrupt_text(f"ZIEL-KNOTEN #{state.current_npc_idx + 1} VON {len(state.npcs)}")
        surface.blit(font_mgr.render(status_lbl, color=GREEN_DIM, size="small"), (24, 46))

        # System Override Bar
        disp_val = state.target_npc.disposition
        disp_max = state.target_npc.max_disposition
        disp_pct = disp_val / 100.0

        bar_x, bar_y, bar_w, bar_h = 680, 14, 570, 24
        pygame.draw.rect(surface, (20, 30, 25), (bar_x, bar_y, bar_w, bar_h))
        fill_w = int(bar_w * disp_pct)
        
        bar_color = GREEN_PHOSPHOR if disp_val >= 60 else (AMBER_WARN if disp_val >= 35 else RED_ALERT)
        if fill_w > 0:
            pygame.draw.rect(surface, bar_color, (bar_x, bar_y, fill_w, bar_h))
        pygame.draw.rect(surface, GREEN_BRIGHT, (bar_x, bar_y, bar_w, bar_h), 1)

        disp_lbl = state._corrupt_text(f"SYSTEM OVERRIDE: {disp_val} / {disp_max}")
        disp_txt = font_mgr.render(disp_lbl, color=WHITE_TEXT, size="small")
        surface.blit(disp_txt, (bar_x + (bar_w - disp_txt.get_width()) // 2, bar_y + 5))

        # Counter-ICE / Trace Bar
        pat_x, pat_y, pat_w, pat_h = 680, 44, 570, 16
        pygame.draw.rect(surface, (20, 20, 20), (pat_x, pat_y, pat_w, pat_h))
        pat_fill = int(pat_w * (state.patience / 100.0))
        if pat_fill > 0:
            pygame.draw.rect(surface, (0, 180, 220), (pat_x, pat_y, pat_fill, pat_h))
        pygame.draw.rect(surface, (60, 80, 100), (pat_x, pat_y, pat_w, pat_h), 1)
        surface.blit(font_mgr.render(state._corrupt_text(f"TRACE-ALERT: {int(state.patience)}%"), color=STEEL_GREY, size="small"), (pat_x - 145, pat_y + 2))

        # 2. CENTER PANEL: 4 COMBAT KATEGORIEN
        for i in range(4):
            rect = state.get_action_rect(i)
            is_hovered = (state.hovered_action_idx == i)
            is_used = state.used_in_round[i]

            wedge_val = state.wedges[i]
            pref_name, mult = state.target_npc.preferences[i]
            pref_norm = state._normalize_rating(pref_name)
            is_revealed = state.target_npc.revealed_preferences[i]
            
            tier_name, tier_desc, icon_filename = state.ATTACK_TIERS[i][min(4, wedge_val)]

            skill_factor = 1.0 + (state.speechcraft_level / 100.0) * 0.5
            projected_delta = int(round(wedge_val * mult * skill_factor * 3.5))
            delta_str = f"+{projected_delta}" if projected_delta >= 0 else f"{projected_delta}"

            if is_used:
                bg_color = (18, 20, 22)
                border_color = (50, 55, 60)
                l1_color = STEEL_GREY
                l3_color = RED_ALERT
            elif is_hovered:
                bg_color = (10, 45, 30)
                border_color = GREEN_BRIGHT
                l1_color = GREEN_BRIGHT
                l3_color = AMBER_WARN
            else:
                bg_color = (12, 28, 22)
                border_color = GREEN_PHOSPHOR
                l1_color = GREEN_PHOSPHOR
                l3_color = AMBER_WARN

            pygame.draw.rect(surface, bg_color, rect)
            pygame.draw.rect(surface, border_color, rect, 1 if not is_hovered else 2)

            icon_x = rect.x + 12
            icon_y = rect.y + 23

            icon_surf = state.attack_icons.get(icon_filename)
            if icon_surf:
                surface.blit(icon_surf, (icon_x, icon_y))
            else:
                pygame.draw.rect(surface, (20, 35, 28), (icon_x, icon_y, 72, 72))
            pygame.draw.rect(surface, border_color, (icon_x - 1, icon_y - 1, 74, 74), 1)

            text_x = rect.x + 98

            category_text = state._corrupt_text(state.ACTION_NAMES[i])
            surface.blit(font_mgr.render(category_text, color=l1_color, size="large"), (text_x, rect.y + 12))

            if state.blinded_active:
                disp_tier_val = "???"
                spell_text = state._corrupt_text("[TIER ???] [BLINDED // OPTIK ÜBERBLENDET]")
            else:
                disp_tier_val = str(wedge_val)
                spell_text = state._corrupt_text(f"[TIER {disp_tier_val}] {tier_name.upper()}")

            surface.blit(font_mgr.render(spell_text, color=WHITE_TEXT if not is_used else STEEL_GREY, size="large"), (text_x, rect.y + 44))

            if is_used:
                l3_text = f"[DEBUG] Resistenz: {pref_norm if is_revealed else '???'} | Status: [ BENUTZT ]"
            elif is_revealed:
                l3_text = f"[DEBUG] Resistenz: {pref_norm} (x{mult}) | Est. Override: {delta_str} | Status: BEREIT"
            else:
                l3_text = f"[DEBUG] Resistenz: ??? [ UNBEKANNT ] | Est. Override: ??? | Status: UNENTDECKT"

            surface.blit(font_mgr.render(state._corrupt_text(l3_text), color=l3_color, size="small"), (text_x, rect.y + 86))

            badge_lbl = font_mgr.render(state._corrupt_text("TIER: "), color=STEEL_GREY if is_used else AMBER_WARN, size="small")
            badge_color = RED_ALERT if state.blinded_active else (WHITE_TEXT if is_used else GREEN_BRIGHT)
            badge_num = font_mgr.render(state._corrupt_text(disp_tier_val), color=badge_color, size="large")
            badge_max = font_mgr.render(state._corrupt_text(" / 4"), color=STEEL_GREY, size="small")

            badge_x = rect.x + 640
            badge_y = rect.y + 8
            surface.blit(badge_lbl, (badge_x, badge_y + 4))
            surface.blit(badge_num, (badge_x + badge_lbl.get_width(), badge_y))
            surface.blit(badge_max, (badge_x + badge_lbl.get_width() + badge_num.get_width(), badge_y + 4))

        if state.blinded_active:
            start_x, start_y = 1195, 155
            anim_t = min(1.0, max(0.0, getattr(state, "blinded_anim_timer", 1.0)))
            t_eased = 1.0 - (1.0 - anim_t) ** 2
            face_sz = 44
            for row_i in range(4):
                row_r = state.get_action_rect(row_i)
                target_x = row_r.x + 690
                target_y = row_r.y + 24
                cx = start_x + (target_x - start_x) * t_eased
                cy = start_y + (target_y - start_y) * t_eased
                fx, fy = int(cx - face_sz // 2), int(cy - face_sz // 2)
                if state.target_npc and state.target_npc.face_surface:
                    mini_face = pygame.transform.smoothscale(state.target_npc.face_surface, (face_sz, face_sz))
                    surface.blit(mini_face, (fx, fy))
                else:
                    pygame.draw.rect(surface, (45, 15, 20), (fx, fy, face_sz, face_sz))
                    fb_t = font_mgr.render("BLIND", color=RED_ALERT, size="small")
                    surface.blit(fb_t, (fx + (face_sz - fb_t.get_width()) // 2, fy + 12))
                pygame.draw.rect(surface, RED_ALERT, (fx - 1, fy - 1, face_sz + 2, face_sz + 2), 2)

        # 3. BOTTOM PANEL
        bottom_box = pygame.Rect(10, 592, 840, 118)
        pygame.draw.rect(surface, (10, 20, 16), bottom_box)
        pygame.draw.rect(surface, GREEN_DIM, bottom_box, 1)

        emo_text = "[ (???) UNBEKANNT ]"
        emo_color = STEEL_GREY

        if state.hovered_action_idx is not None and state.target_npc:
            idx = state.hovered_action_idx
            if state.target_npc.revealed_preferences[idx]:
                pref_raw, _ = state.target_npc.preferences[idx]
                pref_norm = state._normalize_rating(pref_raw)
                emo_text, emo_color = state.EMOTIONS.get(pref_norm, state.EMOTIONS["NEUTRAL"])

        pygame.draw.rect(surface, (15, 25, 20), (20, 600, 220, 50))
        pygame.draw.rect(surface, emo_color, (20, 600, 220, 50), 1)
        surface.blit(font_mgr.render("NET-DIAGNOSTIK:", color=GREEN_DIM, size="small"), (26, 604))
        surface.blit(font_mgr.render(state._corrupt_text(emo_text), color=emo_color, size="small"), (26, 626))

        surface.blit(font_mgr.render(state._corrupt_text(f"CREDITS: {state.credits} Cr"), color=WHITE_TEXT, size="small"), (255, 604))
        surface.blit(font_mgr.render(state._corrupt_text(f"CYBER-LVL: Lvl {state.speechcraft_level}"), color=STEEL_GREY, size="small"), (255, 626))
        surface.blit(font_mgr.render(state._corrupt_text(f"SEQUENZ: #{state.round_counter}"), color=GREEN_BRIGHT, size="small"), (355, 604))
        surface.blit(font_mgr.render(state._corrupt_text(f"TRACE:   {int(state.patience)}%"), color=(0, 180, 220), size="small"), (355, 626))

        surface.blit(font_mgr.render(state._corrupt_text(f"> {state.status_message}"), color=GREEN_BRIGHT, size="small"), (455, 604))
        surface.blit(font_mgr.render("1-4: Angriff | 5-0: Spells | B: Bypass | N: Ziel | ESC: Trennen", color=STEEL_GREY, size="small"), (455, 630))

        btn_data = [
            ("BRIBE", "[ BYPASS ]"),
            ("NEXT_NPC", "[ NEUES ZIEL ]"),
            ("EXIT", "[ DISCONNECT ]")
        ]

        for b_id, b_text in btn_data:
            b_rect = state.get_bottom_button_rect(b_id)
            is_hover = (state.hovered_btn_idx == b_id)
            b_bg = (15, 40, 30) if is_hover else (10, 25, 20)
            b_border = GREEN_BRIGHT if is_hover else GREEN_PHOSPHOR
            b_txt_col = GREEN_BRIGHT if is_hover else GREEN_PHOSPHOR

            pygame.draw.rect(surface, b_bg, b_rect)
            pygame.draw.rect(surface, b_border, b_rect, 1)

            t_surf = font_mgr.render(state._corrupt_text(b_text), color=b_txt_col, size="small")
            surface.blit(t_surf, (b_rect.x + (b_rect.width - t_surf.get_width()) // 2, b_rect.y + 12))

        # 4. RIGHT COLUMN: CHARAKTERBOGEN
        sheet_rect = pygame.Rect(860, 80, 410, 345)
        pygame.draw.rect(surface, (10, 18, 15), sheet_rect)
        pygame.draw.rect(surface, GREEN_PHOSPHOR, sheet_rect, 1)

        surface.blit(font_mgr.render("--- CHARAKTERBOGEN ---", color=GREEN_BRIGHT, size="small"), (875, 90))

        face_x, face_y = 1135, 95
        pygame.draw.rect(surface, (15, 25, 22), (face_x - 2, face_y - 2, 124, 124))
        pygame.draw.rect(surface, GREEN_BRIGHT, (face_x - 2, face_y - 2, 124, 124), 1)

        if state.target_npc.face_surface:
            scaled_face = pygame.transform.smoothscale(state.target_npc.face_surface, (120, 120))
            surface.blit(scaled_face, (face_x, face_y))
        else:
            pygame.draw.rect(surface, (20, 35, 28), (face_x, face_y, 120, 120))
            fb_t = font_mgr.render("NO MATRIX", color=STEEL_GREY, size="small")
            surface.blit(fb_t, (face_x + (120 - fb_t.get_width()) // 2, face_y + 50))

        y_cursor = 108
        name_surf = font_mgr.render(state._corrupt_text(state.target_npc.name), color=WHITE_TEXT, size="medium")
        surface.blit(name_surf, (875, y_cursor))
        y_cursor += 22

        job_lines = state.wrap_text(f"JOB: {state.target_npc.job}", max_chars=30)
        for j_line in job_lines:
            j_surf = font_mgr.render(state._corrupt_text(j_line), color=GREEN_PHOSPHOR, size="small")
            surface.blit(j_surf, (875, y_cursor))
            y_cursor += 16

        y_cursor += 4
        origin_lines = state.wrap_text(f"HERKUNFT: {state.target_npc.origin}", max_chars=30)
        for o_line in origin_lines:
            o_surf = font_mgr.render(state._corrupt_text(o_line), color=STEEL_GREY, size="small")
            surface.blit(o_surf, (875, y_cursor))
            y_cursor += 16

        y_cursor = max(y_cursor + 6, 222)
        pygame.draw.line(surface, GREEN_DIM, (875, y_cursor), (1255, y_cursor), 1)
        y_cursor += 10

        surface.blit(font_mgr.render("SYSTEM-WIDERSTÄNDE & SCHWÄCHEN:", color=GREEN_DIM, size="small"), (875, y_cursor))
        y_cursor += 18

        for act_i in range(4):
            cat_name = state.ACTION_NAMES[act_i]
            if state.target_npc.revealed_preferences[act_i]:
                pref_raw, mult = state.target_npc.preferences[act_i]
                pref_norm = state._normalize_rating(pref_raw)
                _, pref_color = state.EMOTIONS.get(pref_norm, state.EMOTIONS["NEUTRAL"])
                line_str = f"• {cat_name:<8} -> {pref_norm:<9} ({mult:+.1f}x)"
            else:
                pref_color = STEEL_GREY
                line_str = f"• {cat_name:<8} -> ???       [ UNBEKANNT ]"

            surface.blit(font_mgr.render(state._corrupt_text(line_str), color=pref_color, size="small"), (875, y_cursor))
            y_cursor += 18

        # 5. IN-GAME INVENTORY FOLDER WINDOW
        if state.inventory_active:
            dir_box = state.get_dir_box_rect()
            tiles_w = max(2, dir_box.width // 8)
            tiles_h = max(2, dir_box.height // 8)
            panel_surf = state.nineslice.render(tiles_w, tiles_h)
            surface.blit(panel_surf, (dir_box.x, dir_box.y))

            path_str = "/SYS/DECK/FILES/SCRIPTS" if not state.debug_mode else "/SYS/DECK/FILES/SCRIPTS (DEBUG)"
            header_txt = font_mgr.render(state._corrupt_text(path_str), color=GREEN_TERMINAL, size="tiny")
            surface.blit(header_txt, (dir_box.x + 8, dir_box.y + 5))

            pygame.draw.line(surface, (0, 150, 100), (dir_box.x + 8, dir_box.y + 22), (dir_box.x + dir_box.width - 8, dir_box.y + 22), 1)

            dir_files = state._get_sorted_inventory_files()
            total_entries = len(dir_files) + 1

            for r_i in range(min(5, total_entries)):
                item_idx = r_i + state.directory_scroll_offset
                item_rect = state.get_dir_item_rect(r_i)

                pygame.draw.rect(surface, (10, 25, 20), item_rect)
                pygame.draw.rect(surface, (20, 55, 45), item_rect, 1)

                if item_idx == 0:
                    txt = font_mgr.render("/..", color=GREEN_TERMINAL, size="tiny")
                    surface.blit(txt, (item_rect.x + 6, item_rect.y + 3))
                else:
                    file_i = item_idx - 1
                    if file_i < len(dir_files):
                        fn, qty = dir_files[file_i]
                        sp = state.spell_registry.get_spell_by_filename(fn)
                        is_cs = sp.is_counterspell if sp else False

                        is_hover = (state.hovered_spell_filename == fn)
                        if is_hover:
                            pygame.draw.rect(surface, (14, 45, 32), item_rect)
                            pygame.draw.rect(surface, GREEN_BRIGHT, item_rect, 1)

                        if fn == "break_connections.py":
                            display_str = "[⚡] break_connections.py"
                            color = RED_ALERT
                        else:
                            prefix = f"[{qty}] " if qty > 1 else ""
                            tag = " [COUNTER]" if is_cs else ""
                            display_str = f"{prefix}{fn}{tag}"
                            color = GREEN_BRIGHT if not is_cs else AMBER_WARN

                        fn_txt = font_mgr.render(state._corrupt_text(display_str), color=color, size="tiny")
                        surface.blit(fn_txt, (item_rect.x + 6, item_rect.y + 3))

            if total_entries > 5:
                track_x = dir_box.x + dir_box.width - 12
                track_y = dir_box.y + 26
                track_h = 120
                pygame.draw.line(surface, (0, 60, 50), (track_x + 1, track_y), (track_x + 1, track_y + track_h), 2)
                max_scroll = max(1, total_entries - 5)
                thumb_h = max(12, int(track_h * (5 / total_entries)))
                thumb_y = track_y + int((state.directory_scroll_offset / max_scroll) * (track_h - thumb_h))
                thumb_rect = pygame.Rect(track_x, thumb_y, 4, thumb_h)
                pygame.draw.rect(surface, (0, 255, 120), thumb_rect)

        # 6. FOLDER TOGGLE ICON BUTTON
        folder_icon_r = state.get_folder_icon_rect()
        is_icon_hover = folder_icon_r.collidepoint(mx, my)
        bg_col = (15, 45, 30) if (is_icon_hover or state.inventory_active) else (5, 20, 15)
        border_col = (0, 255, 160) if (is_icon_hover or state.inventory_active) else (0, 140, 90)

        pygame.draw.rect(surface, bg_col, folder_icon_r)
        pygame.draw.rect(surface, border_col, folder_icon_r, 1)
        folder_c = GREEN_PHOSPHOR if (is_icon_hover or state.inventory_active) else (0, 200, 120)

        pygame.draw.rect(surface, folder_c, (folder_icon_r.x + 6, folder_icon_r.y + 6, 14, 5))
        body_r = pygame.Rect(folder_icon_r.x + 6, folder_icon_r.y + 11, 38, 22)
        pygame.draw.rect(surface, (8, 28, 20), body_r)
        pygame.draw.rect(surface, folder_c, body_r, 1)
        pygame.draw.line(surface, folder_c, (folder_icon_r.x + 8, folder_icon_r.y + 17), (folder_icon_r.x + 40, folder_icon_r.y + 17), 1)

        # 7. FLOATING ACTION BAR UI WINDOW
        ab_full = state.get_action_bar_full_rect()
        ab_header = state.get_action_bar_header_rect()

        pygame.draw.rect(surface, (10, 24, 18), ab_full)
        pygame.draw.rect(surface, GREEN_BRIGHT if state.dragging_action_bar else GREEN_PHOSPHOR, ab_full, 2)

        header_bg = (15, 45, 32) if state.dragging_action_bar else (12, 32, 22)
        pygame.draw.rect(surface, header_bg, ab_header)
        pygame.draw.line(surface, GREEN_PHOSPHOR, (ab_header.x, ab_header.y + ab_header.height - 1), (ab_header.x + ab_header.width, ab_header.y + ab_header.height - 1), 1)

        ab_title = font_mgr.render("≡ ACTION BAR // HOTKEYS [5-0] (DRAG HEADER) ≡", color=GREEN_BRIGHT, size="small")
        surface.blit(ab_title, (ab_header.x + (ab_header.width - ab_title.get_width()) // 2, ab_header.y + 4))

        for s_i in range(6):
            slot_rect = state.get_action_bar_slot_rect(s_i)
            fn = state.action_bar[s_i]
            is_slot_hover = (state.hovered_spell_filename == fn and fn is not None)
            border_c = GREEN_BRIGHT if is_slot_hover else GREEN_PHOSPHOR

            if fn == "biohacker.py" and state.biohacker_flashing:
                if int(time.time() * 4) % 2 == 0:
                    border_c = AMBER_WARN

            pygame.draw.rect(surface, (12, 24, 18), slot_rect)
            pygame.draw.rect(surface, border_c, slot_rect, 1 if not is_slot_hover else 2)

            hk_txt = font_mgr.render(str(s_i + 5 if s_i < 5 else 0), color=AMBER_WARN, size="small")
            surface.blit(hk_txt, (slot_rect.x + 4, slot_rect.y + 2))

            if fn:
                sp = state.spell_registry.get_spell_by_filename(fn)
                icon_key = sp.icon_key if sp else (fn.replace(".py", ""))
                icon_surf = state.spell_icons.get(icon_key)

                if icon_surf:
                    surface.blit(icon_surf, (slot_rect.x + 5, slot_rect.y + 5))
                else:
                    pygame.draw.rect(surface, (20, 45, 30), (slot_rect.x + 5, slot_rect.y + 5, 48, 48))
                    t_short = font_mgr.render(fn[:4].upper(), color=WHITE_TEXT, size="small")
                    surface.blit(t_short, (slot_rect.x + 8, slot_rect.y + 20))

                qty = state.inventory.get(fn, 1)
                if qty >= 1:
                    badge_color = GREEN_BRIGHT if qty > 1 else AMBER_WARN
                    badge_txt = font_mgr.render(f"x{qty}", color=badge_color, size="small")
                    surface.blit(badge_txt, (slot_rect.x + slot_rect.width - badge_txt.get_width() - 3, slot_rect.y + slot_rect.height - 16))

        # 8. OVERLAYS & TOOLTIPS
        PersuasionOverlays.draw_cursor_tooltip(state, surface)
        PersuasionOverlays.draw_spell_hintbox(state, surface)
        PersuasionOverlays.draw_dragged_item(state, surface)
        PersuasionOverlays.draw_malware_popups(state, surface)
        PersuasionOverlays.draw_cinematic_banners(state, surface)
        PersuasionOverlays.draw_network_jam_overlay(state, surface)
        PersuasionOverlays.draw_result_overlay(state, surface)

        state.fade_controller.draw_overlay(surface)

        # 9. VIRTUAL CURSOR RENDER
        mx, my = state.get_native_mouse_pos()
        is_dizzy = getattr(state, "is_dizzy_effective", lambda: False)()
        if hasattr(state, "cursor_img") and state.cursor_img:
            if is_dizzy:
                pygame.draw.circle(surface, RED_ALERT, (mx + 8, my + 8), 12, 1)
            surface.blit(state.cursor_img, (mx, my))
        else:
            cur_col = RED_ALERT if is_dizzy else GREEN_BRIGHT
            pygame.draw.line(surface, cur_col, (mx - 6, my), (mx + 6, my), 2)
            pygame.draw.line(surface, cur_col, (mx, my - 6), (mx, my + 6), 2)

    @staticmethod
    def draw_spell_hintbox(state: Any, surface: pygame.Surface) -> None:
        PersuasionOverlays.draw_spell_hintbox(state, surface)

    @staticmethod
    def draw_cursor_tooltip(state: Any, surface: pygame.Surface) -> None:
        PersuasionOverlays.draw_cursor_tooltip(state, surface)

    @staticmethod
    def draw_dragged_item(state: Any, surface: pygame.Surface) -> None:
        PersuasionOverlays.draw_dragged_item(state, surface)

    @staticmethod
    def draw_malware_popups(state: Any, surface: pygame.Surface) -> None:
        PersuasionOverlays.draw_malware_popups(state, surface)

    @staticmethod
    def draw_result_overlay(state: Any, surface: pygame.Surface) -> None:
        PersuasionOverlays.draw_result_overlay(state, surface)

    @staticmethod
    def draw_cinematic_banners(state: Any, surface: pygame.Surface) -> None:
        PersuasionOverlays.draw_cinematic_banners(state, surface)
