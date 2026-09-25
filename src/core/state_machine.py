from typing import Optional, Dict, Any

class State:
    """Basisklasse für alle Spielzustände (FSM)."""
    
    def __init__(self, state_machine: 'StateMachine') -> None:
        self.sm = state_machine

    def init(self) -> None:
        """Initialisiert Logik und Register des Zustands."""
        pass

    def init_draw(self) -> None:
        """Initialisiert einmalig statische Grafiken und Caches."""
        pass

    def update(self, dt: float) -> None:
        """Logik-Update-Zyklus (keine Render-Aufrufe)."""
        pass

    def update_draw(self) -> None:
        """Render-Update-Zyklus (keine Logik-Mutation)."""
        pass

    def cleanup(self) -> None:
        """Ressourcen-Freigabe vor Zustandswechsel."""
        pass


class StateMachine:
    """Verwaltet den globalen Game-State."""
    
    def __init__(self) -> None:
        self.states: Dict[str, State] = {}
        self.current_state: Optional[State] = None
        
        # Dependency Injection Container für globale Referenzen (GameManager etc.)
        self.context: Dict[str, Any] = {}

    def register_state(self, name: str, state_instance: State) -> None:
        """Registriert einen Zustand."""
        self.states[name] = state_instance

    def change_state(self, name: str) -> None:
        """
        Atomic transition flow:
        old_state.cleanup() -> allocate_new_state_registers() -> new_state.init() -> new_state.init_draw()
        """
        if self.current_state is not None:
            self.current_state.cleanup()
            
        # Optional: allocate_new_state_registers() -> Reset von Shared Memory Buffern hier
        
        self.current_state = self.states.get(name)
        if self.current_state is not None:
            self.current_state.init()
            self.current_state.init_draw()

    def update(self, dt: float) -> None:
        """Leitet Logik-Zyklus an aktiven State weiter."""
        if self.current_state is not None:
            self.current_state.update(dt)

    def handle_event(self, event: Any) -> None:
        if self.current_state is not None and hasattr(self.current_state, 'handle_event'):
            self.current_state.handle_event(event)

    def update_draw(self) -> None:
        """Leitet Render-Zyklus an aktiven State weiter."""
        if self.current_state is not None:
            self.current_state.update_draw()
