# MySQL InnoDB — Hands-On Examples

## Lab 1: Buffer Pool Inspection

### Check Buffer Pool Status

```sql
-- Buffer pool hit ratio (should be >99% in production)
SHOW GLOBAL STATUS LIKE 'Innodb_buffer_pool%';

-- Key metrics to watch:
-- Innodb_buffer_pool_read_requests  = logical reads (from pool)
-- Innodb_buffer_pool_reads          = physical reads (disk I/O)
-- Hit ratio = 1 - (pool_reads / pool_read_requests)

SELECT
    (1 - (
        (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads')
        /
        (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests')
    )) * 100 AS buffer_pool_hit_ratio_pct;
```

### Buffer Pool Contents by Table

```sql
-- Which tables are consuming the most buffer pool pages?
-- Requires INFORMATION_SCHEMA.INNODB_BUFFER_PAGE (heavy query on large pools)
SELECT
    TABLE_NAME,
    INDEX_NAME,
    COUNT(*) AS pages_in_pool,
    COUNT(*) * 16 / 1024 AS size_mb,
    SUM(IS_OLD = 'YES') AS pages_in_old_sublist,
    SUM(IS_OLD = 'NO') AS pages_in_young_sublist
FROM INFORMATION_SCHEMA.INNODB_BUFFER_PAGE
WHERE TABLE_NAME IS NOT NULL
  AND TABLE_NAME NOT LIKE '%`mysql`%'
GROUP BY TABLE_NAME, INDEX_NAME
ORDER BY pages_in_pool DESC
LIMIT 20;
```

### Buffer Pool Warm-Up After Restart

```sql
-- Check if dump/load is configured
SHOW VARIABLES LIKE 'innodb_buffer_pool_dump%';
SHOW VARIABLES LIKE 'innodb_buffer_pool_load%';

-- Manually dump buffer pool contents (page list)
SET GLOBAL innodb_buffer_pool_dump_now = ON;

-- Manually reload after restart
SET GLOBAL innodb_buffer_pool_load_now = ON;

-- Monitor load progress
SHOW STATUS LIKE 'Innodb_buffer_pool_load_status';
```

---

## Lab 2: Redo Log Analysis

### Check Redo Log Configuration

```sql
-- Redo log size and utilization
SHOW VARIABLES LIKE 'innodb_log_file_size';      -- Per file (e.g., 1G)
SHOW VARIABLES LIKE 'innodb_log_files_in_group';  -- Number of files (default 2)
-- Total redo log capacity = file_size × files_in_group

-- MySQL 8.0.30+: dynamic redo log sizing
SHOW VARIABLES LIKE 'innodb_redo_log_capacity';   -- Total redo log space
```

### Checkpoint Lag — Are We Running Out of Redo Space?

```sql
-- Check if redo log is being consumed faster than pages are flushed
SHOW ENGINE INNODB STATUS\G
-- Look for:
-- Log sequence number:    current LSN
-- Log flushed up to:     last flushed LSN
-- Pages flushed up to:    oldest dirty page LSN
-- Last checkpoint at:     recovery start point

-- If (Log sequence number - Last checkpoint) approaches total redo log size,
-- InnoDB will stall writes to avoid overwriting un-checkpointed redo entries.
-- This is a "checkpoint furious flush" — the most dangerous redo log issue.
```

### Redo Log Write Rate

```sql
-- Track redo log bytes written per second
SELECT
    VARIABLE_VALUE AS redo_log_bytes_written
FROM performance_schema.global_status
WHERE VARIABLE_NAME = 'Innodb_os_log_written';

-- Wait 10 seconds, run again, compute difference
-- If rate > 50MB/s, consider increasing redo log size
```

---

## Lab 3: InnoDB MVCC in Action

### Observe Undo Log and Read Views

```sql
-- Session A: start a consistent read
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
SELECT * FROM users WHERE id = 1;
-- Returns: name = 'Alice'

-- Session B: update the row
UPDATE users SET name = 'Bob' WHERE id = 1;
COMMIT;

-- Session A: read again — MVCC reconstructs old version from undo log
SELECT * FROM users WHERE id = 1;
-- Still returns: name = 'Alice' (reading from undo log)

-- Check undo log utilization
SHOW ENGINE INNODB STATUS\G
-- Look for:
-- History list length: N  (number of unpurged undo records)
-- If this grows, the purge thread is falling behind

COMMIT;  -- Session A releases its read view
-- Now purge thread can clean undo records for trx_id < Session A's read view
```

### Monitor Undo Tablespace Growth

