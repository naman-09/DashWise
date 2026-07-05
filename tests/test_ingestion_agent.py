import pandas as pd
import pytest

from dashwise.agents import ingestion_agent, llm_client
from dashwise.agents.llm_client import LLMMappingError, LLMUnavailableError


@pytest.fixture
def no_llm(monkeypatch):
    def fail_mapping(raw_headers, sample_rows):
        raise LLMMappingError("test disables live LLM calls")

    monkeypatch.setattr(ingestion_agent.llm_client, "map_columns", fail_mapping)


def _write_csv(tmp_path, rows, name="raw.csv"):
    path = tmp_path / name
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_clean_csv_ingests_pipeline_schema(tmp_path, no_llm):
    path = _write_csv(
        tmp_path,
        [
            {
                "dashboard_name": "Sales Pulse",
                "business_unit": "Sales",
                "owner": "Ananya",
                "bi_tool": "Power BI",
                "chart_title": "Revenue by Region",
                "chart_type": "bar chart",
                "sql_query": "select region, sum(revenue) from sales group by region",
                "weekly_views": 25,
                "avg_view_duration_sec": 38.5,
                "render_time_sec": 4.2,
                "data_scanned_gb": 7.5,
                "runs_per_week": 14,
            }
        ],
    )

    dashboards = ingestion_agent.ingest(path)

    assert dashboards == [
        {
            "dashboard_id": "DASH-001",
            "dashboard_name": "Sales Pulse",
            "business_unit": "Sales",
            "owner": "Ananya",
            "bi_tool": "Power BI",
            "charts": [
                {
                    "chart_id": "CHART-0001",
                    "chart_title": "Revenue by Region",
                    "chart_type": "bar_chart",
                    "sql_query": "select region, sum(revenue) from sales group by region",
                    "weekly_views": 25,
                    "avg_view_duration_sec": 38.5,
                    "render_time_sec": 4.2,
                    "data_scanned_gb": 7.5,
                    "runs_per_week": 14,
                }
            ],
        }
    ]


def test_indian_number_formatting_is_coerced(tmp_path, no_llm):
    path = _write_csv(
        tmp_path,
        [
            {
                "dashboard_name": "Ops",
                "business_unit": "Operations",
                "chart_title": "Inventory Ageing",
                "weekly_views": "1,00,000",
                "avg_view_duration_sec": "12.5",
                "render_time_sec": "₹1,234.5",
                "data_scanned_gb": "2,50,000.75",
                "runs_per_week": "1,680",
            }
        ],
    )

    chart = ingestion_agent.ingest(path)[0]["charts"][0]

    assert chart["weekly_views"] == 100000
    assert chart["render_time_sec"] == 1234.5
    assert chart["data_scanned_gb"] == 250000.75
    assert chart["runs_per_week"] == 1680


def test_missing_sql_column_defaults_to_empty_string(tmp_path, no_llm):
    path = _write_csv(
        tmp_path,
        [
            {
                "dashboard_name": "Marketing",
                "business_unit": "Marketing",
                "chart_title": "Lead Funnel",
                "weekly_views": 10,
                "render_time_sec": 2,
                "data_scanned_gb": 1,
                "runs_per_week": 7,
            }
        ],
    )

    chart = ingestion_agent.ingest(path)[0]["charts"][0]

    assert chart["sql_query"] == ""


def test_missing_dashboard_grouping_creates_single_imported_dashboard(tmp_path, no_llm):
    path = _write_csv(
        tmp_path,
        [
            {"chart_title": "Chart A", "weekly_views": 1, "render_time_sec": 1, "data_scanned_gb": 1, "runs_per_week": 1},
            {"chart_title": "Chart B", "weekly_views": 2, "render_time_sec": 1, "data_scanned_gb": 1, "runs_per_week": 1},
        ],
    )

    dashboards = ingestion_agent.ingest(path)

    assert len(dashboards) == 1
    assert dashboards[0]["dashboard_name"] == "Imported Dashboard"
    assert dashboards[0]["business_unit"] == "Unknown"
    assert [chart["chart_title"] for chart in dashboards[0]["charts"]] == ["Chart A", "Chart B"]


def test_malformed_rows_are_dropped_and_reported(tmp_path, no_llm):
    path = _write_csv(
        tmp_path,
        [
            {"dashboard_name": "Finance", "business_unit": "Finance", "chart_title": "Payment Ageing"},
            {"dashboard_name": "Finance", "business_unit": "Finance", "chart_title": ""},
        ],
    )

    dashboards = ingestion_agent.ingest(path)
    report = ingestion_agent.ingest_report(path)

    assert len(dashboards[0]["charts"]) == 1
    assert report["rows_processed"] == 2
    assert report["rows_dropped"] == 1
    assert any("Dropped 1 malformed" in warning for warning in report["warnings"])


