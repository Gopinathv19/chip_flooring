import ast
import json
import os
import re
import sys
from dataclasses import dataclass
from importlib import util as importlib_util
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from openai import OpenAI


ROOT = Path(__file__).resolve().parent
ENV_DIR = ROOT / "chip_flooring_env"
SERVER_DIR = ENV_DIR / "server"

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
TASK_NAME = os.getenv("TASK_NAME", "chip-flooring")
BENCHMARK = os.getenv("BENCHMARK", "chip_flooring_env")
MAX_STEPS = int(os.getenv("MAX_STEPS", "16"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "120"))


def load_module(module_name: str, path: Path):
    spec = importlib_util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    module = importlib_util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


models_mod = load_module("chip_flooring_env.models", ENV_DIR / "models.py")
env_mod = load_module(
    "chip_flooring_env.server.chip_flooring_env_environment",
    SERVER_DIR / "chip_flooring_env_environment.py",
)

ChipFlooringAction = models_mod.ChipFlooringAction
ChipFlooringEnvironment = env_mod.ChipFlooringEnvironment


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} "
        f"done={str(done).lower()} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{reward:.2f}" for reward in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} rewards={rewards_str}",
        flush=True,
    )


def build_prompt(step: int, grid: List[List[int]], remaining_blocks: List[Dict[str, Any]]) -> str:
    return (
        "You are controlling a chip-flooring placement environment.\n"
        "Choose exactly one valid next placement.\n"
        "Return JSON only with keys: block_id, x, y.\n"
        "Coordinates are zero-based indexing row, column.\n"
        "Prefer the earliest valid placement for the earliest remaining block.\n\n"
        f"Step: {step}\n"
        f"Grid: {json.dumps(grid)}\n"
        f"Remaining blocks: {json.dumps(remaining_blocks)}\n"
    )


def extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return None
    snippet = match.group(0)
    try:
        parsed = json.loads(snippet)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        try:
            parsed = ast.literal_eval(snippet)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None
    return None


def model_suggest_action(
    client: OpenAI,
    step: int,
    grid: List[List[int]],
    remaining_blocks: List[Dict[str, Any]],
    extra_instruction: str = "",
) -> Optional[Dict[str, Any]]:
    try:
        user_prompt = build_prompt(step, grid, remaining_blocks)
        if extra_instruction:
            user_prompt += f"\n{extra_instruction.strip()}\n"
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "Return a single JSON object with block_id, x, and y only.",
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        content = completion.choices[0].message.content or ""
        return extract_json_object(content)
    except Exception:
        return None


def normalize_action(
    env: ChipFlooringEnvironment,
    action_data: Optional[Dict[str, Any]],
) -> Tuple[Optional[ChipFlooringAction], Optional[Dict[str, Any]]]:
    remaining_ids = {block.id for block in env.state.remaining_blocks}
    if action_data:
        block_id = action_data.get("block_id")
        x = action_data.get("x")
        y = action_data.get("y")
        if block_id in remaining_ids and isinstance(x, int) and isinstance(y, int):
            index = next(
                (i for i, block in enumerate(env.state.blocks) if block.id == block_id),
                None,
            )
            if index is not None:
                block = env.state.blocks[index]
                if env.canvas.can_occupy((x, y), block.y, block.x):
                    return ChipFlooringAction(x=x, y=y, choosen_block_index=index), {
                        "block_id": block_id,
                        "x": x,
                        "y": y,
                    }

    return None, None


def action_to_string(action_repr: Optional[Dict[str, Any]]) -> str:
    if not action_repr:
        return "null"
    return json.dumps(action_repr, separators=(",", ":"))


def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY) if API_KEY else None
    env = ChipFlooringEnvironment()
    rewards: List[float] = []
    steps_taken = 0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        env.reset()

        for step in range(1, MAX_STEPS + 1):
            if not env.state.remaining_blocks:
                success = True
                break

            grid = env.canvas.grid if env.canvas else []
            remaining_blocks = [
                {
                    "id": block.id,
                    "height": block.x,
                    "width": block.y,
                    "placed": block.placed,
                    "position": block.position,
                }
                for block in env.state.remaining_blocks
            ]

            action = None
            action_repr = None
            attempt_hint = ""
            for _attempt in range(3):
                suggested = (
                    model_suggest_action(
                        client,
                        step,
                        grid,
                        remaining_blocks,
                        extra_instruction=attempt_hint,
                    )
                    if client
                    else None
                )
                action, action_repr = normalize_action(env, suggested)
                if action is not None and action_repr is not None:
                    break
                attempt_hint = (
                    "The previous answer was invalid or could not be placed. "
                    "Try again with a different valid JSON placement."
                )

            if action is None or action_repr is None:
                break

            try:
                result = env.step(action)
                reward = float(getattr(result, "reward", 0.0) or 0.0)
                done = bool(getattr(result, "done", False))
                error = None
                rewards.append(reward)
                steps_taken = step
                log_step(
                    step=step,
                    action=action_to_string(action_repr),
                    reward=reward,
                    done=done,
                    error=error,
                )
                if done:
                    success = len(env.state.remaining_blocks) == 0
                    break
            except Exception as exc:
                log_step(
                    step=step,
                    action=action_to_string(action_repr),
                    reward=0.0,
                    done=False,
                    error=str(exc),
                )
                steps_taken = step
                break

        if env.state.remaining_blocks == []:
            success = True
        elif not success:
            success = len(env.state.remaining_blocks) == 0
    finally:
        close = getattr(env, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                pass
        log_end(success=success, steps=steps_taken, rewards=rewards)


if __name__ == "__main__":
    main()
