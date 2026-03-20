# Oracle Database Architecture — Pitfalls and Anti-Patterns

## Anti-Pattern 01: Not Using Bind Variables

### Why It's Tempting
String concatenation is simpler to write and debug. Dynamic SQL with changing predicates seems easier with literal values. Developers unfamiliar with Oracle's shared pool architecture don't understand the cost.

### Why It's Dangerous

Every unique SQL text triggers a **hard parse** — a full optimization pass that takes 1-100ms and holds shared pool latches. At scale:

| Hard Parses/sec | Impact |
|---|---|
| < 50 | Acceptable |
| 50-200 | Shared pool pressure; increased latch contention |
| 200-500 | Visible latency degradation; library cache waits |
| > 500 | System unusable; shared pool exhaustion; ORA-04031 |

With bind variables, Oracle parses once and reuses the execution plan for all subsequent executions (soft parse: ~0.1ms).

### Detection

```sql
-- Hard parse ratio (should be < 5%)
SELECT ROUND(
  (SELECT value FROM v$sysstat WHERE name = 'parse count (hard)') /
  NULLIF((SELECT value FROM v$sysstat WHERE name = 'parse count (total)'), 0) * 100, 2
) AS hard_parse_pct FROM dual;

-- Find SQL with literals (many similar texts, each executed once)
SELECT COUNT(*) AS similar_count, MIN(sql_text) AS sample_sql
FROM v$sql
WHERE sql_text LIKE 'SELECT%FROM employees WHERE emp_id =%'
GROUP BY REGEXP_REPLACE(sql_text, '[0-9]+', 'N')
HAVING COUNT(*) > 10
ORDER BY similar_count DESC;

-- Version-7 cursor leak: single-use cursors consuming shared pool
SELECT COUNT(*) FROM v$sql WHERE executions = 1;
-- If > 50% of cursors execute once → literal SQL problem
```

### Fix
- **Application**: Use `PreparedStatement` (JDBC), bind variables (PL/SQL `:var`), parameterized queries
- **Emergency**: `ALTER SYSTEM SET cursor_sharing = 'FORCE';` (converts literals to binds automatically)
- **Monitoring**: Alert on hard parse ratio > 10%

---

## Anti-Pattern 02: Undersized Undo for Long Queries

### Why It's Dangerous
Oracle's read consistency depends on undo records. A query that started at SCN 5000000 needs to reconstruct blocks modified after that SCN by applying undo. If those undo records have been overwritten → **ORA-01555: snapshot too old**.

### Detection

```sql
-- Check undo retention vs longest active query
SELECT
  (SELECT value FROM v$parameter WHERE name = 'undo_retention') AS undo_retention_sec,
  (SELECT MAX(elapsed_time/1000000) FROM v$sql WHERE executions > 0) AS longest_query_sec;
-- If longest_query > undo_retention → ORA-01555 risk

-- Historical ORA-01555 occurrences
SELECT begin_time, unxpstealcnt AS unexpired_stolen,
       ssolderrcnt AS snapshot_too_old_count
FROM v$undostat
WHERE ssolderrcnt > 0
ORDER BY begin_time DESC;
```

### Fix
- `UNDO_RETENTION = longest_query_duration + safety_margin`
- `ALTER TABLESPACE undo_ts RETENTION GUARANTEE;` for critical read-consistency
- Size undo tablespace: `undo_rate_gb_per_hour × max_query_hours × 1.5`
- Move long-running analytics to an Active Data Guard standby

---

## Anti-Pattern 03: Excessive Redo Log Switching

### Why It's Dangerous

Each log switch triggers a partial checkpoint. If redo logs are undersized and switching every few minutes:
1. Checkpoint I/O competes with application I/O
2. ARCn may not finish archiving before the redo log needs to be reused → `log file switch (archiving needed)` → **database hangs**
3. Recovery scans more redo log files

### Detection

```sql
-- Log switches per hour (should be < 4-6)
SELECT TO_CHAR(first_time, 'YYYY-MM-DD HH24') AS hour,
       COUNT(*) AS switches
FROM v$log_history
WHERE first_time > SYSDATE - 1
GROUP BY TO_CHAR(first_time, 'YYYY-MM-DD HH24')
HAVING COUNT(*) > 4
ORDER BY 1;

-- Check for "log file switch" wait events
SELECT event, total_waits, time_waited_micro/1000000 AS time_waited_sec
FROM v$system_event
WHERE event LIKE '%log file switch%';
```

### Fix
- Size online redo logs for 15-30 minute switches: `redo_bytes_per_sec × 1800 seconds`
- Typical production sizing: 2-8 GB per redo log file
- Minimum 3 redo log groups; 4-6 for high-write workloads
- Separate redo logs on dedicated I/O path (different from data files)

---

## Anti-Pattern 04: RAC Without Application Affinity

### Why It's Dangerous

RAC provides horizontal scaling, but only if different nodes access different data. If all nodes modify the same blocks:

```
Node 1: UPDATE accounts SET balance = 100 WHERE id = 42;
  → Requests exclusive lock on block containing id=42
  → Cache Fusion ships block from Node 2 via interconnect
  → Modifies block

Node 2: UPDATE accounts SET balance = 200 WHERE id = 42;
  → Requests exclusive lock on same block
  → Cache Fusion ships block back from Node 1
  → "gc buffer busy" wait
```

This "block ping-pong" creates **gc buffer busy** waits that negate RAC's scaling benefits.

### Detection

