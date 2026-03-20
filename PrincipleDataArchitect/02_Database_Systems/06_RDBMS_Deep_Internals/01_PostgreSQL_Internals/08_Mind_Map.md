# 🧠 Mind Map – PostgreSQL Internals

---

## How to Use This Mind Map
- **For Revision**: Scan top-level headers to recall major subsystems; drill into bullets for mechanisms and numbers
- **For Application**: Use the Techniques section to identify which diagnostic query or tuning parameter applies to your current issue
- **For Interviews**: Trace the write path (SQL → Parser → Executor → WAL → Commit) from memory; know the MVCC visibility algorithm

---

## 🗺️ Theory & Concepts

### Process Architecture
- Multi-process, not multi-threaded (design decision from 1986)
  - Each client → dedicated forked OS process (~10MB RSS)
    - Crash isolation: one backend segfault ≠ server-wide crash
    - Trade-off: higher per-connection memory → need PgBouncer at >200 connections
  - Postmaster: supervisor daemon, listens on 5432, forks backends and background processes
  - Background processes: BgWriter, Checkpointer, WAL Writer, Autovacuum Launcher, Stats Collector, Archiver, WAL Sender

### Shared Memory
- Allocated at startup via `shmget()` / `mmap()`; all processes attach
  - **Shared Buffers**: 8KB page cache, ~25% of RAM, clock-sweep eviction (O(1) amortized)
    - Buffer Tag: `(RelFileNode, ForkNumber, BlockNumber)` → hash table → buffer ID
    - Usage count 0-5; sweep hand decrements; victim at 0
  - **WAL Buffers**: ring buffer for WAL records before disk flush (default 16MB)
  - **CLOG (pg_xact/)**: 2 bits per XID — in-progress / committed / aborted / sub-committed
  - **Lock Table**: heavyweight locks for DDL, row-level lock escalation
  - **Proc Array**: per-backend PGPROC structs; used for snapshot visibility checks

### MVCC
- Every row version has `xmin` (creator) and `xmax` (deleter/updater)
  - UPDATE = insert new version + set `xmax` on old version
  - Visibility check: evaluate xmin/xmax against transaction snapshot
    - Snapshot = (xmin_horizon, xmax_horizon, xip[] = in-progress XIDs)
  - Tuple header overhead: 23 bytes minimum (24 with alignment)
  - `t_ctid` → self-referencing if current; points to next version if updated (HOT chain)
- **Visibility Map**: 1 bit per heap page; enables index-only scans
- **Free Space Map**: tracks available space per page for INSERT placement

### WAL (Write-Ahead Log)
- Redo log guaranteeing crash recovery
  - Every modification → WAL record written BEFORE data page change
  - WAL record = XLogRecHdr (24B) + block references + data payload
  - LSN (Log Sequence Number): 64-bit pointer into WAL stream
    - Page header stores last-modifying LSN; recovery skips pages with LSN ≥ WAL record
  - Segment files: 16MB each, stored in `pg_wal/`
- `synchronous_commit = on` (default): fsync WAL to disk before acknowledging commit
- `synchronous_commit = off`: return immediately; WAL Writer flushes every 200ms (risk: up to 200ms data loss)

### TOAST
- The Oversized-Attribute Storage Technique
  - Values >2KB automatically compressed and/or stored out-of-line
  - Compression: default `pglz`, PostgreSQL 14+ supports `lz4`
  - Storage strategies: PLAIN, EXTENDED (compress+out-of-line), EXTERNAL (out-of-line only), MAIN (compress only)
  - Gotcha: updating ANY field in a TOASTed row rewrites the entire TOAST value

---

## 🗺️ Techniques & Patterns

### T1: Checkpoint Tuning
- When to use: periodic latency spikes every 5 minutes
- Mechanism:
  - Checkpointer writes all dirty pages to disk
  - Trigger: `checkpoint_timeout` (default 5min) OR `max_wal_size` exceeded
  - `checkpoint_completion_target = 0.9` → spread writes over 90% of interval
