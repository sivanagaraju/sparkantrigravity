# Real-World Scenarios: Backup & Recovery Strategies

## Case Study 1: The Accidental DELETE Without a WHERE Clause

**Incident:** A developer ran `DELETE FROM orders` (missing `WHERE status = 'cancelled'`) on the production database at 10:42 AM. This deleted 2.3 million orders.

**Recovery timeline:**
1. **10:42 AM** — DELETE executes. 2.3M rows gone.
2. **10:44 AM** — Monitoring alerts fire: order count dropped to zero.
3. **10:46 AM** — Team confirms the accidental deletion.
4. **10:48 AM** — DBA identifies the last pgBackRest backup (incremental at 10:00 AM) and notes continuous WAL archiving is active with `archive_timeout = 60s`.
5. **10:50 AM** — DBA begins PITR on a separate server:
   ```bash
   pgbackrest --stanza=main --type=time \
     "--target=2024-03-15 10:41:00+00" \
     --target-action=pause \
     --delta restore
   ```
6. **11:15 AM** — Recovery complete on the separate server. DBA verifies the orders table has all 2.3M rows at 10:41 AM.
7. **11:20 AM** — DBA exports the orders table from the recovered server:
   ```bash
   pg_dump -h recovered-server -t orders -Fc mydb > orders_recovered.dump
   ```
8. **11:30 AM** — DBA restores the orders table to production:
   ```bash
   pg_restore -h production -d mydb --data-only -t orders orders_recovered.dump
   ```
9. **11:45 AM** — All orders restored. Data loss: 0 (PITR recovered up to 10:41 AM; orders created between 10:41–10:42 were re-entered manually from the application logs).

**Key Lesson:** PITR didn't require restoring the entire database. The DBA restored to a temporary server and selectively exported only the affected table.

## Case Study 2: Ransomware Encrypted the Primary and All Replicas

**Incident:** A healthcare company's PostgreSQL primary and all three replicas were encrypted by ransomware. The attacker gained access via a compromised application server that had direct database credentials.

**Why replicas didn't help:** Replicas faithfully replicated the ransomware's `DROP` and encryption commands. Replication is NOT a backup—it replicates destruction too.

**Recovery:** The company had pgBackRest configured with S3-backed repositories using:
- IAM role-based access (no static credentials on servers)
- S3 Object Lock (WORM) with 30-day retention—even the root AWS account cannot delete these backups
- Cross-region replication to a second S3 bucket

Recovery steps:
1. Provisioned a new PostgreSQL server in a clean VPC.
2. Restored from the last verified pgBackRest backup (6 hours old).
3. Replayed WAL from S3 up to the point just before the ransomware executed.
4. Total data loss: ~5 minutes (time between last WAL archive and the attack).

**Key Lessons:**
- S3 Object Lock (WORM) saved the backups from deletion by the attacker.
- Cross-region replication provided protection against region-level compromise.
- IAM-based access (not database credentials) prevented the attacker from reaching backups.

## Case Study 3: The Backup That Couldn't Be Restored

**Incident:** A startup had been running `pg_dump` backups nightly for 2 years. When they needed to restore after a disk failure, the restore failed:
```
pg_restore: error: unsupported version (1.14) in file header
```

**Root Cause:** They had upgraded PostgreSQL from 14 to 16 but never tested restoring their pg_dump backups. The dump format version was compatible, but the dump referenced extensions (`PostGIS 3.2`) that weren't installed on the new server. After installing extensions, the restore revealed that the dump had been silently failing for 3 months—the cron job ran, but the database connection was refused (password change), and no one checked the exit code.

**Key Lessons:**
1. **Test restores regularly.** A backup that hasn't been tested is not a backup.
2. **Monitor backup job exit codes.** Don't assume cron success.
3. **Restore to a separate server monthly** and verify data integrity.
4. **Document extension dependencies** required for restore.

## Case Study 4: Choosing Between pg_dump and pgBackRest at Scale

**The Problem:** A 2 TB PostgreSQL database. `pg_dump` took 8 hours, producing a 200 GB compressed file. Restore took 12 hours. RPO = 20 hours (8h dump + 12h restore gap). Unacceptable for a financial system.

**Migration to pgBackRest:**
- Full backup: 45 minutes (parallel, compressed, block-level copy).
- Incremental backup: 3-5 minutes (copies only changed blocks).
- PITR restore: 30 minutes for base backup + WAL replay.
- RPO: 60 seconds (archive_timeout = 60).

| Metric | pg_dump | pgBackRest |
| :--- | :--- | :--- |
| Full backup time | 8 hours | 45 minutes |
| Incremental backup time | N/A | 3-5 minutes |
| Restore time | 12 hours | 30 minutes |
| RPO | 20 hours | 60 seconds |
| Cross-version portable | Yes | No (same major version) |
