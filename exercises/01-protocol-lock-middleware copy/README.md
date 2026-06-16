# Exercise 01 — Protocol-Lock gatekeeper middleware

A small, gradable task to test whether someone can **write a DeepAgent `AgentMiddleware`** —
the exact extension mechanism HAEEM uses. Related to our real gatekeeper; small enough for an
afternoon.

- **`exercise.py`** — scaffold with the middleware left as `TODO` (give this to the student).
- **`solution.py`** — reference answer (kept out of the public repo via `.gitignore`).

## Background (1 minute)

HAEEM constrains an agent's research workflow by **attaching one middleware to DeepAgent** — without
forking DeepAgent. Its most important rule: **no FGOALS run may be submitted before the study config
is locked (protocol lock).** You will implement the minimal version of that rule.

This tests whether you can use `AgentMiddleware.wrap_tool_call` to intercept a tool call *before* it
runs, decide **allow vs. reject** based on state, and return a model-friendly error so the agent
self-corrects. Full background: [../../docs/deepagent_integration.md](../../docs/deepagent_integration.md).

## What you're given (`exercise.py`)

- A shared in-memory `STORE` (a fake DB): tools **write** it, your gatekeeper **reads** it — mirroring
  real HAEEM (tools persist to Supabase; the gatekeeper reads core/DB state).
- Three tools: `lock_study_config`, `propose_parameter_set`, `submit_fgoals_run`.
- A wired `create_deep_agent(...)` with your middleware attached.
- A `__main__` with three test prompts.

## Your task

Implement `ProtocolLockMiddleware.wrap_tool_call` so that:

1. `submit_fgoals_run` for a study that is **not** in `STORE["locked_studies"]` is **rejected** —
   return a `ToolMessage` **without** calling `handler`, telling the model to `lock_study_config` first.
2. Anything else passes through via `handler(request)`.

## Must-pass acceptance criteria (core)

1. **Test 1** — submit before lock → blocked; nothing is actually submitted; the returned message tells
   the model to lock first.
2. **Test 2** — lock `S-001`, then submit for `S-001` → succeeds.
3. Rejection works by **returning `ToolMessage` and not calling `handler`**; pass-through uses `handler(request)`.
4. Unrelated tools (e.g. `lock_study_config`) are **never** blocked.
5. The returned `ToolMessage` uses `tool_call_id=request.tool_call["id"]`.

## Stretch goals (reveal the ceiling)

- **Audit**: in the same `wrap_tool_call`, append every call (name + allow/reject) to `audit.jsonl`.
- **Parameter bounds**: reject `propose_parameter_set` / `submit_fgoals_run` when a value is out of
  range (e.g. `vr_fac ∈ [0.5, 2.0]` — the HAEEM default subset, see
  [../../docs/decisions/ADR-0004-fgoals-asset-formalization.md](../../docs/decisions/ADR-0004-fgoals-asset-formalization.md)).
- **State injection**: implement `wrap_model_call` to inject "which studies are locked" into the system
  prompt via `request.override(system_message=...)`.

## Grading rubric

| Dimension | What to look for |
|---|---|
| Hook signature | Correct `wrap_tool_call(self, request, handler)`; reads `name/args/id` from `request.tool_call`. |
| Short-circuit vs pass-through | Understands reject = return `ToolMessage` (no `handler`); allow = `handler(request)`. |
| `tool_call_id` | Returned message uses `request.tool_call["id"]`. |
| No collateral damage | Only the targeted tool is gated; others pass through. |
| Error quality | Rejection message is **actionable** (says what to do next), not just "blocked". |
| State source | Gatekeeper reads shared state (`STORE`), doesn't guess. |

## Setup & run (uv)

This folder is a self-contained `uv` project (`pyproject.toml` + `uv.lock`).

```bash
cd exercises/01-protocol-lock-middleware
uv sync                          # creates .venv and installs deepagents + langchain from the lockfile
cp .env.example .env             # then edit .env and set ANTHROPIC_API_KEY=...
uv run python exercise.py
```

