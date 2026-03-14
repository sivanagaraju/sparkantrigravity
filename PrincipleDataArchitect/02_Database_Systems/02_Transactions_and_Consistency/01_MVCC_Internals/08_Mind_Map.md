# 🧠 Mind Map – MVCC Internals

---

## How to Use This Mind Map
- **For Revision**: Recall the distinct structural difference between PostgreSQL (Append-Only) and MySQL (In-Place + Undo) before selecting an RDBMS for a high-update workload.
- **For Application**: Run the diagnostic queries when dealing with storage alerts to verify if long-running transactions are freezing VACUUM operations.
- **For Interviews**: Use the write amplification explanation to cleanly contrast Postgres versus MySQL architectures as a marker of Principal-level systems knowledge.

---

## 🗺️ Theory & Concepts

### Multiple Versions as Concurrency Control
- **The Core Trade-off**: CPU computation (snapshot filtering) and Storage (retaining old rows) is spent to completely eliminate Lock Contention.
- **The Golden Rule**: Readers never block Writers. Writers never block Readers. (Writers only block other concurrent Writers targeting the same row).
- **Snapshot Isolation**: A snapshot records the exact state of active and committed transactions at `BEGIN`. Queries ignore all updates globally committed *after* the snapshot was minted.

### Append-Only Heap (PostgreSQL)
- Mechanism:
  - `UPDATE` = `DELETE` (mark current tuple obsolete) + `INSERT` (create new tuple).
  - Tuples live side-by-side in the main heap space.
- Identifying Variables:
  - `xmin`: Transaction ID (TXID) that inserted the tuple.
  - `xmax`: TXID of the transaction that updated/deleted the tuple.
  - `ctid`: Pointer to the new physical disk address of the updated version.
- Cost: High Write Amplification. Rapid heap bloat. Every secondary index must be updated when `ctid` changes.

### In-Place + Undo Log (MySQL InnoDB / Oracle)
- Mechanism:
  - `UPDATE` = Directly overwrite the B-Tree leaf node.
  - Push the *previous* version of the row into a separate Undo Log.
- Identifying Variables:
  - `DB_ROLL_PTR`: Internal pointer on the clustered index row linking to the exact block in the Undo Log.
- Cost: Slow historical reads (must unroll the linked list). But zero write amplification for secondary indexes, as they point to the Primary Key, not the disk space.

---

## 🗺️ Techniques & Patterns

### T1: Taming Postgres Write Amplification (HOT)
- When to use: When facing heavy update workloads in PG but migration to MySQL is impossible.
- Step-by-Step:
  - Heap-Only Tuples (HOT) allows PG to skip updating secondary indexes IF the indexed columns didn't change AND there is enough empty padding on the exact same 8KB disk page to fit the new tuple natively.
  - Lower the `FILLFACTOR` on heavily updated tables from 100 to 70.
- Result: Leaves 30% of each disk page empty specifically to absorb localized, purely-heap updates without moving `ctid` across pages.

### T2: Monitoring the Vacuum Daemon
- When to use: When diagnosing runaway table bloat.
- Diagnostics: 
  - `pg_stat_user_tables` (`n_dead_tup`)
  - `pg_stat_activity` (look for `idle in transaction` queries holding old snapshots open).
- Fix: Use statement timeouts, kill phantom analytic queries, and configure aggressive autovacuum wakes rather than slow nightly vacuums.

---

## 🗺️ Hands-On & Code

### Interrogating PG Structure
- Expose hidden columns: `SELECT xmin, xmax, cmin, cmax, ctid FROM ...`
- Inspect physical disk pages: `CREATE EXTENSION pageinspect; SELECT * FROM heap_page_items(...)`

### Triggering MVCC Locks Intentionally
- Start an unresolved `BEGIN REPEATABLE READ` in Session A.
- Run 1M updates in Session B.
- Run `VACUUM VERBOSE` in Session C to observe `1000000 dead row versions cannot be removed yet`.

---

## 🗺️ Real-World Scenarios

### 01: Uber's Postgres to MySQL Migration
- The Trap: PG Append-Only MVCC for highly mutable location data.
- Scale: Millions of trip updates requiring 10-20 cascading B-Tree index physical pointer updates per single byte state change.
- The Fix: Multi-year migration back to MySQL InnoDB to leverage In-Place updates, saving thousands of disk IOPS and stabilizing replication lag.

### 02: GitLab's Transaction ID Wraparound
- The Trap: The maximum 32-bit `xmin` limit reached 4.2 billion due to blocked Vacuum freezes.
- Scale: Total cluster shutdown; a wraparound would make all old data magically invisible as IDs reset to 0.
- The Fix: Manual single-user Vacuum freeze. Instituted aggressive monitoring on `age(relfrozenxid)`.

### 03: Mailchimp Table Bloat
- The Trap: Default conservative HDD-era autovacuum settings on an unceasingly updated email-status table.
- Scale: Billions of status flag updates per day leaving behind dead tuples.
- The Fix: Disabling artificial I/O throttling (`cost_delay = 0`) entirely to let NVMe disks chew through the vacuum queue freely.

---

## 🗺️ Mistakes & Anti-Patterns

### M01: Long Running Analytic Queries over Operational Primaries
- Root Cause: Laziness or lack of read replicas.
- Diagnostic: The replica or primary wildly inflates in size. Disk alerts roar.
- Correction: Set `idle_in_transaction_session_timeout` or shift pure OLAP work to Snowflake/BigQuery where MVCC Vacuum semantics don't sabotage storage.

### M02: Massive Indexes on Mutating Columns
- Root Cause: Indexing every column (like `updated_at`) on a PG table "just in case".
- Diagnostic: Abysmal insert/update performance.
- Correction: Never index highly mutated columns in an Append-Only MVCC engine.

### M03: Treating Postgres and MySQL Isolation Identically
- Root Cause: Trusting ANSI SQL standards over physical implementations.
- Diagnostic: "Phantom Reads" occurring in MySQL Repeatable Read due to gap lock behavior, while strictly blocked in PG snapshot boundaries.
- Correction: Test isolation concurrency directly against your chosen engine's MVCC locking implementation.

---

## 🗺️ Interview Angle

### Core Concept Verification
- "How does MVCC physically stop Writers from blocking Readers?"
- Expected: Explain point-in-time Snapshot extraction and reading older tuple states (`xmin`/`xmax` or Undo Log rollbacks) while the writer creates an uncommitted parallel version.

### The Uber Migration Question
- "Why did Uber leave PostgreSQL?"
- Expected: Explain Write Amplification. Changing a single column in PG alters physical disk pointers (`ctid`), forcing cascade rewrites to 15 different secondary indexes. MySQL isolates the update in-place.

### The Bloat Puzzle
- "Your PG server disk usage is climbing linearly but inserts are static and rows are just updating. What happened?"
- Expected: Deduce that dead tuples are not being reclaimed because (a) autovacuum is throttled, or (b) a rogue uncommitted transaction 3 days ago is holding a snapshot hostage.

---

## 🗺️ Assessment & Reflection
- Do your longest-running `SELECT` queries reside on the same cluster as your high-volume `UPDATE` streams?
- For highly updated tables in Postgres, is `FILLFACTOR` lowered to allow HOT updates?
- Are you alerting on TXID age crossing 1 billion to prevent wraparound death?
- Do you understand the gap-lock consequences in InnoDB Repeatable Read?
