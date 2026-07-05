import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LabelList,
  Cell,
} from "recharts";
import { inr, inrCompact } from "../lib/format.js";
import { SERIES_BLUE } from "../theme.js";

function CostTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) return null;
  const d = payload[0].payload;
  return (
    <div className="rounded-lg border bg-surface px-3 py-2 text-sm shadow-sm" style={{ borderColor: "var(--border)" }}>
      <div className="text-ink-secondary">{d.name}</div>
      <div className="mt-0.5 font-semibold text-ink">{inr(d.cost)} / year</div>
      <div className="text-xs text-ink-muted">Potential savings {inr(d.savings)}</div>
    </div>
  );
}

export default function CostByDashboard({ dashboards, topN = 8 }) {
  const data = [...dashboards]
    .map((d) => ({
      name: d.dashboard_name,
      id: d.dashboard_id,
      cost: d.dashboard_yearly_cost_inr,
      savings: d.dashboard_potential_savings_inr,
    }))
    .sort((a, b) => b.cost - a.cost)
    .slice(0, topN);

  return (
    <div className="rounded-xl border bg-surface p-4 sm:p-5" style={{ borderColor: "var(--border)" }}>
      <h2 className="text-sm font-semibold text-ink">Annual cost by dashboard</h2>
      <p className="mt-0.5 text-xs text-ink-muted">Top {data.length} by warehouse compute spend</p>

      <div className="mt-3" style={{ height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 56, bottom: 4, left: 8 }}>
            <CartesianGrid horizontal={false} stroke="var(--gridline)" strokeWidth={1} />
            <XAxis
              type="number"
              tickFormatter={inrCompact}
              tick={{ fill: "var(--text-muted)", fontSize: 11 }}
              axisLine={{ stroke: "var(--baseline)" }}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={132}
              tick={{ fill: "var(--text-secondary)", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CostTooltip />} cursor={{ fill: "var(--gridline)", opacity: 0.4 }} />
            <Bar dataKey="cost" fill={SERIES_BLUE} barSize={18} radius={[0, 4, 4, 0]} isAnimationActive={false}>
              {data.map((d) => (
                <Cell key={d.id} fill={SERIES_BLUE} />
              ))}
              <LabelList
                dataKey="cost"
                position="right"
                formatter={inrCompact}
                style={{ fill: "var(--text-secondary)", fontSize: 11, fontVariantNumeric: "tabular-nums" }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
