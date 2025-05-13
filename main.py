import argparse
import time
import numpy as np
from detector import WeightDetector
from networking import MeshNode

nodes = [
    ("127.0.0.1", 5001),
    ("127.0.0.1", 5002),
    ("127.0.0.1", 5003),
    ("127.0.0.1", 5004),
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--index", 
                        type=int, required=True, 
                        help="Node index (0-3)"
    )
    parser.add_argument("-v", "--video", 
                        required=True, 
                        help="Path to input video"
    )
    parser.add_argument("-c", "--confidence",
                        type=float, default=0.5,
                        help="Detection confidence",
    )
    parser.add_argument("-f", "--frequency",
                        type=float, default=4,
                        help="Detection frequency in seconds",
    )
    parser.add_argument("-n", "--nodes",
                        type=int, required=True,
                        help="Amount of nodes in group")
    args = vars(parser.parse_args())

    detector = WeightDetector(args["video"], 
                              args["confidence"], 
                              args["frequency"]
                              )
    node = MeshNode(args["index"], nodes)

    while True:
        weight = detector.detect_weight()
        if weight is None:
            print("Video processing complete. Exiting.")
            break
        else:
            print(f"[DETECTOR] Node {args['index']} "
                  f"detected weight: {weight}")
            node.received_weights[args["index"]] = weight
            node.broadcast_weight(weight)
        time.sleep(4)

        total_nodes = len(nodes)
        # For nodes with no update ever, use -infinity so they 
        # won't win the max.
        weights_list = []

        for i in range(total_nodes):
            current_weight = node.received_weights[i]
    
            if current_weight is None:
                weights_list.append(-float("inf"))
            else:
                weights_list.append(current_weight)

        weights_array = np.array(weights_list)
        max_idx = np.argmax(weights_array)

        print("Weights from all nodes:", weights_array)
        print(f"Node with maximum weight:", max_idx, 
              f"with weight:", weights_array[max_idx]
              )
        
        control_message_green = "TURN GREEN"
        control_message_red = "TURN RED"

        # TO DO: dynamic discovery of nodes
        total_nodes = args["nodes"]
        if total_nodes == 2:
            green_nodes = [max_idx]
            red_nodes = [i for i in range(total_nodes) if i not in green_nodes]
        else:
            green_nodes = [max_idx, (max_idx + 2) % total_nodes]
            red_nodes = [i for i in range(total_nodes) if i not in green_nodes]
            
        for i in range(total_nodes):
            if i in green_nodes:
                node.send_control_message(i, control_message_green)
            else:
                node.send_control_message(i, control_message_red)