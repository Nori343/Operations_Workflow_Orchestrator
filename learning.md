# Learning notes

Personal notes on how this project works — not required reading for running the app.

## Planner confidence — intuitive mental model

Don't memorize the formula. Ask three questions:

1. **Did any domain match?** No → **0.0**
2. **Did only one domain match?** Yes → **0.67** (1 hit) or **1.0** (2+ hits)
3. **Did multiple domains match?** → How far ahead is the winner?
   - Barely ahead (2 vs 1) → ~**0.33** → **LLM**
   - Solid lead (3 vs 1) → ~**0.67** → **no LLM**
   - Exact tie → **0.0** → tiebreak → boosted to **0.67** → **no LLM**

### When LLM backup fires

| Situation | Confidence | LLM? |
|-----------|------------|------|
| No keyword hits (unsupported / paraphrase) | 0.0 | Yes |
| Weak winner, not tied (e.g. 2 vs 1 hits) | ~0.33 | Yes |
| Tie resolved by `DOMAIN_PRIORITY` | 0.0 raw, floored to 0.67 | No |
| Clear single-domain hit | ≥ 0.67 | No |

Gate: `confidence < planner_confidence_threshold` (default **0.67**). Tiebreak boosts confidence to threshold so LLM is skipped. Check `planner_source` — `"llm"` means backup ran.

Debug: `python -m services.planner --trace "your message"`
