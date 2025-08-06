# src/vision/recorder.py
from pathlib import Path
from datetime import datetime
import cv2, time

VID_DIR = Path(__file__).resolve().parent.parent / "captures" / "videos"
VID_DIR.mkdir(parents=True, exist_ok=True)

def record_clip(camera, seconds=5, fps=30) -> str:
    """
    Graba `seconds` del objeto `camera` (método get_frame()) en MP4.
    Devuelve la ruta del archivo guardado.
    """
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = VID_DIR / f"{ts}.mp4"

    width  = int(camera.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(camera.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out    = cv2.VideoWriter(str(path), fourcc, fps, (width, height))

    t_end = time.time() + seconds
    while time.time() < t_end:
        frame = camera.get_frame()
        if frame is None:
            break
        out.write(frame)

    out.release()
    return str(path)
