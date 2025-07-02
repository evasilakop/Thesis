import argparse
import time
import numpy as np
import cv2
from sumo_controller import SumoController
from detector import WeightDetector
from networking import MeshNode

nodes = [
    ("127.0.0.1", 5001),
    ("127.0.0.1", 5002),
    ("127.0.0.1", 5003),
    ("127.0.0.1", 5004),
]

# Define the routes for each node based on their index so that they show up correctly
# in the simulation.
direction_routes = [
    ("N2S", "S2N"),
    ("E2W", "W2E"),
    ("S2N", "N2S"),
    ("W2E", "E2W"),
]

# Mapping from detected label to SUMO vType id
label_to_sumo_type = {
    "car": "car",
    "bus": "bus",
    "truck": "truck",
    "motorcycle": "motorcycle"
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--index", type=int, required=True, help="Node index (0-3)")
    parser.add_argument("-v", "--video", required=True, help="Path to input video")
    parser.add_argument("-c", "--confidence", type=float, default=0.5, help="Detection confidence")
    parser.add_argument("-f", "--frequency", type=float, default=4, help="Detection frequency in seconds")
    parser.add_argument("-n", "--nodes", type=int, required=True, help="Amount of nodes in group")
    args = vars(parser.parse_args())

    detector = WeightDetector(args["video"], args["confidence"], args["frequency"])
    node = MeshNode(args["index"], nodes)
    sumo = SumoController("intersection.sumocfg", use_gui=True)
    sumo.start()

    # For generating unique vehicle IDs and depart times, so that the vehicles don't
    # spawn on top of one another.
    depart_counter = 0

    while True:
        detections, frame = detector.detect_vehicles()
        if detections is None:
            print("Video processing complete. Exiting.")
            break

        # Show video with bounding boxes
        if frame is not None:
            # cv2.imshow(f"Node {args['index']} Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        for vehicle in detections:
            vehicle_type = label_to_sumo_type.get(vehicle["type"], "car")
            vehicle_id = f"veh_{args['index']}_{depart_counter}"
            route_id = f"r_{vehicle_id}"
            # Get the direction route for this node
            edge_from, edge_to = direction_routes[args["index"]]
            sumo.add_vehicle(vehicle_id, route_id, edge_from, edge_to, depart_time=depart_counter, vtype=vehicle_type)
            depart_counter += 1

        # Weight aggregation and networking
        weight = sum(d["weight"] for d in detections)
        print(f"[DETECTOR] Node {args['index']} detected weight: {weight}")
        node.received_weights[args["index"]] = weight
        node.broadcast_weight(weight)

        time.sleep(args["frequency"])

        total_nodes = args["nodes"]
        weights_array = np.array([
            node.received_weights[i] if node.received_weights[i] is not None else -float("inf")
            for i in range(total_nodes)
        ])
        if np.all(weights_array == -float("inf")):
            print("No valid weights received from any node. Skipping control message.")
            #continue

        max_idx = np.argmax(weights_array)
        print("Weights from all nodes:", weights_array)
        print(f"Node with maximum weight:", max_idx, f"with weight:", weights_array[max_idx])

        control_message_green = "TURN GREEN"
        control_message_red = "TURN RED"

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

        sumo.set_light_state_from_lists(green_nodes, red_nodes)
        sumo.step()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Exception occurred:", e)