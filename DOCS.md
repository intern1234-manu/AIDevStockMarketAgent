# MATS v2 — Multi-Agent Autonomous Trading System
## Complete Build & Architecture Document

**Broker:** Interactive Brokers (IBKR) via `ib_async`
**Strategy:** Swing (days–weeks) + Position (weeks–months)
**Data:** Free-tier only — yfinance, NewsAPI (free), VADER sentiment
**Autonomy:** Fully autonomous execution — no human confirmation step
**Orchestration:** LangGraph stateful graph

---

## 1. What This System Does

Five agents collaborate on every trading decision:

```
MARKET TICK / SCHEDULE
        │
        ▼
  DATA INGESTION ──── freezes one market snapshot shared by all agents
        │
   ┌────┴────┐
   ▼         ▼         ▼
FUNDAMENTAL  TECHNICAL  RISK/SENTIMENT
  AGENT       AGENT       AGENT
   └────┬─────┘
        │  (all three positions visible to all three — round-robin council)
        ▼
  DEBATE CONTROLLER (max 3 rounds, capped challenges)
        │
        ▼
  MASTER AGENT (adjudicates, runs tie-break, applies veto hierarchy)
        │
   ┌────┴────┐
   ▼         ▼
NO-TRADE   APPROVED ──► EXECUTION AGENT ──► IBKR bracket order
   │                           │
   └─────────► REPORT ◄────────┘
                   │
                   ▼
            SELF-ANALYSIS (journal → weekly review → correlation monitor)
```

**Key properties:**
- Every numeric claim an agent makes must resolve to a real data source — no LLM-hallucinated metrics
- Risk veto is deterministic code, not a vote — it cannot be outvoted
- Entry and stop-loss submitted as a single bracket order — a filled entry with no stop is the worst failure state
- Three agents use three different model providers — prevents stylistic agreement masquerading as independent analysis
- System trades autonomously once conditions clear all gates

---

## 2. Free Data Sources

| Provider | What it covers | Rate limit | How we use it |
|---|---|---|---|
| **yfinance** | OHLCV, fundamentals, earnings dates, balance sheet | No hard limit (unofficial Yahoo API) | Primary price + fundamental data |
| **NewsAPI** (free tier) | 100 req/day, 30-day history | 100 req/day | News headlines for sentiment |
| **VADER** (NLTK) | Sentiment scoring | Local, unlimited | Score news headlines |
| **IBKR** (your account) | Live quotes, order execution, portfolio state | Per IBKR TWS rules | Live prices, bracket orders |

**Important:** yfinance is an unofficial wrapper around Yahoo Finance — it works reliably for EOD/daily data and is widely used, but it is not an official API and could break without notice. For production stability, budget $30–50/month for Polygon.io (free tier also exists) as a backup.

---

## 3. Project Structure

```
mats_v2/
├── DOCS.md                         ← this file
├── .env.example
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
│
├── config/
│   ├── settings.py                 # env loading — fails loudly at boot
│   ├── risk_limits.yaml            # ALL deterministic limits live here
│   ├── circuit_breakers.yaml       # automated halt thresholds
│   ├── models.yaml                 # per-role model assignment
│   └── watchlist.txt               # tickers to scan
│
├── src/mats/
│   ├── state.py                    # TradeDeliberationState — one object, append-only
│   ├── graph.py                    # LangGraph wiring
│   ├── main.py                     # entrypoint + fail-fast boot validation
│   │
│   ├── data/
│   │   ├── snapshot.py             # frozen market snapshot (shared by all agents)
│   │   ├── yfinance_feed.py        # OHLCV, fundamentals, earnings dates
│   │   ├── news_feed.py            # NewsAPI + VADER sentiment
│   │   └── source_ref.py           # claim validation — no unverified numeric claims
│   │
│   ├── agents/
│   │   ├── base.py                 # shared: retry, schema validation, LLM caller
│   │   ├── fundamental.py          # P/E, earnings, macro, guidance
│   │   ├── technical.py            # price action, indicators, volume
│   │   ├── risk_sentiment.py       # news sentiment + hard risk constraints
│   │   ├── master.py               # adjudication + tie-break logic
│   │   └── execution.py            # IBKR bracket order submission
│   │
│   ├── council/
│   │   ├── protocol.py             # any-to-any challenge, 2/round cap
│   │   └── synthesis.py            # human-readable round summary
│   │
│   ├── gates/
│   │   ├── risk_veto.py            # DETERMINISTIC — no LLM. Veto before vote.
│   │   ├── circuit_breakers.py     # automated halt conditions
│   │   └── model_diversity.py      # boot-time: enforce distinct models
│   │
│   ├── broker/
│   │   ├── ibkr_client.py          # ib_async wrapper
│   │   ├── bracket.py              # atomic entry + stop-loss (OCO)
│   │   └── idempotency.py          # prevent double-submit under retry
│   │
│   ├── reflection/
│   │   ├── decision_journal.py     # links decision → market outcome
│   │   ├── performance_review.py   # weekly self-critique (RECOMMENDS only)
│   │   └── correlation_monitor.py  # tracks agent independence over time
│   │
│   ├── persistence/
│   │   ├── checkpointer.py         # LangGraph PostgresSaver
│   │   └── ledger.py               # append-only execution ledger
│   │
│   ├── observability/
│   │   ├── logging.py              # structured JSON via structlog
│   │   ├── metrics.py              # Prometheus counters
│   │   └── health.py               # liveness = last_successful_tick_at
│   │
│   └── scheduler/
│       └── runner.py               # APScheduler — fires against IBKR clock
│
├── tests/
│   ├── unit/
│   │   ├── test_risk_veto.py       # 100% branch — highest priority
│   │   ├── test_circuit_breakers.py
│   │   ├── test_council_protocol.py
│   │   ├── test_tie_break.py
│   │   └── test_bracket_recovery.py
│   └── integration/
│       └── test_paper_flow.py      # full graph, IBKR paper
│
└── scripts/
    ├── explain_last_n.py           # "why did it decide that?"
    ├── gate_report.py              # "what's blocking trades?"
    ├── check_clock.py              # is the market open?
    ├── broker_smoke.py             # IBKR connectivity check
    └── correlation_report.py       # agent independence over time
```

