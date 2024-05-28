import time
import threading
from multiprocessing import Process, Manager, Lock
from pow_block import *
from utils import *

def main():
    n_nodes = 5
    byzantine_probability = 0.2
    difficulty = 5

    nodes = []
    manager = Manager()
    shared_blockchain = manager.list(["0" * 64])
    shared_lock = Lock()

    running_nodes = manager.Value('i', n_nodes)
    running_nodes_lock = Lock()

    for i in range(n_nodes):
        node = PowBlock(i, running_nodes, byzantine_probability, difficulty)
        node.set_blockchain(shared_blockchain)
        node.set_proc_lock(shared_lock)
        node.set_node_list(nodes)
        nodes.append(node)
        

    processes = []
    for node in nodes:
        p = Process(target=node.mine_blocks)
        processes.append(p)
        p.start()

    stop_key = threading.Event()
    input_thread = threading.Thread(target=check_for_q, args=(stop_key, running_nodes, running_nodes_lock))
    input_thread.daemon = True
    input_thread.start()

    while not stop_key.is_set():
        time.sleep(0.1)

    for p in processes:
        p.join()

    print("Blockchain:")
    for block in list(shared_blockchain):
        print(f"  - {block}")

    

if __name__ ==    '__main__':
    main()