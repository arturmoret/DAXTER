from __future__ import annotations
import queue, sounddevice as sd, vosk, json
from pathlib import Path

class SpeechRecognizer:
    def __init__(self, model_path: str = "src/models/vosk-model-small-es-0.42"):
        model_path = Path(model_path).expanduser().resolve()
        if not model_path.exists():
            raise FileNotFoundError(f"Modelo Vosk no encontrado en {model_path}")
        self.model = vosk.Model(str(model_path))

    def transcribe(self, seconds: float = 3.0, sr: int = 16000) -> str:
        q = queue.Queue()

        def cb(indata, frames, time, status):
            q.put(bytes(indata))

        with sd.RawInputStream(samplerate=sr, blocksize=8000,
                               dtype="int16", channels=1, callback=cb):
            rec = vosk.KaldiRecognizer(self.model, sr)
            sd.sleep(int(seconds * 1000))
            while not q.empty():
                rec.AcceptWaveform(q.get())

        result = json.loads(rec.FinalResult())
        return result.get("text", "").lower().strip()
