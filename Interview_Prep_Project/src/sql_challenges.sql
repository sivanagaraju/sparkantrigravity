-- =========================================================
-- SQL INTERVIEW CHALLENGES (Insurance Domain)
-- =========================================================

-- CONTEXT:
-- Table: Claims (claim_id, policyholder_id, claim_amount, claim_date, claim_type)
-- Table: Policyholders (policyholder_id, name, region, join_date)

-- ---------------------------------------------------------
-- QUESTION 1: Highest Claim per Region
-- "Find the policyholder with the highest claim amount in each region."
-- ---------------------------------------------------------

WITH RankedClaims AS (
    SELECT 
        p.region,
        p.name,
        c.claim_amount,
        ROW_NUMBER() OVER(PARTITION BY p.region ORDER BY c.claim_amount DESC) as rn
    FROM Claims c
    JOIN Policyholders p ON c.policyholder_id = p.policyholder_id
)
SELECT region, name, claim_amount
FROM RankedClaims
WHERE rn = 1;

-- ---------------------------------------------------------
-- QUESTION 2: Cumulative Claims (Running Total)
-- "Calculate the running total of claim amounts for each policyholder, ordered by date."
-- ---------------------------------------------------------

SELECT 
    policyholder_id,
    claim_date,
    claim_amount,
    SUM(claim_amount) OVER(PARTITION BY policyholder_id ORDER BY claim_date) as running_total
FROM Claims;

-- ---------------------------------------------------------
-- QUESTION 3: Year-over-Year Growth
-- "Calculate the total claim amount per year and the percentage growth from the previous year."
-- ---------------------------------------------------------

WITH YearlyTotals AS (
    SELECT 
        YEAR(claim_date) as claim_year,
        SUM(claim_amount) as total_amount
    FROM Claims
    GROUP BY YEAR(claim_date)
)
SELECT 
    claim_year,
    total_amount,
    LAG(total_amount) OVER(ORDER BY claim_year) as prev_year_amount,
    (total_amount - LAG(total_amount) OVER(ORDER BY claim_year)) / LAG(total_amount) OVER(ORDER BY claim_year) * 100 as growth_pct
FROM YearlyTotals;

-- ---------------------------------------------------------
-- QUESTION 4: Identify "Risky" Policyholders
-- "Find policyholders who have made more than 3 claims in any 30-day rolling window."
-- (This is a harder "Self-Join" or "Range Window" problem)
-- ---------------------------------------------------------

SELECT DISTINCT c1.policyholder_id
FROM Claims c1
JOIN Claims c2 ON c1.policyholder_id = c2.policyholder_id
    AND c2.claim_date BETWEEN c1.claim_date AND DATE_ADD(c1.claim_date, 30)
    AND c1.claim_id != c2.claim_id
GROUP BY c1.policyholder_id, c1.claim_id
HAVING COUNT(c2.claim_id) >= 2; -- c1 + 2 others = 3 total

-- ---------------------------------------------------------
-- QUESTION 5: Data Quality Check (Null Handling)
-- "Write a query to find claims where the policyholder_id does NOT exist in the Policyholders table."
-- ---------------------------------------------------------

SELECT c.claim_id
FROM Claims c
LEFT JOIN Policyholders p ON c.policyholder_id = p.policyholder_id
WHERE p.policyholder_id IS NULL;

-- OR using NOT EXISTS (often faster)
SELECT claim_id
FROM Claims c
WHERE NOT EXISTS (
    SELECT 1 FROM Policyholders p WHERE p.policyholder_id = c.policyholder_id
);
