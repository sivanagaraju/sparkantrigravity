# SQL Server Internals — Interview Angle

## How This Appears

SQL Server internals questions appear in **backend engineering** and **data platform** interviews at companies using the Microsoft stack (financial services, healthcare, e-commerce, enterprise SaaS). The concurrency model (lock-based vs RCSI), Query Store, columnstore indexes, and tempdb are the most common deep-dive areas. Unlike PostgreSQL/Oracle interviews, SQL Server interviews frequently probe **wait statistics** as a diagnostic framework.

---

## Sample Questions

### Q1: "Explain the difference between READ COMMITTED with and without RCSI. When would you enable RCSI?"

**Weak answer:** "RCSI uses row versioning. It's better than locking."

**Strong answer (Principal):**

"Without RCSI, SQL Server's `READ COMMITTED` isolation uses **shared (S) locks** for reads. A SELECT acquires an S lock on each row it reads, and S locks are incompatible with exclusive (X) locks held by writers. This means readers block writers and writers block readers — which creates cascading blocking chains at scale.

With RCSI enabled (`ALTER DATABASE MyDB SET READ_COMMITTED_SNAPSHOT ON`), reads no longer acquire shared locks. Instead, the storage engine copies the pre-modification version of each row to the **version store in tempdb** before applying the modification. Readers access these versioned rows, getting a **statement-level consistent** snapshot of data as of the statement's start time.

**Key trade-offs:**

| Aspect | Without RCSI | With RCSI |
|---|---|---|
| Reader-writer blocking | Yes | No |
| tempdb usage | Minimal | Version store I/O |
| Read consistency | Current committed data only | Statement-level snapshot |
| Write-write blocking | Yes | Still yes (X locks still used) |
| Application changes | None | None (transparent) |

**When to enable:** Almost always for OLTP workloads. The only cases to be careful:
1. Applications that depend on locking behavior for correctness (rare, usually a design bug)
2. Very high-write workloads where tempdb is already a bottleneck (fix tempdb first)
3. Applications using `SELECT...READ COMMITTED` as a poor man's pessimistic lock (should use UPDLOCK instead)"

### Q2: "Your SQL Server has erratic stored procedure performance — sometimes 2 seconds, sometimes 45 minutes. What's your diagnostic approach?"

**Strong answer (Principal):**

"This is almost certainly **parameter sniffing**. SQL Server compiles a stored procedure once and caches the execution plan based on the first parameter values (the 'sniffed' parameters). If data distribution is highly skewed, the cached plan is optimal for one parameter range but catastrophic for another.

**Diagnostic steps:**

1. **Query Store**: Check if the procedure has multiple distinct plans:
```sql
SELECT q.query_id, p.plan_id,
       rs.avg_duration / 1000 AS avg_ms,
       rs.max_duration / 1000 AS max_ms,
       rs.count_executions
FROM sys.query_store_plan p
JOIN sys.query_store_query q ON p.query_id = q.query_id
JOIN sys.query_store_runtime_stats rs ON p.plan_id = rs.plan_id
WHERE q.object_id = OBJECT_ID('dbo.MyProcedure');
```

2. If one plan shows 2-second average and another shows 45-minute average → confirmed parameter sniffing.

3. **Fix options (in order of preference):**
   - `OPTIMIZE FOR UNKNOWN`: uses average selectivity, no compilation overhead
   - Query Store forced plan: lock the known-good plan for that query
   - `OPTION (RECOMPILE)`: fresh plan every call (CPU cost per execution)
   - `FORCE_LAST_GOOD_PLAN = ON`: SQL Server automatically detects regression and reverts

The nuclear option is to restructure the procedure with dynamic SQL that naturally creates separate cache entries per parameter range, but this is rarely needed with Query Store."

### Q3: "You're designing a system that needs real-time analytics on OLTP data. How would you architect this on SQL Server?"

**Strong answer (Principal):**

"SQL Server is uniquely suited for HTAP (Hybrid Transactional/Analytical Processing) because it offers **non-clustered columnstore indexes on rowstore tables** since SQL Server 2016.

**Architecture:**

1. **OLTP layer**: Clustered rowstore index on the transactional table (orders, transactions). All INSERT/UPDATE/DELETE operations use the rowstore B-tree with row-mode execution.

2. **Analytics layer**: Non-clustered columnstore index on the same table covering the analytical columns:
```sql
CREATE NONCLUSTERED COLUMNSTORE INDEX NCCI_Orders_Analytics
ON dbo.Orders (OrderDate, ProductID, CustomerID, Amount, Quantity);
```

3. **Query routing**: Analytical queries automatically use batch mode execution against the columnstore segments (the optimizer chooses this when the columnstore covers the query columns). OLTP point lookups use the clustered rowstore index.

