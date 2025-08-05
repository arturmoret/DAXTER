import random, time

def start(detector, camera, voz, stt, nombres,
          max_intentos=3, timeout=30):
    # ---------- elige objeto ----------
    frame = camera.get_frame()
    _, clases = detector.detect(frame)
    opciones = [nombres[c] for c in clases]

    if not opciones:
        voz.hablar("No veo nada divertido, colega.")
        return

    palabra = random.choice(opciones)
    inicial = palabra[0].upper()
    voz.hablar(f"¡Veo veo algo que empieza por la letra {inicial}!")

    # ---------- loop intentos ----------
    intentos, inicio = 0, time.time()
    while intentos < max_intentos and time.time() - inicio < timeout:
        voz.hablar("¿Qué es?")
        respuesta = stt.transcribe().lower().strip()

        if not respuesta:
            continue

        # ------- NUEVO: rendición -------
        if "me rindo" in respuesta or "no lo se" in respuesta or "ni idea" in respuesta:
            voz.hablar(f"Vale, la respuesta era {palabra}. ¡Será la próxima!")
            return

        # ------- acierto / fallo -------
        if palabra in respuesta:
            voz.hablar("¡Bingo, lo has clavado!")
            return
        else:
            intentos += 1
            voz.hablar("¡Nop, prueba otra vez!")

    voz.hablar(f"Juego terminado. Era {palabra}.")
