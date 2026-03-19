# Real-World Scenarios: Upgrades & Migrations

## Case Study 1: The 4-Hour Outage from a "Simple" ALTER TABLE

**Incident:** A team added a NOT NULL column with a default value to a 500M-row table on PostgreSQL 10:
```sql
ALTER TABLE events ADD COLUMN source text NOT NULL DEFAULT 'unknown';
```

On PostgreSQL 10, this **rewrites the entire table** (500M rows) while holding `AccessExclusiveLock`. The table was locked for 4 hours. No reads or writes could proceed. The application was completely down.

**Why it happened:** In PostgreSQL 10 and earlier, `ADD COLUMN ... DEFAULT x` requires a full table rewrite because the default value must be physically written to every existing row. PostgreSQL 11 changed this: the default is stored in the catalog and returned "virtually" for existing rows without rewriting them—making it instant.

**Prevention:**
1. Upgrade to PostgreSQL 11+ where `ADD COLUMN ... DEFAULT` is metadata-only.
2. On older versions, use the two-step pattern:
   ```sql
   ALTER TABLE events ADD COLUMN source text;        -- instant (nullable, no default)
   ALTER TABLE events ALTER COLUMN source SET DEFAULT 'unknown';  -- for future rows
   UPDATE events SET source = 'unknown' WHERE source IS NULL;     -- backfill in batches
   ALTER TABLE events ALTER COLUMN source SET NOT NULL;            -- after all rows have values
   ```

## Case Study 2: pg_upgrade Left Standbys Behind

**Incident:** A team used `pg_upgrade --link` to upgrade from PG 14 to PG 15. The primary upgraded successfully in 3 minutes. But they forgot: **pg_upgrade does not upgrade streaming replicas.** The replicas were still running PG 14 and could not connect to the PG 15 primary. The application's read replicas were down.

**The Fix (took 6 hours):**
```bash
# Rebuild each standby from scratch
pg_basebackup -h pg15-primary -D /var/lib/postgresql/15/main -P -R
# 2 TB database × 3 replicas = 6 hours of data transfer
```

**Prevention:**
- Plan for replica rebuild time when using pg_upgrade.
- For large databases, use `rsync` with `pg_upgrade`'s `--link` option to minimize replica rebuild:
  ```bash
  # After pg_upgrade on primary, rsync only changed files to standby
  rsync -av --delete /var/lib/postgresql/15/main/ standby:/var/lib/postgresql/15/main/
  ```
- Or use logical replication upgrade: replicas of the new version are set up independently.

## Case Study 3: The Lock Queue Outage

**Incident:** During a scheduled maintenance window, a DBA ran:
```sql
ALTER TABLE orders ADD COLUMN tracking_number text;
```

This should have been instant (nullable, no default on PG 14). But a long-running analytics query held `AccessShareLock` on the `orders` table. The DDL statement queued for `AccessExclusiveLock`. **All subsequent queries**—including the application's simple SELECTs and INSERTs—queued behind the DDL. The application froze for 12 minutes until the analytics query finished.

**Root Cause:** PostgreSQL's lock manager is FIFO. Once a DDL statement is waiting, it blocks all subsequent lock requests, even compatible ones (like `AccessShareLock` for SELECTs).

**Prevention:**
```sql
-- Always set lock_timeout before DDL
SET lock_timeout = '3s';
ALTER TABLE orders ADD COLUMN tracking_number text;
-- If it can't acquire the lock in 3s, it fails with an error instead of blocking.
-- Retry after killing the blocking query or waiting for it to finish.
```

Also: **kill long-running queries before DDL windows:**
```sql
-- Find long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '1 minute';

-- Terminate if necessary
SELECT pg_terminate_backend(pid);
```

## Case Study 4: Zero-Downtime MySQL 5.7 → 8.0 Migration

**Context:** A SaaS company with 800 GB MySQL database needed to upgrade from 5.7 to 8.0. Downtime was not acceptable (24/7 global service).

**Strategy used:** Blue-Green with ProxySQL.

1. **Built a MySQL 8.0 replica** from the MySQL 5.7 primary using `mysqldump --single-transaction` (schema) + binary log replication. MySQL 8.0 can replicate from 5.7 as a replica.
2. **Tested on the 8.0 replica:** Ran application integration tests, performance benchmarks, checked query plan changes.
3. **Promoted 8.0:** Used ProxySQL to redirect traffic from the 5.7 primary to the 8.0 replica (now the new primary). Switchover time: 2 seconds.
4. **Kept 5.7 running** as a read-only fallback for 48 hours. After validation, decommissioned.

**Challenges encountered:**
- MySQL 8.0 changed the default `character_set_server` from `latin1` to `utf8mb4`. Some queries returned different sort orders. Fixed by explicitly setting character sets before switchover.
- `GROUP BY` implicit ordering was removed in 8.0. Several application queries depended on implicit ordering. Added explicit `ORDER BY` clauses.
