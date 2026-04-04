from uuid import uuid4

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
        self.grid_size=16
        self._reset_count = 0
        self.canvas = None
        self.blocks = []
        self.block_id_map = {}
        self.global_netlist ={
    "nodes": [
        {"id": "A", "height": 2, "width": 3},
        {"id": "B", "height": 1, "width": 2},
        {"id": "C", "height": 2, "width": 2},
    ],
    "edges": [
        {"from": "A", "to": "B", "weight": 1.0},
        {"from": "A", "to": "C", "weight": 2.0},
        {"from": "B", "to": "C", "weight": 1.5},
    ]
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

        return ChipFlooringObservation(
            canva_space=self.canvas.grid,
            remaining_blocks = [self._block_to_dict(b) for b in self._state.remaining_blocks],
            placed_blocks = [],
            done=False,
            reward=0
        )

         
    def step(self, action: ChipFlooringAction) -> ChipFlooringObservation:  # type: ignore[override]
 
        self._state.step_count += 1
        x = action.x
        y = action.y
        current_block_index = action.choosen_block_index
        
        if current_block_index < len(self._state.blocks):
            block = self._state.blocks[current_block_index]
            if self.canvas.can_occupy((x, y), block.y, block.x):
                block_num = self.block_id_map[block.id]
                self.canvas.occupy_region((x, y), block.y, block.x, block_num)
                self._state.placed_blocks.append(block)
                self._state.remaining_blocks.remove(block)
                self._state.reward = 1
                self._state.done = len(self._state.remaining_blocks) == 0
            else:
                self._state.reward = 0
                self._state.done = False
        else:
            self._state.reward = 0
            self._state.done = len(self._state.remaining_blocks) == 0
             

        return ChipFlooringObservation(
            done= self._state.done,
            reward=self._state.reward
        )

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

        


       

            
           

    
 

        
