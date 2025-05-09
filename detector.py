import cv2
import os
import time
from ultralytics import YOLO

class WeightDetector:
    def __init__(self, video_path, confidence=0.5, frequency=3):
        self.video_path = video_path
        self.confidence = confidence
        self.frequency = frequency
        self.weight_mapping = {
            "car": 2,
            "bus": 10,
            "motorcycle": 1,
            "truck": 10
        }

        self.model = YOLO("yolov8n.pt")
        self.cap = cv2.VideoCapture(video_path)
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.frame_interval = int(fps * frequency)
        self.frame_count = 0
        time.sleep(1)

    def detect_weight(self):
        """Processes frames and calculates total detected weight."""
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                self.cap.release()
                print(f"Video ended")
                return None

            self.frame_count += 1
            if self.frame_count % self.frame_interval != 0:
                continue

            total_weight = 0
            results = self.model(frame)
            for result in results:
                for box in result.boxes:
                    conf = box.conf[0].item()
                    cls = int(box.cls[0].item())
                    label = self.model.names[cls]

                    if conf > self.confidence and label in self.weight_mapping:
                        total_weight += self.weight_mapping[label]

            return total_weight