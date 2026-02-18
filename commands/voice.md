---
description: Start Voice Claude - hands-free voice interface
allowed-tools: Bash(python:*), Bash(pip:*), Bash(cd:*), Bash(ls:*), Read
---

## Voice Mode

Launch Voice Claude, the voice-driven interface for Claude Code.

### Steps

1. First, check if voice-claude dependencies are installed:
```
!`python -c "import faster_whisper, edge_tts, sounddevice, keyboard, pystray" 2>&1 && echo "DEPS_OK" || echo "DEPS_MISSING"`
```

2. If dependencies are missing, install them:
```bash
pip install faster-whisper edge-tts sounddevice numpy keyboard pystray Pillow miniaudio pyttsx3
```

3. Determine the voice-claude directory. Check these locations in order:
   - `~/Downloads/Projects/voice-claude/main.py`
   - The current working directory if it contains `main.py` with voice-claude code

4. Launch voice mode by running:
```bash
python <path-to-voice-claude>/main.py
```

5. Tell the user: "Voice mode is starting. Hold Right Shift to speak, release to send. Press Ctrl+C to exit voice mode."

**Important**: This launches an interactive voice loop. The process stays running until the user presses Ctrl+C. Do NOT try to capture the output or wait for it to finish — just launch it and let the user interact with it directly.
