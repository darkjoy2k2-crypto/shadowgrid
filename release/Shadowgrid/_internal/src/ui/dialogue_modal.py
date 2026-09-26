import os
import pygame
from typing import Dict, Any, List, Optional, Tuple
from src.ui.font_manager import font_mgr, RED_ALERT, WHITE_TEXT, GREEN_TERMINAL, AMBER_WARN, STEEL_GREY

class DialogueModal:
    """
    Erweitertes Cyberpunk-Dialog- & Profil-Analyse-Fenster.
    Features:
    1. Pop-out Profilbilder (ragen über den Fensterrahmen hinaus).
    2. Namen in soliden Cyber-Rahmen mit dunklem Hintergrund & Unterstreichung.
    3. Zentrierte Tab-Buttons (DIALOGUE & BACKGROUND) in der Titlebar.
    4. Scrollbare Chat-Historie mit Mausrad & Scrollbar.
    5. Links- vs. Rechtsbündigkeit (Jack links, Zivilist rechts).
    6. Von unten nach oben gestackte Antwort-Buttons (kein leerer Abstand am unteren Rand!).
    """
    def __init__(self) -> None:
        self.active = False
        self.civ_node = None
        self.is_sentinel = False
        self.dialogue_tree = {}
        self.current_node_id = "start"
        self.active_tab = "DIALOGUE" # "DIALOGUE" oder "BACKGROUND"
        
        from src.ui.portrait_box import PortraitBox
        self.jack_portrait = PortraitBox(width=64, height=64)
        self.civ_portrait_surf: Optional[pygame.Surface] = None
        
        self.conversation_history: List[Dict[str, Any]] = []
        self.scroll_offset = 0
        self.max_scroll = 0
        
        self.tab_dialogue_rect = pygame.Rect(0, 0, 0, 0)
        self.tab_bg_rect = pygame.Rect(0, 0, 0, 0)
        self.choice_rects: List[Tuple[pygame.Rect, Dict[str, Any]]] = []
        self.scrollbar_thumb_rect = pygame.Rect(0, 0, 0, 0)

    def open(self, civ_node: Any, is_sentinel: bool = False) -> None:
        from src.data.dialogue_data import get_dialogue_tree_for_node
        self.active = True
        self.civ_node = civ_node
        self.is_sentinel = is_sentinel or hasattr(civ_node, 'nervousness_level')
        self.active_tab = "DIALOGUE"
        self.current_node_id = "start"
        self.scroll_offset = 0
        self.max_scroll = 0
        
        if self.civ_node and self.is_sentinel:
            setattr(self.civ_node, 'ignore_timer', max(getattr(self.civ_node, 'ignore_timer', 0.0), 2.0))
        
        c_pic = getattr(civ_node, 'profile_pic', '')
        self.dialogue_tree = get_dialogue_tree_for_node(civ_node, is_sentinel)
            
        # Zivilisten-Bild laden
        self.civ_portrait_surf = None
        if c_pic and os.path.exists(c_pic):
            try:
                raw_img = pygame.image.load(c_pic).convert_alpha()
                self.civ_portrait_surf = pygame.transform.scale(raw_img, (56, 56))
            except Exception:
                self.civ_portrait_surf = None

        # Start-Dialog in die Historie laden
        self.conversation_history = []
        start_node = self.dialogue_tree.get("start", {})
        if start_node:
            self.conversation_history.append({
                "speaker": start_node.get("speaker", "CIVILIAN"),
                "text": start_node.get("text", "..."),
                "jack_emotion": start_node.get("jack_emotion", 6)
            })

    def goto_node(self, node_id: str) -> None:
        """Wechselt direkt zu einem bestimmten Dialog-Knoten und fügt diesen in die Historie ein."""
        self.active = True
        self.current_node_id = node_id
        node_data = self.dialogue_tree.get(node_id, {})
        if node_data:
            self.conversation_history.append({
                "speaker": node_data.get("speaker", "CIVILIAN"),
                "text": node_data.get("text", "..."),
                "jack_emotion": node_data.get("jack_emotion", 14)
            })
            self.scroll_offset = self.max_scroll

    def close(self) -> None:
        if self.civ_node and (self.is_sentinel or hasattr(self.civ_node, 'nervousness_level')):
            setattr(self.civ_node, 'ignore_timer', max(getattr(self.civ_node, 'ignore_timer', 0.0), 25.0))
        self.active = False
        self.civ_node = None
        self.is_sentinel = False
        self.conversation_history = []

    def _wrap_text_to_lines(self, text: str, max_chars_per_line: int) -> List[str]:
        words = text.split(" ")
        lines = []
        current_line = []
        current_len = 0
        
        for word in words:
            word_len = len(word)
            if current_len + word_len + (1 if current_line else 0) <= max_chars_per_line:
                current_line.append(word)
                current_len += word_len + (1 if current_line else 1)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_len = word_len
                
        if current_line:
            lines.append(" ".join(current_line))
            
        return lines

    def _draw_underlined_text(self, surface: pygame.Surface, text: str, x: int, y: int, color: Tuple[int, int, int], size: str = "tiny", align: str = "left") -> pygame.Rect:
        """Rendert Text mit einer knackigen Pixel-Unterstreichung darunter."""
        txt_surf = font_mgr.render(text, color=color, size=size)
        w = txt_surf.get_width()
        h = txt_surf.get_height()
        
        if align == "right":
            draw_x = x - w
        elif align == "center":
            draw_x = x - (w // 2)
        else:
            draw_x = x
            
        surface.blit(txt_surf, (draw_x, y))
        pygame.draw.line(surface, color, (draw_x, y + h + 1), (draw_x + w - 1, y + h + 1), 1)
        return pygame.Rect(draw_x, y, w, h + 2)

    def handle_scroll(self, y_delta: int) -> None:
        """Scrollt in der Chat-Historie nach oben (y_delta > 0) oder unten (y_delta < 0)."""
        if not self.active or self.active_tab != "DIALOGUE":
            return
        self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset - y_delta * 16))

    def draw(self, surface: pygame.Surface, native_mx: int, native_my: int) -> None:
        if not self.active or not self.civ_node:
            return
            
        screen_w = surface.get_width()
        screen_h = surface.get_height()
        
        # Abdunkelndes Overlay (blockiert optisch & logisch die Spielwelt)
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((5, 10, 15, 210))
        surface.blit(overlay, (0, 0))
        
        # Hauptfenster (580 x 290)
        panel_w = 580
        panel_h = 290
        panel_x = (screen_w - panel_w) // 2
        panel_y = (screen_h - panel_h) // 2 + 10 # Leicht nach unten versetzt für herausragende Porträts
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(surface, (10, 15, 22), panel_rect)
        pygame.draw.rect(surface, (0, 200, 150), panel_rect, 2)
        
        # Top Header Banner
        header_rect = pygame.Rect(panel_x, panel_y, panel_w, 24)
        pygame.draw.rect(surface, (0, 40, 50), header_rect)
        pygame.draw.line(surface, (0, 200, 150), (panel_x, panel_y + 24), (panel_x + panel_w, panel_y + 24), 1)
        
        # Tabs ÜBER der Titlebar
        tab_w1 = 110
        tab_w2 = 125
        gap = 12
        total_tabs_w = tab_w1 + tab_w2 + gap
        tab_start_x = panel_x + (panel_w - total_tabs_w) // 2
        
        self.tab_dialogue_rect = pygame.Rect(tab_start_x, panel_y - 20, tab_w1, 20)
        self.tab_bg_rect = pygame.Rect(tab_start_x + tab_w1 + gap, panel_y - 20, tab_w2, 20)
        
        col_dia = (0, 120, 90) if self.active_tab == "DIALOGUE" else (20, 30, 40)
        col_bg = (0, 120, 90) if self.active_tab == "BACKGROUND" else (20, 30, 40)
        
        pygame.draw.rect(surface, col_dia, self.tab_dialogue_rect)
        pygame.draw.rect(surface, (0, 255, 200) if self.active_tab == "DIALOGUE" else STEEL_GREY, self.tab_dialogue_rect, 1)
        txt_dia = font_mgr.render("[ DIALOGUE ]", color=WHITE_TEXT, size="tiny")
        surface.blit(txt_dia, (self.tab_dialogue_rect.x + 10, self.tab_dialogue_rect.y + 4))
        
        pygame.draw.rect(surface, col_bg, self.tab_bg_rect)
        pygame.draw.rect(surface, (0, 255, 200) if self.active_tab == "BACKGROUND" else STEEL_GREY, self.tab_bg_rect, 1)
        txt_bg = font_mgr.render("[ BACKGROUND ]", color=AMBER_WARN if self.active_tab == "BACKGROUND" else WHITE_TEXT, size="tiny")
        surface.blit(txt_bg, (self.tab_bg_rect.x + 8, self.tab_bg_rect.y + 4))
        
        # Jack's Name: Links geankert in 1 Zeile in der Titlebar neben seinem Porträt
        self._draw_underlined_text(surface, "JACK", panel_x + 56, panel_y + 6, color=GREEN_TERMINAL, size="tiny", align="left")
        
        # Pop-out Links: Jack Porträt (ragt 14px nach oben & links heraus!)
        jack_last_emotion = 6
        if self.conversation_history:
            jack_last_emotion = self.conversation_history[-1].get("jack_emotion", 6)
        self.jack_portrait.set_emotion(jack_last_emotion)
        
        jack_x = panel_x - 14
        jack_y = panel_y - 14
        self.jack_portrait.draw(surface, jack_x, jack_y)
        
        # Pop-out Rechts: Civilian Porträt (ragt 14px nach oben & rechts heraus!)
        civ_box_x = panel_x + panel_w - 50
        civ_box_y = panel_y - 14
        civ_box_rect = pygame.Rect(civ_box_x, civ_box_y, 64, 64)
        
        pygame.draw.rect(surface, (20, 30, 40), civ_box_rect)
        pygame.draw.rect(surface, (0, 200, 150), civ_box_rect, 2)
        if self.civ_portrait_surf:
            surface.blit(self.civ_portrait_surf, (civ_box_x + 4, civ_box_y + 4))
            
        # Zivilisten-Name: Rechts geankert in 1 Zeile in der Titlebar neben seinem Porträt
        civ_name = getattr(self.civ_node, 'name', 'Unknown Node')
        self._draw_underlined_text(surface, civ_name.strip().upper(), panel_x + panel_w - 56, panel_y + 6, color=WHITE_TEXT, size="tiny", align="right")
            
        # Inhaltsbereich (TAB-spezifisch)
        if self.active_tab == "DIALOGUE":
            self._draw_dialogue_tab(surface, panel_x, panel_y, panel_w, panel_h, native_mx, native_my)
        else:
            self._draw_background_tab(surface, panel_x, panel_y, panel_w, panel_h)

    def _draw_dialogue_tab(self, surface: pygame.Surface, panel_x: int, panel_y: int, panel_w: int, panel_h: int, native_mx: int, native_my: int) -> None:
        node_data = self.dialogue_tree.get(self.current_node_id, {})
        choices = node_data.get("choices", [])
        num_choices = len(choices)
        
        btn_w = panel_w - 32
        btn_h = 24
        btn_gap = 6
        
        # Berechnung der Button-Höhe für dynamische Chat-Höhe
        total_choices_h = num_choices * (btn_h + btn_gap)
        
        # Chat-Historie Bereich (reicht bis knapp über die Buttons)
        chat_x = panel_x + 56
        chat_y = panel_y + 32
        chat_w = panel_w - 112
        chat_h = panel_h - 44 - total_choices_h
        
        chat_clip_rect = pygame.Rect(chat_x, chat_y, chat_w, chat_h)
        old_clip = surface.get_clip()
        surface.set_clip(chat_clip_rect)
        
        # Gesamthöhe berechnen für Scrolling
        total_history_h = 0
        formatted_history = []
        
        for entry in self.conversation_history:
            speaker = entry.get("speaker", "CIVILIAN")
            text = entry.get("text", "")
            lines = self._wrap_text_to_lines(text, max_chars_per_line=44)
            entry_h = len(lines) * 12 + 6
            formatted_history.append({
                "speaker": speaker,
                "lines": lines,
                "height": entry_h
            })
            total_history_h += entry_h

        self.max_scroll = max(0, total_history_h - chat_h)
        
        # Zeichne Historie mit scroll_offset
        current_y = chat_y - self.scroll_offset
        for item in formatted_history:
            speaker = item["speaker"]
            lines = item["lines"]
            
            if speaker == "JACK":
                # Jack spricht: Links bündig am linken Profil
                for line_str in lines:
                    if chat_y - 12 <= current_y <= chat_y + chat_h:
                        txt_surf = font_mgr.render(line_str, color=GREEN_TERMINAL, size="tiny")
                        surface.blit(txt_surf, (chat_x + 8, current_y))
                    current_y += 12
            else:
                # Zivilist spricht: Rechts bündig am rechten Profil
                for line_str in lines:
                    if chat_y - 12 <= current_y <= chat_y + chat_h:
                        txt_surf = font_mgr.render(line_str, color=WHITE_TEXT, size="tiny")
                        draw_x = chat_x + chat_w - txt_surf.get_width() - 8
                        surface.blit(txt_surf, (draw_x, current_y))
                    current_y += 12
            current_y += 6
            
        surface.set_clip(old_clip)
        
        # Scrollbar Slider auf der rechten Seite
        if self.max_scroll > 0:
            sb_x = chat_x + chat_w + 4
            sb_y = chat_y
            sb_w = 4
            sb_h = chat_h
            pygame.draw.rect(surface, (20, 30, 40), (sb_x, sb_y, sb_w, sb_h))
            
            thumb_h = max(16, int(sb_h * (chat_h / total_history_h)))
            thumb_y = sb_y + int((self.scroll_offset / self.max_scroll) * (sb_h - thumb_h))
            self.scrollbar_thumb_rect = pygame.Rect(sb_x - 1, thumb_y, sb_w + 2, thumb_h)
            pygame.draw.rect(surface, (0, 200, 150), self.scrollbar_thumb_rect)

        # Choices von UNTEN nach OBEN gestackt (kein Hohlraum am unteren Rand!)
        self.choice_rects = []
        bottom_anchor_y = panel_y + panel_h - 10 - btn_h # Exakt 10px über dem unteren Fensterrahmen
        
        for i, choice in enumerate(choices):
            # i = 0 ist die 1. Option, i = num_choices-1 ist die letzte Option (unten verankert)
            dist_from_bottom = (num_choices - 1 - i)
            btn_x = panel_x + 16
            btn_y = bottom_anchor_y - dist_from_bottom * (btn_h + btn_gap)
            
            rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
            self.choice_rects.append((rect, choice))
            
            is_hovered = rect.collidepoint(native_mx, native_my)
            bg_col = (0, 80, 60) if is_hovered else (15, 30, 40)
            border_col = (0, 255, 200) if is_hovered else (0, 120, 100)
            
            pygame.draw.rect(surface, bg_col, rect)
            pygame.draw.rect(surface, border_col, rect, 1)
            
            c_text = choice.get("text", "")
            txt_col = AMBER_WARN if "RAGEQUIT" in c_text else (GREEN_TERMINAL if is_hovered else WHITE_TEXT)
            c_surf = font_mgr.render(c_text, color=txt_col, size="tiny")
            surface.blit(c_surf, (rect.x + 10, rect.y + 6))

    def _draw_background_tab(self, surface: pygame.Surface, panel_x: int, panel_y: int, panel_w: int, panel_h: int) -> None:
        """Zeigt die 2. Seite (Hintergrund/Profil-Analyse) sauber ohne Overflow."""
        civ = self.civ_node
        
        header_bg = font_mgr.render("--- DECKER SCAN // INDIVIDUAL BACKGROUND PROFILE ---", color=AMBER_WARN, size="tiny")
        surface.blit(header_bg, (panel_x + 60, panel_y + 30))
        
        gender = getattr(civ, 'gender', 'Unknown')
        age_group = getattr(civ, 'age_group', 'Unknown')
        origin = getattr(civ, 'origin', 'Unknown')
        traits = getattr(civ, 'personality_traits', 'Unknown')
        comment_jack = getattr(civ, 'comment_jack', 'No Jack log.')
        story = getattr(civ, 'story', 'No story available.')
        
        y_pos = panel_y + 48
        
        meta_line1 = font_mgr.render(f"GENDER: {gender}  |  AGE: {age_group}", color=WHITE_TEXT, size="tiny")
        surface.blit(meta_line1, (panel_x + 60, y_pos))
        y_pos += 14
        
        nervousness = getattr(civ, 'nervousness_level', None)
        origin_str = f"ORIGIN: {origin}" + (f"  |  NERVOUSNESS THRESHOLD: {int(nervousness)}%" if nervousness is not None else "")
        meta_line2 = font_mgr.render(origin_str, color=WHITE_TEXT, size="tiny")
        surface.blit(meta_line2, (panel_x + 60, y_pos))
        y_pos += 14
        
        meta_line3 = font_mgr.render(f"TRAITS: {traits}", color=AMBER_WARN, size="tiny")
        surface.blit(meta_line3, (panel_x + 60, y_pos))
        y_pos += 18
        
        # Jack's Log
        log_hdr = font_mgr.render("JACK'S ANALYSIS LOG:", color=GREEN_TERMINAL, size="tiny")
        surface.blit(log_hdr, (panel_x + 16, y_pos))
        y_pos += 14
        
        log_lines = self._wrap_text_to_lines(comment_jack, max_chars_per_line=64)
        for l in log_lines:
            l_surf = font_mgr.render(l, color=GREEN_TERMINAL, size="tiny")
            surface.blit(l_surf, (panel_x + 24, y_pos))
            y_pos += 12
            
        y_pos += 6
        
        # Story / Biografie
        story_hdr = font_mgr.render("BACKGROUND DOSSIER:", color=WHITE_TEXT, size="tiny")
        surface.blit(story_hdr, (panel_x + 16, y_pos))
        y_pos += 14
        
        story_lines = self._wrap_text_to_lines(story, max_chars_per_line=64)
        for l in story_lines:
            s_surf = font_mgr.render(l, color=WHITE_TEXT, size="tiny")
            surface.blit(s_surf, (panel_x + 24, y_pos))
            y_pos += 12

    def handle_click(self, mx: int, my: int) -> Optional[str]:
        if not self.active:
            return None
            
        # Tab Klicks
        if self.tab_dialogue_rect.collidepoint(mx, my):
            self.active_tab = "DIALOGUE"
            return None
            
        if self.tab_bg_rect.collidepoint(mx, my):
            self.active_tab = "BACKGROUND"
            return None
            
        # Choice Klicks (nur im DIALOGUE Tab)
        if self.active_tab == "DIALOGUE":
            for rect, choice in self.choice_rects:
                if rect.collidepoint(mx, my):
                    next_node = choice.get("next_node")
                    action = choice.get("action")
                    
                    if next_node:
                        # Füge Jack's gewählten Text und Civ's Antwort zur Historie hinzu
                        self.conversation_history.append({
                            "speaker": "JACK",
                            "text": choice.get("text", "")
                        })
                        
                        self.current_node_id = next_node
                        next_data = self.dialogue_tree.get(next_node, {})
                        if next_data:
                            self.conversation_history.append({
                                "speaker": next_data.get("speaker", "CIVILIAN"),
                                "text": next_data.get("text", "..."),
                                "jack_emotion": next_data.get("jack_emotion", 6)
                            })
                        # Scroll zum Ende
                        self.scroll_offset = self.max_scroll
                        return None
                    elif action:
                        self.close()
                        return action
        return None
