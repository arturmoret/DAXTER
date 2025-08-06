# src/main.py
from __future__ import annotations
import os, cv2, time, queue, threading, msvcrt, warnings, random
from vision.capture import flush_camera, save_frame
from audio.tts       import GestorVoz
from audio.wake      import WakeWordListener
from audio.stt       import SpeechRecognizer
from vision.camera   import Camera
from vision.detector import DetectorYOLO
from control.mode_manager import Modo                # Enum con JUEGO añadido
from vision.capture import (save_frame)
from ai.llm import (
    saludo_boot, saludo_listo,
    sin_objetos, describe, responder_libre
)

# ------------------------------------------------------------------ CONFIG
NOMBRES   = {0: "persona", 9: "semaforo", 11: "señal de stop",
             15: "gato",   16: "perro"}
COOLDOWN   = 10            # intervalo REAL entre descripciones (s)
LISTEN_SEC = 3             # ventana tras hablar para oír órdenes (s)

WAKE_KEY = os.getenv("PV_ACCESS_KEY")
WAKE_PPN = "src/audio/hey_colega.ppn"
if not WAKE_KEY:
    raise RuntimeError("❌ Falta PV_ACCESS_KEY.")

warnings.filterwarnings("ignore", message=".*autocast")

# --------------------------- cambio genérico  “modo X …” ---------------
def cambiar_modo_por_palabra(texto: str, voz: GestorVoz) -> bool:
    global modo, ultima_frase
    if not texto.startswith("modo "):
        return False

    palabra = texto.split(" ", 1)[1].strip()
    mapping = {
        ("reactivo",):                    Modo.REACTIVO,
        ("automatico", "automático", "autonomo","autónomo"):     Modo.AUTOMATICO,
        ("silencio", "mute", "callate", "cállate"): Modo.SILENCIO,
        ("sapo", "rana"):                 Modo.SAPO,
    }

    for aliases, destino in mapping.items():
        if any(palabra.startswith(a) for a in aliases):
            modo = destino

            # ---- MODO SAPO: solo croac de bienvenida ----
            if destino is Modo.SAPO:
                from audio.sfx import croak
                croak()
                ultima_frase = ""
                return True

            # ---- Otros modos: sigue con TTS normal -------
            tag = {
                Modo.REACTIVO:   "reactivo",
                Modo.AUTOMATICO: "automático",
                Modo.SILENCIO:   "silencio",
            }[destino]

            ultima_frase = responder_libre(f"Modo {tag} activado")
            voz.hablar(ultima_frase)
            return True
    return False


# --------------------------------------------------- hilo Wake-word
def lanzar_wake_word(q_wake: queue.Queue):
    listener = WakeWordListener(WAKE_KEY, WAKE_PPN)
    listener.start(); print("🔊 Wake-word listener activo…")
    while True:
        if listener.heard_wake():
            q_wake.put(True)

# --------------------------------------------------- botón virtual (P)
def esperar_encendido():
    print("Pulsa P para encender (Q para salir)…")
    while True:
        if msvcrt.kbhit():
            k = msvcrt.getch().lower()
            if k == b'p': return
            if k == b'q': exit()

def safe_imshow(title: str, img):
    """Muestra la imagen sin romperse si no hay backend de ventana."""
    try:
        cv2.imshow(title, img)
        cv2.waitKey(1)
    except cv2.error:
        pass

