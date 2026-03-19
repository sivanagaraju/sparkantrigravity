# 🧠 Mind Map – Upgrades & Migrations

---
## How to Use This Mind Map
- **For Planning:** Always run `pg_upgrade --check` before upgrading. Always `SET lock_timeout` before DDL.
- **For Interviews:** Know expand-contract. Know why pg_upgrade doesn't upgrade replicas. Know the lock queue problem.
- **For Operations:** Test every migration on production-size data. Batch large UPDATEs. Monitor query plans post-upgrade.

---
## 🔄 Major Version Upgrade
### pg_upgrade
- `--link` mode: hard links, instant, no rollback.
- `--copy` mode: safe, slow, rollback possible.
- Standbys NOT upgraded — must rebuild.
- Always run `--check` first.

### Logical Replication Upgrade
- Old → New via logical decoding.
- Zero-downtime switchover (seconds).
- DDL, sequences, LOBs NOT replicated.
- Higher complexity, better for large DBs.

---
## 🔄 Safe DDL Patterns
### Always Safe
- `ADD COLUMN` (nullable, no default).
- `ADD COLUMN ... DEFAULT x` (PG 11+, instant).
- `CREATE INDEX CONCURRENTLY`.
- `ADD CONSTRAINT ... NOT VALID` + `VALIDATE CONSTRAINT`.

### Dangerous — Use Caution
- `ALTER COLUMN TYPE` (full table rewrite).
- `ADD COLUMN NOT NULL` without default (PG <11).
- `CREATE INDEX` (without CONCURRENTLY — blocks writes).
- Any DDL without `SET lock_timeout`.

---
## 🔄 Expand-Contract Pattern
1. **Expand:** Add new column/table. Old + new coexist.
2. **Migrate:** Backfill data in batches. App writes to both.
3. **Contract:** Drop old column/table after verification.
- Each phase = separate deployment.
- Each phase = independently rollbackable.

---
## 🔄 Anti-Pattern Checklist
- ❌ DDL without `SET lock_timeout`.
- ❌ Testing migration on tiny dev database only.
- ❌ No rollback plan.
- ❌ Single large UPDATE (no batching).
- ❌ Skipping `pg_upgrade --check`.
- ❌ Ignoring query plan changes post-upgrade.
- ❌ Dropping columns in same release that stops using them.
