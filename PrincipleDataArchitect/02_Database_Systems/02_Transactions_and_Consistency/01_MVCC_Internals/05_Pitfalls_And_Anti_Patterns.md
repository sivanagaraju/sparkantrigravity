# MVCC Internals — Pitfalls & Anti-Patterns

---

## Anti-Pattern 1: The Long-Running Stalled Transaction (PostgreSQL)

**Wrong way**: A developer creates an internal dashboard. The dashboard runs a script that opens a connection to the primary database, runs `BEGIN TRANSACTION;`, executes a `SELECT`, and then holds that transaction open for 6 hours while a Python script processes the data slowly over the network.

**Why it's wrong**: 
In PostgreSQL, the `VACUUM` process scans for "Dead Tuples". However, the absolute highest cardinal rule of PG MVCC is that **a tuple cannot be deleted if any currently running transaction might need to look at it**.
Because that Python dashboard holds a 6-hour snapshot open from 9:00 AM, *every single row updated anywhere in the database between 9:00 AM and 3:00 PM must be preserved on disk*. 
- **Symptom**: Massive table bloat across the cluster over the span of hours. Disk space alerts fire.
- **Diagnostic**: `SELECT pid, state, query, datname, backend_xid, backend_xmin FROM pg_stat_activity WHERE state = 'idle in transaction';`
- **Fix**: Never hold transactions open for analytic processing. Use a read replica, or use `commit` immediately after pagination reads. Alternatively, set `idle_in_transaction_session_timeout` aggressively (e.g., 5 minutes).

---

## Anti-Pattern 2: Uber's Trap — High Update Churn on Heavily Indexed Tables

**Wrong way**: Using PostgreSQL for a table where 90% of operations are `UPDATE`s on a specific non-indexed column (e.g., `view_count` on a `videos` table), while that table has 15 different secondary indexes (`created_at`, `author_id`, `category`, etc).

**Why it's wrong**: 
Due to Postgres append-only MVCC, modifying the `view_count` creates a brand new physical row at a new `ctid` (disk address). Because the physical address changed, the database must write to all 15 secondary b-trees to update the physical pointers.
- You modified 4 bytes of data, but generated 16 separate physical disk writes across vastly distributed blocks of the disk layout. 
- **Symptom**: Crippling write latency, massive replication lag.
- **Fix**: Move hyper-mutated unstructured data to a separate table with a 1:1 relationship to the parent, with NO secondary indexes. Alternatively, if building this from scratch, use an Undo Log based DB like MySQL/InnoDB where secondary indexes point to Primary Keys, isolating the write penalty.

---

## Anti-Pattern 3: Ignoring Transaction ID Wraparound Warnings

**Wrong way**: A DBA notices a warning log: `WARNING: database "mydb" must be vacuumed within 10000000 transactions` and ignores it because performance currently looks fine.

**Why it's wrong**: 
This is the database telling you that the 32-bit transaction counter is heading toward 4.2 billion and it hasn't been able to run a "freeze" operation to shield old data from the wraparound. 
If this number hits zero, the database will literally shut off (`PANIC: database is not accepting commands to avoid wraparound data loss in database "mydb"`) and refuse to turn back on without risky offline maintenance.
- **Diagnostic**: Compare the system's `xid` against the oldest frozen ID. `SELECT max(age(datfrozenxid)) FROM pg_database;` If this number crosses 2 billion, you are in danger.
- **Fix**: Immediately investigate what is blocking Autovacuum (usually Anti-Pattern 1, or insufficient I/O limits configuration for Autovacuum).

---

## Anti-Pattern 4: "Repeatable Read" Hallucinations in MySQL vs Postgres

**Wrong way**: Assuming the REPEATABLE READ isolation level defined by the ANSI SQL standard works physically the same way under the hood in MySQL and PostgreSQL.

**Why it's wrong**:
The SQL standard dictates that REPEATABLE READ stops "Dirty Reads" and "Non-Repeatable Reads", but allows "Phantom Reads" (where a concurrent transaction inserts a new row matching your WHERE clause, and it suddenly appears on your second query).
- **Postgres Implementation**: PG implements MVCC via strict snapshot visibility boundaries. Its REPEATABLE READ *does not allow Phantom Reads*. You simply get the exact snapshot state from when you started. (It is practically Snapshot Isolation).
- **MySQL/InnoDB Implementation**: MySQL's REPEATABLE READ *does* allow Phantom Reads strictly speaking via Insert handling, but utilizes Next-Key Locks to try and stop it. 
- **Symptom**: Migrating an application from PG to MySQL (or vice versa) and relying on the exact boundaries of REPEATABLE READ without understanding the internal MVCC engine variance will lead to subtle concurrency bugs and data corruption.
- **Fix**: Know your Engine. If you need strict snapshotting against phantoms in MySQL without locks, upgrade to SERIALIZABLE, or understand explicitly how undo log gap locking behaves.
