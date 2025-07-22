from audio.textToSpeech import GestorVoz
from vision.object_detection import DetectorYOLO
import cv2
import time
import warnings

COOLDOWN = 5       

warnings.filterwarnings("ignore", category=FutureWarning)

def main():

    nombres = {0: "person", 9: "traffic light", 11: "stop sign", 15: "cat", 16: "dog"}

    voz = GestorVoz()
    detector = DetectorYOLO(clases_interes=list(nombres.keys()))

    vistas_anterior = set()
    ultimo_aviso = {}          

    while True:
        frame, actuales = detector.obtener_frame_y_clases()

        if frame is None:
            break

        nuevas = actuales - vistas_anterior

        nuevas_validas = set()
        ahora = time.time()
        for c in nuevas:
            if ahora - ultimo_aviso.get(c, 0) > COOLDOWN:
                nuevas_validas.add(c)

        if nuevas_validas:
            voz.decir(nuevas_validas, nombres)
            for c in nuevas_validas:
                ultimo_aviso[c] = time.time()

        if not actuales:
            vistas_anterior.clear()
        else:
            vistas_anterior = actuales

        detector.mostrar_frame(frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    detector.liberar()

if __name__ == "__main__":
    main()
