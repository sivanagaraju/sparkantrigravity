# Further Reading: Backup & Recovery Strategies

## Essential Sources

*   **pgBackRest Documentation**
    *   *Source:* pgbackrest.org
    *   *Why:* The definitive reference for the most capable PostgreSQL backup tool. Covers full, differential, block-level incremental, parallel operations, encryption, and multi-repository configurations.

*   **PostgreSQL Documentation — Chapter 26: Backup and Restore**
    *   *Source:* postgresql.org/docs/current/backup.html
    *   *Why:* Official coverage of pg_dump, pg_basebackup, continuous archiving, and PITR. The foundation for understanding PostgreSQL-specific backup mechanics.

*   **Percona XtraBackup Documentation**
    *   *Source:* docs.percona.com/percona-xtrabackup
    *   *Why:* The standard for hot physical backups of MySQL/InnoDB. Covers full, incremental, compressed, and encrypted backups.

## Books

*   **PostgreSQL 14 Internals — Egor Rogov (Chapter: WAL, Backup)**
    *   *Why:* Explains the internal mechanics of WAL archiving, base backups, and how PITR works at the page and LSN level.

*   **Database Reliability Engineering — Laine Campbell & Charity Majors**
    *   *Why:* Chapter on backup strategies covers organizational aspects: RPO/RTO negotiations, backup testing culture, and incident response procedures.

## Tools

*   **pgBackRest** — Production-grade PostgreSQL backup with incremental, parallel, and encrypted operations.
*   **Barman** — Backup and Recovery Manager for PostgreSQL by EnterpriseDB. Alternative to pgBackRest.
*   **WAL-G** — Archival and restoration tool by Wal-G community. Supports S3, GCS, Azure. Simpler than pgBackRest.
*   **Percona XtraBackup** — Hot physical backup for MySQL/InnoDB.
*   **mysqldump / mydumper** — Logical backup for MySQL. `mydumper` provides parallel dump/restore.
*   **mongodump / mongorestore** — MongoDB logical backup tools.

## Cross-References

*   **WAL and Durability:** PITR depends entirely on WAL. `archive_mode`, `archive_command`, and `archive_timeout` are the bridge between durability and recoverability.
*   **Replication Topologies:** Backups should be taken from replicas (not the primary) to avoid I/O impact. pgBackRest supports backup from standby.
*   **Connection Pooling:** During restore, connection poolers can queue application requests while the database is unavailable, providing graceful degradation.
