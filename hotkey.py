"""Global Ctrl+Space push-to-talk hotkey handler."""

import asyncio
import keyboard
from typing import Callable


class PushToTalk:
    """Ctrl+Space push-to-talk: press to start recording, release to stop.

    Falls back to F9 toggle mode if Ctrl+Space detection has issues.
    """

    def __init__(self, on_start: Callable, on_stop: Callable,
                 hotkey: str = "ctrl+space"):
        self._on_start = on_start
        self._on_stop = on_stop
        self._hotkey = hotkey
        self._is_pressed = False
        self._hooked = False

    def start(self):
        """Register the hotkey hooks."""
        if self._hooked:
            return

        # For push-to-talk, we need key down and key up events
        if "+" in self._hotkey:
            # Combo key like right shift+. - use hotkey with on_press/on_release
            keyboard.add_hotkey(self._hotkey, self._on_press, suppress=False)
            # For release detection on combos, watch for the last key to release
            last_key = self._hotkey.split("+")[-1].strip()
            keyboard.on_release_key(last_key, self._on_release_key, suppress=False)
        else:
            # Simple key like F9
            keyboard.on_press_key(self._hotkey, lambda _: self._on_press(),
                                  suppress=False)
            keyboard.on_release_key(self._hotkey, self._on_release_key,
                                    suppress=False)

        self._hooked = True

    def _on_press(self):
        if not self._is_pressed:
            self._is_pressed = True
            self._on_start()

    def _on_release_key(self, event=None):
        if self._is_pressed:
            self._is_pressed = False
            self._on_stop()

    def stop(self):
        """Remove all hotkey hooks."""
        if self._hooked:
            keyboard.unhook_all()
            self._hooked = False
            self._is_pressed = False
