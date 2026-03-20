# 🧠 Mind Map – SQL Server Internals

---

## 🗺️ Theory & Concepts

### Three Storage Engines
- **Row Store** (traditional): B-tree, lock-based, 8KB pages
- **Column Store**: columnar segments, batch mode, 10x compression
- **Hekaton** (In-Memory OLTP): latch-free, optimistic MVCC, natively compiled procs

### Storage: Pages, Extents, Filegroups
- **Page** (8KB): header (96 bytes) + row data (grows down) + row offset array (grows up)
  - Page types: Data (1), Index (2), Text/Image (3), IAM (10), PFS, GAM, SGAM
  - `m_lsn`: last modification LSN; `m_slotCnt`: row count
- **Extent** (64KB = 8 pages): mixed (shared) or uniform (single object)
- **Filegroup**: logical container for data files; Primary (.mdf), Secondary (.ndf)
- **Allocation tracking**: GAM (extent-level), SGAM (mixed extents), PFS (page-level fullness), IAM (per-object)
  - PFS contention on tempdb → mitigated by multiple tempdb files

### Buffer Pool
- In-memory cache of 8KB data pages
- Eviction: LRU-K (K=2) — track 2 most recent references, evict oldest second reference
- Dirty pages: modified in memory, not yet flushed to disk
- Checkpoint: flushes dirty pages; indirect checkpoint (2016+ default) targets ~60s recovery
- Lazy Writer: frees pages when memory pressure detected
- **Buffer Pool Extension** (2014+): SSD cache for clean pages only
- Key metrics: Buffer Cache Hit Ratio (>99%), Page Life Expectancy (>300s)

### Transaction Log
- Physical: `.ldf` file; internally divided into **VLFs** (Virtual Log Files)
- VLF count: too many (>1000) = slow recovery; too few = can't truncate
- **LSN** (Log Sequence Number): VLF_sequence:block_offset:slot — strict ordering
- WAL: log record must be flushed before dirty data page can be written
- **Group commit**: batches multiple concurrent commit flushes into one I/O
- Log truncation: after backup (full/bulk-logged) or at checkpoint (simple recovery)
- Blocked truncation: ACTIVE_TRANSACTION, LOG_BACKUP, REPLICATION

### Concurrency Control
- **Default** (pessimistic): S locks for reads, X locks for writes
  - Readers block writers, writers block readers
  - Lock hierarchy: Row → Page → Table (with intent locks)
  - Lock escalation: >5000 row locks → table lock
- **RCSI** (optimistic reads): version store in tempdb
  - Statement-level consistency; reads never acquire S locks
  - Writers still use X locks (write-write still blocks)
- **Snapshot Isolation**: transaction-level consistency; update conflict detection (error 3960)
- **Hekaton MVCC**: completely latch-free; timestamp-ordered versions; validation at commit

### Clustered vs Non-Clustered Indexes
- **Clustered**: B-tree where leaf = data rows (like InnoDB); only 1 per table
  - No clustered index → heap (RID-based access)
- **Non-Clustered**: separate B-tree; leaf = indexed columns + row locator
  - Row locator = clustering key (if clustered exists) or RID (heap)
  - **Key lookup**: NC index seek → get clustering key → CI seek (extra I/O)
  - **Covering index**: INCLUDE columns to avoid key lookups

### Columnstore
- Column-by-column storage in compressed **rowgroups** (~1M rows each)
- Column **segments**: independently compressed (dictionary, run-length, bit-packing)
- **Delta store**: B-tree staging for recent inserts; tuple mover compresses periodically
- **Batch mode**: process ~900 rows/CPU cycle (vs row mode: 1 row/cycle)
- **Segment elimination**: min/max metadata skips irrelevant rowgroups
- **Ordered CCI** (2022+): pre-sorted for range queries

### Hekaton (In-Memory OLTP)
- Tables in memory as linked lists (no pages)
- Hash indexes (Cuckoo hashing) + range indexes (Bw-tree)
- Row versions: BeginTs, EndTs, payload
- Natively compiled procs: T-SQL → C → DLL
- Durability: SCHEMA_AND_DATA (checkpoint files) or SCHEMA_ONLY (volatile)

