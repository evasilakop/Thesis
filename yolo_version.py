import cv2 
import argparse
import time
import os
from ultralytics import YOLO

def detection(frame_interval, confidence, model):
    frame_count = 0
    frame_number = 0
    
    # Mapping for object labels to their weight values
    weight_mapping = {
        "car": 2,
        "bus": 10,
        "motorcycle": 1,
        "truck": 10
    }

    # Ensure the output directory exists
    output_dir = "images"
    os.makedirs(output_dir, exist_ok=True)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Video ended or error reading frame")
            break

        frame_count += 1

        # Only process at specified interval
        if frame_count % frame_interval == 0:
            total_weight = 0
            results = model(frame)
            for result in results:
                for box in result.boxes:
                    conf = box.conf[0].item()
                    cls = int(box.cls[0].item())
                    label = model.names[cls]

                    if conf > confidence and label in weight_mapping:
                        total_weight += weight_mapping[label]
                        # Draw bounding box and label
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cv2.rectangle(frame, (x1, y1), (x2, y2), 
                                     (0, 255, 0), 2)
                        cv2.putText(frame, f"{label}: {conf:.2f}",
                                    (x1, y1-10), 
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, (0, 255, 0), 2)

            frame_number += 1
            print(f"Processed Frame {frame_number}")
            print(f"Weight: {total_weight}")

            output_path = os.path.join(output_dir, 
                                       f"Frame{frame_number}.jpg")
            cv2.imwrite(output_path, frame)

            yield total_weight

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--video", required=True, 
                        help="Path to input video")
    parser.add_argument("-c", "--confidence", type=float, default=0.5,
                        help="Minimum probability to filter weak " \
                        "detections, format: 0.X")
    parser.add_argument("-f", "--frequency", type=float, default=3,
                        help="Time in seconds between each frame capture")
    args = vars(parser.parse_args())

    model = YOLO("yolov8n.pt")

    cap = cv2.VideoCapture(args["video"])
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_interval = int(fps * args["frequency"])
    # Allow time for video or camera to initialize
    time.sleep(1)

    # Process the video and dynamically yield frame weights
    for weight in detection(frame_interval, 
                            args["confidence"], 
                            model):
        print(f"Detected weight from generator: {weight}")

    cap.release()
    cv2.destroyAllWindows()