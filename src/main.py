import argparse
import time
import numpy as np
import cv2
import traceback
import logging
import os

from simulation.sumo_controller import SumoController
from detector import WeightDetector
from networking import MeshNode

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # console
        logging.FileHandler("logs/simulation.log")  # file
    ]
)
logger = logging.getLogger(__name__)

nodes = [
    ("127.0.0.1", 5001),
    ("127.0.0.1", 5002),
    ("127.0.0.1", 5003),
    ("127.0.0.1", 5004),
]

# Define the routes for each node based on their index and the total amount of nodes 
# so that they are shown correctly in the simulation.
direction_routes_4 = [
    ("edge_nc", "edge_cs"),  # Node 0: North to Center, Center to South
    ("edge_wc", "edge_ce"),  # Node 1: West to Center, Center to East
    ("edge_sc", "edge_cn"),  # Node 2: South to Center, Center to North
    ("edge_ec", "edge_cw"),  # Node 3: East to Center, Center to West
]

direction_routes_2 = [
    ("edge_nc", "edge_cs"),  # Node 0: North to Center, Center to South
    ("edge_wc", "edge_cs"),  # Node 1: West to Center, Center to South
]

# Mapping from detected label to SUMO vType id
label_to_sumo_type = {
    "car": "car",
    "bus": "bus",
    "truck": "truck",
    "motorcycle": "motorcycle"
}

def main():
    args = arguments_parser()
    empty_cycles = 0
    max_empty_cycles = 3 
    sumo = SumoController("simulation/config.sumocfg", use_gui=args["gui"])
    sumo.start()
    main.node = MeshNode(args["index"], nodes, sumo=sumo)
    depart_counter = 0
    time.sleep(2)  # Ensure the simulation is ready before starting detection
    detector = WeightDetector(args["video"], args["confidence"], args["frequency"])

    while True:
        detections, frame = detector.detect_vehicles()
        broadcast_sumo_vehicles(detections, args, depart_counter)
        depart_counter = send_vehicles_to_sumo(args, sumo, depart_counter, detections)

        # Weight aggregation and networking
        weight = sum(d["weight"] for d in detections)
        logger.info(f"[DETECTOR] Node {args['index']} detected weight: {weight}")
        main.node.received_weights[args["index"]] = weight
        main.node.broadcast_weight(weight)
        advance_simulation(args, sumo)

        total_nodes = args["nodes"]
        # If a light doesn't start, we assume its weight is -inf
        try:
            weights_array = np.array([
                main.node.received_weights[i] if main.node.received_weights[i] is not None else -float("inf")
                for i in range(total_nodes)
            ])
        except Exception as e:
            logger.exception(f"[ERROR] Could not build weights_array: {e}")

        max_idx = np.argmax(weights_array)
        logger.info(f"Weights from all nodes: {weights_array}")
        logger.info(f"Node with maximum weight: {max_idx} with weight: {weights_array[max_idx]}")

        send_control_messages(sumo, total_nodes, max_idx)
        sumo.step()

        #closing condition
        if np.all((weights_array == -float("inf")) | (weights_array == 0)):
            empty_cycles += 1
            logger.warning("No valid weights received from any node. Skipping control message.")
            logger.info(f"All nodes empty for {empty_cycles} consecutive cycles.")
            if empty_cycles >= max_empty_cycles:
                logger.info("All nodes empty for too long. Exiting.")
                close(sumo)
                break
        else:
            empty_cycles = 0  # Reset if any node is not empty


def close(sumo):
    """Closes all open windows and cleans up resources

    Args:
        sumo (SumoController): The SUMO controller instance
    """
    sumo.close()
    cv2.destroyAllWindows()

def arguments_parser():
    """Parses command line arguments for the simulation

    Returns:
        args: A dictionary containing the parsed arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--index", type=int, required=True, help="Node index (0-3)")
    parser.add_argument("-v", "--video", required=True, help="Path to input video")
    parser.add_argument("-c", "--confidence", type=float, default=0.5, help="Detection confidence, defaults to 50%")
    parser.add_argument("-f", "--frequency", type=float, default=15, help="Detection frequency in seconds, defaults to 15")
    parser.add_argument("-n", "--nodes", type=int, required=True, help="Amount of nodes in group")
    parser.add_argument("-g", "--gui", action="store_true", help="Flag to use SUMO GUI for visualization")
    args = vars(parser.parse_args())
    return args

def send_control_messages(sumo, total_nodes, max_idx):
    """Sends control messages to the SUMO simulation

    Args:
        sumo (SumoController): The SUMO controller instance
        node (MeshNode): The mesh node instance
        total_nodes (int): The total number of nodes
        max_idx (int): The index of the node with the maximum weight
    """
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
            main.node.send_control_message(i, control_message_green)
        else:
            main.node.send_control_message(i, control_message_red)
    sumo.set_light_state_from_lists(green_nodes, red_nodes, 2)

def send_vehicles_to_sumo(args, sumo, depart_counter, detections):
    """Sends vehicle information to the SUMO simulation that the node itself runs.

    Args:
        args (dict): The arguments passed to the simulation
        sumo (SumoController): The SUMO controller instance
        depart_counter (int): The current departure counter
        detections (list): The list of detected vehicles

    Returns:
        int: The updated departure counter
    """
    current_sim_step = depart_counter
    for vehicle in detections:
        vehicle_type = label_to_sumo_type.get(vehicle["type"], "car")
        vehicle_id = f"veh_{args['index']}_{depart_counter}"
        route_id = f"r_{vehicle_id}"
        if (args["nodes"] == 4):
            edge_from, edge_to = direction_routes_4[args["index"]]
        elif (args["nodes"] == 2):
            edge_from, edge_to = direction_routes_2[args["index"]]
        sumo.add_vehicle(
                vehicle_id, route_id, edge_from, edge_to,
                depart_time=current_sim_step, vtype=vehicle_type
                )
        depart_counter += 1
    return depart_counter

def broadcast_sumo_vehicles(detections, args, depart_counter):
    """Broadcasts vehicle information to all nodes."""
    for vehicle in detections:
        vehicle_type = label_to_sumo_type.get(vehicle["type"], "car")
        vehicle_id = f"veh_{args['index']}_{depart_counter}"
        route_id = f"r_{vehicle_id}"
        if (args["nodes"] == 4):
            edge_from, edge_to = direction_routes_4[args["index"]]
        elif (args["nodes"] == 2):
            edge_from, edge_to = direction_routes_2[args["index"]]
        main.node.broadcast_message(f"Vehicle data from node {args['index']}: "
                                    f"{vehicle_id}, {route_id}, {edge_from}, {edge_to}, "
                                    f"{depart_counter}, {vehicle_type}")
        depart_counter += 1

def advance_simulation(args, sumo):
    """Advances the SUMO simulation according to the frequency

    Args:
        args (dict): The arguments passed to the simulation
        sumo (SumoController): The SUMO controller instance
    """
    for _ in range(int(args["frequency"])*5):
        time.sleep(0.2)
        sumo.step()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Exception occurred: {e}")
        traceback.print_exc()