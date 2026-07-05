"""FastAPI service for stateless DashWise analysis requests."""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dashwise import datagen, pipeline
from dashwise.agents import ingestion_agent

SUPPORTED_UPLOAD_EXTENSIONS = {".csv", ".xlsx", ".pbix"}


def _cors_origins() -> list[str]:
    raw = os.getenv("DASHWISE_CORS_ORIGINS", "*").strip()
    if not raw or raw == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(title="DashWise API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    """Basic liveness check."""
    return {"status": "ok"}


@app.post("/analyze")
async def analyze_upload(file: UploadFile = File(...)):
    """Analyze an uploaded CSV/XLSX/PBIX export and return full analysis JSON."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_UPLOAD_EXTENSIONS:
        return _validation_error([f"Unsupported file extension: {suffix or '<none>'}"])

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = Path(temp_file.name)
            shutil.copyfileobj(file.file, temp_file)

        dashboards, ingestion_report = ingestion_agent.ingest_with_report(temp_path)
    except Exception as exc:  # noqa: BLE001 - pandas/openpyxl parsing errors vary.
        return _validation_error([f"Unable to ingest uploaded file: {exc}"])
    finally:
        await file.close()
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    if not dashboards:
        warnings = ingestion_report.get("warnings") or ["No dashboard records could be ingested from the file."]
        return _validation_error(warnings)

    analysis = pipeline.analyze(dashboards)
    return {**analysis, "ingestion_report": ingestion_report}


@app.post("/analyze/sample")
def analyze_sample() -> dict:
    """Analyze freshly generated synthetic dashboards for demo mode."""
    dashboards = datagen.generate_dashboards()
    return pipeline.analyze(dashboards)


def _validation_error(warnings: list[str]) -> JSONResponse:
    return JSONResponse(status_code=422, content={"warnings": warnings})
