"""Unit tests for the SQL anti-pattern detection agent.

One test per anti-pattern the agent is supposed to catch. Assertions target the
human-readable ``issues`` strings and the boolean/count flags rather than exact
complexity scores, so the tests stay meaningful even if the scoring weights are
retuned.
"""
from dashwise.agents.sql_agent import analyze_query


def _issues_text(result):
    """Join all issue strings so we can substring-match against them."""
    return " || ".join(result["issues"])


def test_select_star_flagged():
    result = analyze_query("SELECT * FROM fact_sales WHERE region = 'West'")
    assert result["parse_error"] is False
    assert result["has_select_star"] is True
    assert "SELECT * used" in _issues_text(result)


def test_select_star_counts_multiple_stars():
    result = analyze_query(
        "SELECT a.*, b.* FROM a JOIN b ON a.id = b.id WHERE a.x = 1"
    )
    assert result["has_select_star"] is True
    assert "SELECT * used (2x)" in _issues_text(result)


def test_comma_join_sprawl_is_flagged():
    # NOTE: with modern SQLGlot, comma-joins (FROM a, b, c ...) parse as JOIN
    # nodes, so a wide comma-join surfaces as a high join count rather than the
    # legacy "implicit comma-join" branch. Either way, the sprawl gets caught.
    result = analyze_query(
        """SELECT *
        FROM fact_sales fs, dim_customer dc, dim_product dp, dim_region dr, dim_date dd
        WHERE fs.customer_id = dc.customer_id
          AND fs.product_id = dp.product_id
          AND fs.region_id = dr.region_id
          AND fs.date_id = dd.date_id"""
    )
    assert result["join_count"] == 4
    assert "High join count" in _issues_text(result)
    assert result["has_select_star"] is True


def test_comma_join_without_where_is_flagged():
    result = analyze_query("SELECT a.id FROM table_a a, table_b b")
    assert "No WHERE clause despite joins" in _issues_text(result)


def test_explicit_cross_join_flagged():
    result = analyze_query(
        "SELECT a.id FROM table_a a CROSS JOIN table_b b WHERE a.x = 1"
    )
    assert "CROSS JOIN" in _issues_text(result)


def test_high_join_count_flagged():
    result = analyze_query(
        """SELECT t1.id FROM t1
        JOIN t2 ON t1.id = t2.id
        JOIN t3 ON t2.id = t3.id
        JOIN t4 ON t3.id = t4.id
        JOIN t5 ON t4.id = t5.id
        WHERE t1.x = 1"""
    )
    assert result["join_count"] == 4
    assert "High join count" in _issues_text(result)


def test_duplicate_cte_flagged():
    result = analyze_query(
        """WITH a AS (SELECT id FROM t WHERE x = 1),
                b AS (SELECT id FROM t WHERE x = 1)
        SELECT a.id FROM a JOIN b ON a.id = b.id WHERE a.id = 1"""
    )
    assert "Duplicate CTE definitions" in _issues_text(result)


def test_missing_where_no_joins_flagged():
    result = analyze_query("SELECT region FROM fact_sales")
    assert "No WHERE clause — likely full table scan" in _issues_text(result)


def test_missing_where_with_joins_flagged():
    result = analyze_query(
        "SELECT a.id FROM a JOIN b ON a.id = b.id"
    )
    assert "No WHERE clause despite joins" in _issues_text(result)


def test_group_by_with_select_star_flagged():
    result = analyze_query(
        "SELECT * FROM fact_sales WHERE x = 1 GROUP BY region"
    )
    assert "GROUP BY combined with SELECT *" in _issues_text(result)


def test_order_by_without_limit_flagged():
    result = analyze_query(
        "SELECT region FROM fact_sales WHERE x = 1 ORDER BY region"
    )
    assert "ORDER BY without LIMIT" in _issues_text(result)


def test_order_by_with_limit_not_flagged():
    result = analyze_query(
        "SELECT region FROM fact_sales WHERE x = 1 ORDER BY region LIMIT 100"
    )
    assert "ORDER BY without LIMIT" not in _issues_text(result)


def test_nested_subqueries_flagged():
    result = analyze_query(
        """SELECT id FROM (
               SELECT id FROM (
                   SELECT id FROM t WHERE x = 1
               ) inner_q
           ) outer_q
           WHERE id > 0"""
    )
    assert "Nested subqueries detected" in _issues_text(result)


def test_clean_query_has_no_major_antipatterns():
    result = analyze_query(
        """SELECT month, dept_name, SUM(headcount) AS total_headcount
        FROM fact_hr_monthly
        WHERE year = 2026
        GROUP BY month, dept_name"""
    )
    assert result["parse_error"] is False
    assert result["has_select_star"] is False
    assert result["complexity_score"] == 0
    assert "No major anti-patterns detected" in _issues_text(result)


def test_unparseable_query_returns_parse_error():
    result = analyze_query("this is not valid sql @@@ ;;; ((")
    assert result["parse_error"] is True
    assert result["complexity_score"] == 50
    assert "Could not parse SQL" in _issues_text(result)
