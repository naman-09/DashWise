"""Ingest raw BI export files into the DashWise dashboard schema."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from dashwise.agents import llm_client
from dashwise.agents.llm_client import ALLOWED_CANONICAL_FIELDS, LLMMappingError

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover - dependency is declared, fallback is defensive.
    from difflib import SequenceMatcher

    class fuzz:  # type: ignore[no-redef]
        @staticmethod
        def token_set_ratio(left: str, right: str) -> float:
            return SequenceMatcher(None, left, right).ratio() * 100


FIELD_ALIASES = {
    "chart_title": ["chart title", "visual title", "visual name", "tile title", "report page visual", "metric name"],
    "chart_type": ["chart type", "visual type", "visualization type", "viz type", "type"],
    "sql_query": ["sql query", "query", "source query", "native query", "m query", "statement"],
    "weekly_views": ["weekly views", "views per week", "view count", "views", "usage count", "users viewed"],
    "avg_view_duration_sec": [
        "avg view duration sec",
        "average view duration seconds",
        "duration seconds",
        "avg duration",
        "time spent seconds",
    ],
    "render_time_sec": ["render time sec", "load time seconds", "render seconds", "refresh time sec", "query duration sec"],
    "data_scanned_gb": ["data scanned gb", "scan gb", "data processed gb", "bytes scanned", "gb scanned"],
    "runs_per_week": ["runs per week", "refreshes per week", "queries per week", "executions per week", "run count"],
    "dashboard_name": ["dashboard name", "report name", "workspace report", "pbix name", "dashboard"],
    "business_unit": ["business unit", "department", "dept", "function", "team", "domain"],
    "owner": ["owner", "report owner", "dashboard owner", "created by", "contact"],
    "bi_tool": ["bi tool", "tool", "platform", "source system", "reporting tool"],
}


@dataclass
class IngestionState:
    rows_processed: int = 0
    rows_dropped: int = 0
    warnings: list[str] = field(default_factory=list)
    column_mapping_used: dict[str, str | None] = field(default_factory=dict)
    mapping_source: str = "fuzzy_fallback"


def ingest(file_path) -> list[dict]:
    """Load a raw BI export and return dashboards ready for ``pipeline.analyze``."""
    dashboards, _state = _ingest(file_path)
    return dashboards


def ingest_with_report(file_path) -> tuple[list[dict], dict]:
    """Load a raw BI export and return dashboards plus ingestion diagnostics."""
    dashboards, state = _ingest(file_path)
    return dashboards, _report_from_state(state)


def ingest_report(file_path) -> dict:
    """Return ingestion diagnostics for a raw BI export."""
    _dashboards, state = _ingest(file_path)
    return _report_from_state(state)


def _report_from_state(state: IngestionState) -> dict:
    return {
        "rows_processed": state.rows_processed,
        "rows_dropped": state.rows_dropped,
        "warnings": state.warnings,
        "column_mapping_used": state.column_mapping_used,
        "mapping_source": state.mapping_source,
    }


def _ingest(file_path) -> tuple[list[dict], IngestionState]:
    path = Path(file_path)
    state = IngestionState()
    tables = _load_tables(path, state)
    default_bi_tool = "Power BI" if path.suffix.lower() == ".pbix" else "Unknown"
    chart_rows: list[dict] = []

    for table_name, frame in tables:
        normalized = _normalize_dataframe(frame)
        state.rows_processed += len(normalized)
        if normalized.empty:
            state.warnings.append(f"Skipped empty table: {table_name}")
            continue

        mapping, source = _build_column_mapping(normalized, state, table_name)
        if source == "llm":
            state.mapping_source = "llm"
        mapping_prefix = f"{table_name}." if len(tables) > 1 else ""
        state.column_mapping_used.update({f"{mapping_prefix}{key}": value for key, value in mapping.items()})

        table_rows, dropped = _rows_to_chart_records(normalized, mapping, table_name, default_bi_tool, state)
        state.rows_dropped += dropped
        chart_rows.extend(table_rows)

    dashboards = _group_chart_rows(chart_rows)
    if not dashboards and not state.warnings:
        state.warnings.append("No chart-level rows could be ingested from the file.")
    return dashboards, state


def _load_tables(path: Path, state: IngestionState) -> list[tuple[str, pd.DataFrame]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return [(path.stem, pd.read_csv(path))]
    if suffix in {".xlsx", ".xls"}:
        sheets = pd.read_excel(path, sheet_name=None, engine="openpyxl" if suffix == ".xlsx" else None)
        return [(sheet_name, frame) for sheet_name, frame in sheets.items()]
    if suffix == ".pbix":
        return _extract_pbix_tables(path, state)
    state.warnings.append(f"Unsupported file extension: {suffix or '<none>'}")
    return []


def _extract_pbix_tables(path: Path, state: IngestionState) -> list[tuple[str, pd.DataFrame]]:
    try:
        model = _load_pbix_model(path)
    except Exception as exc:  # noqa: BLE001 - PBIX parsing errors vary by version.
        state.warnings.append(f"Unable to parse PBIX file: {exc}")
        return []

    tables: list[tuple[str, pd.DataFrame]] = []
    skipped_system_tables = 0
    try:
        with model if hasattr(model, "__enter__") else _NullContext(model) as pbix_model:
            for table_name in _table_names(pbix_model):
                if _is_pbix_system_table(str(table_name)):
                    skipped_system_tables += 1
                    continue
                try:
                    tables.append((str(table_name), pbix_model.get_table(table_name)))
                except Exception as exc:  # noqa: BLE001
                    state.warnings.append(f"Unable to extract PBIX table '{table_name}': {exc}")
    except Exception as exc:  # noqa: BLE001
        state.warnings.append(f"Unable to extract PBIX tables: {exc}")
        return []

    if skipped_system_tables:
        state.warnings.append(
            f"Skipped {skipped_system_tables} Power BI auto-generated date table(s)."
        )

    if not tables:
        state.warnings.append("PBIX file did not expose any extractable data tables.")
    return tables


def _is_pbix_system_table(table_name: str) -> bool:
    # Hidden auto-date tables Power BI adds to every model; never user data.
    return table_name.startswith(("DateTableTemplate_", "LocalDateTable_"))


def _load_pbix_model(path: Path):
    from pbixray import PBIXRay

    return PBIXRay(str(path))


def _table_names(pbix_model) -> list:
    tables = pbix_model.tables
    if isinstance(tables, pd.DataFrame):
        for column in ("Name", "TableName", "name", "table_name"):
            if column in tables.columns:
                return tables[column].dropna().tolist()
        return tables.iloc[:, 0].dropna().tolist()
    if isinstance(tables, pd.Series):
        return tables.dropna().tolist()
    return list(tables)


class _NullContext:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self.value

    def __exit__(self, exc_type, exc, traceback):
        close = getattr(self.value, "close", None)
        if callable(close):
            close()
        return False


def _normalize_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    normalized.columns = [str(column).strip() for column in normalized.columns]
    normalized = normalized.dropna(how="all")
    return normalized


def _build_column_mapping(frame: pd.DataFrame, state: IngestionState, table_name: str) -> tuple[dict, str]:
    raw_headers = list(frame.columns)
    sample_rows = [_jsonable_sample(row) for row in frame.head(5).to_dict(orient="records")]
    try:
        mapping = llm_client.map_columns(raw_headers, sample_rows)
        _validate_mapping(mapping, raw_headers)
        if any(value is not None for value in mapping.values()):
            return mapping, "llm"
        state.warnings.append(f"LLM returned no usable column matches for table '{table_name}'.")
    except (LLMMappingError, ValueError, RuntimeError) as exc:
        state.warnings.append(f"LLM column mapping failed for table '{table_name}'; used fuzzy fallback. {exc}")
    return _fuzzy_map_columns(raw_headers), "fuzzy_fallback"


def _validate_mapping(mapping: dict, raw_headers: list[str]) -> None:
    if not isinstance(mapping, dict):
        raise ValueError("column mapping must be a dictionary")
    if not set(mapping).issubset(set(raw_headers)):
        raise ValueError("column mapping contains unknown raw headers")
    for canonical_field in mapping.values():
        if canonical_field is not None and canonical_field not in ALLOWED_CANONICAL_FIELDS:
            raise ValueError(f"unsupported canonical field: {canonical_field}")


def _fuzzy_map_columns(raw_headers: list[str]) -> dict[str, str | None]:
    candidates: list[tuple[float, str, str]] = []
    for header in raw_headers:
        normalized_header = _normalize_label(header)
        for field, aliases in FIELD_ALIASES.items():
            values = [field, field.replace("_", " "), *aliases]
            score = max(fuzz.token_set_ratio(normalized_header, _normalize_label(value)) for value in values)
            if normalized_header == field or normalized_header == field.replace("_", " "):
                score = 100
            candidates.append((float(score), header, field))

    mapping: dict[str, str | None] = {header: None for header in raw_headers}
    assigned_fields: set[str] = set()
    for score, header, field in sorted(candidates, reverse=True):
        if score < 78 or mapping[header] is not None or field in assigned_fields:
            continue
        mapping[header] = field
        assigned_fields.add(field)
    return mapping


def _rows_to_chart_records(
    frame: pd.DataFrame,
    mapping: dict[str, str | None],
    table_name: str,
    default_bi_tool: str,
    state: IngestionState,
) -> tuple[list[dict], int]:
    rows: list[dict] = []
    dropped = 0
    reverse_mapping = _reverse_mapping(mapping)

    for _index, raw_row in frame.iterrows():
        canonical = {
            field: _value_from_row(raw_row, reverse_mapping.get(field))
            for field in ALLOWED_CANONICAL_FIELDS
            if reverse_mapping.get(field)
        }
        chart_title = _clean_text(canonical.get("chart_title"))
        if not chart_title:
            dropped += 1
            continue

        chart = {
            "dashboard_name": _clean_text(canonical.get("dashboard_name")) or "Imported Dashboard",
            "business_unit": _clean_text(canonical.get("business_unit")) or "Unknown",
            "owner": _clean_text(canonical.get("owner")) or "Unknown",
            "bi_tool": _clean_text(canonical.get("bi_tool")) or default_bi_tool,
            "chart_title": chart_title,
            "chart_type": _normalize_chart_type(_clean_text(canonical.get("chart_type"))),
            "sql_query": _clean_text(canonical.get("sql_query")) or "",
            "weekly_views": _coerce_number(canonical.get("weekly_views"), as_int=True),
            "avg_view_duration_sec": _coerce_number(canonical.get("avg_view_duration_sec")),
            "render_time_sec": _coerce_number(canonical.get("render_time_sec")),
            "data_scanned_gb": _coerce_data_scanned_gb(canonical.get("data_scanned_gb")),
            "runs_per_week": _coerce_number(canonical.get("runs_per_week"), as_int=True),
        }
        rows.append(chart)

    if dropped:
        state.warnings.append(f"Dropped {dropped} malformed row(s) from table '{table_name}'.")
    return rows, dropped


def _reverse_mapping(mapping: dict[str, str | None]) -> dict[str, str]:
    reverse: dict[str, str] = {}
    for raw_header, canonical_field in mapping.items():
        if canonical_field and canonical_field not in reverse:
            reverse[canonical_field] = raw_header
    return reverse


def _value_from_row(raw_row: pd.Series, raw_header: str | None):
    if raw_header is None:
        return None
    return raw_row.get(raw_header)


def _group_chart_rows(chart_rows: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str, str, str], list[dict]] = {}
    for row in chart_rows:
        key = (row["dashboard_name"], row["business_unit"], row["owner"], row["bi_tool"])
        groups.setdefault(key, []).append(row)

    dashboards: list[dict] = []
    chart_counter = 1
    for dash_counter, ((dashboard_name, business_unit, owner, bi_tool), rows) in enumerate(groups.items(), start=1):
        charts = []
        for row in rows:
            chart = {
                "chart_id": f"CHART-{chart_counter:04d}",
                "chart_title": row["chart_title"],
                "chart_type": row["chart_type"],
                "sql_query": row["sql_query"],
                "weekly_views": row["weekly_views"],
                "avg_view_duration_sec": row["avg_view_duration_sec"],
                "render_time_sec": row["render_time_sec"],
                "data_scanned_gb": row["data_scanned_gb"],
                "runs_per_week": row["runs_per_week"],
            }
            charts.append(chart)
            chart_counter += 1

        dashboards.append(
            {
                "dashboard_id": f"DASH-{dash_counter:03d}",
                "dashboard_name": dashboard_name,
                "business_unit": business_unit,
                "owner": owner,
                "bi_tool": bi_tool,
                "charts": charts,
            }
        )
    return dashboards


def _jsonable_sample(row: dict) -> dict:
    sample = {}
    for key, value in row.items():
        if _is_missing(value):
            sample[key] = None
        else:
            parsed_date = _parse_indian_date(value)
            sample[key] = parsed_date if parsed_date is not None else value
    return sample


def _parse_indian_date(value) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not re.fullmatch(r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}", stripped):
        return None
    parsed = pd.to_datetime(stripped, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date().isoformat()


def _coerce_data_scanned_gb(value) -> float:
    if isinstance(value, str) and re.search(r"\bbytes?\b", value, flags=re.IGNORECASE):
        return round(_coerce_number(value) / (1024**3), 4)
    return _coerce_number(value)


def _coerce_number(value, as_int: bool = False):
    if _is_missing(value):
        return 0 if as_int else 0.0
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
    else:
        text = str(value).strip()
        if not text:
            return 0 if as_int else 0.0
        cleaned = re.sub(r"(?i)\b(inr|rs\.?|rupees?)\b", "", text)
        cleaned = cleaned.replace("₹", "")
        cleaned = re.sub(r"[^0-9.\-]", "", cleaned)
        if cleaned.count(".") > 1:
            first, *rest = cleaned.split(".")
            cleaned = first + "." + "".join(rest)
        try:
            number = float(cleaned)
        except ValueError:
            return 0 if as_int else 0.0
    if math.isnan(number) or math.isinf(number):
        return 0 if as_int else 0.0
    if as_int:
        return int(round(number))
    return float(number)


def _clean_text(value) -> str:
    if _is_missing(value):
        return ""
    return str(value).strip()


def _normalize_chart_type(value: str) -> str:
    if not value:
        return "unknown"
    return _normalize_label(value).replace(" ", "_")


def _normalize_label(value: str) -> str:
    # PBIX model columns are often camelCase (visualTitle, QueryText); split word
    # boundaries before lowercasing so they can fuzzy-match spaced aliases.
    split = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", str(value))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", split.lower())).strip()


def _is_missing(value) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False