```sql
-- Check undo tablespace usage (MySQL 8.0+)
SELECT
    TABLESPACE_NAME,
    FILE_NAME,
    AUTOEXTEND_SIZE / 1024 / 1024 AS autoextend_mb,
    ENGINE
FROM INFORMATION_SCHEMA.FILES
WHERE TABLESPACE_NAME LIKE 'innodb_undo%';

-- Check history list length (unpurged undo records)
SELECT
    NAME, SUBSYSTEM, COUNT
FROM INFORMATION_SCHEMA.INNODB_METRICS
WHERE NAME = 'trx_rseg_history_len';
-- If > 100000, long transactions are preventing purge
```

---

## Lab 4: Page Splits and Fragmentation

### Detect Page Splits

```sql
-- Page split count (indicates fragmentation from random inserts)
SELECT
    NAME, COUNT, COMMENT
FROM INFORMATION_SCHEMA.INNODB_METRICS
WHERE NAME LIKE '%page_split%';

-- Enable metrics if not already on
SET GLOBAL innodb_monitor_enable = 'index_page_splits';
SET GLOBAL innodb_monitor_enable = 'index_page_merge_attempts';
SET GLOBAL innodb_monitor_enable = 'index_page_merge_successful';
```

### Measure Table Fragmentation

```sql
-- Compare logical size vs actual file size
SELECT
    TABLE_NAME,
    TABLE_ROWS,
    DATA_LENGTH / 1024 / 1024 AS data_mb,
    INDEX_LENGTH / 1024 / 1024 AS index_mb,
    DATA_FREE / 1024 / 1024 AS free_space_mb,
    ROUND(DATA_FREE / (DATA_LENGTH + INDEX_LENGTH + DATA_FREE) * 100, 1) AS fragmentation_pct
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'mydb'
  AND ENGINE = 'InnoDB'
ORDER BY fragmentation_pct DESC;

-- Rebuild a fragmented table (acquires metadata lock, copies data)
ALTER TABLE users ENGINE=InnoDB;  -- In-place rebuild with online DDL
```

### UUID vs Auto-Increment PK: Page Split Demo

```sql
-- Create two identical tables with different PK strategies
CREATE TABLE pk_auto (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    data VARCHAR(100)
) ENGINE=InnoDB;

CREATE TABLE pk_uuid (
    id BINARY(16) PRIMARY KEY,  -- UUID stored as binary
    data VARCHAR(100)
) ENGINE=InnoDB;

-- Insert 100K rows into each
-- pk_auto: sequential inserts, always append to rightmost leaf page
-- pk_uuid: random inserts, cause page splits across the tree

DELIMITER //
CREATE PROCEDURE insert_auto(IN n INT)
BEGIN
    DECLARE i INT DEFAULT 0;
    WHILE i < n DO
        INSERT INTO pk_auto (data) VALUES (REPEAT('x', 50));
        SET i = i + 1;
    END WHILE;
END//

CREATE PROCEDURE insert_uuid(IN n INT)
BEGIN
    DECLARE i INT DEFAULT 0;
    WHILE i < n DO
        INSERT INTO pk_uuid (id, data) VALUES (UNHEX(REPLACE(UUID(), '-', '')), REPEAT('x', 50));
        SET i = i + 1;
    END WHILE;
END//
DELIMITER ;

CALL insert_auto(100000);
CALL insert_uuid(100000);

-- Compare fragmentation
SELECT TABLE_NAME, DATA_LENGTH/1024/1024 AS data_mb, DATA_FREE/1024/1024 AS free_mb
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME IN ('pk_auto', 'pk_uuid');
-- pk_uuid will have significantly more DATA_FREE (wasted space from splits)
```

---

## Lab 5: Change Buffer Behavior

```sql
-- Check change buffer status
SHOW VARIABLES LIKE 'innodb_change_buffer_max_size';   -- % of buffer pool
SHOW VARIABLES LIKE 'innodb_change_buffering';          -- all, none, inserts, deletes, etc.

-- Monitor change buffer activity
SELECT
    NAME, COUNT, COMMENT
FROM INFORMATION_SCHEMA.INNODB_METRICS
WHERE NAME LIKE '%ibuf%'
ORDER BY NAME;

-- Key metrics:
-- ibuf_merges:       number of times change buffer was merged
-- ibuf_merges_insert: insert operations merged from change buffer
-- ibuf_size:         current change buffer size in pages
```

---

## Lab 6: Locking Analysis

### Detect Lock Waits in Real Time

