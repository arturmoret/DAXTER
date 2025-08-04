from audio.tts import GestorVoz
from vision.camera import Camera
from vision.detector import DetectorYOLO
import cv2
import time
import warnings

COOLDOWN = 5
warnings.filterwarnings("ignore", category=FutureWarning)

NOMBRES = {0: "person", 9: "traffic light", 11: "stop sign", 15: "cat", 16: "dog"}

def main():
    voz = GestorVoz()
    camara = Camera()
    detector = DetectorYOLO(classes=list(NOMBRES.keys()))

    vistas_anterior = set()
    ultimo_aviso = {}

    try:
        while True:
            frame = camara.get_frame()
            if frame is None:
                break

            frame_det, actuales = detector.detect(frame)

            ahora = time.time()
            validas = {c for c in actuales
                    if ahora - ultimo_aviso.get(c, 0) > COOLDOWN}

            if validas:
                voz.decir(validas, NOMBRES)
                for c in validas:
                    ultimo_aviso[c] = ahora

            cv2.imshow("Detección", frame_det)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break


    finally:
        camara.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
