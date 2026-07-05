"""
SQL Cost & Quality Agent
Parses SQL statically (no execution) using SQLGlot to detect anti-patterns
that drive up warehouse compute cost, and produces a complexity score.
"""
import sqlglot
from sqlglot import exp


def analyze_query(sql: str) -> dict:
    """Parse a SQL query and return detected issues + complexity score."""
    issues = []
    score = 0  # higher = worse

    try:
        parsed = sqlglot.parse_one(sql, read="postgres")
    except Exception as e:
        return {
            "issues": [f"Could not parse SQL: {str(e)}"],
            "complexity_score": 50,
            "parse_error": True,
        }

    # 1. SELECT * detection
    star_count = len(list(parsed.find_all(exp.Star)))
    if star_count > 0:
        issues.append(f"SELECT * used ({star_count}x) — pulls unnecessary columns, increases scan cost")
        score += 15 * star_count

    # 2. Join count, cross join, and implicit comma-join detection.
    # SQLGlot parses each comma-separated table in FROM (FROM a, b, c) as a Join
    # node carrying no ON/USING condition and no kind/side/method — explicit
    # joins always have at least one of those, so that bare shape uniquely
    # identifies comma-style joins.
    joins = list(parsed.find_all(exp.Join))
    join_count = len(joins)
    cross_joins = [j for j in joins if j.kind and j.kind.upper() == "CROSS"]
    implicit_joins = [
        j
        for j in joins
        if not j.args.get("on")
        and not j.args.get("using")
        and not j.kind
        and not j.side
        and not j.args.get("method")
    ]

    if implicit_joins:
        issues.append(
            f"Implicit comma-join style detected ({len(implicit_joins) + 1} tables) — "
            "no explicit JOIN conditions, risk of cartesian product"
        )
        score += 25 * len(implicit_joins)

    if cross_joins:
        issues.append(f"Explicit CROSS JOIN used ({len(cross_joins)}x) — cartesian product risk, very expensive on large tables")
        score += 30 * len(cross_joins)

    if join_count >= 4:
        issues.append(f"High join count ({join_count} joins) — increases query planning complexity and shuffle cost")
        score += 8 * join_count

    # 3. CTE duplication detection (same/similar CTE defined multiple times)
    ctes = list(parsed.find_all(exp.CTE))
    if len(ctes) >= 2:
        cte_sqls = [c.this.sql(dialect="postgres") if c.this else "" for c in ctes]
        if len(cte_sqls) != len(set(cte_sqls)):
            issues.append("Duplicate CTE definitions detected — same computation repeated, wastes compute")
            score += 20

    # 4. Missing WHERE clause on large scans
    where_clause = parsed.find(exp.Where)
    if not where_clause and join_count == 0:
        issues.append("No WHERE clause — likely full table scan")
        score += 20
    elif not where_clause and join_count > 0:
        issues.append("No WHERE clause despite joins — likely scanning full joined result set")
        score += 25

    # 5. GROUP BY without aggregation filter (no HAVING, no LIMIT) on wide selects
    group_by = parsed.find(exp.Group)
    has_limit = parsed.find(exp.Limit) is not None
    if group_by and star_count > 0:
        issues.append("GROUP BY combined with SELECT * — expensive aggregation over unnecessary columns")
        score += 15

    # 6. ORDER BY without LIMIT (sorts entire result set)
    order_by = parsed.find(exp.Order)
    if order_by and not has_limit:
        issues.append("ORDER BY without LIMIT — sorts entire result set unnecessarily")
        score += 10

    # 7. Subquery depth
    subqueries = list(parsed.find_all(exp.Subquery))
    if len(subqueries) >= 2:
        issues.append(f"Nested subqueries detected ({len(subqueries)}) — consider flattening or using CTEs")
        score += 10 * len(subqueries)

    if not issues:
        issues.append("No major anti-patterns detected — query looks reasonably well-optimized")

    complexity_score = min(100, score)

    return {
        "issues": issues,
        "complexity_score": complexity_score,
        "join_count": join_count,
        "has_select_star": star_count > 0,
        "parse_error": False,
    }


if __name__ == "__main__":
    test_query = """SELECT c.*, o.*, p.*
FROM customers c
CROSS JOIN orders o
LEFT JOIN products p ON o.product_id = p.product_id
WHERE c.signup_date > '2020-01-01'"""
    result = analyze_query(test_query)
    import json
    print(json.dumps(result, indent=2))