### Query Store
- Captures every plan for every query with runtime stats
- Enables: plan regression detection, forced plans, automatic tuning
- `FORCE_LAST_GOOD_PLAN`: auto-revert on regression (2017+)
- Wait stats per query (2017+), tempdb usage (2022+)

### Recovery
- ARIES-based: Analysis → Redo → Undo
- **ADR** (Accelerated Database Recovery, 2019+):
  - Persistent Version Store (PVS) in user database
  - Instant rollback (mark versions as aborted)
  - Seconds for undo phase regardless of transaction duration

---

## 🗺️ Techniques & Patterns

### T1: RCSI Deployment
- When: any OLTP workload with reader-writer concurrency
- `ALTER DATABASE MyDB SET READ_COMMITTED_SNAPSHOT ON;`
- Monitor tempdb version store after enabling

### T2: Wait Stats Diagnosis
- `sys.dm_os_wait_stats`: cumulative waits  
- Filter benign waits; top remaining = bottleneck
- PAGEIOLATCH = disk; WRITELOG = log I/O; LCK_M = locking; PAGELATCH = tempdb

### T3: Parameter Sniffing Management
- Detect: Query Store variance ratio > 100x
- Fix: OPTIMIZE FOR UNKNOWN → forced plan → RECOMPILE → auto-tuning

### T4: tempdb Configuration
- Multiple equal-sized files: MIN(8, CPU cores)
- Fixed MB growth (not percentage)
- Memory-optimized tempdb metadata (2019+)

### T5: Columnstore for HTAP
- Non-clustered columnstore on rowstore table
- Batch mode for analytics; row mode for OLTP
- RCSI for non-blocking concurrent access

---

## 🗺️ Real-World Scenarios

### 01: Stack Overflow — RCSI + Columnstore HTAP
- RCSI eliminated reader-writer blocking
- Non-clustered columnstore for analytics on Votes table → 50x speedup

### 02: E-Commerce — tempdb PFS Contention
- Single tempdb file → PAGELATCH waits at Black Friday peak
- Fix: 8 equal-sized files → P50 from 200ms to 8ms

### 03: Financial — Parameter Sniffing
- Cached Nested Loops plan optimal for 10 rows, catastrophic for 500K
- Fix: Query Store + OPTIMIZE FOR UNKNOWN + auto-tuning

### 04: Healthcare — VLF Fragmentation
- 42,000 VLFs from default autogrowth → 4-hour recovery
- Fix: shrink/regrow to 36 VLFs → 45-second recovery

---

## 🗺️ Mistakes & Anti-Patterns

| # | Anti-Pattern | Detection | Fix |
|---|---|---|---|
| M01 | No RCSI enabled | LCK_M_S waits; blocked sessions | ALTER DATABASE SET RCSI ON |
| M02 | Parameter sniffing ignored | Query Store variance > 100x | OPTIMIZE FOR UNKNOWN; auto-tuning |
| M03 | tempdb misconfigured | PAGELATCH waits on DB 2 | Multiple equal-sized files |
| M04 | Heap tables (no CI) | Forwarding pointers; RID lookups | Create clustered index |
| M05 | Index over-creation | Unused indexes with high writes | Drop unused; consolidate |
| M06 | Ignoring wait stats | Blind tuning | Paul Randal's methodology |

---

## 🗺️ Cross-RDBMS Comparison

| Dimension | SQL Server | PostgreSQL | MySQL InnoDB | Oracle |
|---|---|---|---|---|
| MVCC approach | Lock-based + optional RCSI/SI | Heap-based (always) | Undo-based (always) | Undo-based (always) |
| Columnar | Built-in columnstore | Extensions only | None | In-Memory Column Store |
| In-memory OLTP | Hekaton (latch-free) | None | None | TimesTen (separate) |
| Plan management | Query Store (built-in) | pg_stat_statements | Performance Schema | AWR + SQL Plan Baselines |
| Recovery innovation | ADR (instant rollback) | Standard REDO | Crash recovery redo | Standard REDO |

---

## 🗺️ Assessment & Reflection
- Can you explain why RCSI eliminates reader-writer blocking but not write-write blocking?
- Do you understand when columnstore batch mode activates vs row mode?
- Can you diagnose parameter sniffing using Query Store and choose the right fix?
- Can you explain the VLF lifecycle and why too many VLFs slow recovery?
- Can you design an HTAP solution using non-clustered columnstore + RCSI?
