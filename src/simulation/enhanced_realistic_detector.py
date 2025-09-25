# Enhanced realistic_detector.py
import numpy as np
from research_based_metrics import ResearchBasedYOLOMetrics

class EnhancedRealisticDetector:
    def __init__(self, scenario="urban_intersections", weather="clear", confidence_threshold=0.5):
        self.metrics = ResearchBasedYOLOMetrics(scenario, weather, confidence_threshold)
        self.confidence_threshold = confidence_threshold
        
        # Add temporal consistency (vehicles don't just disappear/appear randomly)
        self.vehicle_tracking = {}
        self.tracking_consistency = 0.85  # 85% chance to detect same vehicle next frame
    
    def simulate_detections(self, sumo_vehicles: List[Dict], frame_id: int = None) -> List[Dict]:
        """Enhanced detection simulation with temporal consistency"""
        realistic_detections = []
        
        for vehicle in sumo_vehicles:
            vehicle_id = vehicle.get("sumo_id", f"unknown_{len(realistic_detections)}")
            vehicle_type = vehicle["type"]
            
            # Get base detection rate
            base_rate = self.metrics.get_detection_rate(vehicle_type)
            
            # Apply temporal consistency
            detection_rate = self._apply_temporal_consistency(vehicle_id, base_rate)
            
            # Simulate detection
            if np.random.random() < detection_rate:
                confidence = self._generate_realistic_confidence(vehicle_type)
                
                if confidence >= self.confidence_threshold:
                    detected_vehicle = vehicle.copy()
                    detected_vehicle["conf"] = confidence
                    detected_vehicle["detection_method"] = "research_based_simulation"
                    realistic_detections.append(detected_vehicle)
                    
                    # Update tracking
                    self.vehicle_tracking[vehicle_id] = {
                        "last_detected": frame_id,
                        "detection_history": self.vehicle_tracking.get(vehicle_id, {}).get("detection_history", []) + [True]
                    }
                else:
                    # Detected but below confidence threshold
                    self.vehicle_tracking[vehicle_id] = {
                        "last_detected": None,
                        "detection_history": self.vehicle_tracking.get(vehicle_id, {}).get("detection_history", []) + [False]
                    }
        
        return realistic_detections
    
    def _apply_temporal_consistency(self, vehicle_id: str, base_rate: float) -> float:
        """Apply temporal consistency to detection rates"""
        if vehicle_id in self.vehicle_tracking:
            history = self.vehicle_tracking[vehicle_id].get("detection_history", [])
            if len(history) > 0 and history[-1]:  # Was detected last frame
                # Higher chance to detect again
                return min(0.98, base_rate * (1 + self.tracking_consistency * 0.2))
        
        return base_rate
    
    def _generate_realistic_confidence(self, vehicle_type: str) -> float:
        """Generate realistic confidence scores based on research data"""
        params = self.metrics.get_confidence_params(vehicle_type)
        
        # Generate confidence with realistic distribution
        confidence = np.random.normal(params["mean"], params["std"])
        
        # Apply realistic constraints
        confidence = np.clip(confidence, 0.1, 0.99)
        
        # Add some bias towards common confidence ranges
        if 0.5 <= confidence <= 0.9:  # Most detections fall in this range
            confidence *= 1.02  # Slight boost
        
        return confidence
    
    def get_performance_summary(self) -> dict:
        """Get performance summary with research-based metrics"""
        return {
            "model": "yolov8n_research_based",
            "scenario": self.metrics.scenario,
            "weather": self.metrics.weather,
            "confidence_threshold": self.confidence_threshold,
            "expected_detection_rates": {
                vtype: self.metrics.get_detection_rate(vtype)
                for vtype in ["car", "truck", "bus", "motorcycle"]
            },
            "confidence_distributions": {
                vtype: self.metrics.get_confidence_params(vtype)
                for vtype in ["car", "truck", "bus", "motorcycle"]
            }
        }
