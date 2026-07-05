import { VERDICT_ORDER, verdictMeta } from "../theme.js";

const SORTS = [
  { key: "savings", label: "Potential savings" },
  { key: "cost", label: "Annual cost" },
  { key: "views", label: "Weekly views" },
  { key: "complexity", label: "SQL complexity" },
];

export default function FilterBar({
  activeVerdicts,
  onToggleVerdict,
  tool,
  onToolChange,
  tools,
  search,
  onSearch,
  sort,
  onSort,
  resultCount,
}) {
  return (
    <div
      className="flex flex-col gap-3 rounded-xl border bg-surface p-3 sm:flex-row sm:flex-wrap sm:items-center"
      style={{ borderColor: "var(--border)" }}
    >
      {/* Verdict toggles */}
      <div className="flex flex-wrap items-center gap-1.5">
        {VERDICT_ORDER.map((v) => {
          const m = verdictMeta(v);
          const on = activeVerdicts.has(v);
          return (
            <button
              key={v}
              type="button"
              onClick={() => onToggleVerdict(v)}
              aria-pressed={on}
              className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors"
              style={{
                borderColor: on ? m.color : "var(--border)",
                backgroundColor: on ? m.color + "1a" : "transparent",
                color: "var(--text-secondary)",
              }}
            >
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: m.color }} />
              {m.label}
            </button>
          );
        })}
      </div>

      <div className="hidden h-6 w-px bg-line sm:block" />

      {/* Search */}
      <input
        type="search"
        value={search}
        onChange={(e) => onSearch(e.target.value)}
        placeholder="Search chart, dashboard, owner…"
        className="min-w-0 flex-1 rounded-lg border bg-transparent px-3 py-1.5 text-sm text-ink placeholder:text-ink-muted focus:outline-none focus:ring-1"
        style={{ borderColor: "var(--border)" }}
      />

      {/* Tool filter */}
      <select
        value={tool}
        onChange={(e) => onToolChange(e.target.value)}
        className="rounded-lg border bg-transparent px-2.5 py-1.5 text-sm text-ink-secondary focus:outline-none"
        style={{ borderColor: "var(--border)" }}
        aria-label="Filter by BI tool"
      >
        <option value="">All tools</option>
        {tools.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>

      {/* Sort */}
      <select
        value={sort}
        onChange={(e) => onSort(e.target.value)}
        className="rounded-lg border bg-transparent px-2.5 py-1.5 text-sm text-ink-secondary focus:outline-none"
        style={{ borderColor: "var(--border)" }}
        aria-label="Sort charts"
      >
        {SORTS.map((s) => (
          <option key={s.key} value={s.key}>
            Sort: {s.label}
          </option>
        ))}
      </select>

      <span className="text-xs text-ink-muted sm:ml-auto">{resultCount} charts</span>
    </div>
  );
}
