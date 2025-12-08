-- ============================================================
-- SQL INTERVIEW QUESTIONS - PART 2: JOINS & SUBQUERIES
-- ============================================================
-- Swiss Re Interview Prep: Senior Application Engineer
-- Topic: Complex Joins, Subqueries, and CTEs
-- ============================================================

-- ============================================================
-- Q1: All Join Types Explained
-- ============================================================

/*
ANSWER:

| Join Type   | Returns                                    | Use Case                          |
|-------------|--------------------------------------------|-----------------------------------|
| INNER JOIN  | Only matching rows                         | Claims WITH policyholders         |
| LEFT JOIN   | All left + matching right (NULL if none)   | All claims, policy info if exists |
| RIGHT JOIN  | All right + matching left                  | Rarely used, just reverse left    |
| FULL JOIN   | All from both (NULLs where no match)       | Reconciliation, finding orphans   |
| CROSS JOIN  | Cartesian product (M x N rows)             | Generate all combinations         |

INTERVIEW TIP: "I rarely use RIGHT JOIN; I prefer to reorder tables and use LEFT JOIN for clarity."
*/

-- EXAMPLE: LEFT JOIN to find claims without payments
SELECT 
    c.claim_id,
    c.claim_amount,
    p.payment_amount
FROM Claims c
LEFT JOIN Payments p ON c.claim_id = p.claim_id
WHERE p.payment_id IS NULL;  -- Claims with no payment

-- ============================================================
-- Q2: Self Join - Hierarchical Data
-- "Find all employee-manager pairs from an Employee table."
-- ============================================================

-- ANSWER:
SELECT 
    e.employee_id,
    e.name as employee_name,
    m.name as manager_name
FROM Employees e
LEFT JOIN Employees m ON e.manager_id = m.employee_id;

-- INTERVIEW TIP: Self-joins are common for hierarchical data like org charts.

-- ============================================================
-- Q3: Finding Duplicates
-- "Find policyholders who have more than one claim on the same day."
-- ============================================================

-- ANSWER:
SELECT 
    policyholder_id,
    claim_date,
    COUNT(*) as claim_count
FROM Claims
GROUP BY policyholder_id, claim_date
HAVING COUNT(*) > 1;

-- More detailed version with claim IDs:
WITH DuplicateDays AS (
    SELECT 
        policyholder_id,
        claim_date
    FROM Claims
    GROUP BY policyholder_id, claim_date
    HAVING COUNT(*) > 1
)
SELECT c.*
FROM Claims c
INNER JOIN DuplicateDays d 
    ON c.policyholder_id = d.policyholder_id 
    AND c.claim_date = d.claim_date
ORDER BY c.policyholder_id, c.claim_date;

-- ============================================================
-- Q4: Correlated Subquery
-- "Find claims where the amount is above the average for that region."
-- ============================================================

-- ANSWER (Correlated Subquery):
SELECT 
    claim_id,
    region,
    claim_amount
FROM Claims c1
WHERE claim_amount > (
    SELECT AVG(claim_amount) 
    FROM Claims c2 
    WHERE c2.region = c1.region
);

-- BETTER (Window Function - more efficient):
WITH RegionAvg AS (
    SELECT 
        claim_id,
        region,
        claim_amount,
        AVG(claim_amount) OVER (PARTITION BY region) as region_avg
    FROM Claims
)
SELECT claim_id, region, claim_amount
FROM RegionAvg
WHERE claim_amount > region_avg;

-- INTERVIEW TIP: "Correlated subqueries run once per row, which can be slow.
-- I prefer window functions or CTEs for better performance."

-- ============================================================
-- Q5: EXISTS vs IN - Performance Consideration
-- "Find claims that have at least one payment."
-- ============================================================

-- Using IN (Can be slow for large datasets):
SELECT *
FROM Claims
WHERE claim_id IN (SELECT DISTINCT claim_id FROM Payments);

-- Using EXISTS (Often faster):
SELECT *
FROM Claims c
WHERE EXISTS (
    SELECT 1 FROM Payments p WHERE p.claim_id = c.claim_id
);

