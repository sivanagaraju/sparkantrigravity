# Pitfalls & Anti-Patterns: WAL and Durability

## 1. Disabling fsync for "Performance"

**The Trap:** Developers benchmark with `fsync = off` in development, see a 10x throughput improvement, and push that setting to production. On the first unexpected power loss, the entire database cluster is unrecoverably corrupted—not just the last few transactions, but potentially the entire data directory.

**Why it's catastrophic:** With `fsync = off`, the OS kernel caches writes indefinitely. Data pages, WAL segments, and even the `pg_control` file may never reach disk. On crash, the database finds inconsistent data pages, corrupt WAL, and a `pg_control` pointing to a checkpoint that never actually reached stable storage.

**The Rule:** `fsync = off` is acceptable only for disposable databases (e.g., loading a static dataset that can be recreated from source). Never, under any circumstance, in production.

## 2. Ignoring Full-Page Write Overhead

**The Trap:** Administrators set very frequent checkpoints (`checkpoint_timeout = 1min`) to minimize crash recovery time. The unintended consequence: after every checkpoint, FPW kicks in, and *every* first modification to a page generates an 8 KB WAL write instead of a 50-byte delta. WAL generation triples, replication lag spikes, and archival storage fills up.

**The Fix:** Balance checkpoint frequency against FPW overhead. For most OLTP workloads, `checkpoint_timeout = 15min` with `max_wal_size = 4GB` provides a good trade-off. Monitor `pg_stat_wal.wal_fpi` to track FPW volume.

## 3. WAL Disk on the Same Volume as Data

**The Trap:** Placing `pg_wal/` on the same physical disk as the data directory. WAL writes are latency-critical sequential writes. Data file writes during checkpoint are random writes. When they share a disk, the disk head thrashes between sequential WAL appends and random data page flushes, destroying both throughput and commit latency.

**The Fix:** Always place `pg_wal/` on a dedicated, fast storage device (ideally a low-latency NVMe SSD with power-loss protection). Use a symlink:
```bash
mv /var/lib/postgresql/16/main/pg_wal /fast-ssd/pg_wal
ln -s /fast-ssd/pg_wal /var/lib/postgresql/16/main/pg_wal
```

## 4. The "Durable by Default" Assumption

**The Trap:** Assuming that `COMMIT OK` from the database means the transaction is guaranteed durable by default on every cloud platform. Many cloud block storage systems (e.g., older EBS gp2 volumes) do not honor `fsync()` correctly or have write-back caches without battery protection. The database believes the data is durable, but the storage layer has not actually persisted it.

**The Fix:**
- Use provisioned IOPS storage (io2 Block Express on AWS) with verified `fsync` behavior.
- Run `pg_test_fsync` (included with PostgreSQL) to verify that the storage actually completes `fsync` calls.
- Ensure the disk controller has a battery-backed write cache (BBWC) or use NVMe with power-loss protection (PLP).

## 5. Not Monitoring Replication LSN Lag

**The Trap:** The primary generates WAL normally, but the replica falls behind (network issue, slow disk). If `wal_keep_size` is too small and WAL archiving is misconfigured, the primary recycles WAL segments that the replica hasn't consumed yet. The replica's replication slot is now broken—it can never catch up and must be rebuilt from scratch (a multi-hour process for large databases).

**The Fix:**
```sql
-- Monitor replication lag by LSN difference
SELECT 
    client_addr,
    state,
    pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn) AS send_lag_bytes,
    pg_wal_lsn_diff(sent_lsn, flush_lsn) AS flush_lag_bytes,
    pg_wal_lsn_diff(flush_lsn, replay_lsn) AS replay_lag_bytes
FROM pg_stat_replication;
```
Alert when `replay_lag_bytes` exceeds a threshold (e.g., 500 MB).

## Decision Matrix: WAL Configuration

| Scenario | checkpoint_timeout | max_wal_size | synchronous_commit | Why |
| :--- | :--- | :--- | :--- | :--- |
| **Financial OLTP** | 5-10 min | 2 GB | on | Minimize data loss window; fast recovery |
| **High-throughput ingestion** | 15-30 min | 8-16 GB | off | Reduce FPW storms; accept small loss window |
| **Data warehouse bulk load** | 30 min | 16-32 GB | off | Minimize I/O contention with loading |
| **Development/Testing** | Default | Default | Default | Don't over-tune environments that don't matter |