---

## 4. Build Sequence

Build in this exact order. Each stage is independently testable. Do NOT skip to stage 4 before stage 2 is green — a working execution path with untested risk gates is how a bug becomes a financial loss.

### Stage 0 — Resolve before touching code

Answer these before writing a line:

| Question | Why it matters |
|---|---|
| What is the max drawdown you'll accept before the system halts? | Sets `circuit_breakers.yaml: intraday_drawdown_pct` |
| What is the max allocation per position (% of portfolio)? | Sets `risk_limits.yaml: max_position_size_pct_portfolio` |
| How many days before earnings is a blackout? | Sets `risk_limits.yaml: blackout_days_before_earnings` |
| What tickers will you scan? | Populate `config/watchlist.txt` |
| Do you have IBKR TWS or IB Gateway running? | `ib_async` requires one to be running and configured for API access |

### Stage 1 — Environment and infrastructure

```bash
# 1. Clone / initialise
git init mats_v2 && cd mats_v2
python -m venv .venv && source .venv/bin/activate

# 2. Install
pip install -e ".[dev]"

# 3. Infrastructure
docker compose up -d postgres redis

# 4. Database
alembic upgrade head

# 5. Verify
python -m mats.main --check-env
```

### Stage 2 — Deterministic gates first (before any LLM wiring)

These are the components that stop a bug from becoming a position loss. Write and test them with zero LLM involvement.

```bash
pytest tests/unit/test_risk_veto.py -v --cov=mats.gates.risk_veto --cov-fail-under=100
pytest tests/unit/test_circuit_breakers.py -v --cov-fail-under=100
pytest tests/unit/test_bracket_recovery.py -v --cov-fail-under=95
```

Do not advance until these are all green with ≥95% branch coverage.

### Stage 3 — Data layer

Wire yfinance + NewsAPI + VADER. Verify `source_ref` resolution works for every claim type before connecting any LLM. If `source_ref` validation is broken, every agent output gets rejected and you'll debug the wrong layer.

```bash
python -m mats.data.snapshot --ticker AAPL --dry-run
```

### Stage 4 — Real agents (stub graph already passing)

Replace stubs with real LLM calls. Every agent output is schema-validated with retry. Log raw payloads on parse failure — an LLM returning markdown instead of JSON is a common first failure.

### Stage 5 — Paper trading (IBKR paper account)

Wire IBKR in paper mode. The system executes autonomously in paper from this point. Validate:
- Bracket orders submit and both legs confirm
- Stop-loss fires on adverse move
- Journal entries link to outcomes
- Circuit breakers trip and alert

```bash
TRADING_MODE=paper python -m mats.main --ticker AAPL --single-session
```

### Stage 6 — Shadow mode (live data, no orders)

Run the full graph against live market data without submitting orders. This is how you calibrate circuit breaker thresholds and observe agent correlation — neither can be done without live market data.

```bash
TRADING_MODE=shadow python -m mats.main
```

