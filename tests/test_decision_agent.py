"""Unit tests for the decision / recommendation agent.

Exercises each verdict branch by feeding hand-built SQL + cost analyses that
isolate one combination of (usage, cost, SQL quality).
"""
from dashwise.agents.decision_agent import classify_chart


def _chart(weekly_views, title="Some Chart", owner="Priya Sharma"):
    return {"chart_title": title, "weekly_views": weekly_views, "owner": owner}


def _sql(complexity, issues=None):
    return {
        "complexity_score": complexity,
        "issues": issues or ["SELECT * used (1x) — pulls unnecessary columns"],
    }


def _cost(monthly, yearly):
    return {"monthly_cost_inr": monthly, "yearly_cost_inr": yearly}


def test_remove_when_low_usage_and_high_cost():
    decision = classify_chart(_chart(5), _sql(10), _cost(monthly=2000, yearly=24000))
    assert decision["verdict"] == "REMOVE"
    # 85% of yearly cost is recoverable by swapping to a static KPI card
    assert decision["estimated_yearly_savings_inr"] == 20400


def test_optimize_when_high_cost_and_poor_sql_but_healthy_usage():
    decision = classify_chart(_chart(50), _sql(60), _cost(monthly=2000, yearly=24000))
    assert decision["verdict"] == "OPTIMIZE_SQL"
    # 50% cost reduction assumed from fixing the query
    assert decision["estimated_yearly_savings_inr"] == 12000


def test_monitor_when_low_usage_but_low_cost():
    decision = classify_chart(_chart(5), _sql(10), _cost(monthly=500, yearly=6000))
    assert decision["verdict"] == "MONITOR"
    assert decision["estimated_yearly_savings_inr"] == 5100


def test_optimize_when_poor_sql_only():
    decision = classify_chart(_chart(50), _sql(60), _cost(monthly=500, yearly=6000))
    assert decision["verdict"] == "OPTIMIZE_SQL"
    # 30% preventative saving when cost is still moderate
    assert decision["estimated_yearly_savings_inr"] == 1800


def test_keep_when_healthy_usage_low_cost_clean_sql():
    decision = classify_chart(_chart(50), _sql(10), _cost(monthly=500, yearly=6000))
    assert decision["verdict"] == "KEEP"
    assert decision["estimated_yearly_savings_inr"] == 0


def test_recommendation_is_rupee_denominated():
    decision = classify_chart(_chart(5), _sql(10), _cost(monthly=2000, yearly=24000))
    assert "₹" in decision["recommendation"]
    assert "$" not in decision["recommendation"]


def test_monitor_recommendation_names_the_owner():
    decision = classify_chart(_chart(5, owner="Arjun Rao"), _sql(10), _cost(monthly=500, yearly=6000))
    assert "Arjun Rao" in decision["recommendation"]
