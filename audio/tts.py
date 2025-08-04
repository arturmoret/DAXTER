import threading, pyttsx3
from typing import Iterable, Mapping

class GestorVoz:
    def __init__(self, velocidad: int = 150, id_voz: int = 0):
        self.velocidad = velocidad
        self.id_voz = id_voz
        self.lock = threading.Lock()

    def hablar(self, texto: str, async_: bool = True):
        target = self._speak_blocking
        if async_:
            threading.Thread(target=target, args=(texto,), daemon=True).start()
        else:
            target(texto)

    def decir(self, clases: Iterable[int], nombres: Mapping[int, str]):
        if not clases:
            return
        etiquetas = [nombres.get(c, f"clase {c}") for c in clases]
        frase = "Veo " + " y ".join(etiquetas)
        self.hablar(frase, async_=True)

    def _speak_blocking(self, texto: str):
        with self.lock:
            engine = pyttsx3.init()
            engine.setProperty("rate", self.velocidad)

            # Seleccionar voz española
            for v in engine.getProperty("voices"):
                if "helena" in v.name.lower() or "es-es" in v.id.lower():
                    engine.setProperty("voice", v.id)
                    break

            engine.say(texto)
            engine.runAndWait()
            engine.stop()          
