"""Text-to-speech using edge-tts with pyttsx3 fallback."""

import asyncio
import io
import tempfile
import os
import numpy as np
import sounddevice as sd

from config import EDGE_TTS_VOICE, TTS_FALLBACK_RATE, SAMPLE_RATE, TTS_VOLUME


async def _edge_tts_speak(text: str) -> bool:
    """Synthesize and play speech using edge-tts + miniaudio. Returns True on success."""
    try:
        import edge_tts
        import miniaudio

        communicate = edge_tts.Communicate(text, EDGE_TTS_VOICE)

        # Collect all audio bytes
        audio_bytes = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]

        if not audio_bytes:
            return False

        # Decode MP3 to raw PCM using miniaudio
        decoded = miniaudio.decode(audio_bytes, sample_rate=24000, nchannels=1)
        samples = np.array(decoded.samples, dtype=np.float32)
        # Normalize and apply volume
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            samples = samples / max_val * 0.9 * TTS_VOLUME

        # Play via sounddevice
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: sd.play(samples, samplerate=24000, blocking=True),
        )
        return True

    except Exception as e:
        print(f"edge-tts failed: {e}")
        return False


async def _pyttsx3_speak(text: str) -> bool:
    """Fallback TTS using pyttsx3. Returns True on success."""
    try:
        import pyttsx3

        loop = asyncio.get_event_loop()

        def _speak():
            engine = pyttsx3.init()
            engine.setProperty("rate", TTS_FALLBACK_RATE)
            engine.setProperty("volume", TTS_VOLUME)
            engine.say(text)
            engine.runAndWait()
            engine.stop()

        await loop.run_in_executor(None, _speak)
        return True

    except Exception as e:
        print(f"pyttsx3 fallback failed: {e}")
        return False


async def speak(text: str):
    """Speak text using edge-tts, falling back to pyttsx3 if needed."""
    if not text or not text.strip():
        return

    text = text.strip()
    print(f"[TTS] Speaking: {text[:80]}{'...' if len(text) > 80 else ''}")

    success = await _edge_tts_speak(text)
    if not success:
        await _pyttsx3_speak(text)
