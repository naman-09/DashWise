import Badge from "./Badge.jsx";
import { inr, num } from "../lib/format.js";

function Metric({ label, value }) {
  return (
    <div>
      <div className="text-xs text-ink-muted">{label}</div>
      <div className="mt-0.5 text-sm font-medium text-ink" style={{ fontVariantNumeric: "tabular-nums" }}>
        {value}
      </div>
    </div>
  );
}

// Slide-over drill-down panel for a single chart.
export default function ChartDetail({ chart, onClose }) {
  if (!chart) return null;
  const { sql_analysis: sql, cost_analysis: cost, decision } = chart;

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      {/* scrim */}
      <button
        type="button"
        aria-label="Close details"
        onClick={onClose}
        className="absolute inset-0 bg-black/40"
      />
      <aside
        className="relative z-50 flex h-full w-full max-w-md flex-col overflow-y-auto border-l bg-surface shadow-xl"
        style={{ borderColor: "var(--border)" }}
        role="dialog"
        aria-label={`Details for ${chart.chart_title}`}
      >
        <div className="flex items-start justify-between gap-3 border-b p-4" style={{ borderColor: "var(--border)" }}>
          <div>
            <div className="flex items-center gap-2">
              <Badge verdict={decision.verdict} size="lg" />
              <span className="text-xs text-ink-muted">{chart.chart_id}</span>
            </div>
            <h3 className="mt-1.5 text-lg font-semibold text-ink">{chart.chart_title}</h3>
            <p className="text-sm text-ink-secondary">
              {chart.dashboard_name} · {chart.owner} · {chart.bi_tool}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border px-2 py-1 text-sm text-ink-secondary"
            style={{ borderColor: "var(--border)" }}
          >
            Close
          </button>
        </div>

        <div className="space-y-5 p-4">
          {/* Recommendation */}
          <section>
            <h4 className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Recommendation</h4>
            <p className="mt-1.5 text-sm leading-relaxed text-ink">{decision.recommendation}</p>
            {decision.estimated_yearly_savings_inr > 0 && (
              <p className="mt-2 text-sm font-medium" style={{ color: "var(--status-good)" }}>
                Est. savings {inr(decision.estimated_yearly_savings_inr)} / year
              </p>
            )}
          </section>

          {/* Metrics grid */}
          <section className="grid grid-cols-2 gap-3">
            <Metric label="Weekly views" value={num(chart.weekly_views)} />
            <Metric label="Runs / week" value={num(chart.runs_per_week)} />
            <Metric label="Render time" value={`${chart.render_time_sec}s`} />
            <Metric label="Data scanned" value={`${num(chart.data_scanned_gb)} GB`} />
            <Metric label="Monthly cost" value={inr(cost.monthly_cost_inr)} />
            <Metric label="Annual cost" value={inr(cost.yearly_cost_inr)} />
            <Metric label="Nodes engaged" value={cost.nodes_engaged} />
            <Metric label="SQL complexity" value={`${sql.complexity_score}/100`} />
          </section>

          {/* SQL issues */}
          <section>
            <h4 className="text-xs font-semibold uppercase tracking-wide text-ink-muted">
              SQL findings ({sql.issues.length})
            </h4>
            <ul className="mt-1.5 space-y-1.5">
              {sql.issues.map((issue, i) => (
                <li key={i} className="flex gap-2 text-sm text-ink-secondary">
                  <span aria-hidden="true" className="text-ink-muted">
                    –
                  </span>
                  <span>{issue}</span>
                </li>
              ))}
            </ul>
          </section>

          {/* SQL source */}
          <section>
            <h4 className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Query</h4>
            <pre
              className="mt-1.5 overflow-x-auto rounded-lg border p-3 text-xs leading-relaxed text-ink-secondary"
              style={{ borderColor: "var(--border)", backgroundColor: "var(--page)" }}
            >
              <code>{chart.sql_query}</code>
            </pre>
          </section>
        </div>
      </aside>
    </div>
  );
}
