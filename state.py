"""Application state machine for Voice Claude."""

import asyncio
from enum import Enum
from typing import Callable, Optional


class AppState(Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    TRANSCRIBING = "TRANSCRIBING"
    PROCESSING = "PROCESSING"
    CONFIRMING = "CONFIRMING"
    SPEAKING = "SPEAKING"


class StateMachine:
    """Thread-safe state machine with change callbacks."""

    def __init__(self):
        self._state = AppState.IDLE
        self._listeners: list[Callable[[AppState, AppState], None]] = []
        self._lock = asyncio.Lock()

    @property
    def state(self) -> AppState:
        return self._state

    async def set_state(self, new_state: AppState):
        async with self._lock:
            old = self._state
            self._state = new_state
            for cb in self._listeners:
                try:
                    cb(old, new_state)
                except Exception:
                    pass

    def on_change(self, callback: Callable[[AppState, AppState], None]):
        self._listeners.append(callback)

    def is_idle(self) -> bool:
        return self._state == AppState.IDLE

    def is_busy(self) -> bool:
        return self._state != AppState.IDLE
