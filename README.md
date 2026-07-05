# DashWise AI — BI Dashboard FinOps & Usage Audit

An agent-based system that audits BI dashboards on three axes — **SQL quality**,
**warehouse compute cost (₹)**, and **actual usage** — and produces a per-chart
verdict (**remove / optimize / monitor / keep**) with an estimated ₹ savings
figure. Ships with a Python package + CLI, a real unit-test suite, a deployable
Vite + React console, and a one-command Docker demo.

> **Honest scope:** this is a scoped, working proof-of-concept on **synthetic
> data**, not a production BI integration. The analysis *logic* (SQL parsing,
> cost model, decision engine) is real and runnable; the dashboards it analyzes
> are generated. See [What's real vs synthetic](#whats-real-vs-synthetic).

<!-- Replace OWNER/REPO after pushing to GitHub to activate the badge. -->
![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)

---

## What it does

Three small, single-responsibility agents run in sequence over every chart:

| Agent | File | Job |
|---|---|---|
| **Ingestion agent** | [dashwise/agents/ingestion_agent.py](dashwise/agents/ingestion_agent.py) | CSV, Excel, and PBIX data-table exports → DashWise dashboard/chart schema |
| **SQL agent** | [dashwise/agents/sql_agent.py](dashwise/agents/sql_agent.py) | Static SQL analysis with **SQLGlot** (no execution) → anti-patterns + a 0–100 complexity score |
| **Cost agent** | [dashwise/agents/cost_agent.py](dashwise/agents/cost_agent.py) | Render time + data scanned → **₹ warehouse cost** (Redshift-style pricing) |
| **Decision agent** | [dashwise/agents/decision_agent.py](dashwise/agents/decision_agent.py) | Usage + cost + SQL quality → a **verdict** and estimated ₹ savings |

## Raw export ingestion

`dashwise.agents.ingestion_agent.ingest(path)` converts messy CSV, Excel, or
PBIX inputs into the same dashboard list consumed by `pipeline.analyze()`.
Column mapping is attempted once per file/table with an LLM and falls back to
fuzzy matching when the model is unavailable or returns malformed JSON.

LLM settings:

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.1-flash-lite
```

PBIX support uses PBIXRay to extract embedded data tables only. It does not
extract DAX measures or report visuals. If you need measures, visual layout, or
Power BI report-page metadata, export the relevant data from Power BI Desktop to
CSV/Excel first and ingest that export as the fallback path.

## Architecture

```
 synthetic input                     dashwise/ package (3 agents)
 ───────────────                     ────────────────────────────
 generate-data ─► data/dashboards.json
                        │
                        ▼
                    analyze ──► sql_agent       (SQLGlot static analysis)
                            ──► cost_agent       (₹ Redshift cost model)
                            ──► decision_agent   (usage + cost + SQL → verdict)
                        │
                        ▼
              output/analysis_results.json
                    │                  │
                    ▼                  ▼
     report ─► executive_report.md    frontend/ (Vite + React + Recharts)
                                       └─► interactive FinOps audit console
```

## Quick start

Requires Python ≥ 3.9 and (for the dashboard) Node ≥ 18.

```bash
# 1. Install the package + dev tools
pip install -e ".[dev]"

# 2. Run the full pipeline: generate data → analyze → report → feed the frontend
dashwise run
#   (equivalently: python -m dashwise run, if the script isn't on your PATH)

# 3. Launch the dashboard
cd frontend
npm install
npm run dev            # open the printed http://localhost:5173
```

`dashwise run` writes `output/analysis_results.json`, `output/executive_report.md`,
and copies the analysis into `frontend/public/` so the console picks it up.

## One-command Docker demo

```bash
docker compose up --build
```

The `pipeline` container generates data and runs the analysis; the `frontend`
container waits for it to finish and serves the console at
**http://localhost:8080**.

## CLI reference

```bash
dashwise generate-data --output data/dashboards.json --dashboards 12 --seed 42
dashwise analyze       --input data/dashboards.json --output output/analysis_results.json
dashwise report        --input output/analysis_results.json --output output/executive_report.md
dashwise run           # all of the above, end-to-end
```

Every command has `--help`. The default seed (42) makes the synthetic estate
reproducible — the committed sample data/output regenerate byte-for-byte.

## Project structure

```
dashwise/            # Python package
  agents/            #   sql_agent, cost_agent, decision_agent
  datagen.py         #   synthetic data generator
  pipeline.py        #   orchestration (SQL → cost → decision)
  reporting.py       #   markdown executive report
  cli.py             #   click CLI (entry point: `dashwise`)
data/                # synthetic input (dashboards.json)
output/              # analysis_results.json + executive_report.md
tests/               # pytest unit tests for all three agents
frontend/            # Vite + React + Tailwind + Recharts console
.github/workflows/   # CI (pytest + frontend build)
```

## What's real vs synthetic

**Real, working code:**
- SQL parsing and anti-pattern detection via **SQLGlot** — fully static, no query
  execution (safe to point at production query logs)
- The ₹ cost model — a documented formula, not a black box
- The decision/recommendation engine combining cost + usage + SQL quality
- The full pipeline, CLI, tests, and React console

**Synthetic (clearly labeled):**
- Dashboard/chart metadata, SQL queries, weekly views, render times, and data
  scanned are all generated by [dashwise/datagen.py](dashwise/datagen.py) to look
  like a realistic Indian mid-size enterprise BI estate, with ~55% intentionally
  bad queries to mimic dashboard sprawl
- No live Snowflake/Power BI/Tableau connection

## Why ₹ / Indian context

Rather than the usual Snowflake-credits, dollar-denominated, Tableau-first
framing, this assumes a stack closer to many Indian enterprises:
- **Power BI-weighted** tool mix (more common here than Tableau)
- **Redshift-style pricing** — ₹210/node-hour, ra3.xlplus-equivalent, Mumbai
  region — rather than Snowflake credits
- **All costs in ₹**, with Indian digit grouping (lakh/crore) in the UI

The cost model is documented in [cost_agent.py](dashwise/agents/cost_agent.py);
the decision thresholds in [decision_agent.py](dashwise/agents/decision_agent.py).

## Testing & CI

```bash
pytest -q
```

35 unit tests cover every SQL anti-pattern the agent detects (SELECT *, cross
joins, duplicate CTEs, missing WHERE, high join counts, ORDER BY without LIMIT,
nested subqueries, …), the cost-model tiers and arithmetic, and each decision
verdict branch. GitHub Actions
([.github/workflows/ci.yml](.github/workflows/ci.yml)) runs the suite on Python
3.10 and 3.12 and builds the frontend on every push and PR.

## What was intentionally cut (and why)

| Cut | Reason |
|---|---|
| Neo4j lineage graph | Real value, but needs real dbt/warehouse metadata to be meaningful — not fakeable convincingly |
| Computer vision on dashboard screenshots | Needs real screenshots + a vision model call; out of scope for this build |
| Live Snowflake/Power BI API connections | Needs real credentials/environment; synthetic data demonstrates the same logic |
| Multi-agent orchestration framework (CrewAI/LangGraph) | The three agents are plain, sequential Python — honest about not over-engineering a demo |
