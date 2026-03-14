# SQL Server Internals — Concept Overview

> Pages, extents, filegroups, and the query optimizer that powers enterprise Windows workloads.

## Key Differences

| Feature | SQL Server | PostgreSQL |
|---|---|---|
| **Page Size** | 8KB (fixed) | 8KB (compile-time, fixed) |
| **Index Types** | Clustered + Non-clustered | B-Tree, Hash, GiST, GIN, BRIN |
| **Concurrency** | Locking + Row Versioning (RCSI) | MVCC (always versioned) |
| **Columnstore** | ✅ Built-in | ❌ (use Citus or columnar extensions) |
| **In-Memory OLTP** | ✅ Hekaton engine | ❌ |
| **Query Store** | ✅ Built-in plan history | pg_stat_statements (extension) |

## Columnstore Indexes — SQL Server's OLAP Secret

```sql
-- Convert a row-store table to columnar (SQL Server)
CREATE CLUSTERED COLUMNSTORE INDEX CCI_FactSales ON fact_sales;
-- Compression: 10x. Analytical query speed: 10-100x faster.
-- Works alongside row-store for mixed OLTP/OLAP.
```

## References

| Resource | Link |
|---|---|
| [SQL Server Architecture](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-architecture-guide) | Microsoft Docs |
| *SQL Server Internals* | Kalen Delaney |
