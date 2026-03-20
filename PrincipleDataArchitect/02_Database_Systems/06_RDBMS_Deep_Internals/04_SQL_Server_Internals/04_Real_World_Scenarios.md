# SQL Server Internals — Real-World Scenarios

## Case Study 01: Stack Overflow — SQL Server at Scale (Public Dataset)

### Context
Stack Overflow runs on SQL Server and has made their database [publicly available](https://www.brentozar.com/archive/2015/10/how-to-download-the-stack-overflow-database-via-bittorrent/) for learning. The production workload serves ~1.7 billion page views/month from a relatively modest SQL Server deployment.

### Technical Challenge
- **Posts table**: 60M+ rows, 80GB+, with full-text content
- **Votes table**: 200M+ rows
- Analytical queries (top users, trending tags) run alongside OLTP reads
- Missing index requests generated ~4000 entries in `sys.dm_db_missing_index_details`

### Solution Architecture

**1. RCSI for reader-writer concurrency**
Stack Overflow enabled RCSI early. With thousands of concurrent readers and frequent writes to Posts and Votes tables, lock-based READ COMMITTED would cause catastrophic blocking.

```sql
-- Stack Overflow's approach: RCSI eliminates reader blocking
ALTER DATABASE StackOverflow SET READ_COMMITTED_SNAPSHOT ON;
-- Result: SELECT queries never wait for INSERT/UPDATE operations
```

**2. Covering indexes for hot queries**
Instead of creating every suggested index from `dm_db_missing_index_details`, targeted covering indexes for the top 10 queries:

```sql
-- Example: Posts by OwnerUserId with common SELECT columns
CREATE NONCLUSTERED INDEX IX_Posts_OwnerUserId_Incl
ON dbo.Posts (OwnerUserId)
INCLUDE (CreationDate, Score, Title, Tags);
-- Eliminates key lookups for the "user profile" query pattern
```

**3. Columnstore for analytics**
Analytical queries on the Votes table (aggregations by date, post, vote type) ran 50x faster after adding a non-clustered columnstore index:

```sql
CREATE NONCLUSTERED COLUMNSTORE INDEX NCCI_Votes_Analytics
ON dbo.Votes (PostId, VoteTypeId, CreationDate);
-- Analytical queries: batch mode execution, segment elimination
-- OLTP queries: continue using rowstore clustered index
```

### Lessons Learned
- RCSI is the single biggest quick win for reader-writer concurrency on SQL Server
- Cover the top 10 queries with indexes rather than blindly following `dm_db_missing_index_details` (which doesn't account for maintenance cost)
- Non-clustered columnstore indexes enable HTAP without separate OLAP infrastructure

---

## Case Study 02: Major E-Commerce Platform — tempdb Contention

### Context
A top-50 e-commerce site running on SQL Server 2016. During Black Friday peak (60K orders/minute), the application experienced escalating latency: P50 went from 5ms to 200ms over 2 hours.

### Root Cause Analysis

**Wait stats** showed `PAGELATCH_UP` and `PAGELATCH_EX` on tempdb as the #1 wait type.

```sql
-- Top waits during the incident
SELECT TOP 10 
    wait_type, 
    wait_time_ms / 1000 AS total_wait_sec,
    waiting_tasks_count
FROM sys.dm_os_wait_stats 
WHERE wait_type LIKE 'PAGELATCH%'
ORDER BY wait_time_ms DESC;
-- Result: PAGELATCH_UP on tempdb pages = 85% of all wait time
```

**Root cause**: PFS page contention in tempdb. Every temp table creation, table variable operation, RCSI version store write, and sort spill touches PFS pages. With one tempdb data file, all operations contended on a single PFS page.

### Fix: tempdb Configuration

```sql
-- 1. Multiple tempdb data files (1 per CPU core, up to 8)
ALTER DATABASE tempdb ADD FILE (
    NAME = 'tempdev2', FILENAME = 'T:\tempdb\tempdev2.ndf', SIZE = 8GB, FILEGROWTH = 1GB
);
-- Repeated for files 3-8

-- 2. Enable trace flag 1118 (uniform extent allocation only)
-- (default in SQL Server 2016+, required as trace flag in earlier versions)
DBCC TRACEON(1118, -1);

-- 3. Ensure all tempdb files are the SAME SIZE
-- SQL Server uses proportional fill across equal-sized files
```

**Before fix**: 60K orders/minute, P50 = 200ms
**After fix**: 60K orders/minute, P50 = 8ms

### Lessons Learned
- tempdb contention is the #1 performance killer in high-concurrency SQL Server workloads
- Rule of thumb: start with 4 or 8 tempdb data files of equal size
- SQL Server 2019+ improved with memory-optimized tempdb metadata; SQL Server 2022 adds in-memory tempdb metadata for even less contention

---

## Case Study 03: Financial Services — Parameter Sniffing Disaster

### Context
A trading platform on SQL Server 2019. A critical stored procedure for portfolio valuation ran in 2 seconds for 99% of calls but occasionally took 45+ minutes, causing trading halts.

### Root Cause

**Parameter sniffing**: SQL Server compiles a stored procedure once and caches the execution plan based on the first parameter values it sees. If the first call is for a small portfolio (10 positions), the optimizer chooses Nested Loops. When a hedge fund with 500,000 positions calls the same stored procedure, it uses the same Nested Loops plan → 500K index lookups instead of a Hash Join.

```sql
-- The problematic procedure
CREATE PROCEDURE dbo.GetPortfolioValuation @FundID INT AS
BEGIN
    SELECT p.PositionID, p.SecurityID, s.Price, p.Quantity,
           p.Quantity * s.Price AS MarketValue
    FROM Positions p
    JOIN Securities s ON p.SecurityID = s.SecurityID
    WHERE p.FundID = @FundID;
END;

-- Fund 42: 10 positions → Nested Loops (fast)
EXEC dbo.GetPortfolioValuation @FundID = 42;

-- Fund 7: 500,000 positions → Same Nested Loops plan → 45 minutes!
EXEC dbo.GetPortfolioValuation @FundID = 7;
```

### Solution

**1. Identified the problem using Query Store:**
```sql
-- Find the procedure's query_id and see multiple plans
SELECT q.query_id, p.plan_id, 
       rs.avg_duration / 1000000 AS avg_duration_sec,
       rs.min_duration / 1000000 AS min_sec,
       rs.max_duration / 1000000 AS max_sec,
       rs.count_executions
FROM sys.query_store_plan p
JOIN sys.query_store_query q ON p.query_id = q.query_id
JOIN sys.query_store_runtime_stats rs ON p.plan_id = rs.plan_id
WHERE q.object_id = OBJECT_ID('dbo.GetPortfolioValuation');
```

**2. Applied `OPTIMIZE FOR UNKNOWN` to prevent initial parameter from biasing the plan:**
```sql
ALTER PROCEDURE dbo.GetPortfolioValuation @FundID INT AS
BEGIN
    SELECT p.PositionID, p.SecurityID, s.Price, p.Quantity,
           p.Quantity * s.Price AS MarketValue
    FROM Positions p
    JOIN Securities s ON p.SecurityID = s.SecurityID
    WHERE p.FundID = @FundID
    OPTION (OPTIMIZE FOR (@FundID UNKNOWN));
END;
```

**3. Enabled automatic tuning for plan regression:**
```sql
ALTER DATABASE TradingDB 
SET AUTOMATIC_TUNING (FORCE_LAST_GOOD_PLAN = ON);
```

### Lessons Learned
- Parameter sniffing is the #1 cause of erratic SQL Server stored procedure performance
- Query Store is essential for detecting and managing plan regressions
- `OPTIMIZE FOR UNKNOWN` uses average selectivity instead of specific parameter statistics
- Automatic tuning (SQL Server 2017+) can auto-revert to the last known good plan

---

## Case Study 04: Healthcare System — VLF Fragmentation Crisis

### Context
A hospital EHR (Electronic Health Records) system on SQL Server 2017. Database had been running for 5 years without proper transaction log maintanence. After a server restart (patching), the database took **4 hours and 17 minutes** to come online.

### Root Cause

The transaction log had **42,000 VLFs** due to repeated small autogrowth events (default 10% growth from 1MB initial size → thousands of tiny VLF additions over 5 years).

```sql
-- VLF count check
SELECT COUNT(*) AS vlf_count FROM sys.dm_db_log_info(DB_ID());
-- Result: 42,147 VLFs

-- Recovery scans every VLF during the Analysis phase
-- 42,000 VLFs × ~100ms per VLF scan = ~70 minutes just for analysis
-- Plus redo + undo phases = 4+ hours total recovery
```

### Fix

**1. Immediate (after database was online):**
```sql
-- Shrink the log to release inactive VLFs
BACKUP LOG EHR_DB TO DISK = 'NUL'; -- Truncate the log
DBCC SHRINKFILE(EHR_DB_log, 1024); -- Shrink to 1GB

-- Regrow the log in large chunks (creates fewer, larger VLFs)
ALTER DATABASE EHR_DB MODIFY FILE (NAME = EHR_DB_log, SIZE = 32GB);
-- 32GB with one growth = ~32 VLFs (each ~1GB)
```

**2. Preventive configuration:**
```sql
-- Set explicit log file growth (not percentage!)
ALTER DATABASE EHR_DB MODIFY FILE (
    NAME = EHR_DB_log, 
    SIZE = 32GB,
    FILEGROWTH = 4GB  -- Each growth adds ~4 VLFs of ~1GB each
    -- NEVER use percentage growth for production
);
```

**After fix:**
- VLF count: 36 (from 42,147)
- Recovery time: 45 seconds (from 4 hours 17 minutes)
- Backup speed: improved 3x

### VLF Count Guidelines

| VLF Count | Impact | Action |
|---|---|---|
| < 50 | Optimal | No action needed |
| 50-200 | Acceptable | Monitor |
| 200-1000 | Degraded recovery speed | Schedule shrink/regrow |
| > 1000 | Severely impacted recovery and backup | Immediate remediation |

### Lessons Learned
- Transaction log management is the most neglected SQL Server maintenance task
- Default autogrowth settings (10% or 1MB) create thousands of tiny VLFs over time
- Pre-size the transaction log and use fixed MB growth increments
- Monitor VLF counts as part of standard health checks
