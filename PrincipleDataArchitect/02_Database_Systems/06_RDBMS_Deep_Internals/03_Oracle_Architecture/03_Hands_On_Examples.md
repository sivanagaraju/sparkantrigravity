# Oracle Database Architecture — Hands-On Examples

## Lab 1: SGA and Buffer Cache Inspection

### View SGA Components

```sql
-- SGA breakdown
SELECT component, current_size / 1024 / 1024 AS mb,
       min_size / 1024 / 1024 AS min_mb,
       max_size / 1024 / 1024 AS max_mb
FROM v$sga_dynamic_components
ORDER BY current_size DESC;

-- Quick SGA summary
SHOW SGA;

-- Buffer cache hit ratio (should be >95%)
SELECT name, value FROM v$sysstat
WHERE name IN ('db block gets', 'consistent gets', 'physical reads');
-- Hit ratio = 1 - (physical reads / (db block gets + consistent gets))
```

### Buffer Cache Contents by Object

```sql
-- Which objects are consuming the most buffer cache?
SELECT o.object_name, o.object_type,
       COUNT(*) AS cached_blocks,
       COUNT(*) * 8 / 1024 AS cached_mb,
       SUM(DECODE(bh.dirty, 'Y', 1, 0)) AS dirty_blocks
FROM v$bh bh
JOIN dba_objects o ON bh.objd = o.data_object_id
WHERE o.owner = 'HR'
GROUP BY o.object_name, o.object_type
ORDER BY cached_blocks DESC
FETCH FIRST 20 ROWS ONLY;
```

### Shared Pool: Hard Parse vs Soft Parse Ratio

```sql
-- Parse efficiency
SELECT 'Hard Parse Ratio' AS metric,
       ROUND(
         (SELECT value FROM v$sysstat WHERE name = 'parse count (hard)') /
         NULLIF((SELECT value FROM v$sysstat WHERE name = 'parse count (total)'), 0) * 100
       , 2) || '%' AS value
FROM dual
UNION ALL
SELECT 'Soft Parse Ratio',
       ROUND(
         1 - (SELECT value FROM v$sysstat WHERE name = 'parse count (hard)') /
         NULLIF((SELECT value FROM v$sysstat WHERE name = 'parse count (total)'), 0)
       , 4) * 100 || '%'
FROM dual;
-- Target: hard parse ratio < 5%
```

---

## Lab 2: Redo Log Analysis

### Check Redo Log Configuration

```sql
-- Online redo log groups and members
SELECT l.group#, l.members, l.bytes / 1024 / 1024 AS size_mb,
       l.status, l.archived, l.sequence#,
       lf.member AS file_path
FROM v$log l
JOIN v$logfile lf ON l.group# = lf.group#
ORDER BY l.group#;

-- Log switch frequency (how often are redo logs filling up?)
SELECT TO_CHAR(first_time, 'YYYY-MM-DD HH24') AS hour,
       COUNT(*) AS log_switches
FROM v$log_history
WHERE first_time > SYSDATE - 1
GROUP BY TO_CHAR(first_time, 'YYYY-MM-DD HH24')
ORDER BY 1;
-- More than 4-6 switches per hour → redo logs are undersized
```

### Redo Generation Rate

```sql
-- Redo bytes generated per hour (last 24 hours)
SELECT TO_CHAR(begin_time, 'HH24:MI') AS time_slot,
       ROUND(value / 1024 / 1024, 1) AS redo_mb
FROM v$sysmetric_history
WHERE metric_name = 'Redo Generated Per Sec'
  AND begin_time > SYSDATE - 1
ORDER BY begin_time;
```

---

## Lab 3: Undo and Read Consistency

### Monitor Undo Usage

