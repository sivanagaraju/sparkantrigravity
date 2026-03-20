# SQL Server Internals — How It Works

## Storage Architecture: Pages, Extents, and Filegroups

### The 8KB Page

The page is SQL Server's fundamental unit of I/O and storage. Every read and write operates on 8KB pages.

```
┌─────────────────────────────────────────────────┐
│              8KB Page (8192 bytes)               │
├─────────────────────────────────────────────────┤
│  Page Header (96 bytes)                          │
│  ┌──────────────────────────────────────────┐   │
│  │ PageID      : (FileID:PageNum)            │   │
│  │ PageType    : 1=Data, 2=Index, 10=IAM ... │   │
│  │ m_slotCnt   : Number of rows on page      │   │
│  │ m_freeData  : Offset to free space start  │   │
│  │ m_freeCnt   : Free bytes on page           │   │
│  │ m_lsn       : Last log record that         │   │
│  │               modified this page           │   │
│  │ m_tornBits  : Torn page detection bits     │   │
│  └──────────────────────────────────────────┘   │
├─────────────────────────────────────────────────┤
│  Row Data Area (grows downward from top)         │
│  ┌──────────────────────────────────────────┐   │
│  │ Row 0: [Status bits | Fixed cols | Var     │   │
│  │         col offset | Null bitmap | Var     │   │
│  │         length array | Variable cols]      │   │
│  │ Row 1: ...                                  │   │
│  │ Row 2: ...                                  │   │
│  └──────────────────────────────────────────┘   │
│                    Free Space                    │
├─────────────────────────────────────────────────┤
│  Row Offset Array (grows upward from bottom)    │
│  [Slot 0 offset | Slot 1 offset | ...]          │
│  (2 bytes per slot, sorted by slot number)       │
└─────────────────────────────────────────────────┘
```

### Row Format

Each row contains:
- **Status bits** (2 bytes): row type, null bitmap flag, variable-length columns flag
- **Fixed-length columns**: stored contiguously in column definition order
- **Number of columns** (2 bytes): total column count
- **Null bitmap**: 1 bit per column (1 = NULL)
- **Variable-length column count** (2 bytes)
- **Variable-length column offset array**: 2 bytes per variable column
- **Variable-length data**: stored after the offset array

**Key insight**: Unlike PostgreSQL, SQL Server rows do not carry xmin/xmax transaction IDs. Versioning happens in tempdb (RCSI) or in-row (Hekaton), not in the heap.

### Extents

Pages are grouped into **extents** of 8 contiguous pages (64KB):
- **Uniform extent**: All 8 pages belong to one object (table or index)
- **Mixed extent**: Pages from different objects share the extent (used for small tables < 8 pages)

SQL Server automatically promotes from mixed to uniform extents as objects grow.

### Allocation Pages

SQL Server uses special pages to track space allocation:

| Page Type | Purpose | Scope |
|---|---|---|
| **GAM** (Global Allocation Map) | Tracks which extents are allocated | 1 bit per extent; covers ~64,000 extents (4GB) |
| **SGAM** (Shared GAM) | Tracks mixed extents with free pages | Same scope as GAM |
| **PFS** (Page Free Space) | Tracks per-page fullness (1 byte per page) | Covers 8,088 pages (~64MB) |
| **IAM** (Index Allocation Map) | Maps extents belonging to one object | 1 bit per extent; links all extents for a heap/index |

**PFS contention** (especially on tempdb) is a known bottleneck at high concurrency — SQL Server 2019+ adds multiple PFS pages to mitigate.

---

## Buffer Pool

The Buffer Pool is SQL Server's data page cache — it is the single largest consumer of SQL Server's memory.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Buffer Pool                       │
│  ┌───────────────────────────────────────────────┐   │
│  │ Clean pages (read from disk, unmodified)       │   │
│  ├───────────────────────────────────────────────┤   │
│  │ Dirty pages (modified, not yet flushed)        │   │
│  ├───────────────────────────────────────────────┤   │
│  │ Free pages (available for new reads)          │   │
│  └───────────────────────────────────────────────┘   │
│                                                      │
│  Eviction: LRU-K (K=2)                              │
│  → Track 2 most recent references per page           │
│  → Evict page with oldest second reference           │
│  → Better than simple LRU for scan resistance        │
│                                                      │
│  Checkpoint:                                         │
│  → Periodically flush dirty pages to disk            │
│  → Recovery interval determines frequency             │
│  → Indirect checkpoint (default in 2016+):            │
│     targets ~60 second recovery time                  │
└─────────────────────────────────────────────────────┘
```

### Buffer Pool Extension (BPE)
SQL Server 2014+ can extend the buffer pool to SSD storage for clean pages. Acts as a secondary cache between the in-memory buffer pool and spinning disk. **Only clean pages** are stored in BPE — dirty pages remain in RAM.

### Key Metrics

```sql
-- Buffer cache hit ratio (should be > 99% for OLTP)
SELECT 
    (a.cntr_value * 1.0 / b.cntr_value) * 100 AS buffer_cache_hit_ratio
