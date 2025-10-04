import argparse
import numpy as np
import traci
import os
from realistic_detector import RealisticDetectionSimulator


class SumoController:
    def __init__(self, sumo_config_path, use_gui):
        """
        sumo_config_path: path to the .sumocfg file
        use_gui: if True, launches sumo-gui; otherwise, uses sumo (headless)
        """
        sumo_binary = "sumo-gui" if use_gui else "sumo"
        self.sumo_cmd = [
            sumo_binary,
            "-c", sumo_config_path,
            "--no-warnings",
            "--start",
            "--device.ssm.probability", "1.0",
            "--output-prefix", "TIME"
        ]
        self.started = False

    def start(self):
        """Start the SUMO simulation."""
        if not os.path.exists(self.sumo_cmd[2]):
            raise FileNotFoundError(f"SUMO config file not found: {self.sumo_cmd[2]}")
        traci.start(self.sumo_cmd)
        self.started = True

    def step(self):
        if self.started:
            traci.simulationStep()

    def close(self):
        if self.started:
            traci.close()
            self.started = False

    def set_light_state(self, tl_id, node_controlled_lanes, green_nodes, state_code=2):
        """
        Set the light state for a given traffic light.

        Args:
            tl_id: traffic light ID
            node_controlled_lanes: dict {node_id: [lanes controlled]}
            green_nodes: list of node IDs that should be green
            state_code: 0=red, 1=yellow, 2=green
        """
        if not self.started:
            return

        num_signals = len(traci.trafficlight.getControlledLinks(tl_id))
        state = ["r"] * num_signals  # default all red

        for node in green_nodes:
            for lane in node_controlled_lanes.get(node, []):
                try:
                    idx = traci.trafficlight.getControlledLanes(tl_id).index(lane)
                    if state_code == 2:
                        state[idx] = "G"
                    elif state_code == 1:
                        state[idx] = "y"
                except ValueError:
                    continue

        light_state = "".join(state)
        traci.trafficlight.setRedYellowGreenState(tl_id, light_state)
        print(f"[SUMO] {tl_id} state set to: {light_state}")