- Failure mode: `max_wal_size` too small → forced checkpoints every 30s → I/O storms

### T2: Autovacuum Tuning
- When to use: dead tuple ratio >10%, table bloat, approaching XID wraparound
- Threshold formula: `vacuum triggers at autovacuum_vacuum_threshold + scale_factor × n_live_tup`
  - Default: 50 + 0.2 × 100M = 20M dead tuples before vacuum on a 100M-row table
  - Fix: per-table override: `scale_factor = 0.01`, `threshold = 5000`
- Cost-based throttling: `autovacuum_vacuum_cost_delay = 2ms` (default 20ms) for faster cleanup
- Failure mode: disabled autovacuum → bloat → XID wraparound → forced shutdown

### T3: Connection Pooling with PgBouncer
- When to use: >100 concurrent connections
- Transaction mode: connections returned to pool between transactions
  - 10K app connections → 50-200 PostgreSQL backends
  - Caveat: prepared statements, SET commands, advisory locks don't persist across transactions
- Session mode: connections held for the session duration (less efficient but compatible)

### T4: Index-Only Scans via Visibility Map
- When to use: query only reads indexed columns
- Requires: visibility map up to date (VACUUM must have run since last modifications)
- Verification: `EXPLAIN (ANALYZE, BUFFERS)` → check "Heap Fetches: 0"
- Failure mode: stale visibility map → falls back to index scan with heap fetches

### T5: HOT Updates (Heap-Only Tuples)
- When to use: frequent updates to non-indexed columns
- Mechanism: new tuple version placed on same page, no index update needed
- Requirement: page must have free space → set `fillfactor = 80-90`
- Check: `pg_stat_user_tables.n_tup_hot_upd / n_tup_upd` → should be >80%
- Failure mode: page full or updated column is indexed → falls back to regular update

---

## 🗺️ Hands-On & Code

### Buffer Cache Inspection
- `CREATE EXTENSION pg_buffercache;`
- Query: top relations in cache, dirty ratio, hit/miss by table
- Signal: `blks_read` rate (blocks/sec) > cache hit ratio

### WAL Diagnostics
- `pg_current_wal_lsn()`, `pg_walfile_name()`, `pg_wal_lsn_diff()`
- `pg_walinspect` extension (PG15+): inspect WAL record types and sizes
- `pg_stat_bgwriter`: checkpoint counts, backend writes, sync times

### VACUUM Monitoring
- `pg_stat_user_tables`: n_dead_tup, last_autovacuum
- `pg_stat_progress_vacuum`: real-time phase, blocks scanned/vacuumed
- `pgstattuple` extension: precise dead tuple measurement

### EXPLAIN Analysis
- `EXPLAIN (ANALYZE, BUFFERS, TIMING, FORMAT TEXT)`
- Red flags: actual rows >> estimated rows, Buffers: shared read high, Sort Method: external merge Disk
- Index usage: Rows Removed by Filter > 0 → missing index predicate

---

## 🗺️ Real-World Scenarios

### 01: Instagram — XID Wraparound Near-Miss
- The Trap: long-running migration held transaction open for hours
- Scale: 2B+ users, thousands of PostgreSQL shards
- What Went Wrong: `age(datfrozenxid)` climbed past 1.5B; no alerting configured
- The Fix: monitoring at 500M/1B/1.5B thresholds, `idle_in_transaction_session_timeout = 5min`

### 02: Discord — Connection Exhaustion
- The Trap: thousands of microservices each opening direct PostgreSQL connections
- Scale: 200M+ monthly users, 10M+ concurrent WebSocket connections
- What Went Wrong: backend process count exceeded memory, connection overhead
- The Fix: PgBouncer transaction mode, `statement_timeout`, application-level backpressure

