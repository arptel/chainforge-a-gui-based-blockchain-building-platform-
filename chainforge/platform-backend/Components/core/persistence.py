import os
import json
import logging
from typing import Optional, List, Any
from core.block import Block

logger = logging.getLogger(__name__)

class Persistence:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        self.blocks_file = os.path.join(data_dir, "blocks.json")
        self.state_file = os.path.join(data_dir, "state.json")

    def save_block(self, block: Block):
        """Append a block to the storage."""
        # In a real implementation, usage of LevelDB or SQLite is preferred.
        # This is a simple JSON append for demonstration.
        blocks = self.load_all_blocks()
        blocks.append(block.to_dict())
        
        with open(self.blocks_file, "w") as f:
            json.dump(blocks, f, indent=4)
            
    def load_last_block(self) -> Optional[Block]:
        """Load the last block from storage."""
        blocks = self.load_all_blocks()
        if not blocks:
            return None
        
        last_block_data = blocks[-1]
        # Reconstruct block object
        return Block(**last_block_data) # Ensure Block constructor matches dictionary
        
    def load_all_blocks(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.blocks_file):
            return []
        try:
            with open(self.blocks_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def save_state(self, state: dict):
        with open(self.state_file, "w") as f:
            json.dump(state, f)
            
    def load_state(self) -> dict:
        if not os.path.exists(self.state_file):
            return {}
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except:
             return {}
