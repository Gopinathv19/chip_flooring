---
title: Chip Flooring Env
emoji: 🧩
colorFrom: red
colorTo: blue
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
  - chip-flooring
  - physical-design
---

# Chip Flooring Env

Chip Flooring Env is a deterministic floorplanning benchmark for agentic placement.
An agent must place rectangular blocks on a discrete grid while respecting legality
constraints and minimizing weighted wirelength across a small netlist.

## Task Presets

The environment exposes three submission tasks via `TASK_NAME`:

- `easy`: 5 blocks on a `12x12` grid
- `medium`: 10 blocks on an `18x18` grid
- `hard`: 15 blocks on a `24x24` grid

Each task uses the same action and observation API, but the density of blocks and
connectivity pressure increase with difficulty.

## Environment Contract

### Action

`ChipFlooringAction` contains:

- `x`: row anchor for the selected block
- `y`: column anchor for the selected block
- `choosen_block_index`: index of the block in the remaining block list

### Observation

`ChipFlooringObservation` contains:

- `canva_space`: current grid occupancy
- `remaining_blocks`: blocks not yet placed
- `placed_blocks`: blocks already placed
- `block_summaries`: connectivity summaries for the remaining blocks
- `candidate_positions`: scored legal anchors for the next placement
- `density_map`: coarse congestion map
- `placement_focus`: the block that should usually be placed next
- `current_hpwl`: current weighted HPWL for placed nets
- `delta_hpwl`: HPWL added by the latest placement
- `placed_block_count`: number of placed blocks
- `task_name`: current task preset
- `invalid_reasons`: reason for the last rejected action, if any

### Reward

The reward is shaped to encourage:

- legal placements
- placing connected blocks near each other
- reducing HPWL
- completing the full placement episode

Invalid placements receive a penalty.

## Deterministic Grading

The manifest registers three deterministic task tiers and exposes a metadata-style
`/grader` endpoint plus a `/tasks` endpoint:

- `/tasks` returns the task metadata
- `/grader` returns a normalized score in `[0, 1]`

The environment itself computes the dense reward during `step()`, so no LLM grader
is needed for submission.

## Running Locally

```bash
cd chip_flooring_env
oenv/bin/openenv validate
oenv/bin/python -m chip_flooring_env.server.app
```

You can also connect through the client:

```python
from chip_flooring_env import ChipFlooringAction, ChipFlooringEnv

with ChipFlooringEnv(base_url="http://localhost:8000").sync() as env:
    result = env.reset()
    print(result.observation.task_name)
```

## Deployment

The environment is packaged as a FastAPI OpenEnv space and can be validated with:

```bash
cd chip_flooring_env
oenv/bin/openenv validate
```

The repository also includes a root-level `inference.py` that prints the required
submission logs:

- `[START] ...`
- `[STEP] ...`
- `[END] ... score=... rewards=...`