Run shadow for at minimum 4 weeks, spanning at least one earnings cycle for names on your watchlist.

### Stage 7 — Live (autonomous)

After shadow mode produces a track record you're satisfied with, switch:

```bash
TRADING_MODE=live python -m mats.main
```

The system executes without confirmation. The circuit breakers and risk veto are your safety net — calibrate them in stage 6, not stage 7.

---

## 5. IBKR Setup

```
TWS or IB Gateway must be running and have API access enabled:
  TWS: Edit → Global Configuration → API → Settings
    ✓ Enable ActiveX and Socket Clients
    ✓ Socket port: 7497 (paper) or 7496 (live)
    ✓ Allow connections from localhost
    ✗ Read-only API: OFF (must be off for orders)

IB Gateway (headless, preferred for production):
  Port: 4002 (paper) or 4001 (live)
```

**IBKR-specific failure modes to know:**
- Orders submitted outside RTH are rejected by default — enable extended hours per order if needed
- `reqAccountSummary` is rate-limited; cache portfolio state, do not poll it per tick
- Paper and live accounts use different ports and different API keys — verify `IBKR_PORT` in `.env` matches your running instance
- `ib_async` reconnects automatically, but your graph must handle the brief gap — `StateGraph` checkpointing handles this

---

## 6. Autonomous Execution Design

**No human confirmation gate** means the risk veto and circuit breakers must be correctly configured before going live. This is the checklist:

```
□ risk_limits.yaml populated with your actual limits (not the example values)
□ circuit_breakers.yaml intraday_drawdown_pct set to your real pain threshold
□ config/watchlist.txt contains only tickers you have researched
□ TRADING_MODE=paper passed at least 2 weeks without unexpected behaviour
□ TRADING_MODE=shadow run for at least 4 weeks
□ tests/unit/ all green with ≥95% branch coverage
□ Bracket order tested: entry fills → adverse move → stop triggers (paper)
□ IBKR port confirmed correct for account type (paper vs live)
□ Alert channel configured (email/Telegram) for circuit breaker trips
```

**Why the risk veto is deterministic code, not an agent vote:**
A 2-1 agent majority should not be able to override a hard limit breach (position too large, no stop available, ticker on restricted list, earnings blackout). These are compliance facts, not analytical opinions. The gate runs before the vote tally and cannot be overridden by consensus.

---

## 7. Self-Analysis Loop

The system reviews its own decisions — not to auto-tune parameters, but to surface patterns for your review.

**Decision journal** (written every session):
```json
{
  "session_id": "...",
  "ticker": "AAPL",
  "decided_at": "2026-09-21T14:30:00Z",
  "decision": "BUY_REDUCED_SIZE",
  "decision_basis": "MAJORITY",
  "agent_positions": {"fundamental": "HOLD", "technical": "BUY", "risk": "BUY_REDUCED_SIZE"},
  "round_synthesis": ["Round 1: Technical challenged Fundamental on valuation framing; Fundamental defended."],
  "entry_price": 223.45,
  "outcome": {
    "evaluated_at": "2026-09-28T20:00:00Z",
    "exit_price": 229.10,
    "pnl_pct": 2.53,
    "thesis_held": true
  }
}
```

**Weekly performance review** — answers:
- Which agent's initial read best predicted outcome, by decision type?
- Did the council talk anyone out of a correct position (concession quality)?
- Any tickers/sectors where system is systematically wrong?
- Which `decision_basis` paths produce the worst risk-adjusted results?

**NEVER auto-writes to `risk_limits.yaml`.** A system that retunes its own risk parameters from a short track record will overfit into a drawdown. The review recommends; you decide.

**Correlation monitor** — tracks agent independence:
- Pairwise initial-position agreement rate
- Confidence correlation across sessions
- Rebuttal win-rate asymmetry (one role always "winning" = persuasiveness, not truth)

Alert threshold: >85% agreement between any pair over 50+ sessions = degraded diversity.

---

## 8. Free API Keys Setup

### NewsAPI (free tier)
1. Register at https://newsapi.org/register
2. Free: 100 requests/day, past 30 days
3. Set `NEWS_API_KEY=<your_key>` in `.env`
4. At 100 req/day with a ~20-ticker watchlist, budget 5 calls/ticker/day max

### yfinance
No API key required. Installs as a Python package. Unofficial Yahoo Finance API — works reliably for EOD data, occasionally unstable for intraday. Cache aggressively.

### VADER Sentiment
```bash
python -c "import nltk; nltk.download('vader_lexicon')"
```
Local, unlimited. No key, no rate limits. Less accurate than a fine-tuned financial model but sufficient for signal filtering.

