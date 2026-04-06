from uuid import uuid4
import string
from typing import Optional

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import ChipFlooringAction, ChipFlooringObservation, ChipFlooringResponseState
except ImportError:
    from models import ChipFlooringAction, ChipFlooringObservation, ChipFlooringResponseState




class ChipFlooringEnvironment(Environment):
 
    def __init__(self):
        """Initialize the chip_flooring_env environment."""
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.grid_size=24
        self._reset_count = 0
        self.canvas = None
        self.blocks = []
        self.block_id_map = {}
        block_ids = list(string.ascii_uppercase[:24])
        nodes = []
        for idx, block_id in enumerate(block_ids):
            height = 1 + (idx % 3)
            width = 1 + ((idx + 1) % 3)
            nodes.append({"id": block_id, "height": height, "width": width})

        edges = []
        for idx in range(len(block_ids) - 1):
            edges.append(
                {
                    "from": block_ids[idx],
                    "to": block_ids[idx + 1],
                    "weight": 1.0 + (idx % 3) * 0.5,
                }
            )
        for idx in range(len(block_ids) - 2):
            if idx % 2 == 0:
                edges.append(
                    {
                        "from": block_ids[idx],
                        "to": block_ids[idx + 2],
                        "weight": 0.75 + (idx % 4) * 0.25,
                    }
                )

        self.global_netlist = {
            "nodes": nodes,
            "edges": edges,
        }
        self.global_netlist = {
            "nodes": [
                {"id": "A", "height": 2, "width": 1},
                {"id": "B", "height": 3, "width": 1},
                {"id": "C", "height": 1, "width": 4},
                {"id": "D", "height": 2, "width": 2},
                {"id": "E", "height": 1, "width": 3},
                {"id": "F", "height": 3, "width": 2},
                {"id": "G", "height": 2, "width": 3},
                {"id": "H", "height": 1, "width": 2},
                {"id": "I", "height": 4, "width": 1},
                {"id": "J", "height": 2, "width": 4},
                {"id": "K", "height": 3, "width": 2},
                {"id": "L", "height": 1, "width": 1},
                {"id": "M", "height": 2, "width": 1},
                {"id": "N", "height": 1, "width": 2},
                {"id": "O", "height": 3, "width": 3},
                {"id": "P", "height": 2, "width": 2},
                {"id": "Q", "height": 1, "width": 5},
                {"id": "R", "height": 4, "width": 2},
                {"id": "S", "height": 2, "width": 4},
                {"id": "T", "height": 1, "width": 3},
                {"id": "U", "height": 3, "width": 1},
                {"id": "V", "height": 2, "width": 3},
                {"id": "W", "height": 1, "width": 2},
                {"id": "X", "height": 3, "width": 4},
            ],
            "edges": [
                {"from": "A", "to": "F", "weight": 2.4},
                {"from": "A", "to": "C", "weight": 1.1},
                {"from": "B", "to": "G", "weight": 1.8},
                {"from": "B", "to": "D", "weight": 0.9},
                {"from": "C", "to": "H", "weight": 2.1},
                {"from": "C", "to": "J", "weight": 1.4},
                {"from": "D", "to": "I", "weight": 1.7},
                {"from": "D", "to": "K", "weight": 0.8},
                {"from": "E", "to": "J", "weight": 2.6},
                {"from": "E", "to": "L", "weight": 1.0},
                {"from": "F", "to": "M", "weight": 1.2},
                {"from": "F", "to": "N", "weight": 2.0},
                {"from": "G", "to": "O", "weight": 2.8},
                {"from": "G", "to": "P", "weight": 1.3},
                {"from": "H", "to": "Q", "weight": 1.6},
                {"from": "I", "to": "R", "weight": 2.2},
                {"from": "J", "to": "S", "weight": 2.9},
                {"from": "K", "to": "T", "weight": 1.5},
                {"from": "L", "to": "U", "weight": 0.7},
                {"from": "M", "to": "V", "weight": 1.9},
                {"from": "N", "to": "W", "weight": 1.4},
                {"from": "O", "to": "X", "weight": 3.1},
                {"from": "P", "to": "Q", "weight": 1.05},
                {"from": "Q", "to": "R", "weight": 2.35},
                {"from": "R", "to": "S", "weight": 1.65},
                {"from": "S", "to": "T", "weight": 0.95},
                {"from": "T", "to": "U", "weight": 1.25},
                {"from": "U", "to": "V", "weight": 2.15},
                {"from": "V", "to": "W", "weight": 1.35},
                {"from": "W", "to": "X", "weight": 2.45},
                {"from": "B", "to": "E", "weight": 1.75},
                {"from": "D", "to": "G", "weight": 2.05},
                {"from": "F", "to": "J", "weight": 1.55},
                {"from": "H", "to": "L", "weight": 0.85},
                {"from": "I", "to": "N", "weight": 1.45},
                {"from": "K", "to": "O", "weight": 2.25},
                {"from": "M", "to": "Q", "weight": 1.95},
                {"from": "P", "to": "T", "weight": 1.15},
                {"from": "R", "to": "V", "weight": 2.55},
                {"from": "S", "to": "X", "weight": 2.75},
            ],
        }


    def reset(self) -> ChipFlooringObservation:
        """
        Reset the environment.

        Returns:
            ChipFlooringObservation with a ready message
        """
        self._reset_count += 1
        self.canvas = Canvas(self.grid_size)
        self.blocks = self._convert_global_netlist_to_blocks()
        self.block_id_map = {
            block.id: idx + 1 for idx, block in enumerate(self.blocks)
        }
        self._state = ChipFlooringResponseState(
            episode_id=str(uuid4()),
            step_count=0,
            grid_size=self.grid_size,
            grid=self.canvas.grid,
            blocks=self.blocks,
            placed_blocks=[],
            remaining_blocks=list(self.blocks),
            done=False,
            reward=0
        )

        return self._build_observation()

         
    def step(self, action: ChipFlooringAction) -> ChipFlooringObservation:  # type: ignore[override]
 
        self._state.step_count += 1
        self._state.reward=0.0
        self._state.done=False
        
        invalid_reasons = None
        x = action.x
        y = action.y
        current_block_index = action.choosen_block_index

        if not isinstance(current_block_index,int) or current_block_index < 0 or current_block_index >= len(self._state.blocks):
            invalid_reasons = "Invalid Block Index correclty choose the block index with in the range"
            self._state.reward=-0.8
        else:
            block = self._state.blocks[current_block_index]
            
            if block not in self._state.remaining_blocks:
                invalid_reasons="The selected block is not in the ramining block properly choose the correct block"
                self._state.reward=-0.6
            elif not self.canvas.can_occupy((x,y),block.y,block.x):
                invalid_reasons = "The given possition cannot be occupied check the canvas once again for the right placment"
                self._state.reward = -0.5

            else:
                block_num = self.block_id_map[block.id]
                self.canvas.occupy_region((x,y),block.y,block.x,block_num)
                block.placed=True
                block.position=(x,y)
                self._state.placed_blocks.append(block)
                self._state.remaining_blocks.remove(block)
                self._state.reward = 0.2 + (0.8 if len(self._state.remaining_blocks)==0 else 0.0)
                self._state.done = len(self._state.remaining_blocks) == 0
        
        self._state.grid = self.canvas.grid
        self._state.trajectory.append(
            {
                "step_count": self._state.step_count,
                "action": {
                    "x": x,
                    "y": y,
                    "choosen_block_index": current_block_index,
                },
                "reward": self._state.reward,
                "done": self._state.done,
                "invalid_reason": invalid_reasons,
                "remaining_blocks": [b.id for b in self._state.remaining_blocks],
                "placed_blocks": [b.id for b in self._state.placed_blocks],
            }
        )

        return self._build_observation(invalid_reason=invalid_reasons)
            


        
 

    @property
    def state(self) -> State:
        """
        Get the current environment state.

        Returns:
            Current State with episode_id and step_count
        """
        return self._state

 

    '''
    This Function is used to convert the global netlist to blocks
    '''

    def _convert_global_netlist_to_blocks(self):
        nodes = self.global_netlist["nodes"]
        edges = self.global_netlist["edges"]

        blocks = {}

        for node in nodes:
            block = Block(id=node["id"], height=node["height"], width=node["width"])
            blocks[node["id"]] = block
        
        for edge in edges:
            src = edge["from"]
            dist = edge["to"]
            weight = edge["weight"]
            blocks[src].connect_block(blocks[dist], weight)
            blocks[dist].connect_block(blocks[src], weight)

        return list(blocks.values())
    
    def _block_to_dict(self,block):
        return{
            "id":block.id,
            "height":block.x,
            "width":block.y,
            "placed":block.placed,
            "position":block.position
        }
    
    def _build_observation(self,invalid_reason: Optional[str]=None)->ChipFlooringObservation:
        return ChipFlooringObservation(
            canva_space=self.canvas.grid,
            remaining_blocks=[self._block_to_dict(b) for b in self._state.remaining_blocks],
            placed_blocks=[self._block_to_dict(b) for b in self._state.placed_blocks],
            done=self._state.done,
            reward=self._state.reward,
            invalid_reasons=invalid_reason,
        )
    


