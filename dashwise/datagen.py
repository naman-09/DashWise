"""
Synthetic data generator.

Generates synthetic but realistic data for an Indian mid-size enterprise:
- 12 dashboards, each with 3-6 charts
- Each chart backed by a SQL query (some good, some bad)
- Clickstream/usage logs (views, time spent)
- Warehouse cost data (₹ per query run, based on Redshift-style ra3.xlplus
  on-demand pricing converted to INR, ~₹210/hour per node, typical Indian
  mid-size warehouse: 2-4 node cluster)

Deterministic for a given ``seed`` so the committed sample is reproducible.
"""
import json
import random
from pathlib import Path

BUSINESS_UNITS = ["Sales", "Finance", "Supply Chain", "HR", "Marketing", "Operations"]
OWNERS = ["Priya Sharma", "Rahul Mehta", "Ananya Iyer", "Vikram Nair", "Sneha Gupta", "Arjun Rao"]

# Realistic SQL query templates - mix of well-written and poorly-written
GOOD_QUERIES = [
    """SELECT region, SUM(revenue) as total_revenue
FROM fact_sales
WHERE order_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY region
ORDER BY total_revenue DESC""",

    """SELECT product_category, COUNT(DISTINCT customer_id) as unique_customers
FROM fact_orders o
JOIN dim_product p ON o.product_id = p.product_id
WHERE o.order_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY product_category""",

    """SELECT month, dept_name, SUM(headcount) as total_headcount
FROM fact_hr_monthly
WHERE year = 2026
GROUP BY month, dept_name""",
]

BAD_QUERIES = [
    """SELECT *
FROM fact_sales fs, dim_customer dc, dim_product dp, dim_region dr, dim_date dd
WHERE fs.customer_id = dc.customer_id
AND fs.product_id = dp.product_id
AND fs.region_id = dr.region_id
AND fs.date_id = dd.date_id""",

    """SELECT c.*, o.*, p.*
FROM customers c
CROSS JOIN orders o
LEFT JOIN products p ON o.product_id = p.product_id
WHERE c.signup_date > '2020-01-01'""",

    """WITH cte1 AS (SELECT * FROM fact_transactions WHERE txn_date >= '2024-01-01'),
cte2 AS (SELECT * FROM fact_transactions WHERE txn_date >= '2024-01-01'),
cte3 AS (SELECT customer_id, SUM(amount) FROM cte1 GROUP BY customer_id)
SELECT * FROM cte1 c1
JOIN cte2 c2 ON c1.txn_id = c2.txn_id
JOIN cte3 c3 ON c1.customer_id = c3.customer_id""",

    """SELECT * FROM fact_web_events
WHERE event_type = 'click'
ORDER BY event_timestamp DESC""",

    """SELECT s.*, i.*
FROM fact_shipments s, dim_inventory i
WHERE s.warehouse_id = i.warehouse_id
AND s.status != 'DELIVERED'
GROUP BY s.shipment_id""",
]

CHART_TYPES = ["bar_chart", "line_chart", "pie_chart", "kpi_card", "table", "heatmap", "scatter_plot"]
CHART_TITLES = [
    "Revenue by Region", "Monthly Active Customers", "Headcount Trend",
    "Order Fulfillment Rate", "Customer Churn by Segment", "Warehouse Utilization",
    "Top 10 SKUs by Volume", "Marketing Spend vs Conversion", "Support Ticket Backlog",
    "Inventory Ageing Report", "Employee Attrition by Dept", "Freight Cost Trend",
    "Lead Funnel Conversion", "Vendor Payment Ageing", "Plant-wise Production Output",
]


def generate_dashboards(n_dashboards: int = 12, seed: int = 42) -> list:
    """Build the synthetic dashboard estate. Deterministic for a given seed."""
    random.seed(seed)
    dashboards = []
    chart_id_counter = 1

    for d_idx in range(1, n_dashboards + 1):
        n_charts = random.randint(3, 6)
        dashboard = {
            "dashboard_id": f"DASH-{d_idx:03d}",
            "dashboard_name": f"{random.choice(BUSINESS_UNITS)} Dashboard {d_idx}",
            "business_unit": random.choice(BUSINESS_UNITS),
            "owner": random.choice(OWNERS),
            "bi_tool": random.choice(["Power BI", "Power BI", "Tableau"]),  # Power BI weighted higher (Indian enterprise reality)
            "charts": [],
        }

        for c_idx in range(n_charts):
            is_bad_query = random.random() < 0.55  # 55% of queries are poorly written (realistic dashboard sprawl)
            query = random.choice(BAD_QUERIES) if is_bad_query else random.choice(GOOD_QUERIES)

            # Usage: skew low - realistic "dashboard sprawl" means most charts are barely viewed
            weekly_views = int(random.expovariate(1 / 25))  # exponential distribution, mean ~25
            weekly_views = min(weekly_views, 500)
            avg_view_duration_sec = round(random.uniform(2, 45), 1)

            # Render time correlates with query badness
            base_render = random.uniform(1, 4) if not is_bad_query else random.uniform(8, 28)
            render_time_sec = round(base_render, 1)

            # Data scanned correlates with query badness (in GB)
            data_scanned_gb = round(random.uniform(0.5, 8) if not is_bad_query else random.uniform(40, 900), 1)

            chart = {
                "chart_id": f"CHART-{chart_id_counter:04d}",
                "chart_title": random.choice(CHART_TITLES),
                "chart_type": random.choice(CHART_TYPES),
                "sql_query": query,
                "weekly_views": weekly_views,
                "avg_view_duration_sec": avg_view_duration_sec,
                "render_time_sec": render_time_sec,
                "data_scanned_gb": data_scanned_gb,
                "runs_per_week": random.choice([7, 14, 21, 168]),  # daily, 2x/day, 3x/day, hourly refresh
            }
            dashboard["charts"].append(chart)
            chart_id_counter += 1

        dashboards.append(dashboard)

    return dashboards


def generate(output_path, n_dashboards: int = 12, seed: int = 42) -> list:
    """Generate the dashboard estate and write it to ``output_path`` as JSON."""
    data = generate_dashboards(n_dashboards=n_dashboards, seed=seed)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data