class MultiNodeMetricsSimulation:
    def __init__(self, num_nodes, scenario_name, yolo_profile, sumo_config, use_gui=True, yellow_duration=3):
        self.num_nodes = num_nodes
        self.scenario_name = scenario_name
        self.yellow_duration = yellow_duration

        # SUMO + detector
        self.sumo = SumoController(sumo_config, use_gui)
        self.detection_simulator = RealisticDetectionSimulator(yolo_profile)

        # Traffic light → controlled lanes
        self.traffic_light_lanes = {}
        self.node_controlled_lanes = {}

        # State tracking
        self.current_green_nodes = {}
        self.pending_yellow = {}

    def initialize_traffic_light_zones(self):
        if not self.sumo.started:
            return

        tl_ids = traci.trafficlight.getIDList()
        print(f"[INIT] Found traffic lights: {tl_ids}")

        for tl_id in tl_ids:
            controlled_lanes = traci.trafficlight.getControlledLanes(tl_id)
            self.traffic_light_lanes[tl_id] = controlled_lanes
            print(f"[INIT] {tl_id} controls lanes: {controlled_lanes}")
            self.assign_lanes_to_nodes(tl_id, controlled_lanes)

    def assign_lanes_to_nodes(self, tl_id, controlled_lanes):
        lanes_per_node = len(controlled_lanes) // self.num_nodes
        self.node_controlled_lanes[tl_id] = {}

        for node_id in range(self.num_nodes):
            start_idx = node_id * lanes_per_node
            end_idx = start_idx + lanes_per_node
            if node_id == self.num_nodes - 1:
                end_idx = len(controlled_lanes)

            node_lanes = controlled_lanes[start_idx:end_idx]
            self.node_controlled_lanes[tl_id][node_id] = node_lanes
            print(f"[INIT] {tl_id}: Node {node_id} assigned lanes {node_lanes}")

    def get_vehicles_for_node(self, tl_id, node_id):
        if not self.sumo.started or tl_id not in self.node_controlled_lanes:
            return []

        node_lanes = self.node_controlled_lanes[tl_id][node_id]
        vehicles_for_node = []

        for veh_id in traci.vehicle.getIDList():
            try:
                veh_lane_id = traci.vehicle.getLaneID(veh_id)
                veh_road_id = traci.vehicle.getRoadID(veh_id)
                veh_type = traci.vehicle.getTypeID(veh_id)

                if veh_lane_id in node_lanes:
                    vehicle_data = {
                        "type": veh_type,
                        "sumo_id": veh_id,
                        "lane_id": veh_lane_id,
                        "road_id": veh_road_id,
                        "detecting_node": node_id,
                        "traffic_light": tl_id
                    }
                    vehicles_for_node.append(vehicle_data)
            except traci.TraCIException:
                continue

        return vehicles_for_node

    def simulate_step(self, step):
        for tl_id in self.traffic_light_lanes:
            # If yellow is active
            if tl_id in self.pending_yellow:
                next_green, remaining = self.pending_yellow[tl_id]
                if remaining > 1:
                    self.pending_yellow[tl_id] = (next_green, remaining - 1)
                else:
                    self.sumo.set_light_state(
                        tl_id,
                        self.node_controlled_lanes[tl_id],
                        next_green,
                        state_code=2
                    )
                    self.current_green_nodes[tl_id] = next_green
                    del self.pending_yellow[tl_id]
                continue

            # Compute vehicle weights
            node_weights = []
            for node_id in range(self.num_nodes):
                vehicles_for_node = self.get_vehicles_for_node(tl_id, node_id)
                detections = self.detection_simulator.simulate_detections(vehicles_for_node)
                node_weights.append(sum(d.get("weight", 0) for d in detections))

            weights_array = np.array(node_weights)
            max_idx = np.argmax(weights_array) if np.any(weights_array > 0) else 0

            # Compute new green group
            if self.num_nodes == 2:
                new_green = [max_idx]
            else:  # 4 nodes
                new_green = [max_idx, (max_idx + 2) % self.num_nodes]

            # Apply logic
            if tl_id not in self.current_green_nodes:
                self.sumo.set_light_state(tl_id, self.node_controlled_lanes[tl_id], new_green, state_code=2)
                self.current_green_nodes[tl_id] = new_green

            elif set(new_green) != set(self.current_green_nodes[tl_id]):
                if not set(new_green).intersection(self.current_green_nodes[tl_id]):
                    prev_green = self.current_green_nodes[tl_id]
                    self.sumo.set_light_state(tl_id, self.node_controlled_lanes[tl_id], prev_green, state_code=1)
                    self.pending_yellow[tl_id] = (new_green, self.yellow_duration)
                else:
                    self.sumo.set_light_state(tl_id, self.node_controlled_lanes[tl_id], self.current_green_nodes[tl_id], state_code=2)

        print(f"[SIM] Step {step} complete.")

    def run_simulation(self, max_steps=1000):
        self.sumo.start()
        self.initialize_traffic_light_zones()

        print(f"[SIM] Starting {self.num_nodes}-node decentralized simulation: {self.scenario_name}")

        for step in range(max_steps):
            self.simulate_step(step)
            if len(traci.vehicle.getIDList()) == 0:
                print(f"[SIM] No vehicles remaining at step {step}")
                break
            self.sumo.step()

        self.sumo.close()


def main():
    parser = argparse.ArgumentParser(description="Multi-Node Traffic Simulation (Decentralized)")
    parser.add_argument("-n", "--nodes", type=int, required=True, help="Number of nodes (2 or 4)")
    parser.add_argument("-s", "--scenario", required=True, help="Scenario name")
    parser.add_argument("--sumo-config", required=True, help="Path to SUMO .sumocfg file")
    parser.add_argument("--max-steps", type=int, default=1000, help="Maximum simulation steps")
    parser.add_argument("--yolo-profile", default="yolo_performance_profile.json",
                        help="YOLOv8 performance profile")
    parser.add_argument("-g", "--gui", action="store_true", help="Use SUMO GUI")
    args = vars(parser.parse_args())

    simulation = MultiNodeMetricsSimulation(
        num_nodes=args["nodes"],
        scenario_name=args["scenario"],
        yolo_profile=args["yolo_profile"],
        sumo_config=args["sumo_config"],
        use_gui=args["gui"]
    )
    simulation.run_simulation(max_steps=args["max_steps"])


if __name__ == "__main__":
    main()
