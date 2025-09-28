import os
import random
import json
import numpy as np
import traci

class RealisticDetectionSimulator:
    def __init__(self, profile_file=None):
        """Initialize with research-based detection rates"""
        if profile_file and os.path.exists(profile_file):
            with open(profile_file, 'r') as f:
                self.profile = json.load(f)
            self.detection_rates = self.profile.get("detection_rates", {})
            self.confidence = self.profile.get("avg_confidences", {})
        else:
            # Default research-based rates
            self.detection_rates = {
                "car": 0.84,
                "truck": 0.88,
                "bus": 0.90,
                "motorcycle": 0.67
            }
            self.confidence = {}

        self.confidence_threshold = 0.5

    def simulate_detections(self, sumo_vehicles):
        """Apply realistic detection rates to SUMO vehicles"""
        realistic_detections = []
        for vehicle in sumo_vehicles:
            vehicle_type = vehicle["type"]
            detection_rate = self.detection_rates.get(vehicle_type, 0.5)

            if random.random() < detection_rate:
                if not self.confidence:
                    confidence = self._generate_confidence(vehicle_type)
                else:
                    confidence = self.confidence.get(vehicle_type, 0.7)

                if confidence >= self.confidence_threshold:
                    detected_vehicle = dict(vehicle)  # copy
                    detected_vehicle["conf"] = confidence
                    detected_vehicle["detection_source"] = "realistic_simulation"
                    realistic_detections.append(detected_vehicle)

        return realistic_detections

    def _generate_confidence(self, vehicle_type):
        """Generate realistic confidence scores"""
        base_confidence = {
            "car": 0.78,
            "truck": 0.82,
            "bus": 0.84,
            "motorcycle": 0.69
        }
        base = base_confidence.get(vehicle_type, 0.7)
        confidence = np.random.normal(base, 0.12)
        return max(0.1, min(0.99, confidence))

class ActuatedTLSController:
    def __init__(self, tl_id, num_nodes, opposite_map, node_controlled_lanes,
                 min_green=15, max_green=3000):
        self.tl_id = tl_id
        self.num_nodes = num_nodes
        self.opposite_map = opposite_map          # dictionary that points to the opposite node
        self.node_controlled_lanes = node_controlled_lanes
        self.min_green = min_green
        self.max_green = max_green
        self.current_node = 0                     # start with node 0
        self.steps_in_phase = 0

    def step(self, weights):
        """Decide which node should be green based on weights."""
        self.steps_in_phase += 1

        # Stay green if not past the minimum green time
        if self.steps_in_phase < self.min_green:
            return self.current_node

        # Find the "heaviest" node
        best_node = max(weights, key=weights.get)

        # Switch if different node OR forced by max green
        if (best_node != self.current_node and
            self.steps_in_phase >= self.min_green) or self.steps_in_phase >= self.max_green:
            self.current_node = best_node
            self.steps_in_phase = 0

        return self.current_node

    def apply_to_tls(self):
        """Apply the chosen node (and opposite if applicable) to SUMO."""
        try:
            current_state = traci.trafficlight.getRedYellowGreenState(self.tl_id)
            state = list(current_state)
        except traci.TraCIException:
            return

        # reset all to red
        for i in range(len(state)):
            state[i] = "r"

        # active = winner + opposite
        active_nodes = [self.current_node]
        if self.current_node in self.opposite_map:
            active_nodes.append(self.opposite_map[self.current_node])

        # set their controlled links to green
        links = traci.trafficlight.getControlledLinks(self.tl_id)
        for node_id in active_nodes:
            for lane_id in self.node_controlled_lanes[self.tl_id].get(node_id, []):
                for link_idx, link in enumerate(links):
                    if link and link[0][0] == lane_id:
                        state[link_idx] = "G"

        traci.trafficlight.setRedYellowGreenState(self.tl_id, "".join(state))

class SumoController:
    def __init__(self, sumo_config_path, use_gui=True):
        sumo_binary = "sumo-gui" if use_gui else "sumo"
        self.sumo_cmd = [
            sumo_binary,
            "-c", os.path.abspath(sumo_config_path),
            "--no-warnings",
            "--start",
            "--output-prefix", "TIME",
            "--scale", "5.0"
        ]
        print("Launching SUMO with:", self.sumo_cmd)
        self.started = False
        self.node_controlled_lanes = {}
        self.tls_controllers = {}

        self.start()
        self.initialize_traffic_light_zones()

    def start(self):
        if not self.started:
            traci.start(self.sumo_cmd)
            self.started = True
            traci.simulationStep()  # step once so TLS are initialized

    def initialize_traffic_light_zones(self):
        """Map which lanes belong to which 'nodes' for each TLS."""
        for tl_id in traci.trafficlight.getIDList():
            self.node_controlled_lanes[tl_id] = {}

            links = traci.trafficlight.getControlledLinks(tl_id)
            for idx, link in enumerate(links):
                if not link:
                    continue
                lane_id = link[0][0]
                node_id = idx % 4  # simplistic: assign every 4th index to same node
                self.node_controlled_lanes[tl_id].setdefault(node_id, []).append(lane_id)

            # define opposite directions (for 4-node junctions)
            opposite_map = {0: 2, 1: 3, 2: 0, 3: 1}

            # create controller
            self.tls_controllers[tl_id] = ActuatedTLSController(
                tl_id,
                num_nodes=len(self.node_controlled_lanes[tl_id]),
                opposite_map=opposite_map,
                node_controlled_lanes=self.node_controlled_lanes
            )

    def step(self, detector):
        """Run one simulation step with detection + TLS update."""
        traci.simulationStep()

        for tl_id, controller in self.tls_controllers.items():
            weights = {}
            for node_id in self.node_controlled_lanes[tl_id]:
                vehicles = self.get_vehicles_for_node(self.node_controlled_lanes[tl_id][node_id])
                detections = detector.simulate_detections(vehicles)
                weights[node_id] = sum(v.get("weight", 1) for v in detections)

            controller.step(weights)
            controller.apply_to_tls()

    def get_vehicles_for_node(self, lane_list):
        """Get vehicles on the given set of lanes."""
        vehicles = []
        for lane_id in lane_list:
            for veh_id in traci.lane.getLastStepVehicleIDs(lane_id):
                vehicles.append({"id": veh_id, "type": traci.vehicle.getTypeID(veh_id)})
        return vehicles


if __name__ == "__main__":
    sumo_config = "C:\\Users\\User\\Documents\\GitHub\\Thesis\\src\\evaluation\\2025-09-25-13-02-54\\osm.sumocfg"
    controller = SumoController(sumo_config, use_gui=True)
    detector = RealisticDetectionSimulator()

    for step in range(3974):
        controller.step(detector)

    traci.close()