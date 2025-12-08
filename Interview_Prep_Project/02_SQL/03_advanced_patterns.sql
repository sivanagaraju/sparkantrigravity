-- ============================================================
-- SQL INTERVIEW QUESTIONS - PART 3: ADVANCED PATTERNS
-- ============================================================
-- Swiss Re Interview Prep: Senior Application Engineer
-- Topic: CTEs, Recursive Queries, Pivot, and Complex Logic
-- ============================================================

-- ============================================================
-- Q1: Recursive CTE - Hierarchical Data (Employee/Manager)
-- "Show the full management chain for employee ID 10."
-- ============================================================

/*
ANSWER:

Recursive CTEs have two parts:
1. ANCHOR MEMBER: The starting point (e.g., the specific employee)
2. RECURSIVE MEMBER: Joins with previous results to get next level

This is perfect for:
- Org charts (employee -> manager -> CEO)
- Category trees (product -> subcategory -> category)
- Bill of Materials (part -> subpart -> raw material)
*/

WITH RECURSIVE ManagerChain AS (
    -- Anchor: Start with the specific employee
    SELECT 
        employee_id,
        name,
        manager_id,
        1 as level,
        CAST(name AS VARCHAR(500)) as chain
    FROM Employees
    WHERE employee_id = 10
    
    UNION ALL
    
    -- Recursive: Get the manager of the current level
    SELECT 
        e.employee_id,
        e.name,
        e.manager_id,
        mc.level + 1,
        CONCAT(mc.chain, ' -> ', e.name)
    FROM Employees e
    INNER JOIN ManagerChain mc ON e.employee_id = mc.manager_id
)
SELECT * FROM ManagerChain;

-- INTERVIEW TIP: Always include a level counter to avoid infinite loops
-- and set a MAX recursion limit if your DB supports it.

-- ============================================================
-- Q2: Recursive CTE - Date Series Generation
-- "Generate a calendar table for a date range."
-- ============================================================

WITH RECURSIVE DateSeries AS (
    SELECT DATE '2024-01-01' as date_val
    
    UNION ALL
    
    SELECT date_val + INTERVAL '1 day'
    FROM DateSeries
    WHERE date_val < DATE '2024-01-31'
)
SELECT 
    date_val,
    EXTRACT(DOW FROM date_val) as day_of_week,
    TO_CHAR(date_val, 'Day') as day_name
FROM DateSeries;

-- USE CASE: Create a date dimension table or fill gaps in time series data.

-- ============================================================
-- Q3: Pivot (Rows to Columns)
-- "Transform monthly claim totals into columns."
-- ============================================================

/*
Problem: You have data like:
| region | month | total |
|--------|-------|-------|
| North  | Jan   | 100   |
| North  | Feb   | 200   |
| South  | Jan   | 150   |

You want:
| region | Jan | Feb |
|--------|-----|-----|
| North  | 100 | 200 |
| South  | 150 | NULL|
*/

-- Standard SQL (works everywhere):
SELECT 
    region,
    SUM(CASE WHEN EXTRACT(MONTH FROM claim_date) = 1 THEN claim_amount END) as Jan,
    SUM(CASE WHEN EXTRACT(MONTH FROM claim_date) = 2 THEN claim_amount END) as Feb,
    SUM(CASE WHEN EXTRACT(MONTH FROM claim_date) = 3 THEN claim_amount END) as Mar,
    SUM(CASE WHEN EXTRACT(MONTH FROM claim_date) = 4 THEN claim_amount END) as Apr
FROM Claims
WHERE claim_date BETWEEN '2024-01-01' AND '2024-04-30'
GROUP BY region;

-- PostgreSQL CROSSTAB (Extension):
-- SELECT * FROM crosstab(...) -- requires tablefunc extension

-- ============================================================
-- Q4: Unpivot (Columns to Rows)
-- "Transform column-based data into rows."
-- ============================================================

/*
Problem: You have data like:
| region | q1_sales | q2_sales |
|--------|----------|----------|
| North  | 100      | 200      |

You want:
| region | quarter | sales |
|--------|---------|-------|
| North  | Q1      | 100   |
| North  | Q2      | 200   |
*/

-- Standard SQL:
SELECT region, 'Q1' as quarter, q1_sales as sales FROM SalesTable
UNION ALL
SELECT region, 'Q2' as quarter, q2_sales as sales FROM SalesTable;

-- Using LATERAL/VALUES (PostgreSQL 9.3+, SQL Server 2008+):
SELECT 
    s.region,
    u.quarter,
    u.sales
FROM SalesTable s
CROSS JOIN LATERAL (
    VALUES ('Q1', s.q1_sales), ('Q2', s.q2_sales)
) AS u(quarter, sales);

-- ============================================================
-- Q5: Gaps and Islands - Session Detection
-- "Group user events into sessions (30-minute gap = new session)."
-- ============================================================

/*
This is a CLASSIC interview problem!

The pattern:
1. Use LAG to get previous event time
2. Flag rows where gap > threshold as "new session start"
3. Use SUM() window to create session groups
*/

