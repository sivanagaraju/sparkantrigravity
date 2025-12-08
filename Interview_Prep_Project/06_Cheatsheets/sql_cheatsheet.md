# SQL CHEATSHEET - Interview Quick Reference

## 🔥 MEMORY TRICKS

### Window Functions Order
**"PROWS"** = **P**ARTITION BY, **R**OW_NUMBER, **O**RDER BY, **W**INDOW frame, **S**elect
```sql
SELECT col,
    ROW_NUMBER() OVER (PARTITION BY x ORDER BY y) as rn
```

### JOIN Types
**"LEFT = All Left + Matching Right"**
```
INNER: ∩ (intersection only)
LEFT:  ◀━━ (all left + matching right)
RIGHT: ━━▶ (all right + matching left)
FULL:  ◀━━━▶ (all from both)
```

### NULL Danger
**"NULL poisons everything"**
- `NULL = NULL` → NOT TRUE (it's UNKNOWN)
- `NOT IN (subquery with NULL)` → Returns NOTHING!

---

## 📊 WINDOW FUNCTIONS

### Ranking
```sql
-- ROW_NUMBER: Unique (1,2,3,4)
-- RANK: Gaps (1,1,3,4)
-- DENSE_RANK: No gaps (1,1,2,3)

SELECT 
    employee_id,
    salary,
    ROW_NUMBER() OVER (ORDER BY salary DESC) as row_num,
    RANK()       OVER (ORDER BY salary DESC) as rank,
    DENSE_RANK() OVER (ORDER BY salary DESC) as dense_rank
FROM employees;
```

### Running Totals & Moving Averages
```sql
-- Running Total
SUM(amount) OVER (ORDER BY date ROWS UNBOUNDED PRECEDING)

-- Moving Average (last 3 rows)
AVG(amount) OVER (ORDER BY date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)

-- Year-to-Date
SUM(amount) OVER (PARTITION BY YEAR(date) ORDER BY date)
```

### LAG & LEAD
```sql
-- Previous value
LAG(value, 1) OVER (ORDER BY date)

-- Next value
LEAD(value, 1) OVER (ORDER BY date)

-- Month-over-Month Change
value - LAG(value) OVER (ORDER BY month) as mom_change
```

### FIRST_VALUE & LAST_VALUE
```sql
-- First in partition
FIRST_VALUE(name) OVER (PARTITION BY dept ORDER BY salary DESC)

-- Last in partition (MUST set frame!)
LAST_VALUE(name) OVER (
    PARTITION BY dept ORDER BY salary 
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
)
```

### NTILE (Percentiles)
```sql
-- Divide into 4 groups (quartiles)
NTILE(4) OVER (ORDER BY score) as quartile
```

---

## 📝 CTEs (Common Table Expressions)

### Basic CTE
```sql
WITH cte_name AS (
    SELECT col1, col2 FROM table WHERE condition
)
SELECT * FROM cte_name;
```

### Multiple CTEs
```sql
WITH 
    cte1 AS (SELECT ...),
    cte2 AS (SELECT ... FROM cte1),
    cte3 AS (SELECT ... FROM cte2)
SELECT * FROM cte3;
```

### Recursive CTE (Hierarchy)
```sql
WITH RECURSIVE hierarchy AS (
    -- ANCHOR: Starting point
    SELECT id, name, manager_id, 1 as level
    FROM employees WHERE manager_id IS NULL
    
    UNION ALL
    
    -- RECURSIVE: Join with previous level
    SELECT e.id, e.name, e.manager_id, h.level + 1
    FROM employees e
    INNER JOIN hierarchy h ON e.manager_id = h.id
)
SELECT * FROM hierarchy;
```

### Date Series Generation
```sql
WITH RECURSIVE dates AS (
    SELECT DATE '2024-01-01' as dt
    UNION ALL
    SELECT dt + INTERVAL '1 day' FROM dates WHERE dt < '2024-01-31'
)
SELECT * FROM dates;
```

---

## 🔄 SUBQUERIES

### Scalar Subquery (returns single value)
```sql
SELECT name, salary,
    (SELECT AVG(salary) FROM employees) as avg_salary
FROM employees;
```

### Correlated Subquery (references outer query)
```sql
SELECT * FROM employees e1
WHERE salary > (
    SELECT AVG(salary) FROM employees e2 
    WHERE e2.dept_id = e1.dept_id  -- References e1!
);
```

### EXISTS (for existence check)
```sql
-- Employees with orders
SELECT * FROM employees e
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.emp_id = e.id);

-- Employees WITHOUT orders
SELECT * FROM employees e
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.emp_id = e.id);
```

### IN vs EXISTS
```sql
-- Use IN for small lists
WHERE id IN (1, 2, 3, 4, 5)

-- Use EXISTS for large/complex subqueries
WHERE EXISTS (SELECT 1 FROM big_table WHERE ...)

-- NEVER use NOT IN with NULLs! Use NOT EXISTS
```

---

## 📊 AGGREGATIONS

### Basic Aggregates
```sql
COUNT(*)      -- All rows (including NULL)
COUNT(col)    -- Non-NULL values only
SUM(col)      -- Sum (ignores NULL)
AVG(col)      -- Average (ignores NULL!)
MIN(col)      -- Minimum
MAX(col)      -- Maximum
```

### GROUP BY with HAVING
```sql
SELECT dept, COUNT(*) as cnt, AVG(salary)
FROM employees
GROUP BY dept
HAVING COUNT(*) > 10;  -- Filter AFTER grouping
```

### ROLLUP (Subtotals)
```sql
SELECT region, product, SUM(sales)
FROM sales
GROUP BY ROLLUP (region, product);
-- Returns subtotals for each region + grand total
```

### CUBE (All Combinations)
```sql
SELECT region, product, SUM(sales)
FROM sales
GROUP BY CUBE (region, product);
-- Returns all possible subtotal combinations
```

### GROUPING SETS (Custom)
```sql
SELECT region, product, SUM(sales)
FROM sales
GROUP BY GROUPING SETS (
    (region, product),
    (region),
    ()  -- Grand total
);
```

---

## 🔗 JOINS

### Quick Reference
```sql
-- INNER: Only matches
FROM a INNER JOIN b ON a.id = b.id

-- LEFT: All from A, matching from B
FROM a LEFT JOIN b ON a.id = b.id

-- Find unmatched (A not in B)
FROM a LEFT JOIN b ON a.id = b.id WHERE b.id IS NULL

-- CROSS: Cartesian product
FROM a CROSS JOIN b
```

### Self Join
```sql
-- Employee with Manager name
SELECT e.name, m.name as manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;
```

---

## ⚠️ NULL HANDLING

### Safe Patterns
```sql
-- Check for NULL
WHERE col IS NULL
WHERE col IS NOT NULL

-- Replace NULL
COALESCE(col, 'default')
NULLIF(col, 0)  -- Returns NULL if col=0

-- NULL-safe comparison (PostgreSQL)
WHERE col1 IS NOT DISTINCT FROM col2

-- NULL-safe comparison (MySQL)
WHERE col1 <=> col2
```

### NULL Gotchas to Remember
```sql
-- ❌ WRONG: Returns only non-NULL rows that don't equal 'X'
WHERE col != 'X'

-- ✅ CORRECT: Include NULLs
WHERE col != 'X' OR col IS NULL

-- ❌ DANGER: Returns NOTHING if subquery has NULL
WHERE id NOT IN (SELECT id FROM table)

-- ✅ SAFE: Use NOT EXISTS
WHERE NOT EXISTS (SELECT 1 FROM table t WHERE t.id = outer.id)
```

---

## 🎯 COMMON PATTERNS

### Top N per Group
```sql
WITH ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY group_col ORDER BY val DESC) as rn
    FROM table
)
SELECT * FROM ranked WHERE rn <= 3;
```

### Gaps and Islands
```sql
WITH flagged AS (
    SELECT *, 
        CASE WHEN event_time - LAG(event_time) OVER (ORDER BY event_time) > INTERVAL '30 min'
             THEN 1 ELSE 0 END as new_session
    FROM events
)
SELECT *, SUM(new_session) OVER (ORDER BY event_time) as session_id
FROM flagged;
```

### Deduplication
```sql
WITH ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY email ORDER BY created_at DESC) as rn
    FROM users
)
DELETE FROM ranked WHERE rn > 1;
```

### Pivot (Rows to Columns)
```sql
SELECT 
    product,
    SUM(CASE WHEN month = 'Jan' THEN sales END) as jan,
    SUM(CASE WHEN month = 'Feb' THEN sales END) as feb
FROM sales
GROUP BY product;
```

---

## 💡 INTERVIEW TIPS

1. **Always clarify**: "Can there be NULLs?" "Are duplicates possible?"
2. **Start with CTE**: Makes complex queries readable
3. **Filter early**: Put WHERE before GROUP BY, JOIN
4. **Use window functions**: Show you know modern SQL
5. **Check edge cases**: Empty tables, NULL values, duplicates
