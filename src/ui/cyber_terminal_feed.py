import random
from typing import Optional, Dict, Any

# Kryptische C# / Matrix / Sanskrit Fantasie Skripte & Funktionen
SANSKRIT_MATRIX_SYMBOLS = ["⟁", "∇", "λ", "⨳", "⟠", "⟁", "∇", "Ξ", "Ψ", "Ω"]

FANTASY_CSHARP_TEMPLATES = [
    "async Task<{sym1}> {sym2}_SyncCore(0x{hex2}) {{ await {sym1}_shift; }}",
    "[λ] => decrypt(0x{hex3}) :: {sym1}.compile();",
    "struct {sym1}_Grid {{ float3 {sym2}_pos; int {sym1}_state; }}",
    "override void {sym2}_Pulse(0x{hex2}) => {sym1}_layer.bind();",
    "namespace Shadowgrid.{sym2}Core {{ internal class {sym1}_Node {{}} }}",
    "[{hex4}] {sym1}.eval(λ => λ.override(0x{hex2}));",
    "while({sym2}_active) {{ {sym1}_stream.push(0x{hex3}); }}",
    "public static {sym1}_Matrix {sym2}_Inject(byte[] 0x{hex2}) {{ ... }}",
    "yield return {sym1}_Kernel.eval(0x{hex3});",
    "[{sym3}] {sym2}_threat_level = {threat_val}%;",
    "{sym1}_node.connect(0x{hex3});",
    "if ({sym1}_channel.is_active) {sym2}_flush(0x{hex2});",
    "fixed ({sym1}_byte* p = &0x{hex3}) {{ {sym2}_read(p); }}"
]

class CyberTerminalFeed:
    """
    Generiert schnelle, kryptische Matrix / Sanskrit C# Fantasie-Skripte
    und Funktionen, die über das Terminal-Panel des HUDs durchlaufen.
    """
    def __init__(self, max_history: int = 50) -> None:
        self.max_history = max_history
        self.lines: list[str] = []
        self.gen_timer = 0.0
        
        # Initialer Feed
        for _ in range(12):
            self.lines.append(self._generate_fantasy_line())

    def _generate_fantasy_line(self, context: Optional[Dict[str, Any]] = None) -> str:
        ctx = context or {}
        threat = ctx.get("threat_level", 0.0)
        
        sym1 = random.choice(SANSKRIT_MATRIX_SYMBOLS)
        sym2 = random.choice(SANSKRIT_MATRIX_SYMBOLS)
        sym3 = random.choice(SANSKRIT_MATRIX_SYMBOLS)
        
        template = random.choice(FANTASY_CSHARP_TEMPLATES)
        line = template.format(
            sym1=sym1,
            sym2=sym2,
            sym3=sym3,
            hex2=f"{random.randint(0x10, 0xFF):02X}",
            hex3=f"{random.randint(0x1000, 0xFFFF):04X}",
            hex4=f"0x{random.randint(0x100, 0xFFF):03X}",
            threat_val=int(threat)
        )
        return line

    def add_event(self, tag: str, detail: str) -> None:
        sym = random.choice(SANSKRIT_MATRIX_SYMBOLS)
        line = f"[{sym}] {tag.upper()} :: {detail}"
        self.lines.append(line)
        if len(self.lines) > self.max_history:
            self.lines.pop(0)

    def update(self, dt: float, context: Optional[Dict[str, Any]] = None) -> None:
        """Schnelles Durchlaufen der Fantasie-Skripte."""
        self.gen_timer -= dt
        if self.gen_timer <= 0:
            # Hohe Frequenz (alle 80ms - 200ms eine neue Codezeile)
            self.gen_timer = random.uniform(0.08, 0.20)
            new_line = self._generate_fantasy_line(context)
            self.lines.append(new_line)
            if len(self.lines) > self.max_history:
                self.lines.pop(0)

    def get_recent_lines(self, count: int = 4) -> list[str]:
        """Gibt die jüngsten N Codezeilen zurück."""
        return self.lines[-count:]
