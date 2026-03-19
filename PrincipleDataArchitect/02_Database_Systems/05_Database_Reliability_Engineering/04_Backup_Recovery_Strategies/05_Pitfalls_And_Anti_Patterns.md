# Pitfalls & Anti-Patterns: Backup & Recovery

## 1. "Replication IS My Backup"

**The Fallacy:** "We have 3 replicas, so our data is safe."

**Why It Fails:** Replication faithfully replicates:
- `DROP TABLE production;` — replicated to all replicas instantly.
- Logical corruption (e.g., a bug writes bad data) — replicated everywhere.
- Ransomware `ALTER TABLE ... RENAME` — replicated.

**Replication != Backup.** Replication protects against hardware failure. Backups protect against data corruption, human error, and software bugs.

**The Rule:** Every database needs BOTH replication (for availability) and backups (for recoverability).

## 2. Never Testing Restores

**The Trap:** Running backup scripts for years without ever testing a restore. When disaster strikes, you discover:
- The backup is corrupted.
- The backup script has been silently failing.
- The restore requires extensions/configurations that don't exist.
- The restore takes 10x longer than expected.

**The Fix:** Schedule monthly or quarterly restore drills:
```bash
# Monthly: restore to a test server and verify
pgbackrest --stanza=main --type=time \
  "--target=$(date -u -d '1 hour ago' +%Y-%m-%d\ %H:%M:%S)+00" \
  --target-action=promote \
  --pg1-path=/var/lib/postgresql/16/restore-test \
  --delta restore

# Verify critical tables
psql -h restored-server -c "SELECT count(*) FROM orders;"
psql -h restored-server -c "SELECT max(created_at) FROM orders;"
```

## 3. No Backup Monitoring

**The Trap:** Backup scripts run as cron jobs. The DBA checks them... never. Common failures:
- Disk full: backup fails silently.
- Network timeout: S3 upload fails.
- Credential rotation: database password changed, backup script can't connect.

**The Fix:**
- Check backup exit codes in the script.
- Send alerts on failure (Slack, PagerDuty).
- Monitor backup age: alert if the last successful backup is older than 2× the expected interval.
- Monitor WAL archive lag: `pg_stat_archiver.last_archived_time` should be within `archive_timeout`.

## 4. Logical-Only Backup for Large Databases

**The Trap:** Using `pg_dump` for a 500 GB database. Dump takes 4 hours. Restore takes 8 hours. During restore, indexes are rebuilt from scratch. RPO = 12 hours minimum.

**The Fix:** Use physical backups (pgBackRest, pg_basebackup) for databases > 50-100 GB. Use `pg_dump` only for:
- Small databases (< 50 GB)
- Cross-version migration (pg_dump PG14 → restore on PG16)
- Selective table-level export

## 5. Storing Backups on the Same Machine/Volume

**The Trap:** Backup files stored on the same EBS volume as the database. When the volume fails, both the database and its backups are lost.

**The Fix:**
- Store backups on separate storage (S3, separate EBS volume, different server).
- Follow the 3-2-1 rule: 3 copies, 2 media types, 1 offsite.
- Use S3 Object Lock (WORM) for ransomware protection.

## 6. Ignoring WAL Archive Gaps

**The Trap:** WAL archiving is configured, but a network issue caused WAL segment 000000010000000A00000023 to fail archiving. Archiving resumed from segment 24 onward. During PITR, recovery fails:
```
FATAL: could not find required WAL file "000000010000000A00000023"
```

The single missing WAL segment makes all subsequent WAL unusable for recovery.

**The Fix:**
- Monitor `pg_stat_archiver`: `failed_count` should always be 0. `last_failed_wal` and `last_failed_time` indicate problems.
- PostgreSQL will NOT delete un-archived WAL segments if `archive_mode = on` (they accumulate in `pg_wal`). Monitor `pg_wal` directory size for unexpected growth—it signals archiving failures.
- Use pgBackRest's built-in archive management, which handles retries and gap detection.

## Decision Checklist

| Question | If Yes | If No |
| :--- | :--- | :--- |
| Database > 100 GB? | Use pgBackRest / physical backup | pg_dump may suffice |
| RPO < 5 minutes? | Continuous WAL archiving required | Periodic dumps may work |
| Multi-region DR? | S3 cross-region replication | Single-region backups |
| Compliance (PCI/HIPAA)? | Encrypted backups + access logging | Encryption still recommended |
| Tested restore in last 90 days? | Good | STOP and test now |
