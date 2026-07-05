"""
FinOps Cost Agent
Computes warehouse compute cost in INR for each chart's underlying query,
based on a Redshift/on-prem-style pricing model common in Indian enterprises
(rather than assuming Snowflake, which is less common in Indian companies).

Pricing model (illustrative, documented assumption):
- Cluster: 2-node ra3.xlplus-equivalent, ~₹210/hour per node on-demand (INR,
  approximate AWS Mumbai region pricing after conversion)
- Cost per query ≈ (render_time_sec / 3600) * node_hour_rate * nodes_engaged
- nodes_engaged scales up with data_scanned_gb (more data = more nodes doing work)
"""

NODE_HOURLY_RATE_INR = 210  # ₹ per node-hour, Redshift ra3.xlplus-equivalent, Mumbai region
BASE_NODES = 2


def estimate_nodes_engaged(data_scanned_gb: float) -> float:
    """More data scanned = more of the cluster's nodes doing work on that query."""
    if data_scanned_gb < 5:
        return 0.5
    elif data_scanned_gb < 50:
        return 1.0
    elif data_scanned_gb < 200:
        return 2.0
    else:
        return 3.5


def compute_chart_cost(render_time_sec: float, data_scanned_gb: float, runs_per_week: int) -> dict:
    nodes_engaged = estimate_nodes_engaged(data_scanned_gb)
    cost_per_run_inr = (render_time_sec / 3600) * NODE_HOURLY_RATE_INR * nodes_engaged

    weekly_cost_inr = cost_per_run_inr * runs_per_week
    monthly_cost_inr = weekly_cost_inr * 4.33  # avg weeks/month
    yearly_cost_inr = weekly_cost_inr * 52

    return {
        "cost_per_run_inr": round(cost_per_run_inr, 2),
        "weekly_cost_inr": round(weekly_cost_inr, 2),
        "monthly_cost_inr": round(monthly_cost_inr, 2),
        "yearly_cost_inr": round(yearly_cost_inr, 2),
        "nodes_engaged": nodes_engaged,
    }


if __name__ == "__main__":
    result = compute_chart_cost(render_time_sec=18.5, data_scanned_gb=480, runs_per_week=168)
    import json
    print(json.dumps(result, indent=2))
