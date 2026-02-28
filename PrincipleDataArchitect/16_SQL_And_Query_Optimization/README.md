# 16 — SQL & Query Optimization

> "SQL is the lingua franca of data. After 50 years, nothing has replaced it. A Principal who can't write a recursive CTE from memory is not ready."

At the Principal level, SQL mastery goes far beyond SELECT-FROM-WHERE. You must know analytical functions deeply, read EXPLAIN plans like a book, understand the query optimizer's decision-making, and write SQL that performs identically across Postgres, Snowflake, BigQuery, and Spark SQL.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_Advanced_Analytical_Functions/`

- **Window Functions**: `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `NTILE()`, `LEAD()`, `LAG()`, `FIRST_VALUE()`, `LAST_VALUE()`, `NTH_VALUE()`. Understanding `ROWS BETWEEN` vs. `RANGE BETWEEN` frame specifications.
- **Running Totals and Moving Averages**: `SUM(amount) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` for a 7-day rolling average.
- **PERCENTILE_CONT vs. PERCENTILE_DISC**: Continuous (interpolated) vs. discrete (exact value) percentiles. Calculating P50, P95, P99 latencies for SLA monitoring.
- **QUALIFY Clause**: Snowflake/BigQuery's powerful filter on window function results. Replacing the nested subquery pattern `SELECT * FROM (SELECT *, ROW_NUMBER() ...) WHERE rn = 1`.

### `02_Recursive_CTEs_And_Hierarchies/`

- **The Bill of Materials Problem**: Querying a product hierarchy (Assembly → Subassembly → Component → Raw Material) of arbitrary depth using `WITH RECURSIVE`.
- **Organizational Chart Traversal**: Finding all subordinates of a manager, calculating the depth of each employee, and detecting circular references (infinite recursion).
- **Graph Traversal in SQL**: Shortest path, connected components, and cycle detection — tasks typically associated with graph databases, but achievable in SQL for moderate-sized graphs.

### `03_EXPLAIN_Plans_And_Optimizer_Mechanics/`

- **Reading PostgreSQL EXPLAIN ANALYZE**: Understanding Seq Scan, Index Scan, Index Only Scan, Bitmap Heap Scan. actual_time, actual_rows, loops. Identifying the "rows" estimation error that causes catastrophic plan choices.
- **Join Algorithm Selection**: Nested Loop (fast for small tables), Hash Join (fast for large unsorted tables), Merge Join (fast for large pre-sorted tables). Why the optimizer sometimes chooses wrong and how to diagnose it.
- **Statistics and Histograms**: `ANALYZE` command collects column statistics (most-common-values, distinct count, null fraction, histograms). When stale statistics cause the optimizer to estimate 100 rows but the actual result is 10 million.
- **Index Advisor Tools**: pg_stat_user_indexes (unused indexes), pg_stat_statements (slow queries), HypoPG (hypothetical indexes without creating them).

### `04_SQL_Anti_Patterns_And_Performance_Killers/`

- **Implicit Type Conversions**: `WHERE varchar_column = 12345` silently casts every row, destroying index usage. One of the most common and invisible performance killers.
- **Correlated Subqueries**: A subquery that runs once per row of the outer query. Rewriting as a JOIN or window function can improve performance 1000x.
- **SELECT * in Production**: Retrieving 100 columns when you need 5. In columnar databases (Snowflake, Parquet), this can cost 20x more in I/O and money.
- **OR Conditions on Indexed Columns**: `WHERE status = 'A' OR status = 'B'` may not use the index. Rewriting as `WHERE status IN ('A', 'B')` or using `UNION ALL`.

### `05_SQL_Dialect_Differences/`

- **PostgreSQL vs. Snowflake vs. BigQuery vs. Spark SQL vs. Redshift**: Differences in `QUALIFY`, `MERGE` syntax, `LATERAL` joins, `ARRAY`/`STRUCT` handling, `TIMESTAMP` timezone behavior, `NULL` handling in `GROUP BY`, and string function names.
- **Writing Portable SQL**: Techniques for writing SQL that works across engines. When to give up portability and embrace engine-specific optimizations (e.g., BigQuery's `UNNEST`, Snowflake's `FLATTEN`).

---
*Part of [Principal Data Architect Learning Path](../README.md)*
