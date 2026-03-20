# 🧠 Mind Map – MySQL InnoDB Internals

---

## How to Use This Mind Map
- **For Revision**: Scan headers to recall InnoDB's core subsystems; compare with PostgreSQL equivalents
- **For Application**: Use Techniques section to identify the right diagnostic query for your InnoDB issue
- **For Interviews**: Be ready to explain clustered vs heap storage trade-offs and trace the InnoDB write path

---

## 🗺️ Theory & Concepts

### Storage Architecture — Clustered Index
- Table IS a B+ Tree ordered by primary key
  - Leaf nodes contain full row data (not just key)
  - Consequence: PK range scans = sequential I/O
  - Consequence: random PK (UUID) → page splits → fragmentation → 3.5x slower inserts
  - No PK defined → InnoDB uses first UNIQUE NOT NULL, else hidden 6-byte ROW_ID
- Secondary index leaf nodes store indexed columns + PK value
  - Lookup = 2 B+ Tree traversals (secondary → PK → clustered)
  - Covering index avoids the second traversal (`Using index` in EXPLAIN)
  - PK size bloats every secondary index

### Buffer Pool
- Modified LRU with young (5/8) / old (3/8) sublists
  - New pages enter old sublist; promoted to young only if accessed again within `innodb_old_blocks_time` (1000ms)
  - Purpose: prevent table scans from flushing hot pages
  - Size recommendation: 70-80% of RAM
  - Multiple instances (`innodb_buffer_pool_instances`) reduce mutex contention
  - Dump/load at shutdown/startup for fast warm-up

### Redo Log (Write-Ahead Log)
- Circular log files (`ib_logfile0`, `ib_logfile1`) or dynamic (MySQL 8.0.30+: `innodb_redo_log_capacity`)
- Records = physiological (physical page + logical operation)
- `innodb_flush_log_at_trx_commit` controls durability:
  - `1` = fsync on commit (default, safest, ~50% slower)
  - `2` = write to OS cache (survives MySQL crash, not OS crash)
  - `0` = buffer only (fastest, up to 1s data loss)
- Checkpoint: Page Cleaner flushes dirty pages → advances checkpoint LSN → frees redo space
- Failure mode: undersized redo → furious flushing (forced checkpoint) → I/O storms

### Undo Log and MVCC
- Only current row version in clustered index; old versions in undo log
- `roll_ptr` chains through undo records for version traversal
- Read view = snapshot of active transaction IDs at statement/transaction start
- Purge thread cleans undo records no longer needed by any read view
- History list length = count of unpurged undo records (must monitor)
- Failure mode: long transaction → purge blocked → undo tablespace bloat, slow reads

### Change Buffer
- Defers secondary index writes when target page not in buffer pool
- Only for non-unique indexes (unique indexes require page read for uniqueness check)
- Merged when: page is read into buffer pool, background merge, or during crash recovery
- `innodb_change_buffer_max_size = 25` (% of buffer pool)
- Impact: converts random secondary index I/O to sequential buffered writes

### Page Layout (16KB)
- FIL Header (38B): checksum, space ID, page number, LSN, prev/next page pointers
- Page Header (56B): record count, free space, heap top, index ID, level
- Infimum/Supremum: boundary pseudo-records
- User Records: singly-linked list ordered by PK, with page directory for binary search
- FIL Trailer (8B): checksum + LSN for integrity validation

### Locking
- Record lock: single index record
- Gap lock: gap between records (prevents phantom inserts)
- Next-key lock: record + preceding gap (default in REPEATABLE READ)
- Insert intention lock: allows concurrent inserts at different gap positions
- Deadlock detection: automatic victim selection, rollback of smallest transaction
- `innodb_print_all_deadlocks = ON` logs all deadlocks to error log

### Doublewrite Buffer
- Prevents torn pages (16KB page written in 4KB filesystem blocks)
- Write sequence: dirty page → doublewrite area (sequential) → fsync → data file (random)
- Recovery: if data file page is torn, load intact copy from doublewrite buffer
- Disable only with atomic write storage: `innodb_doublewrite = OFF`

---

## 🗺️ Techniques & Patterns

### T1: Primary Key Selection
- Use `BIGINT AUTO_INCREMENT` for compact, sequential PK
- If UUID required: use `UUID_TO_BIN(UUID(), 1)` for time-ordered binary UUID
- Never use `VARCHAR` or unordered `CHAR(36)` UUID as PK
- Rule: PK size × number of secondary index entries = hidden storage cost