4. **Concurrency**: Enable RCSI so analytical scans never block OLTP writes.

**The delta store handles recent changes**: New inserts first land in a B-tree delta store. When ~1M rows accumulate, the tuple mover compresses them into a new columnstore rowgroup. This means analytics see data within seconds of insertion — no ETL needed.

**Comparison:**
- PostgreSQL: No built-in columnar. Need Citus or third-party columnar extensions.
- Oracle: In-Memory Column Store exists but requires Enterprise Edition + additional license.
- MySQL: No columnstore capability at all.
- SQL Server: Built into Standard Edition since 2016. The best HTAP story in the RDBMS world."

### Q4: "What are wait statistics, and how do you use them to diagnose SQL Server performance problems?"

**Strong answer (Principal):**

"Wait statistics are SQL Server's built-in performance instrumentation. Every time a thread cannot make progress, it records the reason as a wait type. There are ~1000 wait types, but in practice 10-15 cover 95% of real-world performance issues.

**The diagnostic framework:**

1. Query `sys.dm_os_wait_stats` to see cumulative waits since server start
2. Take two snapshots and diff them to see waits during a specific time window
3. Filter out benign waits (like `BROKER_TASK_STOP`, `LAZYWRITER_SLEEP`)
4. The top remaining wait type tells you the bottleneck category

**The top 5 actionable wait types:**

| Wait Type | Meaning | Fix |
|---|---|---|
| `PAGEIOLATCH_SH/EX` | Reading data from disk (buffer miss) | More RAM, faster I/O, missing indexes |
| `WRITELOG` | Commit (log flush) latency | Faster log drive, batch commits |
| `LCK_M_S`, `LCK_M_X` | Lock contention | Enable RCSI, shorter transactions |
| `CXPACKET/CXCONSUMER` | Parallel query thread imbalance | Tune MAXDOP, cost threshold |
| `PAGELATCH_EX` on tempdb | Allocation page contention | Multiple tempdb files |

This is the single most powerful diagnostic approach in SQL Server. Paul Randal's wait stats methodology is the gold standard: start with waits, not with CPU or memory."

---

## Follow-Up Questions

| After Question | They'll Ask | What They Want |
|---|---|---|
| RCSI vs locking | "What about Snapshot Isolation vs RCSI?" | SI = transaction-level consistency + update conflict detection; RCSI = statement-level, no conflict detection |
| Parameter sniffing | "What if OPTIMIZE FOR UNKNOWN also produces a bad plan?" | Use plan guides, Query Store forced plan, or dynamic SQL with `sp_executesql` per parameter range |
| HTAP architecture | "What about the delta store lag?" | Tuple mover runs every ~5 minutes; REORGANIZE forces immediate compression; lag is seconds not minutes for reads |
| Wait stats | "How do you handle CXPACKET?" | Usually not a problem itself; check if parallel plans are scan-heavy due to missing indexes; tune `cost threshold for parallelism` (default 5 is too low for most workloads, set to 50) |

---

## Whiteboard Exercise

**Draw: The write path for an UPDATE in SQL Server with RCSI enabled.**

```
1. Application issues: UPDATE orders SET status='shipped' WHERE id=42

2. Storage Engine:
   ┌──────────────────────────────────────────────┐
   │ a) Read page containing row id=42 into       │
   │    Buffer Pool (if not already cached)        │
   │                                               │
   │ b) Copy old row version to tempdb             │
   │    version store (for RCSI readers)           │
   │                                               │
   │ c) Acquire X lock on row                      │
   │                                               │
   │ d) Generate log record in Log Buffer:         │
   │    [LSN | TxID | Page | Offset |              │
   │     Old_Status='pending' |                    │
   │     New_Status='shipped']                     │
   │                                               │
   │ e) Modify row in-place in Buffer Pool page    │
   │    (page is now dirty; m_lsn updated)         │
   └──────────────────────────────────────────────┘

3. On COMMIT:
   ┌──────────────────────────────────────────────┐
   │ f) Log Buffer → flush to .ldf file (fsync)   │
   │    WRITELOG wait if slow                      │
   │                                               │
   │ g) Release X lock                             │
   │                                               │
   │ h) Dirty page stays in Buffer Pool            │
   │    → written to .mdf by Checkpoint/Lazy Writer│
   │    (NOT in commit path)                       │
   └──────────────────────────────────────────────┘

4. Concurrent Reader (RCSI):
   ┌──────────────────────────────────────────────┐
   │ SELECT * FROM orders WHERE id = 42            │
   │ → Sees row in Buffer Pool has version chain   │
   │ → Follows pointer to tempdb version store     │
   │ → Returns pre-UPDATE value                    │
   │ → No S lock acquired; never blocked           │
   └──────────────────────────────────────────────┘
```
