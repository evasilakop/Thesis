import cv2 # type: ignore
import argparse
import time
import numpy as np # type: ignore

from ultralytics import YOLO # type: ignore
from scipy.sparse import csr_array # type: ignore
from scipy.sparse.csgraph import floyd_warshall # type: ignore


def detection(fps, cap_frequency, confidence, model):


    frame_count = 0
    frame_number = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Video ended or error reading frame")
            break
        if ret:
            frame_count += 1
            total_weight = 0
            if frame_count % (fps*cap_frequency) == 0:
                results = model(frame)
                for result in results:
                    for box in result.boxes:
                        conf = box.conf[0].item()
                        cls = int(box.cls[0].item())
                        label = model.names[cls]
                        if label == "car":
                            if conf > confidence:
                                total_weight += 2
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                cv2.rectangle(frame, (x1, y1), (x2, y2),
                                            (0, 255, 0), 2)
                                cv2.putText(frame, f"{label}: {conf:.2f}",
                                            (x1, y1-10),
                                            cv2.FONT_HERSHEY_SIMPLEX,
                                            0.5, (0, 255, 0), 2)
                        if label == "bus":
                            if conf > confidence:
                                total_weight += 10
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                cv2.rectangle(frame, (x1, y1), (x2, y2),
                                            (0, 255, 0), 2)
                                cv2.putText(frame, f"{label}: {conf:.2f}",
                                            (x1, y1-10),
                                            cv2.FONT_HERSHEY_SIMPLEX,
                                            0.5, (0, 255, 0), 2)
                        if label == "motorcycle":
                            if conf > confidence:
                                total_weight += 1
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                cv2.rectangle(frame, (x1, y1), (x2, y2),
                                            (0, 255, 0), 2)
                                cv2.putText(frame, f"{label}: {conf:.2f}",
                                            (x1, y1-10),
                                            cv2.FONT_HERSHEY_SIMPLEX,
                                            0.5, (0, 255, 0), 2)
                        if label == "truck":
                            if conf > confidence:
                                total_weight += 10
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                cv2.rectangle(frame, (x1, y1), (x2, y2),
                                            (0, 255, 0), 2)
                                cv2.putText(frame, f"{label}: {conf:.2f}",
                                            (x1, y1-10),
                                            cv2.FONT_HERSHEY_SIMPLEX,
                                            0.5, (0, 255, 0), 2)
                frame_number += 1
                print(f"Processed Frame {frame_number}\n")
                print(f"Weight: {total_weight}")
                cv2.imwrite("images/Frame%1d.jpg" % (frame_number), frame)
    return total_weight


if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--video", required=True,
                    help="Path to input video")
    ap.add_argument("-c", "--confidence", type=float, default=0.5,
                    help="Minimum probability to filter weak " \
                         "detections, format: 0.X")
    ap.add_argument("-f", "--frequency", required=False, type=float,
                    default=3, help="Time in seconds between each " \
                                    "frame capture")
    args = vars(ap.parse_args())

    model = YOLO("yolov8n.pt")

    cap = cv2.VideoCapture(args["video"])
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    # Allow time for the video to load/camera to start.
    time.sleep(1)
    weight = detection(fps,
                        args["frequency"],
                        args["confidence"],
                        model)

    arr = np.array([
        [   0,       0,    "w0+w2",    0],
        [   0,       0,       0,    "w1+w3"],
        ["w0+w2",    0,       0,       0],
        [   0,    "w1+w3",    0,       0]
    ])

    graph = csr_array(arr)

    dist_matrix = floyd_warshall(csgraph=graph, directed=False)
    green_direction = dist_matrix.argmax(axis=0)
    # Returns the row where the maximum traffic is detected, odd or
    # even is what describes each direction.


    
    cap.release()
    cv2.destroyAllWindows()