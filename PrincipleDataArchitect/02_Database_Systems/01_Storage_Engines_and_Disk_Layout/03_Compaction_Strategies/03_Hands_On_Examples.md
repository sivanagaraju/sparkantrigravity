# Compaction Strategies — Hands-On Examples

> Inspecting, triggering, and tuning compaction in real systems like RocksDB and Cassandra.

---

## Example 1: Creating a Write Amplification Test in RocksDB

This C++ example demonstrates how to configure Leveled Compaction (LCS) versus Universal Compaction (similar to STCS) in RocksDB to measure Write Amplification.

```cpp
#include <rocksdb/db.h>
#include <rocksdb/options.h>
#include <iostream>

using namespace rocksdb;

int main() {
    DB* db;
    Options options;
    options.create_if_missing = true;
    
    // Enable Compaction Statistics
    options.statistics = rocksdb::CreateDBStatistics();

    // ==========================================
    // SCENARIO A: Leveled Compaction (Default)
    // ==========================================
    options.compaction_style = kCompactionStyleLevel;
    options.write_buffer_size = 64 * 1024 * 1024; // 64MB memtable
    options.max_bytes_for_level_base = 256 * 1024 * 1024; // 256MB L1
    options.max_bytes_for_level_multiplier = 10; // 10x size per level
    
    // ==========================================
    // SCENARIO B: Universal Compaction (like STCS)
    // Uncomment to test Write-Heavy workload
    // ==========================================
    // options.compaction_style = kCompactionStyleUniversal;
    // options.compaction_options_universal.size_ratio = 1;

    Status s = DB::Open(options, "/tmp/rocksdb_test", &db);

    // Simulate write-heavy workload: Overwriting the SAME keys repeatedly
    // This creates massive garbage that compaction must clean up
    for (int i = 0; i < 5000000; i++) {
        std::string key = "user_" + std::to_string(i % 10000); // 10k unique keys
        std::string value = std::string(1024, 'x'); // 1KB payload
        db->Put(WriteOptions(), key, value);
    }

    // Print compaction stats
    std::string stats;
    db->GetProperty("rocksdb.stats.level0", &stats);
    std::cout << "Compaction Stats:\n" << stats << std::endl;
    // Look for "Write Amp" in the output. 
    // Leveled will show ~10-15x. Universal will show ~2-4x.

    delete db;
    return 0;
}
```

---

## Example 2: Inspecting Cassandra Compaction Activity

Apache Cassandra allows you to monitor and control compaction in real-time using `nodetool`.

### 1. View Current Compaction Activity
```bash
# Are any compactions running right now?
nodetool compactionstats

# Output example:
# pending tasks: 12
# id                                   compaction type keyspace table completed total    unit  progress
# 42a7b1...                            Compaction      users    data  1.2GB     4.5GB    bytes 26.6%
```
*Diagnostic value*: A consistently high number of `pending tasks` means your database cannot compact fast enough. It is falling behind the write load.

### 2. Viewing SSTables per Level (LCS)
```bash
# See how files are distributed across levels
nodetool tablestats keyspace.table | grep "SSTables in each level"

# Good Output (Pyramid shape - healthy):
# SSTables in each level: [1, 10, 100, 350, 0, 0, 0, 0, 0]

# Bad Output (L0 is bloated - falling behind):
# SSTables in each level: [85, 10, 100, 350, 0, 0, 0, 0, 0]
```
*Why 85 in L0 is fatal*: Reads must check *every* overlapping file in L0. 85 files in L0 means read latency just spiked by 85x.

---

## Example 3: Altering Compaction Strategy on a Live Table (Cassandra)

You discover a table holding IoT sensor data was created with the default Size-Tiered (STCS) strategy, but it has a 30-day TTL. Tombstone eviction is failing, and disk space is exhausted.

You must change it to Time-Window Compaction Strategy (TWCS).

```sql
-- View current strategy
DESCRIBE TABLE iot_measurements;

-- Change live to TimeWindowCompactionStrategy
-- We set the window size to 1 day since data is queried by day
ALTER TABLE iot.measurements WITH compaction = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'DAYS',
    'compaction_window_size': 1
};
```

**What happens immediately under the hood?**
Nothing destructive. Cassandra will gradually begin grouping new files into 1-day windows. You do not need to rewrite the entire historical dataset (though you can force it later via `nodetool compact`).

---

## Example 4: Diagnosing "Tombstone Overwhelming"

A common compaction trap in Cassandra/ScyllaDB: you run a query and it times out, reporting a `TombstoneOverwhelmingException`. 

**The Cause**: The database found 100,000 deleted records before finding 1 valid record. Compaction hasn't purged the tombstones yet because the `gc_grace_seconds` (default 10 days) hasn't passed.

**The Fix (if data is safely not resurrected):**
```sql
-- 1. Reduce the wait time before tombstones can be physically deleted from 10 days to 1 hour
ALTER TABLE users WITH gc_grace_seconds = 3600;

-- 2. Force a major compaction to purge them
-- (WARNING: Major compaction rewrites the whole table, causing massive I/O)
```
```bash
nodetool compact my_keyspace users
```

---

## Example 5: Configuring RocksDB Rate Limiters for Compaction

Compaction causes massive background I/O spikes. Without rate limiting, user queries (p99 latency) will suffer during compactions.

```cpp
// Create a rate limiter allowing max 50 MB/s for background compactions
std::shared_ptr<RateLimiter> rate_limiter(NewGenericRateLimiter(50 * 1024 * 1024));

Options options;
options.rate_limiter = rate_limiter;

// Increase concurrent background threads so compaction doesn't fall behind 
// even though it is rate-limited
options.max_background_compactions = 4;
options.max_background_flushes = 2;
```
*Result*: Background compactions take longer to complete, but they no longer saturate the NVMe drives, ensuring steady single-digit millisecond latency for user API requests.
