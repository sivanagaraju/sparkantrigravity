-- ============================================================
-- SQL ADVANCED PATTERNS - Lead Engineer Interview
-- ============================================================
-- Topic: EXCEPT, INTERSECT, Date Functions, Constraints, Window Deep Dive
-- ============================================================

-- ============================================================
-- Q1: EXCEPT, INTERSECT, UNION
-- ============================================================

-- UNION ALL: Combine all rows (duplicates kept)
SELECT id, name FROM table_a
UNION ALL
SELECT id, name FROM table_b;

-- UNION: Combine unique rows (duplicates removed)
SELECT id, name FROM table_a
UNION
SELECT id, name FROM table_b;

-- INTERSECT: Rows in BOTH tables
SELECT id, name FROM table_a
INTERSECT
SELECT id, name FROM table_b;

-- EXCEPT: Rows in first but NOT in second
SELECT id, name FROM table_a
EXCEPT
SELECT id, name FROM table_b;

-- PRACTICAL: Find customers who ordered but never returned
SELECT customer_id FROM orders
EXCEPT
SELECT customer_id FROM returns;

-- ============================================================
-- Q2: Window Functions Deep Dive
-- ============================================================

-- RANKING FUNCTIONS
SELECT 
    name,
    department,
    salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as row_num,  -- 1,2,3,4
    RANK()       OVER (PARTITION BY department ORDER BY salary DESC) as rank,      -- 1,1,3,4 (gaps)
    DENSE_RANK() OVER (PARTITION BY department ORDER BY salary DESC) as dense_rank,-- 1,1,2,3 (no gaps)
    NTILE(4)     OVER (PARTITION BY department ORDER BY salary DESC) as quartile   -- 1,1,2,2,3,3,4,4
FROM employees;

-- OFFSET FUNCTIONS
SELECT 
    date,
    sales,
    LAG(sales, 1, 0)  OVER (ORDER BY date) as prev_day_sales,      -- Previous row
    LEAD(sales, 1, 0) OVER (ORDER BY date) as next_day_sales,      -- Next row
    FIRST_VALUE(sales) OVER (ORDER BY date) as first_sale,         -- First in window
    LAST_VALUE(sales) OVER (
        ORDER BY date
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING   -- CRITICAL for LAST_VALUE!
    ) as last_sale
FROM daily_sales;

