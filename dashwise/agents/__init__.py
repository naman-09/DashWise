"""DashWise analysis agents.

Three small, single-responsibility agents that run sequentially:

- ``sql_agent.analyze_query``    — static SQL anti-pattern detection (SQLGlot)
- ``cost_agent.compute_chart_cost`` — ₹ warehouse-compute cost model
- ``decision_agent.classify_chart``  — combine the above + usage into a verdict
"""

from dashwise.agents.cost_agent import compute_chart_cost
from dashwise.agents.decision_agent import classify_chart
from dashwise.agents.sql_agent import analyze_query

__all__ = ["analyze_query", "compute_chart_cost", "classify_chart"]
