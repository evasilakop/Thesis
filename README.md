````markdown
# 🚦 Intelligent Traffic Light System

An adaptive traffic management system using computer vision and distributed decision-making to optimize traffic flow in real-time.

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph DL ["🔍 Detection Layer"]
        A[Video Input] --> B[Computer Vision]
        B --> C[Vehicle Classification]
        C --> D["• Cars<br/>• Buses<br/>• Trucks<br/>• Motorcycles"]
    end
    
    subgraph DecL ["🧠 Decision Layer"] 
        E[Weight Calculation] --> F[Network Communication]
        F --> G[Priority Index]
    end
    
    subgraph CL ["⚡ Control Layer"]
        H[Control Messages] --> I[SUMO Controller]
        I --> J[Traffic Light Management]
    end
    
    D --> E
    G --> H
    
    style DL fill:#e1f5fe
    style DecL fill:#f3e5f5
    style CL fill:#e8f5e8
```

## 🛠️ System Requirements

- **OS**: Windows 11 (tested)
- **Environment**: Anaconda
- **Python**: 3.x
- **Dependencies**: See `requirements.txt`

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/evasilakop/Thesis.git
   cd Thesis
   ```

2. **Create conda environment:**
   ```bash
   conda create -n traffic-system python=3.12
   conda activate traffic-system
   ```

3. **Install dependencies:**
   

```bash
   pip install -r requirements.txt
   ```

## 🚀 Usage

### Running Individual Nodes

Each node represents a traffic direction and must be run separately:

```bash
python main.py -i <node_index> -v <video_path> -n <total_nodes> [options]
```

### Required Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `-i, --index` | Node index (0-3) | `-i 0` |
| `-v, --video` | Path to video file | `-v videos/north_traffic.mp4` |
| `-n, --nodes` | Total nodes in group | `-n 4` |

### Optional Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-c, --confidence` | Detection confidence threshold | `0.5` |
| `-f, --frequency` | Detection frequency (seconds) | `15` |
| `-g, --gui` | Enable SUMO GUI visualization | `False` |

### Example Commands

**4-Node Intersection Setup:**
```bash
# Terminal 1 - North Node
python main.py -i 0 -v videos/north.mp4 -n 4 -g

# Terminal 2 - West Node  
python main.py -i 1 -v videos/west.mp4 -n 4 -g

# Terminal 3 - South Node
python main.py -i 2 -v videos/south.mp4 -n 4 -g

# Terminal 4 - East Node
python main.py -i 3 -v videos/east.mp4 -n 4 -g
```

**2-Node Intersection Setup:**
```bash
# Terminal 1 - North Node
python main.py -i 0 -v videos/north.mp4 -n 2

# Terminal 2 - West Node
python main.py -i 1 -v videos/west.mp4 -n 2
```

## 🎯 Key Features

- **Real-time Vehicle Detection**: Computer vision-based traffic monitoring
- **Adaptive Signal Control**: Dynamic traffic light timing based on actual traffic
- **Distributed Decision Making**: Mesh network communication between nodes
- **Multi-vehicle Classification**: Cars, buses, trucks, motorcycles
- **SUMO Integration**: Professional traffic simulation environment
- **Scalable Architecture**: Support for 2-node and 4-node intersections

## 🔧 Configuration

### Vehicle Weight Mapping
The system assigns different weights to vehicle types for priority calculation:

```python
label_to_sumo_type = {
    "car": "car",
    "bus": "bus", 
    "truck": "truck",
    "motorcycle": "motorcycle"
}
```

### Network Ports
- Node 0: `127.0.0.1:5001`
- Node 1: `127.0.0.1:5002` 
- Node 2: `127.0.0.1:5003`
- Node 3: `127.0.0.1:5004`

## 📊 Logging

System logs are automatically generated in the `logs/` directory:
- Console output for real-time monitoring
- File logging in `logs/simulation.log`

## 🙏 Acknowledgments

- SUMO Traffic Simulation Suite
- OpenCV Computer Vision Library
- Research in Intelligent Transportation Systems

---

**Note**: This system is designed for research and educational purposes. For production deployment, additional safety measures and certifications would be required.
````
