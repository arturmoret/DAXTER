import torch
import cv2

class DetectorYOLO:

    def __init__(self, clases_interes):
        self.modelo = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        self.modelo.conf = 0.45                  
        self.modelo.classes = clases_interes      
        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            raise RuntimeError("No se pudo abrir la cámara")

    def obtener_frame_y_clases(self):
        ok, frame = self.cap.read()
        if not ok:
            return None, set()

        res = self.modelo(frame, size=640)
        
        img_bgr = res.render()[0]
        clases_detectadas = {int(x[-1]) for x in res.xyxy[0]}  
        return img_bgr, clases_detectadas

    def mostrar_frame(self, frame, ventana='Detection'):
        cv2.imshow(ventana, frame)

    def liberar(self):
        self.cap.release()
        cv2.destroyAllWindows()
