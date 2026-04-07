from uuid import uuid4
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
        self.hpwl_weight = 0.03
        self._reset_count = 0
        self.canvas = None
        self.blocks = []
        self.block_id_map = {}
        self._block_lookup = {}
        # Standard 15-block benchmark for v1/v2 evaluation.
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
                {"from": "B", "to": "E", "weight": 1.75},
                {"from": "D", "to": "G", "weight": 2.05},
                {"from": "F", "to": "J", "weight": 1.55},
                {"from": "H", "to": "L", "weight": 0.85},
                {"from": "I", "to": "N", "weight": 1.45},
                {"from": "K", "to": "O", "weight": 2.25},
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
        self._block_lookup = {block.id: block for block in self.blocks}
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
            reward=0,
            current_hpwl=0.0,
            delta_hpwl=0.0,
        )

        return self._build_observation()

         
    def step(self, action: ChipFlooringAction) -> ChipFlooringObservation:  # type: ignore[override]
 
        self._state.step_count += 1
        self._state.reward=0.0
        self._state.done=False
        self._state.delta_hpwl = 0.0
        
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
                incremental_hpwl = self._compute_incremental_hpwl(block)
                self._state.delta_hpwl = incremental_hpwl
                self._state.current_hpwl = self._compute_total_hpwl()
                self._state.reward = 0.2 - (self.hpwl_weight * incremental_hpwl)
                self._state.done = len(self._state.remaining_blocks) == 0
                if self._state.done:
                    self._state.reward += 0.8 - (self.hpwl_weight * self._state.current_hpwl)
        
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
                "current_hpwl": self._state.current_hpwl,
                "delta_hpwl": self._state.delta_hpwl,
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

    def _block_center(self, block: "Block"):
        if block.position is None:
            return None
        row, col = block.position
        return (row + (block.x / 2.0), col + (block.y / 2.0))

    def _manhattan_distance(self, point_a, point_b):
        return abs(point_a[0] - point_b[0]) + abs(point_a[1] - point_b[1])

    def _compute_incremental_hpwl(self, placed_block: "Block") -> float:
        """
        Compute the wirelength added by the latest placement.

        Only connections whose other endpoint is already placed are counted here,
        so each edge is charged once when its second endpoint lands.
        """
        placed_center = self._block_center(placed_block)
        if placed_center is None:
            return 0.0

        total = 0.0
        for neighbor_id, weight in placed_block.get_internal_netlist().items():
            neighbor = self._block_lookup.get(neighbor_id)
            if neighbor is None or not neighbor.placed:
                continue
            neighbor_center = self._block_center(neighbor)
            if neighbor_center is None:
                continue
            total += weight * self._manhattan_distance(placed_center, neighbor_center) / self.grid_size

        return total

    def _compute_total_hpwl(self) -> float:
        """
        Compute the total weighted HPWL for the currently placed layout.

        This only counts edges where both endpoints are already placed.
        """
        total = 0.0
        for edge in self.global_netlist["edges"]:
            src = self._block_lookup.get(edge["from"])
            dst = self._block_lookup.get(edge["to"])
            if src is None or dst is None or not src.placed or not dst.placed:
                continue
            src_center = self._block_center(src)
            dst_center = self._block_center(dst)
            if src_center is None or dst_center is None:
                continue
            total += edge["weight"] * self._manhattan_distance(src_center, dst_center) / self.grid_size

        return total
    
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
            current_hpwl=self._state.current_hpwl,
            delta_hpwl=self._state.delta_hpwl,
            placed_block_count=len(self._state.placed_blocks),
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

        


       

            
           

    
 

        
