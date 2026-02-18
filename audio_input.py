"""Microphone recording via sounddevice with silence detection."""

import asyncio
import numpy as np
import sounddevice as sd
from config import (
    SAMPLE_RATE, CHANNELS, DTYPE,
    SILENCE_THRESHOLD, SILENCE_DURATION, MAX_RECORDING_DURATION,
)


class AudioRecorder:
    """Records audio from the microphone until silence or manual stop."""

    def __init__(self):
        self._recording = False
        self._frames: list[np.ndarray] = []

    async def record_until_silence(self) -> np.ndarray | None:
        """Record audio, stopping after sustained silence or max duration.

        Returns numpy array of int16 samples, or None if nothing recorded.
        """
        self._frames = []
        self._recording = True
        silence_samples = 0
        total_samples = 0
        chunk_size = int(SAMPLE_RATE * 0.1)  # 100ms chunks
        samples_for_silence = int(SILENCE_DURATION * SAMPLE_RATE)
        max_samples = int(MAX_RECORDING_DURATION * SAMPLE_RATE)

        loop = asyncio.get_event_loop()

        def _record_blocking():
            nonlocal silence_samples, total_samples
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=chunk_size,
            ) as stream:
                while self._recording:
                    data, _ = stream.read(chunk_size)
                    chunk = data.copy().flatten()
                    self._frames.append(chunk)
                    total_samples += len(chunk)

                    rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
                    if rms < SILENCE_THRESHOLD:
                        silence_samples += len(chunk)
                    else:
                        silence_samples = 0

                    if silence_samples >= samples_for_silence:
                        break
                    if total_samples >= max_samples:
                        break

        await loop.run_in_executor(None, _record_blocking)
        self._recording = False

        if not self._frames:
            return None

        audio = np.concatenate(self._frames)
        # Trim trailing silence
        if silence_samples > 0 and len(audio) > silence_samples:
            audio = audio[:-silence_samples]

        if len(audio) < SAMPLE_RATE * 0.3:  # less than 300ms = probably noise
            return None

        return audio

    def stop(self):
        """Manually stop recording."""
        self._recording = False
