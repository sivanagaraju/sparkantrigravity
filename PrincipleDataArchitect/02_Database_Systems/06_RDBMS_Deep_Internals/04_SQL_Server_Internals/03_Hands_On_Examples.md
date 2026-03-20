# SQL Server Internals — Hands-On Examples

## Lab 1: Page and Extent Inspection

### View Page Contents with DBCC PAGE

```sql
-- Create a test table
CREATE TABLE dbo.PageDemo (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(50),
    Amount DECIMAL(10,2)
);

INSERT INTO dbo.PageDemo (Name, Amount)
SELECT TOP 1000
    'Customer_' + CAST(ROW_NUMBER() OVER (ORDER BY a.object_id) AS VARCHAR(10)),
    CAST(RAND(CHECKSUM(NEWID())) * 10000 AS DECIMAL(10,2))
FROM sys.all_objects a CROSS JOIN sys.all_objects b;

-- Find pages allocated to the table
-- sys.dm_db_database_page_allocations (SQL Server 2012+)
SELECT 
    allocated_page_page_id,
    page_type_desc,
    allocation_unit_type_desc,
    is_iam_page,
    is_allocated
FROM sys.dm_db_database_page_allocations(
    DB_ID(), OBJECT_ID('dbo.PageDemo'), NULL, NULL, 'DETAILED')
WHERE is_allocated = 1
ORDER BY allocated_page_page_id;

-- View a specific data page (trace flag 3604 sends output to client)
DBCC TRACEON(3604);
DBCC PAGE(N'YourDatabase', 1, <page_id>, 3); -- Format 3 = full page dump
DBCC TRACEOFF(3604);
```

**What to look for:**
- `m_slotCnt`: number of rows on the page
- `m_freeData` and `m_freeCnt`: where free space starts and how much exists
- `m_lsn`: the LSN of the last modification
- Row offset array at the bottom: 2 bytes per slot, points to each row's start

### View Extent Allocation

```sql
-- Show extent allocation for a table
DBCC EXTENTINFO('YourDatabase', 'dbo.PageDemo', -1);

-- Check if using mixed or uniform extents
SELECT 
    page_type_desc,
    extent_page_id,
    COUNT(*) AS pages_in_extent
FROM sys.dm_db_database_page_allocations(
    DB_ID(), OBJECT_ID('dbo.PageDemo'), NULL, NULL, 'DETAILED')
WHERE is_allocated = 1
GROUP BY page_type_desc, extent_page_id;
```

---

## Lab 2: Buffer Pool Analysis

### Buffer Pool Contents

```sql
-- What's in the buffer pool right now?
SELECT 
    DB_NAME(database_id) AS db_name,
    COUNT(*) AS pages_in_memory,
    COUNT(*) * 8 / 1024 AS mb_in_memory,
    SUM(CASE WHEN is_modified = 1 THEN 1 ELSE 0 END) AS dirty_pages
FROM sys.dm_os_buffer_descriptors
GROUP BY database_id
ORDER BY pages_in_memory DESC;

-- Buffer pool usage by object
SELECT 
    OBJECT_NAME(p.object_id) AS table_name,
    COUNT(*) AS pages_cached,
    COUNT(*) * 8 / 1024 AS mb_cached,
    SUM(CASE WHEN bd.is_modified = 1 THEN 1 ELSE 0 END) AS dirty_pages
FROM sys.dm_os_buffer_descriptors bd
JOIN sys.allocation_units au ON bd.allocation_unit_id = au.allocation_unit_id
JOIN sys.partitions p ON au.container_id = p.hobt_id
WHERE bd.database_id = DB_ID()
GROUP BY p.object_id
ORDER BY pages_cached DESC;

-- Page Life Expectancy trend
-- Run multiple times to see if PLE is dropping
SELECT 
    cntr_value AS page_life_expectancy_seconds,
    GETDATE() AS sample_time
FROM sys.dm_os_performance_counters
WHERE counter_name = 'Page life expectancy'
  AND object_name LIKE '%Buffer Manager%';
```

**Interpretation:**
- PLE < 300 seconds → buffer pool is under memory pressure
- High dirty page count → checkpoint may be slow
- Table with disproportionate buffer pool usage → possible scan operation or missing index

---

## Lab 3: Transaction Log Analysis

### VLF Count and Status

