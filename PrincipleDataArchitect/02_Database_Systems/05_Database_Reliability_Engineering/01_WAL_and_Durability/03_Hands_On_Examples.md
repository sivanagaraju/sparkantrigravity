# Hands-On Examples: WAL and Durability (PostgreSQL)

## 1. Inspecting the Current WAL Position

```sql
-- Get the current WAL insertion point (LSN)
SELECT pg_current_wal_lsn();
-- Returns: 0/3A000120

-- Get the WAL segment file name for a given LSN
SELECT pg_walfile_name('0/3A000120');
-- Returns: 00000001000000000000003A

-- Get the byte offset within the segment
SELECT pg_walfile_name_offset('0/3A000120');
-- Returns: (00000001000000000000003A, 288)
```

## 2. Measuring WAL Generation Rate

```sql
-- Snapshot the LSN, wait, then measure the delta
SELECT pg_current_wal_lsn() AS start_lsn;
-- ... run your workload for 60 seconds ...
SELECT pg_current_wal_lsn() AS end_lsn;

-- Calculate WAL generated (in bytes)
SELECT pg_wal_lsn_diff('0/3C000000', '0/3A000120') AS wal_bytes_generated;
-- Returns: 33554144 (about 32 MB in 60 seconds)

-- Monitor WAL generation in real-time (PostgreSQL 14+)
SELECT * FROM pg_stat_wal;
-- Shows: wal_records, wal_fpi (full page images count), 
--        wal_bytes, wal_buffers_full, wal_write, wal_sync
```

## 3. Checkpoint Tuning

```sql
-- View current checkpoint configuration
SHOW checkpoint_timeout;          -- Default: 5min
SHOW max_wal_size;                -- Default: 1GB
SHOW checkpoint_completion_target; -- Default: 0.9

-- Check when the last checkpoint occurred
SELECT checkpoints_timed, checkpoints_req, 
       checkpoint_write_time, checkpoint_sync_time,
       buffers_checkpoint, buffers_clean, buffers_backend
FROM pg_stat_bgwriter;
```

**Tuning guidance:**
```sql
-- For write-heavy OLTP: increase checkpoint interval to reduce FPW overhead
ALTER SYSTEM SET checkpoint_timeout = '15min';
ALTER SYSTEM SET max_wal_size = '4GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;

-- IMPORTANT: Longer checkpoint intervals mean longer crash recovery.
-- A 15-minute checkpoint timeout means up to 15 minutes of WAL replay on crash.
SELECT pg_reload_conf(); -- Apply without restart
```

## 4. The synchronous_commit Spectrum

```sql
-- Per-transaction durability control (Postgres superpower)
-- Use case: Bulk-loading analytics events that are re-derivable

BEGIN;
SET LOCAL synchronous_commit = 'off';
INSERT INTO analytics_events SELECT generate_series(1, 100000);
COMMIT; -- Returns immediately without waiting for fsync
-- Risk: last ~600ms of commits may be lost if server crashes RIGHT NOW

-- For the financial transaction in the same database:
BEGIN;
SET LOCAL synchronous_commit = 'on';
UPDATE accounts SET balance = balance - 1000 WHERE id = 42;
INSERT INTO transfers(from_id, amount) VALUES (42, 1000);
COMMIT; -- Waits for WAL fsync confirmation before returning
```

**This is the killer feature:** You can mix durability levels *per transaction* in the same database. Audit logs get `off` for speed; money movements get `on` for safety.

## 5. Inspecting WAL Contents with pg_waldump

```bash
# Decode WAL records from a specific segment (run as postgres user)
pg_waldump /var/lib/postgresql/16/main/pg_wal/00000001000000000000003A \
  --start=0/3A000000 --end=0/3A001000

# Output example:
# rmgr: Heap     len: 54  tx: 12345  lsn: 0/3A000028  desc: INSERT off 5
#   blkref #0: rel 1663/16384/16385 fork main blk 0 FPW
# rmgr: Transaction len: 34 tx: 12345 lsn: 0/3A000060 desc: COMMIT 2024-01-15
```

**Reading the output:**
- `rmgr: Heap` — This is a heap (table) operation.
- `FPW` — Full-Page Write was included (first modification after checkpoint).
- `rel 1663/16384/16385` — tablespace OID / database OID / relation OID.
- `blk 0` — Block (page) number 0 of the relation.

## 6. Simulating a Crash Recovery

```bash
# 1. Start a transaction, insert data, commit
psql -c "INSERT INTO test_wal VALUES (1, 'before crash');"
psql -c "INSERT INTO test_wal VALUES (2, 'also before crash');"

# 2. Force a crash (simulate power failure) — NEVER in production
pg_ctl -D /var/lib/postgresql/16/main stop -m immediate

# 3. Start the server — observe recovery in the log
pg_ctl -D /var/lib/postgresql/16/main start

# In the server log you will see:
# LOG:  database system was interrupted; last known up at 2024-01-15 10:00:00
# LOG:  redo starts at 0/3A000028
# LOG:  redo done at 0/3A000060
# LOG:  last completed transaction was at log time 2024-01-15 10:00:05
# LOG:  database system is ready to accept connections

# 4. Verify data survived
psql -c "SELECT * FROM test_wal;"
# Both rows are present because WAL was fsynced before COMMIT OK was returned.
```

## 7. Monitoring WAL Disk Usage

```sql
-- Check current WAL directory size
SELECT pg_size_pretty(sum(size)) AS wal_size
FROM pg_ls_waldir();

-- Monitor WAL retention (how far back WAL goes)
SELECT 
    min(modification) AS oldest_wal_file,
    max(modification) AS newest_wal_file,
    count(*) AS total_wal_files,
    pg_size_pretty(sum(size)) AS total_wal_size
FROM pg_ls_waldir();
```
