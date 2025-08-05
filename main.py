# src/main.py
from __future__ import annotations
import os, cv2, time, queue, threading, msvcrt

from audio.tts      import GestorVoz
from audio.wake     import WakeWordListener
from audio.stt      import SpeechRecognizer
from vision.camera   import Camera
from vision.detector import DetectorYOLO
from control.mode_manager import Modo
from ai.llm import (
    saludo_boot, saludo_listo, ack_wake,
    sin_objetos, describe, responder_libre
)

# --------------------------------------------------------------------------
# Configuración
# --------------------------------------------------------------------------
NOMBRES  = {0: "person", 9: "traffic light", 11: "stop sign", 15: "cat", 16: "dog"}
COOLDOWN = 10
WAKE_KEY = os.getenv("PV_ACCESS_KEY")
WAKE_PPN = "src/audio/hey_colega.ppn"
if not WAKE_KEY:
    raise RuntimeError("❌ Falta la variable de entorno PV_ACCESS_KEY.")

# --------------------------------------------------------------------------
# Hilo del wake-word
# --------------------------------------------------------------------------
def lanzar_wake_word(q_wake: queue.Queue) -> None:
    listener = WakeWordListener(WAKE_KEY, WAKE_PPN)
    listener.start()
    print("🔊 Wake-word listener activo…")
    while True:
        if listener.heard_wake():
            q_wake.put(True)

# --------------------------------------------------------------------------
# Botón virtual (tecla P)
# --------------------------------------------------------------------------
def esperar_encendido() -> None:
    print("Pulsa P para encender (Q para salir)…")
    while True:
        if msvcrt.kbhit():
            tecla = msvcrt.getch().lower()
            if tecla == b'p':
                return
            if tecla == b'q':
                exit()

# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------
def main() -> None:
    # Espera “botón”
    esperar_encendido()

    voz  = GestorVoz()
    stt  = SpeechRecognizer()                     # Vosk
    voz.hablar(saludo_boot(), async_=False)

    cam  = Camera()
    det  = DetectorYOLO(classes=list(NOMBRES.keys()))
    for _ in range(15): cam.get_frame()           # estabiliza cámara
    voz.hablar(saludo_listo())

    q_wake = queue.Queue()
    threading.Thread(target=lanzar_wake_word, args=(q_wake,), daemon=True).start()

    modo = Modo.REACTIVO
    ultimo_aviso: dict[int, float] = {}
    ultima_frase = ""

    try:
        while True:
            # -------------------------------------------------- MODO AUTO
            if modo == Modo.AUTOMATICO:
                frame = cam.get_frame()
                if frame is None:
                    break
                frame_det, actuales = det.detect(frame)

                ahora = time.time()
                validas = {c for c in actuales
                           if ahora - ultimo_aviso.get(c, 0) > COOLDOWN}
                if validas:
                    objs = [NOMBRES[c] for c in validas]
                    ultima_frase = describe(objs)
                    voz.hablar(ultima_frase)
                    for c in validas:
                        ultimo_aviso[c] = ahora

                cv2.imshow("Detección", frame_det)

            # ------------------------------------------------ MODO REACTIVO
            elif modo == Modo.REACTIVO:
                try:
                    q_wake.get(timeout=1)         # “Hey colega” detectado
                    texto = stt.transcribe()      # (graba antes de hablar)
                    texto = texto.lower().strip()
                    print("🔤", texto)

                    if not texto:
                        voz.hablar("No te he oído, tronco")
                        continue

                    # ---------- comandos ----------
                    if texto in {"que tengo delante", "qué tengo delante"}:
                        frame = cam.get_frame()
                        frame_det, act = det.detect(frame)
                        if act:
                            objs = [NOMBRES[c] for c in act]
                            ultima_frase = describe(objs)
                        else:
                            ultima_frase = sin_objetos()
                        voz.hablar(ultima_frase)
                        cv2.imshow("Detección", frame_det)
                        cv2.waitKey(1)

                    elif texto.startswith(("callate", "cállate")):
                        modo = Modo.SILENCIO
                        ultima_frase = responder_libre("Voy a callarme")
                        voz.hablar(ultima_frase)

                    elif "modo automático" in texto:
                        modo = Modo.AUTOMATICO
                        ultima_frase = responder_libre("Entrando en modo automático")
                        voz.hablar(ultima_frase)

                    elif texto.startswith("despierta"):
                        modo = Modo.REACTIVO
                        ultima_frase = responder_libre("He vuelto")
                        voz.hablar(ultima_frase)

                    elif "repite" in texto:
                        voz.hablar(ultima_frase or responder_libre("No dije nada"))

                    else:  # ---------------- frase libre ----------------
                        ultima_frase = responder_libre(texto)
                        voz.hablar(ultima_frase)

                except queue.Empty:
                    pass

            # ------------------------------------------------- SILENCIO
            elif modo == Modo.SILENCIO:
                try:
                    # sigue escuchando la wake-word
                    q_wake.get(timeout=1)
                    texto = stt.transcribe().lower().strip()
                    print("🔤 (silencio)", texto)

                    # --- órdenes que SÍ rompen el silencio ---
                    if texto.startswith("despierta") or "espabila" in texto:
                        modo = Modo.REACTIVO
                        ultima_frase = responder_libre("He vuelto, colega")
                        voz.hablar(ultima_frase)

                    elif "modo automático" in texto:
                        modo = Modo.AUTOMATICO
                        ultima_frase = responder_libre("Entrando en modo automático")
                        voz.hablar(ultima_frase)

                    # puedes añadir más comandos que despierten aquí
                    # todo lo demás se ignora y sigue callado

                except queue.Empty:
                    # no se oyó wake-word → sigue mudo
                    pass

            # -------- teclas demo rápidas (a, r, s, q) --------
            k = cv2.waitKey(1) & 0xFF
            if   k == ord('a'): modo = Modo.AUTOMATICO; voz.hablar("Modo automático")
            elif k == ord('r'): modo = Modo.REACTIVO;   voz.hablar("Modo reactivo")
            elif k == ord('s'): modo = Modo.SILENCIO;   voz.hablar("Silencio")
            elif k == ord('q'): break

    finally:
        cam.release()
        cv2.destroyAllWindows()

# --------------------------------------------------------------------------
if __name__ == "__main__":
    main()