FROM sys.dm_os_performance_counters a
CROSS JOIN sys.dm_os_performance_counters b
WHERE a.counter_name = 'Buffer cache hit ratio'
  AND b.counter_name = 'Buffer cache hit ratio base'
  AND a.object_name = b.object_name;

-- Page Life Expectancy (target: > 300 seconds for OLTP)
SELECT cntr_value AS page_life_expectancy_seconds
FROM sys.dm_os_performance_counters
WHERE counter_name = 'Page life expectancy'
  AND object_name LIKE '%Buffer Manager%';
```

---

## Transaction Log Architecture

### Virtual Log Files (VLFs)

The physical `.ldf` file is internally divided into **Virtual Log Files (VLFs)**. VLFs are the unit of log management — truncation, backup, and recovery operate at the VLF level.

```
┌─────────────────────────────────────────────────────────────┐
│                     Transaction Log (.ldf)                   │
│                                                              │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐         │
│  │VLF 1│ │VLF 2│ │VLF 3│ │VLF 4│ │VLF 5│ │VLF 6│         │
│  │(inac)│ │(inac)│ │ACTIVE│ │ACTIVE│ │(free)│ │(free)│       │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘          │
│                    ↑                                         │
│              MinLSN (oldest active transaction)              │
│                                                              │
│  → Log wraps around: when VLF 6 is full, reuse VLF 1       │
│    (if VLF 1 is inactive = backed up or truncated)           │
│  → Too many VLFs (> 1000) = slow recovery + startup         │
└─────────────────────────────────────────────────────────────┘
```

### Log Sequence Number (LSN)

Every log record has a unique **LSN** = `VLF_sequence : log_block_offset : slot_number`. LSNs are strictly monotonically increasing. The LSN is stored in:
- The log record itself
- The page header (`m_lsn`) — last LSN that modified the page
- Backup headers — for point-in-time recovery

### Write-Ahead Logging (WAL)

The WAL protocol in SQL Server:
1. Modification generates a log record in the **log buffer** (in-memory)
2. Before the modified data page can be written to disk, the log record **must be flushed first**
3. On `COMMIT`: log buffer is flushed to the `.ldf` file (`WRITELOG` wait)
4. Dirty data pages are written to `.mdf`/`.ndf` lazily by **checkpoint** or **lazy writer**

**Group commit**: SQL Server batches multiple concurrent commit flushes into one I/O operation — amortizing the fsync cost across transactions.

---

## Concurrency Control

### Default: Lock-Based (Pessimistic)

SQL Server's default `READ COMMITTED` uses shared locks for reads:

```
Transaction A: SELECT * FROM orders WHERE id = 42;
  → Acquires Shared (S) lock on row
  → Releases S lock after reading (not at commit!)

Transaction B: UPDATE orders SET status = 'shipped' WHERE id = 42;
  → Requests Exclusive (X) lock on row
  → S and X are incompatible → B WAITS until A's S lock is released
```

**Lock hierarchy**: Row → Page → Table (with intent locks at each level). Lock escalation automatically promotes many row locks to a table lock when > 5,000 locks are held on one object.

### RCSI: Read Committed Snapshot Isolation (Optimistic Reads)

When RCSI is enabled:
```sql
ALTER DATABASE MyDB SET READ_COMMITTED_SNAPSHOT ON;
```

Read behavior changes fundamentally:
- **Reads no longer acquire shared locks**
- Instead, reads access the **version store in tempdb**
- Each statement sees a snapshot of data as of the statement's start time
- Writers still acquire exclusive locks (write-write conflicts still block)

```
Transaction A: UPDATE orders SET status = 'shipped' WHERE id = 42;
  → Copies old version to tempdb version store
  → Writes new data in-place
  → Holds X lock until commit