The scripts load this folder's `.env` automatically (via `python-dotenv`) — no manual `export`
needed. `.env` is git-ignored; only `.env.example` is committed.

> **Colon-path caveat:** if your checkout path contains a `:` (colon) — as this repo's folder name does —
> `uv run` fails with `path segment contains separator ':'`. Run the interpreter directly instead:
> ```bash
> uv sync && ./.venv/bin/python exercise.py
> ```

Verified resolved versions: `deepagents 0.6.10`, `langchain 1.2`, `langchain-core 1.2`, `langgraph 1.0`,
`langchain-anthropic 0.3.22`. The exact import paths in the scaffold (`ToolCallRequest`, `request.override`,
`AgentMiddleware`) are valid in these versions; if you bump versions and imports break, check
`uv pip show deepagents langchain` and adjust — that's part of the test.

## Reference output

A passing run of the **reference solution** (all stretch goals on) looks like the below. **Your exact
wording will differ** — the prose is the *model's* output and is non-deterministic. Judge correctness by
the **decisions**, not the phrasing (see "what to compare" after the block).

```text
=== Test 1: run before lock → must be REJECTED ===
The submission was rejected by the system — Study `S-001` is not locked. Confirmatory runs
require a locked protocol. Would you like me to lock `S-001` first and then resubmit?

=== Test 2: lock then run → must SUCCEED ===
Done. Study S-001 is locked and the confirmatory run with `ccn_o = 1.2` has been submitted.

=== Test 3: out-of-bounds param → must be REJECTED ===
The proposal was rejected: `vr_fac = 3.5` falls outside the allowed range [0.5, 2.0] for S-001.
Options: (1) clamp to vr_fac = 2.0 and resubmit, or (2) choose a different value within [0.5, 2.0].

Audit trail written to .../audit.jsonl
```

**Deterministic vs. model-generated — know the boundary.** The friendly prose above (the bulleted
"Options", the bold, the follow-up question) is **the model rephrasing**, not your middleware. Your
middleware only emits a structured `ToolMessage`, e.g. for Test 3:

```json
{"ok": false, "error_code": "PARAMETER_OUT_OF_BOUNDS",
 "message": "Parameter vr_fac=3.5 is outside the locked range [0.5, 2.0].",
 "required_action": "clamp vr_fac into [0.5, 2.0] and retry"}
```

The model reads that JSON and writes the user-facing sentence. You control the *signal*
(`message` / `required_action`); the model controls the *wording*. If you need fixed wording, enforce
it outside the agent, not via `required_action`.

**What to compare (the deterministic ground truth) — `audit.jsonl`.** Regardless of phrasing, a correct
solution must produce exactly these four decisions, in order:

```json
{"tool": "submit_fgoals_run",   "args": {"study_design_id": "S-001", ...}, "decision": "reject", "detail": "protocol not locked"}
{"tool": "lock_study_config",   "args": {"study_design_id": "S-001"},      "decision": "allow"}
{"tool": "submit_fgoals_run",   "args": {"study_design_id": "S-001", ...}, "decision": "allow"}
{"tool": "propose_parameter_set","args": {"study_design_id": "S-001", "parameters": {"vr_fac": 3.5}}, "decision": "reject", "detail": "vr_fac=3.5 out of [0.5,2.0]"}
```

Note line 1: the Test-1 reject has **no preceding `lock_study_config`** — the gate fired on a genuinely
unlocked submit. If you instead see a `lock_study_config` *allow* before the first submit, your agent
locked the study itself and the gate was never exercised (fix: tell Test 1 to submit *without* locking,
and don't pre-instruct "lock first" in `wrap_model_call`).

## Deliverable

`exercise.py` with the middleware filled in, screenshots of the three tests, and 3–5 sentences
explaining how reject vs. allow happen. **Estimated time: 2–4 hours.**
