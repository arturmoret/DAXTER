# src/vision/colors.py
import cv2, numpy as np

# Diccionario básico HSV → nombre
COLOR_TABLE = {
    "rojo":       [(0, 50, 50), (10, 255, 255)],
    "naranja":    [(11, 50, 50), (25, 255, 255)],
    "amarillo":   [(26, 50, 50), (34, 255, 255)],
    "verde":      [(35, 50, 50), (85, 255, 255)],
    "cian":       [(86, 50, 50), (100, 255, 255)],
    "azul":       [(101, 50, 50), (130, 255, 255)],
    "morado":     [(131, 50, 50), (160, 255, 255)],
    "rosa":       [(161, 50, 50), (179, 255, 255)],
}

def dominante(frame_bgr: np.ndarray) -> str:
    """
    Devuelve el nombre del color dominante aproximado en la imagen BGR.
    Toma región central (50 %) para evitar bordes.
    """
    h, w, _ = frame_bgr.shape
    crop = frame_bgr[h//4:3*h//4, w//4:3*w//4]          # zona central
    hsv  = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    hist = {}

    for nombre, (lo, hi) in COLOR_TABLE.items():
        mask = cv2.inRange(hsv, np.array(lo), np.array(hi))
        hist[nombre] = int(mask.sum())                  # suma de píxeles

    # Color con más píxeles
    return max(hist, key=hist.get)
