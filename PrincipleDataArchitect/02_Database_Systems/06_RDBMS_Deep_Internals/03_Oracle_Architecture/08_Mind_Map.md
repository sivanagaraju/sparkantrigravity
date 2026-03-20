# 🧠 Mind Map – Oracle Database Architecture

---

## 🗺️ Theory & Concepts

### Instance vs Database
- **Instance** = SGA (shared memory) + Background Processes (running in OS)
- **Database** = Files on disk (data files, redo logs, control files, undo)
- One database can have multiple instances (RAC)
- Instance starts → mounts control file → opens database

### SGA (System Global Area)
- **Buffer Cache**: Data block cache, touch-count LRU (hot/cold), KEEP/RECYCLE pools
  - Block access: hash on (data_object_id, block#) → buffer header → read/pin
  - Hit ratio target: > 95%
- **Shared Pool**: Library cache (parsed cursors) + Data dictionary cache (metadata)
  - Hard parse: full optimization, 1-100ms, holds latches → kills scalability
  - Soft parse: reuse existing plan, ~0.1ms → bind variables mandatory
  - `cursor_sharing = FORCE` as emergency fix
- **Redo Log Buffer**: Staging area for change vectors before LGWR flush
- **Large Pool**: Used by RMAN, shared server mode, parallel query
- **In-Memory Area** (12c+): Optional columnar store for analytics on OLTP data

### PGA (Program Global Area)
- Private memory per server process
- Sort area: `SORT_AREA_SIZE` or auto-managed via `PGA_AGGREGATE_TARGET`
- Hash area: hash join operations
- PL/SQL runtime area: compiled PL/SQL code and variables

### Redo Log
- Online redo log groups (minimum 2, typically 3-6)
- Each group has mirrored members on separate disks
- LGWR writes redo buffer → current log group on commit
- Log switch → current group full → LGWR switches to next → ARCn archives previous
- Change vector format: block address + before/after data
- Sizing: 15-30 minute switch intervals

### Undo and Read Consistency
- Undo segments store before-images of modified data
- Read consistency: query at SCN X reads blocks at SCN X by applying undo
  - If block SCN > query SCN → create CR clone → roll back using undo → return consistent data
- Readers NEVER block writers; writers NEVER block readers
- ORA-01555: undo overwritten before query finishes → need larger undo retention
- `UNDO_RETENTION` + `RETENTION GUARANTEE` for analytical workloads

### Data Block (8KB default)
- Block header: cache layer (SCN, checksum) + transaction layer (ITL slots)
- ITL (Interested Transaction List): per-block, tracks active transactions
  - Limited slots → ITL wait if all slots in use → increase INITRANS
- Row directory: offsets to each row
- Row data: grows downward; row directory grows upward
- Free space between them

### Background Processes
- LGWR: write redo buffer to online redo logs (commit = fsync)
- DBWn: write dirty blocks to data files (lazy, not in commit path)
- CKPT: update data file headers with checkpoint SCN
- SMON: crash recovery (redo replay + undo rollback)
- PMON: clean up dead processes (release locks, rollback)
- ARCn: archive filled redo logs
- MMON: AWR snapshots, memory advisors

### RAC (Real Application Clusters)
- Multiple instances → one shared database
- Cache Fusion: block transfers over high-speed interconnect (InfiniBand)
- Global Cache Service (GCS): coordinates block ownership across nodes
- Failure mode: gc buffer busy → all nodes modifying same blocks
- Fix: partition hot tables, application affinity, CACHE NOORDER sequences

---

## 🗺️ Techniques & Patterns

### T1: Bind Variable Enforcement
- When: hard parse ratio > 5%
- Mechanism: same SQL text → shared cursor → soft parse
- Emergency: `cursor_sharing = FORCE`
- Permanent: PreparedStatement (JDBC), parameterized queries

### T2: Undo Sizing
- Formula: undo_rate × max_query_duration × 1.5
- `ALTER TABLESPACE undo_ts RETENTION GUARANTEE;`
- Monitor: `v$undostat.ssolderrcnt`

### T3: Redo Log Sizing
- Target: 15-30 min between log switches
- Formula: redo_bytes_per_sec × 1800
- Monitor: `v$log_history` switches per hour

### T4: AWR-Based Diagnostics
- AWR snapshots every 60 min (default)
- Key sections: Load Profile → Top 5 Events → SQL by Elapsed Time
- ASH: 1-second sampling of active sessions for real-time analysis

### T5: SQL Plan Baselines
- Lock known-good execution plans
- Evolve: test new plans against baseline before accepting
- Prevents plan regression from statistics refresh

---

## 🗺️ Real-World Scenarios

### 01: Bank — RAC gc buffer busy
- All nodes modifying same account blocks
- Fix: hash partition + application affinity + CACHE 10000 NOORDER sequences

### 02: Telecom — ORA-01555 during billing
- 4-hour batch query vs 15-min undo retention
- Fix: undo retention = 4 hours; GUARANTEE mode; offload to standby

### 03: Government — Hard parse storm
- 94.7% hard parse ratio; literal SQL everywhere
- Fix: cursor_sharing=FORCE (emergency) → application rewrite with bind variables

### 04: Insurance — Partition strategy evolution
- 120M rows un-partitioned → interval + list sub-partitioning
- 30x faster reporting; instant partition drop for archival

---

## 🗺️ Mistakes & Anti-Patterns

| # | Anti-Pattern | Detection | Fix |
|---|---|---|---|
| M01 | No bind variables | Hard parse > 10%, library cache waits | PreparedStatement; cursor_sharing |
| M02 | Undersized undo | ORA-01555, undo steal counts | Retention = max query time |
| M03 | Small redo logs | > 6 switches/hour | Size for 15-30 min switches |
| M04 | RAC without affinity | gc buffer busy > 10% DB time | Partition + application affinity |
| M05 | Stale statistics | E-Rows vs A-Rows > 10x mismatch | Auto-gather; SQL Plan Baselines |
| M06 | Single tablespace | Mixed I/O, no granularity | Separate: data, index, LOB, undo |

---

## 🗺️ Assessment & Reflection
- Can you explain why Oracle's undo-based MVCC avoids heap bloat but creates ORA-01555 risk?
- Do you understand why bind variables are critical for Oracle's shared pool?
- Can you diagnose `log file sync` waits and explain the commit write path?
- Can you design a RAC deployment that avoids Cache Fusion contention?
- Can you read an AWR report and identify the top bottleneck in 5 minutes?
