import { useEffect, useMemo, useState } from "react";
import SummaryCards from "./components/SummaryCards.jsx";
import VerdictDonut from "./components/VerdictDonut.jsx";
import CostByDashboard from "./components/CostByDashboard.jsx";
import FilterBar from "./components/FilterBar.jsx";
import ChartTable from "./components/ChartTable.jsx";
import ChartDetail from "./components/ChartDetail.jsx";
import { VERDICT_ORDER } from "./theme.js";

const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

const SORT_ACCESSORS = {
  savings: (c) => c.decision.estimated_yearly_savings_inr,
  cost: (c) => c.cost_analysis.yearly_cost_inr,
  views: (c) => c.weekly_views,
  complexity: (c) => c.sql_analysis.complexity_score,
};

function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}

function useTheme() {
  const [theme, setTheme] = useState(() =>
    window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
  );
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);
  return [theme, setTheme];
}

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [ingestionReport, setIngestionReport] = useState(null);
  const [analysisMode, setAnalysisMode] = useState(null);
  const [theme, setTheme] = useTheme();

  const [activeVerdicts, setActiveVerdicts] = useState(() => new Set(VERDICT_ORDER));
  const [tool, setTool] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("savings");
  const [selected, setSelected] = useState(null);

  async function readApiError(response) {
    try {
      const payload = await response.json();
      if (Array.isArray(payload.warnings) && payload.warnings.length) {
        return payload.warnings.join(" ");
      }
      if (payload.detail) {
        return typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail);
      }
    } catch {
      // Fall through to the generic status message.
    }
    return `HTTP ${response.status}`;
  }

  async function handleResponse(response) {
    if (!response.ok) {
      throw new Error(await readApiError(response));
    }
    return response.json();
  }

  async function analyzeFile(file) {
    const form = new FormData();
    form.append("file", file);
    setLoading(true);
    setError(null);
    setData(null);
    setIngestionReport(null);
    setAnalysisMode(null);
    setSelected(null);
    try {
      const payload = await handleResponse(
        await fetch(apiUrl("/analyze"), {
          method: "POST",
          body: form,
        })
      );
      setData(payload);
      setIngestionReport(payload.ingestion_report || null);
      setAnalysisMode("upload");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadSampleData() {
    setLoading(true);
    setError(null);
    setData(null);
    setIngestionReport(null);
    setAnalysisMode(null);
    setSelected(null);
    try {
      const payload = await handleResponse(
        await fetch(apiUrl("/analyze/sample"), {
          method: "POST",
        })
      );
      setData(payload);
      setIngestionReport(null);
      setAnalysisMode("sample");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // Flatten every chart with its parent dashboard context.
  const rows = useMemo(() => {
    if (!data) return [];
    const out = [];
    for (const d of data.dashboards) {
      for (const c of d.charts) {
        out.push({
          ...c,
          dashboard_name: d.dashboard_name,
          dashboard_id: d.dashboard_id,
          owner: d.owner,
          bi_tool: d.bi_tool,
          business_unit: d.business_unit,
        });
      }
    }
    return out;
  }, [data]);

  const tools = useMemo(() => [...new Set(rows.map((r) => r.bi_tool))].sort(), [rows]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    const accessor = SORT_ACCESSORS[sort] || SORT_ACCESSORS.savings;
    return rows
      .filter((c) => activeVerdicts.has(c.decision.verdict))
      .filter((c) => !tool || c.bi_tool === tool)
      .filter((c) => {
        if (!q) return true;
        return (
          c.chart_title.toLowerCase().includes(q) ||
          c.dashboard_name.toLowerCase().includes(q) ||
          c.owner.toLowerCase().includes(q)
        );
      })
      .sort((a, b) => accessor(b) - accessor(a));
  }, [rows, activeVerdicts, tool, search, sort]);

  const toggleVerdict = (v) =>
    setActiveVerdicts((prev) => {
      const next = new Set(prev);
      next.has(v) ? next.delete(v) : next.add(v);
      return next;
    });

  const controls = <AnalysisControls loading={loading} onFile={analyzeFile} onSample={loadSampleData} />;

  let content;
  if (error) {
    content = (
      <div className="space-y-4">
        {controls}
        <div className="rounded-xl border bg-surface p-8 text-center" style={{ borderColor: "var(--border)" }}>
          <h2 className="text-lg font-semibold text-ink">No analysis data found</h2>
          <p className="mt-2 text-sm text-ink-secondary">The API could not complete the analysis ({error}).</p>
        </div>
      </div>
    );
  } else if (loading) {
    content = (
      <div className="space-y-4">
        {controls}
        <div className="animate-pulse text-sm text-ink-muted">Loading analysis...</div>
      </div>
    );
  } else if (!data) {
    content = (
      <div className="space-y-4">
        {controls}
        <div className="rounded-xl border bg-surface p-8 text-center" style={{ borderColor: "var(--border)" }}>
          <h2 className="text-lg font-semibold text-ink">No analysis data found</h2>
          <p className="mt-2 text-sm text-ink-secondary">Upload a CSV/XLSX/PBIX export or load sample data to begin.</p>
        </div>
      </div>
    );
  } else {
    content = (
      <>
        <div className="space-y-4">
          {controls}
          {analysisMode === "upload" && <IngestionReport report={ingestionReport} />}

          <SummaryCards summary={data.summary} />

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <VerdictDonut counts={data.summary.verdict_counts} />
            <CostByDashboard dashboards={data.dashboards} />
          </div>

          <FilterBar
            activeVerdicts={activeVerdicts}
            onToggleVerdict={toggleVerdict}
            tool={tool}
            onToolChange={setTool}
            tools={tools}
            search={search}
            onSearch={setSearch}
            sort={sort}
            onSort={setSort}
            resultCount={filtered.length}
          />

          <ChartTable rows={filtered} sort={sort} onSort={setSort} onSelect={setSelected} />
        </div>

        <ChartDetail chart={selected} onClose={() => setSelected(null)} />
      </>
    );
  }

  return (
    <Shell theme={theme} setTheme={setTheme} analysisMode={analysisMode}>
      {content}
    </Shell>
  );
}

function AnalysisControls({ loading, onFile, onSample }) {
  const [fileName, setFileName] = useState("");

  function handleFileChange(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    onFile(file);
    event.target.value = "";
  }

  return (
    <section className="rounded-xl border bg-surface p-4 sm:p-5" style={{ borderColor: "var(--border)" }}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-sm font-semibold text-ink">Analyze dashboard export</div>
          <div className="mt-1 text-sm text-ink-secondary">
            {fileName ? `Last upload: ${fileName}` : "Upload a CSV/XLSX/PBIX file or run the generated sample analysis."}
          </div>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <label
            className="inline-flex cursor-pointer items-center justify-center rounded-lg border px-3 py-2 text-sm font-medium text-ink-secondary"
            style={{ borderColor: "var(--border)" }}
          >
            <input
              type="file"
              accept=".csv,.xlsx,.pbix,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream"
              className="sr-only"
              disabled={loading}
              onChange={handleFileChange}
            />
            Upload CSV/XLSX/PBIX
          </label>
          <button
            type="button"
            onClick={onSample}
            disabled={loading}
            className="rounded-lg border px-3 py-2 text-sm font-medium text-ink-secondary disabled:cursor-not-allowed disabled:opacity-60"
            style={{ borderColor: "var(--border)" }}
          >
            Load sample data
          </button>
        </div>
      </div>
    </section>
  );
}

function IngestionReport({ report }) {
  if (!report) return null;
  const warnings = report.warnings || [];

  return (
    <details className="rounded-xl border bg-surface p-4 text-sm" style={{ borderColor: "var(--border)" }} open>
      <summary className="cursor-pointer font-semibold text-ink">Ingestion report</summary>
      <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-ink-muted">Rows processed</div>
          <div className="mt-1 text-lg font-semibold text-ink">{report.rows_processed ?? 0}</div>
        </div>
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-ink-muted">Rows dropped</div>
          <div className="mt-1 text-lg font-semibold text-ink">{report.rows_dropped ?? 0}</div>
        </div>
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-ink-muted">Mapping source</div>
          <div className="mt-1 text-lg font-semibold text-ink">{report.mapping_source || "unknown"}</div>
        </div>
      </div>
      {warnings.length > 0 && (
        <div className="mt-3">
          <div className="text-xs font-medium uppercase tracking-wide text-ink-muted">Warnings</div>
          <ul className="mt-2 space-y-1 text-ink-secondary">
            {warnings.map((warning, index) => (
              <li key={`${warning}-${index}`}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
    </details>
  );
}

function Shell({ theme, setTheme, analysisMode, children }) {
  const subtitle =
    analysisMode === "sample"
      ? "Sample demo data - warehouse cost modeled on Redshift ra3.xlplus (INR 210/node-hour, Mumbai)"
      : "Live analysis - warehouse cost modeled on Redshift ra3.xlplus (INR 210/node-hour, Mumbai)";

  return (
    <div className="min-h-screen">
      <header className="border-b" style={{ borderColor: "var(--border)" }}>
        <div className="mx-auto flex max-w-6xl items-start justify-between gap-4 px-4 py-5">
          <div>
            <h1 className="text-xl font-semibold text-ink">DashWise AI</h1>
            <p className="text-sm text-ink-secondary">BI Dashboard FinOps &amp; Usage Audit</p>
            <p className="mt-1 text-xs text-ink-muted">{subtitle}</p>
          </div>
          <button
            type="button"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="rounded-lg border px-2.5 py-1.5 text-sm text-ink-secondary"
            style={{ borderColor: "var(--border)" }}
            aria-label="Toggle light/dark theme"
          >
            {theme === "dark" ? "Light" : "Dark"}
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
