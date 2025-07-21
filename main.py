from audio.textToSpeech import GestorVoz
from vision.object_detection import DetectorYOLO
import cv2

def main():
    nombres_clases = { 0: "persona", 9: "semáforo", 11: "señal de stop", 15: "gato", 16: "perro" }

    voz = GestorVoz()
    detector = DetectorYOLO(clases_interes=[0, 9, 11, 15, 16])

    while True:
        frame, clases_detectadas = detector.obtener_frame_y_clases()
        if frame is None:
            break

        voz.decir_si_corresponde(clases_detectadas, nombres_clases)
        detector.mostrar_frame(frame)

        if cv2.waitKey(1) == ord('q'):
            break

    detector.liberar()

if __name__ == "__main__":
    main()
