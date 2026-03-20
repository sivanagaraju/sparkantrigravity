# MySQL InnoDB — Pitfalls and Anti-Patterns

## Anti-Pattern 01: Using UUID as Primary Key

### Why It's Tempting
- Globally unique without coordination
- No sequence bottleneck across shards
- Hides business logic (no guessable sequential IDs)

### Why It's Dangerous on InnoDB

InnoDB stores rows in a **clustered B+ Tree** ordered by primary key. UUIDv4 is random, so each INSERT targets a random leaf page:

```
Sequential PK (AUTO_INCREMENT):     Random PK (UUIDv4):
├── Page 100 [rows 1-200]           ├── Page 100 [row 42, row 189, row 7...]
├── Page 101 [rows 201-400]         ├── Page 101 [row 1003, row 55, row 812...]
├── Page 102 [rows 401-600]  ← append here   ├── PAGE SPLIT! ← insert row 150 here
└── ...                              └── ...
```

**Measured Impact:**
| Metric | AUTO_INCREMENT PK | UUIDv4 PK | Difference |
|---|---|---|---|
| Insert throughput (10M rows) | 28,000 rows/sec | 8,000 rows/sec | 3.5x slower |
| Data file size | 1.8 GB | 2.9 GB | 61% larger |
| Page split count | ~200 | ~450,000 | 2250x more |
| Buffer pool efficiency | 99.8% hit ratio | 92% hit ratio | Hot pages constantly evicted |

### Detection

```sql
-- Check if any table uses a non-integer PK
SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE,
       COLUMN_KEY, EXTRA
FROM INFORMATION_SCHEMA.COLUMNS
WHERE COLUMN_KEY = 'PRI'
  AND DATA_TYPE IN ('varchar', 'char', 'binary', 'varbinary', 'blob')
  AND TABLE_SCHEMA NOT IN ('mysql', 'information_schema', 'performance_schema');

-- Check page split rates
SELECT NAME, COUNT FROM INFORMATION_SCHEMA.INNODB_METRICS
WHERE NAME LIKE '%page_split%';
```

### Fix
- **Option 1**: Use `BIGINT AUTO_INCREMENT` as PK. Add UUID as a secondary unique index if needed for external references.
- **Option 2**: Use UUIDv7 (time-ordered) or MySQL 8.0's `UUID_TO_BIN(uuid, 1)` which reorders the timestamp portion for temporal locality.
- **Option 3**: Use `BINARY(16)` with `UUID_TO_BIN(UUID(), 1)` for ordered binary UUIDs.

```sql
-- UUIDv7-style ordered UUID (MySQL 8.0+)
CREATE TABLE users (
    id BINARY(16) PRIMARY KEY DEFAULT (UUID_TO_BIN(UUID(), 1)),
    name VARCHAR(100)
) ENGINE=InnoDB;
-- swap_flag=1 rearranges UUID bytes for time-ordering
```

---

## Anti-Pattern 02: Ignoring the History List Length

### Why It's Dangerous
When a long-running transaction holds a read view open, the purge thread cannot clean undo log records that might be needed by that read view. The **history list length** grows unbounded.

**Symptoms:**
- Simple SELECT queries slow down (must traverse longer undo chains to find visible row version)
- Undo tablespace files grow to tens of gigabytes
- Eventually, new transactions slow down as InnoDB struggles with undo log management

### Detection

```sql
-- Quick check
SHOW ENGINE INNODB STATUS\G
-- Look for: History list length: <value>
-- Healthy: < 10,000
-- Warning: 10,000 - 100,000
-- Critical: > 100,000

-- Automated monitoring
SELECT COUNT FROM INFORMATION_SCHEMA.INNODB_METRICS
WHERE NAME = 'trx_rseg_history_len';

-- Find the transaction holding the oldest read view
SELECT
    trx_id, trx_state, trx_started,
    TIMESTAMPDIFF(SECOND, trx_started, NOW()) AS duration_sec,
    trx_rows_locked, trx_mysql_thread_id, trx_query
FROM INFORMATION_SCHEMA.INNODB_TRX
ORDER BY trx_started ASC
LIMIT 5;
```

### Fix
- Kill the offending long-running transaction: `KILL <trx_mysql_thread_id>;`
- Set guardrails: `innodb_max_purge_lag = 100000` (throttle DML when purge falls behind)
- `MAX_EXECUTION_TIME` hint on analytical queries
- Move analytical workloads to a dedicated read replica
- Monitor history list length and alert at 50,000

---

## Anti-Pattern 03: Oversized Redo Log (or Undersized)

### Undersized Redo Log
**Problem**: `innodb_log_file_size` is too small relative to write volume. InnoDB runs out of redo log space and triggers **furious flushing** — aggressively writing dirty pages to disk to advance the checkpoint and free redo space. This causes I/O storms and latency spikes.

**Detection**: 
```sql
-- If checkpoint_age approaches total redo log capacity, you're at risk
SHOW ENGINE INNODB STATUS\G
-- Calculate: Log sequence number - Last checkpoint at = checkpoint age
-- Total redo capacity = innodb_log_file_size × innodb_log_files_in_group
-- If checkpoint_age > 75% of total capacity → undersized
```

### Oversized Redo Log
**Problem**: `innodb_log_file_size` is too large. Crash recovery must replay all redo records since the last checkpoint. A 128GB redo log that's 50% full means replaying 64GB of redo on crash — recovery could take 30+ minutes.

### The Goldilocks Zone