-- AGGREGATE WINDOW FUNCTIONS
SELECT 
    date,
    amount,
    SUM(amount) OVER (ORDER BY date) as running_total,              -- Running sum
    SUM(amount) OVER (
        ORDER BY date 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) as moving_3_day_sum,                                          -- Moving window
    AVG(amount) OVER (
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as moving_7_day_avg,                                          -- 7-day average
    SUM(amount) OVER () as grand_total,                             -- Total across all rows
    amount / SUM(amount) OVER () * 100 as pct_of_total             -- Percentage of total
FROM transactions;

-- PERCENT RANK and CUME_DIST
SELECT 
    name,
    score,
    PERCENT_RANK() OVER (ORDER BY score) as percentile,            -- (rank-1)/(n-1)
    CUME_DIST() OVER (ORDER BY score) as cumulative_dist           -- rank/n
FROM students;

-- ============================================================
-- Q3: Window Frame Specifications
-- ============================================================

/*
ROWS BETWEEN <start> AND <end>

<start>/<end> options:
- UNBOUNDED PRECEDING: First row of partition
- n PRECEDING: n rows before current
- CURRENT ROW: Current row
- n FOLLOWING: n rows after current
- UNBOUNDED FOLLOWING: Last row of partition

DEFAULT: RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
*/

-- Current row and all previous
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW

-- Previous 2 rows and next 2 rows (5-row window)
ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING

-- All rows in partition
ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING

-- RANGE vs ROWS
-- RANGE: Includes all rows with same ORDER BY value
-- ROWS: Exact row positions

-- ============================================================
-- Q4: Date Functions
-- ============================================================

-- Current date/time
SELECT 
    CURRENT_DATE,                    -- 2024-01-15
    CURRENT_TIMESTAMP,               -- 2024-01-15 10:30:00
    NOW();                           -- Same as CURRENT_TIMESTAMP

-- Date parts
SELECT 
    YEAR(date_col),                  -- 2024
    MONTH(date_col),                 -- 1
    DAY(date_col),                   -- 15
    DAYOFWEEK(date_col),             -- 1-7 (Sunday=1)
    DAYOFYEAR(date_col),             -- 1-365
    WEEKOFYEAR(date_col),            -- 1-52
    QUARTER(date_col);               -- 1-4

-- Date arithmetic
SELECT 
    DATE_ADD(date_col, 7),           -- Add 7 days
    DATE_SUB(date_col, 7),           -- Subtract 7 days
    DATEDIFF(end_date, start_date),  -- Days between
    MONTHS_BETWEEN(d1, d2),          -- Months between
    ADD_MONTHS(date_col, 3);         -- Add 3 months

-- Date truncation
SELECT 
    DATE_TRUNC('MONTH', date_col),   -- First of month
    DATE_TRUNC('YEAR', date_col),    -- First of year
    DATE_TRUNC('WEEK', date_col);    -- First day of week

-- Date formatting
SELECT 
    DATE_FORMAT(date_col, 'yyyy-MM-dd'),
    DATE_FORMAT(date_col, 'MMMM dd, yyyy'),
    TO_DATE('2024-01-15', 'yyyy-MM-dd'),
    TO_TIMESTAMP('2024-01-15 10:30:00', 'yyyy-MM-dd HH:mm:ss');

-- ============================================================
-- Q5: SQL Constraints
-- ============================================================

-- PRIMARY KEY (unique + not null)
CREATE TABLE customers (
    id INT PRIMARY KEY,
    name VARCHAR(100)
);

-- COMPOSITE PRIMARY KEY
CREATE TABLE order_items (
    order_id INT,
    product_id INT,
    quantity INT,
    PRIMARY KEY (order_id, product_id)
);

-- FOREIGN KEY
CREATE TABLE orders (
    id INT PRIMARY KEY,
    customer_id INT,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- UNIQUE
CREATE TABLE users (
    id INT PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    username VARCHAR(50) UNIQUE
);

-- CHECK
CREATE TABLE products (
    id INT PRIMARY KEY,
    price DECIMAL(10,2) CHECK (price > 0),
    quantity INT CHECK (quantity >= 0)
);

-- NOT NULL
CREATE TABLE employees (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL
);

-- DEFAULT
CREATE TABLE audit_log (
    id INT PRIMARY KEY,
    action VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Q6: Correlated Subqueries vs Joins
-- ============================================================

-- CORRELATED SUBQUERY: Uses outer query reference
SELECT e1.name, e1.salary, e1.department
FROM employees e1
WHERE e1.salary > (
    SELECT AVG(e2.salary)
    FROM employees e2
    WHERE e2.department = e1.department  -- References outer query!
);

-- EQUIVALENT JOIN (often more efficient)
SELECT e.name, e.salary, e.department
FROM employees e
JOIN (
    SELECT department, AVG(salary) as avg_salary
    FROM employees
    GROUP BY department
) dept_avg ON e.department = dept_avg.department
WHERE e.salary > dept_avg.avg_salary;

-- EXISTS (correlated)
SELECT c.name
FROM customers c
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.id
);

-- ============================================================
-- Q7: When Subquery vs Join vs CTE
-- ============================================================

/*
USE SUBQUERY WHEN:
- Simple, one-time reference
- Scalar value needed (SELECT in column)
- EXISTS/NOT EXISTS check

USE JOIN WHEN:
- Need columns from both tables
- Multiple references to same data
- Performance critical (usually faster)

USE CTE WHEN:
- Complex, multi-step logic
- Same subquery used multiple times
- Recursive queries needed
- Readability matters
*/

-- SUBQUERY in SELECT (scalar)
SELECT 
    name,
    salary,
    (SELECT AVG(salary) FROM employees) as company_avg
FROM employees;

-- SUBQUERY in FROM (derived table)
SELECT *
FROM (
    SELECT department, AVG(salary) as avg_salary
    FROM employees
    GROUP BY department
) dept_summary
WHERE avg_salary > 50000;

-- ============================================================
-- Q8: GROUP BY Advanced
-- ============================================================

-- GROUPING SETS
SELECT region, product, SUM(sales)
FROM sales
GROUP BY GROUPING SETS (
    (region, product),  -- Group by both
    (region),           -- Group by region only
    (product),          -- Group by product only
    ()                  -- Grand total
);

-- ROLLUP (hierarchical)
SELECT region, product, SUM(sales)
FROM sales
GROUP BY ROLLUP (region, product);
-- Equivalent to GROUPING SETS ((region, product), (region), ())

-- CUBE (all combinations)
SELECT region, product, SUM(sales)
FROM sales
GROUP BY CUBE (region, product);
-- Equivalent to GROUPING SETS ((region, product), (region), (product), ())

-- GROUPING function (identify which level)
SELECT 
    region,
    product,
    SUM(sales),
    GROUPING(region) as region_grouped,
    GROUPING(product) as product_grouped
FROM sales
GROUP BY CUBE (region, product);

-- ============================================================
-- Q9: Array and Map Functions (Spark SQL)
-- ============================================================

-- EXPLODE: Array to rows
SELECT id, exploded_item
FROM orders
LATERAL VIEW EXPLODE(items) t AS exploded_item;

-- Alternative syntax
SELECT id, item
FROM orders, LATERAL VIEW EXPLODE(items) AS item;

-- COLLECT_LIST: Rows to array
SELECT customer_id, COLLECT_LIST(product) as products
FROM orders
GROUP BY customer_id;

-- COLLECT_SET: Rows to unique array
SELECT customer_id, COLLECT_SET(category) as categories
FROM orders
GROUP BY customer_id;

-- ARRAY functions
SELECT 
    ARRAY(1, 2, 3),                     -- Create array
    ARRAY_CONTAINS(arr, 2),             -- Check if contains
    SIZE(arr),                          -- Length
    ARRAY_DISTINCT(arr),                -- Remove duplicates
    ARRAY_SORT(arr),                    -- Sort
    ARRAY_JOIN(arr, ','),               -- Join to string
    SLICE(arr, 1, 3);                   -- Slice (1-indexed)

-- ============================================================
-- Q10: Performance Tips
-- ============================================================

/*
QUERY OPTIMIZATION CHECKLIST:

1. Use indexes on WHERE, JOIN, ORDER BY columns
2. Filter early (WHERE before JOIN)
3. Avoid SELECT * (select only needed columns)
4. Use EXISTS instead of IN for subqueries
5. Avoid functions on indexed columns in WHERE
6. Use LIMIT for debugging/sampling
7. Analyze query plan (EXPLAIN ANALYZE)
8. Partition large tables
9. Update statistics regularly
10. Consider materialized views for complex aggregations
*/

-- Anti-pattern: Function on indexed column
SELECT * FROM orders WHERE YEAR(order_date) = 2024;  -- No index use!

-- Better: Range condition
SELECT * FROM orders 
WHERE order_date >= '2024-01-01' AND order_date < '2025-01-01';  -- Uses index
