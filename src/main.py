import argparse
import time
import numpy as np
import cv2
from simulation.sumo_controller import SumoController
from detector import WeightDetector
from networking import MeshNode
import traceback

nodes = [
    ("127.0.0.1", 5001),
    ("127.0.0.1", 5002),
    ("127.0.0.1", 5003),
    ("127.0.0.1", 5004),
]

# Define the routes for each node based on their index so that they show up correctly
# in the simulation.
direction_routes = [
    ("edge_nc", "edge_cs"),  # Node 0: North to Center, Center to South
    ("edge_wc", "edge_ce"),  # Node 1: West to Center, Center to East
    ("edge_sc", "edge_cn"),  # Node 2: South to Center, Center to North
    ("edge_ec", "edge_cw"),  # Node 3: East to Center, Center to West
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
    parser.add_argument("-c", "--confidence", type=float, default=0.5, help="Detection confidence, defaults to 50%")
    parser.add_argument("-f", "--frequency", type=float, default=5, help="Detection frequency in seconds, defaults to 5")
    parser.add_argument("-n", "--nodes", type=int, required=True, help="Amount of nodes in group")
    parser.add_argument("-g", "--gui", action="store_true", help="Flag to use SUMO GUI for visualization")
    args = vars(parser.parse_args())

    empty_cycles = 0
    max_empty_cycles = 3 

    sumo = SumoController("simulation/config.sumocfg", use_gui=args["gui"])
    sumo.start()
    node = MeshNode(args["index"], nodes)
    depart_counter = 0
    time.sleep(2)  # Ensure the simulation is ready before starting detection
    detector = WeightDetector(args["video"], args["confidence"], args["frequency"])

    while True:
        detections, frame = detector.detect_vehicles()
        if detections is None:
            print("Video processing complete. Exiting.")
            sumo.close()
            #cv2.destroyAllWindows()
            break

        # Show video with bounding boxes
        if frame is not None:
            #cv2.imshow(f"Node {args['index']} Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Batch add all detected vehicles with the same depart_time (current simulation step)
        current_sim_step = depart_counter  # Or use a simulation time if available
        for vehicle in detections:
            vehicle_type = label_to_sumo_type.get(vehicle["type"], "car")
            vehicle_id = f"veh_{args['index']}_{depart_counter}"
            route_id = f"r_{vehicle_id}"
            edge_from, edge_to = direction_routes[args["index"]]
            sumo.add_vehicle(
                vehicle_id, route_id, edge_from, edge_to,
                depart_time=current_sim_step, vtype=vehicle_type
                )
            depart_counter += 1

        # Weight aggregation and networking
        weight = sum(d["weight"] for d in detections)
        print(f"[DETECTOR] Node {args['index']} detected weight: {weight}")
        node.received_weights[args["index"]] = weight
        node.broadcast_weight(weight)

        # Step the simulation after all vehicles are added
        for _ in range(int(args["frequency"])):
            time.sleep(0.2)
            sumo.step()

        total_nodes = args["nodes"]
        # Defensive check: received_weights access
        try:
            weights_array = np.array([
                node.received_weights[i] if node.received_weights[i] is not None else -float("inf")
                for i in range(total_nodes)
            ])
        except Exception as e:
            print(f"[ERROR] Could not build weights_array: {e}")
            break
        if np.all(weights_array == -float("inf")):
            print("No valid weights received from any node. Skipping control message.")
            continue

        if np.all(weights_array == 0):
            empty_cycles += 1
            print(f"All nodes empty for {empty_cycles} consecutive cycles.")
            if empty_cycles >= max_empty_cycles:
                print("All nodes empty for too long. Exiting.")
                break
        else:
            empty_cycles = 0  # Reset if any node is not empty

        max_idx = np.argmax(weights_array)
        print("Weights from all nodes:", weights_array)
        print(f"Node with maximum weight: {max_idx} with weight: {weights_array[max_idx]}")

        control_message_green = "TURN GREEN\n"
        control_message_red = "TURN RED\n"

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
        sumo.set_light_state_from_lists(green_nodes, red_nodes, 2)
        sumo.step()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Exception occurred:", e)
        traceback.print_exc()