class Canvas:

    '''
        Initializing the grid type canvas in order to pricisely map the components in the canvas
    '''
    def __init__(self,grid_size):
        self.grid_size = grid_size
        self.grid = [[0 for _ in range(grid_size)] for _ in range(grid_size)]

    '''
        Function for knowing whether the particular unit is available or not
    '''

    def is_unit_occupied(self,x,y):
        return self.grid[x][y] != 0
    
    '''
        Function to identify whether the component can be placed in the grid
    '''

    def can_occupy(self, anchor, width, height):
        row, col = anchor

        # boundary check
        if row + height > self.grid_size or col + width > self.grid_size:
            return False

        # overlap check
        for dx in range(height):
            for dy in range(width):
                if self.grid[row + dx][col + dy] != 0:
                    return False

        return True
        
    '''
        Function for using the group of cords in the grid
    '''
    def occupy_region(self, anchor, width, height, block_id):
        row, col = anchor
        for dx in range(height):
            for dy in range(width):
                self.grid[row + dx][col + dy] = block_id

    '''
        Function for removing the group of cords in the grid
    '''
    
    def remove_region(self, anchor, width, height):
        row, col = anchor
        for dx in range(height):
            for dy in range(width):
                self.grid[row + dx][col + dy] = 0

class Block:
    def __init__(self,id,height,width):
        self.id = id 
        self.x  = height
        self.y  = width
        self.placed = False
        self.position = None
        self.internal_netlist = {}

    def connect_block(self,block,weight):
        self.internal_netlist[block.id] = weight
    
    def get_internal_netlist(self):
        return self.internal_netlist

        


       

            
           

    
 

        