WITH EventsWithLag AS (
    SELECT 
        user_id,
        event_time,
        LAG(event_time) OVER (PARTITION BY user_id ORDER BY event_time) as prev_event_time
    FROM UserEvents
),
EventsWithFlag AS (
    SELECT 
        user_id,
        event_time,
        CASE 
            WHEN prev_event_time IS NULL THEN 1
            WHEN event_time - prev_event_time > INTERVAL '30 minutes' THEN 1
            ELSE 0
        END as is_new_session
    FROM EventsWithLag
),
EventsWithSession AS (
    SELECT 
        user_id,
        event_time,
        SUM(is_new_session) OVER (PARTITION BY user_id ORDER BY event_time) as session_id
    FROM EventsWithFlag
)
SELECT 
    user_id,
    session_id,
    MIN(event_time) as session_start,
    MAX(event_time) as session_end,
    COUNT(*) as events_in_session,
    MAX(event_time) - MIN(event_time) as session_duration
FROM EventsWithSession
GROUP BY user_id, session_id;

-- ============================================================
-- Q6: Running Difference / Change Detection
-- "Find dates where the claim count dropped by more than 50%."
-- ============================================================

WITH DailyCounts AS (
    SELECT 
        claim_date,
        COUNT(*) as claim_count
    FROM Claims
    GROUP BY claim_date
),
WithChange AS (
    SELECT 
        claim_date,
        claim_count,
        LAG(claim_count) OVER (ORDER BY claim_date) as prev_count,
        claim_count - LAG(claim_count) OVER (ORDER BY claim_date) as change
    FROM DailyCounts
)
SELECT 
    claim_date,
    claim_count,
    prev_count,
    ROUND(100.0 * (claim_count - prev_count) / NULLIF(prev_count, 0), 2) as pct_change
FROM WithChange
WHERE claim_count < prev_count * 0.5;  -- Dropped by more than 50%

-- ============================================================
-- Q7: Top N per Group
-- "Find the 3 highest claims for each claim_type."
-- ============================================================

-- Using ROW_NUMBER:
WITH Ranked AS (
    SELECT 
        claim_id,
        claim_type,
        claim_amount,
        ROW_NUMBER() OVER (PARTITION BY claim_type ORDER BY claim_amount DESC) as rn
    FROM Claims
)
SELECT claim_id, claim_type, claim_amount
FROM Ranked
WHERE rn <= 3;

-- Using FETCH/LIMIT with LATERAL (PostgreSQL):
SELECT DISTINCT c.claim_type, top3.*
FROM (SELECT DISTINCT claim_type FROM Claims) c
CROSS JOIN LATERAL (
    SELECT claim_id, claim_amount
    FROM Claims
    WHERE claim_type = c.claim_type
    ORDER BY claim_amount DESC
    FETCH FIRST 3 ROWS ONLY
) top3;

-- ============================================================
-- Q8: Median Calculation
-- "Calculate the median claim amount per region."
-- ============================================================

-- Using PERCENTILE_CONT (Standard SQL, works in PostgreSQL, Oracle):
SELECT 
    region,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY claim_amount) as median_amount
FROM Claims
GROUP BY region;

-- Alternative without PERCENTILE (for MySQL, older DBs):
WITH Ordered AS (
    SELECT 
        region,
        claim_amount,
        ROW_NUMBER() OVER (PARTITION BY region ORDER BY claim_amount) as rn,
        COUNT(*) OVER (PARTITION BY region) as cnt
    FROM Claims
)
SELECT 
    region,
    AVG(claim_amount) as median_amount
FROM Ordered
WHERE rn IN (cnt/2, cnt/2 + 1, (cnt+1)/2)
GROUP BY region;

-- ============================================================
-- Q9: Conditional Aggregation Pattern
-- "Create a summary report: Counts per claim_type as columns."
-- ============================================================

SELECT 
    region,
    COUNT(*) as total_claims,
    COUNT(CASE WHEN claim_type = 'Coinsurance' THEN 1 END) as coinsurance_count,
    COUNT(CASE WHEN claim_type = 'Reinsurance' THEN 1 END) as reinsurance_count,
    SUM(CASE WHEN claim_priority = 'Urgent' THEN claim_amount ELSE 0 END) as urgent_total,
    AVG(CASE WHEN claim_amount > 5000 THEN claim_amount END) as avg_high_value
FROM Claims
GROUP BY region;

-- ============================================================
-- Q10: MERGE / UPSERT Statement
-- "Update existing claims or insert new ones."
-- ============================================================

-- Standard SQL MERGE (SQL Server, Oracle, PostgreSQL 15+):
MERGE INTO Claims AS target
USING StagingClaims AS source
ON target.claim_id = source.claim_id
WHEN MATCHED THEN
    UPDATE SET 
        claim_amount = source.claim_amount,
        claim_type = source.claim_type
WHEN NOT MATCHED THEN
    INSERT (claim_id, policyholder_id, claim_amount, claim_date, claim_type)
    VALUES (source.claim_id, source.policyholder_id, source.claim_amount, source.claim_date, source.claim_type);

-- PostgreSQL INSERT ON CONFLICT (Upsert):
INSERT INTO Claims (claim_id, claim_amount, claim_type)
VALUES ('CL001', 5000, 'Coinsurance')
ON CONFLICT (claim_id)
DO UPDATE SET 
    claim_amount = EXCLUDED.claim_amount,
    claim_type = EXCLUDED.claim_type;
