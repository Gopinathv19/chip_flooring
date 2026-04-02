# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Chip Flooring Env Environment.

The chip_flooring_env environment is a simple test environment that echoes back messages.
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class ChipFlooringAction(Action):
    """Action for the Chip Flooring Env environment - just a message to echo."""

    message: str = Field(..., description="Message to echo back")


class ChipFlooringObservation(Observation):
    """Observation from the Chip Flooring Env environment - the echoed message."""

    canva_space : list[list[int]] = Field(default=[[0]],description="The grid type structure to represent the canva space")
    current_block_structure : dict = Field(default={},description="Used to define the current block structure")
    current_block_index : int = Field(default=0 ,description="Used to point in which block we are currently at")
    total_block : int = Field(default=0,description="Used to Identify the total block")

class ChipFlooringResponseState(State):
    "State for the Chip Flooring Environment to track the changes in the environment"

    episode_id : str = Field(default="",description="Used to identify the episode id")
    step_count : int = Field(default=0,description="Used to identify the step count")
    grid_size : int = Field(default=16,description="Used to identify the grid size")
    grid : list[list[int]] = Field(default=[[0]],description="Used to identify the grid")
    blocks : list[Block] = Field(default=[],description="Used to identify the blocks")
    current_block_index : int = Field(default=0,description="Used to identify the current block index")
    placed_blocks : list[Block] = Field(default=[],description="Used to identify the placed blocks")
    remaining_blocks : list[Block] = Field(default=[],description="Used to identify the remaining blocks")
    done : bool = Field(default=False,description="Used to identify if the episode is done")




