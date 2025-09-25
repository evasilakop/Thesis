# multi_node_metrics.py - Using SUMO's built-in position data
import argparse
import time
from venv import logger
import numpy as np
import json
import traci
from collections import defaultdict
from simulation.sumo_controller import SumoController
from realistic_detector import RealisticDetectionSimulator

class MultiNodeMetricsSimulation:
    def __init__(self, num_nodes, scenario_name, yolo_profile):
        self.num_nodes = num_nodes
        self.scenario_name = scenario_name
        
        # Single SUMO instance
        self.sumo = SumoController("simulation/config.sumocfg", use_gui=False)
        
        # Single detection simulator
        self.detection_simulator = RealisticDetectionSimulator(yolo_profile)
        
        # Will be populated dynamically from SUMO
        self.traffic_light_lanes = {}
        self.node_controlled_lanes = {}
        
        # Metrics collection
        self.metrics = {
            "scenario": scenario_name,
            "num_nodes": num_nodes,
            "simulation_steps": []
        }
    
    def initialize_traffic_light_zones(self):
        """Dynamically determine which lanes each node controls using SUMO data"""
        if not self.sumo.started:
            return
        
        # Get all traffic lights in the simulation
        tl_ids = traci.trafficlight.getIDList()
        logger.info(f"Found traffic lights: {tl_ids}")
        
        if not tl_ids:
            logger.error("No traffic lights found in simulation!")
            return
        
        # For each traffic light, get the lanes it controls
        for tl_id in tl_ids:
            controlled_lanes = traci.trafficlight.getControlledLanes(tl_id)
            self.traffic_light_lanes[tl_id] = controlled_lanes
            logger.info(f"Traffic light {tl_id} controls lanes: {controlled_lanes}")
        
        # Assign lanes to nodes based on your network structure
        # This distributes controlled lanes among nodes
        self._assign_lanes_to_nodes()
    
    def _assign_lanes_to_nodes(self):
        """Assign controlled lanes to nodes based on direction/position"""
        if not self.traffic_light_lanes:
            return
        
        # Get the main traffic light (assuming single intersection)
        main_tl = list(self.traffic_light_lanes.keys())[0]
        all_controlled_lanes = self.traffic_light_lanes[main_tl]
        
        # Divide lanes among nodes
        lanes_per_node = len(all_controlled_lanes) // self.num_nodes
        
        for node_id in range(self.num_nodes):
            start_idx = node_id * lanes_per_node
            end_idx = start_idx + lanes_per_node
            
            # Handle remainder lanes for last node
            if node_id == self.num_nodes - 1:
                end_idx = len(all_controlled_lanes)
            
            node_lanes = all_controlled_lanes[start_idx:end_idx]
            self.node_controlled_lanes[node_id] = node_lanes
            
            logger.info(f"Node {node_id} assigned lanes: {node_lanes}")
    
    def get_vehicles_for_node(self, node_id):
        """Get vehicles that node can detect using SUMO's lane/road metadata"""
        if not self.sumo.started or node_id not in self.node_controlled_lanes:
            return []
        
        node_lanes = self.node_controlled_lanes[node_id]
        vehicles_for_node = []
        
        # Check all vehicles in simulation
        for veh_id in traci.vehicle.getIDList():
            try:
                # Get vehicle's current lane and road
                veh_lane_id = traci.vehicle.getLaneID(veh_id)
                veh_road_id = traci.vehicle.getRoadID(veh_id)
                veh_type = traci.vehicle.getTypeID(veh_id)
                
                # Check if vehicle is on a lane this node monitors
                # Look for vehicles approaching the controlled lanes
                if self._is_vehicle_in_node_detection_zone(veh_lane_id, veh_road_id, node_lanes):
                    vehicle_data = {
                        "type": veh_type,
                        "weight": self.sumo._get_weight_for_vehicle_type(veh_type),
                        "sumo_id": veh_id,
                        "lane_id": veh_lane_id,
                        "road_id": veh_road_id,
                        "detecting_node": node_id
                    }
                    vehicles_for_node.append(vehicle_data)
                    
            except traci.TraCIException:
                # Vehicle might be in junction or transitioning
                continue
        
        return vehicles_for_node
    
    def _is_vehicle_in_node_detection_zone(self, veh_lane_id, veh_road_id, node_controlled_lanes):
        """
        Determine if a vehicle is in the detection zone for a node
        Using SUMO's lane/road metadata
        """
        # Method 1: Direct lane match (vehicle is on a controlled lane)
        if veh_lane_id in node_controlled_lanes:
            return True
        
        # Method 2: Check if vehicle is on incoming edge to controlled lanes
        for controlled_lane in node_controlled_lanes:
            try:
                # Get the edge of the controlled lane
                controlled_edge = traci.lane.getEdgeID(controlled_lane)
                
                # Check if vehicle's road connects to this edge
                # This catches vehicles approaching the intersection
                if self._roads_are_connected(veh_road_id, controlled_edge):
                    return True
                    
            except traci.TraCIException:
                continue
        
        return False
    
    def _roads_are_connected(self, road1, road2):
        """
        Check if two roads/edges are connected (simple heuristic)
        You can make this more sophisticated based on your network
        """
        try:
            # Simple check: if road names suggest they're connected
            # e.g., "edge_nc" connects to "edge_cs" through center
            
            # Get outgoing edges from road1
            outgoing = traci.edge.getOutgoing(road1)
            if road2 in outgoing:
                return True
            
            # Alternative: check if they share a junction
            # This is a simplified approach - you might need to adjust
            return False
            
        except traci.TraCIException:
            return False
    
    def simulate_step(self, step):
        """Simulate one step - each node sees vehicles in its zone"""
        node_detections = {}
        node_weights = []
        node_vehicle_counts = {}
        
        for node_id in range(self.num_nodes):
            # Get vehicles this node can detect using SUMO metadata
            vehicles_for_node = self.get_vehicles_for_node(node_id)
            
            # Apply realistic detection simulation
            detections = self.detection_simulator.simulate_detections(vehicles_for_node)
            weight = sum(d["weight"] for d in detections)
            
            node_detections[node_id] = detections
            node_weights.append(weight)
            node_vehicle_counts[node_id] = {
                "ground_truth": len(vehicles_for_node),
                "detected": len(detections),
                "lanes": self.node_controlled_lanes.get(node_id, [])
            }
        
        # Traffic light decision
        weights_array = np.array(node_weights)
        max_idx = np.argmax(weights_array) if np.any(weights_array > 0) else 0
        
        # Apply traffic control
        self.apply_traffic_control(max_idx)
        
        # Record metrics
        step_data = {
            "step": step,
            "node_weights": node_weights,
            "winning_node": int(max_idx),
            "winning_weight": float(weights_array[max_idx]),
            "node_vehicle_counts": node_vehicle_counts,
            "total_vehicles_in_sim": len(traci.vehicle.getIDList())
        }
        
        # Detailed logging
        zone_details = []
        for node_id in range(self.num_nodes):
            counts = node_vehicle_counts[node_id]
            zone_details.append(f"Node{node_id}:GT={counts['ground_truth']},Det={counts['detected']}")
        
        logger.info(f"Step {step}: {' | '.join(zone_details)} | Winner=Node{max_idx}")
        
        return step_data
    
    def run_simulation(self, max_steps=1000):
        """Run the complete simulation"""
        self.sumo.start()
        
        # Initialize zones using SUMO data
        self.initialize_traffic_light_zones()
        
        logger.info(f"Starting {self.num_nodes}-node simulation: {self.scenario_name}")
        logger.info(f"Node lane assignments: {self.node_controlled_lanes}")
        
        for step in range(max_steps):
            step_data = self.simulate_step(step)
            self.metrics["simulation_steps"].append(step_data)
            
            if step_data["total_vehicles_in_sim"] == 0:
                logger.info(f"No vehicles remaining at step {step}")
                break
            
            self.sumo.step()
        
        self.sumo.close()
        self.save_results()
    
    def apply_traffic_control(self, winning_node):
        """Apply traffic light control based on winning node"""
        if self.num_nodes == 2:
            green_nodes = [winning_node]
            red_nodes = [i for i in range(self.num_nodes) if i != winning_node]
        else:  # 4 nodes
            green_nodes = [winning_node, (winning_node + 2) % self.num_nodes]
            red_nodes = [i for i in range(self.num_nodes) if i not in green_nodes]
        
        self.sumo.set_light_state_from_lists(green_nodes, red_nodes, 2)
    
    def save_results(self):
        """Save simulation results"""
        filename = f"logs/multi_node_metrics_{self.scenario_name}_{int(time.time())}.json"
        
        # Calculate summary statistics
        if self.metrics["simulation_steps"]:
            total_vehicles = [s["total_vehicles"] for s in self.metrics["simulation_steps"]]
            node_wins = defaultdict(int)
            for step in self.metrics["simulation_steps"]:
                node_wins[step["winning_node"]] += 1
            
            self.metrics["summary"] = {
                "total_steps": len(self.metrics["simulation_steps"]),
                "avg_vehicles_per_step": np.mean(total_vehicles),
                "node_win_counts": dict(node_wins),
                "node_win_percentages": {
                    node: (wins / len(self.metrics["simulation_steps"])) * 100
                    for node, wins in node_wins.items()
                }
            }
        
        with open(filename, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        print(f"Multi-node simulation results saved to {filename}")
        return filename

def main():
    parser = argparse.ArgumentParser(description="Multi-Node Traffic Metrics Simulation")
    parser.add_argument("-n", "--nodes", type=int, required=True, help="Number of nodes (2 or 4)")
    parser.add_argument("-s", "--scenario", required=True, help="Scenario name")
    parser.add_argument("--max-steps", type=int, default=1000, help="Maximum simulation steps")
    parser.add_argument("--yolo-profile", default="yolo_performance_profile.json", 
                       help="YOLOv8 performance profile")
    parser.add_argument("-g", "--gui", action="store_true", help="Use SUMO GUI")
    
    args = vars(parser.parse_args())
    
    # Run single simulation with all nodes
    simulation = MultiNodeMetricsSimulation(
        num_nodes=args["nodes"],
        scenario_name=args["scenario"],
        yolo_profile=args["yolo_profile"]
    )
    
    simulation.run_simulation(max_steps=args["max_steps"])

if __name__ == "__main__":
    main()
