# realistic_detector.py (no typing imports)
import random
import json
import numpy as np
import os
from collections import defaultdict

class RealisticDetectionSimulator:
    def __init__(self, profile_file=None):
        """Initialize with research-based detection rates"""
        if profile_file and os.path.exists(profile_file):
            with open(profile_file, 'r') as f:
                self.profile = json.load(f)
            self.detection_rates = self.profile.get("detection_rates", {})
        else:
            # Use research-based default rates
            self.detection_rates = {
                "car": 0.84,        # 84% detection rate for cars
                "truck": 0.88,      # 88% for trucks  
                "bus": 0.90,        # 90% for buses
                "motorcycle": 0.67  # 67% for motorcycles
            }
        
        self.confidence_threshold = 0.5
        print(f"Initialized realistic detector with rates: {self.detection_rates}")
    
    def simulate_detections(self, sumo_vehicles):
        """
        Apply realistic detection rates to SUMO vehicles
        No typing - just regular Python
        """
        realistic_detections = []
        
        for vehicle in sumo_vehicles:
            vehicle_type = vehicle["type"]
            
            # Get detection rate for this vehicle type
            detection_rate = self.detection_rates.get(vehicle_type, 0.5)
            
            # Simulate detection decision
            if random.random() < detection_rate:
                # Generate realistic confidence score
                confidence = self._generate_confidence(vehicle_type)
                
                if confidence >= self.confidence_threshold:
                    # Create a new defaultdict for the detected vehicle
                    detected_vehicle = defaultdict(lambda: None)
                    detected_vehicle.update(vehicle)  # Copy all existing data
                    detected_vehicle["conf"] = confidence
                    detected_vehicle["detection_source"] = "realistic_simulation"
                    realistic_detections.append(detected_vehicle)
        
        return realistic_detections
    
    def _generate_confidence(self, vehicle_type):
        """Generate realistic confidence scores"""
        # Base confidence levels by vehicle type
        base_confidence = {
            "car": 0.78,
            "truck": 0.82, 
            "bus": 0.84,
            "motorcycle": 0.69
        }
        
        base = base_confidence.get(vehicle_type, 0.7)
        # Add some realistic variance
        confidence = np.random.normal(base, 0.12)
        
        # Keep in realistic range
        return max(0.1, min(0.99, confidence))