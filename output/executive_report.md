# DashWise AI — BI Dashboard FinOps & UX Audit Report

*Synthetic demo data. Warehouse costs modeled on Redshift ra3.xlplus-equivalent pricing (₹210/node-hour, Mumbai region), reflecting typical Indian enterprise cloud warehouse setups rather than Snowflake.*

## Executive Summary

- **Dashboards analyzed:** 12
- **Charts analyzed:** 49
- **Total annual warehouse compute cost:** ₹186,768
- **Total estimated potential savings:** ₹130,753/year (70% of current spend)
- **Dashboard health score:** 34.7/100 (% of charts flagged healthy)

### Verdict Breakdown

| Verdict | Count | Meaning |
|---|---|---|
| 🔴 REMOVE | 3 | Low usage + high cost — replace with static KPI |
| 🟠 OPTIMIZE_SQL | 15 | Poorly written query driving up cost |
| 🟡 MONITOR | 14 | Low usage, low cost — not urgent |
| 🟢 KEEP | 17 | Healthy chart, no action needed |

---

## Dashboard-by-Dashboard Findings

### Supply Chain Dashboard 3 (DASH-003)
**Owner:** Arjun Rao | **Business Unit:** Finance | **Tool:** Power BI

Annual cost: ₹49,675 | Potential savings: ₹41,194

**Flagged charts:**

- 🟡 **Vendor Payment Ageing** (CHART-0008)
  - Chart 'Vendor Payment Ageing' is low-usage (6 views/week) but low-cost (₹248/month). Not urgent, but flag owner (Arjun Rao) to confirm it's still needed.
  - Weekly views: 6 | Render time: 23.4s | Data scanned: 88.1GB | Monthly cost: ₹248

- 🔴 **Employee Attrition by Dept** (CHART-0009)
  - Chart 'Employee Attrition by Dept' is viewed only 5x/week but costs ₹3,787/month (₹45,482/year) in warehouse compute. Recommend replacing with a static pre-aggregated KPI card refreshed daily instead of on every dashboard load.
  - Weekly views: 5 | Render time: 25.5s | Data scanned: 310.6GB | Monthly cost: ₹3,787

### Operations Dashboard 12 (DASH-012)
**Owner:** Ananya Iyer | **Business Unit:** HR | **Tool:** Power BI

Annual cost: ₹54,120 | Potential savings: ₹40,787

**Flagged charts:**

- 🟡 **Plant-wise Production Output** (CHART-0045)
  - Chart 'Plant-wise Production Output' is low-usage (3 views/week) but low-cost (₹20/month). Not urgent, but flag owner (Ananya Iyer) to confirm it's still needed.
  - Weekly views: 3 | Render time: 3.8s | Data scanned: 5.6GB | Monthly cost: ₹20

- 🔴 **Warehouse Utilization** (CHART-0046)
  - Chart 'Warehouse Utilization' is viewed only 9x/week but costs ₹3,520/month (₹42,271/year) in warehouse compute. Recommend replacing with a static pre-aggregated KPI card refreshed daily instead of on every dashboard load.
  - Weekly views: 9 | Render time: 23.7s | Data scanned: 561.7GB | Monthly cost: ₹3,520

- 🟠 **Employee Attrition by Dept** (CHART-0047)
  - Chart 'Employee Attrition by Dept' has a poorly optimized query (complexity 75/100) even though current cost is moderate. Fixing now prevents cost growth as data volume increases.
  - Weekly views: 17 | Render time: 27.2s | Data scanned: 672.9GB | Monthly cost: ₹505

- 🟠 **Order Fulfillment Rate** (CHART-0048)
  - Chart 'Order Fulfillment Rate' has a poorly optimized query (complexity 70/100) even though current cost is moderate. Fixing now prevents cost growth as data volume increases.
  - Weekly views: 10 | Render time: 23.0s | Data scanned: 618.6GB | Monthly cost: ₹285

