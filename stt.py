"""Speech-to-text using faster-whisper with CUDA support."""

import asyncio
import numpy as np
from faster_whisper import WhisperModel
from config import WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE, SAMPLE_RATE


class SpeechToText:
    """Transcribes audio using faster-whisper."""

    def __init__(self):
        self._model: WhisperModel | None = None

    def load_model(self):
        """Load the Whisper model. Call once at startup."""
        print(f"Loading Whisper model '{WHISPER_MODEL}' on {WHISPER_DEVICE}...")
        try:
            self._model = WhisperModel(
                WHISPER_MODEL,
                device=WHISPER_DEVICE,
                compute_type=WHISPER_COMPUTE_TYPE,
            )
        except Exception:
            print(f"CUDA failed, falling back to CPU...")
            self._model = WhisperModel(
                WHISPER_MODEL,
                device="cpu",
                compute_type="int8",
            )
        print("Whisper model loaded.")

    async def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe int16 audio array to text."""
        if self._model is None:
            raise RuntimeError("Whisper model not loaded. Call load_model() first.")

        # Convert int16 to float32 normalized to [-1, 1]
        audio_float = audio.astype(np.float32) / 32768.0

        loop = asyncio.get_event_loop()

        def _transcribe_blocking():
            segments, info = self._model.transcribe(
                audio_float,
                beam_size=3,
                language="en",
                vad_filter=True,
            )
            text = " ".join(seg.text.strip() for seg in segments)
            return text.strip()

        result = await loop.run_in_executor(None, _transcribe_blocking)
        return result
