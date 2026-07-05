// Verdict metadata — the one place that maps a verdict to its status color,
// label, and icon. Status colors are the dataviz skill's fixed status palette
// (not themed; they clear 3:1 on both light and dark surfaces) and always ride
// with an icon + label so meaning is never carried by color alone.
//
// Ordered most-severe first for legends and sorting.

export const STATUS = {
  good: "#0ca30c",
  warning: "#fab219",
  serious: "#ec835a",
  critical: "#d03b3b",
};

export const VERDICTS = {
  REMOVE: { key: "REMOVE", label: "Remove", color: STATUS.critical, icon: "⛔", blurb: "Low usage + high cost" },
  OPTIMIZE_SQL: { key: "OPTIMIZE_SQL", label: "Optimize SQL", color: STATUS.serious, icon: "🛠", blurb: "Costly, poorly written query" },
  MONITOR: { key: "MONITOR", label: "Monitor", color: STATUS.warning, icon: "👁", blurb: "Low usage, low cost" },
  KEEP: { key: "KEEP", label: "Keep", color: STATUS.good, icon: "✓", blurb: "Healthy — no action" },
};

// Display / sort order, most severe first.
export const VERDICT_ORDER = ["REMOVE", "OPTIMIZE_SQL", "MONITOR", "KEEP"];

export function verdictMeta(v) {
  return VERDICTS[v] || { key: v, label: v, color: "var(--text-muted)", icon: "•", blurb: "" };
}

// Single-hue blue for cost magnitude (themed via CSS variable).
export const SERIES_BLUE = "var(--series-1)";
