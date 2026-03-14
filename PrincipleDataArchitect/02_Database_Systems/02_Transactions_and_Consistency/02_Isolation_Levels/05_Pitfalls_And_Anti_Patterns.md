# Isolation Levels — Common Pitfalls & Anti-Patterns

> These are the mistakes that cause production incidents. Every one has been observed at scale.

---

## Anti-Pattern 1: "Serializable Everywhere" (The Sledgehammer)

**The Mistake**: A well-meaning engineer reads about write skew and sets `default_transaction_isolation = 'serializable'` globally in `postgresql.conf`.

**Why It's Dangerous**:
- Under moderate concurrency (~100 TPS), serialization failure rate stays at 1-3%. Manageable.
- Under high concurrency (~1000+ TPS), failure rate can hit 30-40%. Each failed transaction retries, adding more concurrency, creating a positive feedback loop.
- Connection pool exhaustion follows within minutes.

**Detection**:
```sql
-- Monitor serialization failures in PostgreSQL
SELECT count(*) 
FROM pg_stat_database 
WHERE datname = 'mydb' 
  AND conflicts > 0;

-- Or check application logs for:
-- ERROR: could not serialize access due to read/write dependencies
```

**Fix**: Use Serializable only for the 3-5 critical write paths where correctness is non-negotiable. Everything else should use Read Committed (the PostgreSQL default for a reason).

---

## Anti-Pattern 2: Missing Retry Logic at Serializable

**The Mistake**: Application code uses `BEGIN ISOLATION LEVEL SERIALIZABLE` but has no retry mechanism when the transaction aborts.

```python
# WRONG — no retry
conn.set_isolation_level(ISOLATION_LEVEL_SERIALIZABLE)
try:
    cur.execute("SELECT balance FROM accounts WHERE id = 1")
    balance = cur.fetchone()[0]
    if balance >= 100:
        cur.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
    conn.commit()
except Exception as e:
    conn.rollback()
    raise  # ← User sees 500 error for a completely normal event
```

**Why It's Dangerous**: At Serializable, transaction aborts are **expected behavior**, not bugs. Treating them as fatal errors means 1-5% of legitimate operations fail permanently.

**Fix**: Always implement retry with exponential backoff (see `03_Hands_On_Examples.md` Section 6).

---

## Anti-Pattern 3: Long Transactions at High Isolation (The VACUUM Blocker)

**The Mistake**: A nightly analytics report runs for 4 hours inside a single `REPEATABLE READ` transaction.

**Why It's Dangerous**: 
- PostgreSQL: The old snapshot prevents VACUUM from cleaning tuples. Table bloat grows linearly with transaction duration.
- MySQL: Long transactions hold gap locks for hours, blocking inserts.
- Oracle: Long consistent reads may exhaust undo segments → ORA-01555 "Snapshot Too Old."

**Detection**:
```sql
-- Find long-running transactions in PostgreSQL
SELECT pid, age(now(), xact_start) AS duration, query
FROM pg_stat_activity
WHERE state = 'active' 
  AND xact_start < now() - interval '10 minutes'
ORDER BY duration DESC;

-- Check table bloat
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS total_size,
       n_dead_tup, n_live_tup,
       ROUND(n_dead_tup::numeric / NULLIF(n_live_tup, 0) * 100, 2) AS dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
ORDER BY n_dead_tup DESC;
```

**Fix**: Break long reports into 15-minute chunks with separate Read Committed transactions. Or run on a read replica.

---

## Anti-Pattern 4: Assuming Cross-Engine Isolation Equivalence

**The Mistake**: Migrating from MySQL to PostgreSQL (or vice versa) and assuming "Repeatable Read" means the same thing.

| Behavior at RR | PostgreSQL | MySQL InnoDB |
|---|---|---|
| Phantom prevention | ✅ Via snapshot (optimistic) | ✅ Via gap locks (pessimistic) |
| Write detection | First-updater-wins abort | Lock-wait then proceed |
| Gap lock deadlocks | Impossible (no gap locks) | Common under load |
| Non-locking reads block | Never | Never |
| UPDATE evaluation locks | Minimal | Short-duration row locks |

**Why It's Dangerous**: Application logic that relied on MySQL's gap locks to prevent phantom inserts will silently produce phantoms on PostgreSQL if the application doesn't use `FOR UPDATE` or Serializable.

**Fix**: During migration, audit every transaction that uses `FOR UPDATE`, `IN SHARE MODE`, or relies on range-based uniqueness. Test each with concurrent access patterns.

---

## Anti-Pattern 5: Using Read Uncommitted "For Performance"

**The Mistake**: Setting `SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED` in SQL Server for "fast reads" without understanding the consequences.

**Why It's Dangerous**: Dirty reads can cause:
- Financial reports based on uncommitted transactions that later roll back
- Inventory systems showing phantom stock that doesn't exist
- Analytics dashboards with impossible numbers (negative balances, counts > total)

**Fix**: If you need fast reads without blocking, use **Snapshot Isolation** (`ALTER DATABASE SET READ_COMMITTED_SNAPSHOT ON` in SQL Server). You get MVCC performance without dirty reads.

---

## Anti-Pattern 6: SELECT COUNT(*) as Consistency Guard

**The Mistake**: Using `SELECT COUNT(*) FROM table WHERE condition` to check business rules before modifying data, without proper isolation or locking.

```sql
-- WRONG at Read Committed:
BEGIN;
SELECT COUNT(*) FROM seats WHERE flight = 'AA100' AND status = 'available';
-- Returns 5. "Safe to book."
-- Meanwhile another transaction books the last seat...
UPDATE seats SET status = 'booked' WHERE flight = 'AA100' AND seat = '14A';
COMMIT;
-- Overbooking!
```

**Why It's Dangerous**: The COUNT and the UPDATE are separate statements with separate snapshots at Read Committed. The world can change between them.

**Fix**: Either:
1. Use `SELECT ... FOR UPDATE` to lock the rows you're checking
2. Use Serializable isolation with retry logic
3. Use a single atomic statement: `UPDATE seats SET status = 'booked' WHERE flight = 'AA100' AND seat = '14A' AND status = 'available'` and check `rows_affected`

---

## Decision Matrix: When Isolation Levels Are the WRONG Tool

| Requirement | Wrong Approach | Right Approach |
|---|---|---|
| Prevent double-spending | Serializable on every transaction | Application-level idempotency key + Read Committed |
| Ensure unique assignment | Gap locks via Repeatable Read | UNIQUE constraint + INSERT ON CONFLICT |
| Global counter accuracy | Serializable isolation | Redis atomic increment or `SELECT ... FOR UPDATE` on counter row |
| Cross-service consistency | Database isolation levels | Saga pattern or distributed transactions |
| Prevent concurrent user edits | Row locking via FOR UPDATE | Optimistic locking with version column |
