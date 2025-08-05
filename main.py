# src/main.py
from __future__ import annotations
import os, cv2, time, queue, threading, msvcrt, warnings

from audio.tts      import GestorVoz
from audio.wake     import WakeWordListener
from audio.stt      import SpeechRecognizer
from vision.camera   import Camera
from vision.detector import DetectorYOLO
from control.mode_manager import Modo
from ai.llm import (
    saludo_boot, saludo_listo,
    sin_objetos, describe, responder_libre
)

# ------------------------------------------------------------------ CONFIG
NOMBRES   = {0: "person", 9: "traffic light", 11: "stop sign", 15: "cat", 16: "dog"}
COOLDOWN  = 15                                                # cada 10 s en automático
WAKE_KEY  = os.getenv("PV_ACCESS_KEY")
WAKE_PPN  = "src/audio/hey_colega.ppn"
if not WAKE_KEY:
    raise RuntimeError("❌ Falta PV_ACCESS_KEY")

warnings.filterwarnings("ignore", message=".*autocast")  # limpia warning torch

# ------------------------------- cambio genérico de modo por “modo X …”
def cambiar_modo_por_palabra(texto: str, voz: GestorVoz) -> bool:
    global modo, ultima_frase
    if not texto.startswith("modo "):
        return False

    palabra = texto.split(" ", 1)[1].strip()

    mapping = {
        ("reactivo",):          Modo.REACTIVO,
        ("automatico", "automático"): Modo.AUTOMATICO,
        ("silencio", "mute", "callate", "cállate"): Modo.SILENCIO,
    }
    for aliases, destino in mapping.items():
        if any(palabra.startswith(a) for a in aliases):
            modo = destino
            tag = {Modo.REACTIVO:"reactivo",Modo.AUTOMATICO:"automático",Modo.SILENCIO:"silencio"}[destino]
            ultima_frase = responder_libre(f"Modo {tag} activado")
            voz.hablar(ultima_frase)
            return True
    # palabra desconocida → no cambia
    return False

# ----------------------------------------------------------------- wake hilo
def lanzar_wake_word(q_wake: queue.Queue):
    listener = WakeWordListener(WAKE_KEY, WAKE_PPN)
    listener.start(); print("🔊 Wake-word listener activo…")
    while True:
        if listener.heard_wake():
            q_wake.put(True)

# --------------------------------------------------------------- botón (P)
def esperar_encendido():
    print("Pulsa P para encender (Q para salir)…")
    while True:
        if msvcrt.kbhit():
            k = msvcrt.getch().lower()
            if k == b'p': return
            if k == b'q': exit()

# ------------------------------------------------------------------- main
def main():
    esperar_encendido()

    voz = GestorVoz()
    stt = SpeechRecognizer()
    voz.hablar(saludo_boot(), async_=False)

    cam = Camera()
    det = DetectorYOLO(classes=list(NOMBRES.keys()))
    for _ in range(15): cam.get_frame()
    voz.hablar(saludo_listo())

    q_wake = queue.Queue()
    threading.Thread(target=lanzar_wake_word, args=(q_wake,), daemon=True).start()

    global modo, ultima_frase          # para cambiar_modo_por_palabra
    modo = Modo.REACTIVO
    ultima_frase = ""
    ultimo_aviso: dict[int,float] = {}

    try:
        while True:
            # ------------------------------------------------ AUTO
            if modo == Modo.AUTOMATICO:
                frame = cam.get_frame();  ahora = time.time()
                frame_det, act = det.detect(frame)
                validas = {c for c in act if ahora-ultimo_aviso.get(c,0)>COOLDOWN}
                if validas:
                    objs = [NOMBRES[c] for c in validas]
                    ultima_frase = describe(objs); voz.hablar(ultima_frase)
                    for c in validas: ultimo_aviso[c]=ahora
                cv2.imshow("Detección", frame_det)

                # escucha wake-word sin bloquear
                try:
                    q_wake.get_nowait()
                    texto = stt.transcribe().lower().strip()
                    print("🔤 (auto)", texto)
                    if cambiar_modo_por_palabra(texto, voz):
                        continue
                    if texto.startswith(("para","detente")):
                        modo = Modo.REACTIVO
                        ultima_frase = responder_libre("Dejando el modo automático")
                        voz.hablar(ultima_frase)
                except queue.Empty:
                    pass

            # ------------------------------------------------ REACTIVO
            elif modo == Modo.REACTIVO:
                try:
                    q_wake.get(timeout=1)
                    texto = stt.transcribe().lower().strip()
                    print("🔤", texto)
                    if cambiar_modo_por_palabra(texto, voz):
                        continue
                    if not texto:
                        voz.hablar("No te he oído, tronco"); continue

                    if texto in {"que tengo delante","qué tengo delante"}:
                        frame = cam.get_frame()
                        frame_det, act = det.detect(frame)
                        ultima_frase = describe([NOMBRES[c] for c in act]) if act else sin_objetos()
                        voz.hablar(ultima_frase)
                        cv2.imshow("Detección", frame_det); cv2.waitKey(1)
                    elif texto.startswith(("callate","cállate")):
                        modo = Modo.SILENCIO
                        ultima_frase = responder_libre("Voy a callarme"); voz.hablar(ultima_frase)
                    elif "repite" in texto:
                        voz.hablar(ultima_frase or responder_libre("No dije nada"))
                    else:
                        ultima_frase = responder_libre(texto); voz.hablar(ultima_frase)
                except queue.Empty:
                    pass

            # ------------------------------------------------ SILENCIO
            elif modo == Modo.SILENCIO:
                try:
                    q_wake.get(timeout=1)
                    texto = stt.transcribe().lower().strip()
                    print("🔤 (silencio)", texto)
                    if cambiar_modo_por_palabra(texto, voz):
                        continue
                    if texto.startswith(("despierta","espabila")):
                        modo = Modo.REACTIVO
                        ultima_frase = responder_libre("He vuelto, colega"); voz.hablar(ultima_frase)
                except queue.Empty:
                    pass

            # ---------------- teclas demo
            k = cv2.waitKey(1) & 0xFF
            if   k==ord('a'): modo=Modo.AUTOMATICO; voz.hablar("Modo automático")
            elif k==ord('r'): modo=Modo.REACTIVO;   voz.hablar("Modo reactivo")
            elif k==ord('s'): modo=Modo.SILENCIO;   voz.hablar("Silencio")
            elif k==ord('q'): break

    finally:
        cam.release(); cv2.destroyAllWindows()

# -------------------------------------------------------------------------
if __name__ == "__main__":
    main()
