import torch

class DetectorYOLO:
    def __init__(self, classes, conf=0.45, device=None):
        self.model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True)
        self.model.conf = conf
        if device:
            self.model.to(device)
        self.model.classes = classes          

    def detect(self, frame, size=640):
        res = self.model(frame, size=size)
        annotated = res.render()[0]
        classes = {int(det[-1]) for det in res.xyxy[0]}
        return annotated, classes
