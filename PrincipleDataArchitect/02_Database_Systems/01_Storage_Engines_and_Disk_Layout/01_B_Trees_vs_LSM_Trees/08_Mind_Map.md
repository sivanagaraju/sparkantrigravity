# 🧠 Mind Map – B-Trees vs LSM-Trees

---

## How to Use This Mind Map

- **For Revision**: Scan the Theory section before any database internals interview
- **For Application**: Use the decision heuristic (write:read ratio) when choosing a storage engine
- **For Interviews**: Practice the whiteboard exercise — draw both structures side by side in 5 minutes
- **For Debugging**: Reference the Mistakes section when diagnosing production latency issues

---

## 🗺️ Theory & Concepts

### B-Tree (Balanced Tree)

- Invented by Bayer & McCreight (1970) at Boeing
- Sorted key-value store organized in fixed-size pages (8KB PostgreSQL, 16KB InnoDB)
  - Internal pages: keys + pointers to child pages
  - Leaf pages: keys + values (or pointers to heap in PostgreSQL)
    - Leaf pages linked together for efficient range scans
- Write path: find the correct leaf page → update in-place → WAL for durability
  - Random I/O: target page can be anywhere on disk
  - Page splits when a leaf is full → update parent → cascading if parent is also full
- Read path: root → internal → leaf → typically 3-4 page reads for 1B rows
  - O(log_B n) where B = branching factor (~500 for 8KB pages)
  - Excellent read amplification: 1 read per query
- Used by: PostgreSQL, MySQL InnoDB, Oracle, SQL Server, SQLite

### LSM-Tree (Log-Structured Merge Tree)

- Proposed by O'Neil et al. (1996)
- Append-only: writes go to in-memory memtable (sorted), then flush to immutable SSTables on disk
  - WAL written first for durability (sequential I/O)
  - Memtable implemented as skip list or red-black tree
    - Size: typically 64-256MB before flush
- SSTables organized in levels (L0 → L1 → L2 → ...)
  - L0: recent flushes, may overlap
  - L1+: non-overlapping key ranges (after leveled compaction)
- Read path: check memtable → L0 SSTables → L1 → L2 → ...
  - Bloom filters reduce unnecessary SSTable reads
    - 10 bits/key → 1% false positive rate
    - 15 bits/key → 0.02% false positive rate
  - Without Bloom filter: read amplification = number of levels
- Used by: RocksDB, Cassandra, HBase, LevelDB, ScyllaDB, Pebble

### Three Amplification Factors

- **Read Amplification**: how many locations must be checked per read
  - B-Tree: 1 (single path root→leaf)
  - LSM: 1-N (depends on levels and Bloom filter effectiveness)
- **Write Amplification**: how many times data is physically written to disk
  - B-Tree: ~2x (data page + WAL)
  - LSM: 10-30x (memtable → L0 → L1 → L2 → L3... each level rewrites)
    - Critical for SSD lifespan: 100GB data × 20x = 2TB/day actual disk writes
- **Space Amplification**: extra disk used beyond logical data size
  - B-Tree: ~1x (dead tuples in PostgreSQL increase this without VACUUM)
  - LSM: 1.1-2x (old versions persist until compaction merges them)

---

## 🗺️ Techniques & Patterns

### T1: Choosing B-Tree vs LSM Based on Write:Read Ratio

- Write:Read < 2:1 → B-Tree (PostgreSQL, MySQL)
  - Random I/O acceptable at moderate write rates
  - Superior read performance (1 page per query)
- Write:Read > 5:1 → LSM (RocksDB, Cassandra, ClickHouse)
  - Sequential writes essential for sustained throughput
  - Accept read amplification trade-off
- Write:Read 2:1 to 5:1 → Benchmark both
  - WiredTiger (MongoDB) offers hybrid characteristics
- Failure mode: using B-Tree for IoT ingestion → throughput degrades 5-7x at 100M rows

### T2: Tuning Bloom Filters for LSM Read Performance

- When to use: read-heavy workloads on LSM engines
- Mechanism: probabilistic membership test per SSTable
  - "Definitely NOT here" (skip) or "Probably here" (read)
  - False negatives: IMPOSSIBLE
- Step by step:
  - 1. Set bits per key (10 = default, 15 = read-heavy workloads)
  - 1. Monitor `rocksdb.bloom.filter.useful` vs `full.positive`
  - 1. Increase bits if false positive rate exceeds target
- Failure mode: default 10 bits → 1% unnecessary SSTable reads → latency tail at p99

### T3: Write Amplification Budgeting

- When to use: capacity planning for LSM-based databases
- Formula: Daily disk writes = Logical write rate × Write amplification factor
  - Example: 100GB/day logical × 20x WA = 2TB/day physical
- SSD lifespan: Total Bytes Written (TBW) / Daily writes = Days until failure
  - Consumer SSD (150 TBW) at 2TB/day = 75 days
  - Enterprise SSD (3 DWPD × 1TB × 365 days ≈ 1095 TBW) at 2TB/day = 548 days
