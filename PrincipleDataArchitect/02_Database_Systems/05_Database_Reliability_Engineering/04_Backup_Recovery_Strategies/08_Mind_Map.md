# 🧠 Mind Map – Backup & Recovery Strategies

---
## How to Use This Mind Map
- **For Architecture:** Start with RPO/RTO → choose backup strategy → choose tools.
- **For Interviews:** Remember: Replication ≠ Backup. Always test restores. Know the 3-2-1 rule.
- **For Operations:** Monitor backup age, WAL archive lag, and run quarterly restore drills.

---
## 📦 Backup Types
### Logical (pg_dump)
- SQL-level export.
- Cross-version portable.
- Slow for large DBs (>100 GB).
- Best for: small DBs, migration, selective export.

### Physical (pg_basebackup)
- Raw data file copy.
- Version-specific.
- Fast for large DBs.
- Requires WAL for consistency.

### PITR (pgBackRest + WAL)
- Base backup + continuous WAL archiving.
- Recover to any second in time.
- RPO: seconds.
- Gold standard for production.

### Snapshot (EBS/ZFS)
- Storage-level copy-on-write.
- Near-instant creation.
- Crash-consistent (needs WAL replay).
- Best for: cloud-native, very large DBs.

### Incremental (pgBackRest)
- Only changed blocks since last backup.
- Dramatically reduces backup time/storage.
- Requires full backup as base.

---
## 📦 RPO/RTO Decision
| RPO | Strategy |
|-----|----------|
| 0 | Sync replication + WAL archive |
| < 1 min | Async repl + archive_timeout=60 |
| < 1 hour | Periodic pgBackRest incr |
| < 24 hours | Nightly pg_dump |

| RTO | Strategy |
|-----|----------|
| < 30s | Hot standby (Patroni) |
| < 30 min | pgBackRest delta restore |
| < 4 hours | Cold restore from S3 |

---
## 📦 Critical Rules
- 3-2-1: 3 copies, 2 media, 1 offsite.
- Replication ≠ Backup (replicates drops too).
- Test restores quarterly.
- Monitor: backup age, WAL archive lag, exit codes.
- S3 Object Lock for ransomware protection.

---
## 📦 Anti-Pattern Checklist
- ❌ Replication as sole backup.
- ❌ Never testing restores.
- ❌ No backup monitoring/alerting.
- ❌ pg_dump for >100 GB databases.
- ❌ Backups on same volume as data.
- ❌ Ignoring WAL archive gaps.
- ❌ Not encrypting backup data at rest.
