# Voice Claude - Project Instructions

## What This Is
A voice-driven wrapper around Claude Code. User presses a hotkey, speaks a command, Claude Code executes it autonomously, then reads aloud a summary.

## Architecture
- `main.py` - Entry point, async orchestrator, TCP permission server
- `config.py` - All configuration constants
- `state.py` - App state machine (IDLE/LISTENING/PROCESSING/etc.)
- `hotkey.py` - Ctrl+Space push-to-talk via `keyboard` library
- `audio_input.py` - Microphone recording via `sounddevice` with silence detection
- `stt.py` - faster-whisper CUDA transcription
- `claude_interface.py` - Claude Code CLI subprocess wrapper + session continuity
- `summarizer.py` - Strip markdown, condense long responses for speech
- `tts.py` - edge-tts async synthesis + pyttsx3 fallback
- `tray.py` - System tray icon with colored status indicator
- `permission_server_mcp.py` - MCP stdio server for risky action confirmation

## Running
```bash
pip install -r requirements.txt
python main.py
```
Requires admin/elevated terminal for global hotkey hooks.

## Key Details
- Session continuity via `--resume SESSION_ID` parsed from Claude's JSON output
- Push-to-talk with silence auto-stop (1.5s silence threshold)
- TCP IPC on port 19384 for permission confirmation between MCP server and main process
- Whisper tries CUDA first, falls back to CPU
- TTS tries edge-tts first, falls back to pyttsx3
