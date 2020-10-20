from hashlib import sha256
import json
import time


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash):

        # Constructor for the `Block` class.
        # :param index:         Unique ID of the block.
        # :param transactions:  List of transactions.
        # :param timestamp:     Time of generation of the block.
        # :param previous_hash: Hash of the previous block in the chain which this block is part of.

        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash  # Adding the previous hash field

    def compute_hash(self):

        # Returns the hash of the block instance by first converting it
        # into JSON string.

        # The string equivalent also considers the previous_hash field now
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()


class Blockchain:
    difficulty = 2

    def __init__(self):
        # """
        # Constructor for the `Blockchain` class.
        # """
        self.unconfirmed_transactions = []  # data yet to get into blockchain
        self.chain = []
        self.create_genesis_block()

    def proof_of_work(self, block):
        """
        Function that tries different values of the nonce to get a hash
        that satisfies our difficulty criteria.
        """
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def create_genesis_block(self):
        # """
        # A function to generate genesis block and appends it to
        # the chain. The block has index 0, previous_hash as 0, and
        # a valid hash.
        # """
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        # """
        # A quick pythonic way to retrieve the most recent block in the chain. Note that
        # the chain will always consist of at least one block (i.e., genesis block)
        # """
        return self.chain[-1]

    def add_block(self, block, proof):
        # """
        # A function that adds the block to the chain after verification.
        # Verification includes:
        # * Checking if the proof is valid.
        # * The previous_hash referred in the block and the hash of a latest block
        #   in the chain match.
        # """
        previous_hash = self.last_block.hash
        if previous_hash != block.previous_hash:
            return False

        if not Blockchain.is_valid_proof(self, block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    def is_valid_proof(self, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    def mine(self):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out proof of work.
        """
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)
        self.unconfirmed_transactions = []
        return new_block.index
