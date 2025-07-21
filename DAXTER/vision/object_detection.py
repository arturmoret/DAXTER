import torch
import cv2

class DetectorYOLO:
    def __init__(self, clases_interes):
        self.modelo = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        self.modelo.classes = clases_interes
        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            raise RuntimeError("The camera couln't be opened")

    def obtener_frame_y_clases(self):
        ret, frame = self.cap.read()
        if not ret:
            return None, set()

        resultados = self.modelo(frame)
        resultados.render()
        clases_detectadas = set(int(x[5]) for x in resultados.xyxy[0])

        return frame, clases_detectadas

    def mostrar_frame(self, frame, ventana='Detection'):
        cv2.imshow(ventana, frame)

    def liberar(self):
        self.cap.release()
        cv2.destroyAllWindows()
