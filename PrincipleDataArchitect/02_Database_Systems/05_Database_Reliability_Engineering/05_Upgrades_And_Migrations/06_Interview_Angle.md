# Interview Angle: Upgrades & Migrations

## How This Appears

Upgrade/migration questions surface in Staff+ interviews as:
1. **System Design:** "How would you perform a zero-downtime major version upgrade of a 2 TB PostgreSQL database?"
2. **Incident Response:** "A schema migration locked a production table for 30 minutes. How would you prevent this?"
3. **Architecture:** "Describe your approach to schema evolution in a microservices architecture."

## Sample Questions & Answer Frameworks

### Q1: "How do you safely add a NOT NULL column to a table with 500 million rows?"

**Strong Answer:**
"The naive approach — `ALTER TABLE t ADD COLUMN c NOT NULL DEFAULT 'x'` — has version-dependent behavior.

On PG 11+, this is metadata-only (instant) because the default value is stored in the catalog and returned virtually for rows that don't have the column yet. The `NOT NULL` constraint is enforced through the catalog default. No table rewrite.

On PG 10 and earlier, or for more complex scenarios, I use a multi-step approach:
1. `ALTER TABLE t ADD COLUMN c text;` — instant, nullable, no default.
2. `ALTER TABLE t ALTER COLUMN c SET DEFAULT 'x';` — for future rows.
3. Batch UPDATE existing rows in chunks of 10K with `pg_sleep` between batches to avoid WAL bloat and replication lag.
4. `ALTER TABLE t ADD CONSTRAINT t_c_nn CHECK (c IS NOT NULL) NOT VALID;` — instant, marks constraint as not yet validated.
5. `ALTER TABLE t VALIDATE CONSTRAINT t_c_nn;` — scans the table to verify all rows satisfy the constraint, but uses a `ShareUpdateExclusiveLock` that does NOT block reads or writes.

Each step is wrapped with `SET lock_timeout = '3s'` to prevent cascading queue blocks."

### Q2: "Describe the tradeoffs between pg_upgrade and logical replication for a major version upgrade."

**Principal Answer:**

| Dimension | pg_upgrade --link | Logical Replication |
| :--- | :--- | :--- |
| **Downtime** | Minutes (stop PG, run upgrade, start) | Seconds (switchover only) |
| **Replica handling** | Must rebuild all replicas from scratch | New-version replicas set up independently |
| **Database size impact** | O(files), not O(data) — fast at any size | Initial sync is O(data), then streaming |
| **Rollback** | Not possible (hard links share files) | Keep old primary running as fallback |
| **Complexity** | Low (single command, well-tested) | High (sequence sync, DDL not replicated, LOBs) |
| **Extension compatibility** | Must be pre-verified | Must be pre-verified |

My recommendation depends on scale:
- **< 500 GB with acceptable downtime window:** `pg_upgrade --link`. Simpler, well-understood, 5-minute downtime.
- **> 500 GB or zero-downtime requirement:** Logical replication. Higher setup effort but enables testing on the new version under real load before switchover, and provides instant rollback."

### Q3: "Your team ships schema migrations weekly. How do you ensure they don't cause outages?"

**Framework:**
"I enforce a migration safety checklist:

1. **Tool enforcement:** All migrations go through Flyway/Alembic with code review. No manual DDL on production.
2. **Lock timeout:** Every migration file starts with `SET lock_timeout = '5s';`.
3. **Production-size testing:** CI pipeline runs each migration against a production-size database copy. Measures execution time and reports locks acquired.
4. **Concurrency-safe patterns:** `CREATE INDEX CONCURRENTLY`, `ADD CONSTRAINT ... NOT VALID` + `VALIDATE CONSTRAINT`, `ADD COLUMN` nullable-first.
5. **Batch data changes:** Any UPDATE/DELETE affecting >10K rows must be batched with throttling.
6. **Rollback scripts:** Every migration has a corresponding rollback migration (V5.1__rollback_add_priority.sql).
7. **Expand-Contract:** Column renames and type changes use the multi-deploy pattern. Never drop a column in the same release that stops writing to it.
8. **Post-migration monitoring:** Alert on `pg_stat_activity` for `waiting = true` or `lock_type = AccessExclusiveLock` held for >5 seconds."