- Failure mode: capacity planning ignoring WA → quarterly SSD replacements

---

## 🗺️ Hands-On & Code

### PostgreSQL B-Tree Inspection

- `EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM t WHERE id = 42;`
  - Look for: `Buffers: shared hit=4` (4 B-Tree pages traversed)
- `SELECT * FROM pg_stat_user_tables WHERE relname = 'my_table';`
  - Monitor: `n_dead_tup` / `n_live_tup` ratio for bloat detection

### RocksDB LSM Benchmarking

- `db_bench --benchmarks=fillrandom --num=1000000` → measure write ops/sec
- `db_bench --benchmarks=readrandom --num=1000000` → measure read ops/sec
- Expected: writes 3-10x faster than reads on LSM

### Key Configuration

- PostgreSQL: `shared_buffers`, `effective_cache_size`, `autovacuum_vacuum_scale_factor`
- RocksDB: `write_buffer_size` (memtable), `max_background_compactions`, `bloom_bits_per_key`

---

## 🗺️ Real-World Scenarios

### 01: Facebook — RocksDB Replacing InnoDB

- The Trap: 500K writes/sec on B-Tree (InnoDB) → random I/O saturates SSDs
- Scale: 300TB messages database, 5:1 write:read ratio
- The Fix: Built RocksDB (LSM) → 10x write throughput, 5x longer SSD lifespan
  - Trade-off: reads went from 1 to 2-3 disk reads (Bloom filters keep 99% at 1)

### 02: Percona — SSD Burnout from LSM Write Amplification

- The Trap: 100GB Cassandra with STCS → 3TB/day disk writes (30x WA)
- Scale: SSDs dying every 3.3 months instead of expected 5 years
- The Fix: STCS → LCS compaction reduced WA from 30x to 10x

### 03: LinkedIn — PostgreSQL B-Tree Index Bloat

- The Trap: Long-running queries holding snapshots → 60% dead tuples in index
- Scale: 500M row table, latency 5ms → 25ms during peak
- The Fix: Aggressive autovacuum (scale_factor 0.01), analytical queries moved to replica

---

## 🗺️ Mistakes & Anti-Patterns

### M01: B-Tree for Write-Heavy IoT

- Root Cause: assuming any RDBMS works for all workloads
- Diagnostic: INSERT throughput degrades 5-7x as table grows past 100M rows
- Correction: LSM engine (RocksDB, ClickHouse) or TimescaleDB hypertables

### M02: LSM for Read-Heavy User Profiles

- Root Cause: Cassandra/DynamoDB chosen for scalability without considering access pattern
- Diagnostic: `rocksdb.read.amp > 3` or Cassandra read latency p99 growing
- Correction: PostgreSQL/MySQL B-Tree for read-dominant workloads

### M03: Ignoring Write Amplification in SSD Cost Models

- Root Cause: capacity planning based on logical data size only
- Diagnostic: SSD SMART data shows TBW approaching rated limit prematurely
- Correction: multiply logical writes by 10-30x for LSM; use enterprise SSDs (3 DWPD)

### M04: Not Tuning Bloom Filters

- Root Cause: using RocksDB defaults for a read-heavy workload
- Diagnostic: `bloom.filter.full.positive` count high relative to useful
- Correction: increase from 10 to 15 bits/key → FPR drops from 1% to 0.02%

### M05: Running Compaction During Peak Hours

- Root Cause: no compaction scheduling or rate limiting
- Diagnostic: latency spikes correlate with compaction activity
- Correction: rate-limit compaction I/O or schedule during off-peak

---

## 🗺️ Interview Angle

### Foundational Question

- "Explain B-Trees vs LSM-Trees"
- Key axes: in-place vs append-only, random vs sequential I/O, three amplification factors
- Draw both write paths on whiteboard

### Diagnostic Question

- "Write performance degrades over time — what's happening?"
- B-Tree: dead tuple bloat (VACUUM), index fragmentation
- LSM: L0 file accumulation (compaction backlog), write stall

### Design Question

- "Design storage for 1M events/sec"
- Answer: LSM. 200MB/sec sequential vs 200K random IOPS. 2 NVMe SSDs vs 20.

### Depth Check

- "What is write amplification?"
- Must include: ratio definition, concrete numbers (10-30x), SSD impact, cost implications

---

## 🗺️ Assessment & Reflection

- Can you draw both B-Tree and LSM-Tree write paths from memory?
- Can you calculate SSD lifespan given write amplification?
- Do you know which storage engine underlies your production databases?
- Have you checked `n_dead_tup` on your PostgreSQL tables recently?
- Can you articulate when PostgreSQL (B-Tree) is better than Cassandra (LSM)?
- Have you verified Bloom filter configuration on any LSM-based systems you operate?
