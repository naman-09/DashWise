"""Unit tests for the FinOps ₹ cost model."""
import pytest

from dashwise.agents.cost_agent import (
    NODE_HOURLY_RATE_INR,
    compute_chart_cost,
    estimate_nodes_engaged,
)


class TestNodesEngagedTiers:
    """`estimate_nodes_engaged` steps up with data scanned (GB)."""

    def test_tiny_scan(self):
        assert estimate_nodes_engaged(4.9) == 0.5

    def test_boundary_5gb(self):
        assert estimate_nodes_engaged(5) == 1.0

    def test_small_scan(self):
        assert estimate_nodes_engaged(49.9) == 1.0

    def test_boundary_50gb(self):
        assert estimate_nodes_engaged(50) == 2.0

    def test_medium_scan(self):
        assert estimate_nodes_engaged(199) == 2.0

    def test_boundary_200gb(self):
        assert estimate_nodes_engaged(200) == 3.5

    def test_large_scan(self):
        assert estimate_nodes_engaged(900) == 3.5


class TestComputeChartCost:
    def test_cost_per_run_formula(self):
        # 36s / 3600 * ₹210/node-hr * 1 node (10 GB tier) = ₹2.10
        result = compute_chart_cost(render_time_sec=36, data_scanned_gb=10, runs_per_week=10)
        assert result["cost_per_run_inr"] == pytest.approx(2.10, abs=0.01)
        assert result["nodes_engaged"] == 1.0

    def test_weekly_is_per_run_times_runs(self):
        result = compute_chart_cost(render_time_sec=36, data_scanned_gb=10, runs_per_week=10)
        assert result["weekly_cost_inr"] == pytest.approx(21.0, abs=0.01)

    def test_monthly_is_weekly_times_4_33(self):
        result = compute_chart_cost(render_time_sec=36, data_scanned_gb=10, runs_per_week=10)
        assert result["monthly_cost_inr"] == pytest.approx(result["weekly_cost_inr"] * 4.33, abs=0.01)

    def test_yearly_is_weekly_times_52(self):
        result = compute_chart_cost(render_time_sec=36, data_scanned_gb=10, runs_per_week=10)
        assert result["yearly_cost_inr"] == pytest.approx(result["weekly_cost_inr"] * 52, abs=0.01)

    def test_more_data_costs_more_for_same_query(self):
        cheap = compute_chart_cost(render_time_sec=10, data_scanned_gb=3, runs_per_week=7)
        pricey = compute_chart_cost(render_time_sec=10, data_scanned_gb=500, runs_per_week=7)
        assert pricey["yearly_cost_inr"] > cheap["yearly_cost_inr"]

    def test_node_hourly_rate_is_inr_210(self):
        # Guardrail: the documented Redshift Mumbai assumption must not drift.
        assert NODE_HOURLY_RATE_INR == 210
