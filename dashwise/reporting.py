"""
Executive report generator.
Turns the pipeline's analysis_results.json into a human-readable markdown
report, sorted by potential savings.
"""
import json
from pathlib import Path


def build_report(data: dict) -> str:
    """Render the analysis dict into a markdown report string."""
    s = data["summary"]
    dashboards = data["dashboards"]

    lines = []
    lines.append("# DashWise AI — BI Dashboard FinOps & UX Audit Report")
    lines.append("")
    lines.append("*Synthetic demo data. Warehouse costs modeled on Redshift ra3.xlplus-equivalent pricing (₹210/node-hour, Mumbai region), reflecting typical Indian enterprise cloud warehouse setups rather than Snowflake.*")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- **Dashboards analyzed:** {s['total_dashboards']}")
    lines.append(f"- **Charts analyzed:** {s['total_charts']}")
    lines.append(f"- **Total annual warehouse compute cost:** ₹{s['total_yearly_cost_inr']:,.0f}")
    savings_pct = (s['total_potential_savings_inr'] / s['total_yearly_cost_inr'] * 100) if s['total_yearly_cost_inr'] else 0
    lines.append(f"- **Total estimated potential savings:** ₹{s['total_potential_savings_inr']:,.0f}/year "
                 f"({savings_pct:.0f}% of current spend)")
    lines.append(f"- **Dashboard health score:** {s['dashboard_health_score']}/100 (% of charts flagged healthy)")
    lines.append("")
    lines.append("### Verdict Breakdown")
    lines.append("")
    lines.append("| Verdict | Count | Meaning |")
    lines.append("|---|---|---|")
    lines.append(f"| 🔴 REMOVE | {s['verdict_counts']['REMOVE']} | Low usage + high cost — replace with static KPI |")
    lines.append(f"| 🟠 OPTIMIZE_SQL | {s['verdict_counts']['OPTIMIZE_SQL']} | Poorly written query driving up cost |")
    lines.append(f"| 🟡 MONITOR | {s['verdict_counts']['MONITOR']} | Low usage, low cost — not urgent |")
    lines.append(f"| 🟢 KEEP | {s['verdict_counts']['KEEP']} | Healthy chart, no action needed |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Dashboard-by-Dashboard Findings")
    lines.append("")

    # Sort dashboards by potential savings, highest first
    sorted_dashboards = sorted(dashboards, key=lambda d: d["dashboard_potential_savings_inr"], reverse=True)

    for dash in sorted_dashboards:
        lines.append(f"### {dash['dashboard_name']} ({dash['dashboard_id']})")
        lines.append(f"**Owner:** {dash['owner']} | **Business Unit:** {dash['business_unit']} | **Tool:** {dash['bi_tool']}")
        lines.append("")
        lines.append(f"Annual cost: ₹{dash['dashboard_yearly_cost_inr']:,.0f} | "
                     f"Potential savings: ₹{dash['dashboard_potential_savings_inr']:,.0f}")
        lines.append("")

        flagged_charts = [c for c in dash["charts"] if c["decision"]["verdict"] != "KEEP"]
        if flagged_charts:
            lines.append("**Flagged charts:**")
            lines.append("")
            for chart in flagged_charts:
                verdict_emoji = {"REMOVE": "🔴", "OPTIMIZE_SQL": "🟠", "MONITOR": "🟡"}.get(chart["decision"]["verdict"], "")
                lines.append(f"- {verdict_emoji} **{chart['chart_title']}** ({chart['chart_id']})")
                lines.append(f"  - {chart['decision']['recommendation']}")
                lines.append(f"  - Weekly views: {chart['weekly_views']} | Render time: {chart['render_time_sec']}s | "
                             f"Data scanned: {chart['data_scanned_gb']}GB | "
                             f"Monthly cost: ₹{chart['cost_analysis']['monthly_cost_inr']:,.0f}")
                lines.append("")
        else:
            lines.append("*All charts on this dashboard are healthy.*")
            lines.append("")

    return "\n".join(lines)


def write_report(input_path, output_path) -> str:
    """Read analysis JSON from ``input_path``, write a markdown report to ``output_path``."""
    input_path = Path(input_path)
    output_path = Path(output_path)

    with input_path.open(encoding="utf-8") as f:
        data = json.load(f)

    report = build_report(data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(report)

    return report
