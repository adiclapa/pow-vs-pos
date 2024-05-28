import time
import threading
import pprint
from datetime import datetime
from multiprocessing import Process, Manager, Lock, Barrier
from pos_block import PosBlock
from utils import *

def main():
    n_nodes = 5
    byzantine_probability = 0.2
    initial_weight = 50

    nodes = []
    manager = Manager()
    shared_blockchain = manager.list()
    proposed_blocks = manager.list()
    winners = manager.list()

    
    init_block = {
        "index": 0,
        "timestamp": str(datetime.now()),
        "weight": 0,
        "prev_hash": "",
        "validator": 0,
        "hash": ""
    }
    init_block["hash"] = sha256(str(init_block))
        
    shared_blockchain.append(init_block)
    shared_lock = Lock()

    running_nodes = manager.Value('i', n_nodes)
    running_nodes_lock = Lock()
    epoch_barrier = Barrier(n_nodes)

    for i in range(n_nodes):
        node = PosBlock(i, running_nodes, byzantine_probability, initial_weight)
        node.set_blockchain(shared_blockchain)
        node.set_proposed_blocks(proposed_blocks)
        node.set_proc_lock(shared_lock)
        node.set_node_list(nodes)
        node.set_winners(winners)
        node.set_epoch_barrier(epoch_barrier)
        nodes.append(node)

    for i in range(n_nodes):
        node.set_node_list(nodes)

    processes = []
    for node in nodes:
        p = Process(target=node.pos_mine)
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
        print(pprint.pprint(block))

if __name__ == '__main__':
    main()