- 🟡 **Top 10 SKUs by Volume** (CHART-0049)
  - Chart 'Top 10 SKUs by Volume' is low-usage (7 views/week) but low-cost (₹177/month). Not urgent, but flag owner (Ananya Iyer) to confirm it's still needed.
  - Weekly views: 7 | Render time: 25.0s | Data scanned: 102.6GB | Monthly cost: ₹177

### HR Dashboard 5 (DASH-005)
**Owner:** Priya Sharma | **Business Unit:** Sales | **Tool:** Power BI

Annual cost: ₹27,213 | Potential savings: ₹22,092

**Flagged charts:**

- 🟡 **Freight Cost Trend** (CHART-0016)
  - Chart 'Freight Cost Trend' is low-usage (6 views/week) but low-cost (₹2/month). Not urgent, but flag owner (Priya Sharma) to confirm it's still needed.
  - Weekly views: 6 | Render time: 2.7s | Data scanned: 1.1GB | Monthly cost: ₹2

- 🟠 **Support Ticket Backlog** (CHART-0019)
  - Chart 'Support Ticket Backlog' has a poorly optimized query (complexity 70/100) even though current cost is moderate. Fixing now prevents cost growth as data volume increases.
  - Weekly views: 15 | Render time: 9.3s | Data scanned: 58.1GB | Monthly cost: ₹66

- 🔴 **Order Fulfillment Rate** (CHART-0020)
  - Chart 'Order Fulfillment Rate' is viewed only 6x/week but costs ₹2,139/month (₹25,684/year) in warehouse compute. Recommend replacing with a static pre-aggregated KPI card refreshed daily instead of on every dashboard load.
  - Weekly views: 6 | Render time: 25.2s | Data scanned: 100.9GB | Monthly cost: ₹2,139

### Marketing Dashboard 6 (DASH-006)
**Owner:** Arjun Rao | **Business Unit:** Finance | **Tool:** Tableau

Annual cost: ₹22,074 | Potential savings: ₹10,704

**Flagged charts:**

- 🟠 **Warehouse Utilization** (CHART-0022)
  - Chart 'Warehouse Utilization' has a poorly optimized query (complexity 100/100) even though current cost is moderate. Fixing now prevents cost growth as data volume increases.
  - Weekly views: 27 | Render time: 10.0s | Data scanned: 386.3GB | Monthly cost: ₹62

- 🟠 **Vendor Payment Ageing** (CHART-0023)
  - Chart 'Vendor Payment Ageing' costs ₹1,738/month and its query has a complexity score of 75/100 (SELECT * used (3x) — pulls unnecessary columns, increases scan cost). Recommend rewriting the query (remove SELECT *, add filters, fix joins) before considering removal — usage is healthy at 19 views/week.
  - Weekly views: 19 | Render time: 11.7s | Data scanned: 437.9GB | Monthly cost: ₹1,738

- 🟡 **Monthly Active Customers** (CHART-0024)
  - Chart 'Monthly Active Customers' is low-usage (2 views/week) but low-cost (₹5/month). Not urgent, but flag owner (Arjun Rao) to confirm it's still needed.
  - Weekly views: 2 | Render time: 2.6s | Data scanned: 0.6GB | Monthly cost: ₹5

### Operations Dashboard 11 (DASH-011)
**Owner:** Rahul Mehta | **Business Unit:** Operations | **Tool:** Power BI

Annual cost: ₹17,321 | Potential savings: ₹8,547

**Flagged charts:**

- 🟠 **Plant-wise Production Output** (CHART-0039)
  - Chart 'Plant-wise Production Output' has a poorly optimized query (complexity 100/100) even though current cost is moderate. Fixing now prevents cost growth as data volume increases.
  - Weekly views: 12 | Render time: 17.4s | Data scanned: 211.6GB | Monthly cost: ₹323

- 🟡 **Monthly Active Customers** (CHART-0040)
  - Chart 'Monthly Active Customers' is low-usage (6 views/week) but low-cost (₹297/month). Not urgent, but flag owner (Rahul Mehta) to confirm it's still needed.
  - Weekly views: 6 | Render time: 16.0s | Data scanned: 279.6GB | Monthly cost: ₹297