```
Total redo capacity should hold approximately 1 hour of peak writes.

Calculation:
1. Measure redo write rate: SELECT VARIABLE_VALUE FROM performance_schema.global_status
   WHERE VARIABLE_NAME = 'Innodb_os_log_written';
2. Wait 60 seconds, measure again
3. Difference = bytes per minute → multiply by 60 for hourly rate
4. Set total redo capacity = hourly_rate × 1 (1 hour)

Example:
  Redo write rate: 200 MB/min = 12 GB/hour
  Set: innodb_redo_log_capacity = 12G  (MySQL 8.0.30+)
  Or: innodb_log_file_size = 6G with innodb_log_files_in_group = 2
```

---

## Anti-Pattern 04: Not Using Covering Indexes

### Why It's a Problem on InnoDB Specifically

Remember: every secondary index lookup on InnoDB requires a **bookmark lookup** back to the clustered index. If your query reads columns not in the secondary index, InnoDB must:
1. Traverse the secondary index B+ Tree → find PK value
2. Traverse the clustered index B+ Tree → find the full row
3. Extract the needed columns

For a query returning 10,000 rows via a secondary index: **20,000 B+ Tree traversals** instead of 10,000.

### Detection

```sql
-- Identify queries doing excessive bookmark lookups
EXPLAIN FORMAT=JSON SELECT email, created_at FROM users WHERE email LIKE 'alice%';
-- Look for: "using_index": false → means bookmark lookup is happening

-- Check handler stats for a session
FLUSH STATUS;
SELECT email, created_at FROM users WHERE email LIKE 'alice%';
SHOW SESSION STATUS LIKE 'Handler_read%';
-- Handler_read_rnd_next = rows read via bookmark lookup
```

### Fix: Covering Index

```sql
-- Before: index only on search column
CREATE INDEX idx_email ON users (email);
-- Query reads email + created_at, but created_at isn't in the index → bookmark lookup

-- After: covering index includes all queried columns
CREATE INDEX idx_email_cover ON users (email, created_at);
-- EXPLAIN now shows "Using index" → no clustered index access needed

-- For INCLUDE-like behavior (MySQL doesn't have INCLUDE syntax like PostgreSQL):
-- Put filter/join columns first, then SELECT-only columns
CREATE INDEX idx_cover ON orders (status, created_at, customer_id, total);
```

---

## Anti-Pattern 05: Large Transactions with Row-Based Replication

### Why It's Dangerous

MySQL row-based replication (`binlog_format = ROW`) writes every modified row to the binary log. A single `UPDATE` touching 5 million rows generates a binary log event of potentially several gigabytes. The replica must:
1. Receive the entire event over the network
2. Parse and apply each row change
3. Single-threaded if the event is a single transaction (prior to MySQL 8.0's writeset-based parallelism)

### Detection

```sql
-- Find large transactions in the binary log
SHOW BINARY LOGS;
-- If individual binlog files jump from 100MB to 5GB, a large transaction occurred

-- Check current transaction size
SELECT trx_id, trx_state, trx_rows_modified, trx_rows_locked
FROM INFORMATION_SCHEMA.INNODB_TRX
WHERE trx_rows_modified > 100000;

-- Monitor replication lag
SHOW REPLICA STATUS\G
-- Seconds_Behind_Source > 60 → investigate
```

### Fix
- **Batch operations**: `DELETE FROM orders WHERE created_at < '2024-01-01' LIMIT 10000;` in a loop with `SLEEP(0.1)` between batches
- `binlog_row_image = MINIMAL` reduces binlog event size by writing only PK + changed columns
- `replica_parallel_workers = 16` + `replica_parallel_type = LOGICAL_CLOCK` (MySQL 8.0+)
- For MySQL 8.0.27+: `binlog_transaction_dependency_tracking = WRITESET` enables writeset-based parallelism on replicas

---

## Anti-Pattern 06: Disabling the Doublewrite Buffer Without Atomic Writes

### Why People Disable It
The doublewrite buffer writes every dirty page twice — once to the doublewrite area, once to the final data file. This is 2x write amplification. On write-heavy workloads, it can consume significant I/O bandwidth.

### When Disabling Is Safe
- Filesystem supports atomic writes (ZFS, ext4 with `O_DIRECT` and hardware RAID with battery-backed cache)
- Some SSDs support atomic 16KB writes
- Running on AWS with EBS io2 Block Express (provides atomic writes)

### When Disabling Is Dangerous
- Standard ext4/XFS without hardware RAID BBU
- Any filesystem where a 16KB write can be partially completed (power failure mid-write)
- Direct-attached SSDs without power-loss protection

### Detection

```sql
SHOW VARIABLES LIKE 'innodb_doublewrite';
-- If OFF, verify atomic write support in your storage stack
-- If unsure, leave it ON — the cost is 2x sequential write to a contiguous area,
-- which is far cheaper than data corruption from a torn page
```

---

## Anti-Pattern Summary Table

| # | Anti-Pattern | Root Cause | Detection Signal | Fix |
|---|---|---|---|---|
| 01 | UUID as PK | Random key → page splits | High DATA_FREE, slow inserts | AUTO_INCREMENT PK + UUID secondary index, or UUIDv7 |
| 02 | Ignoring history list | Long transactions block purge | history_list_len > 100K | Kill long txns, set purge lag limits, move analytics to replica |
| 03 | Wrong redo log size | Undersized → furious flush; oversized → slow recovery | Checkpoint age > 75% capacity | Size for 1 hour of peak writes |
| 04 | No covering indexes | Bookmark lookups on every row | EXPLAIN: "using_index: false" | Add covering composite indexes |
| 05 | Large single-txn DML | Row-based replication of millions of rows | Replica lag, huge binlog events | Batch in 10K-row chunks |
| 06 | Disabled doublewrite without atomic storage | 2x write amp avoidance | `innodb_doublewrite = OFF` | Verify storage supports atomic writes before disabling |
