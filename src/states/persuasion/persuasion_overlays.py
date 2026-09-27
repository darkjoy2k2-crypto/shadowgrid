import time
import random
import pygame
from typing import Any, Tuple
from src.ui.font_manager import font_mgr, GREEN_PHOSPHOR, GREEN_BRIGHT, GREEN_DIM, GREEN_TERMINAL, RED_ALERT, AMBER_WARN, WHITE_TEXT, STEEL_GREY

CANVAS_W = 1280
CANVAS_H = 720

class PersuasionOverlays:
    """Zeichnet Overlays, Popups, Banners und Tooltips für das Cyberdeck Combat Minigame."""

    @staticmethod
    def get_smart_tooltip_pos(mx: int, my: int, tt_w: int, tt_h: int) -> Tuple[int, int]:
        OFFSET_X = 15
        OFFSET_Y = 15

        tt_x = mx + OFFSET_X
        tt_y = my + OFFSET_Y

        if tt_x + tt_w > CANVAS_W - 10:
            if mx - tt_w - OFFSET_X >= 10:
                tt_x = mx - tt_w - OFFSET_X
            else:
                tt_x = CANVAS_W - tt_w - 10

        if tt_y + tt_h > CANVAS_H - 10:
            if my - tt_h - OFFSET_Y >= 10:
                tt_y = my - tt_h - OFFSET_Y
            else:
                tt_y = CANVAS_H - tt_h - 10

        cursor_box = pygame.Rect(mx - 4, my - 4, 24, 24)
        tt_rect = pygame.Rect(tt_x, tt_y, tt_w, tt_h)

        if tt_rect.colliderect(cursor_box):
            if mx - tt_w - OFFSET_X >= 10:
                tt_x = mx - tt_w - OFFSET_X
            elif my - tt_h - OFFSET_Y >= 10:
                tt_y = my - tt_h - OFFSET_Y

        tt_x = max(10, min(CANVAS_W - tt_w - 10, tt_x))
        tt_y = max(10, min(CANVAS_H - tt_h - 10, tt_y))

        return tt_x, tt_y

    @staticmethod
    def draw_spell_hintbox(state: Any, surface: pygame.Surface) -> None:
        if not state.hovered_spell_filename or state.dragged_item or state.active_banner_anim is not None:
            return

        if time.time() - state.last_mouse_move_time < 1.0:
            return

        fn = state.hovered_spell_filename
        mx, my = state.get_native_mouse_pos()

        if fn == "break_connections.py":
            name_str = "[BREAK_CONNECTIONS.PY]"
            desc_str = "Trennt sofort alle Verbindungen und bricht den Kampf ohne Strafen ab."
            is_counter = False
            icon_surf = None
        else:
            sp = state.spell_registry.get_spell_by_filename(fn)
            if not sp:
                return
            name_str = f"[{sp.filename.upper()}] {sp.name}"
            desc_str = sp.description
            is_counter = sp.is_counterspell
            icon_surf = state.spell_icons.get(sp.icon_key)

        title_surf = font_mgr.render(state._corrupt_text(name_str), color=WHITE_TEXT, size="small")
        badge_type = "[GEGENSPELL / COUNTER]" if is_counter else "[JACK SCRIPT]"
        badge_c = RED_ALERT if is_counter else GREEN_BRIGHT
        badge_surf = font_mgr.render(badge_type, color=badge_c, size="small")

        wrapped = state.wrap_text(desc_str, max_chars=44)
        max_desc_w = max(font_mgr.render(l, size="small").get_width() for l in wrapped) if wrapped else 0

        content_w = max(title_surf.get_width() + 68, badge_surf.get_width() + 68, max_desc_w + 20)
        tt_w = max(420, min(520, content_w + 20))
        tt_h = 54 + len(wrapped) * 16 + 8

        tt_x, tt_y = PersuasionOverlays.get_smart_tooltip_pos(mx, my, tt_w, tt_h)

        tt_rect = pygame.Rect(tt_x, tt_y, tt_w, tt_h)
        border_c = RED_ALERT if is_counter else GREEN_BRIGHT
        bg_c = (15, 25, 30) if not is_counter else (30, 15, 18)

        pygame.draw.rect(surface, bg_c, tt_rect)
        pygame.draw.rect(surface, border_c, tt_rect, 2)

        icon_x = tt_x + 10
        icon_y = tt_y + 10
        if icon_surf:
            surface.blit(icon_surf, (icon_x, icon_y))
        else:
            pygame.draw.rect(surface, (25, 45, 35), (icon_x, icon_y, 48, 48))

        text_x = tt_x + 68
        surface.blit(title_surf, (text_x, tt_y + 10))
        surface.blit(badge_surf, (text_x, tt_y + 28))

        pygame.draw.line(surface, border_c, (tt_x + 10, tt_y + 50), (tt_x + tt_w - 10, tt_y + 50), 1)

        ty = tt_y + 56
        for line in wrapped:
            line_surf = font_mgr.render(state._corrupt_text(line), color=STEEL_GREY, size="small")
            surface.blit(line_surf, (tt_x + 10, ty))
            ty += 16

    @staticmethod
    def draw_cursor_tooltip(state: Any, surface: pygame.Surface) -> None:
        if state.hovered_icon_idx is None or state.active_banner_anim is not None:
            return

        if time.time() - state.last_mouse_move_time < 1.0:
            return
        
        idx = state.hovered_icon_idx
        if state.used_in_round[idx]:
            return

        wedge_val = state.wedges[idx]
        _, tier_desc, _ = state.ATTACK_TIERS[idx][min(4, wedge_val)]

        mx, my = state.get_native_mouse_pos()
        wrapped = state.wrap_text(f"\"{tier_desc}\"", max_chars=44)
        max_w = max(font_mgr.render(l, size="small").get_width() for l in wrapped) if wrapped else 0

        tt_w = max(340, min(500, max_w + 24))
        tt_h = 16 + len(wrapped) * 16

        tt_x, tt_y = PersuasionOverlays.get_smart_tooltip_pos(mx, my, tt_w, tt_h)

        tt_rect = pygame.Rect(tt_x, tt_y, tt_w, tt_h)
        pygame.draw.rect(surface, (8, 22, 18), tt_rect)
        pygame.draw.rect(surface, GREEN_BRIGHT, tt_rect, 1)

        ty = tt_y + 8
        for line in wrapped:
            surface.blit(font_mgr.render(state._corrupt_text(line), color=WHITE_TEXT, size="small"), (tt_x + 10, ty))
            ty += 16

    @staticmethod
    def draw_dragged_item(state: Any, surface: pygame.Surface) -> None:
        if not state.dragged_item:
            return

        mx, my = state.get_native_mouse_pos()
        fn = state.dragged_item["filename"]

        sp = state.spell_registry.get_spell_by_filename(fn)
        icon_key = sp.icon_key if sp else fn.replace(".py", "")
        icon_surf = state.spell_icons.get(icon_key)

        drag_box = pygame.Rect(mx - 24, my - 24, 48, 48)
        pygame.draw.rect(surface, (10, 45, 30), drag_box)
        pygame.draw.rect(surface, GREEN_BRIGHT, drag_box, 2)

        if icon_surf:
            surface.blit(icon_surf, (drag_box.x, drag_box.y))
        else:
            t_short = font_mgr.render(fn[:4].upper(), color=WHITE_TEXT, size="small")
            surface.blit(t_short, (drag_box.x + 4, drag_box.y + 14))

    @staticmethod
    def draw_malware_popups(state: Any, surface: pygame.Surface) -> None:
        for pop in state.malware_popups:
            p_rect = pop["rect"]
            pygame.draw.rect(surface, (35, 10, 15), p_rect)
            pygame.draw.rect(surface, RED_ALERT, p_rect, 2)

            header_rect = pygame.Rect(p_rect.x, p_rect.y, p_rect.width, 26)
            pygame.draw.rect(surface, (200, 30, 40), header_rect)

            surface.blit(font_mgr.render(pop["title"], color=WHITE_TEXT, size="small"), (p_rect.x + 10, p_rect.y + 4))

            close_rect = pygame.Rect(p_rect.x + p_rect.width - 24, p_rect.y + 3, 20, 20)
            pygame.draw.rect(surface, (255, 80, 80), close_rect)
            surface.blit(font_mgr.render("X", color=WHITE_TEXT, size="small"), (close_rect.x + 5, close_rect.y + 2))

            wrapped = state.wrap_text(pop["text"], max_chars=30)
            ty = p_rect.y + 36
            for line in wrapped:
                surface.blit(font_mgr.render(line, color=WHITE_TEXT, size="small"), (p_rect.x + 15, ty))
                ty += 18

            ok_w, ok_h = 90, 26
            ok_x = p_rect.x + (p_rect.width - ok_w) // 2
            ok_y = p_rect.y + p_rect.height - 34
            ok_rect = pygame.Rect(ok_x, ok_y, ok_w, ok_h)
            pygame.draw.rect(surface, (180, 25, 35), ok_rect)
            pygame.draw.rect(surface, RED_ALERT, ok_rect, 1)
            ok_txt = font_mgr.render("[ OK ]", color=WHITE_TEXT, size="small")
            surface.blit(ok_txt, (ok_x + (ok_w - ok_txt.get_width()) // 2, ok_y + 5))

    @staticmethod
    def spawn_single_malware_popup(state: Any) -> None:
        titles = ["SYSTEM_OVERFLOW.EXE", "ICE_CORRUPTION_ALERT", "CRITICAL_DECK_ERROR", "ACCESS_VIOLATION_0x8F", "MALWARE_STACK_TRACE"]
        texts = ["DECK RESOURCE OVERFLOW! PURGE IMMEDIATELY.", "COUNTER-ICE CORRUPTING MEMORY STACK!", "UNAUTHORIZED MEMORY ACCESS DETECTED!", "WARNING: KERNEL BUFFER EXCEEDED!"]
        w, h = 320, 150
        x, y = random.randint(30, CANVAS_W - w - 30), random.randint(40, CANVAS_H - h - 40)
        state.malware_popups.append({"rect": pygame.Rect(x, y, w, h), "title": random.choice(titles), "text": random.choice(texts)})

    @staticmethod
    def handle_malware_click(state: Any, mx: int, my: int) -> bool:
        for i in range(len(state.malware_popups) - 1, -1, -1):
            pop = state.malware_popups[i]
            p_rect = pop["rect"]
            if p_rect.collidepoint(mx, my):
                ok_rect = pygame.Rect(p_rect.x + (p_rect.width - 90) // 2, p_rect.y + p_rect.height - 34, 90, 26)
                close_rect = pygame.Rect(p_rect.x + p_rect.width - 24, p_rect.y + 3, 20, 20)
                if ok_rect.collidepoint(mx, my) or close_rect.collidepoint(mx, my):
                    state.malware_popups.pop(i)
                    state._play_sfx("click_target", 0.8)
                    if state.malware_injection_active:
                        PersuasionOverlays.spawn_single_malware_popup(state)
                return True
        return False

    @staticmethod
    def draw_result_overlay(state: Any, surface: pygame.Surface) -> None:
        if not state.combat_finished or not state.combat_result or not state.target_npc:
            return

        box_w, box_h = 780, 270
        box_x = (CANVAS_W - box_w) // 2
        box_y = (CANVAS_H - box_h) // 2

        overlay_bg = pygame.Surface((CANVAS_W, CANVAS_H), pygame.SRCALPHA)
        overlay_bg.fill((0, 0, 0, 175))
        surface.blit(overlay_bg, (0, 0))

        card_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        
        if state.combat_result == "VICTORY":
            bg_col = (10, 48, 28, 248)
            border_col = (0, 255, 128, 255)
            title_text = "🏆 SYSTEM OVERRIDE ERFOLGREICH 🏆"
            title_color = GREEN_BRIGHT
            sub_text = f"ZIEL-KNOTEN [{state.target_npc.name.upper()}] VOLLSTÄNDIG ÜBERNOMMEN!"
            stats_text = f"REWARD: +250 CREDITS   |   CYBER-LEVEL: {state.speechcraft_level}"
            hint_text = "[N] NÄCHSTES ZIEL    [R] KAMPF RESTART    [ESC] BEENDEN"
        else:
            bg_col = (48, 12, 18, 248)
            border_col = (255, 60, 60, 255)
            title_text = "⚠️ COMBAT PROTOKOLL FEHLGESCHLAGEN ⚠️"
            title_color = RED_ALERT
            sub_text = f"COUNTER-ICE IMMUN-REAKTION VON [{state.target_npc.name.upper()}] HAT DECK ÜBERRANNT!"
            stats_text = f"TRACE-ALERT: 100%   |   OVERRIDE GESCHEITERT"
            hint_text = "[R] KAMPF NEUSTARTEN    [N] NÄCHSTES ZIEL    [ESC] BEENDEN"

        pygame.draw.rect(surface, bg_col, card_rect)
        pygame.draw.rect(surface, border_col, card_rect, 3)

        cy = box_y + 24
        t_surf = font_mgr.render(title_text, color=title_color, size="large")
        surface.blit(t_surf, (box_x + (box_w - t_surf.get_width()) // 2, cy))
        cy += 38

        sub_surf = font_mgr.render(sub_text, color=WHITE_TEXT, size="medium")
        surface.blit(sub_surf, (box_x + (box_w - sub_surf.get_width()) // 2, cy))
        cy += 34

        pygame.draw.line(surface, border_col, (box_x + 30, cy), (box_x + box_w - 30, cy), 1)
        cy += 22

        st_surf = font_mgr.render(stats_text, color=AMBER_WARN, size="medium")
        surface.blit(st_surf, (box_x + (box_w - st_surf.get_width()) // 2, cy))
        cy += 44

        h_surf = font_mgr.render(hint_text, color=GREEN_PHOSPHOR, size="medium")
        surface.blit(h_surf, (box_x + (box_w - h_surf.get_width()) // 2, cy))

    @staticmethod
    def draw_cinematic_banners(state: Any, surface: pygame.Surface) -> None:
        if not state.active_banner_anim:
            return

        anim = state.active_banner_anim
        t = anim["timer"]
        cfg = state.BANNER_CONFIG
        is_cs = anim.get("is_counterspell", False)

        jack_lines = state.wrap_text(anim["jack_msg"], max_chars=cfg["max_chars"])
        npc_lines = state.wrap_text(anim["npc_msg"], max_chars=cfg["max_chars"])

        jack_banner_h = 24 + len(jack_lines) * 26
        npc_banner_h = 24 + len(npc_lines) * 26

        if not is_cs:
            jack_target_y = 210 - jack_banner_h
            npc_target_y = 260
        else:
            npc_target_y = 140
            jack_target_y = 360

        if not anim.get("dismissing", False):
            jack_t = min(1.0, t / 0.35)
            jack_ease = 1.0 - (1.0 - jack_t) ** 3
            jack_x = int(cfg["jack_start_x"] + (cfg["jack_target_x"] - cfg["jack_start_x"]) * jack_ease)
            jack_y = jack_target_y

            npc_t = min(1.0, max(0.0, (t - 0.2) / 0.35))
            npc_ease = 1.0 - (1.0 - npc_t) ** 3
            npc_right_x = int(cfg["npc_start_right_x"] - (cfg["npc_start_right_x"] - cfg["npc_target_right_x"]) * npc_ease)
            npc_y = npc_target_y

            anim["current_jack_x"] = jack_x
            anim["current_npc_right_x"] = npc_right_x
        else:
            dt_fly = anim.get("dismiss_timer", 0.0) / 0.25
            fly_ratio = min(1.0, dt_fly)
            fly_ease = fly_ratio ** 2

            start_jx = anim.get("start_jack_x", cfg["jack_target_x"])
            start_nrx = anim.get("start_npc_right_x", cfg["npc_target_right_x"])

            jack_x = int(start_jx + (cfg["jack_exit_x"] - start_jx) * fly_ease)
            jack_y = jack_target_y

            npc_right_x = int(start_nrx - (start_nrx - cfg["npc_exit_right_x"]) * fly_ease)
            npc_y = npc_target_y

        max_npc_txt_w = max(font_mgr.render(nl, size="large").get_width() for nl in npc_lines)
        npc_banner_w = min(cfg["banner_max_w"], max_npc_txt_w + 36)
        npc_x = npc_right_x - npc_banner_w

        banner_surf = pygame.Surface((CANVAS_W, CANVAS_H), pygame.SRCALPHA)

        jack_rect = pygame.Rect(jack_x, jack_y, cfg["banner_max_w"], jack_banner_h)
        jack_bg = (10, 45, 30, 240) if not is_cs else (40, 15, 20, 240)
        jack_border = (0, 255, 128, 255) if not is_cs else (255, 60, 60, 255)

        pygame.draw.rect(banner_surf, jack_bg, jack_rect)
        pygame.draw.rect(banner_surf, jack_border, jack_rect, 2)
        
        ty = jack_y + 12
        for jl in jack_lines:
            j_txt = font_mgr.render(jl, color=GREEN_BRIGHT if not is_cs else RED_ALERT, size="large")
            banner_surf.blit(j_txt, (jack_x + 18, ty))
            ty += 26

        if t >= 0.2 or anim.get("dismissing", False):
            pref_norm = anim["pref_norm"]
            bg_col = (45, 15, 20, 240) if (pref_norm == "RESIST" or is_cs) else (15, 35, 45, 240)
            border_col = (255, 60, 60, 255) if (pref_norm == "RESIST" or is_cs) else (0, 220, 255, 255)
            txt_col = RED_ALERT if (pref_norm == "RESIST" or is_cs) else WHITE_TEXT

            npc_rect = pygame.Rect(npc_x, npc_y, npc_banner_w, npc_banner_h)
            pygame.draw.rect(banner_surf, bg_col, npc_rect)
            pygame.draw.rect(banner_surf, border_col, npc_rect, 2)

            ty = npc_y + 12
            for nl in npc_lines:
                n_txt = font_mgr.render(nl, color=txt_col, size="large")
                banner_surf.blit(n_txt, (npc_right_x - 18 - n_txt.get_width(), ty))
                ty += 26

        surface.blit(banner_surf, (0, 0))

    @staticmethod
    def draw_network_jam_overlay(state: Any, surface: pygame.Surface) -> None:
        if not getattr(state, "network_jam_active", False):
            return

        flicker_alpha = random.randint(6, 18)
        overlay = pygame.Surface((CANVAS_W, CANVAS_H), pygame.SRCALPHA)
        tint_color = (15, random.randint(140, 210), 35, flicker_alpha)
        overlay.fill(tint_color)

        for _ in range(random.randint(1, 2)):
            gy = random.randint(0, CANVAS_H - 10)
            gh = random.randint(1, 3)
            band = pygame.Surface((CANVAS_W, gh), pygame.SRCALPHA)
            band.fill((0, 255, 128, random.randint(15, 40)))
            overlay.blit(band, (0, gy))

        surface.blit(overlay, (0, 0))

