from pathlib import Path
from datetime import datetime
import cv2

CAP_DIR = Path(__file__).resolve().parent.parent / "captures"
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
