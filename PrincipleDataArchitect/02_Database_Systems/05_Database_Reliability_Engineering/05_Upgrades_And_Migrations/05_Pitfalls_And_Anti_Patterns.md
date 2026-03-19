# Pitfalls & Anti-Patterns: Upgrades & Migrations

## 1. DDL Without lock_timeout

**The Trap:** Running `ALTER TABLE` on a busy table without `SET lock_timeout`. If any query holds a conflicting lock, the DDL queues—and ALL subsequent queries queue behind it. A simple metadata change turns into a full outage.

**The Rule:** Every DDL statement in production must be preceded by:
```sql
SET lock_timeout = '3s';  -- or '5s'
```
Fail fast, retry, fix the blocker. Never wait indefinitely.

## 2. Untested Migrations on Production-Sized Data

**The Trap:** Testing a migration on a dev database with 100 rows. It runs in 10ms. On production with 200M rows, it runs for 6 hours while holding an exclusive lock.

**The Rule:** Test every migration on a **production-size copy.** Measure execution time and locks acquired. Use `EXPLAIN ANALYZE` for UPDATE/DELETE migrations.

Migrations to watch:
- `ALTER TABLE ... ALTER COLUMN TYPE` (full table rewrite).
- `ALTER TABLE ... ADD CONSTRAINT ... NOT VALID` followed by `VALIDATE CONSTRAINT` (full table scan, but non-blocking).
- Large `UPDATE` statements (batch them: 10,000 rows per transaction, with `pg_sleep(0.1)` between batches to avoid overwhelming replication).

## 3. Not Planning Rollback

**The Trap:** Deploying a migration that adds a NOT NULL constraint and removes the old column. If the new application code has a bug, you can't roll back—the old code expects the dropped column.

**The Rule:** Every migration must have a documented rollback plan. Use the expand-contract pattern:
1. **Deploy migration** that ADDs new structures (expand).
2. **Deploy application code** that uses both old and new structures.
3. **Backfill data** in batches.
4. **Deploy application code** that uses only new structures.
5. **Deploy migration** that DROPs old structures (contract)—only after verifying everything works.

Each step is independently rollable.

## 4. pg_upgrade Without Checking Extensions

**The Trap:** Running `pg_upgrade` and discovering that PostGIS 3.2 is incompatible with PG 17, or that a custom C extension wasn't compiled for the new version. The upgrade fails mid-way.

**The Rule:** Always run `pg_upgrade --check` first. Additionally:
```sql
-- Before upgrade: list all extensions and their versions
SELECT extname, extversion FROM pg_extension;
-- Verify each has a compatible version for the target PostgreSQL major version.
```

## 5. Large Batch Updates Without Throttling

**The Trap:** A data backfill migration:
```sql
UPDATE users SET display_name = user_name WHERE display_name IS NULL;
```
On a table with 50M rows, this runs as a single transaction, generating a massive WAL volume, bloating the table (dead tuples), and causing replication lag to spike to hours.

**The Fix:** Batch the update:
```sql
DO $$
DECLARE
  batch_size integer := 10000;
  affected integer;
BEGIN
  LOOP
    UPDATE users SET display_name = user_name
    WHERE ctid IN (
      SELECT ctid FROM users
      WHERE display_name IS NULL
      LIMIT batch_size
      FOR UPDATE SKIP LOCKED
    );
    GET DIAGNOSTICS affected = ROW_COUNT;
    EXIT WHEN affected = 0;
    COMMIT;
    PERFORM pg_sleep(0.1);  -- throttle to avoid replication lag
  END LOOP;
END $$;
```

## 6. Ignoring Query Plan Changes After Upgrade

**The Trap:** After a major version upgrade, the query optimizer may choose different plans (new statistics, new optimization rules). A query that used an index scan in PG 15 might switch to a sequential scan in PG 16, causing a 100x slowdown.

**The Fix:**
- Run `ANALYZE` on all tables immediately after upgrade.
- Compare `EXPLAIN ANALYZE` output for critical queries before and after upgrade.
- Keep a "query plan baseline" of your top 20 most frequent queries and verify them post-upgrade.
- Use `pg_stat_statements` to identify queries with increased execution time.

## Anti-Pattern Summary

| Anti-Pattern | Impact | Fix |
| :--- | :--- | :--- |
| DDL without lock_timeout | Cascading outage | `SET lock_timeout = '3s'` |
| Untested on production-size data | Hours-long lock | Test on prod-size copy |
| No rollback plan | Stuck with broken state | Expand-contract pattern |
| Skip pg_upgrade --check | Mid-upgrade failure | Always run --check first |
| Single large UPDATE | WAL bloat, repl lag | Batch with throttle |
| Ignore plan changes | Performance regression | Compare EXPLAIN before/after |
