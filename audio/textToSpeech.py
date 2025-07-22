import threading
import pyttsx3

class GestorVoz:
    def __init__(self, velocidad=150, id_voz=1):
        self.velocidad = velocidad
        self.id_voz = id_voz
        self.lock = threading.Lock()     

    def _hablar(self, texto):
        with self.lock:                  
            engine = pyttsx3.init()
            engine.setProperty('rate', self.velocidad)

            voces = engine.getProperty('voices')
            if self.id_voz < len(voces):
                engine.setProperty('voice', voces[self.id_voz].id)

            engine.say(texto)
            engine.runAndWait()          
            engine.stop()                

    def decir(self, clases, nombres_clases):
        if not clases:
            return

        nombres_gen = (nombres_clases.get(c, f'class {c}') for c in clases)
        texto = "I saw " + " and ".join(nombres_gen)
        threading.Thread(target=self._hablar, args=(texto,), daemon=True).start()

