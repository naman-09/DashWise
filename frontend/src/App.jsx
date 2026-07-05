import { useEffect, useMemo, useState } from "react";
import SummaryCards from "./components/SummaryCards.jsx";
import VerdictDonut from "./components/VerdictDonut.jsx";
import CostByDashboard from "./components/CostByDashboard.jsx";
import FilterBar from "./components/FilterBar.jsx";
import ChartTable from "./components/ChartTable.jsx";
import ChartDetail from "./components/ChartDetail.jsx";
import { VERDICT_ORDER } from "./theme.js";

const SORT_ACCESSORS = {
  savings: (c) => c.decision.estimated_yearly_savings_inr,
  cost: (c) => c.cost_analysis.yearly_cost_inr,
  views: (c) => c.weekly_views,
  complexity: (c) => c.sql_analysis.complexity_score,
};

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
  const [theme, setTheme] = useTheme();

  const [activeVerdicts, setActiveVerdicts] = useState(() => new Set(VERDICT_ORDER));
  const [tool, setTool] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("savings");
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    fetch("analysis_results.json")
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

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

  if (error) {
    return (
      <Shell theme={theme} setTheme={setTheme}>
        <div className="rounded-xl border bg-surface p-8 text-center" style={{ borderColor: "var(--border)" }}>
          <h2 className="text-lg font-semibold text-ink">No analysis data found</h2>
          <p className="mt-2 text-sm text-ink-secondary">
            Couldn't load <code>analysis_results.json</code> ({error}).
          </p>
          <p className="mt-1 text-sm text-ink-secondary">
            Generate it from the repo root with:&nbsp;
            <code className="rounded bg-page px-1.5 py-0.5">dashwise run</code>
          </p>
        </div>
      </Shell>
    );
  }

  if (!data) {
    return (
      <Shell theme={theme} setTheme={setTheme}>
        <div className="animate-pulse text-sm text-ink-muted">Loading analysis…</div>
      </Shell>
    );
  }

  return (
    <Shell theme={theme} setTheme={setTheme}>
      <div className="space-y-4">
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
    </Shell>
  );
}

function Shell({ theme, setTheme, children }) {
  return (
    <div className="min-h-screen">
      <header className="border-b" style={{ borderColor: "var(--border)" }}>
        <div className="mx-auto flex max-w-6xl items-start justify-between gap-4 px-4 py-5">
          <div>
            <h1 className="text-xl font-semibold text-ink">DashWise AI</h1>
            <p className="text-sm text-ink-secondary">BI Dashboard FinOps &amp; Usage Audit</p>
            <p className="mt-1 text-xs text-ink-muted">
              Synthetic demo data · warehouse cost modeled on Redshift ra3.xlplus (₹210/node-hour, Mumbai)
            </p>
          </div>
          <button
            type="button"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="rounded-lg border px-2.5 py-1.5 text-sm text-ink-secondary"
            style={{ borderColor: "var(--border)" }}
            aria-label="Toggle light/dark theme"
          >
            {theme === "dark" ? "☀ Light" : "☾ Dark"}
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