```sql
-- Undo tablespace utilization
SELECT tablespace_name, status,
       COUNT(*) AS extents,
       SUM(bytes) / 1024 / 1024 AS total_mb
FROM dba_undo_extents
GROUP BY tablespace_name, status
ORDER BY tablespace_name, status;
-- Status: ACTIVE = in use by active txn
--         UNEXPIRED = within undo retention period
--         EXPIRED = available for reuse

-- Current undo retention
SHOW PARAMETER undo_retention;

-- Active transactions and their undo usage
SELECT s.sid, s.serial#, s.username,
       t.used_ublk * (SELECT value FROM v$parameter WHERE name = 'db_block_size') / 1024 AS undo_kb,
       t.start_time, s.sql_id
FROM v$transaction t
JOIN v$session s ON t.ses_addr = s.saddr
ORDER BY t.used_ublk DESC;
```

### Demonstrate ORA-01555 Scenario

```sql
-- Session A: Start a long-running query
-- (Ensure UNDO_RETENTION is short for demo purposes)
ALTER SYSTEM SET undo_retention = 30;  -- 30 seconds

-- Session A:
SELECT COUNT(*) FROM large_table WHERE complex_predicate;
-- This will scan for several minutes

-- Session B: Run heavy DML that generates undo
BEGIN
  FOR i IN 1..1000000 LOOP
    UPDATE large_table SET col1 = col1 + 1 WHERE id = i;
    IF MOD(i, 10000) = 0 THEN COMMIT; END IF;
  END LOOP;
END;
/

-- Session A's query may get:
-- ORA-01555: snapshot too old: rollback segment number N too small
-- Because the undo records needed for consistent read have been overwritten
```

---

## Lab 4: Wait Event Analysis with ASH

### Top Wait Events Right Now

```sql
-- Current active session waits
SELECT event, wait_class, COUNT(*) AS sessions_waiting,
       ROUND(AVG(time_waited_micro) / 1000, 1) AS avg_wait_ms
FROM v$active_session_history
WHERE sample_time > SYSDATE - INTERVAL '5' MINUTE
  AND session_state = 'WAITING'
GROUP BY event, wait_class
ORDER BY sessions_waiting DESC
FETCH FIRST 10 ROWS ONLY;
```

### Historical Wait Analysis (AWR)

```sql
-- Top 5 wait events in the last hour
SELECT event_name, wait_class,
       total_waits, time_waited_micro / 1000000 AS time_waited_sec,
       ROUND(time_waited_micro / NULLIF(total_waits, 0) / 1000, 2) AS avg_wait_ms
FROM dba_hist_system_event
WHERE snap_id = (SELECT MAX(snap_id) FROM dba_hist_snapshot)
  AND wait_class != 'Idle'
ORDER BY time_waited_micro DESC
FETCH FIRST 10 ROWS ONLY;
```

### SQL Performance by Wait Events

```sql
-- Find the SQL consuming the most DB time
SELECT sql_id, sql_plan_hash_value,
       SUM(10) AS db_time_seconds,  -- each ASH sample = ~10 seconds
       COUNT(DISTINCT session_id) AS distinct_sessions,
       SUM(DECODE(session_state, 'ON CPU', 10, 0)) AS cpu_seconds,
       SUM(DECODE(wait_class, 'User I/O', 10, 0)) AS io_wait_seconds
FROM v$active_session_history
WHERE sample_time > SYSDATE - INTERVAL '1' HOUR
  AND sql_id IS NOT NULL
GROUP BY sql_id, sql_plan_hash_value
ORDER BY db_time_seconds DESC
FETCH FIRST 10 ROWS ONLY;
```

---

## Lab 5: Execution Plan Analysis

### Using DBMS_XPLAN

```sql
-- Explain without executing
EXPLAIN PLAN FOR
SELECT o.order_id, c.customer_name, o.total
FROM orders o JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date > DATE '2025-01-01' AND o.total > 1000;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);

-- Explain with actual execution statistics
SELECT /*+ GATHER_PLAN_STATISTICS */ o.order_id, c.customer_name, o.total
FROM orders o JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date > DATE '2025-01-01' AND o.total > 1000;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR(NULL, NULL, 'ALLSTATS LAST'));
-- Shows: E-Rows vs A-Rows (estimated vs actual)
-- If E-Rows ≠ A-Rows by more than 10x → stale statistics
```

