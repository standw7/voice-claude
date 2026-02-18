"""Voice Claude - Voice interface for Claude Code.

Entry point and async orchestrator. Press Ctrl+Space (push-to-talk) or F9
to speak commands, hear Claude's response. System tray shows current state.
Includes a TCP permission server for voice-based tool approval.
"""

import asyncio
import sys
import os

from config import HOTKEY
from state import StateMachine, AppState
from audio_input import AudioRecorder
from stt import SpeechToText
from claude_interface import ClaudeInterface
from tts import speak
from summarizer import summarize_for_speech
from hotkey import PushToTalk
from tray import TrayIcon

PERMISSION_PORT = 19384

# Stores last response for "repeat" command
_last_response: str = ""


async def voice_confirm(description: str, sm: StateMachine,
                        recorder: AudioRecorder, stt: SpeechToText) -> bool:
    """Ask the user for voice confirmation of a risky action."""
    await sm.set_state(AppState.CONFIRMING)
    await speak(f"Claude wants to: {description}. Say yes or no.")

    await sm.set_state(AppState.LISTENING)
    audio = await recorder.record_until_silence()

    if audio is None:
        await speak("No response heard. Denying action.")
        return False

    text = await stt.transcribe(audio)
    lower = text.lower().strip()
    print(f"[Confirmation]: {text}")

    approved = any(w in lower for w in ("yes", "yeah", "yep", "sure", "go ahead",
                                         "do it", "okay", "ok", "approve"))
    if approved:
        await speak("Approved.")
    else:
        await speak("Denied.")

    return approved


async def run_permission_server(sm: StateMachine, recorder: AudioRecorder,
                                stt: SpeechToText):
    """TCP server that handles permission requests from the MCP permission server."""

    async def handle_client(reader: asyncio.StreamReader,
                            writer: asyncio.StreamWriter):
        try:
            data = await asyncio.wait_for(reader.readline(), timeout=5)
            message = data.decode().strip()

            if message.startswith("CONFIRM:"):
                description = message[8:]
                approved = await voice_confirm(description, sm, recorder, stt)
                writer.write(b"YES\n" if approved else b"NO\n")
            else:
                writer.write(b"NO\n")

            await writer.drain()
        except Exception as e:
            print(f"[PermissionTCP] Error: {e}")
            try:
                writer.write(b"NO\n")
                await writer.drain()
            except Exception:
                pass
        finally:
            writer.close()

    server = await asyncio.start_server(handle_client, "127.0.0.1", PERMISSION_PORT)
    print(f"[PermissionTCP] Listening on port {PERMISSION_PORT}")

    async with server:
        await server.serve_forever()


async def voice_loop(sm: StateMachine, recorder: AudioRecorder,
                     stt: SpeechToText, claude: ClaudeInterface):
    """Main voice interaction loop - triggered by hotkey."""
    global _last_response

    # Record
    await sm.set_state(AppState.LISTENING)
    print("\n--- Listening... (speak now, silence will auto-stop) ---")
    audio = await recorder.record_until_silence()

    if audio is None:
        print("No speech detected.")
        await sm.set_state(AppState.IDLE)
        return

    print(f"Recorded {len(audio) / 16000:.1f}s of audio.")

    # Transcribe
    await sm.set_state(AppState.TRANSCRIBING)
    text = await stt.transcribe(audio)
    print(f"[You said]: {text}")

    if not text.strip():
        print("Transcription was empty.")
        await sm.set_state(AppState.IDLE)
        return

    # Check for special commands
    lower = text.lower().strip()
    if lower in ("new conversation", "new session", "start over"):
        claude.new_session()
        await speak("Starting a new conversation.")
        await sm.set_state(AppState.IDLE)
        return

    if lower in ("cancel", "never mind", "nevermind"):
        await sm.set_state(AppState.IDLE)
        return

    if lower in ("repeat", "say that again", "repeat that"):
        if _last_response:
            await sm.set_state(AppState.SPEAKING)
            await speak(_last_response)
        else:
            await speak("Nothing to repeat yet.")
        await sm.set_state(AppState.IDLE)
        return

    # Handle "work on <project>" command
    if lower.startswith("work on "):
        project = text[8:].strip()
        prompt = f'work on {project}'
        await sm.set_state(AppState.PROCESSING)
        response = await claude.send(prompt)
        speech_text = summarize_for_speech(response)
        _last_response = speech_text
        await sm.set_state(AppState.SPEAKING)
        await speak(speech_text)
        await sm.set_state(AppState.IDLE)
        return

    # Send to Claude
    await sm.set_state(AppState.PROCESSING)
    print("[Processing with Claude...]")
    response = await claude.send(text)
    print(f"[Claude]: {response[:200]}{'...' if len(response) > 200 else ''}")

    # Summarize for speech
    speech_text = summarize_for_speech(response)
    _last_response = speech_text

    # Speak response
    await sm.set_state(AppState.SPEAKING)
    await speak(speech_text)

    await sm.set_state(AppState.IDLE)
    print("--- Ready (press hotkey to speak) ---")


async def main():
    sm = StateMachine()
    recorder = AudioRecorder()
    stt_engine = SpeechToText()
    claude = ClaudeInterface()

    # Shutdown flag
    shutdown_event = asyncio.Event()

    def request_shutdown():
        shutdown_event.set()

    # System tray
    tray = TrayIcon(on_quit=request_shutdown)
    sm.on_change(tray.update_state)
    tray.start()

    # Start TCP permission server in background
    perm_task = asyncio.create_task(
        run_permission_server(sm, recorder, stt_engine)
    )

    # Load Whisper model
    print("=== Voice Claude ===")
    print("Initializing...")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, stt_engine.load_model)

    # Speak ready notification
    await speak("Voice Claude is ready.")
    print(f"\nPress {HOTKEY.upper()} to speak a command. Press Ctrl+C to quit.\n")

    # Push-to-talk hotkey
    trigger = asyncio.Event()

    def on_ptt_start():
        if sm.is_idle():
            trigger.set()

    def on_ptt_stop():
        # Signal recorder to stop (for push-to-talk release)
        recorder.stop()

    ptt = PushToTalk(on_start=on_ptt_start, on_stop=on_ptt_stop, hotkey=HOTKEY)
    ptt.start()

    # Main loop
    try:
        while not shutdown_event.is_set():
            trigger.clear()
            # Wait for hotkey press or shutdown (check every 100ms)
            while not trigger.is_set() and not shutdown_event.is_set():
                await asyncio.sleep(0.1)

            if shutdown_event.is_set():
                break

            await voice_loop(sm, recorder, stt_engine, claude)

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        perm_task.cancel()
        ptt.stop()
        tray.stop()
        print("Voice Claude stopped.")


if __name__ == "__main__":
    asyncio.run(main())