```sql
-- MySQL 8.0+ Performance Schema approach
SELECT
    r.trx_id AS waiting_trx_id,
    r.trx_mysql_thread_id AS waiting_thread,
    r.trx_query AS waiting_query,
    b.trx_id AS blocking_trx_id,
    b.trx_mysql_thread_id AS blocking_thread,
    b.trx_query AS blocking_query,
    b.trx_started AS blocking_since
FROM performance_schema.data_lock_waits w
JOIN INFORMATION_SCHEMA.INNODB_TRX r ON r.trx_id = w.REQUESTING_ENGINE_TRANSACTION_ID
JOIN INFORMATION_SCHEMA.INNODB_TRX b ON b.trx_id = w.BLOCKING_ENGINE_TRANSACTION_ID;
```

### Visualize Gap Locks

```sql
-- Create test table
CREATE TABLE lock_demo (
    id INT PRIMARY KEY,
    val VARCHAR(50),
    INDEX idx_val (val)
) ENGINE=InnoDB;

INSERT INTO lock_demo VALUES (10, 'a'), (20, 'b'), (30, 'c');

-- Session A: range query with REPEATABLE READ (acquires next-key locks)
START TRANSACTION;
SELECT * FROM lock_demo WHERE id BETWEEN 15 AND 25 FOR UPDATE;
-- Locks: gap (10,20], record 20, gap (20,30]

-- Session B: try to insert into the locked gap
INSERT INTO lock_demo VALUES (12, 'x');
-- BLOCKED! Gap lock between 10 and 20 prevents this insert
-- This prevents phantom reads

-- Check which locks are held
SELECT
    OBJECT_NAME, INDEX_NAME, LOCK_TYPE, LOCK_MODE, LOCK_STATUS, LOCK_DATA
FROM performance_schema.data_locks
WHERE OBJECT_NAME = 'lock_demo';
```

---

## Lab 7: Deadlock Analysis

```sql
-- View the most recent deadlock
SHOW ENGINE INNODB STATUS\G
-- Find section: LATEST DETECTED DEADLOCK
-- Shows:
--   Transaction 1: which locks it held and which it was waiting for
--   Transaction 2: which locks it held and which it was waiting for
--   Victim: which transaction was rolled back

-- Enable deadlock detection logging (MySQL 8.0+)
SET GLOBAL innodb_print_all_deadlocks = ON;
-- Deadlocks are now logged to the MySQL error log
```

### Reproducing a Deadlock

```sql
-- Session A:
START TRANSACTION;
UPDATE lock_demo SET val = 'updated' WHERE id = 10;

-- Session B:
START TRANSACTION;
UPDATE lock_demo SET val = 'updated' WHERE id = 20;

-- Session A (now tries to lock what B holds):
UPDATE lock_demo SET val = 'updated_again' WHERE id = 20;
-- WAITING for B's lock on id=20

-- Session B (now tries to lock what A holds):
UPDATE lock_demo SET val = 'updated_again' WHERE id = 10;
-- DEADLOCK DETECTED! One transaction is rolled back automatically
```

---

## Runnable Exercise

### Exercise: Diagnose Why This Query Is Slow

Given:
```sql
CREATE TABLE orders (
    order_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    status ENUM('pending', 'shipped', 'delivered'),
    total DECIMAL(10,2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_customer (customer_id),
    INDEX idx_status (status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB;

-- 10M rows inserted. This query is slow:
SELECT customer_id, SUM(total) AS total_spent
FROM orders
WHERE status = 'delivered'
  AND created_at >= '2025-01-01'
GROUP BY customer_id
ORDER BY total_spent DESC
LIMIT 20;
```

### Diagnostic Steps:

```sql
-- Step 1: Check EXPLAIN
EXPLAIN FORMAT=JSON SELECT customer_id, SUM(total) AS total_spent
FROM orders WHERE status = 'delivered' AND created_at >= '2025-01-01'
GROUP BY customer_id ORDER BY total_spent DESC LIMIT 20;

-- Problem: likely using only idx_status OR idx_created (not both)
-- Then doing a "bookmark lookup" to clustered index for each matching row
-- to fetch customer_id and total (not in the chosen index)

-- Step 2: Create a covering composite index
ALTER TABLE orders ADD INDEX idx_status_created_cover (status, created_at, customer_id, total);

-- Now the query uses this single index:
-- 1. Range scan: status='delivered' AND created_at >= '2025-01-01'
-- 2. Customer_id and total are IN the index → no bookmark lookup
-- 3. GROUP BY and ORDER BY still require a temp table + filesort, but on fewer rows

-- Step 3: Verify with EXPLAIN
EXPLAIN FORMAT=JSON SELECT customer_id, SUM(total) AS total_spent
FROM orders WHERE status = 'delivered' AND created_at >= '2025-01-01'
GROUP BY customer_id ORDER BY total_spent DESC LIMIT 20;
-- Should show: Using index (covering), no table access
```