### Checking for Bind Variable Peeking Issues

```sql
-- Find SQL with multiple execution plans (plan instability)
SELECT sql_id, COUNT(DISTINCT plan_hash_value) AS plan_count,
       SUM(executions) AS total_executions,
       ROUND(SUM(elapsed_time) / SUM(executions) / 1000, 1) AS avg_elapsed_ms
FROM v$sql
GROUP BY sql_id
HAVING COUNT(DISTINCT plan_hash_value) > 1
ORDER BY total_executions DESC
FETCH FIRST 20 ROWS ONLY;
```

---

## Lab 6: Segment and Tablespace Diagnostics

### Find Space-Wasting Segments

```sql
-- Tables with high row chaining / migration
SELECT owner, table_name, chain_cnt,
       ROUND(chain_cnt / NULLIF(num_rows, 0) * 100, 1) AS chain_pct
FROM dba_tables
WHERE chain_cnt > 0 AND num_rows > 10000
ORDER BY chain_pct DESC
FETCH FIRST 20 ROWS ONLY;
-- chain_pct > 20% → rows are too wide for block size; consider:
--   1. Increase db_block_size (requires recreating tablespace)
--   2. Move wide columns to a separate table
--   3. ALTER TABLE MOVE to re-pack rows

-- Tablespace usage
SELECT tablespace_name,
       ROUND(SUM(bytes) / 1024 / 1024 / 1024, 1) AS allocated_gb,
       ROUND(SUM(bytes - NVL(free_bytes, 0)) / 1024 / 1024 / 1024, 1) AS used_gb,
       ROUND((SUM(bytes - NVL(free_bytes, 0)) / SUM(bytes)) * 100, 1) AS used_pct
FROM (
  SELECT tablespace_name, bytes, NULL AS free_bytes FROM dba_data_files
  UNION ALL
  SELECT tablespace_name, NULL, bytes FROM dba_free_space
)
GROUP BY tablespace_name
ORDER BY used_pct DESC;
```

---

## Lab 7: Data Guard Status (if configured)

```sql
-- Check Data Guard configuration
SELECT database_role, protection_mode, protection_level,
       switchover_status
FROM v$database;

-- Redo transport lag (standby behind primary)
SELECT name, value, datum_time
FROM v$dataguard_stats
WHERE name IN ('transport lag', 'apply lag', 'apply finish time');

-- Redo apply rate on standby
SELECT process, status, sequence#, block#
FROM v$managed_standby
WHERE process LIKE 'MRP%';  -- Media Recovery Process
```

---

## Runnable Exercise

### Exercise: Diagnose a "Library Cache Lock" Contention

**Scenario**: Application response time spikes from 5ms to 500ms. AWR shows top wait event: `library cache lock`.

```sql
-- Step 1: Identify sessions waiting on library cache
SELECT sid, serial#, event, p1text, p1, p2text, p2,
       wait_time_micro / 1000 AS wait_ms,
       sql_id
FROM v$session
WHERE event LIKE 'library cache%'
  AND state = 'WAITING';

-- Step 2: Check hard parse rate
SELECT value FROM v$sysstat WHERE name = 'parse count (hard)';
-- Wait 60 seconds, check again. If > 200/sec → hard parse storm

-- Step 3: Find the SQL using literal values (not bind variables)
SELECT sql_id, sql_text, parse_calls, executions
FROM v$sql
WHERE sql_text LIKE 'SELECT * FROM users WHERE id = %'
  AND sql_text NOT LIKE '%:1%'
ORDER BY parse_calls DESC
FETCH FIRST 10 ROWS ONLY;

-- Step 4: Fix — use CURSOR_SHARING = FORCE as emergency measure
ALTER SYSTEM SET cursor_sharing = 'FORCE';
-- This forces Oracle to replace literals with system-generated bind variables
-- Permanent fix: modify application to use bind variables
```
