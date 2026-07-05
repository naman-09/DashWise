"""
DashWise AI - Main Pipeline
Orchestrates: SQL Agent -> Cost Agent -> Decision Agent
across all dashboards/charts, then produces final report data.
"""
import json
from pathlib import Path

from dashwise.agents.cost_agent import compute_chart_cost
from dashwise.agents.decision_agent import classify_chart
from dashwise.agents.sql_agent import analyze_query


def analyze(dashboards: list) -> dict:
    """Run the three agents over every chart and roll up an estate-wide summary.

    Pure function: takes the raw dashboards list, returns the analysis dict.
    """
    results = []
    total_yearly_cost = 0
    total_potential_savings = 0
    verdict_counts = {"REMOVE": 0, "OPTIMIZE_SQL": 0, "MONITOR": 0, "KEEP": 0}

    for dashboard in dashboards:
        dash_result = {
            "dashboard_id": dashboard["dashboard_id"],
            "dashboard_name": dashboard["dashboard_name"],
            "business_unit": dashboard["business_unit"],
            "owner": dashboard["owner"],
            "bi_tool": dashboard["bi_tool"],
            "charts": [],
            "dashboard_yearly_cost_inr": 0,
            "dashboard_potential_savings_inr": 0,
        }

        for chart in dashboard["charts"]:
            sql_analysis = analyze_query(chart["sql_query"])
            cost_analysis = compute_chart_cost(
                render_time_sec=chart["render_time_sec"],
                data_scanned_gb=chart["data_scanned_gb"],
                runs_per_week=chart["runs_per_week"],
            )
            chart_with_owner = {**chart, "owner": dashboard["owner"]}
            decision = classify_chart(chart_with_owner, sql_analysis, cost_analysis)

            chart_result = {
                **chart,
                "sql_analysis": sql_analysis,
                "cost_analysis": cost_analysis,
                "decision": decision,
            }
            dash_result["charts"].append(chart_result)
            dash_result["dashboard_yearly_cost_inr"] += cost_analysis["yearly_cost_inr"]
            dash_result["dashboard_potential_savings_inr"] += decision["estimated_yearly_savings_inr"]

            total_yearly_cost += cost_analysis["yearly_cost_inr"]
            total_potential_savings += decision["estimated_yearly_savings_inr"]
            verdict_counts[decision["verdict"]] += 1

        dash_result["dashboard_yearly_cost_inr"] = round(dash_result["dashboard_yearly_cost_inr"], 2)
        dash_result["dashboard_potential_savings_inr"] = round(dash_result["dashboard_potential_savings_inr"], 2)
        results.append(dash_result)

    total_charts = sum(len(d["charts"]) for d in dashboards)
    health_score = round(100 * (verdict_counts["KEEP"] / total_charts), 1) if total_charts else 0

    summary = {
        "total_dashboards": len(dashboards),
        "total_charts": total_charts,
        "total_yearly_cost_inr": round(total_yearly_cost, 2),
        "total_potential_savings_inr": round(total_potential_savings, 2),
        "verdict_counts": verdict_counts,
        "dashboard_health_score": health_score,
    }

    return {"summary": summary, "dashboards": results}


def run(input_path, output_path) -> dict:
    """Load dashboards from ``input_path``, analyze, and write results to ``output_path``."""
    input_path = Path(input_path)
    output_path = Path(output_path)

    with input_path.open(encoding="utf-8") as f:
        dashboards = json.load(f)

    output = analyze(dashboards)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    return output
