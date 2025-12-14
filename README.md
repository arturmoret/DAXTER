# DAXTER – Talking Smart Glasses with Vision, Game, and Cloned Voice

> A **hands‑free** assistant that sees, listens, and answers with personality.
> Listening modes, automatic description, OCR, dominant color, screenshots,
> video clips, an **“I Spy” mini‑game**, and live switching between **local voice** ↔ **cloned voice (ElevenLabs)**.
> Ready for PC and prepared for **Raspberry Pi 4**.

---

## Features

* **Wake word** (“Hey colega”) with Picovoice Porcupine.
* **Modes**:
  * **Reactive**: waits and responds to commands.
  * **Automatic**: looks and describes every *N* seconds, with a short window for commands.
  * **Silent**: does not speak (but still listens for “wake up” or “mode X”).
  * **Frog**: only goes *croak* (just because!).
  * **Game**: “**I Spy**” using the camera (guess it or give up).
* **Vision**:
  * Object detection with **YOLOv5**.
  * **OCR** with EasyOCR (“what does it say?”).
  * **Dominant color** (“what color is it?”).
* **Captures**:
  * **Photos** saved to disk.
  * Short **videos** (5 s) saved to disk.
* **Voice**:
  * **Local** (pyttsx3, offline).
  * **Cloned** (ElevenLabs, online). Switches in real time: “real voice/Daxter voice” ↔ “robot voice”.
* **Anti‑echo** and **frame freshness**: prevents TTS from contaminating STT and drops stale frames (no “photos from the past”).

---

## Architecture (high level)

```
src/
├─ main.py # main loop + modes
├─ ai/
│ └─ llm.py # phrases and style (Daxter)
├─ audio/
│ ├─ stt.py # SpeechRecognizer (STT)
│ ├─ tts_factory.py # get_tts()/switch_tts()
│ ├─ tts_local.py # TTS pyttsx3 (offline)
│ ├─ tts_eleven.py # TTS ElevenLabs (online)
│ ├─ wake.py # WakeWordListener (Porcupine)
│ └─ sfx/
│ ├─ frog/ # sounds for FROG mode
│ └─ __init__.py
├─ control/
│ └─ mode_manager.py # Mode Enum {REACTIVE, ...}
├─ games/
│ └─ i_spy.py # “I Spy” mini‑game
├─ vision/
│ ├─ camera.py # camera wrapper
│ ├─ detector.py # YOLOv5
│ ├─ ocr.py # EasyOCR
│ ├─ colors.py # dominant color
│ ├─ capture.py # flush_camera(), save_frame()
│ └─ recorder.py # video recording (5s)
└─ captures/
 ├─ images/ # saved photos
 └─ videos/ # saved clips
```

---

## Requirements

* **Python 3.10–3.11** (recommended).
* **Windows / Linux / macOS** or **Raspberry Pi 4 (4GB+)**.
* **Microphone** + **camera**.
* **ffmpeg/mpv** (optional to play streamed audio from ElevenLabs).
* GPU (optional) → speeds up YOLOv5 and OCR.

---

## Installation

1. **Clone** and enter:

```bash
git clone https://github.com/your-user/daxter-glasses.git
cd daxter-glasses
```

2. **Virtual environment**:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

3. **Dependencies**:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **Models / binaries**

* YOLOv5 downloads the first time (torch hub).
* EasyOCR downloads its weights on first use.
* For ElevenLabs streaming playback: install **mpv** or **ffmpeg** (optional).

---

## Environment variables

Create a `.env` file at the project root (or set system env vars):

```ini
# Wake word (Picovoice Porcupine)
PV_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ElevenLabs (optional, only if you will use the cloned voice)
ELEVENLABS_API_KEY=elevenlabssssssssssssssssss
ELEVENLABS_VOICE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx

# Default language (optional)
LANG=es_ES
```

> The **wake word** file is expected at `src/audio/hey_colega.ppn`.

---

## Run

```bash
python src/main.py
```

* In the console you will see: **“Press P to power on (Q to quit)”**.
* Press **P** to start; **Q** exits the process.

---

## Command guide (cheat‑sheet)

> Always start with the wake word (button + “Hey colega…”) — internally `WakeWordListener` pushes an event into a queue and STT captures the phrase.

### Switch **mode**

* “**reactive mode**”
* “**automatic mode**” / “**autonomous mode**”
* “**silent mode**”
* “**frog mode**”

### Wake up from silence

* “**wake up**” / “**snap out of it**”

### **Voice**

* Enable cloned: “**real voice**” / “**Daxter voice**” / “**speak properly**”
* Back to local: “**robot voice**” / “**normal voice**” / “**speak robot**”

### **Vision / camera**

* “**what’s in front of me**” → YOLOv5
* “**take a photo**” → saves to `src/captures/images/`
* “**record a video**” → 5s clip to `src/captures/videos/`
* “**what does it say**” / “**read the sign**” → OCR + read aloud
* “**what color is it**” / “**dominant color**” → dominant color of the current frame

### **Game**

* “**I spy**” → enters **GAME** mode:
  * Daxter: “I spy something that starts with the letter X! What is it?”
  * You can answer (correct), miss (retries), or give up (“**I give up / I don’t know / no idea**”).
  * Daxter ends by announcing the solution and returns to **reactive**.

