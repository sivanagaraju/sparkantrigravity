# 🧠 Mind Map – Compaction Strategies

---

## How to Use This Mind Map
- **For Revision**: Review the RUM conjecture trade-offs before designing an LSM-based storage layer. 
- **For Application**: Use the decision heuristics in the Techniques section to choose the right strategy (STCS vs LCS vs TWCS) based on your I/O and workload profile.
- **For Interviews**: Be ready to whiteboard the Leveled Compaction cascade and explain why Time-Window Compaction solves the TTL problem.
- **For Debugging**: Reference the Anti-Patterns section to diagnose SSD burnout or Tombstone Overwhelming exceptions.

---

## 🗺️ Theory & Concepts

### The Compaction Imperative
- Why Compaction?
  - LSM Trees are append-only. Updates and Deletes are just new appends (Deletes = Tombstones).
  - Without compaction, fetching a key requires reading every SSTable ever created (infinite Read Amplification).
  - Without compaction, disk fills with dead data (infinite Space Amplification).
- The Merge Sort 
  - Compaction reads overlapping SSTables, merges them sequentially (like MergeSort).
  - Discards older versions of identical keys.
  - Discards tombstones (if the data they delete is also being compacted).

### The RUM Conjecture
- You cannot optimize all three simultaneously:
  - **Read Amplification (R)**: How many disk reads it takes to satisfy one logical read query.
  - **Update Amplification (U)**: (Write Amplification). How many physical bytes are written to disk for one byte inserted.
  - **Memory/Space Amplification (M)**: How much physical disk space is used per logical byte of data.

---

## 🗺️ Techniques & Patterns

### T1: Size-Tiered Compaction Strategy (STCS)
- When to use: Write-heavy logging, sensor data ingest, low-cost spinning HDDs.
- Mechanics:
  - Wait until N files of similar size exist (e.g., four 100MB files).
  - Merge them into one N× larger file (e.g., one 400MB file).
- Trade-offs:
  - **Optims**: Best for Write Amplification (lowest disk burnout).
  - **Penalties**: Worst Space Amplification (requires 50% free disk space to merge massive top-tier files). Worst Read Amplification (no boundaries; a query might check every file).

### T2: Leveled Compaction Strategy (LCS)
- When to use: Read-heavy workloads, OLTP data, user profiles, product catalogs. 
- Mechanics:
  - Key ranges are strictly partitioned per level (no overlapping ranges within Level 1, Level 2, etc.).
  - When L1 is full, a file is picked and merged *only* into the overlapping files in L2.
- Trade-offs:
  - **Optims**: Absolute best for Read Amplification (you check exactly 1 file per level). Best for Space (clears dead data rapidly).
  - **Penalties**: Terribly high Write Amplification (data is rewritten 10x-30x as it falls down the levels).

### T3: Time-Window Compaction Strategy (TWCS)
- When to use: Immutable Time-Series data WITH a Time-To-Live (TTL).
- Mechanics:
  - Groups files into time buckets (e.g., 1-hour window).
  - Only compacts files *inside* their own bucket. Never merges 10 PM data with 11 PM data.
  - When TTL expires, drops the entire file via OS file delete.
- Trade-offs:
  - **Optims**: Zero I/O cost for deleting data. Perfect for time-range queries.
  - **Penalties**: Fails completely if you update/delete historical records (destroys time partitioning).

---

## 🗺️ Hands-On & Code

### RocksDB Configuration
- `options.compaction_style = kCompactionStyleLevel;` (LCS, Default)
- `options.compaction_style = kCompactionStyleUniversal;` (Similar to STCS)
- `options.rate_limiter = NewGenericRateLimiter(50MB/s);` (Prevent NVMe saturation during background merges).

### Cassandra / ScyllaDB Diagnostics
- `nodetool compactionstats` (View running compactions and pending backlog)
- `nodetool tablestats keyspace.table` (View SSTables per level. L0 bloat = compaction falling behind)
- `ALTER TABLE x WITH compaction = {'class': 'TimeWindow...}` (Change strategy on a live table)

