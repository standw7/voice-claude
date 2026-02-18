# Voice Claude - Project Instructions

## What This Is
A voice-driven wrapper around Claude Code. User presses Right Shift + Period (hold to talk, release to send), speaks a command, Claude Code executes it autonomously, then reads aloud a summary.

## Setup on a New Machine

When the user asks to "install voice-claude", "set up voice mode", or "install the voice plugin from GitHub", follow these steps:

1. **Clone the repo** (if not already local):
   ```bash
   cd ~/Downloads/Projects
   git clone https://github.com/standw7/voice-claude.git
   ```

2. **Run the setup script** (installs deps + copies /voice command):
   ```bash
   cd ~/Downloads/Projects/voice-claude
   python setup.py
   ```

3. **Verify** the /voice command was installed:
   - Check that `~/.claude/commands/voice.md` exists
   - The user can now type `/voice` in any Claude Code session

That's it. Two commands: clone + `python setup.py`.

### Mac-Specific Notes
- The `keyboard` library on macOS requires accessibility permissions (System Settings > Privacy & Security > Accessibility) — the terminal app running Claude must be granted access
- macOS has no CUDA, so Whisper will auto-fall back to CPU (slightly slower but works fine)
- The `pystray` tray icon works on macOS but may need the `rumps` backend — if tray fails, voice mode still works without it

## Architecture
- `main.py` - Entry point, async orchestrator, TCP permission server
- `config.py` - All configuration constants (hotkey, audio, TTS voice, etc.)
- `state.py` - App state machine (IDLE/LISTENING/PROCESSING/etc.)
- `hotkey.py` - Right Shift + Period push-to-talk via `keyboard` library
- `audio_input.py` - Microphone recording via `sounddevice` with silence detection
- `stt.py` - faster-whisper CUDA/CPU transcription
- `claude_interface.py` - Claude Code CLI subprocess wrapper + session continuity
- `summarizer.py` - Strip markdown, condense long responses for speech
- `tts.py` - edge-tts async synthesis + pyttsx3 fallback
- `tray.py` - System tray icon with colored status indicator
- `permission_server_mcp.py` - MCP stdio server for risky action confirmation
- `setup.py` - Cross-machine installer (deps + /voice command)
- `commands/voice.md` - The /voice slash command template

## Running
```bash
python main.py
```
Or use `/voice` from any Claude Code session.

## Hotkey
- **Right Shift + Period**: Hold to record, release to send (push-to-talk)
- Configurable in `config.py` via the `HOTKEY` variable
- The `keyboard` library supports: `right shift`, `left shift`, `ctrl+space`, `f1`-`f12`, etc.

## Key Details
- Session continuity via `--resume SESSION_ID` parsed from Claude's JSON output
- Push-to-talk with silence auto-stop (1.5s silence threshold)
- TCP IPC on port 19384 for permission confirmation between MCP server and main process
- Whisper tries CUDA first, falls back to CPU
- TTS tries edge-tts first, falls back to pyttsx3
- TTS volume controlled by `TTS_VOLUME` in config.py (default 0.5 = half volume)