### T2: Covering Index Design
- Include all columns needed by the query in the index
- Order: equality filters → range filters → SELECT-only columns
- Check: `EXPLAIN` shows `Using index` (no bookmark lookup)
- MySQL lacks PostgreSQL's `INCLUDE` clause; all columns are key columns in the index

### T3: Redo Log Sizing
- Size for ~1 hour of peak write volume
- Measure: `Innodb_os_log_written` per minute × 60
- MySQL 8.0.30+: use `innodb_redo_log_capacity` instead of `innodb_log_file_size`
- Monitor: checkpoint age < 75% of total redo capacity

### T4: Replication Lag Mitigation
- Enable multi-threaded applier: `replica_parallel_workers = 16`
- Use WRITESET dependency tracking: `binlog_transaction_dependency_tracking = WRITESET`
- Batch large DML: `LIMIT 10000` per transaction
- `binlog_row_image = MINIMAL` reduces event size
- Use `gh-ost` for schema changes to avoid DDL-caused lag

### T5: Buffer Pool Monitoring
- Hit ratio > 99%: `1 - (Innodb_buffer_pool_reads / Innodb_buffer_pool_read_requests)`
- `INNODB_BUFFER_PAGE` for per-table page counts
- Warm-up: `innodb_buffer_pool_dump_at_shutdown = ON` + `innodb_buffer_pool_load_at_startup = ON`

---

## 🗺️ Real-World Scenarios

### 01: Meta — MyRocks Alongside InnoDB
- InnoDB for latency-sensitive OLTP; MyRocks (RocksDB) for space-efficient replicas
- `gh-ost` for online schema changes across thousands of shards
- DDL-caused replication lag = primary operational challenge

### 02: Uber — PostgreSQL → MySQL Migration
- PostgreSQL write amplification: every update touched N index B-Trees
- InnoDB advantage: secondary indexes store only PK (non-indexed column update ≠ index update)
- InnoDB's undo-based MVCC avoids heap bloat

### 03: GitHub — ProxySQL Connection Multiplexing
- 2000 app connections → 100 MySQL backends via ProxySQL
- Undo log purge lag from analytics queries; fixed with MAX_EXECUTION_TIME and purge lag monitoring

### 04: Shopify — Vitess Horizontal Sharding
- 50M-row bulk DELETE caused 6-hour replication lag
- Fix: batch to 10K rows, MINIMAL binlog image, WRITESET parallelism

---

## 🗺️ Mistakes & Anti-Patterns

| # | Anti-Pattern | Detection | Fix |
|---|---|---|---|
| M01 | UUID as PK | High DATA_FREE, >100K page splits | AUTO_INCREMENT PK + UUID secondary |
| M02 | Ignoring history list | `trx_rseg_history_len > 100K` | Kill long txns, set purge lag limits |
| M03 | Wrong redo log size | Checkpoint age > 75% capacity | Size for 1 hour of peak writes |
| M04 | No covering indexes | EXPLAIN: no `Using index` | Composite index with all needed columns |
| M05 | Large single-txn DML | Replication lag, huge binlog events | Batch 10K rows per transaction |
| M06 | Disabled doublewrite | `innodb_doublewrite = OFF` | Verify atomic writes or re-enable |

---

## 🗺️ InnoDB vs PostgreSQL Quick Comparison

| Aspect | InnoDB | PostgreSQL |
|---|---|---|
| Storage model | Clustered B+ Tree | Heap + separate B-Trees |
| MVCC old versions | Undo log (separate) | In-heap (inline) |
| Cleanup | Purge thread (undo) | VACUUM (heap) |
| Secondary index stores | PK value | Physical TID |
| Page size | 16KB | 8KB |
| Connection model | Thread per connection | Process per connection |
| Torn page protection | Doublewrite buffer | Full-page images in WAL |
| Buffer pool recommendation | 70-80% RAM | 25% RAM (+ OS cache) |

---

## 🗺️ Assessment & Reflection
- Can you explain why the clustered index design makes PK selection critical?
- Do you understand the bookmark lookup and how covering indexes eliminate it?
- Can you trace an INSERT through buffer pool → redo log → commit → eventual data file flush?
- Can you diagnose replication lag and identify whether it's large transactions, DDL, or applier configuration?
- Do you know how InnoDB's MVCC differs from PostgreSQL and the operational implications?
