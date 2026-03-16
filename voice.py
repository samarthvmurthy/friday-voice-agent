import speech_recognition as sr
import sounddevice as sd
import numpy as np
import threading
import queue
import io
import wave
import pyttsx3

RATE = 16000
CHANNELS = 1
WAKE_PHRASES = ["hey friday", "hey, friday", "friday", "hi friday", "ok friday", "okay friday"]

# ── TTS engine ────────────────────────────────────────────────────────────────
_tts_queue:  queue.Queue = queue.Queue()
_tts_muted:  list[bool]  = [False]


def _tts_worker():
    engine = pyttsx3.init()
    engine.setProperty('rate', 175)
    engine.setProperty('volume', 0.95)
    # prefer Zira (US female) then Hazel (GB female)
    voices = engine.getProperty('voices')
    for v in voices:
        if any(n in v.name.lower() for n in ('zira', 'aria', 'hazel', 'eva')):
            engine.setProperty('voice', v.id)
            break
    while True:
        text = _tts_queue.get()
        if text is None:
            break
        if not _tts_muted[0]:
            engine.say(text)
            engine.runAndWait()


_tts_thread = threading.Thread(target=_tts_worker, daemon=True)
_tts_thread.start()


def speak(text: str):
    """Speak text asynchronously. Clears any queued speech first."""
    while not _tts_queue.empty():
        try:
            _tts_queue.get_nowait()
        except queue.Empty:
            break
    _tts_queue.put(text)


def set_muted(muted: bool):
    _tts_muted[0] = muted


def is_muted() -> bool:
    return _tts_muted[0]


# ── Audio helpers ─────────────────────────────────────────────────────────────

def _numpy_to_audio_data(arr: np.ndarray, recognizer: sr.Recognizer) -> sr.AudioData:
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(arr.tobytes())
    buf.seek(44)
    raw = buf.read()
    return sr.AudioData(raw, RATE, 2)


def _record_until_silence(max_seconds: int = 10, silence_threshold: float = 300,
                           silence_duration: float = 1.5) -> np.ndarray:
    frames = []
    chunk_size = int(RATE * 0.1)
    silence_chunks_needed = int(silence_duration / 0.1)

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())
        rms = np.sqrt(np.mean(indata.astype(np.float32) ** 2))
        if rms < silence_threshold:
            silent_chunks_box[0] += 1
        else:
            silent_chunks_box[0] = 0

    silent_chunks_box = [0]

    with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype='int16',
                        blocksize=chunk_size, callback=callback):
        max_chunks = int(max_seconds / 0.1)
        for _ in range(max_chunks):
            sd.sleep(100)
            if len(frames) > 10 and silent_chunks_box[0] >= silence_chunks_needed:
                break

    return np.concatenate(frames, axis=0) if frames else np.array([], dtype=np.int16)


# ── VoiceListener ─────────────────────────────────────────────────────────────

class VoiceListener:
    def __init__(self):
        self._r = sr.Recognizer()
        self._wake_event = threading.Event()
        self._silence_threshold = 300

    def calibrate(self):
        print("  Calibrating microphone...", flush=True)
        noise = sd.rec(int(RATE * 1.5), samplerate=RATE, channels=CHANNELS,
                       dtype='int16', blocking=True)
        rms = np.sqrt(np.mean(noise.astype(np.float32) ** 2))
        self._silence_threshold = max(rms * 1.5, 250)
        print(f"  Ready. Noise floor: {rms:.0f}, threshold: {self._silence_threshold:.0f}", flush=True)

    def _transcribe(self, arr: np.ndarray) -> str | None:
        if arr.size == 0:
            return None
        try:
            audio_data = _numpy_to_audio_data(arr, self._r)
            return self._r.recognize_google(audio_data).lower()
        except (sr.UnknownValueError, sr.RequestError):
            return None

    def _listen_chunk(self, seconds: float = 2.0) -> np.ndarray:
        return sd.rec(int(RATE * seconds), samplerate=RATE,
                      channels=CHANNELS, dtype='int16', blocking=True)

    def wait_for_wake(self, manual_event=None):
        self._wake_event.clear()
        print("  Listening for wake word...", flush=True)

        while not self._wake_event.is_set():
            if manual_event and manual_event.is_set():
                print("  [mic button] Manual trigger.", flush=True)
                return
            chunk = self._listen_chunk(seconds=2.0)
            text = self._transcribe(chunk)
            if text:
                print(f"  [heard] {text}", flush=True)
                if any(p in text for p in WAKE_PHRASES):
                    self._wake_event.set()

    def record_command(self) -> str | None:
        print("  Recording command...", flush=True)
        arr = _record_until_silence(max_seconds=12,
                                    silence_threshold=self._silence_threshold)
        text = self._transcribe(arr)
        print(f"  [command] {text}", flush=True)
        return text
