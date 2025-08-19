import cv2
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
        time.sleep(1)  # allow time for the video file to open

    def detect_vehicles(self):
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                self.cap.release()
                print("Video ended")
                return [], None  # Always return a tuple

            self.frame_count += 1
            if self.frame_count % self.frame_interval != 0:
                continue

            detections = []
            results = self.model(frame)
            for result in results:
                for box in result.boxes:
                    conf = box.conf[0].item()
                    cls = int(box.cls[0].item())
                    label = self.model.names[cls]
                    if conf > self.confidence and label in self.weight_mapping:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        detections.append({
                            "type": label,
                            "weight": self.weight_mapping[label],
                            "bbox": (x1, y1, x2, y2),
                            "conf": conf
                        })
                        # Draw bounding box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(
                            frame,
                            f"{label} {conf:.2f}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 255, 0),
                            2
                        )
                return detections, frame
        return [], None  # In case the video never opens