```sql
-- VLF count (target: < 200 for performance; < 1000 to avoid slow recovery)
DBCC LOGINFO;
-- Each row = one VLF. Status: 0 = inactive (available for reuse), 2 = active

-- Better method (SQL Server 2016+):
SELECT 
    name,
    COUNT(l.database_id) AS vlf_count
FROM sys.databases d
CROSS APPLY sys.dm_db_log_info(d.database_id) l
GROUP BY name
ORDER BY vlf_count DESC;

-- Log space usage
DBCC SQLPERF(LOGSPACE);

-- What's preventing log truncation?
SELECT 
    name,
    log_reuse_wait_desc
FROM sys.databases;
-- Common blockers: ACTIVE_TRANSACTION, LOG_BACKUP, REPLICATION, 
-- ACTIVE_BACKUP_OR_RESTORE, DATABASE_MIRRORING
```

### Watch Log Flushes in Real-Time

```sql
-- WRITELOG waits (the commit latency)
SELECT
    wait_type,
    waiting_tasks_count,
    wait_time_ms,
    CAST(wait_time_ms * 1.0 / NULLIF(waiting_tasks_count, 0) AS DECIMAL(10,2)) 
        AS avg_wait_ms
FROM sys.dm_os_wait_stats
WHERE wait_type = 'WRITELOG';
-- avg_wait_ms > 5 → slow log storage
-- avg_wait_ms > 20 → serious I/O bottleneck on log drive
```

---

## Lab 4: RCSI and Version Store

### Enable RCSI and Observe Behavior

```sql
-- Enable RCSI (requires exclusive database access in older versions)
ALTER DATABASE TestDB SET READ_COMMITTED_SNAPSHOT ON;

-- Check if RCSI is enabled
SELECT name, is_read_committed_snapshot_on
FROM sys.databases WHERE name = 'TestDB';
```

### Demonstrate Non-Blocking Reads

```sql
-- Session 1: Start an update but don't commit
BEGIN TRAN;
UPDATE dbo.Orders SET Status = 'Processing' WHERE OrderID = 1;
-- DON'T COMMIT YET

-- Session 2: Read the same row (with RCSI enabled)
SELECT * FROM dbo.Orders WHERE OrderID = 1;
-- Returns the OLD value from version store
-- NO BLOCKING! (without RCSI, this would wait)

-- Session 1: Commit
COMMIT;

-- Session 2: Read again
SELECT * FROM dbo.Orders WHERE OrderID = 1;
-- Now returns the NEW value
```

### Monitor Version Store

```sql
-- tempdb version store usage
SELECT 
    SUM(version_store_reserved_page_count) * 8 / 1024 AS version_store_mb
FROM sys.dm_db_file_space_usage;

-- Persistent Version Store (ADR) — SQL Server 2019+
SELECT 
    pvs_page_count * 8 / 1024 AS pvs_mb,
    current_aborted_transaction_count
FROM sys.dm_db_file_space_usage;

-- Who's generating versions?
SELECT 
    session_id,
    transaction_id,
    elapsed_time_seconds
FROM sys.dm_tran_version_store_space_usage
WHERE database_id = DB_ID();
```

---

## Lab 5: Columnstore Index Performance

### Create and Query a Columnstore Index

```sql
-- Create a fact table with 5M rows
CREATE TABLE dbo.FactSales (
    SaleID INT IDENTITY(1,1),
    SaleDate DATE,
    ProductID INT,
    StoreID INT,
    Quantity INT,
    UnitPrice DECIMAL(10,2),
    Discount DECIMAL(5,2)
);

-- Insert ~5M rows (adjust for your environment)
INSERT INTO dbo.FactSales (SaleDate, ProductID, StoreID, Quantity, UnitPrice, Discount)
SELECT TOP 5000000
    DATEADD(DAY, ABS(CHECKSUM(NEWID())) % 1095, '2022-01-01'),
    ABS(CHECKSUM(NEWID())) % 1000 + 1,
    ABS(CHECKSUM(NEWID())) % 100 + 1,
    ABS(CHECKSUM(NEWID())) % 50 + 1,
    CAST(RAND(CHECKSUM(NEWID())) * 500 AS DECIMAL(10,2)),
    CAST(RAND(CHECKSUM(NEWID())) * 30 AS DECIMAL(5,2))
FROM sys.all_objects a CROSS JOIN sys.all_objects b;

-- Analytical query on rowstore (baseline)
SET STATISTICS IO ON;
SET STATISTICS TIME ON;

SELECT 
    YEAR(SaleDate) AS SaleYear,
    MONTH(SaleDate) AS SaleMonth,
    SUM(Quantity * UnitPrice) AS Revenue,
    AVG(Discount) AS AvgDiscount
FROM dbo.FactSales
GROUP BY YEAR(SaleDate), MONTH(SaleDate)
ORDER BY SaleYear, SaleMonth;

-- Create clustered columnstore index  
CREATE CLUSTERED COLUMNSTORE INDEX CCI_FactSales ON dbo.FactSales;

-- Re-run the same query → compare IO and time
SELECT 
    YEAR(SaleDate) AS SaleYear,
    MONTH(SaleDate) AS SaleMonth,
    SUM(Quantity * UnitPrice) AS Revenue,
    AVG(Discount) AS AvgDiscount
FROM dbo.FactSales
GROUP BY YEAR(SaleDate), MONTH(SaleDate)
ORDER BY SaleYear, SaleMonth;
```

