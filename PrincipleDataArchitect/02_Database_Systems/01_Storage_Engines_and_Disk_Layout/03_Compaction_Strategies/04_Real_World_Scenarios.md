# Compaction Strategies — Real-World Scenarios

> When compaction strategies hit production reality, the wrong choice can burn through SSDs or cause severe CPU starvation.

---

## Case Study 1: Spotify — The "Tombstone Overwhelming" Incident

**Context**: Spotify used Cassandra (with Size-Tiered Compaction, STCS) to track billions of user-playlist relationships, inserting and deleting records frequently as users modified their libraries.

**The Problem**:
- A major feature release triggered millions of deletes across the cluster.
- In Cassandra, a delete writes a "tombstone" marker.
- Due to the default STCS, old SSTables and new tombstones lived in separate files for weeks without being compacted together.
- When a user queried their playlist, the read path had to scan through millions of tombstones just to find 50 active songs.
- Result: Nodes returning `TombstoneOverwhelmingException` and dropping queries. Latencies spiked to over 10 seconds.

**The Fix**:
- Switched the compaction strategy on the heavily-mutated table from STCS to **Leveled Compaction Strategy (LCS)**.
- LCS constantly pushes overlapping files down and merges them, aggressively purging tombstones.
- Result: Read latencies returned to single-digit milliseconds within 24 hours. The cost was higher Write Amplification (CPU and disk I/O), but read stability was achieved.

---

## Case Study 2: Fastly — SSD Burnout from Write Amplification

**Context**: A CDN provider built a distributed logging system using RocksDB. The logging system ingested 200,000 requests per second per node.

**The Problem**:
- RocksDB defaults to **Leveled Compaction Strategy (LCS)**.
- While LCS guarantees low read latencies (great for key-value lookups), its write amplification is severe (often 20x to 30x).
- 10 TB of logical data ingested per day translated into 250 TB of physical disk writes per day due to constant background compaction.
- Enterprise SSDs (rated for 3 Drive Writes Per Day, or DWPD) began failing within 6 months of deployment.

**The Fix**:
- Recognizing that logging is an **append-only, write-heavy, read-rarely** workload, the team altered the RocksDB configuration.
- Changed to a tiered strategy (`kCompactionStyleUniversal`), drastically reducing background merges.
- Result: Write amplification plummeted from 25x to 3x. Read latency slightly degraded (which was acceptable for offline log processing), but SSD lifetime extended to 5+ years.

---

## Case Study 3: DataStax — The Compaction Death Spiral

**Context**: An e-commerce client experienced "compaction death spirals" during Black Friday traffic surges.

**The Problem**:
- Under normal load, Cassandra handles compaction easily.
- During Black Friday, the insert rate quadrupled.
- Background compactions (the I/O bound process of merging SSTables) couldn't finish before new SSTables were flushed from memtables.
- L0/Tier 1 files skyrocketed from 10 to 400 overlapping files.
- Read amplification exploded because every `SELECT` query had to scan 400 files.
- High read latency → CPU saturated handling timeouts → Compaction threads starved → More files built up (The Death Spiral).

**The Fix**:
- Temporary: Manually bumped up `concurrent_compactors` to dedicate more CPU to clearing the backlog at the expense of upfront write latency.
- Permanent: Upgraded underlying storage to NVMe to eliminate the I/O bottleneck, and tuned `compaction_throughput_mb_per_sec` up from the default 16 MB/s to 200 MB/s. 

---

## Case Study 4: Cloudflare — Time-Series Nirvana

**Context**: Cloudflare processes petabytes of HTTP request logs daily for security analytics. Logs are naturally partitioned by time.

**The Problem**:
- Initial deployments used STCS. Because of minor late-arriving data (out of order by hours or minutes), large overarching compactions triggered randomly, burning massive I/O resources and causing intermittent query timeouts.

**The Fix**:
- Adopted **Time-Window Compaction Strategy (TWCS)**, configured to 1-hour windows.
- Files from 1:00-2:00 PM are compacted together, and *never* merged with data from 2:00-3:00 PM.
- Because data drops off completely after 30 days (TTL), TWCS simply deletes the historical files with `rm` on the OS level. Zero compaction overhead for deletions.
- Result: I/O dropped by 80%, query performance stabilized, and node stability became completely predictable.

---

## Summary of Real-World Learnings

| Workload Type | The Trap | The Solution |
|---|---|---|
| **High Deletes/Updates** | STCS (Leaves tombstones around for too long, crashing reads) | **LCS** (Aggressively merges and purges tombstones) |
| **High Insert/Logging** | LCS (High write amplification kills SSDs prematurely) | **STCS / Universal** (Minimizes writes, saves drives) |
| **Time Series / TTL** | STCS/LCS (Massive I/O wasted on data that will just expire anyway) | **TWCS** (Files separated by time; dropped instantly on TTL) |
