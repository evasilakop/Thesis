import argparse
import time
from detector import WeightDetector
from networking import MeshNode

nodes = [
    ("127.0.0.1", 5001),
    ("127.0.0.1", 5002),
    ("127.0.0.1", 5003),
    ("127.0.0.1", 5004)
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--index", type=int, 
                        required=True, help="Node index (0-3)")
    parser.add_argument("-v", "--video", required=True, 
                        help="Path to input video")
    parser.add_argument("-c", "--confidence", type=float, default=0.5)
    parser.add_argument("-f", "--frequency", type=float, default=3)
    args = vars(parser.parse_args())

    detector = WeightDetector(args["video"],
                              args["confidence"],
                              args["frequency"])
    node = MeshNode(args["index"], nodes)

    while True:
        weight = detector.detect_weight()
        if weight is None:
            print("Video processing complete. Exiting.")
            break
        else:
            print(
                f"[DETECTOR] Node {args['index']} detected weight:"
                f" {weight}"
            )
            node.broadcast_weight(weight)
        time.sleep(3)