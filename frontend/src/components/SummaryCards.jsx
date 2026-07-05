import { inr, num } from "../lib/format.js";
import { STATUS } from "../theme.js";

function Card({ children }) {
  return (
    <div className="rounded-xl border bg-surface p-4 sm:p-5" style={{ borderColor: "var(--border)" }}>
      {children}
    </div>
  );
}

function Label({ children }) {
  return <div className="text-xs font-medium uppercase tracking-wide text-ink-muted">{children}</div>;
}

// Health meter: fill carries severity, track is a recessive tint of the same ink.
function HealthMeter({ score }) {
  const color = score >= 70 ? STATUS.good : score >= 40 ? STATUS.warning : STATUS.critical;
  return (
    <div className="mt-3">
      <div className="h-2 w-full overflow-hidden rounded-full" style={{ backgroundColor: "var(--gridline)" }}>
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${Math.max(0, Math.min(100, score))}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export default function SummaryCards({ summary }) {
  const spend = summary.total_yearly_cost_inr;
  const savings = summary.total_potential_savings_inr;
  const savingsPct = spend ? Math.round((savings / spend) * 100) : 0;
  const flagged = summary.total_charts - (summary.verdict_counts.KEEP || 0);

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <Card>
        <Label>Annual warehouse spend</Label>
        <div className="mt-2 text-3xl font-semibold text-ink">{inr(spend)}</div>
        <div className="mt-1 text-sm text-ink-secondary">
          across {summary.total_dashboards} dashboards · {summary.total_charts} charts
        </div>
      </Card>

      <Card>
        <Label>Potential savings / year</Label>
        <div className="mt-2 text-3xl font-semibold" style={{ color: STATUS.good }}>
          {inr(savings)}
        </div>
        <div className="mt-1 text-sm text-ink-secondary">{savingsPct}% of current spend</div>
      </Card>

      <Card>
        <Label>Dashboard health score</Label>
        <div className="mt-2 text-3xl font-semibold text-ink">
          {summary.dashboard_health_score}
          <span className="text-lg text-ink-muted">/100</span>
        </div>
        <HealthMeter score={summary.dashboard_health_score} />
      </Card>

      <Card>
        <Label>Charts flagged for action</Label>
        <div className="mt-2 text-3xl font-semibold text-ink">
          {num(flagged)}
          <span className="text-lg text-ink-muted"> / {summary.total_charts}</span>
        </div>
        <div className="mt-1 text-sm text-ink-secondary">
          {summary.verdict_counts.REMOVE} remove · {summary.verdict_counts.OPTIMIZE_SQL} optimize ·{" "}
          {summary.verdict_counts.MONITOR} monitor
        </div>
      </Card>
    </div>
  );
}
