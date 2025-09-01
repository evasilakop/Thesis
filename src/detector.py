import cv2
import time
from ultralytics import YOLO


class WeightDetector:
    """ Detects vehicles in a video stream and estimates their total weight 
        according to the predetermined weight mapping for each type of vehicle.
    """
    def __init__(self, video_path, confidence=0.5, frequency=15):
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
        # frequency is in seconds: process every N seconds
        self.frame_interval = int(fps * self.frequency)
        self.frame_count = 0
        time.sleep(1)

    def detect_vehicles(self):
        """Detect vehicles in the video stream.

        Returns:
            tuple: A tuple containing a list of detected vehicles and the current frame.
        """
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
            self.draw_results_on_frame(frame, detections, results)
            return detections, frame
        return [], None # In case the video never opens

    def draw_results_on_frame(self, frame, detections, results):
        """Draws the detection results on the video frame.

        Args:
            frame (ndarray): The current video frame.
            detections (list): The list of detected vehicles.
            results (list): The results from the YOLO model.
        """
        for result in results:
            for box in result.boxes:
                conf = box.conf[0].item()
                cls = int(box.cls[0].item())
                label = self.model.names[cls]
                if conf > self.confidence and label in self.weight_mapping:
                    x1, y1, x2, y2 = self.write_label(detections, box, conf, label)
                    self.draw_bounding_box(frame, conf, label, x1, y1, x2, y2)

    def draw_bounding_box(self, frame, conf, label, x1, y1, x2, y2):
        """Draws a bounding box around the detected vehicle.

        Args:
            frame (ndarray): The current video frame.
            conf (float): The confidence score of the detection.
            label (str): The label of the detected vehicle.
            x1 (int): The x-coordinate of the top-left corner of the bounding box.
            y1 (int): The y-coordinate of the top-left corner of the bounding box.
            x2 (int): The x-coordinate of the bottom-right corner of the bounding box.
            y2 (int): The y-coordinate of the bottom-right corner of the bounding box.
        """
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame,
                    f"{label} {conf:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                    )

    def write_label(self, detections, box, conf, label):
        """Writes the label and bounding box information to the detections list.

        Args:
            detections (list): The list of detected vehicles.
            box (Box): The bounding box of the detected vehicle.
            conf (float): The confidence score of the detection.
            label (str): The label of the detected vehicle.

        Returns:
            tuple: The coordinates of the bounding box (x1, y1, x2, y2).
        """
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        detections.append({
                            "type": label,
                            "weight": self.weight_mapping[label],
                            "bbox": (x1, y1, x2, y2),
                            "conf": conf
                        })
        return x1,y1,x2,y2