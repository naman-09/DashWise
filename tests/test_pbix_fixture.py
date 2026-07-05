"""End-to-end ingestion of a real PBIX file, with nothing mocked.

The fixture is a genuine Power BI Desktop file (see tests/fixtures/README.md).
PBIXRay parses the actual binary; the LLM call is really attempted against a
closed local port so the real fuzzy-fallback path runs deterministically.
"""
from pathlib import Path

import pytest

from dashwise.agents import ingestion_agent

FIXTURE = Path(__file__).parent / "fixtures" / "PerformanceAnalyzerExportReport.pbix"

CHART_KEYS = {
    "chart_id",
    "chart_title",
    "chart_type",
    "sql_query",
    "weekly_views",
    "avg_view_duration_sec",
    "render_time_sec",
    "data_scanned_gb",
    "runs_per_week",
}
DASHBOARD_KEYS = {"dashboard_id", "dashboard_name", "business_unit", "owner", "bi_tool", "charts"}

pytestmark = pytest.mark.pbix_e2e


@pytest.fixture(autouse=True)
def unreachable_llm(monkeypatch):
    # Port 0 is never connectable, so the Ollama request fails immediately and
    # ingestion exercises its real LLM-failure -> fuzzy-fallback path.
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


def test_real_pbix_ingests_into_dashboard_schema():
    dashboards, report = ingestion_agent.ingest_with_report(FIXTURE)

    assert len(dashboards) == 1
    dashboard = dashboards[0]
    assert set(dashboard) == DASHBOARD_KEYS
    assert dashboard["dashboard_id"] == "DASH-001"
    assert dashboard["bi_tool"] == "Power BI"
    assert dashboard["dashboard_name"] == "Visual Container Lifecycle"

    charts = dashboard["charts"]
    assert len(charts) == 7
    titles = {chart["chart_title"] for chart in charts}
    assert "SalesAmount by CalendarYear and CalendarSemester" in titles
    for chart in charts:
        assert set(chart) == CHART_KEYS
        assert chart["chart_title"].strip()
        assert isinstance(chart["chart_title"], str)
        assert isinstance(chart["sql_query"], str)
        assert isinstance(chart["weekly_views"], int)
        assert isinstance(chart["runs_per_week"], int)
        assert isinstance(chart["avg_view_duration_sec"], float)
        assert isinstance(chart["render_time_sec"], float)
        assert isinstance(chart["data_scanned_gb"], float)

    assert report["mapping_source"] == "fuzzy_fallback"
    assert report["rows_processed"] == 377
    assert report["rows_dropped"] == 370


def test_real_pbix_camelcase_columns_are_fuzzy_mapped():
    # Real PBIX models expose camelCase columns; the fuzzy fallback must map
    # them without an LLM. The mocked tests only cover snake_case headers.
    report = ingestion_agent.ingest_report(FIXTURE)

    mapping = report["column_mapping_used"]
    assert mapping["Events.visualTitle"] == "chart_title"
    assert mapping["Events.visualType"] == "chart_type"
    assert mapping["Events.QueryText"] == "sql_query"
