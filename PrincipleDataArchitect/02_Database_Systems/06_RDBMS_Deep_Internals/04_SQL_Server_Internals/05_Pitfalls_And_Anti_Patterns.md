# SQL Server Internals — Pitfalls and Anti-Patterns

## Anti-Pattern 01: Not Enabling RCSI

### Why It's Tempting
Default SQL Server behavior "just works." No changes needed. Developers might not even know RCSI exists.

### Why It's Dangerous

Default `READ COMMITTED` uses shared locks for reads. This means:
- **Readers block writers** (shared lock prevents exclusive lock acquisition)
- **Writers block readers** (exclusive lock prevents shared lock acquisition)
- At scale, this creates cascading blocking chains that look like deadlocks but are just contention

```
Session A: SELECT * FROM orders WHERE id = 42;  -- S lock on row
Session B: UPDATE orders SET status = 'x' WHERE id = 42;  -- Waits for S lock release
Session C: SELECT * FROM orders WHERE id = 42;  -- Waits for X lock from B
Session D: SELECT * FROM orders WHERE id = 42;  -- Waits for X lock from B
-- One writer blocks ALL subsequent readers on that row
```

### Detection

```sql
-- Blocked sessions right now
SELECT COUNT(*) AS blocked_sessions
FROM sys.dm_exec_requests
WHERE blocking_session_id <> 0;

-- Is RCSI enabled?
SELECT name, is_read_committed_snapshot_on
FROM sys.databases;

-- Historical blocking waits
SELECT wait_type, waiting_tasks_count, wait_time_ms
FROM sys.dm_os_wait_stats
WHERE wait_type IN ('LCK_M_S', 'LCK_M_IS', 'LCK_M_SCH_S')
ORDER BY wait_time_ms DESC;
-- High LCK_M_S (shared lock) waits = readers waiting for writers = RCSI candidate
```

### Fix

```sql
-- Enable RCSI (one-time change)
ALTER DATABASE MyDB SET READ_COMMITTED_SNAPSHOT ON;
-- Note: This requires exclusive access in SQL Server 2012 and earlier
-- SQL Server 2014+ can do it with minimal blocking

-- Monitor tempdb version store after enabling
SELECT 
    SUM(version_store_reserved_page_count) * 8 / 1024 AS version_store_mb
FROM sys.dm_db_file_space_usage;
```

**Trade-off**: Increased tempdb I/O for version store. But for 95% of OLTP workloads, this is the right trade-off.

---

## Anti-Pattern 02: Ignoring Parameter Sniffing

### Why It's Dangerous

SQL Server caches the first execution plan for a stored procedure/parameterized query. If the data distribution is skewed:

| First Execution | Cached Plan | Effect on Subsequent Calls |
|---|---|---|
| Small result set (10 rows) | Nested Loops + Index Seek | Large result sets (1M rows) use same plan → 1M index seeks |
| Large result set (1M rows) | Hash Join + Table Scan | Small result sets (10 rows) use same plan → unnecessary full scan |

### Detection

```sql
-- Queries with high variance in execution time (Query Store)
SELECT 
    q.query_id,
    LEFT(qt.query_sql_text, 100) AS query_text,
    rs.avg_duration / 1000 AS avg_ms,
    rs.min_duration / 1000 AS min_ms,
    rs.max_duration / 1000 AS max_ms,
    CASE WHEN rs.min_duration > 0 
         THEN rs.max_duration / rs.min_duration 
         ELSE 0 END AS variance_ratio
FROM sys.query_store_runtime_stats rs
JOIN sys.query_store_plan p ON rs.plan_id = p.plan_id
JOIN sys.query_store_query q ON p.query_id = q.query_id
JOIN sys.query_store_query_text qt ON q.query_text_id = qt.query_text_id
WHERE rs.count_executions > 10
  AND CASE WHEN rs.min_duration > 0 
           THEN rs.max_duration / rs.min_duration 
           ELSE 0 END > 100 -- max is 100x min
ORDER BY variance_ratio DESC;
```

### Fix Options

```sql
-- Option 1: OPTIMIZE FOR UNKNOWN (uses average statistics)
SELECT * FROM orders WHERE customer_id = @cust_id
OPTION (OPTIMIZE FOR (@cust_id UNKNOWN));

-- Option 2: RECOMPILE (fresh plan every execution — CPU cost)
SELECT * FROM orders WHERE customer_id = @cust_id
OPTION (RECOMPILE);

-- Option 3: Query Store forced plan
EXEC sp_query_store_force_plan @query_id = 42, @plan_id = 7;

-- Option 4: Automatic tuning (2017+)
ALTER DATABASE MyDB SET AUTOMATIC_TUNING (FORCE_LAST_GOOD_PLAN = ON);
```

---

## Anti-Pattern 03: tempdb Misconfiguration

