import os, queue, pvporcupine, sounddevice as sd, numpy as np

class WakeWordListener:
    def __init__(self, access_key: str, keyword_path: str):
        model_es = os.path.join(os.path.dirname(__file__), "porcupine_params_es.pv")
        self.porc = pvporcupine.create(
            access_key=access_key,
            keyword_paths=[keyword_path],
            model_path=model_es
        )
        self.q = queue.Queue()

    # ---------- stream callback ----------
    def _callback(self, indata, frames, time_info, status):
        pcm = np.frombuffer(indata, dtype=np.int16)
        if self.porc.process(pcm) >= 0:
            self.q.put_nowait(True)

    # ---------- API pública --------------
    def start(self):
        self.stream = sd.InputStream(
            samplerate=self.porc.sample_rate,
            blocksize=self.porc.frame_length,
            channels=1,
            dtype="int16",
            callback=self._callback
        )
        self.stream.start()

    def heard_wake(self) -> bool:
        try:
            return self.q.get_nowait()
        except queue.Empty:
            return False
