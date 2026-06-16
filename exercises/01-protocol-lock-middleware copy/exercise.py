"""
HAEEM exercise 01 — Protocol-Lock gatekeeper middleware (STUDENT SCAFFOLD)

Goal: implement ProtocolLockMiddleware so a FGOALS run cannot be submitted before
the study config is locked. See README.md for full requirements.

Setup & run (uv):
    uv sync                              # create .venv and install deps from pyproject.toml
    cp .env.example .env                 # then put your key in .env (ANTHROPIC_API_KEY=...)
    uv run python exercise.py
    # If your folder path contains a ':' (colon), `uv run` fails — use the venv directly:
    #     ./.venv/bin/python exercise.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from dotenv import load_dotenv

# Load this folder's .env (e.g. ANTHROPIC_API_KEY=...) regardless of the cwd you run from.
load_dotenv(Path(__file__).with_name(".env"))

from deepagents import create_deep_agent
from langchain.agents.middleware import AgentMiddleware
from langchain.tools.tool_node import ToolCallRequest
from langchain.messages import ToolMessage
from langchain_core.tools import tool

# Shared "pseudo-DB": tools WRITE it, the gatekeeper READS it.
STORE: dict = {"locked_studies": set()}

# (Stretch goal) tunable parameter bounds — HAEEM default subset (ADR-0004).
BOUNDS: dict[str, tuple[float, float]] = {
    "ccn_o": (0.1, 5.0),
    "c_psaci": (0.1, 2.0),
    "vr_fac": (0.5, 2.0),
}


# ----------------------------------------------------------------------------
# Tools (the "backend / action API") — already done for you.
# ----------------------------------------------------------------------------
@tool
def lock_study_config(study_design_id: str) -> str:
    """Lock a study so confirmatory runs are allowed (the human-approved step)."""
    STORE["locked_studies"].add(study_design_id)
    return f"Study {study_design_id} is now LOCKED."


@tool
def propose_parameter_set(study_design_id: str, parameters: dict) -> str:
    """Propose a parameter set for a study."""
    return f"Parameter set accepted for {study_design_id}: {parameters}"


@tool
def submit_fgoals_run(study_design_id: str, parameter_set: dict) -> str:
    """Submit a FGOALS-UFS simulation run for a study."""
    return f"Run submitted for {study_design_id} with params {parameter_set}."


# ============================================================================
# TODO: implement this middleware.
# ============================================================================
class ProtocolLockMiddleware(AgentMiddleware):
    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage],
    ) -> ToolMessage:
        # TODO (core):
        #   1) read request.tool_call -> name / args / id
        #   2) if name == "submit_fgoals_run" and its study_design_id is NOT in
        #      STORE["locked_studies"]:
        #         return a ToolMessage(content=<actionable error>, tool_call_id=<id>)
        #         WITHOUT calling handler  (this rejects the call)
        #   3) otherwise: return handler(request)   (this allows the call)
        #
        # TODO (stretch): audit logging; parameter-bounds check for
        #   propose_parameter_set / submit_fgoals_run using BOUNDS.
        raise NotImplementedError("Implement wrap_tool_call")

    # TODO (stretch): implement wrap_model_call to inject which studies are
    #   locked into the system prompt via request.override(system_message=...).
# ============================================================================


agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",   # swap to a model you can access
    tools=[lock_study_config, propose_parameter_set, submit_fgoals_run],
    middleware=[ProtocolLockMiddleware()],
    system_prompt="You are a FGOALS-UFS research assistant. Use the tools to run experiments.",
)


def _last(msgs) -> str:
    return msgs["messages"][-1].content


def _reset() -> None:
    # STORE is process-global, so each agent.invoke would otherwise inherit the
    # previous test's locks. Reset between tests so they're independent.
    STORE["locked_studies"].clear()


if __name__ == "__main__":
    print("=== Test 1: run before lock → must be REJECTED ===")
    _reset()
    # 'do NOT lock first' is essential: a capable agent would otherwise lock S-001
    # itself and the submit would legitimately pass, so you'd never see the gate fire.
    print(_last(agent.invoke({"messages": [{"role": "user",
        "content": "Submit a FGOALS run for study S-001 with params {'ccn_o': 1.2}. "
                   "Submit it directly — do NOT call lock_study_config first."}]})))

    print("\n=== Test 2: lock then run → must SUCCEED ===")
    _reset()
    print(_last(agent.invoke({"messages": [{"role": "user",
        "content": "Lock study S-001, then submit a run for it with params {'ccn_o': 1.2}."}]})))

    print("\n=== Test 3 (stretch): out-of-bounds param → should be REJECTED ===")
    _reset()
    print(_last(agent.invoke({"messages": [{"role": "user",
        "content": "For study S-001 propose a parameter set with vr_fac = 3.5."}]})))