/*
EXPLANATION:
- IN: Retrieves all values from subquery, then matches
- EXISTS: Stops as soon as it finds first match (short-circuit)

WHEN TO USE WHAT:
- Use IN if subquery returns small result set
- Use EXISTS if subquery returns large result set or you're checking existence
*/

-- ============================================================
-- Q6: NOT EXISTS - Anti-Join Pattern
-- "Find policyholders who have never made a claim."
-- ============================================================

-- ANSWER:
SELECT *
FROM Policyholders p
WHERE NOT EXISTS (
    SELECT 1 FROM Claims c WHERE c.policyholder_id = p.policyholder_id
);

-- Alternative (LEFT JOIN + IS NULL):
SELECT p.*
FROM Policyholders p
LEFT JOIN Claims c ON p.policyholder_id = c.policyholder_id
WHERE c.claim_id IS NULL;

-- INTERVIEW TIP: Both approaches are valid. LEFT JOIN might be clearer to some.

-- ============================================================
-- Q7: Multi-Table Join with Aggregation
-- "For each policyholder, show their name, total claims, and total payments."
-- ============================================================

-- ANSWER:
SELECT 
    p.policyholder_id,
    p.name,
    COALESCE(claim_summary.total_claims, 0) as total_claims,
    COALESCE(claim_summary.total_claim_amount, 0) as total_claim_amount,
    COALESCE(payment_summary.total_payments, 0) as total_payments
FROM Policyholders p
LEFT JOIN (
    SELECT 
        policyholder_id,
        COUNT(*) as total_claims,
        SUM(claim_amount) as total_claim_amount
    FROM Claims
    GROUP BY policyholder_id
) claim_summary ON p.policyholder_id = claim_summary.policyholder_id
LEFT JOIN (
    SELECT 
        c.policyholder_id,
        SUM(pay.payment_amount) as total_payments
    FROM Claims c
    INNER JOIN Payments pay ON c.claim_id = pay.claim_id
    GROUP BY c.policyholder_id
) payment_summary ON p.policyholder_id = payment_summary.policyholder_id;

-- INTERVIEW TIP: Use subqueries in the FROM clause to avoid duplicate counting issues.

-- ============================================================
-- Q8: UNION vs UNION ALL
-- "Combine two claim lists: Urgent claims and High-value claims."
-- ============================================================

-- UNION (Removes duplicates - slower):
SELECT claim_id, 'Urgent' as flag FROM Claims WHERE claim_priority = 'Urgent'
UNION
SELECT claim_id, 'High Value' as flag FROM Claims WHERE claim_amount > 10000;

-- UNION ALL (Keeps duplicates - faster):
SELECT claim_id, 'Urgent' as flag FROM Claims WHERE claim_priority = 'Urgent'
UNION ALL
SELECT claim_id, 'High Value' as flag FROM Claims WHERE claim_amount > 10000;

-- INTERVIEW TIP: "Use UNION ALL when you know there are no duplicates or when
-- you want to keep them. It's faster because it doesn't sort."

-- ============================================================
-- Q9: EXCEPT and INTERSECT
-- ============================================================

-- EXCEPT: Claims that are Urgent but NOT High Value
SELECT claim_id FROM Claims WHERE claim_priority = 'Urgent'
EXCEPT
SELECT claim_id FROM Claims WHERE claim_amount > 10000;

-- INTERSECT: Claims that are BOTH Urgent AND High Value
SELECT claim_id FROM Claims WHERE claim_priority = 'Urgent'
INTERSECT
SELECT claim_id FROM Claims WHERE claim_amount > 10000;

-- ============================================================
-- Q10: Practical Example - Data Reconciliation
-- "Find claims in System A that don't exist in System B."
-- ============================================================

-- ANSWER:
SELECT 
    a.claim_id,
    a.claim_amount as system_a_amount,
    b.claim_amount as system_b_amount
FROM SystemA_Claims a
LEFT JOIN SystemB_Claims b ON a.claim_id = b.claim_id
WHERE b.claim_id IS NULL
   OR a.claim_amount <> b.claim_amount;

-- This finds:
-- 1. Claims missing from System B (b.claim_id IS NULL)
-- 2. Claims where amounts don't match (a.claim_amount <> b.claim_amount)
