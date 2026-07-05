"""
Decision / Recommendation Agent
Combines SQL Quality Agent + FinOps Cost Agent + usage data to produce
a per-chart verdict and an estimated savings figure if action is taken.
"""

# Thresholds (documented, tunable assumptions)
LOW_USAGE_WEEKLY_VIEWS = 10          # below this = "barely viewed"
HIGH_COST_MONTHLY_INR = 1500          # above this = "expensive"
HIGH_COMPLEXITY_SCORE = 50            # above this = "poorly written query"


def classify_chart(chart: dict, sql_analysis: dict, cost_analysis: dict) -> dict:
    weekly_views = chart["weekly_views"]
    monthly_cost = cost_analysis["monthly_cost_inr"]
    yearly_cost = cost_analysis["yearly_cost_inr"]
    complexity = sql_analysis["complexity_score"]

    low_usage = weekly_views < LOW_USAGE_WEEKLY_VIEWS
    high_cost = monthly_cost > HIGH_COST_MONTHLY_INR
    poor_sql = complexity > HIGH_COMPLEXITY_SCORE

    if low_usage and high_cost:
        verdict = "REMOVE"
        recommendation = (
            f"Chart '{chart['chart_title']}' is viewed only {weekly_views}x/week but costs "
            f"₹{monthly_cost:,.0f}/month (₹{yearly_cost:,.0f}/year) in warehouse compute. "
            f"Recommend replacing with a static pre-aggregated KPI card refreshed daily instead of "
            f"on every dashboard load."
        )
        estimated_savings_inr = round(yearly_cost * 0.85, 0)  # assume 85% savings from static replacement

    elif high_cost and poor_sql:
        verdict = "OPTIMIZE_SQL"
        recommendation = (
            f"Chart '{chart['chart_title']}' costs ₹{monthly_cost:,.0f}/month and its query has a "
            f"complexity score of {complexity}/100 ({sql_analysis['issues'][0]}). "
            f"Recommend rewriting the query (remove SELECT *, add filters, fix joins) before "
            f"considering removal — usage is healthy at {weekly_views} views/week."
        )
        estimated_savings_inr = round(yearly_cost * 0.5, 0)  # assume 50% cost reduction from query fix

    elif low_usage and not high_cost:
        verdict = "MONITOR"
        recommendation = (
            f"Chart '{chart['chart_title']}' is low-usage ({weekly_views} views/week) but low-cost "
            f"(₹{monthly_cost:,.0f}/month). Not urgent, but flag owner ({chart.get('owner', 'N/A')}) "
            f"to confirm it's still needed."
        )
        estimated_savings_inr = round(yearly_cost * 0.85, 0)

    elif poor_sql:
        verdict = "OPTIMIZE_SQL"
        recommendation = (
            f"Chart '{chart['chart_title']}' has a poorly optimized query (complexity {complexity}/100) "
            f"even though current cost is moderate. Fixing now prevents cost growth as data volume increases."
        )
        estimated_savings_inr = round(yearly_cost * 0.3, 0)

    else:
        verdict = "KEEP"
        recommendation = f"Chart '{chart['chart_title']}' is healthy — good usage, reasonable cost, clean query."
        estimated_savings_inr = 0

    return {
        "verdict": verdict,
        "recommendation": recommendation,
        "estimated_yearly_savings_inr": estimated_savings_inr,
    }
