# Customer Operations Workflow Orchestrator

LangGraph backend for customer support: classify a message, apply company policy, flag risk, and return a reply. Heuristics and rules handle routing and decisions; the LLM only steps in for ambiguous classification or to polish the final wording.

## Overview

Each message moves through a fixed pipeline. No node skips ahead or makes another node's call:

1. **Planner** — pick domain (returns, shipping, cancellation, etc.) and intent (action vs general policy question). Heuristic keywords first; LLM classifier only when confidence is low.
2. **Order lookup** — fetch mock order data when an action request includes an order ID. Skipped when there's no ID yet.
3. **Policy** — run deterministic rules against structured policy JSON. Output is a backend `decision` plus a `recommended_action` for the response layer.
4. **Risk** — check whether a human needs to review (high-value orders, missing-package claims, unsupported workflows).
5. **Response** — turn policy + risk output into customer copy. LLM if `OPENAI_API_KEY` is set; otherwise canned templates keyed on `recommended_action` in `services/template_response.py`.

That split is intentional: policy and risk are testable and stable; only phrasing varies.

Multiturn works through LangGraph checkpointing. The client sends the same `conversation_id` on each request; the API maps it to a checkpoint `thread_id` (`conversation_id-demo-1`). Turn 1 might leave `missing_fields: ["order_id"]`; turn 2 with `PG-1001` hits `try_continue_ticket`, which resumes the same workflow without re-classifying — `planner_source: "continuation"`.

The eval suite (`python eval.py`) covers 21 single-turn and 6 multiturn flows so graph behavior stays assertable even when response wording drifts.

## Architecture

```
Customer message
       │
       ▼
   planner ──(conditional)──► order ──► policy ──► risk ──► response
       │                         ▲
       └──── skip order ─────────┘
```

| Component | Role |
|---|---|
| `main.py` | FastAPI entry point. POST `/process-ticket`; maps `conversation_id` → LangGraph `thread_id`. |
| `graph/builder.py` | Compiles the graph, exports `workflow_app`, attaches `MemorySaver` for in-process checkpointing. |
| `graph/routing.py` | Routes to order node only when `requires_order` and an order ID are present. |
| Planner node | Thin wrapper over `services/planner.py` (classification, continuation, stale-state cleanup on reclassify). |
| Order node | Mock lookup via `workers/order_worker.py`. |
| Policy node | Dispatches to domain evaluators through `workers/handler_registry.py`. |
| Risk node | Escalation rules in `workers/risk_worker.py`. |
| Response node | Calls `services/llm.py` or falls back to templates. Never overrides policy. |
| `schemas.py` | Pydantic models at API and worker boundaries. |

In production, messages would come from a chat UI rather than curl; the orchestrator logic is the same.

## Project structure

```
Customer Operations Workflow Orchestrator/
├── main.py                      # FastAPI app + /process-ticket endpoint
├── eval.py                      # Golden eval suite (single + multiturn)
├── schemas.py                   # Pydantic models (SupportTicket, PolicyDecision, etc.)
├── requirements.txt
├── learning.md                  # Personal architecture notes
│
├── config/
│   └── settings.py              # Env-based config (LLM, planner threshold, risk)
│
├── graph/
│   ├── builder.py               # StateGraph compile + MemorySaver checkpointing
│   └── routing.py               # Conditional edge after planner
│
├── nodes/                       # Thin LangGraph node wrappers
│   ├── planner.py
│   ├── order.py
│   ├── policy.py
│   ├── risk.py
│   └── response.py
│
├── services/
│   ├── planner.py               # Heuristic classification, continuation, LLM fallback gate
│   ├── llm.py                   # LLM classifier + response synthesis
│   └── template_response.py     # Deterministic templates when no API key
│
├── workers/
│   ├── handler_registry.py      # Maps workflow_type → evaluator
│   ├── policy_worker.py         # Dispatches to domain evaluators
│   ├── order_worker.py          # Mock order lookup
│   ├── risk_worker.py           # Escalation rules
│   ├── returns_evaluator.py
│   ├── shipping_evaluator.py
│   ├── cancellation_evaluator.py
│   ├── damaged_evaluator.py
│   ├── missing_package_evaluator.py
│   └── policy_evaluator.py      # General policy questions (no order)
│
├── state/
│   └── workflow_state.py        # LangGraph TypedDict state + reducers
│
├── data/
│   ├── mock_orders.py           # Simulated order records (PG-1001, etc.)
│   ├── policy_store.py          # Structured policy rules (JSON)
│   ├── returns_policy.md
│   ├── shipping_policy.md
│   ├── cancellation_policy.md
│   ├── damaged_items.md
│   ├── missing_package_policy.md
│   ├── general_faqs.md
│   ├── product_catalog.md
│   └── warranty_policy.md
│
└── tests/
    └── test_planner.py          # Unit tests for classification + confidence logic
```

## Setup

Python 3.11+

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Environment variables (all optional — without `OPENAI_API_KEY`, the planner skips LLM fallback and the response node uses templates):

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | — | LLM classifier fallback + response synthesis |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model for LLM calls |
| `PLANNER_CONFIDENCE_THRESHOLD` | `0.67` | Below this, planner may invoke LLM classifier |
| `RISK_HIGH_VALUE_USD` | `500` | Orders above this trigger escalation |

```env
OPENAI_API_KEY=sk-...
```

## Run the API

```bash
uvicorn main:app --reload
```

Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Single-turn:

```bash
curl -X POST http://127.0.0.1:8000/process-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "demo-1",
    "customer_message": "Can I return order PG-1001?"
  }'
```

Multiturn — same `conversation_id` both times:

```bash
# Turn 1 — asks for order ID
curl -X POST http://127.0.0.1:8000/process-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "demo-1",
    "customer_message": "I want to return my order."
  }'

# Turn 2 — continuation (planner_source: "continuation")
curl -X POST http://127.0.0.1:8000/process-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "demo-1",
    "customer_message": "PG-1001"
  }'
```

Example turn-2 response:

```json
{
  "conversation_id": "demo-1",
  "response": "...",
  "missing_fields": [],
  "order_id": "PG-1001",
  "escalation_required": false,
  "workflow_type": "returns_request",
  "planner_source": "continuation"
}
```

Order IDs for testing: see `data/mock_orders.py`.

## Evals and tests

```bash
python eval.py                              # 21 single-turn + 6 multiturn golden cases
python -m unittest tests.test_planner       # planner classification unit tests
python -m services.planner --trace "..."    # debug a single message
```

## Limitations

- No chat UI — backend only. Photo upload for damaged items and similar signals would come from other systems.
- `MemorySaver` checkpointing is in-memory; conversations reset on server restart. Production would use a persistent checkpointer and a real customer/order store.
- Orders and policies are mock dicts and local files, not live APIs.
- API exposes `conversation_id` only; a production system might add a per-request `request_id` for logging.
