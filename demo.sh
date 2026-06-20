#!/usr/bin/env bash
# Customer Ops Workflow Orchestrator — live demo helper
#
# You do NOT need to memorize curl. Run this script instead.
#
# Before demo (two terminals):
#   Terminal 1:  uvicorn main:app --reload
#   Terminal 2:  ./demo.sh          (full demo)
#                ./demo.sh api       (curl examples only)
#                ./demo.sh multiturn (two-turn thread only)
#                ./demo.sh eval      (golden tests, no server needed)
#
# Swagger UI (click "Try it out" if you prefer GUI): http://127.0.0.1:8000/docs
#
# 5-minute talk track:
#   1. Problem — support tickets need classify → lookup → policy → risk → reply, not one LLM call.
#   2. POST /process-ticket — planner picks workflow; order node fetches mock order; policy is deterministic rules.
#   3. Show return approved (PG-1001) — decision in debug, customer-facing response in response.
#   4. Same conversation_id across turns — turn 1 asks for order ID, turn 2 "PG-1001" continues via checkpoint.
#   5. python eval.py — 27 cases assert decision/recommended_action, not LLM wording.

set -euo pipefail

BASE="${BASE_URL:-http://127.0.0.1:8000}"
ROOT="$(cd "$(dirname "$0")" && pwd)"

pretty() {
  if command -v jq >/dev/null 2>&1; then
    jq .
  else
    cat
  fi
}

banner() {
  echo
  echo "============================================================"
  echo " $1"
  echo "============================================================"
  echo
}

need_server() {
  if ! curl -sf "${BASE}/health" >/dev/null; then
    echo "Server not reachable at ${BASE}"
    echo "Start it first:  uvicorn main:app --reload"
    exit 1
  fi
}

post_ticket() {
  local conv_id="$1"
  local message="$2"
  local debug="${3:-false}"
  local url="${BASE}/process-ticket"
  if [[ "$debug" == "true" ]]; then
    url="${url}?debug=true"
  fi
  curl -s -X POST "$url" \
    -H "Content-Type: application/json" \
    -d "{\"conversation_id\":\"${conv_id}\",\"customer_message\":$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$message")}" \
    | pretty
}

run_health() {
  banner "GET /health"
  curl -s "${BASE}/health" | pretty
}

run_api() {
  need_server

  banner "1. Return approved — order in message (PG-1001)"
  echo "Look at: workflow_type, response, debug.policy_decision.decision"
  post_ticket "demo-return-1" "Can I return order PG-1001?" true

  banner "2. Shipping status — where is PG-1002?"
  post_ticket "demo-shipping-1" "Where is order PG-1002?" true

  banner "3. Policy question — no order needed"
  post_ticket "demo-policy-1" "What is your return policy?" true
}

run_multiturn() {
  need_server
  local conv="demo-multiturn-1"

  banner "Multiturn — same conversation_id on both requests"
  echo "Turn 1: customer has no order ID yet → missing_fields should include order_id"
  post_ticket "$conv" "I want to return my order." true

  echo
  echo "--- press Enter for turn 2 ---"
  read -r _

  echo "Turn 2: PG-1001 → planner_source should be continuation, return approved"
  post_ticket "$conv" "PG-1001" true
}

run_eval() {
  banner "Golden evals (no API server required)"
  cd "$ROOT"
  python eval.py
}

run_all() {
  run_health
  run_api
  run_multiturn
  banner "Eval suite"
  run_eval
}

case "${1:-all}" in
  health) run_health ;;
  api) run_api ;;
  multiturn) run_multiturn ;;
  eval) run_eval ;;
  all) run_all ;;
  *)
    echo "Usage: $0 [all|health|api|multiturn|eval]"
    exit 1
    ;;
esac
