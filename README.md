# DashWise AI - BI Dashboard FinOps & Usage Audit

DashWise audits BI dashboards on three axes: **SQL quality**, **warehouse
compute cost (₹)**, and **actual usage**. It produces a per-chart verdict
(**remove / optimize / monitor / keep**) with an estimated ₹ savings figure.

> **Honest scope:** this is a scoped, working proof-of-concept. The analysis
> logic is real and runnable, and raw CSV/XLSX/PBIX uploads can be ingested.
> The bundled demo estate is synthetic. See
> [What's Real vs Synthetic](#whats-real-vs-synthetic).

![CI](https://github.com/naman-09/DashWise/actions/workflows/ci.yml/badge.svg)

## What It Does

DashWise has **4 total backend components**:

| Component | File | Role |
|---|---|---|
| **Ingestion component** | [dashwise/agents/ingestion_agent.py](dashwise/agents/ingestion_agent.py) | LLM-assisted mapping of CSV/XLSX/PBIX data-table exports into the DashWise dashboard/chart schema, with rapidfuzz fallback |
| **SQL agent** | [dashwise/agents/sql_agent.py](dashwise/agents/sql_agent.py) | Rule-based static SQL analysis with SQLGlot; no query execution |
| **Cost agent** | [dashwise/agents/cost_agent.py](dashwise/agents/cost_agent.py) | Rule-based Redshift Mumbai warehouse cost modeling in ₹ |
| **Decision agent** | [dashwise/agents/decision_agent.py](dashwise/agents/decision_agent.py) | Rule-based verdicts from usage, cost, and SQL quality |

Only `ingestion_agent` can make an LLM call, and only for column mapping.
`sql_agent`, `cost_agent`, and `decision_agent` are rule-based analysis agents
and do not use an LLM.

## Architecture

```
CSV/XLSX/PBIX upload or generated sample data
        |
        v
ingestion_agent
  - CSV/XLSX via pandas/openpyxl
  - PBIX data tables via PBIXRay
  - LLM-assisted column mapping (Ollama default, Gemini optional)
  - rapidfuzz fallback when the LLM is unavailable or returns malformed JSON
        |
        v
pipeline.analyze()
  - sql_agent: rule-based SQLGlot static analysis
  - cost_agent: rule-based Redshift Mumbai cost model
    (ra3.xlplus, ₹210/node-hour)
  - decision_agent: rule-based usage + cost + SQL verdicts
        |
        v
FastAPI
  - POST /analyze: analyze uploaded CSV/XLSX/PBIX exports
  - POST /analyze/sample: analyze generated sample dashboards
  - GET /health: service health check
        |
        v
React frontend (Vite + Tailwind + Recharts)
```

## Raw Export Ingestion

`dashwise.agents.ingestion_agent.ingest(path)` converts messy CSV, XLSX, or
PBIX data-table inputs into the same dashboard list consumed by
`pipeline.analyze()`. `ingest_report(path)` returns diagnostics, and
`ingest_with_report(path)` returns both the dashboards and the report for the
FastAPI upload path.

Column mapping is attempted once per file/table with an LLM. If the LLM is not
available, times out, or returns malformed JSON, ingestion falls back to
rapidfuzz matching instead of crashing. Once the backend proves unreachable,
the remaining tables in that file skip the LLM entirely so multi-table files
degrade quickly instead of paying a connection timeout per table.

PBIX support uses PBIXRay to extract embedded data tables only. It does not
extract DAX measures or report visuals. If you need measures, visual layout, or
Power BI report-page metadata, export the relevant data from Power BI Desktop to
CSV/XLSX first and ingest that export as the fallback path.

## Setup

Requires Python >= 3.9 and Node >= 18 for the frontend.

Install the Python package and dev tools:

```bash
pip install -e ".[dev]"
```

The Python install uses the runtime dependencies declared in
[pyproject.toml](pyproject.toml): `sqlglot`, `click`, `pandas`, `openpyxl`,
`rapidfuzz`, `pbixray`, `fastapi`, `uvicorn`, and `python-multipart`.

Optional LLM configuration for ingestion:

```bash
# Default provider
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Optional Gemini provider
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

If no LLM is reachable, DashWise still ingests files through rapidfuzz fallback.

Install and run the frontend:

```bash
cd frontend
npm install
npm run dev
```

## Running Locally

Generate synthetic data, analyze it, render a report, and feed the frontend:

```bash
dashwise run
```

Run the API directly:

```bash
uvicorn dashwise.api:app --host 127.0.0.1 --port 8000
```

Useful API routes:

```bash
GET  /health
POST /analyze
POST /analyze/sample
```

## Docker Demo

```bash
docker compose up --build
```

The `api` service exposes FastAPI on **http://localhost:8000**. The `frontend`
service exposes the React console on **http://localhost:8080** and calls the API
at `http://localhost:8000`.

## CLI Reference

```bash
dashwise generate-data --output data/dashboards.json --dashboards 12 --seed 42
dashwise analyze       --input data/dashboards.json --output output/analysis_results.json
dashwise report        --input output/analysis_results.json --output output/executive_report.md
dashwise run           # all of the above, end-to-end
```

Every command has `--help`. The default seed (42) makes the synthetic estate
reproducible.

## Project Structure

```
dashwise/            # Python package
  agents/            # ingestion_agent, sql_agent, cost_agent, decision_agent
  api.py             # FastAPI service (/analyze, /analyze/sample, /health)
  datagen.py         # synthetic data generator
  pipeline.py        # orchestration (SQL -> cost -> decision)
  reporting.py       # markdown executive report
  cli.py             # click CLI (entry point: dashwise)
data/                # synthetic input (dashboards.json)
output/              # analysis_results.json + executive_report.md
tests/               # pytest suite
frontend/            # Vite + React + Tailwind + Recharts console
.github/workflows/   # CI (pytest + frontend build)
```

## What's Real vs Synthetic

**Real, working code:**

- CSV/XLSX ingestion via pandas/openpyxl
- PBIX data-table extraction via PBIXRay
- LLM-assisted column mapping for ingestion only, with rapidfuzz fallback
- Static SQL parsing and anti-pattern detection via SQLGlot
- Redshift Mumbai cost modeling in ₹ using ra3.xlplus at ₹210/node-hour
- Rule-based decision/recommendation logic
- FastAPI upload/sample endpoints, CLI, tests, Docker config, and React console

**Synthetic or intentionally scoped:**

- The bundled sample dashboard/chart metadata, SQL queries, weekly views, render
  times, and data scanned are generated by
  [dashwise/datagen.py](dashwise/datagen.py) to resemble an Indian mid-size
  enterprise BI estate.
- There is no live Power BI/Tableau API connection.
- PBIX support reads data tables only, not DAX measures or report visuals.

## Why ₹ / Indian Context

DashWise keeps cost assumptions aligned with an Indian enterprise warehouse
context:

- Power BI-weighted demo data
- Redshift-style pricing modeled as ₹210/node-hour, ra3.xlplus-equivalent,
  Mumbai region
- All costs in ₹, with Indian digit grouping in the UI

The cost model is documented in [cost_agent.py](dashwise/agents/cost_agent.py).
The decision thresholds are documented in
[decision_agent.py](dashwise/agents/decision_agent.py).

## Testing & CI

```bash
pytest -q
npm run build
```

The Python suite covers SQL anti-pattern detection, the cost-model tiers and
arithmetic, decision verdict branches, ingestion behavior, and API upload/sample
paths. It also ingests a real PBIX fixture
([tests/fixtures/](tests/fixtures/)) end-to-end through PBIXRay; deselect that
with `pytest -m "not pbix_e2e"` for the fastest runs. GitHub Actions ([.github/workflows/ci.yml](.github/workflows/ci.yml))
runs the suite and builds the frontend on every push and PR.

## What Was Intentionally Cut

| Cut | Reason |
|---|---|
| Lineage graph | Needs real warehouse/dbt metadata to be meaningful |
| Computer vision on dashboard screenshots | Needs real screenshots and a vision model call |
| Live BI platform API connections | Needs real credentials and customer tenant context |
| Multi-agent orchestration framework | The rule-based analysis agents are plain Python functions by design |