def test_mocked_llm_response_maps_messy_headers(tmp_path, monkeypatch):
    path = _write_csv(
        tmp_path,
        [
            {
                "Report Label": "Executive Usage",
                "Dept Name": "Finance",
                "Visual Caption": "Spend Trend",
                "Viz Kind": "line chart",
                "Views 7D": "42",
                "Runtime Seconds": "9",
                "GB Processed": "13.5",
                "Weekly Executions": "21",
            }
        ],
    )

    def mapped(raw_headers, sample_rows):
        return {
            "Report Label": "dashboard_name",
            "Dept Name": "business_unit",
            "Visual Caption": "chart_title",
            "Viz Kind": "chart_type",
            "Views 7D": "weekly_views",
            "Runtime Seconds": "render_time_sec",
            "GB Processed": "data_scanned_gb",
            "Weekly Executions": "runs_per_week",
        }

    monkeypatch.setattr(ingestion_agent.llm_client, "map_columns", mapped)

    dashboards = ingestion_agent.ingest(path)
    report = ingestion_agent.ingest_report(path)

    assert dashboards[0]["dashboard_name"] == "Executive Usage"
    assert dashboards[0]["business_unit"] == "Finance"
    assert dashboards[0]["charts"][0]["chart_title"] == "Spend Trend"
    assert report["mapping_source"] == "llm"


def test_malformed_llm_response_falls_back_to_fuzzy_matching(tmp_path, monkeypatch):
    path = _write_csv(
        tmp_path,
        [
            {
                "dashboard_name": "Sales",
                "business_unit": "Sales",
                "chart_title": "Revenue",
                "weekly_views": 5,
            }
        ],
    )

    def malformed(raw_headers, sample_rows):
        return {"chart_title": "not_allowed"}

    monkeypatch.setattr(ingestion_agent.llm_client, "map_columns", malformed)

    report = ingestion_agent.ingest_report(path)

    assert report["mapping_source"] == "fuzzy_fallback"
    assert report["column_mapping_used"]["chart_title"] == "chart_title"


def test_unreachable_llm_is_attempted_only_once_per_file(tmp_path, monkeypatch):
    path = tmp_path / "multi.xlsx"
    sheet = pd.DataFrame([{"chart_title": "Chart", "weekly_views": 1}])
    with pd.ExcelWriter(path) as writer:
        sheet.to_excel(writer, sheet_name="Sheet1", index=False)
        sheet.to_excel(writer, sheet_name="Sheet2", index=False)
        sheet.to_excel(writer, sheet_name="Sheet3", index=False)

    calls = []

    def unreachable(raw_headers, sample_rows):
        calls.append(raw_headers)
        raise LLMUnavailableError("Ollama is unreachable")

    monkeypatch.setattr(ingestion_agent.llm_client, "map_columns", unreachable)

    dashboards, report = ingestion_agent.ingest_with_report(path)

    assert len(calls) == 1
    assert report["mapping_source"] == "fuzzy_fallback"
    assert sum(len(d["charts"]) for d in dashboards) == 3
    assert any("LLM unavailable" in warning for warning in report["warnings"])


def test_connection_failure_raises_llm_unavailable_error(monkeypatch):
    # Real network attempt: port 0 is never connectable, so the client must
    # classify the failure as "unavailable" (and do so immediately).
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:0")

    with pytest.raises(LLMUnavailableError):
        llm_client.map_columns(["chart_title"], [{"chart_title": "Revenue"}])


def test_missing_gemini_key_raises_llm_unavailable_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(LLMUnavailableError):
        llm_client.map_columns(["chart_title"], [{"chart_title": "Revenue"}])


def test_pbix_tables_are_extracted_with_same_mapping_logic(tmp_path, monkeypatch):
    pbix_path = tmp_path / "usage.pbix"
    pbix_path.write_bytes(b"placeholder")

    class FakePBIX:
        tables = ["Usage", "DateTableTemplate_abc123", "LocalDateTable_def456"]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def get_table(self, table_name):
            assert table_name == "Usage"
            return pd.DataFrame(
                [
                    {
                        "dashboard_name": "PBIX Usage",
                        "business_unit": "Operations",
                        "chart_title": "Refresh Duration",
                        "weekly_views": 11,
                        "render_time_sec": 3,
                        "data_scanned_gb": 4,
                        "runs_per_week": 7,
                    }
                ]
            )

    monkeypatch.setattr(ingestion_agent, "_load_pbix_model", lambda path: FakePBIX())
    monkeypatch.setattr(
        ingestion_agent.llm_client,
        "map_columns",
        lambda raw_headers, sample_rows: (_ for _ in ()).throw(LLMMappingError("fallback")),
    )

    dashboards, report = ingestion_agent.ingest_with_report(pbix_path)

    assert dashboards[0]["dashboard_name"] == "PBIX Usage"
    assert dashboards[0]["bi_tool"] == "Power BI"
    assert dashboards[0]["charts"][0]["chart_title"] == "Refresh Duration"
    # get_table would assert on any non-"Usage" table, so the auto-generated
    # date tables must have been skipped before extraction.
    assert any("Skipped 2 Power BI auto-generated date table(s)" in warning for warning in report["warnings"])


def test_pbix_parse_failure_is_reported_without_crashing(tmp_path, monkeypatch):
    pbix_path = tmp_path / "broken.pbix"
    pbix_path.write_bytes(b"placeholder")

    def fail(path):
        raise RuntimeError("unsupported PBIX version")

    monkeypatch.setattr(ingestion_agent, "_load_pbix_model", fail)

    assert ingestion_agent.ingest(pbix_path) == []
    report = ingestion_agent.ingest_report(pbix_path)
    assert report["rows_processed"] == 0
    assert any("Unable to parse PBIX file" in warning for warning in report["warnings"])