### Why It's Dangerous

tempdb is a **global shared resource** in SQL Server. Everything uses it:
- Temp tables (`#temp`, `##temp`)
- Table variables (`@tablevar`)
- Sort spills (when memory grant is insufficient)
- Hash join spills
- RCSI version store
- Online index rebuilds
- MARS (Multiple Active Result Sets)

With one tempdb file, all concurrent operations contend on PFS, GAM, and SGAM allocation pages.

### Detection

```sql
-- tempdb contention waits
SELECT 
    wait_type, 
    waiting_tasks_count,
    wait_time_ms / 1000 AS wait_seconds
FROM sys.dm_os_wait_stats
WHERE wait_type LIKE 'PAGELATCH%'
  AND wait_time_ms > 0
ORDER BY wait_time_ms DESC;

-- Identify PAGELATCH waits specifically on tempdb allocation pages
SELECT 
    session_id, 
    wait_type, 
    wait_resource, -- Format: database_id:file_id:page_id
    wait_time
FROM sys.dm_exec_requests
WHERE wait_type LIKE 'PAGELATCH%'
  AND wait_resource LIKE '2:%'; -- Database_id 2 = tempdb
```

### Fix

```sql
-- Multiple equal-sized tempdb data files
-- Rule: MIN(8, number_of_CPU_cores)
-- All files MUST be the same size for proportional fill

-- Check current tempdb files
SELECT name, size * 8 / 1024 AS size_mb, growth
FROM sys.master_files WHERE database_id = 2;

-- Example: 8-core server → 8 tempdb files, each 4GB
ALTER DATABASE tempdb MODIFY FILE (NAME = tempdev, SIZE = 4GB, FILEGROWTH = 512MB);
ALTER DATABASE tempdb ADD FILE (NAME = tempdev2, FILENAME = 'T:\tempdb\tempdev2.ndf', 
                                SIZE = 4GB, FILEGROWTH = 512MB);
-- ... repeat for files 3-8
```

---

## Anti-Pattern 04: Heap Tables in OLTP Workloads

### Why It's Dangerous

A heap (table without a clustered index) has no logical ordering. Consequences:
- **Forwarding pointers**: When an UPDATE makes a row larger than the original slot, SQL Server creates a forwarding pointer. Reads must follow the pointer → 2x I/O.
- **No efficient range scans**: Every query is a full table scan or non-clustered index + RID lookup (slower than key lookup on clustered tables).
- **Space reclamation**: Deleted row space is not efficiently reused like in B-tree pages.

### Detection

```sql
-- Find heap tables
SELECT 
    SCHEMA_NAME(o.schema_id) + '.' + o.name AS table_name,
    p.rows,
    SUM(a.total_pages) * 8 / 1024 AS total_mb
FROM sys.indexes i
JOIN sys.objects o ON i.object_id = o.object_id
JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
JOIN sys.allocation_units a ON p.partition_id = a.container_id
WHERE i.type = 0 -- Heap
  AND o.is_ms_shipped = 0
GROUP BY o.schema_id, o.name, p.rows
ORDER BY p.rows DESC;

-- Forwarding pointer count (page scan needed)
SELECT 
    OBJECT_NAME(object_id) AS table_name,
    forwarded_fetch_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, 0, NULL, 'DETAILED')
WHERE index_id = 0 AND forwarded_fetch_count > 0;
```

### Fix
Create a clustered index on every table:
```sql
-- Add a clustered index (choose a narrow, always-increasing key)
CREATE CLUSTERED INDEX CX_Orders ON dbo.Orders (OrderID);
-- If OrderID is the PK, it's already clustered by default
```

---

## Anti-Pattern 05: Index Over-Creation

### Why It's Dangerous

Each non-clustered index:
- Must be updated on every INSERT (new entry in every index B-tree)
- Must be updated on UPDATE if the indexed column changed
- Consumed by DELETE operations
- Uses buffer pool memory for index pages
- Increases backup size and duration

A table with 15 non-clustered indexes means every INSERT triggers 16 B-tree modifications (1 clustered + 15 non-clustered).

### Detection

