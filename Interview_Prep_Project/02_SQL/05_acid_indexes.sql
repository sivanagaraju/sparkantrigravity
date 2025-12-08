-- ============================================================
-- DATABASE CONCEPTS - ACID, Indexes, and Performance
-- ============================================================
-- Swiss Re Interview Prep: Senior Application Engineer
-- Topic: ACID Properties, Index Types, Query Optimization
-- ============================================================

-- ============================================================
-- Q1: ACID Properties
-- ============================================================

/*
QUESTION: What are ACID properties?

ANSWER:

A = ATOMICITY
    "All or Nothing"
    - Transaction either completes fully or not at all
    - If any part fails, entire transaction is rolled back
    - Example: Bank transfer (debit AND credit must both succeed)

C = CONSISTENCY
    "Valid State to Valid State"
    - Database always remains in a consistent state
    - All constraints, triggers, rules are enforced
    - Example: Account balance can never be negative (if that's a rule)

I = ISOLATION
    "Transactions Don't Interfere"
    - Concurrent transactions appear to run sequentially
    - Each transaction is isolated from others
    - Different isolation levels: READ UNCOMMITTED, READ COMMITTED,
      REPEATABLE READ, SERIALIZABLE

D = DURABILITY
    "Committed = Permanent"
    - Once committed, data survives system failures
    - Changes are written to persistent storage
    - Transaction logs enable recovery
*/

-- EXAMPLE: ACID in action
BEGIN TRANSACTION;

-- Debit from Account A
UPDATE Accounts SET balance = balance - 100 WHERE account_id = 'A';

-- Credit to Account B
UPDATE Accounts SET balance = balance + 100 WHERE account_id = 'B';

-- If both succeed, commit
COMMIT;

-- If anything fails, everything is rolled back (ATOMICITY)
-- ROLLBACK;

-- ============================================================
-- Q2: Isolation Levels
-- ============================================================

/*
QUESTION: Explain different isolation levels.

ANSWER:

| Level              | Dirty Read | Non-Repeatable Read | Phantom Read |
|--------------------|------------|---------------------|--------------|
| READ UNCOMMITTED   | Possible   | Possible            | Possible     |
| READ COMMITTED     | Prevented  | Possible            | Possible     |
| REPEATABLE READ    | Prevented  | Prevented           | Possible     |
| SERIALIZABLE       | Prevented  | Prevented           | Prevented    |

PHENOMENA EXPLAINED:

DIRTY READ: Reading uncommitted data from another transaction
  - T1 updates a row but hasn't committed
  - T2 reads the updated value
  - T1 rolls back
  - T2 has read "dirty" data that never existed

NON-REPEATABLE READ: Same query returns different results
  - T1 reads a row
  - T2 updates and commits that row
  - T1 reads again - gets different value!

PHANTOM READ: New rows appear in repeated queries
  - T1 queries WHERE salary > 50000 (gets 10 rows)
  - T2 inserts a new row with salary 60000
  - T1 queries again - gets 11 rows (a "phantom"!)

DEFAULT LEVELS:
- PostgreSQL: READ COMMITTED
- MySQL (InnoDB): REPEATABLE READ
- SQL Server: READ COMMITTED
- Oracle: READ COMMITTED
*/

-- Set isolation level
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- ============================================================
-- Q3: Index Types
-- ============================================================

/*
QUESTION: What types of indexes are there and when to use each?

ANSWER:

1. B-TREE INDEX (Default, most common)
   - Balanced tree structure
   - Good for: =, <, >, BETWEEN, ORDER BY
   - Use for: Most columns, primary keys, foreign keys

2. HASH INDEX
   - Hash table structure
   - Good for: = (equality only)
   - Not good for: range queries, ORDER BY
   - Use for: Exact match lookups

3. GIN (Generalized Inverted Index)
   - For composite values (arrays, JSON, full-text)
   - Good for: CONTAINS, @>, full-text search
   - Use for: JSONB columns, array columns

4. GiST (Generalized Search Tree)
   - For geometric/spatial data
   - Good for: Nearest neighbor, overlap, contains
   - Use for: PostGIS, geometric queries

5. BRIN (Block Range Index)
   - Stores min/max per block of pages
   - Very small, good for sorted data
   - Use for: Timestamp columns in append-only tables

6. BITMAP INDEX (Oracle, PostgreSQL uses on-the-fly)
   - Bit array for each distinct value
   - Good for: Low cardinality columns (status, type)
   - Use for: Columns with few distinct values
*/

-- Create B-tree index (default)
CREATE INDEX idx_claims_date ON Claims(claim_date);

