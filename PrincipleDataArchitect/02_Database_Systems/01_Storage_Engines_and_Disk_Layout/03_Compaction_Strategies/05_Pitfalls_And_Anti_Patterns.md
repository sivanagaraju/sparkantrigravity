# Compaction Strategies — Pitfalls & Anti-Patterns

---

## Anti-Pattern 1: Leveled Compaction for Write-Heavy Logging Workloads

**Wrong way**: Using the default Leveled Compaction Strategy (LCS) in RocksDB or Cassandra for an append-only, high-throughput ingest workload (like logging, clickstreams, or telemetry tracking).

**Why it's wrong**: LCS forces data to be rewritten 10 to 30 times as it cascades down levels L0 through L6 to ensure zero file overlap. This produces massive Write Amplification.
1. You burn through SSD TBW (Total Bytes Written) ratings in months instead of years.
2. Background I/O saturation throttles the foreground write path (creating artificial backpressure limits).

**Detection**:
- Monitor Write Amplification: `(Bytes Written to Disk by Compaction + Bytes Flushed) / Bytes Flushed`.
- If WA is > 15x on a purely append-only workload, you have configured the wrong strategy.

**Fix**: Switch to Size-Tiered (Cassandra) or Universal / FIFO compaction (RocksDB), which accept higher read amplification (which you don't care about for bulk logging) in exchange for single-digit write amplification.

---

## Anti-Pattern 2: Time-Window Compaction (TWCS) for Mutating Data

**Wrong way**: Developers hear "TWCS is the most efficient!" and apply it to a regular operational table (like user profiles or shopping carts).

**Why it's wrong**: TWCS *only* merges files that fall within the exact same time window (e.g., today). If a user created their account 3 years ago (File A) but updates their password today (File B), those two files will *never* be merged.
- Because they are never merged, the old password record (and the tombstone to overwrite it) lives forever.
- Reading that user profile requires scanning files across years of history.

**Detection**:
- Look for tables with `compaction = {'class': 'TimeWindowCompactionStrategy'}` that frequently process `UPDATE` or `DELETE` statements on old rows.
- Read latencies will slowly degrade over time as the number of unmerged SSTables grows.

**Fix**: TWCS is strictly for IMMUTABLE, TIME-SERIES data (insert once, read sometimes, let expire). If data mutates across time boundaries, switch back to LCS or STCS.

---

## Anti-Pattern 3: STCS with Insufficient Free Disk Space

**Wrong way**: Running Size-Tiered Compaction Strategy on a hard drive that is 60% full.

**Why it's wrong**: STCS merges similar-sized files together. If you have four 100GB files (400GB total), STCS needs to create a *new* 400GB file *before* it can delete the old ones. 
- You need 400GB of FREE space to complete the compaction.
- If you only have 200GB free, the compaction will fail and abort. The cluster will stop compacting its largest tier entirely.
- Left unchecked, read performance drops as smaller tiers continue to back up.

**Detection**:
- `nodetool compactionstats` showing large pending tasks that start, pause, and fail.
- Disk usage hovering around 70-80% on STCS nodes without throwing direct errors.

**Fix**: As a strict rule of thumb, **STCS requires 50% free disk space** at all times to guarantee the largest tier can successfully compact. If you cannot afford 50% overhead, you must use LCS (which only compacts ~100MB at a time).

---

## Anti-Pattern 4: Relying on Default Compaction Throughput

**Wrong way**: Migrating from HDD to NVMe SSDs but leaving `compaction_throughput_mb_per_sec` (Cassandra default: 16 MB/s) unchanged.

**Why it's wrong**: That default was set in 2011 to prevent spinning disks from grinding to a halt during background merges. On modern NVMe drives capable of 3,000 MB/s, limiting compaction to 16 MB/s guarantees that background compaction falls behind foreground insert bursts. This generates a massive backlog of overlapping L0 SSTables, spiking query latencies.

**Fix**: 
- If using NVMe SSDs, increase throughput to 200-500 MB/s, or disable throttling entirely (`compaction_throughput_mb_per_sec = 0` in Cassandra), provided your application CPU can handle the merge sort logic.

---

## Anti-Pattern 5: The Giant Major Compaction

**Wrong way**: Setting up a cron job to run `nodetool compact` (a major compaction merging all SSTables into one giant file) every Sunday night.

**Why it's wrong for STCS**: Once you force all data into one giant 1TB file, STCS will not compact it again until another 1TB file is created naturally over months. During those months, deleted records inside the 1TB file cannot be purged because the file itself isn't eligible for compaction yet.

**Fix**: Never manually trigger a major compaction on a tiered (LSM) system unless you are permanently decommissioning nodes or dealing with an emergency tombstone purge. Let the automated triggering algorithms handle file merging.