### 03: Notion — TOAST Bloat from JSONB Updates
- The Trap: every property change rewrites entire JSONB → TOAST value replaced each time
- Scale: 100M+ users, blocks stored as JSONB properties
- What Went Wrong: TOAST table grew 5x faster than main table
- The Fix: decomposed hot properties into separate columns, aggressive TOAST autovacuum

### 04: Shopify — Checkpoint Storms on Black Friday
- The Trap: `max_wal_size = 1GB` with 10GB/min write volume
- Scale: 2M+ merchants, millions of TPS aggregate
- What Went Wrong: checkpoints every 30s instead of 5min, P99 latency 5ms → 800ms
- The Fix: `max_wal_size = 16GB`, NVMe SSDs, `wal_compression = lz4`

---

## 🗺️ Mistakes & Anti-Patterns

### M01: Disabling Autovacuum
- Root Cause: misconception that VACUUM causes I/O; desire to "optimize"
- Diagnostic: `age(datfrozenxid)` > 800M, n_dead_tup growing unbounded
- Correction: re-enable + per-table tuning, add wraparound monitoring

### M02: VACUUM FULL as Routine Maintenance
- Root Cause: confusion between VACUUM (concurrent) and VACUUM FULL (exclusive lock)
- Diagnostic: AccessExclusiveLock held during maintenance windows
- Correction: use `pg_repack` for online table reorganization

### M03: Ignoring Connection Pooling
- Root Cause: process-per-connection model hidden from application developers
- Diagnostic: >200 PostgreSQL backends, 5GB+ process-level memory, contention on LWLocks
- Correction: PgBouncer in transaction mode, 10K client → 50-200 backends

### M04: Over-Indexing
- Root Cause: assumption that more indexes always improve reads
- Diagnostic: `pg_stat_user_indexes.idx_scan = 0` for multiple large indexes
- Correction: audit quarterly, drop unused, merge overlapping, use INCLUDE columns

### M05: Long-Running Transactions Blocking VACUUM
- Root Cause: application holds transactions open during slow batch processing
- Diagnostic: `pg_stat_activity` shows `idle in transaction` for >5 minutes
- Correction: `idle_in_transaction_session_timeout`, server-side cursors, batch commit patterns

### M06: Wrong random_page_cost on SSDs
- Root Cause: default 4.0 tuned for spinning disks; never changed after SSD migration
- Diagnostic: planner chooses Seq Scan over Index Scan on selective queries
- Correction: `random_page_cost = 1.1`, `effective_io_concurrency = 200`

---

## 🗺️ Interview Angle

### Write Path Question
- Expected: trace SQL → Parser → Rewriter → Planner → Executor → Buffer Manager → XLogInsert → XLogFlush → CommitAck
- Key insight: WAL is fsynced BEFORE commit acknowledged; data files written lazily

### MVCC Deep Dive
- Expected: explain tuple headers (xmin, xmax, ctid, infomask), visibility algorithm, snapshot isolation
- Follow-up: per-row overhead (23-24 bytes), why VACUUM is necessary

### Checkpoint / Latency Spikes
- Expected: diagnose via `pg_stat_bgwriter`, distinguish checkpoints_req vs timed
- Key fix: `max_wal_size` increase, `checkpoint_completion_target = 0.9`

### Whiteboard
- Draw: SQL → Parser → Executor → Buffer Manager ↔ Shared Buffers → WAL Insert → WAL Flush → Commit
- Annotate: BgWriter/Checkpointer handle lazy data file writes; WAL is the durability guarantee

---

## 🗺️ Assessment & Reflection
- Can you trace an INSERT from network receipt to commit acknowledgment?
- Do you know the per-row MVCC overhead and the visibility check algorithm?
- Can you explain why VACUUM exists and what happens without it?
- Can you diagnose checkpoint storms using `pg_stat_bgwriter`?
- Do you understand why PgBouncer is necessary and which pool mode to choose?
- Can you draw the PostgreSQL write path on a whiteboard in 5 minutes?