```sql
-- Unused indexes (high maintenance cost, zero reads)
SELECT 
    OBJECT_NAME(i.object_id) AS table_name,
    i.name AS index_name,
    s.user_seeks + s.user_scans + s.user_lookups AS total_reads,
    s.user_updates AS total_writes,
    CASE WHEN (s.user_seeks + s.user_scans + s.user_lookups) = 0 
         THEN 'UNUSED — DROP CANDIDATE'
         ELSE CAST(s.user_updates * 1.0 / 
              NULLIF(s.user_seeks + s.user_scans + s.user_lookups, 0) AS VARCHAR(20))
    END AS write_to_read_ratio
FROM sys.indexes i
LEFT JOIN sys.dm_db_index_usage_stats s 
    ON i.object_id = s.object_id AND i.index_id = s.index_id AND s.database_id = DB_ID()
WHERE i.type > 0 -- Non-heap
  AND OBJECTPROPERTY(i.object_id, 'IsUserTable') = 1
ORDER BY total_reads ASC, total_writes DESC;

-- Index size impact
SELECT 
    OBJECT_NAME(i.object_id) AS table_name,
    i.name AS index_name,
    SUM(a.total_pages) * 8 / 1024 AS index_mb
FROM sys.indexes i
JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
JOIN sys.allocation_units a ON p.partition_id = a.container_id
WHERE i.type > 1 -- Non-clustered only
GROUP BY i.object_id, i.name
ORDER BY index_mb DESC;
```

### Fix
- Drop indexes with 0 reads and high writes
- Consolidate overlapping indexes (e.g., idx on (A) and idx on (A, B) — the second covers the first)
- Use `INCLUDE` columns instead of creating wider indexes

---

## Anti-Pattern 06: Ignoring Wait Statistics

### Why It's Dangerous

Many DBAs tune based on "gut feeling" or focus on CPU/memory without understanding what SQL Server is actually waiting for. Wait stats tell you exactly where time is spent:

| Wait Type | Root Cause | Action |
|---|---|---|
| `CXPACKET` / `CXCONSUMER` | Parallel query waits | Tune MAXDOP, cost threshold for parallelism |
| `PAGEIOLATCH_*` | Reading pages from disk (buffer miss) | More memory; better I/O; check for missing indexes |
| `WRITELOG` | Transaction log flush latency | Faster log storage; batch commits |
| `LCK_M_*` | Lock contention | Enable RCSI; reduce transaction scope |
| `PAGELATCH_*` | In-memory page latch contention | tempdb file configuration (if tempdb) |
| `SOS_SCHEDULER_YIELD` | CPU pressure | Add CPU; reduce plan complexity |

### Detection

```sql
-- Top waits (excluding benign waits)
WITH Waits AS (
    SELECT 
        wait_type,
        wait_time_ms / 1000.0 AS wait_sec,
        100.0 * wait_time_ms / NULLIF(SUM(wait_time_ms) OVER(), 0) AS pct,
        ROW_NUMBER() OVER(ORDER BY wait_time_ms DESC) AS rn
    FROM sys.dm_os_wait_stats
    WHERE wait_type NOT IN (
        'BROKER_TASK_STOP','BROKER_EVENTHANDLER','BROKER_RECEIVE_WAITFOR',
        'BROKER_TRANSMITTER','CLR_AUTO_EVENT','CLR_MANUAL_EVENT',
        'CLR_SEMAPHORE','DBMIRROR_DBM_EVENT','DBMIRROR_EVENTS_QUEUE',
        'DBMIRROR_WORKER_QUEUE','DBMIRRORING_CMD','DIRTY_PAGE_POLL',
        'DISPATCHER_QUEUE_SEMAPHORE','FT_IFTS_SCHEDULER_IDLE_WAIT',
        'FT_IFTSHC_MUTEX','HADR_FILESTREAM_IOMGR_IOCOMPLETION',
        'HADR_WORK_QUEUE','LAZYWRITER_SLEEP','LOGMGR_QUEUE',
        'ONDEMAND_TASK_QUEUE','REQUEST_FOR_DEADLOCK_SEARCH',
        'SLEEP_BPOOL_FLUSH','SLEEP_TASK','SQLTRACE_BUFFER_FLUSH',
        'WAITFOR','XE_DISPATCHER_WAIT','XE_TIMER_EVENT'
        -- Add more benign waits as needed
    )
)
SELECT wait_type, wait_sec, pct,
    SUM(pct) OVER(ORDER BY wait_sec DESC) AS running_pct
FROM Waits
WHERE rn <= 20;
```

---

## Anti-Pattern Summary Table

| # | Anti-Pattern | Root Cause | Detection Signal | Fix |
|---|---|---|---|---|
| 01 | No RCSI | Lock-based reads | LCK_M_S waits; blocked session count | `SET READ_COMMITTED_SNAPSHOT ON` |
| 02 | Parameter sniffing | Cached plan for wrong distribution | Query Store variance > 100x | OPTIMIZE FOR UNKNOWN; auto-tuning |
| 03 | tempdb misconfigured | Single file; PFS contention | PAGELATCH waits on database_id 2 | Multiple equal-sized files |
| 04 | Heap tables | No clustered index | Forwarding pointers; RID lookups | Create clustered index on every table |
| 05 | Index over-creation | Too many NC indexes | Unused indexes with high write cost | Drop unused; consolidate overlapping |
| 06 | Ignoring wait stats | No systematic diagnostic | Blind tuning without data | Paul Randal's wait stats analysis |
