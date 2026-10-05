# Natural Language Workflow Generator

A small GenAI assessment project that turns a business objective into a structured workflow, validates its graph, and executes its selected path using controlled demo operations.

## Problem and solution

Business requests often include tools, data checks, decisions, and human sign-off. This project represents those instructions as a typed workflow instead of returning a prose answer. It then checks the workflow before execution and reports each step's outcome.

## Architecture

```text
Business requirement → Workflow generation → Pydantic schema → Graph/action validation
                                                              ↓
                                                       Graph executor → Results
```

- `app/llm.py` uses OpenRouter's OpenAI-compatible JSON mode when configured. Without a key it provides deterministic local demo templates, so the application can be demonstrated offline.
- `app/models.py` defines workflow and step schemas.
- `app/validator.py` checks required fields, unique IDs, supported actions, and graph references.
- `app/executor.py` follows transition edges, implements a small safe condition language, pauses for approval, routes failures, and stops loops.
- `app/tools.py` contains the action registry and predefined transformations. Generated content is never evaluated as Python.
- `app/main.py` provides the API and lightweight responsive browser UI.

## Features

- API, tool, transform, validation, condition, approval, and error-handler step types.
- `on_success` and `on_failure` graph transitions; condition and approval steps select one branch.
- Human approval pauses execution until an operator chooses Approve or Reject.
- Deterministic demo tools and safe named transforms (`multiply`, `add`, `copy`).
- Validation errors and per-step execution statuses, including pending and failed states.
- Local mode requires no API key; OpenRouter mode uses environment configuration.

## Technology

Python 3.10+, FastAPI, Pydantic v2, OpenAI-compatible SDK (OpenRouter), and plain HTML/CSS/JavaScript.

## Project structure

```text
app/
  executor.py       graph execution and safe conditions
  llm.py            OpenRouter and offline workflow generation
  main.py           FastAPI routes and browser interface
  models.py         workflow schema
  tools.py          allowlisted demo actions and transforms
  validator.py      workflow validation
  test_workflow.py  execution and validation tests
  test_llm.py       local generation test
requirements.txt
```

## Installation and run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`. Health endpoint: `GET /health`.

## Environment variables

OpenRouter is optional. Set these in your shell or a local `.env` file (never commit secrets):

```text
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

The OpenAI-compatible SDK reads the key from the process environment. Local generation works when the key is absent.

To force local deterministic templates even when a key is configured, set `WORKFLOW_GENERATION_MODE=local`.

## Example request

```text
Process a customer order. If the order amount is above 10000, ask the manager for approval. If approved, create the order. If rejected, cancel it.
```

The local order template loads and validates the order, checks the amount, and pauses at manager approval. Approving runs only `create_order`; rejecting runs only `cancel_order`.

Other local demo prompts include payment failure notification and calculating a total for a stated number of products and unit price. The generator uses deterministic demo values for execution; this is an assessment demo, not a connection to real business systems.

## API

- `GET /`: UI.
- `GET /health`: returns `{"status":"ok"}`.
- `POST /generate`: accepts `{"requirement":"..."}`, generates and validates a workflow, and runs it until completion or pending approval.
- `POST /execute`: accepts a validated workflow and optional decision map, e.g. `{"workflow":{...},"approvals":{"approval":true}}`, to continue through the chosen branch.

## Execution, validation, and errors

Execution starts at the first step and follows transition IDs. Conditions support numeric comparisons for `amount` and `total`, and equality/inequality checks for `payment_status`. Unsupported expressions fail as step errors. A visited-step set prevents cycles. Step exceptions route to `on_failure`; without a failure target, execution stops. Invalid workflows are never executed. Unknown actions are rejected by validation.

## Human approval

Approval steps return a pending result when no decision has been supplied. The UI displays Approve and Reject controls; the selected decision is sent to `/execute` and selects the matching transition. Decisions are in-memory demo input, not an identity-verified approval record.

## Data transformation

A transform step selects a named operation rather than supplying an expression. For example, `multiply` with `{"left":3,"right":500}` returns `{"value":1500}`. The result is available to later steps as `value` and `total`.

## Tests

Run the standard-library test suite from the project root:

```powershell
python -m unittest discover -s app -p "test_*.py" -v
```

## Limitations and future improvements

- Demo tools use fixed or request-provided sample data and do not call external services.
- Offline generation uses simple templates for the assessment scenarios; arbitrary requirements need a configured OpenRouter model.
- Approval state is stateless and intended for a single demo request. Production use would need persisted workflow runs, authenticated approvers, retries, and audit records.
- The supported condition language and named transformations are intentionally small and explicit.
