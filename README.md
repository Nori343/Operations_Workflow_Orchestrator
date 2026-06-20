# Customer Operations Workflow Orchestrator

LangGraph backend for customer support ticket handling. Classifies incoming messages, applies company policy, assesses risk, and generates responses using a hybrid deterministic + LLM approach.

Policy and risk decisions are rules-based and auditable. The LLM only handles ambiguous classification and response phrasing — it never approves a return or overrides policy.

## Key features

- Layered pipeline with conditional routing (skip order lookup when no order ID)
- Heuristic planner with confidence-gated LLM fallback classifier
- Deterministic policy engine with domain-specific evaluators (returns, shipping, cancellation, damaged items, missing package, FAQs)
- Risk assessment and human escalation rules
- Multiturn conversations via LangGraph checkpointing + continuation when customer supplies a missing order ID
- 27-case eval suite (single-turn and multiturn)
- Graceful degradation: template responses when no `OPENAI_API_KEY` is set

## Quickstart

Python 3.11+

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn main:app --reload
```

Single-turn:

```bash
curl -X POST http://127.0.0.1:8000/process-ticket \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "demo-1", "customer_message": "Can I return order PG-1001?"}'
```

API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Health check: `GET /health`

Debug mode — append `?debug=true` to include policy decision, risk decision, node trace, and errors in the response (for demos and troubleshooting, not needed for normal clients):

```bash
curl -X POST "http://127.0.0.1:8000/process-ticket?debug=true" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "demo-1", "customer_message": "Can I return order PG-1001?"}'
```

Copy `.env.example` to `.env` and set keys as needed:

```env
OPENAI_API_KEY=sk-...
```

## Architecture

```
Customer message
       │
       ▼
   planner ──(conditional)──► order ──► policy ──► risk ──► response
       │                         ▲
       └──── skip order ─────────┘
```

Design philosophy: each layer owns one decision type, in fixed order. Classify → (maybe fetch order) → enforce policy → flag risk → format reply.

## What I learned

- Splitting decisions across layers makes agent workflows debuggable — if a return is wrongly denied, I look at `returns_evaluator`, not the response prompt.
- Deterministic policy + LLM-as-formatter is more testable than a single prompt that classifies, decides, and replies at once.
- Checkpointing + continuation (`try_continue_ticket`) handles slot-filling (ask for order ID on turn 1, resume on turn 2) without treating every message as a brand-new ticket.
- Golden evals should assert on `decision` and `recommended_action`, not LLM response wording — phrasing can drift without breaking behavior.

## Multiturn example

Use the same `conversation_id` on each request:

```bash
# Turn 1 — asks for order ID
curl -X POST http://127.0.0.1:8000/process-ticket \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "demo-1", "customer_message": "I want to return my order."}'

# Turn 2 — continuation (planner_source: "continuation")
curl -X POST http://127.0.0.1:8000/process-ticket \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "demo-1", "customer_message": "PG-1001"}'
```

The API maps `conversation_id` to LangGraph's checkpoint `thread_id` (`conversation_id-demo-1`). Same ID = merged state across turns.

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

Order IDs for testing: `data/mock_orders.py`

## Tech stack

- LangGraph — workflow orchestration + in-memory checkpointing (`MemorySaver`)
- LangChain — message types and state reducers
- FastAPI — HTTP API
- Pydantic — schemas at API and worker boundaries
- OpenAI — optional LLM classifier fallback and response synthesis

## Evals and tests

```bash
python eval.py                              # 21 single-turn + 6 multiturn golden cases
python -m unittest tests.test_planner       # planner classification unit tests
python -m services.planner --trace "..."    # debug classification for one message
```

## How it works

Each message runs through five stages. No stage skips ahead or makes another stage's call.

1. Planner — pick domain (returns, shipping, cancellation, etc.) and intent (action vs policy question). Keyword heuristics first; LLM classifier only when confidence is below threshold (default 0.67). On reclassify, clears stale `order` from checkpoint.
2. Order lookup — fetch mock order data when an action request includes an order ID. Skipped when there is no ID yet (policy node returns `needs_more_info`).
3. Policy — run deterministic rules against structured policy JSON in `data/policy_store.py`. Returns a backend `decision` and a `recommended_action` for the response layer. Domain evaluators live in `workers/*_evaluator.py`; `handler_registry.py` selects the handler.
4. Risk — escalation rules: unsupported workflows, missing-package claims, high-value orders (default > $500).
5. Response — format policy + risk into customer copy. Uses LLM when an API key is set; otherwise templates in `services/template_response.py` keyed on `recommended_action`. On policy-intent turns, order context is omitted from the LLM prompt.

Multiturn continuation: if checkpoint has `missing_fields: ["order_id"]` and the customer sends `PG-XXXX`, `try_continue_ticket` resumes the same workflow without re-classifying.

| Component | Role |
|---|---|
| `main.py` | FastAPI entry. POST `/process-ticket`; maps `conversation_id` → LangGraph `thread_id`. |
| `graph/builder.py` | Compiles the graph, exports `workflow_app`, attaches `MemorySaver`. |
| `graph/routing.py` | Routes to order node only when `requires_order` and an order ID are present. |
| Planner node | Wrapper over `services/planner.py` (classification, continuation, stale-state cleanup). |
| Order node | Mock lookup via `workers/order_worker.py`. |
| Policy node | Dispatches to domain evaluators through `workers/handler_registry.py`. |
| Risk node | Escalation rules in `workers/risk_worker.py`. |
| Response node | `services/llm.py` or template fallback. Never overrides policy. |
| `schemas.py` | Pydantic models at boundaries. |

In production, messages would arrive from a chat UI rather than curl; the orchestrator logic is the same.

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
│   ├── mock_orders.py           # Mock orders (relative date offsets → resolved at lookup)
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

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | — | LLM classifier fallback + response synthesis |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model for LLM calls |
| `PLANNER_CONFIDENCE_THRESHOLD` | `0.67` | Below this, planner may invoke LLM classifier |
| `RISK_HIGH_VALUE_USD` | `500` | Orders above this trigger escalation |
| `MOCK_REFERENCE_DATE` | — | Optional. Freeze `YYYY-MM-DD` for stable time-based policy checks |

Without `OPENAI_API_KEY`, the planner skips LLM fallback and the response node uses templates.

## Limitations

- No chat UI — backend only. Photo upload for damaged items would come from external systems.
- `MemorySaver` checkpointing is in-memory; conversations reset on server restart. Production would use a persistent checkpointer and a real customer/order store.
- Orders and policies are mock dicts and local files, not live APIs.
- API exposes `conversation_id` only; production might add a per-request `request_id` for logging.
