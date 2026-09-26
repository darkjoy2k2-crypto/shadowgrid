import pygame
import random
from typing import Optional, Dict, Any

# Sehr knappe, ultra-kurze Sanskrit Code-Snippets
SANSKRIT_FANTASY_FUNCTIONS = [
    "fn ॐ_ज्ञान(0x{hex2})",
    "ॐ_तन्त्र => shift()",
    "void ॐ_कर्म()",
    "struct ॐ_माया {{ }}",
    "ॐ_अग्नि.flush()",
    "pub ॐ_चित्त()",
    "while(ॐ_active)",
    "fn ॐ_योग(0x{hex2})",
    "[λ] => ॐ_eval()",
    "yield ॐ_अमृत",
    "if (ॐ_active)",
    "fn ॐ_शान्ति()",
    "ॐ_मन्त्र.bind()",
    "async ॐ_शून्य()",
    "fn ॐ_रुद्र(0x{hex2})",
    "ॐ_तेज.state()",
    "ॐ_मोक्ष.run()",
    "fn ॐ_प्रज्ञा()",
    "ॐ_रुद्र.call()",
    "return ॐ_अमृत"
]

class CyberTerminalFeed:
    """
    Generiert sehr knappe, ultra-kurze Sanskrit Code-Snippets.
    Kein Autoscroll, kein Soft-Scrolling:
    Texte bleiben bei Leerlauf komplett stillstehen und werden NUR dann hart
    um jeweils eine Zeile nach oben geschoben, wenn 10 neue Ereignisse im Perception-Log auflaufen.
    """
    def __init__(self, max_history: int = 40) -> None:
        self.max_history = max_history
        self.lines: list[dict] = [] # Liste aus {"text": str, "y": float}
        self.line_step = 18.0 # Harter Zeilenabstand in Pixeln
        self.last_seen_event_counter = 0
        
        # Sanskrit Font Loader (Nirmala UI -> Mangal -> Segoe UI Historic -> Fallback)
        self.sanskrit_font: Optional[pygame.font.Font] = None
        self._init_sanskrit_font()
        
        # Initialer Event-Stand
        from src.utils.perception_logger import PerceptionLogger
        self.last_seen_event_counter = PerceptionLogger.get_instance().event_counter
        
        # Initial 2 Zeilen im unteren Bereich
        self.lines.append({"text": self._generate_fantasy_line(), "y": 322.0})
        self.lines.append({"text": self._generate_fantasy_line(), "y": 340.0})

    def _init_sanskrit_font(self) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        for font_name in ["nirmalaui", "nirmalatext", "mangal", "segoeuihistoric", "segoeui", "arial"]:
            try:
                self.sanskrit_font = pygame.font.SysFont(font_name, 11, bold=True)
                if self.sanskrit_font:
                    break
            except Exception:
                pass

    def _generate_fantasy_line(self, context: Optional[Dict[str, Any]] = None) -> str:
        template = random.choice(SANSKRIT_FANTASY_FUNCTIONS)
        line = template.format(
            hex2=f"{random.randint(0x10, 0xFF):02X}"
        )
        return line

    def add_event(self, tag: str, detail: str) -> None:
        # Harter Zeilenschub nach oben bei manuellem Event
        for item in self.lines:
            item["y"] -= self.line_step
        line = f"ॐ_{tag[:6].upper()}()"
        self.lines.append({"text": line, "y": 340.0})

    def update(self, dt: float, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Kein Autoscroll. Texte bleiben stillstehen.
        NUR wenn 10 neue Log-Ereignisse eintreffen, werden alle bestehenden Zeilen
        hart um genau 1 Zeile (18px) nach oben geschoben und eine neue Zeile unten platziert.
        """
        from src.utils.perception_logger import PerceptionLogger
        logger = PerceptionLogger.get_instance()
        
        if logger.event_counter - self.last_seen_event_counter >= 10:
            self.last_seen_event_counter = logger.event_counter
            
            # 1. Alle bestehenden Zeilen hart um 1 Zeilenhöhe (18px) nach oben schieben
            for item in self.lines:
                item["y"] -= self.line_step
                
            # 2. Neue Zeile unten bei y=340.0 anfügen
            self.lines.append({
                "text": self._generate_fantasy_line(context),
                "y": 340.0
            })
            
            # 3. Zeilen entfernen, die oben komplett aus dem Bild geschoben wurden
            self.lines = [item for item in self.lines if item["y"] > -25.0]

    def get_recent_lines(self, count: int = 4) -> list[str]:
        """Gibt die jüngsten N Codezeilen als Text zurück."""
        return [item["text"] for item in self.lines[-count:]]

    def draw_background_layer(self, surface: pygame.Surface) -> None:
        """
        Rendert die nach oben wandernden Sanskrit-Zeilen mit ihren individuellen y-Positionen
        und natürlichen Leerräumen.
        """
        right_margin = 624
        if not self.lines:
            return
            
        for item in self.lines:
            y = item["y"]
            if -18 <= y <= 365:
                # Sanftes Transparenz/Farbfading am oberen Bildschirmrand
                alpha_factor = min(1.0, max(0.25, (y + 18) / 90.0))
                green_val = int(160 * alpha_factor)
                color = (0, green_val, int(green_val * 0.55))
                
                if self.sanskrit_font:
                    line_surf = self.sanskrit_font.render(item["text"], True, color)
                else:
                    from src.ui.font_manager import font_mgr
                    line_surf = font_mgr.render(item["text"], color=color, size="tiny")
                    
                x = right_margin - line_surf.get_width()
                surface.blit(line_surf, (x, int(y)))
