import weakref
from typing import Callable, Dict, List, Any
from enum import Enum, auto

class Signal(Enum):
    PLAYER_DEATH = auto()
    ENTITY_DAMAGED = auto()
    GRID_TRACE_ESCALATION = auto()
    STATE_CHANGE_REQ = auto()

class EventBus:
    """Observer Pattern (Publish-Subscribe) für synchrone Signalübertragung."""
    
    def __init__(self) -> None:
        # weakref.WeakMethod prevents memory leaks when listeners are destroyed
        self._listeners: Dict[Signal, List[weakref.WeakMethod]] = {
            signal: [] for signal in Signal
        }

    def subscribe(self, signal: Signal, listener: Callable[..., None]) -> None:
        """Fügt einen Listener für ein Signal hinzu."""
        # Wrap the bound method in a WeakMethod
        if hasattr(listener, '__self__'):
            weak_listener = weakref.WeakMethod(listener)
            self._listeners[signal].append(weak_listener)
        else:
            # Fallback for normal functions (rare in this OOP architecture)
            pass

    def dispatch(self, signal: Signal, *args: Any, **kwargs: Any) -> None:
        """Verteilt ein Signal an alle registrierten Listener synchron."""
        active_listeners = []
        for weak_listener in self._listeners[signal]:
            listener = weak_listener()
            if listener is not None:
                listener(*args, **kwargs)
                active_listeners.append(weak_listener)
                
        # Clean up dead references
        self._listeners[signal] = active_listeners