Transaction B: SELECT * FROM orders WHERE id = 42;
  → No S lock needed!
  → Reads from version store (sees pre-UPDATE value)
  → Never blocked by Transaction A
```

**Impact**: Dramatically reduces blocking. Trade-off: tempdb I/O for the version store.

### Snapshot Isolation (Transaction-Level)

```sql
SET TRANSACTION ISOLATION LEVEL SNAPSHOT;
BEGIN TRAN;
  SELECT * FROM orders; -- sees snapshot as of BEGIN TRAN
  -- even if other transactions commit between begin and here
COMMIT;
```

**Difference from RCSI**: RCSI gives statement-level consistency; Snapshot gives transaction-level consistency. Snapshot also detects **update conflicts**: if two snapshot transactions modify the same row, the second to commit gets error 3960.

---

## Clustered vs Non-Clustered Indexes

### Clustered Index (Data = Index)

Like InnoDB, a clustered index **IS** the table. The leaf level of the B-tree contains the actual data rows, ordered by the clustering key.

```
                    Root Page
                   /    |    \
              Internal  Internal  Internal
             /   |   \ 
        Leaf(1-100)  Leaf(101-200)  Leaf(201-300)
        ┌──────────────────────────┐
        │ Data rows ordered by      │
        │ clustering key (e.g. ID)  │
        └──────────────────────────┘
```

- Only **one** clustered index per table
- If no clustered index exists, the table is a **heap** (unordered pages)
- Default: PRIMARY KEY creates a clustered index (unlike PostgreSQL)

### Non-Clustered Index

Separate B-tree where leaf nodes contain:
- The indexed column values
- A **row locator**: either the clustering key (if clustered index exists) or the RID (file:page:slot) for heaps

**Implication**: Non-clustered index lookups on clustered tables require a **key lookup** — navigate the non-clustered index, get the clustering key, then navigate the clustered index to fetch the full row. This is called a **bookmark lookup**.

### Covering Index

```sql
-- Non-clustered index that covers the query (no key lookup needed)
CREATE NONCLUSTERED INDEX IX_Orders_Status
ON orders (status)
INCLUDE (customer_id, total_amount);
-- Query: SELECT customer_id, total_amount FROM orders WHERE status = 'pending';
-- → Index-only scan, no key lookup to clustered index
```

---

## Columnstore Indexes

### Architecture

```
┌───────────────────────────────────────────────────┐
│             Columnstore Index                      │
│                                                    │
│  Rowgroup 1 (~1M rows)                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Col A Seg │ │ Col B Seg │ │ Col C Seg │         │
│  │ compressed│ │ compressed│ │ compressed│         │
│  │ (run-len, │ │ (dict,    │ │ (bit-pack)│         │
│  │  dict)    │ │  value)   │ │           │         │
│  └──────────┘ └──────────┘ └──────────┘          │
│                                                    │
│  Rowgroup 2 (~1M rows)                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Col A Seg │ │ Col B Seg │ │ Col C Seg │         │
│  └──────────┘ └──────────┘ └──────────┘          │
│                                                    │
│  Delta Store (B-tree for recent inserts)           │
│  ┌──────────────────────────────────────┐         │
│  │ Recent rows not yet compressed        │         │
│  │ Tuple Mover compresses when ~1M rows  │         │
│  └──────────────────────────────────────┘         │
└───────────────────────────────────────────────────┘
```

### Batch Mode Execution

Traditional row mode: processes 1 row at a time through each operator.
Batch mode: processes ~900 rows at a time as a **column vector** through each operator.

- CPU-efficient: SIMD-like processing, better cache utilization
- Available for columnstore queries (and some rowstore queries in SQL Server 2019+)
- 10-100x performance improvement for scan-heavy analytical queries

### Segment Elimination

Each column segment stores **min/max metadata**. The query engine skips entire rowgroups whose min/max range doesn't match the predicate — similar to PostgreSQL's BRIN indexes but built into the columnstore.

---

## Hekaton (In-Memory OLTP)

### Architecture

```
┌────────────────────────────────────────────────────┐
│              Hekaton Engine                          │
│                                                     │
│  Memory-Optimized Tables                            │
│  ┌──────────────────────────────────────────────┐  │
│  │ Rows stored as linked lists (no pages!)      │  │
│  │ Each row version has:                         │  │
│  │   Begin timestamp | End timestamp | Payload  │  │
│  │                                               │  │
│  │ Hash indexes: lock-free Cuckoo hashing       │  │
│  │ Range indexes: lock-free Bw-tree (B-tree     │  │
│  │   variant with delta updates)                 │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  Natively Compiled Stored Procedures                │
│  ┌──────────────────────────────────────────────┐  │
│  │ T-SQL → C code → DLL (machine code)          │  │
│  │ No interpreter overhead                       │  │
│  │ Eliminates latch/lock acquisition             │  │
│  │ 10-50x faster for high-frequency TX           │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  Durability Options                                 │
│  ┌──────────────────────────────────────────────┐  │
│  │ SCHEMA_AND_DATA: full durability (default)   │  │
│  │   → checkpoint files: data + delta files     │  │
│  │ SCHEMA_ONLY: no durability (session cache)   │  │
│  │   → data lost on restart, schema preserved   │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