-- Create composite index (multiple columns)
CREATE INDEX idx_claims_region_date ON Claims(region, claim_date);

-- Create partial index (only specific rows)
CREATE INDEX idx_urgent_claims ON Claims(claim_id) 
WHERE claim_priority = 'Urgent';

-- Create covering index (includes non-key columns)
CREATE INDEX idx_claims_covering ON Claims(policyholder_id) 
INCLUDE (claim_amount, claim_date);

-- ============================================================
-- Q4: Index Selection Guidelines
-- ============================================================

/*
QUESTION: How do you decide which columns to index?

ANSWER:

INDEX THESE:
✓ Primary keys (automatic)
✓ Foreign keys (for JOIN performance)
✓ Columns in WHERE clauses (frequently filtered)
✓ Columns in ORDER BY (for sorted output)
✓ Columns in GROUP BY (for aggregations)
✓ Columns with high selectivity (many distinct values)

DON'T INDEX:
✗ Small tables (full scan is fast enough)
✗ Columns rarely used in queries
✗ Columns with low selectivity (boolean, status with 3 values)
✗ Frequently updated columns (index maintenance overhead)
✗ Wide columns (long text)

COMPOSITE INDEX RULES:
- Put most selective column first
- Put equality columns before range columns
- Order matters! (region, date) != (date, region)
*/

-- ============================================================
-- Q5: Index Gotchas
-- ============================================================

/*
QUESTION: When does an index NOT get used?

ANSWER:

1. FUNCTION ON INDEXED COLUMN
   WHERE UPPER(name) = 'JOHN'  -- Index on 'name' NOT used!
   FIX: Create functional index or change query

2. TYPE MISMATCH
   WHERE id = '123'  -- id is INT but comparing to STRING
   FIX: Ensure types match

3. LEADING WILDCARD
   WHERE name LIKE '%Smith'  -- Index NOT used!
   WHERE name LIKE 'Smith%'  -- Index IS used

4. OR CONDITIONS
   WHERE col1 = 'A' OR col2 = 'B'  -- May not use indexes efficiently
   FIX: Use UNION or ensure both columns are indexed

5. NOT, != CONDITIONS
   WHERE status != 'CLOSED'  -- Often does full scan
   FIX: Rewrite as positive condition if possible

6. NULL CHECKS (sometimes)
   WHERE column IS NULL  -- Depends on database and index

7. LOW SELECTIVITY
   WHERE gender = 'M'  -- If table is 50% M, full scan might be faster
*/

-- Bad: Function on column
SELECT * FROM Employees WHERE LOWER(name) = 'john';

-- Good: Functional index
CREATE INDEX idx_name_lower ON Employees(LOWER(name));
SELECT * FROM Employees WHERE LOWER(name) = 'john';

-- ============================================================
-- Q6: EXPLAIN ANALYZE - Reading Query Plans
-- ============================================================

/*
QUESTION: How do you analyze query performance?

ANSWER: Use EXPLAIN ANALYZE to see the execution plan.

KEY THINGS TO LOOK FOR:
1. Seq Scan vs Index Scan
   - Seq Scan = Full table scan (often bad for large tables)
   - Index Scan = Using an index (usually good)
   - Index Only Scan = Even better (no table access)

2. Join Types
   - Nested Loop: Good for small tables or indexed columns
   - Hash Join: Good for large tables, equality joins
   - Merge Join: Good for sorted data, large tables

3. Cost Numbers
   - Format: (startup cost..total cost)
   - Lower is better
   - Compare before and after optimization

4. Actual Time
   - actual time=X..Y (in milliseconds)
   - Loops = how many times this step ran
*/

-- PostgreSQL
EXPLAIN ANALYZE 
SELECT * FROM Claims WHERE claim_date > '2024-01-01';

-- Look for:
-- "Seq Scan" = bad for large tables
-- "Index Scan using idx_claims_date" = good!
-- "Bitmap Index Scan" = good for multiple conditions

-- ============================================================
-- Q7: Query Optimization Techniques
-- ============================================================

/*
QUESTION: How do you optimize a slow query?

ANSWER: Follow this checklist:

1. CHECK INDEXES
   - Are there indexes on WHERE, JOIN, ORDER BY columns?
   - Is the index being used? (Check EXPLAIN)

2. REWRITE THE QUERY
   - Avoid SELECT * (select only needed columns)
   - Avoid functions on indexed columns
   - Use EXISTS instead of IN for subqueries
   - Break complex queries into simpler steps

3. OPTIMIZE JOINS
   - Ensure join columns are indexed
   - Put smaller tables first (or let optimizer handle it)
   - Use broadcast/hash hints if available

4. LIMIT DATA EARLY
   - Filter as early as possible
   - Use LIMIT for top-N queries
   - Partition large tables

5. CONSIDER DENORMALIZATION
   - Pre-compute expensive aggregations
   - Store redundant data to avoid joins
   - Use materialized views
*/