### Check Rowgroup Quality

```sql
-- Columnstore rowgroup health
SELECT 
    object_name(object_id) AS table_name,
    row_group_id,
    state_desc,
    total_rows,
    deleted_rows,
    size_in_bytes / 1024 AS size_kb,
    trim_reason_desc
FROM sys.dm_db_column_store_row_group_physical_stats
WHERE object_id = OBJECT_ID('dbo.FactSales')
ORDER BY row_group_id;
-- Ideal: all rowgroups COMPRESSED with ~1M rows, 0 deleted rows
-- Trim reasons like DICTIONARY_SIZE or MEMORY_LIMITATION indicate suboptimal compression
```

---

## Lab 6: Query Store Analysis

### Enable and Explore Query Store

```sql
-- Enable Query Store
ALTER DATABASE TestDB SET QUERY_STORE = ON (
    OPERATION_MODE = READ_WRITE,
    DATA_FLUSH_INTERVAL_SECONDS = 900,
    INTERVAL_LENGTH_MINUTES = 60,
    MAX_STORAGE_SIZE_MB = 1024,
    QUERY_CAPTURE_MODE = AUTO,
    WAIT_STATS_CAPTURE_MODE = ON -- 2017+
);

-- Run some queries to populate Query Store
-- (run the analytical query from Lab 5 a few times)

-- Top resource-consuming queries
SELECT TOP 10
    q.query_id,
    qt.query_sql_text,
    rs.avg_duration / 1000 AS avg_duration_ms,
    rs.avg_cpu_time / 1000 AS avg_cpu_ms,
    rs.avg_logical_io_reads,
    rs.count_executions,
    p.plan_id,
    p.query_plan
FROM sys.query_store_query q
JOIN sys.query_store_query_text qt ON q.query_text_id = qt.query_text_id
JOIN sys.query_store_plan p ON q.query_id = p.query_id
JOIN sys.query_store_runtime_stats rs ON p.plan_id = rs.plan_id
ORDER BY rs.avg_duration DESC;

-- Queries with multiple plans (plan regression candidates)
SELECT 
    q.query_id,
    qt.query_sql_text,
    COUNT(DISTINCT p.plan_id) AS plan_count
FROM sys.query_store_query q
JOIN sys.query_store_query_text qt ON q.query_text_id = qt.query_text_id
JOIN sys.query_store_plan p ON q.query_id = p.query_id
GROUP BY q.query_id, qt.query_sql_text
HAVING COUNT(DISTINCT p.plan_id) > 1
ORDER BY plan_count DESC;
```

---

## Lab 7: Locking and Blocking Diagnostics

### Observe Lock Escalation

```sql
-- Show current locks held
SELECT 
    resource_type,
    resource_description,
    request_mode,
    request_status,
    request_session_id
FROM sys.dm_tran_locks
WHERE resource_database_id = DB_ID()
ORDER BY request_session_id;

-- Blocked sessions and blocking chains
SELECT 
    blocked.session_id AS blocked_session,
    blocked.blocking_session_id AS blocker,
    blocked.wait_type,
    blocked.wait_time / 1000 AS wait_seconds,
    blocker_text.text AS blocking_query,
    blocked_text.text AS blocked_query
FROM sys.dm_exec_requests blocked
JOIN sys.dm_exec_requests blocker_req ON blocked.blocking_session_id = blocker_req.session_id
CROSS APPLY sys.dm_exec_sql_text(blocker_req.sql_handle) blocker_text
CROSS APPLY sys.dm_exec_sql_text(blocked.sql_handle) blocked_text
WHERE blocked.blocking_session_id <> 0;

-- Deadlock detection: enable trace flag or use Extended Events
-- Extended Events (preferred in 2012+):
CREATE EVENT SESSION [DeadlockCapture] ON SERVER
ADD EVENT sqlserver.xml_deadlock_report
ADD TARGET package0.event_file(SET filename=N'DeadlockCapture')
WITH (MAX_MEMORY=4096 KB, STARTUP_STATE=ON);
ALTER EVENT SESSION [DeadlockCapture] ON SERVER STATE = START;
```
