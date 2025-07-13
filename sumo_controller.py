import traci
import traci.constants as tc
import os

class SumoController:
    def __init__(self, sumo_config_path, use_gui):
        """
        sumo_config_path: path to the .sumocfg file
        use_gui: if True, launches sumo-gui; otherwise, uses sumo (headless)
        """
        sumo_binary = "sumo-gui" if use_gui else "sumo"
        self.sumo_cmd = [sumo_binary, "-c", sumo_config_path, "--start"]
        self.started = False

    def start(self):
        """Start the SUMO simulation."""
        if not os.path.exists(self.sumo_cmd[2]):
            raise FileNotFoundError(f"SUMO config file not found: {self.sumo_cmd[2]}")
        traci.start(self.sumo_cmd)
        self.tl_id = traci.trafficlight.getIDList()[0]
        self.edge_list = traci.edge.getIDList()
        self.started = True
        print(f"[SUMO] Simulation started with traffic light: {self.tl_id}")

    def step(self):
        if self.started:
            traci.simulationStep()

    def close(self):
        if self.started:
            traci.close()
            self.started = False
            print("[SUMO] Simulation closed.")

    def set_light_state(self, state):
        """
        Set the traffic light state manually.
        Example values: "GrGr", "rGrG", "rrrr", etc.
        """
        if self.started:
            traci.trafficlight.setRedYellowGreenState(self.tl_id, state)
            print(f"[SUMO] Set traffic light state to: {state}")

    def set_light_state_from_lists(self, green_nodes, red_nodes):
        """
        Convert green/red node indices to a light state string and set it in SUMO.
        Assumes 4 light lanes (NS, EW).
        """
        if not self.started:
            return
 
        # Mapping node index to position in light state string
        # Order: [N, E, S, W] → indices 0 to 3
        light_bits = ['r'] * 4

        for i in green_nodes:
            if 0 <= i < 4:
                light_bits[i] = 'G'
        for i in red_nodes:
            if 0 <= i < 4:
                light_bits[i] = 'r'

        light_state = ''.join(light_bits)
        traci.trafficlight.setRedYellowGreenState(self.tl_id, light_state)
        print(f"[SUMO] Traffic light state set to: {light_state}")


    def add_vehicle(self, veh_id, route_id, edge_from, edge_to, depart_time=0, vtype="car"):
        """
        Dynamically adds a vehicle to the simulation.
        veh_id: unique vehicle ID
        route_id: ID for the route
        edge_from/to: edges (as strings) where vehicle starts and exits
        depart_time: when vehicle appears in the simulation
        vtype: SUMO vehicle type id (e.g., 'car', 'bus', 'truck', 'motorcycle')
        """
        print(f"[SUMO] Adding vehicle {veh_id} on route {route_id} from {edge_from} to {edge_to} at time {depart_time} with type {vtype}")
        if self.started:
            if edge_from not in self.edge_list or edge_to not in self.edge_list:
                print(f"[SUMO WARNING] Invalid edge(s): {edge_from} → {edge_to}")
                return

            try:
                traci.route.add(route_id, [edge_from, edge_to])
                traci.vehicle.add(veh_id, route_id, typeID=vtype, depart=str(depart_time))
                print(f"[SUMO] Vehicle {veh_id} (type {vtype}) added on route {edge_from} → {edge_to}")
            except traci.TraCIException as e:
                print(f"[SUMO ERROR] Could not add vehicle {veh_id}: {e}")

    def get_vehicle_count(self):
        """Returns number of vehicles currently in simulation."""
        if self.started:
            return traci.simulation.getMinExpectedNumber()
        return 0