-- Bad: SELECT *
SELECT * FROM Claims WHERE region = 'North';

-- Good: Select only needed columns
SELECT claim_id, claim_amount FROM Claims WHERE region = 'North';

-- Bad: Subquery with IN
SELECT * FROM Employees 
WHERE dept_id IN (SELECT id FROM Departments WHERE region = 'North');

-- Good: JOIN or EXISTS
SELECT e.* FROM Employees e
WHERE EXISTS (
    SELECT 1 FROM Departments d 
    WHERE d.id = e.dept_id AND d.region = 'North'
);

-- ============================================================
-- Q8: Partitioning
-- ============================================================

/*
QUESTION: What is table partitioning and when should you use it?

ANSWER:

PARTITIONING = Dividing a large table into smaller, manageable pieces.

TYPES:
1. RANGE PARTITIONING
   - By date ranges (most common)
   - Partition by: year, month, day

2. LIST PARTITIONING
   - By specific values
   - Partition by: region, country, status

3. HASH PARTITIONING
   - By hash of a column
   - Distributes data evenly

BENEFITS:
- Faster queries (partition pruning)
- Easier maintenance (drop old partitions)
- Parallel query execution

WHEN TO USE:
- Tables with millions+ rows
- Clear partition key (date, region)
- Queries consistently filter by partition key
- Need to archive old data regularly
*/

-- PostgreSQL 10+ declarative partitioning
CREATE TABLE Claims (
    claim_id SERIAL,
    claim_date DATE,
    claim_amount NUMERIC
) PARTITION BY RANGE (claim_date);

CREATE TABLE Claims_2024_Q1 PARTITION OF Claims
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE Claims_2024_Q2 PARTITION OF Claims
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

-- Query automatically uses only relevant partitions
SELECT * FROM Claims WHERE claim_date = '2024-02-15';
-- Only Claims_2024_Q1 is scanned!

-- ============================================================
-- Q9: Transactions and Locking
-- ============================================================

/*
QUESTION: Explain database locking.

ANSWER:

LOCK TYPES:
1. SHARED LOCK (S) / READ LOCK
   - Multiple transactions can hold simultaneously
   - Prevents writes while reading

2. EXCLUSIVE LOCK (X) / WRITE LOCK
   - Only one transaction can hold
   - Blocks all other reads and writes

LOCK GRANULARITY:
- Row-level: Locks specific rows (fine-grained, less contention)
- Page-level: Locks a page of data
- Table-level: Locks entire table (coarse, high contention)

DEADLOCK:
- T1 holds Lock A, waiting for Lock B
- T2 holds Lock B, waiting for Lock A
- Neither can proceed!
- Database detects and kills one transaction

PREVENT DEADLOCKS:
- Access tables in consistent order
- Keep transactions short
- Use lower isolation levels if possible
*/

-- Explicit locking (PostgreSQL)
BEGIN;
SELECT * FROM Accounts WHERE id = 1 FOR UPDATE;  -- Row is locked
UPDATE Accounts SET balance = balance - 100 WHERE id = 1;
COMMIT;  -- Lock released

-- ============================================================
-- Q10: Delta Lake ACID (For Spark Context)
-- ============================================================

/*
QUESTION: How does Delta Lake provide ACID on a data lake?

ANSWER:

Delta Lake adds ACID to Parquet files using a TRANSACTION LOG (_delta_log/).

1. ATOMICITY
   - Each write is a single commit
   - If write fails, previous version remains

2. CONSISTENCY
   - Schema enforcement
   - Constraints (CHECK constraints in Delta 2.1+)

3. ISOLATION
   - Optimistic concurrency control
   - Writers check the log before committing
   - Conflicts are detected and resolved

4. DURABILITY
   - Data stored in Parquet (durable)
   - Transaction log is replicated

TRANSACTION LOG:
_delta_log/
  - 00000000000000000000.json  (Initial commit)
  - 00000000000000000001.json  (Second commit)
  - 00000000000000000002.json  (Third commit)
  - ...

Each JSON file records:
- Files added
- Files removed
- Schema changes
- Metadata

TIME TRAVEL:
Read any previous version using the log!
*/
