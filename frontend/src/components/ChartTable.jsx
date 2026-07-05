import Badge from "./Badge.jsx";
import { inr, num } from "../lib/format.js";

const NUMERIC_COLS = [
  { key: "views", label: "Views", get: (c) => c.weekly_views },
  { key: "cost", label: "Annual ₹", get: (c) => c.cost_analysis.yearly_cost_inr },
  { key: "complexity", label: "Complexity", get: (c) => c.sql_analysis.complexity_score },
  { key: "savings", label: "Savings ₹", get: (c) => c.decision.estimated_yearly_savings_inr },
];

function SortHeader({ col, sort, onSort }) {
  const active = sort === col.key;
  return (
    <th className="px-3 py-2 text-right font-medium">
      <button
        type="button"
        onClick={() => onSort(col.key)}
        className="inline-flex items-center gap-1 hover:text-ink"
        style={{ color: active ? "var(--text-primary)" : "var(--text-muted)" }}
      >
        {col.label}
        <span aria-hidden="true" className="text-[10px]">
          {active ? "▼" : ""}
        </span>
      </button>
    </th>
  );
}

export default function ChartTable({ rows, sort, onSort, onSelect }) {
  return (
    <div className="overflow-x-auto rounded-xl border bg-surface" style={{ borderColor: "var(--border)" }}>
      <table className="w-full min-w-[720px] border-collapse text-sm">
        <thead>
          <tr className="border-b text-xs uppercase tracking-wide text-ink-muted" style={{ borderColor: "var(--border)" }}>
            <th className="px-3 py-2 text-left font-medium">Chart</th>
            <th className="px-3 py-2 text-left font-medium">Dashboard</th>
            <th className="px-3 py-2 text-left font-medium">Tool</th>
            <th className="px-3 py-2 text-left font-medium">Verdict</th>
            {NUMERIC_COLS.map((col) => (
              <SortHeader key={col.key} col={col} sort={sort} onSort={onSort} />
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr
              key={c.chart_id}
              onClick={() => onSelect(c)}
              className="cursor-pointer border-b transition-colors last:border-0 hover:bg-page"
              style={{ borderColor: "var(--border)" }}
            >
              <td className="px-3 py-2">
                <div className="font-medium text-ink">{c.chart_title}</div>
                <div className="text-xs text-ink-muted">{c.chart_id}</div>
              </td>
              <td className="px-3 py-2 text-ink-secondary">
                <div>{c.dashboard_name}</div>
                <div className="text-xs text-ink-muted">{c.owner}</div>
              </td>
              <td className="px-3 py-2 text-ink-secondary">{c.bi_tool}</td>
              <td className="px-3 py-2">
                <Badge verdict={c.decision.verdict} />
              </td>
              <td className="px-3 py-2 text-right text-ink-secondary" style={{ fontVariantNumeric: "tabular-nums" }}>
                {num(c.weekly_views)}
              </td>
              <td className="px-3 py-2 text-right text-ink" style={{ fontVariantNumeric: "tabular-nums" }}>
                {inr(c.cost_analysis.yearly_cost_inr)}
              </td>
              <td className="px-3 py-2 text-right text-ink-secondary" style={{ fontVariantNumeric: "tabular-nums" }}>
                {c.sql_analysis.complexity_score}
              </td>
              <td
                className="px-3 py-2 text-right font-medium"
                style={{
                  fontVariantNumeric: "tabular-nums",
                  color: c.decision.estimated_yearly_savings_inr > 0 ? "var(--status-good)" : "var(--text-muted)",
                }}
              >
                {c.decision.estimated_yearly_savings_inr > 0 ? inr(c.decision.estimated_yearly_savings_inr) : "—"}
              </td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={8} className="px-3 py-8 text-center text-ink-muted">
                No charts match the current filters.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
