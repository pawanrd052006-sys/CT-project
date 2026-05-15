"""
blockchain.py - Core Blockchain Implementation
================================================
This module implements a simple but real blockchain:
  - Each block contains product data
  - Each block stores the hash of the previous block (linking the chain)
  - SHA-256 is used to generate tamper-proof hashes
  - If any block is modified, hash validation will detect tampering
"""

import hashlib
import json
import time
from datetime import datetime


class Block:
    """
    Represents a single block in the blockchain.
    
    A block contains:
      - index: position in the chain
      - timestamp: when the block was created
      - data: the product information stored in this block
      - previous_hash: hash of the previous block (creates the "chain")
      - hash: SHA-256 hash of this block's contents
    """

    def __init__(self, index, data, previous_hash="0"):
        self.index = index
        self.timestamp = datetime.utcnow().isoformat()
        self.data = data                  # Product information dict
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash() # Computed on creation

    def calculate_hash(self):
        """
        Compute SHA-256 hash of all block contents.
        Any change to index, timestamp, data, or previous_hash 
        produces a completely different hash — this is tamper detection.
        """
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        """Serialize block to a dictionary for storage/display."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }


class Blockchain:
    """
    Manages the chain of blocks.
    
    Blockchain rules:
      1. The first block is the "Genesis Block" with no previous hash.
      2. Each new block links to the previous block via its hash.
      3. Integrity check: re-computing all hashes verifies nothing was tampered.
    """

    def __init__(self):
        self.chain = []
        self._create_genesis_block()

    def _create_genesis_block(self):
        """Create the very first block (Genesis Block) with no parent."""
        genesis = Block(
            index=0,
            data={"type": "GENESIS", "message": "BlockVerify Chain Initialized"},
            previous_hash="0" * 64  # 64 zeros — no parent
        )
        self.chain.append(genesis)

    def get_latest_block(self):
        """Return the most recently added block."""
        return self.chain[-1]

    def add_block(self, product_data):
        """
        Add a new block to the chain containing product_data.
        
        The new block's previous_hash = last block's hash.
        This is how the chain is formed — each block points back to its parent.
        """
        new_block = Block(
            index=len(self.chain),
            data=product_data,
            previous_hash=self.get_latest_block().hash
        )
        self.chain.append(new_block)
        return new_block

    def is_chain_valid(self):
        """
        Verify the entire chain has not been tampered with.
        
        For each block (after genesis):
          1. Re-compute its hash and compare with stored hash.
          2. Check that previous_hash matches the previous block's actual hash.
        Returns True if chain is intact, False if tampered.
        """
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # If the stored hash doesn't match recomputed hash → tampered
            if current.hash != current.calculate_hash():
                return False

            # If previous_hash link is broken → tampered
            if current.previous_hash != previous.hash:
                return False

        return True

    def find_product(self, product_id):
        """Search all blocks for a product with matching product_id."""
        for block in self.chain:
            if block.data.get("product_id") == product_id:
                return block
        return None

    def get_all_blocks(self):
        """Return all blocks as a list of dicts (skip genesis block in display)."""
        return [block.to_dict() for block in self.chain]

    def get_product_blocks(self):
        """Return only blocks that contain actual product data."""
        return [
            block.to_dict()
            for block in self.chain
            if block.data.get("type") != "GENESIS"
        ]

    def to_dict(self):
        """Serialize the entire blockchain."""
        return {
            "chain": [block.to_dict() for block in self.chain],
            "length": len(self.chain),
            "is_valid": self.is_chain_valid()
        }
