-- ============================================================
-- SQL TRICKY QUESTIONS - NULL Behavior & Gotchas
-- ============================================================
-- Swiss Re Interview Prep: Senior Application Engineer
-- Topic: NULL handling, edge cases, and common mistakes
-- ============================================================
-- THESE ARE THE QUESTIONS THAT TRIP UP EVEN EXPERIENCED DEVS!
-- ============================================================

-- ============================================================
-- Q1: NULL Comparison (THE #1 GOTCHA!)
-- ============================================================

/*
QUESTION: How many rows does this return?

SELECT * FROM Employees WHERE department != 'Sales';

If table has: 'Sales', 'IT', NULL

ANSWER: Only 1 row ('IT')!

NULL != 'Sales' is NOT TRUE, it's UNKNOWN.
Rows with UNKNOWN are filtered out.
*/

-- Example data
-- | id | department |
-- |----|------------|
-- | 1  | Sales      |
-- | 2  | IT         |
-- | 3  | NULL       |

-- This returns ONLY 'IT' (NOT the NULL row!)
SELECT * FROM Employees WHERE department != 'Sales';

-- To include NULLs, you must explicitly check:
SELECT * FROM Employees 
WHERE department != 'Sales' OR department IS NULL;

-- Or use COALESCE:
SELECT * FROM Employees 
WHERE COALESCE(department, 'NONE') != 'Sales';

-- ============================================================
-- Q2: NULL in Aggregations
-- ============================================================

/*
QUESTION: What's the difference between COUNT(*) and COUNT(column)?

ANSWER:
- COUNT(*) counts ALL rows, including NULLs
- COUNT(column) counts only NON-NULL values in that column
*/

-- Example:
-- | id | bonus |
-- |----|-------|
-- | 1  | 100   |
-- | 2  | NULL  |
-- | 3  | 200   |

SELECT 
    COUNT(*) as total_rows,        -- 3
    COUNT(bonus) as non_null_bonus, -- 2
    SUM(bonus) as sum_bonus,       -- 300 (NULLs ignored)
    AVG(bonus) as avg_bonus        -- 150 (300/2, NULLs ignored!)
FROM Employees;

-- GOTCHA: AVG ignores NULLs! If you want NULLs as 0:
SELECT 
    AVG(COALESCE(bonus, 0)) as avg_with_zeros  -- 100 (300/3)
FROM Employees;

-- ============================================================
-- Q3: NULL in JOINs
-- ============================================================

/*
QUESTION: Will NULL = NULL join rows together?

ANSWER: NO! NULL = NULL is UNKNOWN, not TRUE.
Rows with NULL keys will NOT join.
*/

-- Table A: | id | val |    Table B: | id | info |
--          | 1  | X   |             | 1  | A    |
--          | NULL | Y |             | NULL | B  |

-- INNER JOIN returns only 1 row (id=1), NOT the NULL=NULL match!
SELECT * FROM TableA a INNER JOIN TableB b ON a.id = b.id;
-- Result: 1 row

-- To join on NULLs, use COALESCE or explicit check:
SELECT * FROM TableA a 
INNER JOIN TableB b 
ON (a.id = b.id) OR (a.id IS NULL AND b.id IS NULL);

-- ============================================================
-- Q4: NULL in NOT IN (DANGEROUS!)
-- ============================================================

/*
QUESTION: What does this return if subquery contains NULL?

SELECT * FROM Employees WHERE id NOT IN (SELECT manager_id FROM Departments);

If manager_id has values: 1, 2, NULL

ANSWER: ZERO ROWS!

'id NOT IN (1, 2, NULL)' is equivalent to:
'id != 1 AND id != 2 AND id != NULL'
The last condition is UNKNOWN, making entire expression UNKNOWN.
*/

-- DANGEROUS: NOT IN with NULLs returns nothing!
SELECT * FROM Employees 
WHERE id NOT IN (SELECT manager_id FROM Departments);  -- May return 0 rows!

-- SAFE: Use NOT EXISTS instead
SELECT * FROM Employees e
WHERE NOT EXISTS (
    SELECT 1 FROM Departments d WHERE d.manager_id = e.id
);

-- SAFE: Exclude NULLs from subquery
SELECT * FROM Employees 
WHERE id NOT IN (SELECT manager_id FROM Departments WHERE manager_id IS NOT NULL);

-- ============================================================
-- Q5: COALESCE vs NULLIF vs IFNULL
-- ============================================================

/*
COALESCE(a, b, c): Returns first non-NULL value
NULLIF(a, b): Returns NULL if a = b, otherwise returns a
IFNULL(a, b): (MySQL) Same as COALESCE(a, b)
NVL(a, b): (Oracle) Same as COALESCE(a, b)
*/

SELECT 
    COALESCE(NULL, NULL, 'third') as coalesce_result,  -- 'third'
    NULLIF(5, 5) as nullif_equal,                       -- NULL
    NULLIF(5, 6) as nullif_different,                   -- 5
    COALESCE(column_a, column_b, 'default') as fallback
FROM SomeTable;

-- Prevent division by zero:
SELECT 
    numerator / NULLIF(denominator, 0) as safe_division  -- Returns NULL instead of error
FROM Numbers;

-- ============================================================
-- Q6: NULL Ordering
-- ============================================================

/*
QUESTION: Where do NULLs appear when you ORDER BY?

ANSWER: It depends on the database!
- PostgreSQL: NULLs are LAST for ASC, FIRST for DESC (by default)
- Oracle: NULLs are LAST (always, unless specified)
- MySQL: NULLs are FIRST for ASC
- SQL Server: NULLs are FIRST for ASC
*/

-- Control NULL ordering explicitly:
SELECT * FROM Employees 
ORDER BY department NULLS FIRST;

SELECT * FROM Employees 
ORDER BY department NULLS LAST;

-- For databases that don't support NULLS FIRST/LAST:
SELECT * FROM Employees 
ORDER BY 
    CASE WHEN department IS NULL THEN 1 ELSE 0 END,
    department;

-- ============================================================
-- Q7: Tricky GROUP BY with NULLs
-- ============================================================

/*
QUESTION: How does GROUP BY treat NULL values?

ANSWER: All NULLs are grouped together as ONE group!
*/

-- | department |
-- |------------|
-- | Sales      |
-- | IT         |
-- | NULL       |
-- | NULL       |

SELECT department, COUNT(*) 
FROM Employees 
GROUP BY department;

-- Result:
-- | department | count |
-- |------------|-------|
-- | Sales      | 1     |
-- | IT         | 1     |
-- | NULL       | 2     |  <-- All NULLs grouped together!

-- ============================================================
-- Q8: CASE WHEN with NULLs
-- ============================================================

/*
GOTCHA: CASE WHEN column = NULL doesn't work!
*/

-- WRONG:
SELECT 
    CASE department
        WHEN NULL THEN 'No Dept'    -- This will NEVER match!
        ELSE department
    END as dept_name
FROM Employees;

-- CORRECT:
SELECT 
    CASE 
        WHEN department IS NULL THEN 'No Dept'
        ELSE department
    END as dept_name
FROM Employees;

-- Also correct: Use COALESCE
SELECT COALESCE(department, 'No Dept') as dept_name FROM Employees;

-- ============================================================
-- Q9: String Concatenation with NULLs
-- ============================================================

/*
QUESTION: What does 'Hello' || NULL return?

ANSWER: It depends!
- PostgreSQL: NULL (NULL "poisons" the result)
- MySQL CONCAT: 'Hello' (NULL is ignored)
- SQL Server +: NULL (NULL poisons)
*/

-- PostgreSQL/Oracle (standard):
SELECT 'Hello' || NULL || 'World';  -- Returns NULL!

-- To handle:
SELECT COALESCE(first_name || ' ', '') || last_name FROM Employees;

-- Or use CONCAT_WS (concatenate with separator):
SELECT CONCAT_WS(' ', first_name, middle_name, last_name) FROM Employees;

-- ============================================================
-- Q10: Boolean Logic with NULLs (Three-Valued Logic)
-- ============================================================

/*
QUESTION: What's TRUE AND NULL?

ANSWER:
| A     | B     | A AND B | A OR B  |
|-------|-------|---------|---------|
| TRUE  | TRUE  | TRUE    | TRUE    |
| TRUE  | FALSE | FALSE   | TRUE    |
| TRUE  | NULL  | NULL    | TRUE    |  <-- Tricky!
| FALSE | NULL  | FALSE   | NULL    |  <-- Tricky!
| NULL  | NULL  | NULL    | NULL    |
*/

-- Example:
SELECT * FROM Employees
WHERE is_active = TRUE AND department = NULL;  -- Never matches!

-- Use IS NULL:
SELECT * FROM Employees
WHERE is_active = TRUE AND department IS NULL;

-- ============================================================
-- BONUS: DISTINCT and NULLs
-- ============================================================

/*
QUESTION: Does SELECT DISTINCT include NULL?

ANSWER: Yes! DISTINCT treats all NULLs as ONE value.
*/

-- | department |
-- |------------|
-- | Sales      |
-- | IT         |
-- | NULL       |
-- | NULL       |

SELECT DISTINCT department FROM Employees;
-- Result: Sales, IT, NULL (3 rows, NULLs combined)

-- ============================================================
-- CHEAT SHEET: NULL-Safe Comparisons
-- ============================================================

/*
| Standard SQL          | NULL-Safe Alternative                    |
|-----------------------|------------------------------------------|
| a = b                 | a IS NOT DISTINCT FROM b (PostgreSQL)   |
| a = b                 | a <=> b (MySQL)                          |
| a != b                | a IS DISTINCT FROM b (PostgreSQL)        |
| a != b OR a IS NULL   | COALESCE(a, '') != COALESCE(b, '')      |
| WHERE x = value       | WHERE x IS NOT NULL AND x = value       |
| COUNT(*)              | COUNT(column) (if you want non-nulls)   |
| NOT IN (subquery)     | NOT EXISTS (subquery)                   |
*/