# ------------------------------------------------------------------- MAIN
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

    global modo, ultima_frase
    modo = Modo.REACTIVO
    ultima_frase = ""
    ultimo_aviso: dict[int, float] = {}

    try:
        while True:

            # -------------------------------------------------- MODO AUTOMÁTICO
            if modo == Modo.AUTOMATICO:
                ciclo_ini = time.time()

                # 1· captura + detección
                frame = cam.get_frame()
                frame_det, act = det.detect(frame)
                objs = [NOMBRES[c] for c in act] if act else []

                # 2· habla
                if objs:
                    ultima_frase = describe(objs)
                    voz.hablar(ultima_frase)

                safe_imshow("Detección", frame_det)

                # 3· escucha LISTEN_SEC
                escuchado = False
                escucha_fin = time.time() + LISTEN_SEC
                while time.time() < escucha_fin:
                    try:
                        q_wake.get(timeout=0.2)
                        texto = stt.transcribe().lower().strip()
                        print("🔤 (auto)", texto)

                        if cambiar_modo_por_palabra(texto, voz):
                            escuchado = True; break

                        if texto.startswith(("para","detente","reactivo")):
                            modo = Modo.REACTIVO
                            ultima_frase = responder_libre("Dejando modo automático")
                            voz.hablar(ultima_frase); escuchado=True; break

                        if texto.replace(" ", "").startswith(("callate","cállate","silencio","apagate","apágate")):
                            modo = Modo.SILENCIO
                            ultima_frase = responder_libre("Vale, me callo")
                            voz.hablar(ultima_frase); escuchado=True; break
                    except queue.Empty:
                        pass

                if escuchado:
                    continue  # nuevo modo

                # 4· pausa hasta COOLDOWN
                restante = COOLDOWN - (time.time() - ciclo_ini)
                if restante > 0:
                    time.sleep(restante)

            # -------------------------------------------------- MODO REACTIVO
            elif modo == Modo.REACTIVO:
                try:
                    q_wake.get(timeout=1)
                    texto = stt.transcribe().lower().strip()
                    print("🔤", texto)

                    # --- minijuego ---
                    if "veo veo" in texto:
                        modo = Modo.JUEGO
                        continue

                    if cambiar_modo_por_palabra(texto, voz):
                        continue
                    if not texto:
                        voz.hablar("No te he oído, tronco"); continue

                    if texto in {"que tengo delante","qué tengo delante"}:
                        frame = cam.get_frame()
                        frame_det, act = det.detect(frame)
                        ultima_frase = describe([NOMBRES[c] for c in act]) if act else sin_objetos()
                        voz.hablar(ultima_frase)
                        safe_imshow("Detección", frame_det)

                    elif texto.startswith(("callate","cállate")):
                        modo = Modo.SILENCIO
                        ultima_frase = responder_libre("Voy a callarme"); voz.hablar(ultima_frase)

                    elif "repite" in texto:
                        voz.hablar(ultima_frase or responder_libre("No dije nada"))

                    elif "saca una foto" in texto or "haz una foto" in texto or "sacó una foto" in texto:
                        
                        flush_camera(cam, n=5)             # ← descarta ~5 frames (~200 ms)
                        frame = cam.get_frame()            # ← ahora sí el último instantáneo
                        if frame is not None:
                            ruta = save_frame(frame)
                            ultima_frase = responder_libre("¡Te he hecho una foto, colega!")
                            voz.hablar(ultima_frase)
                            print(f"📸  Guardada en {ruta}")
                        else:
                            voz.hablar("No pude capturar la imagen, tronco")

                    elif "graba un video" in texto or "graba un vídeo" in texto:
                        from vision.recorder import record_clip
                        ruta = record_clip(cam, seconds=5, fps=30)
                        ultima_frase = responder_libre("Vídeo grabado, colega")
                        voz.hablar(ultima_frase)
                        print(f"🎥  Guardado en {ruta}")

                    elif any(k in texto for k in ("qué pone", "que pone", "lee el cartel")):
                        flush_camera(cam, n=5)   
                        frame = cam.get_frame()
                        if frame is not None:
                            from vision.ocr import read_text
                            texto_leido = read_text(frame)
                            print(f"📝 OCR bruto ({len(texto_leido)} chars):\n{texto_leido}\n")


                            if texto_leido:
                                prefacio = responder_libre("Claro, déjame que lo lea alto y claro")
                                voz.hablar(prefacio, async_=False)          # comentario
                                voz.hablar_largo(texto_leido)               # ← NUEVO
                                ultima_frase = texto_leido

                            else:
                                ultima_frase = responder_libre("No veo texto claro, colega")
                                voz.hablar(ultima_frase)
                        else:
                            voz.hablar("No pude capturar imagen, tronco")

                    elif "de qué color" in texto or "color predominante" in texto or "que color tengo delante" in texto:
                        flush_camera(cam, n=5)
                        frame = cam.get_frame()
                        if frame is not None:
                            from vision.colors import dominante
                            color = dominante(frame)
                            
                            # 2) nombre del color, sin pasar por LLM
                            frase_color = f"El color predominante es {color}"
                            voz.hablar(frase_color, async_=False)

                            ultima_frase = frase_color            # para “repite…”
                        else:
                            voz.hablar("No puedo ver el color, tronco")

                    else:
                        ultima_frase = responder_libre(texto); voz.hablar(ultima_frase)
                except queue.Empty:
                    pass

            # -------------------------------------------------- MODO SILENCIO
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

            # -------------------------------------------------- MODO JUEGO
            elif modo == Modo.JUEGO:
                from games.veo_veo import start
                start(det, cam, voz, stt, NOMBRES)
                modo = Modo.REACTIVO
                continue

            # -------------------------------------------------- MODO SAPO
            elif modo == Modo.SAPO:
                try:
                    q_wake.get(timeout=1)
                    texto = stt.transcribe().lower().strip()
                    print("🔤 (sapo)", texto)

                    # ¿cambio de modo?
                    if cambiar_modo_por_palabra(texto, voz):
                        continue

                    from audio.sfx import croak
                    if "repite" in texto:
                        croak(); continue

                    # 1-3 croacs aleatorios
                    for _ in range(random.randint(1, 2)):
                        croak()

                except queue.Empty:
                    pass


    finally:
        cam.release(); cv2.destroyAllWindows()

# -------------------------------------------------------------------------
if __name__ == "__main__":
    main()
