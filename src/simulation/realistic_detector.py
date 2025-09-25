import random
import json
import numpy as np
from typing import List, Dict

class RealisticDetectionSimulator:
    def __init__(self, yolo_profile_file: str):
        """Initialize with YOLOv8 performance profile"""
        with open(yolo_profile_file, 'r') as f:
            self.profile = json.load(f)
        
        self.detection_rates = self.profile["detection_rates"]
        self.confidence_threshold = self.profile["confidence_threshold"]
        
        # Add some randomness to make it more realistic
        self.detection_variance = 0.1  # ±10% variance in detection rates
    
    def simulate_detections(self, sumo_vehicles: List[Dict]) -> List[Dict]:
        """
        Simulate realistic YOLOv8 detections based on SUMO ground truth
        """
        realistic_detections = []
        
        for vehicle in sumo_vehicles:
            vehicle_type = vehicle["type"]
            
            # Get detection rate for this vehicle type
            base_rate = self.detection_rates.get(vehicle_type, 0.5)
            
            # Add some randomness
            actual_rate = max(0, min(1, base_rate + random.uniform(
                -self.detection_variance, self.detection_variance
            )))
            
            # Decide if this vehicle is detected
            if random.random() < actual_rate:
                # Simulate confidence score
                confidence = self._simulate_confidence(vehicle_type)
                
                if confidence >= self.confidence_threshold:
                    detected_vehicle = vehicle.copy()
                    detected_vehicle["conf"] = confidence
                    detected_vehicle["detection_source"] = "simulated_yolo"
                    realistic_detections.append(detected_vehicle)
        
        return realistic_detections
    
    def _simulate_confidence(self, vehicle_type: str) -> float:
        """Simulate realistic confidence scores"""
        # Base confidence from profile
        avg_conf = self.profile["avg_confidences"].get(vehicle_type, 0.7)
        
        # Add realistic variance (confidence scores tend to cluster around certain values)
        confidence = np.random.normal(avg_conf, 0.15)  # Standard deviation of 0.15
        
        # Clamp to realistic range
        return max(0.1, min(0.99, confidence))
    
    def get_detection_summary(self, sumo_count: int, detected_count: int) -> Dict:
        """Get summary of detection performance"""
        detection_rate = detected_count / sumo_count if sumo_count > 0 else 0
        
        return {
            "ground_truth_vehicles": sumo_count,
            "detected_vehicles": detected_count,
            "detection_rate": detection_rate,
            "missed_vehicles": sumo_count - detected_count
        }
