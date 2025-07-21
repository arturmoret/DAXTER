import pyttsx3
import time

class GestorVoz:
    def __init__(self, velocidad=150, espera_entre_mensajes=5):
        self.motor = pyttsx3.init()
        self.motor.setProperty('rate', velocidad)
        self.ultima_vez_dicho = {}
        self.espera = espera_entre_mensajes

    def decir_si_corresponde(self, clases, nombres_clases):
        ahora = time.time()
        clases_a_decir = []

        for c in clases:
            hace_cuanto = ahora - self.ultima_vez_dicho.get(c, 0)
            if hace_cuanto > self.espera:
                clases_a_decir.append(nombres_clases.get(c, f"clase {c}"))
                self.ultima_vez_dicho[c] = ahora

        if clases_a_decir:
            texto = "I saw " + " and ".join(clases_a_decir)
            self.motor.say(texto)
            self.motor.runAndWait()