---

## 🗺️ Real-World Scenarios

### 01: Spotify's Tombstone Overwhelm
- The Trap: STCS on heavily mutated playlist data
- The Impact: Tombstones and old data trapped in separate tiers; reads had to scan millions of tombstones; read timeouts
- The Fix: Switched to LCS (aggressively merges and purges tombstones)

### 02: Fastly's SSD Burnout
- The Trap: LCS on an append-only CDN logging system (200k RPS)
- The Impact: LCS rewrote data 25x; Enterprise SSDs failed in 6 months from TBW exhaustion
- The Fix: Switched to Universal/STCS. Write Amplification dropped to 3x; SSD life extended to 5+ years

### 03: Black Friday Compaction Death Spiral
- The Trap: Massive insert burst overwhelmed background compaction CPU threads
- The Impact: L0 files exploded to 400+. Read queries had to scan 400 files. CPU saturated, starving compaction further.
- The Fix: Dedicated more CPU to concurrent compactors; upgraded I/O limits, preventing L0 bloat

### 04: Cloudflare's Time-Series Nirvana
- The Trap: STCS over-compacting vast swaths of HTTP logs that were just going to expire anyway
- The Impact: Wasted CPU and I/O
- The Fix: Adopted TWCS with 1-hour windows. I/O dropped 80% because expired data is just `rm` deleted, not compacted.

---

## 🗺️ Mistakes & Anti-Patterns

### M01: LCS for Write-Heavy Ingest
- Root Cause: Leaving default settings on logging/telemetry workloads
- Diagnostic: Calculate Write Amplification > 15x. SSD wear metrics climbing rapidly. 
- Correction: Switch to STCS/Universal. You don't need fast point-reads for logs.

### M02: TWCS for Mutating Operational Data
- Root Cause: Thinking TWCS is universally "better" or jumping on the hype
- Diagnostic: Read latencies degrade over months because an old insert and a new update fall into different time windows and are never compacted together.
- Correction: Restrict TWCS entirely to immutable data with TTLs. 

### M03: Running STCS with near-full Disks
- Root Cause: Treating DB storage like a laptop drive
- Diagnostic: Disks hit 70-80% capacity; large compactions abort; pending compaction tasks skyrocket.
- Correction: STCS requires exactly 50% free space buffer to perform its largest merge. Expand storage immediately.

### M04: Rate-Limiting NVMe Drives to HDD Era Defaults
- Root Cause: Legacy configuration (`compaction_throughput_mb_per_sec = 16`)
- Diagnostic: L0 files building up despite low CPU and barely touching NVMe capacity limits.
- Correction: Increase throughput to 200MB/s+ or disable limits (`0`) to let modern I/O catch up with memory flushes.

---

## 🗺️ Interview Angle

### Core Concept Verification
- "How does an LSM tree handle DELETES if files are immutable?"
- Expected: Explain Tombstones and how compaction eventually physically removes the data.

### SSD Burnout Question
- "Your DB drives are wearing out in 6 months from write amplification. How do you fix it?"
- Expected: Identify LCS as the culprit. Suggest changing to STCS/Universal at the cost of slightly higher read latency.

### The Storage Exhaustion Trick Question
- "You have IoT data filling your Cassandra cluster using STCS. You can't afford more disks. What do you do?"
- Expected: Recognize that STCS wastes 50% of the disk for merge headroom. Switch to TWCS to drop time-expired data directly without merging.

### Whiteboard Scenario
- Draw the RUM Conjecture triangle. Explain how you must trade Space, Write, and Read amplification against each other based on workload (Read-heavy = LCS, Write-heavy = STCS, TTL-heavy = TWCS).

---

## 🗺️ Assessment & Reflection
- Do you know the exact Write Amplification factor of your production databases?
- Are your high-churn tables using STCS, putting them at risk of tombstone overwhelm?
- Are you leaving 50% free space on STCS nodes?
- Are your time-series tables using TWCS, or are you wasting I/O compacting data that is about to expire?
