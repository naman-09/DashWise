import pandas as pd
import pytest
from fastapi.testclient import TestClient

from dashwise.agents import ingestion_agent
from dashwise.agents.llm_client import LLMMappingError
from dashwise.api import app


@pytest.fixture
def no_llm(monkeypatch):
    def fail_mapping(raw_headers, sample_rows):
        raise LLMMappingError("test disables live LLM calls")

    monkeypatch.setattr(ingestion_agent.llm_client, "map_columns", fail_mapping)


@pytest.fixture
def client():
    return TestClient(app)


def test_analyze_upload_success_returns_analysis_and_ingestion_report(client, no_llm):
    csv_bytes = (
        pd.DataFrame(
            [
                {
                    "dashboard_name": "Sales Pulse",
                    "business_unit": "Sales",
                    "owner": "Ananya",
                    "bi_tool": "Power BI",
                    "chart_title": "Revenue by Region",
                    "chart_type": "bar chart",
                    "sql_query": "select region, sum(revenue) from sales where region is not null group by region",
                    "weekly_views": 25,
                    "avg_view_duration_sec": 38.5,
                    "render_time_sec": 4.2,
                    "data_scanned_gb": 7.5,
                    "runs_per_week": 14,
                }
            ]
        )
        .to_csv(index=False)
        .encode("utf-8")
    )

    response = client.post("/analyze", files={"file": ("dashboards.csv", csv_bytes, "text/csv")})

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"summary", "dashboards", "ingestion_report"}
    assert payload["summary"]["total_dashboards"] == 1
    assert payload["summary"]["total_charts"] == 1
    assert payload["ingestion_report"]["rows_processed"] == 1
    assert payload["dashboards"][0]["dashboard_yearly_cost_inr"] >= 0
    assert "total_yearly_cost_inr" in payload["summary"]


def test_analyze_upload_accepts_pbix_extension(client, monkeypatch):
    dashboards = [
        {
            "dashboard_id": "DASH-001",
            "dashboard_name": "PBIX Usage",
            "business_unit": "Operations",
            "owner": "Ananya",
            "bi_tool": "Power BI",
            "charts": [
                {
                    "chart_id": "CHART-0001",
                    "chart_title": "Refresh Duration",
                    "chart_type": "line_chart",
                    "sql_query": "select 1 as metric",
                    "weekly_views": 12,
                    "avg_view_duration_sec": 30,
                    "render_time_sec": 3,
                    "data_scanned_gb": 4,
                    "runs_per_week": 7,
                }
            ],
        }
    ]
    report = {
        "rows_processed": 1,
        "rows_dropped": 0,
        "warnings": [],
        "column_mapping_used": {},
        "mapping_source": "fuzzy_fallback",
    }

    def fake_ingest_with_report(file_path):
        assert file_path.suffix == ".pbix"
        return dashboards, report

    monkeypatch.setattr(ingestion_agent, "ingest_with_report", fake_ingest_with_report)

    response = client.post(
        "/analyze",
        files={"file": ("usage.pbix", b"minimal pbix placeholder", "application/octet-stream")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total_dashboards"] == 1
    assert payload["ingestion_report"]["rows_processed"] == 1


def test_analyze_sample_uses_generated_dashboards(client):
    response = client.post("/analyze/sample")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total_dashboards"] == 12
    assert payload["summary"]["total_charts"] > 0
    assert payload["dashboards"]
    assert "total_yearly_cost_inr" in payload["summary"]


def test_analyze_malformed_file_returns_422_with_warnings(client, no_llm):
    response = client.post(
        "/analyze",
        files={"file": ("bad.csv", b"not_a_dashwise_column\nstill_not_a_chart\n", "text/csv")},
    )

    assert response.status_code == 422
    payload = response.json()
    assert "warnings" in payload
    assert any("Dropped" in warning or "No chart-level rows" in warning for warning in payload["warnings"])
