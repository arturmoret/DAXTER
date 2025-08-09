# DAXTER – Gafas parlantes con visión, juego y voz clonada

> Un asistente **hands‑free** que ve, escucha y contesta con personalidad.
> Modos de escucha, descripción automática, OCR, color predominante, capturas,
> clips de vídeo, **minijuego “veo‑veo”** y conmutación de **voz local** ↔ **voz clonada (ElevenLabs)** en vivo.
> Listo para PC y preparado para **Raspberry Pi 4**.

---

## Características

* **Wake word** (“Hey colega”) con Picovoice Porcupine.
* **Modos**:
* **Reactivo**: espera y responde a órdenes.
* **Automático**: mira y describe cada *N* segundos, con ventana corta para órdenes.
* **Silencio**: no habla (pero sigue escuchando “despierta” o “modo X”).
* **Sapo**: solo hace *croac* (¡porque sí !).
* **Juego**: “**veo‑veo**” con la cámara (acierta o ríndete).
* **Visión**:
* Detección de objetos con **YOLOv5**.
* **OCR** con EasyOCR (“qué pone”).
* **Color predominante** (“de qué color es”).
* **Capturas**:
* **Fotos** a disco.
* **Vídeos** cortos (5 s) a disco.
* **Voz**:
* **Local** (pyttsx3, offline).
* **Clonada** (ElevenLabs, online). Cambia en tiempo real: “voz real/voz Daxter” ↔ “voz robot”.
* **Anti‑eco** y **frescura de frame**: evita que el TTS contamine el STT y descarta frames viejos (no verás “fotos del pasado”).

---

## Arquitectura (alto nivel)

```
src/
├─ main.py # bucle principal + modos
├─ ai/
│ └─ llm.py # frases y estilo (Daxter)
├─ audio/
│ ├─ stt.py # SpeechRecognizer (STT)
│ ├─ tts_factory.py # get_tts()/switch_tts()
│ ├─ tts_local.py # TTS pyttsx3 (offline)
│ ├─ tts_eleven.py # TTS ElevenLabs (online)
│ ├─ wake.py # WakeWordListener (Porcupine)
│ └─ sfx/
│ ├─ frog/ # sonidos del modo SAPO
│ └─ __init__.py
├─ control/
│ └─ mode_manager.py # Enum Modo {REACTIVO, ...}
├─ games/
│ └─ veo_veo.py # minijuego “veo‑veo”
├─ vision/
│ ├─ camera.py # wrapper de cámara
│ ├─ detector.py # YOLOv5
│ ├─ ocr.py # EasyOCR
│ ├─ colors.py # color predominante
│ ├─ capture.py # flush_camera(), save_frame()
│ └─ recorder.py # grabación de vídeo (5s)
└─ captures/
 ├─ images/ # fotos guardadas
 └─ videos/ # clips guardados
```

---

## Requisitos

* **Python 3.10–3.11** (recomendado).
* **Windows / Linux / macOS** o **Raspberry Pi 4 (4GB+)**.
* **Micrófono** + **cámara**.
* **ffmpeg/mpv** (opcional para reproducir audio streamed de ElevenLabs).
* GPU (opcional) → acelera YOLOv5 y OCR.

---

## Instalación

1. **Clona** y entra:

```bash
git clone https://github.com/tu-usuario/daxter-glasses.git
cd daxter-glasses
```

2. **Entorno**:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

3. **Dependencias**:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **Modelos / binarios**

* YOLOv5 se descarga la primera vez (torch hub).
* EasyOCR descargará sus pesos al primer uso.
* Para reproducir streaming ElevenLabs: instala **mpv** o **ffmpeg** (opcional).

---

## Variables de entorno

Crea un fichero `.env` en la raíz (o define variables del sistema):

```ini
# Wake word (Picovoice Porcupine)
PV_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ElevenLabs (opcional, solo si vas a usar la voz clonada)
ELEVENLABS_API_KEY=elevenlabssssssssssssssssss
ELEVENLABS_VOICE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx

# Idioma por defecto (opcional)
LANG=es_ES
```

> El archivo **wake word** se espera en `src/audio/hey_colega.ppn`.

---

## Ejecución

```bash
python src/main.py
```

* En consola verás: **“Pulsa P para encender (Q para salir)”**.
* Pulsa **P** para iniciar; **Q** cierra el proceso.

---

## Guía de comandos (cheat‑sheet)

> Siempre empieza con la wake word (botón + “Hey colega…”) —internamente `WakeWordListener` mete un evento en la cola y el STT toma la frase.

### Cambiar de **modo**

* “**modo reactivo**”
* “**modo automático**” / “**modo autónomo**”
* “**modo silencio**”
* “**modo sapo**”

### Despertar desde silencio

* “**despierta**” / “**espabila**”

### **Voz**

* Activar clonada: “**voz real**” / “**voz Daxter**” / “**habla bien**”
* Volver a local: “**voz robot**” / “**voz normal**” / “**habla robot**”

### **Visión / cámara**

* “**qué tengo delante**” → YOLOv5
* “**saca una foto** / **haz una foto**” → guarda en `src/captures/images/`
* “**graba un vídeo**” → clip 5s en `src/captures/videos/`
* “**qué pone** / **lee el cartel**” → OCR + lectura
* “**de qué color** / **color predominante**” → color dominante del frame

### **Juego**

* “**veo veo**” → entra en modo **JUEGO**:
* Daxter: “¡Veo veo algo que empieza por la letra X! ¿Qué es?”
* Puedes responder (acierto), fallar (reintentos) o rendirte (“**me rindo / no lo sé / ni idea**”).
* Daxter termina anunciando la solución y vuelve a **reactivo**.