- 🟠 **Monthly Active Customers** (CHART-0041)
  - Chart 'Monthly Active Customers' has a poorly optimized query (complexity 70/100) even though current cost is moderate. Fixing now prevents cost growth as data volume increases.
  - Weekly views: 12 | Render time: 18.7s | Data scanned: 847.7GB | Monthly cost: ₹231

- 🟡 **Top 10 SKUs by Volume** (CHART-0042)
  - Chart 'Top 10 SKUs by Volume' is low-usage (0 views/week) but low-cost (₹4/month). Not urgent, but flag owner (Rahul Mehta) to confirm it's still needed.
  - Weekly views: 0 | Render time: 2.0s | Data scanned: 6.4GB | Monthly cost: ₹4

- 🟡 **Lead Funnel Conversion** (CHART-0043)
  - Chart 'Lead Funnel Conversion' is low-usage (5 views/week) but low-cost (₹207/month). Not urgent, but flag owner (Rahul Mehta) to confirm it's still needed.
  - Weekly views: 5 | Render time: 16.7s | Data scanned: 487.1GB | Monthly cost: ₹207

- 🟠 **Monthly Active Customers** (CHART-0044)
  - Chart 'Monthly Active Customers' has a poorly optimized query (complexity 100/100) even though current cost is moderate. Fixing now prevents cost growth as data volume increases.
  - Weekly views: 74 | Render time: 20.5s | Data scanned: 610.5GB | Monthly cost: ₹381

### Sales Dashboard 1 (DASH-001)
**Owner:** Ananya Iyer | **Business Unit:** Operations | **Tool:** Power BI

Annual cost: ₹6,197 | Potential savings: ₹4,413

**Flagged charts:**

- 🟠 **Revenue by Region** (CHART-0001)
  - Chart 'Revenue by Region' has a poorly optimized query (complexity 100/100) even though current cost is moderate. Fixing now prevents cost growth as data volume increases.
  - Weekly views: 28 | Render time: 9.7s | Data scanned: 402.9GB | Monthly cost: ₹120

- 🟡 **Order Fulfillment Rate** (CHART-0002)
  - Chart 'Order Fulfillment Rate' is low-usage (0 views/week) but low-cost (₹390/month). Not urgent, but flag owner (Ananya Iyer) to confirm it's still needed.
  - Weekly views: 0 | Render time: 21.0s | Data scanned: 508.6GB | Monthly cost: ₹390

### HR Dashboard 9 (DASH-009)
**Owner:** Arjun Rao | **Business Unit:** Marketing | **Tool:** Power BI

Annual cost: ₹5,627 | Potential savings: ₹1,636

**Flagged charts:**

- 🟠 **Warehouse Utilization** (CHART-0033)
  - Chart 'Warehouse Utilization' has a poorly optimized query (complexity 100/100) even though current cost is moderate. Fixing now prevents cost growth as data volume increases.
  - Weekly views: 33 | Render time: 13.6s | Data scanned: 221.1GB | Monthly cost: ₹252

- 🟠 **Customer Churn by Segment** (CHART-0034)
  - Chart 'Customer Churn by Segment' has a poorly optimized query (complexity 80/100) even though current cost is moderate. Fixing now prevents cost growth as data volume increases.
  - Weekly views: 58 | Render time: 9.8s | Data scanned: 404.3GB | Monthly cost: ₹61

- 🟠 **Top 10 SKUs by Volume** (CHART-0035)
  - Chart 'Top 10 SKUs by Volume' has a poorly optimized query (complexity 75/100) even though current cost is moderate. Fixing now prevents cost growth as data volume increases.
  - Weekly views: 25 | Render time: 22.8s | Data scanned: 514.4GB | Monthly cost: ₹141

### Marketing Dashboard 8 (DASH-008)
**Owner:** Vikram Nair | **Business Unit:** Sales | **Tool:** Tableau

