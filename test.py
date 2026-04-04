import importlib.util
import sys
import types
from pathlib import Path

root = Path('/home/gopi-nts0117/gopinath/chip_flooring')

# Stubs for missing local deps in this workspace.
openenv = types.ModuleType('openenv')
core = types.ModuleType('openenv.core')
env_server = types.ModuleType('openenv.core.env_server')
interfaces = types.ModuleType('openenv.core.env_server.interfaces')
types_mod = types.ModuleType('openenv.core.env_server.types')
pydantic_mod = types.ModuleType('pydantic')

class _Base:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class Environment(_Base):
    pass

class State(_Base):
    pass

class Action(_Base):
    pass

class Observation(_Base):
    pass

def Field(default=None, default_factory=None, description=None):
    if default_factory is not None:
        return default_factory()
    return default

interfaces.Environment = Environment
types_mod.State = State
types_mod.Action = Action
types_mod.Observation = Observation
pydantic_mod.Field = Field

sys.modules['openenv'] = openenv
sys.modules['openenv.core'] = core
sys.modules['openenv.core.env_server'] = env_server
sys.modules['openenv.core.env_server.interfaces'] = interfaces
sys.modules['openenv.core.env_server.types'] = types_mod
sys.modules['pydantic'] = pydantic_mod

chip_pkg = types.ModuleType('chip_flooring_env')
chip_pkg.__path__ = [str(root / 'chip_flooring_env')]
server_pkg = types.ModuleType('chip_flooring_env.server')
server_pkg.__path__ = [str(root / 'chip_flooring_env' / 'server')]
sys.modules['chip_flooring_env'] = chip_pkg
sys.modules['chip_flooring_env.server'] = server_pkg

models_path = root / 'chip_flooring_env' / 'models.py'
models_spec = importlib.util.spec_from_file_location('chip_flooring_env.models', models_path)
models_mod = importlib.util.module_from_spec(models_spec)
sys.modules['chip_flooring_env.models'] = models_mod
models_spec.loader.exec_module(models_mod)

env_path = root / 'chip_flooring_env' / 'server' / 'chip_flooring_env_environment.py'
env_spec = importlib.util.spec_from_file_location('chip_flooring_env.server.chip_flooring_env_environment', env_path)
env_mod = importlib.util.module_from_spec(env_spec)
sys.modules['chip_flooring_env.server.chip_flooring_env_environment'] = env_mod
env_spec.loader.exec_module(env_mod)

env = env_mod.ChipFlooringEnvironment()
obs = env.reset()

print("block_id_map:", env.block_id_map)
print("remaining:", [b["id"] for b in obs.remaining_blocks])
print("grid before:")
for row in obs.canva_space[:6]:
    print(row[:8])

for label, action in [
    ("A", models_mod.ChipFlooringAction(x=0, y=0, choosen_block_index=0)),
    ("B", models_mod.ChipFlooringAction(x=2, y=0, choosen_block_index=1)),
    ("C", models_mod.ChipFlooringAction(x=3, y=0, choosen_block_index=2)),
]:
    obs = env.step(action)
    print(f"after {label}: reward={obs.reward}, done={obs.done}")
    for row in env.canvas.grid[:6]:
        print(row[:8])
    print("remaining:", [b.id for b in env.state.remaining_blocks])
    print("placed:", [b.id for b in env.state.placed_blocks])
    print()