### **Other**

* “**repeat**” → reads the last phrase again (in FROG mode: croaks again).

---

## Implementation details that matter

### Frame freshness

* Before taking a photo / OCR / dominant color, the system calls `flush_camera(n=5)` and **then** reads the current frame. This avoids “frames from the past” when the camera has buffered frames.

### Anti‑echo TTS→STT

* Short pauses and **synchronous** calls (e.g., `async_=False`) for key phrases to avoid *feedback loops* between speaking and listening.

### `safe_imshow`

* In environments without a window backend (WSL/SSH), `cv2.imshow` can fail. A wrapper catches the error so execution continues.

### Live voice switching

* `audio/tts_factory.py` exposes:
  * `get_tts()` → current instance (local or ElevenLabs).
  * `switch_tts("local"|"eleven")` → switches.
* **Voice commands** call `switch_tts` without restarting the process.

---

## Output folders

```
src/captures/
├─ images/
│ └─ YYYYMMDD_HHMMSS.jpg
└─ videos/
 └─ YYYYMMDD_HHMMSS.mp4
```

---

## Typical flow

1. Power on (P).
2. “Hey colega, **what’s in front of me**” → describes detections.
3. “Hey colega, **real voice**” → enables ElevenLabs.
4. “Hey colega, **what does it say**” → OCR, reads aloud.
5. “Hey colega, **I spy**” → play for a bit.
6. “Hey colega, **take a photo**” → image saved to disk.
7. “Hey colega, **automatic mode**” → describes every *COOLDOWN* s.
8. “Hey colega, **silent mode**” → quiet. Say “**wake up**” to return.

---

## Raspberry Pi 4 (ready)

> Tested/optimized for **Raspberry Pi 4 Model B (4GB)**. Requirements and notes:

* **OS:** Raspberry Pi OS (Bookworm), 64‑bit recommended.
* **Python:** 3.11 recommended (use `pyenv` or the system version).
* **Camera:** CSI (libcamera) or USB UVC.
* **Audio:** USB mic or HAT; speaker or jack/HDMI.

### System packages

```bash
sudo apt update
sudo apt install -y python3-venv python3-dev build-essential \
 libopenblas-dev libatlas-base-dev libjpeg-dev zlib1g-dev \
 libtiff5-dev libavformat-dev libavdevice-dev libavcodec-dev \
 libswscale-dev libgtk-3-dev portaudio19-dev ffmpeg
```

### Environment + deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install -r requirements_rpi.txt # (tuned list for ARMv7/ARM64)
```

### Performance tips on Pi

* Use **YOLOv5n** or reduce input resolution in `vision/detector.py`.
* Increase `COOLDOWN` (e.g., 15–20 s) for automatic mode.
* EasyOCR runs on CPU: **limit OCR** to on-demand (“what does it say?”).
* Consider enabling **Vulkan GPU** if you use compatible libraries, or switch to **tflite/ncnn** models if needed (future roadmap).

---

## Troubleshooting

**OpenCV “The function is not implemented (cvShowImage/cvDestroyAllWindows)”**
→ No GUI backend is available. Use `safe_imshow` (already in the code), or install `libgtk-3-dev` (Linux) / only use `imshow` if a desktop environment is present. On Windows, avoid `destroyAllWindows()` if you never opened windows.

**Pandas/Numpy “dtype size changed”**
→ Binary incompatibility. Run:

```bash
pip install --upgrade --force-reinstall numpy pandas
```

**ElevenLabs 401 “needs_authorization”**
→ Missing `ELEVENLABS_API_KEY` in the environment. Create `.env` or export the variable.

**No ElevenLabs voice playback**
→ Install `mpv` or `ffmpeg`, or use the method that saves WAV to disk and plays it with `playsound`.

**“Photo from the past”**
→ Make sure the command uses `flush_camera(...)` (it already does in `main`).

**Wake word doesn’t trigger**
→ Check `PV_ACCESS_KEY` and the `.ppn` path. Reduce background noise.

---

## Roadmap (next ideas)

* Local **Whisper** (tiny/base) for offline STT.
* **Object tracking** and “tour guide” narration.
* **AR overlays** (bounding boxes and labels on-device).
* **Wise mode**: “zen mentor” style answers.
* Simplified **indoor navigation** (BLE beacons).
* Additional **voice training**.

---

## Contributing

1. Fork and create a branch: `feat/my-idea`.
2. Run `ruff`/`black` (if you feel like it).
3. Open a PR with a clear description + test steps.

---

## License

Pick the one you prefer (MIT recommended).
Include responsible use notes for **image/voice recording** and **OCR of sensitive content**.

---

## Credits

* **YOLOv5** – Ultralytics.
* **EasyOCR** – Jaided AI.
* **Porcupine** (wake word) – Picovoice.
* **ElevenLabs** (cloned voice).
* Open-source community.

---

## Appendix: key variables and paths

* `PV_ACCESS_KEY` – Porcupine key.
* `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID` – cloned voice.
* `src/audio/hey_colega.ppn` – wake word.
* Captures: `src/captures/images/` and `src/captures/videos/`.

---

If you made it this far: **thank you**. Put on the glasses, say **“Hey colega”**… and let Daxter do the rest.