### IBKR
- Paper account: free, create at interactivebrokers.com
- Live account: requires account funding
- No separate API key — authentication is through TWS/IB Gateway running on your machine

---

## 9. Environment Variables

```bash
# ── Trading mode ──────────────────────────────────────────────────
TRADING_MODE=paper              # paper | shadow | live

# ── IBKR ──────────────────────────────────────────────────────────
IBKR_HOST=127.0.0.1
IBKR_PORT=7497                  # 7497=TWS paper | 7496=TWS live
                                # 4002=Gateway paper | 4001=Gateway live
IBKR_CLIENT_ID=1                # unique int per connection

# ── Models (MUST be distinct providers for 3 analyst roles) ───────
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=

# ── Free data ─────────────────────────────────────────────────────
NEWS_API_KEY=                   # newsapi.org free tier

# ── Infrastructure ────────────────────────────────────────────────
DATABASE_URL=postgresql://mats:mats@localhost:5432/mats
REDIS_URL=redis://localhost:6379/0
TZ=America/New_York             # CRITICAL: schedule off US market time
LOG_LEVEL=INFO
METRICS_PORT=9090

# ── Alerts ────────────────────────────────────────────────────────
ALERT_EMAIL=                    # receives circuit breaker trips
ALERT_TELEGRAM_TOKEN=           # optional
ALERT_TELEGRAM_CHAT_ID=         # optional
```

---

## 10. Model Heterogeneity (Critical)

Three analyst agents must run on three **different** foundation model providers. If they share a provider, their "disagreement" is stylistic noise, not independent analysis — and the risk reduction you expect from three-way debate is much weaker than it appears.

`config/models.yaml`:
```yaml
roles:
  fundamental:    {provider: anthropic, model: claude-sonnet-4-6}
  technical:      {provider: openai,    model: gpt-4o}
  risk_sentiment: {provider: google,    model: gemini-1.5-pro}
  master:         {provider: anthropic, model: claude-opus-4-1}
enforce_distinct: true
```

The system checks this at boot and refuses to start if two analyst roles share a provider.

---

## 11. Operational Runbook

### Normal operation
```bash
docker compose up -d
docker compose logs -f app | grep heartbeat   # should fire every scheduled tick
```

### "It's running but not trading"
```bash
python -m mats.scripts.explain_last_n --sessions 20   # see decision_basis
python -m mats.scripts.gate_report --window 7d         # what's the veto hitting?
```
Most "not trading" is the risk gate correctly rejecting proposals. Check your `risk_limits.yaml` values — if `min_confidence_to_trade` is 0.80+, agents rarely clear it.

### "It traded when it shouldn't have / wrong size"
```bash
# Replay the session state from checkpoint
python -m mats.scripts.replay_session --session-id <uuid>
```

### Circuit breaker tripped
System halts new entries automatically. Existing stop-loss orders stay live.
1. Check `ALERT_EMAIL` for the trigger reason
2. `python -m mats.scripts.gate_report` to see state
3. Manually clear in the DB after investigating: `UPDATE circuit_breaker_state SET tripped=false`

### Weekly self-analysis
```bash
python -m mats.reflection.performance_review --window 7d --output report.json
python -m mats.reflection.correlation_monitor --report
```
Review the output. If any pair shows >85% initial agreement, revisit the model/prompt assignment for those roles.

---

## 12. Known Limitations

- **yfinance is unofficial.** It will occasionally fail or return bad data. The `source_ref` validation layer rejects numeric claims that don't resolve — so agents fall back to HOLD rather than hallucinating — but persistent feed failures will cause the system to mostly not trade. Monitor `source_ref_resolution_failures` in Prometheus.
- **NewsAPI free tier is 100 req/day.** On a 20+ ticker watchlist at daily frequency, budget 5 req/ticker/day. The news feed batches by query term to stay within limits.
- **VADER is not a financial-grade sentiment model.** It scores general English sentiment, not financial nuance. "Earnings beat" scores positively; "beat by a small margin amid concerns" may not score as differently as a financial model would. Treat it as a noise filter, not a signal generator.
- **LLM confidence scores are not calibrated.** The tie-break uses confidence weighting, but self-reported LLM confidence correlates imperfectly with actual accuracy. High-confidence wrong calls happen. The circuit breakers and risk veto are the real safety net, not the agents' self-reported certainty.
- **Swing + position holding both active.** The system needs a field in `TradeDeliberationState` to distinguish the intended hold horizon per trade — otherwise the risk gate applies the same stop-loss width to a 3-day swing and a 3-month position, which is inappropriate. This is configurable per session in `config/risk_limits.yaml` by strategy type.
