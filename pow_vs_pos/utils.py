import hashlib
import random
from enum import Enum

class NodeType(Enum):
    HONEST = 1
    BYZANTINE = 2

def sha256(data):
    return hashlib.sha256(data.encode()).hexdigest()

def check_for_q(key, running_nodes, running_nodes_lock):
    while not key.is_set():
        if input().lower() == 'q':
            with running_nodes_lock:
                running_nodes.value = 0
            key.set()
