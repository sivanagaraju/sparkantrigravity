-- ============================================================
-- SQL INTERVIEW QUESTIONS - PART 1: BASICS & WINDOW FUNCTIONS
-- ============================================================
-- Swiss Re Interview Prep: Senior Application Engineer
-- Topic: SQL Fundamentals for Data Engineering
-- ============================================================

-- CONTEXT: You are working with insurance claims data
-- Tables:
--   Claims (claim_id, policyholder_id, claim_amount, claim_date, claim_type, region)
--   Policyholders (policyholder_id, name, join_date, tier)
--   Payments (payment_id, claim_id, payment_amount, payment_date)

-- ============================================================
-- Q1: Basic Aggregation with GROUP BY
-- "Find the total claim amount per region, ordered by highest first."
-- ============================================================

-- ANSWER:
SELECT 
    region,
    COUNT(*) as total_claims,
    SUM(claim_amount) as total_amount,
    AVG(claim_amount) as avg_amount
FROM Claims
GROUP BY region
ORDER BY total_amount DESC;

-- INTERVIEW TIP: Always mention you would add indexes on commonly grouped columns.

-- ============================================================
-- Q2: Filtering Groups with HAVING
-- "Find regions where the average claim amount exceeds $5000."
-- ============================================================

-- ANSWER:
SELECT 
    region,
    AVG(claim_amount) as avg_amount
FROM Claims
GROUP BY region
HAVING AVG(claim_amount) > 5000;

-- DIFFERENCE: WHERE filters rows BEFORE grouping, HAVING filters AFTER grouping.

-- ============================================================
-- Q3: ROW_NUMBER() - The Most Common Window Function
-- "For each region, find the top 3 highest claims."
-- ============================================================

-- ANSWER:
WITH RankedClaims AS (
    SELECT 
        claim_id,
        region,
        claim_amount,
        ROW_NUMBER() OVER (PARTITION BY region ORDER BY claim_amount DESC) as rn
    FROM Claims
)
SELECT claim_id, region, claim_amount
FROM RankedClaims
WHERE rn <= 3;

-- INTERVIEW TIP: Always use a CTE for readability.
-- ROW_NUMBER gives unique ranks (1, 2, 3).
-- RANK gives same rank for ties (1, 1, 3).
-- DENSE_RANK gives consecutive ranks for ties (1, 1, 2).

-- ============================================================
-- Q4: Running Total (Cumulative Sum)
-- "Calculate the running total of claim amounts per policyholder, ordered by date."
-- ============================================================

-- ANSWER:
SELECT 
    policyholder_id,
    claim_date,
    claim_amount,
    SUM(claim_amount) OVER (
        PARTITION BY policyholder_id 
        ORDER BY claim_date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as running_total
FROM Claims
ORDER BY policyholder_id, claim_date;

-- EXPLANATION:
-- PARTITION BY: Restart the sum for each policyholder
-- ORDER BY: Define the order for the running sum
-- ROWS BETWEEN: Defines the window frame (from start to current row)

-- ============================================================
-- Q5: LAG and LEAD - Accessing Adjacent Rows
-- "For each claim, show the previous claim amount for the same policyholder."
-- ============================================================

-- ANSWER:
SELECT 
    claim_id,
    policyholder_id,
    claim_date,
    claim_amount,
    LAG(claim_amount, 1) OVER (PARTITION BY policyholder_id ORDER BY claim_date) as prev_claim_amount,
    LEAD(claim_amount, 1) OVER (PARTITION BY policyholder_id ORDER BY claim_date) as next_claim_amount
FROM Claims;

-- LAG(column, n): Returns the value from n rows BEFORE current row
-- LEAD(column, n): Returns the value from n rows AFTER current row

-- ============================================================
-- Q6: Period-over-Period Comparison (YoY Growth)
-- "Calculate the total claim amount per month and the growth % from the previous month."
-- ============================================================

-- ANSWER:
WITH MonthlyTotals AS (
    SELECT 
        DATE_TRUNC('month', claim_date) as claim_month,
        SUM(claim_amount) as total_amount
    FROM Claims
    GROUP BY DATE_TRUNC('month', claim_date)
),
WithLag AS (
    SELECT 
        claim_month,
        total_amount,
        LAG(total_amount, 1) OVER (ORDER BY claim_month) as prev_month_amount
    FROM MonthlyTotals
)
SELECT 
    claim_month,
    total_amount,
    prev_month_amount,
    ROUND(
        (total_amount - prev_month_amount) / NULLIF(prev_month_amount, 0) * 100, 
        2
    ) as growth_pct
FROM WithLag
ORDER BY claim_month;

-- INTERVIEW TIP: Always use NULLIF to avoid division by zero.

-- ============================================================
-- Q7: FIRST_VALUE and LAST_VALUE
-- "For each claim, show the first and last claim amount for that policyholder."
-- ============================================================

-- ANSWER:
SELECT 
    claim_id,
    policyholder_id,
    claim_date,
    claim_amount,
    FIRST_VALUE(claim_amount) OVER w as first_claim,
    LAST_VALUE(claim_amount) OVER (
        PARTITION BY policyholder_id 
        ORDER BY claim_date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) as last_claim
FROM Claims
WINDOW w AS (PARTITION BY policyholder_id ORDER BY claim_date);

-- WARNING: LAST_VALUE default frame is UNBOUNDED PRECEDING to CURRENT ROW,
-- so you must explicitly set UNBOUNDED FOLLOWING to get the actual last value.

-- ============================================================
-- Q8: NTILE - Dividing Data into Buckets
-- "Divide claims into 4 quartiles based on claim_amount."
-- ============================================================

-- ANSWER:
SELECT 
    claim_id,
    claim_amount,
    NTILE(4) OVER (ORDER BY claim_amount) as quartile
FROM Claims;

-- NTILE(n) divides the data into n equal (or nearly equal) groups.
-- Quartile 1 = lowest 25%, Quartile 4 = highest 25%

-- ============================================================
-- Q9: PERCENT_RANK and CUME_DIST
-- "Calculate the percentile rank of each claim's amount."
-- ============================================================

-- ANSWER:
SELECT 
    claim_id,
    claim_amount,
    ROUND(PERCENT_RANK() OVER (ORDER BY claim_amount) * 100, 2) as percentile_rank,
    ROUND(CUME_DIST() OVER (ORDER BY claim_amount) * 100, 2) as cumulative_dist
FROM Claims;

-- PERCENT_RANK: Relative rank as a percentage (0 to 1)
-- CUME_DIST: Percentage of rows <= current row

-- ============================================================
-- Q10: Practical Example - Identify Outliers
-- "Flag claims where the amount is more than 2 standard deviations from the mean."
-- ============================================================

-- ANSWER:
WITH Stats AS (
    SELECT 
        AVG(claim_amount) as mean_amount,
        STDDEV(claim_amount) as std_amount
    FROM Claims
)
SELECT 
    c.claim_id,
    c.claim_amount,
    CASE 
        WHEN c.claim_amount > s.mean_amount + 2 * s.std_amount THEN 'High Outlier'
        WHEN c.claim_amount < s.mean_amount - 2 * s.std_amount THEN 'Low Outlier'
        ELSE 'Normal'
    END as outlier_flag
FROM Claims c
CROSS JOIN Stats s;

-- INTERVIEW TIP: This is a common data quality check in insurance.
-- Outliers might indicate fraud or data entry errors.
