import numpy as np # type: ignore
import json
import subscribe

from scipy.sparse import csr_array # type: ignore
from scipy.sparse.csgraph import floyd_warshall # type: ignore

direction0 = subscribe.direction[7]
w0 = subscribe.weight

arr = np.array([
        [   0,       0,    "w0+w2",    0],
        [   0,       0,       0,    "w1+w3"],
        ["w0+w2",    0,       0,       0],
        [   0,    "w1+w3",    0,       0]
    ])

graph = csr_array(arr)

dist_matrix = floyd_warshall(csgraph=graph, directed=False)
green_direction = dist_matrix.argmax(axis=0)
# Returns the row where the maximum traffic is detected, odd or
# even is what describes each direction.
#return green_direction