### MVCC in Hekaton

Hekaton uses **timestamp-ordered optimistic MVCC**:
- Each row version has `BeginTs` and `EndTs` (logical timestamps, not physical clocks)
- A transaction at timestamp T sees rows where `BeginTs ≤ T < EndTs`
- **No locks, no latches**: validation happens at commit time
- If two transactions modify the same row, the first to commit wins; the second gets a write-write conflict and must retry

### When to Use Hekaton

| Use Case | Hekaton Benefit |
|---|---|
| Session state / caching | SCHEMA_ONLY = no I/O overhead |
| High-frequency OLTP (> 100K TPS) | Latch-free = no contention at scale |
| Queue tables (high insert/delete churn) | Eliminates page latch contention |
| Lookup tables (millions of reads/sec) | Hash index = O(1) point lookups |

---

## Query Store

### How It Works

```
┌───────────────────────────────────────────────┐
│              Query Store                       │
│                                                │
│  Query text → Query hash                       │
│                ↓                               │
│  Plan compilation → Plan hash                  │
│                ↓                               │
│  Execution → Runtime stats captured:           │
│    duration, CPU, reads, writes, rows,         │
│    wait stats (2017+), tempdb usage (2022+)    │
│                                                │
│  Stored in:                                    │
│    sys.query_store_query                        │
│    sys.query_store_plan                         │
│    sys.query_store_runtime_stats               │
│                                                │
│  Actions:                                      │
│    → Force specific plan for a query           │
│    → Detect regressions (plan change → perf ↓) │
│    → Automatic tuning (2017+): auto-force      │
│      last known good plan on regression        │
└───────────────────────────────────────────────┘
```

### Plan Forcing

```sql
-- Force a specific plan for a query
EXEC sp_query_store_force_plan @query_id = 42, @plan_id = 7;

-- Auto-force last known good plan on regression
ALTER DATABASE MyDB SET AUTOMATIC_TUNING (FORCE_LAST_GOOD_PLAN = ON);
```

No other RDBMS offers this level of built-in plan regression management. PostgreSQL has `pg_hint_plan` (third-party extension) and Oracle has SQL Plan Baselines, but neither match Query Store's automatic detection + forcing capability.

---

## Recovery Process

### Crash Recovery (ARIES-Based)

SQL Server uses a variant of the **ARIES** (Analysis, Redo, Undo) algorithm:

1. **Analysis**: Scan the log from the last checkpoint to determine:
   - Which transactions were active at crash time  
   - Which pages need redo (dirty page tracking)

2. **Redo**: Replay all logged operations from the oldest dirty page LSN forward. This restores all committed AND uncommitted changes.

3. **Undo**: Roll back all uncommitted transactions by reading their log records in reverse order and applying compensating actions.

### Accelerated Database Recovery (ADR) — SQL Server 2019+

Traditional recovery: undo phase can take hours for long-running transactions.

ADR maintains a **Persistent Version Store (PVS)** that stores old row versions in the user database (not tempdb). This allows:
- **Instant rollback**: instead of undoing via the log, mark row versions as aborted
- **Aggressive log truncation**: log space is independent of transaction length
- **Fast recovery**: undo phase takes seconds regardless of transaction duration

This is a fundamental architectural improvement — similar in spirit to Oracle's always-available undo.
