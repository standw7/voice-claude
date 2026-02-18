"""System tray icon with color-coded status indicator."""

import threading
from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem
from state import AppState
from config import TRAY_COLORS


def _create_icon_image(color: tuple) -> Image.Image:
    """Create a simple colored circle icon."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 4
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=color,
        outline=(255, 255, 255, 200),
        width=2,
    )
    return img


class TrayIcon:
    """System tray icon that reflects the current app state."""

    def __init__(self, on_quit: callable):
        self._on_quit = on_quit
        self._icon: Icon | None = None
        self._thread: threading.Thread | None = None
        self._current_state = AppState.IDLE

    def start(self):
        """Start the tray icon in a background thread."""
        menu = Menu(
            MenuItem("Voice Claude", None, enabled=False),
            Menu.SEPARATOR,
            MenuItem("Quit", self._quit_clicked),
        )

        self._icon = Icon(
            "Voice Claude",
            icon=_create_icon_image(TRAY_COLORS["IDLE"]),
            title="Voice Claude - Idle",
            menu=menu,
        )

        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def update_state(self, old_state: AppState, new_state: AppState):
        """Callback for state machine changes - updates icon color and tooltip."""
        self._current_state = new_state
        if self._icon is None:
            return

        color = TRAY_COLORS.get(new_state.value, TRAY_COLORS["IDLE"])
        self._icon.icon = _create_icon_image(color)
        self._icon.title = f"Voice Claude - {new_state.value.title()}"

    def _quit_clicked(self, icon, item):
        self._on_quit()

    def stop(self):
        """Remove the tray icon."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
