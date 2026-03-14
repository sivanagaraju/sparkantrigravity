# Backup & Recovery Strategies — Concept Overview

> The three-legged stool: logical backups, physical backups, and WAL archiving.

---

## Comparison

| Strategy | Speed (Backup) | Speed (Restore) | Point-in-Time? | Portability |
|---|---|---|---|---|
| **pg_dump (logical)** | Slow (reads all data) | Slow (re-inserts) | ❌ | ✅ Cross-version |
| **pg_basebackup (physical)** | Fast (copies files) | Fast (copy back) | ✅ With WAL | ❌ Same version |
| **WAL Archiving + PITR** | Continuous | Fast (base + replay) | ✅ To any second | ❌ Same version |
| **Barman/pgBackRest** | Fast (incremental) | Fast (parallel) | ✅ | ❌ Same version |

## Interview — Q: "Design a backup strategy for a 5TB PostgreSQL production database."

**Strong Answer**: "Nightly physical backup with pgBackRest (incremental, parallel, compressed). Continuous WAL archiving to S3 for point-in-time recovery. Weekly pg_dump of critical schemas as a logical safety net. Test restores monthly — an untested backup is not a backup."

## References

| Resource | Link |
|---|---|
| [pgBackRest](https://pgbackrest.org/) | Production-grade backup tool |
| [Barman](https://pgbarman.org/) | Backup manager for PostgreSQL |
