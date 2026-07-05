import { verdictMeta } from "../theme.js";

// A verdict badge: colored dot + icon + text label. Identity never rests on
// color alone (dataviz status-palette rule).
export default function Badge({ verdict, size = "sm" }) {
  const m = verdictMeta(verdict);
  const pad = size === "lg" ? "px-2.5 py-1 text-sm" : "px-2 py-0.5 text-xs";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${pad}`}
      style={{ borderColor: "var(--border)" }}
    >
      <span
        aria-hidden="true"
        className="inline-block h-2 w-2 rounded-full"
        style={{ backgroundColor: m.color }}
      />
      <span className="text-ink-secondary whitespace-nowrap">{m.label}</span>
    </span>
  );
}
