# 🧠 Mind Map – WAL and Durability

---
## How to Use This Mind Map
- **For Revision:** Trace the write path from COMMIT → WAL Buffer → fsync → COMMIT OK. Internalize that data pages are NOT on disk at commit time.
- **For Debugging:** When data is "lost" after crash, check: Was `fsync = on`? Was `synchronous_commit = on`? Was the storage honoring `fsync`? Was there a long-running transaction preventing WAL recycling?
- **For Architecture:** Choose the right durability level per workload—not everything demands synchronous commits.

---
## 🔒 The Durability Stack
### Layer 1: Application
- COMMIT is issued by the client.
- The database returns COMMIT OK only after the WAL is durable (when `synchronous_commit = on`).

### Layer 2: WAL Buffer → WAL Segment
- WAL records accumulate in shared-memory ring buffer.
- At COMMIT, the buffer is flushed to the WAL segment file on disk.
- Sequential I/O only—no random writes.

### Layer 3: fsync / fdatasync
- OS system call forcing file-system cache → physical storage.
- Without fsync, the OS may cache indefinitely—crash = data loss + corruption.
- `pg_test_fsync` validates the storage stack.

### Layer 4: Physical Storage
- Must have power-loss protection (Enterprise SSD with PLP / Battery-Backed Write Cache).
- Consumer-grade SSDs may lie about fsync completion.

---
## 🔒 Checkpoint Mechanics
### Purpose
- Flush dirty shared-buffer pages to data files.
- Advance the recovery redo point.
- Enable recycling of old WAL segments.

### Tuning Knobs
- `checkpoint_timeout`: Time-triggering (default 5 min).
- `max_wal_size`: Volume-triggering (default 1 GB).
- `checkpoint_completion_target`: Spread I/O over 90% of the interval.

### The FPW Trade-off
- After checkpoint: first modification → entire 8 KB page in WAL.
- Protects against torn pages (partial 8 KB writes).
- Inflates WAL by 2-3x immediately post-checkpoint.

---
## 🔒 The Durability Spectrum
### `synchronous_commit = on` (Default)
- COMMIT waits for fsync confirmation.
- Zero data loss window.
- Higher commit latency.

### `synchronous_commit = off`
- COMMIT returns after WAL buffer write (no fsync wait).
- ~600ms risk window.
- 3-5x throughput improvement.
- **Can be set per-transaction** with `SET LOCAL`.

### `fsync = off`
- **NEVER in production.**
- Entire database may corrupt on any crash.

---
## 🔒 Recovery Process
1. Read `pg_control` → find last checkpoint's redo LSN.
2. Open WAL segments starting from redo LSN.
3. For each WAL record, check target page's `pd_lsn`.
4. If `pd_lsn < record LSN` → apply the record (page was dirty in memory, never flushed).
5. If `pd_lsn >= record LSN` → skip (page was already flushed to disk).
6. Database is now consistent.

---
## 🔒 Anti-Pattern Checklist
- ❌ `fsync = off` in production.
- ❌ WAL and data files on the same physical disk.
- ❌ Frequent checkpoints without monitoring FPW overhead.
- ❌ No monitoring of WAL directory size or replication LSN lag.
- ❌ Consumer-grade SSDs without power-loss protection.
- ❌ Long-running transactions blocking WAL recycling.
