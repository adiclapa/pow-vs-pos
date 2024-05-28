import random
from collections import Counter
import numpy as np
from time import sleep
from datetime import datetime
from hashlib import sha256
from multiprocessing import Queue
from utils import NodeType, sha256

class PosBlock:
    def __init__(self, index, running_nodes, byzantine_probability, initial_weight):
        """
        Initialize a new PoS block node.
        
        :param index: Index of the node.
        :param running_nodes: Shared value to keep track of running nodes.
        :param byzantine_probability: Probability of the node being Byzantine.
        :param initial_weight: Initial weight for the node.
        """
        self.index = index
        self.running_nodes = running_nodes
        self.node_type = self._decide_node_type(byzantine_probability)
        self.weight = initial_weight
        self.age = 1
        self.address = sha256(str(index))

    def get_address(self):
        return self.address
    
    def get_weight(self):
        return self.weight
    
    def get_age(self):
        return self.age
    
    def get_index(self):
        return self.index

    def set_blockchain(self, shared_blockchain):
        self.blockchain = shared_blockchain

    def set_proposed_blocks(self, proposed_blocks):
        self.proposed_blocks = proposed_blocks

    def set_proc_lock(self, shared_lock):
        self.lock = shared_lock

    def set_epoch_barrier(self, epoch_barrier):
        self.epoch_barier=epoch_barrier

    def set_node_list(self, nodes):
        self.nodes = nodes

    def set_winners(self, winners):
        self.winners=winners

    def _decide_node_type(self, probability):
        return np.random.choice([NodeType.HONEST, NodeType.BYZANTINE], p=[1-probability, probability])

    def is_byzantine(self):
        return self.node_type == NodeType.BYZANTINE

    def generate_new_block(self):
        """
        Generate a new block to add to the blockchain.
        """

        prev_hash = self.blockchain[-1]['hash']
        new_block = {
            "index": len(self.blockchain),
            "timestamp": str(datetime.now()),
            "prev_hash": sha256('byzantine') if self.is_byzantine() else prev_hash,
            "validator": self.address,
        }
        new_block["hash"] = sha256(str(new_block))
        return new_block

    def validate_block(self, block, prev_block=None):
        """
        Validate a given block against the previous block.
        
        :param block: Block to validate.
        :param prev_block: Previous block in the blockchain.
        :return: True if the block is valid, else False.
        """
        if self.is_byzantine():
            return True

        try:
            _hash = block.pop('hash')
            hash2 = sha256(str(block))
            block['hash'] = _hash
            assert _hash == hash2
        except (KeyError, AssertionError):
            return False

        prev_hash = prev_block['hash'] if prev_block else self.blockchain[-1]['hash']
        if self.blockchain:
            try:
                assert prev_hash == block["prev_hash"]
            except AssertionError:
                return False
        return True

    def add_new_block(self, block):
        """
        Add a new block to the blockchain if it is valid.
        
        :param block: Block to add.
        """
        if self.validate_block(block):
            self.blockchain.append(block)

    def most_frequent_items(self,lst):
        if not lst:
            return []

        counting = [block['validator'] for block in lst]
        count = Counter(counting)
        max_count = max(count.values())
        most_frequent = [item for item, cnt in count.items() if cnt == max_count]
        return most_frequent

    def pick_winner(self):
        # pick winner here
        # Initial check to make sure there are proposed blocks
        
        winner=None
        while winner==None:
            try:
                self.epoch_barier.wait(timeout=15)
                if not self.proposed_blocks:
                    return None
                # Choose the winner based on weighted random choice, leveraging the 'weight' as the chance of selection
                stakes=[0]*len(self.nodes)
                for node in self.nodes:
                    stakes[node.get_index()] = node.get_weight()*node.get_age()
                total_stake=sum(stakes)
                
                print(f"Node {self.index} stakes: {stakes}")
                print(f"Total stake - {self.index}: {total_stake}")
                print(f"Node {self.index} - proposed blocks len {len(self.proposed_blocks)}")
                

                if self.is_byzantine():
                    for node in self.nodes:
                        if node.is_byzantine():
                            for block in self.proposed_blocks:
                                if block['validator'] == node.get_address():
                                    winning_block=block
                                    break
                else:
                    winning_block = random.choices(self.proposed_blocks, weights=[stake/total_stake for stake in stakes], k=1)[0]
                
                self.winners.append(winning_block)
                self.epoch_barier.wait(timeout=15)

                selection_result = self.most_frequent_items(self.winners)
                # print(f"Node {self.index} - selection resutl: {selection_result}")
                if selection_result == None:
                    continue
                if len(selection_result) == 1:
                    for item in self.winners:
                        if item['validator'] == selection_result[0]:
                            winner = item
                            break
            except Exception as e:
                print(f"Node {self.index} error: {str(e)}")
                self.weight=self.weight-5
                return None

        if self.address == winner['validator']:
            print(f"Winner is {winner} with block index {winning_block['index']}.")
            self.add_new_block(winner)
            self.weight+=1
            self.age=0
        else:
            self.age+=1

    def pos_mine(self):
        """
        Perform the Proof of Stake mining process.
        """
        print(f"Node {self.index} type: {self.node_type}")
        
        while self.running_nodes.value > 0:
            self.epoch_barier.wait()
            self.winners[:] = [] 
            self.proposed_blocks[:] = [] 
            new_block = self.generate_new_block()
            self.propose_block(new_block)
            self.pick_winner()
            sleep(1)

    def propose_block(self, block):
        self.proposed_blocks.append(block)
        

