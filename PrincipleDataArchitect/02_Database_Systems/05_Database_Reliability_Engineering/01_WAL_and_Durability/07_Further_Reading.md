# Further Reading: WAL and Durability

## Essential Sources

*   **The Internals of PostgreSQL — Chapter 9: WAL**
    *   *Source:* interdb.jp
    *   *Why:* The most thorough free technical reference on PostgreSQL WAL internals. Covers WAL record format, resource managers, checkpoint mechanics, and PITR from a source-code perspective.

*   **PostgreSQL Documentation: Reliability and the Write-Ahead Log**
    *   *Source:* postgresql.org/docs/current/wal.html
    *   *Why:* The official reference for WAL configuration parameters (`fsync`, `synchronous_commit`, `wal_level`, `checkpoint_timeout`, `max_wal_size`). Start here for any GUC tuning.

*   **"PostgreSQL fsync Errors" — The 2018 Data Loss Bug**
    *   *Search Term:* "PostgreSQL fsync errors Craig Ringer" or "data_sync_retry"
    *   *Why:* A critical case study in how OS-level `fsync` semantics can undermine database durability guarantees. Essential reading for anyone responsible for production database reliability.

## Books

*   **Designing Data-Intensive Applications (DDIA) — Chapter 3: Storage and Retrieval**
    *   *Author:* Martin Kleppmann
    *   *Why:* Covers WAL, LSM-trees, and B-trees with cross-database comparison. The durability discussion spans PostgreSQL, MySQL, LevelDB, and more.

*   **PostgreSQL 14 Internals — Egor Rogov**
    *   *Why:* Extremely deep coverage of buffer management, WAL writers, checkpointers, and the recovery process. Available free from Postgres Professional.

## Tools

*   **pg_waldump** — Decode and inspect WAL records from the command line.
*   **pg_test_fsync** — Benchmark various `fsync` methods on your storage to verify durability guarantees.
*   **pg_stat_wal** (PostgreSQL 14+) — Runtime view of WAL generation statistics.
*   **pg_ls_waldir()** — List WAL files with size and modification time.

## Cross-References

*   **Backup & Recovery Strategies:** WAL archiving is the foundation of PITR. Understanding WAL is a prerequisite for the backup topic.
*   **Replication Topologies:** Streaming replication works by sending WAL records from primary to replica. WAL-level understanding is essential for debugging replication lag.
*   **Storage Engines and Disk Layout:** WAL interacts directly with the buffer manager, shared buffers, and the background writer.
