# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Chip Flooring Env Environment Implementation.

A simple test environment that echoes back messages sent to it.
Perfect for testing HTTP server infrastructure.
"""

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
        self._reset_count = 0
        self.canvas = None
        self.block = []
        self.current_block_index = 0

    def reset(self) -> ChipFlooringObservation:
        """
        Reset the environment.

        Returns:
            ChipFlooringObservation with a ready message
        """
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._reset_count += 1
        self.canvas = Canvas(grid_size=16)
        self.block  = []
        self._state = ChipFlooringResponseState(
            episode_id=str(uuid4()),
            step_count=0,
            grid_size=self.grid_size,
            grid=self.canvas.grid,
            blocks=self.block,
            current_block_index=0,
            placed_blocks=[],
            remaining_blocks=[],
            done=False
        )

    def step(self, action: ChipFlooringAction) -> ChipFlooringObservation:  # type: ignore[override]
        """
        Execute a step in the environment by echoing the message.

        Args:
            action: ChipFlooringAction containing the message to echo

        Returns:
            ChipFlooringObservation with the echoed message and its length
        """
        self._state.step_count += 1

        message = action.message
        length = len(message)

        # Simple reward: longer messages get higher rewards
        reward = length * 0.1
        
        return ChipFlooringObservation(
            echoed_message=message,
            message_length=length,
            done=False,
            reward=reward,
            metadata={"original_message": message, "step": self._state.step_count},
        )

    @property
    def state(self) -> State:
        """
        Get the current environment state.

        Returns:
            Current State with episode_id and step_count
        """
        return self._state

    def _make_observation(self):
        return ChipFlooringObservation(
            canva_space=self._state.grid,
            current_block_structure=self._state.blocks[self._state.current_block_index],
            current_block_index=self.state.current_block_index,
            total_block=len(self._state.blocks),
            done=self._state.done,
            reward=self.state.reward,
        )
    


class Canvas:

    '''
        Initializing the grid type canvas in order to pricisely map the components in the canvas
    '''
    def __init__(self,grid_size):
        self.grid = [[0]*(grid_size) for _ in range(grid_size)]

    '''
        Function for knowing whether the particular unit is available or not
    '''

    def is_unit_occupied(self,x,y):
        return self.grid[x][y]==1
    
    '''
        Function to identify whether the component can be placed in the grid
    '''

    def can_occupy(self,anchor_cords,width,height):

        x,y = anchor_cords

        if x >= self.grid_size or y>=self.grid.size:
            return False

        for dx in range(height):
            for dy in range(width):
                if self.grid[x+dx][y+dy]==1:
                    return False
                
        return True 
    

   
    
    
    '''
        Function for using the group of cords in the grid
    '''
    def occupy_region(self,anchor_cords,width,height):
        x,y = anchor_cords
        for dx in range(height):
            for dy in range(width): 
                self.grid[x+dx][y+dy]=1

    '''
        Function for removing the group of cords in the grid
    '''
    
    def remove_region(self,anchor_cords,width,height):
        x,y=anchor_cords
        for dx in range(height):
            for dy in range(width):
                self.grid[x+dx][y+dy]=0

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

        


       

            
           

    
 

        