### **Otros**

* “**repite**” → lee la última frase (en SAPO: vuelve a croar).

---

## Detalles de implementación que importan

### Frescura de frame

* Antes de sacar foto/OCR/color, se hace `flush_camera(n=5)` y **luego** se lee el frame actual. Evita “frames del pasado” cuando la cámara lleva buffer.

### Anti‑eco TTS→STT

* Pausas cortas y llamadas **sincrónicas** (p.ej. `async_=False`) en frases clave para no crear *feedback loops* entre voz y escucha.

### `safe_imshow`

* En entornos sin backend de ventana (WSL/SSH), `cv2.imshow` puede fallar. Se usa un wrapper que atrapa el error y no rompe la ejecución.

### Conmutación de voz en vivo

* `audio/tts_factory.py` expone:
* `get_tts()` → instancia actual (local o ElevenLabs).
* `switch_tts("local"|"eleven")` → conmuta.
* Los **comandos de voz** llaman a `switch_tts` sin reiniciar el proceso.

---

## Carpetas de salida

```
src/captures/
├─ images/
│ └─ YYYYMMDD_HHMMSS.jpg
└─ videos/
 └─ YYYYMMDD_HHMMSS.mp4
```

---

## Flujo típico

1. Enciendes (P).
2. “Hey colega, **qué tengo delante**” → describe detecciones.
3. “Hey colega, **voz real**” → activa ElevenLabs.
4. “Hey colega, **qué pone**” → OCR, lee en alto.
5. “Hey colega, **veo veo**” → juega un rato.
6. “Hey colega, **saca una foto**” → imagen a disco.
7. “Hey colega, **modo automático**” → describe cada *COOLDOWN* s.
8. “Hey colega, **modo silencio**” → calla. “**despierta**” para volver.

---

## Raspberry Pi 4 (preparado)

> Probado/optimizado para **Raspberry Pi 4 Model B (4GB)**. Requisitos y notas:

* **SO:** Raspberry Pi OS (Bookworm), 64‑bit recomendado.
* **Python:** 3.11 recomendado (usa `pyenv` o la versión del sistema).
* **Cámara:** CSI (libcamera) o USB UVC.
* **Audio:** micro USB o HAT; altavoz o jack/HDMI.

### Paquetes del sistema

```bash
sudo apt update
sudo apt install -y python3-venv python3-dev build-essential \
 libopenblas-dev libatlas-base-dev libjpeg-dev zlib1g-dev \
 libtiff5-dev libavformat-dev libavdevice-dev libavcodec-dev \
 libswscale-dev libgtk-3-dev portaudio19-dev ffmpeg
```

### Entorno + deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install -r requirements_rpi.txt # (lista afinada para ARMv7/ARM64)
```

### Consejos de rendimiento en Pi

* Usa **YOLOv5n** o reduce resolución de entrada en `vision/detector.py`.
* Sube `COOLDOWN` (p.ej. 15–20 s) para modo automático.
* EasyOCR va en CPU: **limitar OCR** a petición (“qué pone”).
* Considera activar **GPU Vulkan** si usas librerías compatibles, o cambiar a modelos **tflite/ncnn** si lo necesitas (futuro roadmap).

---

## Solución de problemas

**OpenCV “The function is not implemented (cvShowImage/cvDestroyAllWindows)”**
→ No hay backend GUI. Usa `safe_imshow` (ya en el código) o instala `libgtk-3-dev` (Linux) / usa `imshow` solo si hay escritorio. En Windows, evita `destroyAllWindows()` si no has abierto ventanas.

**Pandas/Numpy “dtype size changed”**
→ Incompatibilidad binaria. Haz:

```bash
pip install --upgrade --force-reinstall numpy pandas
```

**ElevenLabs 401 “needs\_authorization”**
→ Falta `ELEVENLABS_API_KEY` en entorno. Crea `.env` o exporta la variable.

**No reproduce voz ElevenLabs**
→ Instala `mpv` o `ffmpeg`, o usa el método que guarda WAV a disco y lo reproduce con `playsound`.

**Foto “del pasado”**
→ Asegúrate de que el comando usa `flush_camera(...)` (ya está en el main).

**Wake word no salta**
→ Revisa `PV_ACCESS_KEY` y la ruta del `.ppn`. Baja ruido de fondo.

---

## Roadmap (ideas próximas)

* **Whisper** local (tiny/base) para STT offline.
* **Seguimiento de objetos** y narración “tipo guía”.
* **AR overlays** (bounding boxes y etiquetas on‑device).
* **Modo Sabio**: respuestas estilo “mentor zen”.
* **Navegación indoor simplificada** (balizas BLE).
* **Entrenamiento de voces** adicionales.

---

## Contribuir

1. Haz un fork y crea rama: `feat/mi-idea`.
2. Pasa `ruff`/`black` (si te apetece).
3. PR con descripción clara + pasos de prueba.

---

## Licencia

Elige la que prefieras (MIT recomendado).
Incluye notas de uso responsable para **grabación de imágenes/voz** y **OCR de contenido sensible**.

---

## Créditos

* **YOLOv5** – Ultralytics.
* **EasyOCR** – Jaided AI.
* **Porcupine** (wake word) – Picovoice.
* **ElevenLabs** (voz clonada).
* Comunidad open‑source .

---

## Apéndice: variables y rutas clave

* `PV_ACCESS_KEY` – clave Porcupine.
* `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID` – voz clonada.
* `src/audio/hey_colega.ppn` – wake word.
* Capturas: `src/captures/images/` y `src/captures/videos/`.

---

Si llegaste hasta aquí: **gracias**. Ponte las gafas, di **“Hey colega”**… y deja que Daxter haga el resto .
