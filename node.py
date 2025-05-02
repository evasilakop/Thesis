# node.py
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
        self.output_dir = "images"
        os.makedirs(self.output_dir, exist_ok=True)

        self.model = YOLO("yolov8n.pt")
        self.cap = cv2.VideoCapture(video_path)
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.frame_interval = int(fps * frequency)
        self.frame_count = 0
        self.frame_number = 0
        time.sleep(1)

    def __iter__(self):
        return self

    def __next__(self):
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                self.cap.release()
                raise StopIteration

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
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cv2.rectangle(frame, (x1, y1), (x2, y2), 
                                    (0, 255, 0), 2)
                        cv2.putText(frame, f"{label}: {conf:.2f}",
                                    (x1, y1-10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                    (0, 255, 0), 2)

            self.frame_number += 1
            output_path = os.path.join(self.output_dir, 
                                  f"Frame{self.frame_number}.jpg")
            cv2.imwrite(output_path, frame)

            return total_weight

        self.cap.release()
        raise StopIteration

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--video", required=True, 
                        help="Path to input video")
    parser.add_argument("-c", "--confidence", type=float, default=0.5)
    parser.add_argument("-f", "--frequency", type=float, default=3)
    args = vars(parser.parse_args())

    detector = WeightDetector(args["video"],
                              args["confidence"],
                              args["frequency"])

    for weight in detector:
        print(f"Detected weight: {weight}")

    cv2.destroyAllWindows()