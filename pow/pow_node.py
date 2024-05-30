import random
import numpy as np 
from time import sleep
from multiprocessing import Queue
from utils import NodeType, sha256

class PowNode:
    def __init__(self, index, running_nodes, byzantine_probability, difficulty):
        self.index = index
        self.difficulty = difficulty
        self.running_nodes = running_nodes
        self.message_queue = Queue()
        self.node_type = self._decide_node_type(byzantine_probability)

    def set_blockchain(self, shared_blockchain):
        self.blockchain = shared_blockchain

    def set_proc_lock(self, shared_lock):
        self.lock = shared_lock

    def set_node_list(self, nodes):
        self.nodes = nodes

    def get_message_queue(self):
        return self.message_queue

        
    def is_byzantine(self):
        if self.node_type == NodeType.BYZANTINE: return True
        return False
    
    def get_node_type(self):
        return self.node_type
    
    def get_index(self):
        return self.index
    
    def _decide_node_type(self, probability):
        return np.random.choice([NodeType.HONEST, NodeType.BYZANTINE], p=[1-probability, probability])
    
    
    def _mine(self, block, merkle_root_hash):
        new_block=""
        while not self._check_block(new_block):
            nonce = random.randint(0, 100000000)
            new_block=sha256(block + str(nonce) + merkle_root_hash)
        return new_block


    def _check_block(self, new_block):
        if not new_block.startswith("0" * self.difficulty):
            return False

        if new_block == self.blockchain[-1]:
            return False
        
        return True

    def _vote_block(self, new_block):
        votes = 0
        if new_block in self.blockchain:
            return False
        for node in self.nodes:
            if node.is_byzantine():
                vote = not node._check_block(new_block)
            else:
                vote = node._check_block(new_block)

            if vote:
                votes += 1

        return votes >= len(self.nodes) - len([node for node in self.nodes if node.is_byzantine()])

    def _broadcast_block(self, new_block):
        for node in self.nodes:
            q = node.get_message_queue()
            q.put((new_block))

    def _generate_transactions(self, num_transactions):
        transactions = []
        for _ in range(num_transactions):
            sender = random.randint(1, 100)
            receiver = random.randint(1, 100)
            amount = random.uniform(0.1, 100)
            transactions.append((sender, receiver, amount))
        return transactions

    def _merkle_root(self, transactions):
        if not transactions:
            return ""

        hashes = [sha256(str(tx)) for tx in transactions]

        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])

            hashes = [sha256(hashes[i] + hashes[i + 1]) for i in range(0, len(hashes), 2)]

        return hashes[0]


    def mine_blocks(self):
        print(f"Node {self.index} type: ", self.node_type)

        while self.running_nodes.value > 0:
            with self.lock:
                block = self.blockchain[-1]

            transactions = self._generate_transactions(random.randint(1, 10))
            merkle_root_hash = self._merkle_root(transactions)

            new_block = 64*'F'
            if self.is_byzantine():
                new_block = sha256(new_block + "NOT TODAY - " + str(random.randint(0, 1000000000)))
            else:
                new_block = self._mine(block, merkle_root_hash)

            self._broadcast_block(new_block)

            if self._vote_block(new_block):
                with self.lock:
                    self.blockchain.append(new_block)
                    print(f"Node {self.index} mined a new block: {new_block}")
            
            if self.is_byzantine():
                sleep(2)
        
        print(f"Node {self.index}: stopped mining.")