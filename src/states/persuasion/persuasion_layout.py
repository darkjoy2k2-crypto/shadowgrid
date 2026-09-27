import pygame
from typing import Tuple, List

CANVAS_W = 1280
CANVAS_H = 720

class PersuasionLayout:
    """Berechnet Layout-Rechtecke und Maus-Koordinaten für das Persuasion Minigame."""

    @staticmethod
    def get_native_mouse_pos(scaled_surface: Any, raw_pos: Tuple[int, int]) -> Tuple[int, int]:
        if not scaled_surface:
            return raw_pos
        scale_x = CANVAS_W / float(scaled_surface.get_width())
        scale_y = CANVAS_H / float(scaled_surface.get_height())
        return int(raw_pos[0] * scale_x), int(raw_pos[1] * scale_y)

    @staticmethod
    def get_action_rect(i: int) -> pygame.Rect:
        return pygame.Rect(10, 80 + i * 125, 840, 118)

    @staticmethod
    def get_dir_box_rect(pos: List[int]) -> pygame.Rect:
        return pygame.Rect(pos[0], pos[1], 410, 150)

    @staticmethod
    def get_dir_item_rect(pos: List[int], r_i: int) -> pygame.Rect:
        box = PersuasionLayout.get_dir_box_rect(pos)
        return pygame.Rect(box.x + 8, box.y + 26 + r_i * 24, box.width - 24, 22)

    @staticmethod
    def get_folder_icon_rect() -> pygame.Rect:
        return pygame.Rect(1220, 672, 50, 38)

    @staticmethod
    def get_action_bar_full_rect(pos: List[int]) -> pygame.Rect:
        return pygame.Rect(pos[0], pos[1], 410, 115)

    @staticmethod
    def get_action_bar_header_rect(pos: List[int]) -> pygame.Rect:
        return pygame.Rect(pos[0], pos[1], 410, 24)

    @staticmethod
    def get_action_bar_slot_rect(pos: List[int], s_i: int) -> pygame.Rect:
        return pygame.Rect(pos[0] + 10 + s_i * 66, pos[1] + 32, 58, 58)

    @staticmethod
    def get_bottom_button_rect(b_id: str) -> pygame.Rect:
        if b_id == "BRIBE":
            return pygame.Rect(20, 660, 260, 42)
        elif b_id == "NEXT_NPC":
            return pygame.Rect(290, 660, 260, 42)
        else:
            return pygame.Rect(560, 660, 280, 42)

    @staticmethod
    def wrap_text(text: str, max_chars: int = 36) -> List[str]:
        words = text.split(' ')
        lines = []
        cur_line = []
        cur_len = 0
        for w in words:
            if cur_len + len(w) + (1 if cur_line else 0) <= max_chars:
                cur_line.append(w)
                cur_len += len(w) + (1 if cur_line else 0)
            else:
                if cur_line:
                    lines.append(" ".join(cur_line))
                cur_line = [w]
                cur_len = len(w)
        if cur_line:
            lines.append(" ".join(cur_line))
        return lines
