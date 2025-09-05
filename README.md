Tested in an anaconda environment on Windows 11 with the packages listed in the requirements.txt file.

Run each node with the following command format: python main.py -i (insert number 0-3 for node index, required)
                                                                -v (path to video file, samples provided)
                                                                -n (number of nodes in the group)

graph TB
    subgraph "Detection Layer"
        A[Video Input] --> B[WeightDetector]
        B --> C[Vehicle Classification]
    end
    
    subgraph "Decision Layer"
        D[Weight Calculation] --> E[MeshNode Network]
        E --> F[Priority Decision]
    end
    
    subgraph "Control Layer"
        G[SUMO Controller] --> H[Traffic Lights]
    end
    
    C --> D
    F --> G
