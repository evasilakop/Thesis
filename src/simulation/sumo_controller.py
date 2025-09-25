import traci
import os

class SumoController:
    def __init__(self, sumo_config_path, use_gui):
        """
        sumo_config_path: path to the .sumocfg file
        use_gui: if True, launches sumo-gui; otherwise, uses sumo (headless)
        """
        sumo_binary = "sumo-gui" if use_gui else "sumo"
        self.sumo_cmd = [sumo_binary, "-c", sumo_config_path, "--log", "logs/sumo_log.log", "--log.timestamps", "--no-warnings", "--start"]
        self.started = False

    def start(self):
        """Start the SUMO simulation."""
        if not os.path.exists(self.sumo_cmd[2]):
            raise FileNotFoundError(f"SUMO config file not found: {self.sumo_cmd[2]}")
        traci.start(self.sumo_cmd)
        self.tl_id = traci.trafficlight.getIDList()[0]
        self.edge_list = traci.edge.getIDList()
        self.started = True

    def step(self):
        if self.started:
            traci.simulationStep()

    def close(self):
        if self.started:
            traci.close()
            self.started = False


    def set_light_state_from_lists(self, green_nodes, red_nodes, lanes_per_direction=1):
        """
        Convert green/red node indices to a light state string and set it in SUMO.
        lanes_per_direction: number of lanes per direction (1 or 2)
        For 4 directions, total lights = 4 * lanes_per_direction
        """
        if not self.started:
            return

        num_directions = 4
        total_lights = num_directions * lanes_per_direction
        light_bits = ['r'] * total_lights

        for i in green_nodes:
            for lane in range(lanes_per_direction):
                idx = i * lanes_per_direction + lane
                if 0 <= idx < total_lights:
                    light_bits[idx] = 'G'
        for i in red_nodes:
            for lane in range(lanes_per_direction):
                idx = i * lanes_per_direction + lane
                if 0 <= idx < total_lights:
                    light_bits[idx] = 'r'

        light_state = ''.join(light_bits)
        traci.trafficlight.setRedYellowGreenState(self.tl_id, light_state)
        print(f"[SUMO] Traffic light state set to: {light_state}")


    def add_vehicle(self, veh_id, route_id, edge_from, edge_to, depart_time=0, vtype="car"):
        """
        Dynamically adds a vehicle to the simulation.
        """
        if self.started:
            if edge_from not in self.edge_list or edge_to not in self.edge_list:
                raise ValueError(f"[SUMO ERROR] Invalid edge(s): {edge_from} > {edge_to}")
            try:
                traci.route.add(route_id, [edge_from, edge_to])
                traci.vehicle.add(veh_id, 
                                  route_id, 
                                  typeID=vtype, 
                                  depart=str(depart_time), 
                                  departLane="best",
                                  departSpeed="max")
            except traci.TraCIException as e:
                raise ValueError(f"[SUMO ERROR] Could not add vehicle {veh_id}: {e}")
        else:
            print(f"[SUMO WARNING] Cannot add vehicle {veh_id}, SUMO not started.")
    
    def get_realistic_detections(self, node_index: int, detection_simulator, detection_radius=50):
        """
        Get vehicles from SUMO and apply realistic YOLOv8 detection simulation
        """
        # Get all vehicles in detection zone (ground truth)
        ground_truth_vehicles = self.get_vehicles_in_detection_zone(node_index, detection_radius)
        
        # Apply realistic detection simulation
        realistic_detections = detection_simulator.simulate_detections(ground_truth_vehicles)
        
        return realistic_detections, ground_truth_vehicles
