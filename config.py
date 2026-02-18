"""Configuration constants for Voice Claude."""

# Audio recording
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"

# STT (faster-whisper)
WHISPER_MODEL = "base"
WHISPER_DEVICE = "cuda"       # "cuda" or "cpu"
WHISPER_COMPUTE_TYPE = "float16"  # "float16" for GPU, "int8" for CPU

# TTS
EDGE_TTS_VOICE = "en-US-GuyNeural"
TTS_FALLBACK_RATE = 175  # pyttsx3 words per minute
TTS_VOLUME = 0.5  # Volume multiplier (0.0 to 1.0)

# Hotkey
HOTKEY = "right shift+."  # Push-to-talk key (hold to record, release to send)

# Claude Code CLI
CLAUDE_CMD = "claude"
CLAUDE_TIMEOUT = 120  # seconds
CLAUDE_WORKING_DIR = None  # set at runtime or defaults to cwd
CLAUDE_ENV_STRIP = ["CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT"]  # prevent nesting errors

# Summarization
MAX_SPEECH_CHARS = 500  # condense responses longer than this

# System tray colors (RGBA)
TRAY_COLORS = {
    "IDLE": (128, 128, 128, 255),       # gray
    "LISTENING": (255, 0, 0, 255),      # red
    "TRANSCRIBING": (255, 165, 0, 255), # orange
    "PROCESSING": (0, 100, 255, 255),   # blue
    "CONFIRMING": (200, 0, 200, 255),   # magenta
    "SPEAKING": (0, 200, 0, 255),       # green
}

# Silence detection
SILENCE_THRESHOLD = 500       # RMS threshold for silence
SILENCE_DURATION = 1.5        # seconds of silence before auto-stop
MAX_RECORDING_DURATION = 30   # max seconds per recording
