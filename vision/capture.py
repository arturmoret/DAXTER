from pathlib import Path
from datetime import datetime
import cv2

CAP_DIR = Path(__file__).resolve().parent.parent / "captures" / "images"
CAP_DIR.mkdir(exist_ok=True)

def save_frame(frame) -> str:
    """
    Guarda un frame BGR (numpy) en carpetas /captures y
    devuelve la ruta (str). Nombre: YYYYMMDD_HHMMSS.jpg
    """
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    fn  = CAP_DIR / f"{ts}.jpg"
    cv2.imwrite(str(fn), frame)
    return str(fn)

# src/vision/capture.py  (añade al final del archivo)
def flush_camera(camera, n=5):
    """
    Descarta los últimos `n` frames que queden en el buffer de la cámara.
    Así la próxima llamada a .get_frame() será realmente ‘en tiempo real’.
    """
    for _ in range(n):
        _ = camera.get_frame()
