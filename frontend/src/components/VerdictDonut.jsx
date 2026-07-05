import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { VERDICT_ORDER, verdictMeta } from "../theme.js";
import { num } from "../lib/format.js";

function DonutTooltip({ active, payload, total }) {
  if (!active || !payload || !payload.length) return null;
  const d = payload[0].payload;
  const pct = total ? Math.round((d.value / total) * 100) : 0;
  return (
    <div className="rounded-lg border bg-surface px-3 py-2 text-sm shadow-sm" style={{ borderColor: "var(--border)" }}>
      <div className="flex items-center gap-2">
        <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: d.color }} />
        <span className="text-ink-secondary">{d.label}</span>
      </div>
      <div className="mt-0.5 font-semibold text-ink" style={{ fontVariantNumeric: "tabular-nums" }}>
        {num(d.value)} charts · {pct}%
      </div>
    </div>
  );
}

export default function VerdictDonut({ counts }) {
  const total = VERDICT_ORDER.reduce((s, k) => s + (counts[k] || 0), 0);
  const data = VERDICT_ORDER.map((k) => {
    const m = verdictMeta(k);
    return { key: k, label: m.label, icon: m.icon, value: counts[k] || 0, color: m.color };
  });

  return (
    <div className="rounded-xl border bg-surface p-4 sm:p-5" style={{ borderColor: "var(--border)" }}>
      <h2 className="text-sm font-semibold text-ink">Recommendation breakdown</h2>
      <p className="mt-0.5 text-xs text-ink-muted">Every analyzed chart, by verdict</p>

      <div className="relative mt-2" style={{ height: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="label"
              cx="50%"
              cy="50%"
              innerRadius={62}
              outerRadius={92}
              paddingAngle={2}
              stroke="var(--surface-1)"
              strokeWidth={2}
              isAnimationActive={false}
            >
              {data.map((d) => (
                <Cell key={d.key} fill={d.color} />
              ))}
            </Pie>
            <Tooltip content={<DonutTooltip total={total} />} />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-3xl font-semibold text-ink">{num(total)}</div>
          <div className="text-xs text-ink-muted">charts</div>
        </div>
      </div>

      {/* Legend — identity via dot + icon + label, never color alone */}
      <ul className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1.5">
        {data.map((d) => (
          <li key={d.key} className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: d.color }} />
              <span className="text-ink-secondary">{d.label}</span>
            </span>
            <span className="font-medium text-ink" style={{ fontVariantNumeric: "tabular-nums" }}>
              {num(d.value)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
