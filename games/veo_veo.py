# src/games/veo_veo.py
import random, time

def start(detector, camera, voz, stt, nombres,
          max_intentos=3, timeout=30):
    """
    Minijuego 'veo-veo'.
      • Máx. `max_intentos` fallos; silencios NO cuentan.
      • Se puede rendir con “me rindo / no lo sé / ni idea”.
      • Espera hasta `timeout` segundos en total.
    """
    # ---------- elegir objeto visible ----------
    _, clases = detector.detect(camera.get_frame())
    opciones = [nombres[c] for c in clases]
    if not opciones:
        voz.hablar("No veo nada divertido, colega.", async_=False)
        return

    palabra = random.choice(opciones)        # ej. "dog"
    inicial = palabra[0].upper()             # 'D'
    voz.hablar(f"¡Veo veo algo que empieza por la letra {inicial}! ¿Que es?", async_=False)
    time.sleep(0.3)                      # breve pausa para que no grabe su propia voz

    intentos   = 0
    t_inicio   = time.time()
    
    # Pregunta SOLO una vez por intento
    while intentos < max_intentos and time.time() - t_inicio < timeout:

        # Espera respuesta válida
        respuesta = ""
        while not respuesta and time.time() - t_inicio < timeout:
            respuesta = stt.transcribe().lower().strip()

            # descarta ruido muy corto (<3 letras)
            if len(respuesta) < 4:
                respuesta = ""

        if not respuesta:                    # se acabó el tiempo global
            break

        # ------------ rendición ------------
        if any(p in respuesta for p in ("me rindo", "no lo se", "no lo sé", "ni idea")):
            voz.hablar(f"¿Ya? La respuesta era {palabra}. ¡Soy muy bueno a lo que me propongo!", async_=False)
            return

        # ------------ acierto / fallo ------------
        if palabra in respuesta:
            voz.hablar("¡Bingo, lo has clavado!", async_=False)
            return
        else:
            intentos += 1
            if intentos < max_intentos:
                voz.hablar("¡Casi colega pero no!", async_=False)

    # fin por intentos agotados o tiempo
    voz.hablar(f"Has perdido! La palabra era {palabra}.", async_=False)
