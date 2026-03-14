# MVCC Internals — Real-World Scenarios

> When MVCC implementation details clash with massive scale, the resulting architectural pivots cost millions of dollars and multi-year engineering migrations.

---

## Case Study 1: Uber — The $100M Postgres to MySQL Migration

**Context**: In 2013, Uber migrated their trip dispatch architecture from MySQL to PostgreSQL. By 2016, as they hit hyper-growth (millions of trips per day), they publicly announced a massive, multi-year migration *back* from PostgreSQL to MySQL (specifically InnoDB).

**The Architectural Root Cause**: PostgreSQL's Append-Only MVCC layer.

**What Went Wrong**:
Uber's core table stored trip status (Requested, Accepted, En Route, Arrived, Completed). A single trip was updated dozens of times over 30 minutes. The table had several secondary indexes (e.g., Rider ID, Driver ID, City).

Because PostgreSQL's MVCC writes a completely new physical row for every update, the new row gets a new physical address (`ctid`). Even though Uber only changed the `status` column, they had to rewrite the *entire physical row* AND they were forced to update every single secondary index to point to the new physical address. 
- **The Result**: A simple 1-byte status update resulted in 10-20 distinct disk page writes across various B-Trees. Write Amplification crippled their replica replication stream (which operates at the physical page level in PG), and replication lag routinely spiked into minutes, breaking read-replica consistency.

**The Fix**:
Uber moved back to MySQL/InnoDB. Because InnoDB uses In-Place updates and Undo Logs, a trip status update happens directly on the original row. Secondary indexes in MySQL point to the Primary Key (not a physical disk location).
- **The Result**: Updating a trip status required exactly one write to the main B-Tree node and one append to the Undo Log. Zero secondary index writes. Replication lag stabilized to milliseconds.

---

## Case Study 2: GitLab — The Transaction ID Wraparound Outage (2017)

**Context**: GitLab operates one of the largest single PostgreSQL clusters in the world. 

**The Architectural Root Cause**: PostgreSQL's 32-bit `xmin`/`xmax` counters.

**What Went Wrong**:
To keep track of MVCC visibility, Postgres assigns every changing transaction a 32-bit Transaction ID (TXID). 32 bits allows for exactly 4.2 billion transactions. When the counter hits 4.2 billion, it abruptly "wraps around" back to zero.
- **The Hazard**: If 4.2 billion wraps to 0, suddenly a row created last year by TX 1,000 looks like it was created *in the future* compared to TX 0. The row becomes instantaneously invisible to everyone. Data vanishes.
- **The Mechanism**: To prevent this, Postgres uses a background process called **Autovacuum Freezing**, which marks older rows with a special "Frozen" bit, making them universally visible regardless of TXID math. 
- **The Incident**: Heavy update loads and long-running reporting queries prevented Autovacuum from running successfully on central tables. The database hit the absolute hard limit where a wraparound was mathematically imminent. To prevent catastrophic data corruption, Postgres intentionally shut itself down and refused all connections until a manual, offline single-user vacuum could complete. Gitlab suffered substantial downtime.

**The Fix**:
- Improved monitoring of `age(relfrozenxid)` on all database tables.
- Rearchitected long-running background cron jobs that held uncommitted read snapshots for hours, which were the ultimate blocker for the vacuum daemon.

---

## Case Study 3: Mailchimp — Massive Table Bloat (2019)

**Context**: Mailchimp sends billions of emails daily, heavily updating status flags (Pending, Sent, Bounced, Opened).

**The Architectural Root Cause**: MVCC Dead Tuples vs Autovacuum contention.

**What Went Wrong**:
Updating email interaction statuses generated millions of dead MVCC tuples per hour. The background worker, autovacuum, was configured with conservative defaults designed for mechanical hard drives (to prevent I/O saturation).
- **The Result**: Autovacuum ran too slowly to delete the dead tuples. Mailchimp's central tables bloated to 3-5x their necessary size. 
- Because the tables were massively bloated, every sequential scan (e.g., "Find all unsent emails in this campaign") took 3-5x longer because it had to read through gigabytes of dead space. This saturated memory and CPU limits.

**The Fix**:
- Shifted physical disks to NVMe.
- Explicitly disabled the mechanical drive limiters by setting `autovacuum_vacuum_cost_delay = 0` (turning off artificial I/O throttling).
- Set `autovacuum_naptime = 1min` so the daemon woke up 60 times an hour instead of 1 time an hour, successfully keeping the top-heavy tables perfectly lean. Space utilization dropped by 70%.