Annual cost: ₹2,015 | Potential savings: ₹627

**Flagged charts:**

- 🟡 **Customer Churn by Segment** (CHART-0029)
  - Chart 'Customer Churn by Segment' is low-usage (9 views/week) but low-cost (₹5/month). Not urgent, but flag owner (Vikram Nair) to confirm it's still needed.
  - Weekly views: 9 | Render time: 3.0s | Data scanned: 2.9GB | Monthly cost: ₹5

- 🟠 **Order Fulfillment Rate** (CHART-0031)
  - Chart 'Order Fulfillment Rate' has a poorly optimized query (complexity 75/100) even though current cost is moderate. Fixing now prevents cost growth as data volume increases.
  - Weekly views: 17 | Render time: 15.0s | Data scanned: 99.2GB | Monthly cost: ₹159

### HR Dashboard 7 (DASH-007)
**Owner:** Vikram Nair | **Business Unit:** HR | **Tool:** Power BI

Annual cost: ₹1,094 | Potential savings: ₹416

**Flagged charts:**

- 🟡 **Lead Funnel Conversion** (CHART-0025)
  - Chart 'Lead Funnel Conversion' is low-usage (4 views/week) but low-cost (₹12/month). Not urgent, but flag owner (Vikram Nair) to confirm it's still needed.
  - Weekly views: 4 | Render time: 2.2s | Data scanned: 7.4GB | Monthly cost: ₹12

- 🟠 **Revenue by Region** (CHART-0026)
  - Chart 'Revenue by Region' has a poorly optimized query (complexity 70/100) even though current cost is moderate. Fixing now prevents cost growth as data volume increases.
  - Weekly views: 27 | Render time: 11.8s | Data scanned: 227.2GB | Monthly cost: ₹73

- 🟡 **Revenue by Region** (CHART-0027)
  - Chart 'Revenue by Region' is low-usage (1 views/week) but low-cost (₹3/month). Not urgent, but flag owner (Vikram Nair) to confirm it's still needed.
  - Weekly views: 1 | Render time: 3.8s | Data scanned: 4.5GB | Monthly cost: ₹3

### Sales Dashboard 10 (DASH-010)
**Owner:** Rahul Mehta | **Business Unit:** Operations | **Tool:** Tableau

Annual cost: ₹1,042 | Potential savings: ₹234

**Flagged charts:**

- 🟠 **Plant-wise Production Output** (CHART-0036)
  - Chart 'Plant-wise Production Output' has a poorly optimized query (complexity 80/100) even though current cost is moderate. Fixing now prevents cost growth as data volume increases.
  - Weekly views: 21 | Render time: 10.5s | Data scanned: 305.1GB | Monthly cost: ₹65

### Operations Dashboard 4 (DASH-004)
**Owner:** Arjun Rao | **Business Unit:** Finance | **Tool:** Power BI

Annual cost: ₹207 | Potential savings: ₹81

**Flagged charts:**

- 🟡 **Vendor Payment Ageing** (CHART-0014)
  - Chart 'Vendor Payment Ageing' is low-usage (7 views/week) but low-cost (₹8/month). Not urgent, but flag owner (Arjun Rao) to confirm it's still needed.
  - Weekly views: 7 | Render time: 1.5s | Data scanned: 7.3GB | Monthly cost: ₹8

### Sales Dashboard 2 (DASH-002)
**Owner:** Priya Sharma | **Business Unit:** HR | **Tool:** Power BI

Annual cost: ₹185 | Potential savings: ₹22

**Flagged charts:**

- 🟡 **Plant-wise Production Output** (CHART-0004)
  - Chart 'Plant-wise Production Output' is low-usage (7 views/week) but low-cost (₹2/month). Not urgent, but flag owner (Priya Sharma) to confirm it's still needed.
  - Weekly views: 7 | Render time: 2.4s | Data scanned: 1.4GB | Monthly cost: ₹2
