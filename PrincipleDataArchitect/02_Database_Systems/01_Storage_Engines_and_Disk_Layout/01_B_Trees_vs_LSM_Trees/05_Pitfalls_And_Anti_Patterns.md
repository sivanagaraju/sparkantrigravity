# B-Trees vs LSM-Trees — Pitfalls & Anti-Patterns

---

## Anti-Pattern 1: Using B-Tree for Write-Heavy IoT Ingestion

**Wrong way**: Storing 500K sensor readings/sec into PostgreSQL with B-Tree indexes on every column.

**Why it's wrong**: Each INSERT requires finding the correct leaf page in each B-Tree index → random I/O per row per index. At high insert rates, the random I/O saturates the disk.

**Detection**:

```sql
-- Check I/O wait time
SELECT * FROM pg_stat_bgwriter;
-- High buffers_backend and buffers_backend_fsync = the background writer
-- can't keep up, backends are flushing pages themselves

-- Check WAL write rate
SELECT pg_wal_lsn_diff(pg_current_wal_lsn(), '0/0') / 1024 / 1024 AS wal_mb;
-- If WAL is growing faster than disk can flush, you've hit the ceiling
```

**Fix**: Use an LSM-based engine (RocksDB, ClickHouse) or TimescaleDB (hypertables partition by time, making writes sequential within each chunk).

---

## Anti-Pattern 2: Using LSM for Read-Heavy User Profile Lookups

**Wrong way**: Storing user profiles in RocksDB/Cassandra when 95% of operations are reads.

**Why it's wrong**: LSM reads check memtable → L0 → L1 → L2... Multiple levels = multiple disk reads per query. B-Tree: single path from root to leaf = 3-4 pages.

**Detection**:

```
# RocksDB stats — check read amplification
rocksdb.read.amp = 4.2  (reading 4.2 SSTables per query on average)
# If > 2, reads are being amplified across levels
```

**Fix**: Use PostgreSQL/MySQL (B-Tree). If you must use RocksDB, tune Bloom filters aggressively (15 bits/key → 0.02% false positive rate) and increase block cache to keep hot data in RAM.

---

## Anti-Pattern 3: Ignoring Write Amplification in Cost Models

**Wrong way**: Capacity planning for an LSM database based only on logical data size.

**Why it's wrong**: 100GB of logical data with 20x write amplification writes 2TB/day to disk. A consumer SSD rated for 150 TBW (total bytes written) lasts only 75 days.

**Detection**:

```bash
# Linux: check actual bytes written to disk
cat /sys/block/nvme0n1/stat | awk '{print $7}'  # sectors_written
# Compare against application-level writes
# Ratio = write amplification
```

**Fix**:

- Factor write amplification (10-30x for LSM) into SSD procurement
- Use enterprise SSDs with high DWPD (Drive Writes Per Day) rating: 3 DWPD vs 0.3 DWPD
- Monitor `rocksdb.compact.write.bytes` and `rocksdb.flush.write.bytes`

---

## Anti-Pattern 4: Not Tuning Bloom Filter Bits Per Key

**Wrong way**: Using RocksDB default Bloom filter settings for a read-heavy workload.

**Why it's wrong**: Default 10 bits/key gives 1% false positive rate. For read-heavy workloads, this means 1 in 100 queries reads an unnecessary SSTable.

**Detection**: Monitor `rocksdb.bloom.filter.useful` vs `rocksdb.bloom.filter.full.positive` — if `full.positive` is high, the filter isn't selective enough.

**Fix**:

| Bits Per Key | False Positive Rate | Memory Cost (1M keys) |
|---|---|---|
| 10 | 1.0% | 1.2 MB |
| 12 | 0.3% | 1.4 MB |
| 15 | 0.02% | 1.8 MB |
| 20 | 0.0001% | 2.4 MB |

For read-heavy workloads: use 15 bits/key. The extra 0.6 MB per million keys saves thousands of unnecessary disk reads.

---

## Anti-Pattern 5: Running Compaction During Peak Hours

**Wrong way**: Letting RocksDB/Cassandra run major compaction during business hours.

**Why it's wrong**: Major compaction rewrites gigabytes of data → consumes 50-80% of disk I/O → read/write latency spikes.

**Detection**: Latency spikes that correlate with compaction scheduler activity. Check `rocksdb.compaction.times.micros`.

**Fix**:

- Rate-limit compaction I/O: `rocksdb.rate_limiter` with bytes/sec cap
- Schedule major compaction during off-peak (Cassandra: `nodetool compact` with `--begin-token` / `--end-token`)
- Increase compaction threads for faster completion: `max_background_compactions`

---

## Decision Matrix: When Each Is the WRONG Choice

| Scenario | Wrong Choice | Right Choice | Why |
|---|---|---|---|
| IoT 500K writes/sec | PostgreSQL (B-Tree) | ClickHouse, RocksDB, Cassandra | B-Tree random I/O can't sustain write rate |
| User profile lookup (95% reads) | Cassandra (LSM) | PostgreSQL, MySQL | LSM read amplification hurts latency |
| Mixed OLTP (50/50 read/write) | Pure LSM | PostgreSQL, MySQL, WiredTiger | B-Tree or hybrid handles mixed well |
| Append-only event log | PostgreSQL (row-heavy table) | Kafka + ClickHouse, LSM store | LSM's append-only nature matches perfectly |
| Time-series with retention | Plain B-Tree | TimescaleDB, InfluxDB, FIFO compaction | Time-based partitioning + TTL is essential |