```sql
-- gc wait events in AWR
SELECT event, total_waits, time_waited_micro/1000000 AS sec
FROM v$system_event
WHERE event LIKE 'gc%'
ORDER BY time_waited_micro DESC;

-- Blocks being shipped between instances
SELECT inst_id, class, cr_block AS consistent_read_ships,
       current_block AS current_mode_ships
FROM gv$instance_cache_transfer
ORDER BY current_block DESC;
```

### Fix
1. **Hash-partition** hot tables by primary key — different partitions reside on different nodes' caches
2. **Application-level affinity**: Route user sessions by account range or region to specific RAC nodes
3. **Service-based routing**: Create Oracle services mapped to specific instances; direct OLTP to Node 1-2, reporting to Node 3-4
4. **Sequence tuning**: `CACHE 10000 NOORDER` — each node pre-allocates a batch of sequence values locally

---

## Anti-Pattern 05: Ignoring Statistics Maintenance

### Why It's Dangerous

Oracle's cost-based optimizer (CBO) relies on table and index statistics to choose execution plans. Stale statistics → wrong cardinality estimates → catastrophic plan choices.

Example: Optimizer estimates query will return 10 rows (based on stale stats) → chooses Nested Loop join. Actual rows: 2,000,000 → Nested Loop does 2M index lookups instead of a Hash Join.

### Detection

```sql
-- Tables with stale or missing statistics
SELECT owner, table_name, num_rows, last_analyzed,
       stale_stats, stattype_locked
FROM dba_tab_statistics
WHERE owner = 'MYAPP'
  AND (stale_stats = 'YES' OR last_analyzed IS NULL OR last_analyzed < SYSDATE - 30)
ORDER BY num_rows DESC;

-- Queries with bad estimates (estimated vs actual rows mismatch)
SELECT sql_id, child_number,
       ROUND(rows_processed / NULLIF(optimizer_estimated_rows, 0), 1) AS estimate_ratio
FROM (
  SELECT sql_id, child_number, rows_processed,
         -- Approximation: check via DBMS_XPLAN for precise values
         CASE WHEN rows_processed > 0 THEN rows_processed ELSE 1 END AS optimizer_estimated_rows
  FROM v$sql
  WHERE executions > 10
)
WHERE rows_processed / NULLIF(optimizer_estimated_rows, 0) > 100
ORDER BY rows_processed DESC;
```

### Fix
- **Automatic**: `DBMS_STATS.GATHER_DATABASE_STATS(options => 'GATHER STALE')` in nightly maintenance window
- **Incremental** for partitioned tables: `DBMS_STATS.SET_TABLE_PREFS('OWNER', 'TABLE', 'INCREMENTAL', 'TRUE');`
- **Histograms** for skewed data: `METHOD_OPT => 'FOR ALL COLUMNS SIZE AUTO'`
- **SQL Plan Baselines**: Lock known-good plans to prevent regression even if statistics change

---

## Anti-Pattern 06: Single Large Tablespace for Everything

### Why It's Dangerous
- Cannot set different block sizes for different workload types (OLTP=8KB, DW=16KB)
- Cannot archive or drop old data by partition — must DELETE row by row
- Backup/recovery is all-or-nothing at tablespace level
- Space management contention; single point of failure

### Fix

```sql
-- Recommended tablespace strategy:
-- 1. SYSTEM + SYSAUX: Oracle internal (never touch)
-- 2. UNDO: Dedicated undo tablespace with RETENTION GUARANTEE
-- 3. TEMP: Dedicated temporary tablespace for sorts/hash joins
-- 4. DATA_CURRENT: Active data (last 1-2 years)
-- 5. DATA_ARCHIVE: Historical data (compressed, read-only)
-- 6. INDEX_TS: Separate tablespace for indexes (different I/O pattern)
-- 7. LOB_TS: Separate tablespace for LOB data

CREATE TABLESPACE data_current
  DATAFILE '/u01/oradata/data_current_01.dbf' SIZE 50G AUTOEXTEND ON MAXSIZE 200G
  EXTENT MANAGEMENT LOCAL UNIFORM SIZE 1M
  SEGMENT SPACE MANAGEMENT AUTO;

CREATE TABLESPACE data_archive
  DATAFILE '/u02/oradata/data_archive_01.dbf' SIZE 100G
  DEFAULT TABLE COMPRESS FOR OLTP;
-- Archive tablespace uses compression; can be read-only after loading
```

---

## Anti-Pattern Summary Table

| # | Anti-Pattern | Root Cause | Detection Signal | Fix |
|---|---|---|---|---|
| 01 | No bind variables | Literal SQL → hard parse per execution | Hard parse ratio > 10%, library cache waits | PreparedStatement; cursor_sharing=FORCE (emergency) |
| 02 | Undersized undo | Short retention vs long queries | ORA-01555, undo steal counts | Retention = max query time + margin; GUARANTEE |
| 03 | Small redo logs | Frequent log switches → checkpoint storms | > 6 switches/hour, log file switch waits | Size for 15-30 min switches |
| 04 | RAC without affinity | All nodes hit same blocks | gc buffer busy waits > 10% of DB time | Partition hot tables; application affinity |
| 05 | Stale statistics | CBO makes wrong plan choices | E-Rows vs A-Rows mismatch > 10x | Auto-gather stale stats; SQL Plan Baselines |
| 06 | Single tablespace | No granular management | Can't archive, different I/O mixed | Separate by function: data, index, LOB, undo, temp |
