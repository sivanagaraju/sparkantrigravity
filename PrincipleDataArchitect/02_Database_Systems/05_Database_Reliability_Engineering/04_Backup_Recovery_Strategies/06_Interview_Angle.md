# Interview Angle: Backup & Recovery Strategies

## How This Appears

Backup/recovery questions surface in Staff/Principal interviews as:
1. **System Design:** "Design a disaster recovery strategy for a multi-region fintech database."
2. **Incident Response:** "Your 2 TB PostgreSQL database has corrupted data from a bug deployed 3 hours ago. Walk through recovery."
3. **Architecture Trade-offs:** "Compare logical vs. physical backups. When would you choose each?"

## Sample Questions & Answer Frameworks

### Q1: "What's the difference between RPO and RTO, and how do they drive backup architecture?"

**Strong:** "RPO is how much data you can afford to lose, measured backward from the failure. RTO is how long you can afford to be down, measured forward from detection.

- **RPO = 0:** Requires synchronous replication. Every committed transaction exists on at least two nodes before acknowledgment. Trade-off: higher write latency.
- **RPO < 1 minute:** Continuous WAL archiving with `archive_timeout = 60` plus async replication. Cost-effective for most production systems.
- **RPO < 1 hour:** Periodic backups (hourly pg_dump or pgBackRest incremental). Acceptable for non-critical data.

- **RTO < 30 seconds:** Hot standby with automated failover (Patroni/etcd). The standby is already running and replaying WAL.
- **RTO < 30 minutes:** Warm standby or pgBackRest delta restore. Data files exist; need WAL replay.
- **RTO < 4 hours:** Cold restore from backup. Acceptable for development or non-critical systems.

The key insight: RPO is primarily a backup/replication problem. RTO is primarily a standby/infrastructure problem. They're independent axes—you can have RPO = 0 with RTO = 4 hours (sync replication, but no automated failover), or RPO = 1 hour with RTO = 30 seconds (hot standby with hourly backups)."

### Q2: "Walk me through recovering from an accidental DELETE of 5 million rows that happened 2 hours ago."

**Principal Answer:**
"First, I assess the situation: is this a full table delete or partial? Is the application still writing to the table? What's our backup infrastructure?

Assuming we have pgBackRest with continuous WAL archiving:

1. **Do NOT restore in place.** I spin up a recovery instance alongside production.
2. **PITR to just before the DELETE:**
   ```
   pgbackrest --stanza=main --type=time
     --target='2 hours and 1 minute ago'
     --target-action=pause restore
   ```
3. **Verify the recovered data** on the recovery instance. Check row counts, spot-check key records.
4. **Export only the affected table** from the recovery instance using pg_dump.
5. **Import the data** into production using pg_restore with `--data-only`.
6. **Handle the gap:** Any legitimate inserts to the table between the DELETE and now need to be reconciled. I'd check the application logs or use the recovered WAL to identify these transactions.

This approach avoids a full production restore (which would lose 2 hours of data in OTHER tables) and surgically repairs only the affected data."

### Q3: "You're responsible for a 5 TB PostgreSQL database. Design the backup strategy."

**Strong:**
"At 5 TB, logical backups (pg_dump) are impractical—they'd take 20+ hours. My strategy:

**Tool:** pgBackRest with dual repositories.
- **Repo 1:** Local NFS for fast restores (RTO optimization).
- **Repo 2:** S3 with Object Lock for disaster recovery and ransomware protection.

**Schedule:**
- Weekly full backup (parallel, zstd compressed, ~2 hours).
- Daily differential backup (~30 minutes).
- Continuous WAL archiving with `archive_timeout = 60`.

**Retention:** 4 weeks of full backups, daily differentials within each full cycle. WAL retention sufficient to cover the oldest full backup.

**Recovery scenarios:**
- **Hardware failure:** Failover to streaming replica (RTO: seconds). Not a backup scenario.
- **Data corruption:** PITR from pgBackRest to a recovery instance. Surgically repair affected tables.
- **Full disaster:** Restore from S3 to new infrastructure. RTO: ~3 hours (download + WAL replay).

**Validation:** Monthly automated restore drill. A script restores the latest backup to a test instance, runs data integrity checks, and reports to Slack."

### Q4: "Why is replication not a substitute for backups?"

**Crisp answer:** "Replication protects against server failure—if the primary dies, the replica takes over. But replication faithfully copies every operation, including destructive ones. `DROP TABLE` replicates instantly. A bug that corrupts data replicates the corruption. Ransomware replicates the encryption. Backups, especially with PITR, let you go back in time to before the destructive event. You need both: replication for availability (RTO), backups for recoverability (RPO against logical errors)."
