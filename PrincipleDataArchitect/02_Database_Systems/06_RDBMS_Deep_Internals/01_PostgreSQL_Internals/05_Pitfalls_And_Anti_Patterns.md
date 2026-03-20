# PostgreSQL Internals — Pitfalls and Anti-Patterns

## Anti-Pattern 1: Disabling or Ignoring Autovacuum

### The Mistake

```sql
-- "VACUUM is slow and causes I/O. Let's turn it off."
ALTER TABLE orders SET (autovacuum_enabled = false);

-- Or the subtle version: never tuning thresholds for large tables
-- Default: vacuum triggers at 50 + 0.2 * n_live_tup dead tuples
-- A 100M-row table waits for 20,000,050 dead tuples before vacuum fires
```

### Why It's Wrong

MVCC means every UPDATE creates a new tuple version and marks the old one dead. Without VACUUM:
1. **Table bloat**: Dead tuples consume disk space. A table that should be 10GB grows to 50GB.
2. **Index bloat**: Index entries pointing to dead tuples remain. Index scans read and discard dead entries.
3. **Transaction ID wraparound**: PostgreSQL uses 32-bit XIDs (~4.2B). Without freezing old tuples, the database will force-shutdown at 2^31 remaining XIDs to prevent data corruption.

### Detection

```sql
-- Tables approaching wraparound danger
SELECT
    c.relname,
    age(c.relfrozenxid) AS xid_age,
    CASE
        WHEN age(c.relfrozenxid) > 1200000000 THEN '🔴 CRITICAL - shutdown imminent'
        WHEN age(c.relfrozenxid) > 800000000 THEN '🟡 WARNING - vacuum urgently needed'
        ELSE '🟢 OK'
    END AS status,
    pg_size_pretty(pg_total_relation_size(c.oid)) AS total_size,
    s.n_dead_tup,
    s.last_autovacuum
FROM pg_class c
JOIN pg_stat_user_tables s ON s.relid = c.oid
WHERE c.relkind = 'r'
ORDER BY age(c.relfrozenxid) DESC
LIMIT 10;

-- Symptom: pg_log shows "WARNING: oldest xmin is far in the past"
-- Symptom: Table sizes grow without corresponding data growth
```

### Fix

```sql
-- Per-table aggressive autovacuum for high-write tables:
ALTER TABLE orders SET (
    autovacuum_vacuum_scale_factor = 0.01,    -- Trigger at 1% dead vs 20% default
    autovacuum_vacuum_threshold = 5000,
    autovacuum_vacuum_cost_delay = 2,          -- 2ms vs 20ms default
    autovacuum_freeze_max_age = 100000000      -- Freeze at 100M vs 200M default
);

-- Global: increase autovacuum workers for high-table-count databases
-- postgresql.conf:
-- autovacuum_max_workers = 6    (default 3)
-- autovacuum_naptime = 15       (seconds; default 60)
```

---

## Anti-Pattern 2: Using VACUUM FULL as Routine Maintenance

### The Mistake

```sql
-- "The table is bloated, let's VACUUM FULL it every night."
VACUUM FULL orders;
-- This acquires an ACCESS EXCLUSIVE lock — blocks ALL reads and writes
-- On a 100GB table, this can take 30+ minutes
```

### Why It's Wrong

`VACUUM FULL` rewrites the entire table into a new file, requiring:
- **Exclusive lock** for the entire duration — all transactions queue behind it
- **2x disk space** temporarily (old file + new file)
- **All indexes rebuilt** from scratch, adding more I/O and lock time
- **Not concurrent** — unlike `CREATE INDEX CONCURRENTLY`, there's no concurrent VACUUM FULL

### Detection

```sql
-- Check if someone is running VACUUM FULL in production
SELECT pid, query, state, wait_event_type, wait_event, now() - query_start AS duration
FROM pg_stat_activity
WHERE query ILIKE '%vacuum full%'
    AND state = 'active';

-- Check for locks caused by VACUUM FULL
SELECT
    l.pid,
    l.locktype,
    l.mode,
    c.relname,
    l.granted,
    a.query,
    now() - a.query_start AS lock_duration
FROM pg_locks l
JOIN pg_class c ON c.oid = l.relation
JOIN pg_stat_activity a ON a.pid = l.pid
WHERE l.mode = 'AccessExclusiveLock'
    AND c.relkind = 'r';
```

### Fix

Use `pg_repack` instead — it rewrites the table with only a brief `ACCESS EXCLUSIVE` lock at the very end:

```bash
# Install pg_repack extension
# Then:
pg_repack --table orders --no-superuser-check -d mydb

# pg_repack creates a new table, copies data, builds indexes,
# then swaps the old table for the new one with a brief lock
# Total lock time: <1 second for most tables
```

---

## Anti-Pattern 3: Ignoring Connection Pooling

### The Mistake

```python
# Every request opens a new PostgreSQL connection
import psycopg2

def handle_request():
    conn = psycopg2.connect("dbname=myapp")
    cur = conn.cursor()
    cur.execute("SELECT ...")
    result = cur.fetchall()
    conn.close()        # Connection created and destroyed per request
    return result
```

### Why It's Wrong

PostgreSQL forks a new OS process per connection. Each backend:
- Consumes ~10MB RSS
- Full fork() overhead on connection establishment (~1-5ms)
- Shared memory context switch overhead scales with connection count
- At 500 connections: 5GB RAM consumed by backends alone, plus contention on shared memory structures (lock table, proc array)

Benchmark impact:

| Connections | TPS (pgbench, simple queries) | P99 Latency |
|---|---|---|
| 50 | 45,000 | 2ms |
| 200 | 38,000 | 8ms |
| 500 | 22,000 | 45ms |
| 1000 | 12,000 | 180ms |

### Detection

```sql
-- Current connection count and max
SELECT
    count(*) AS active_connections,
    (SELECT setting FROM pg_settings WHERE name = 'max_connections') AS max_allowed,
    round(100.0 * count(*) / (SELECT setting::int FROM pg_settings WHERE name = 'max_connections'), 2) AS pct_used,
    count(*) FILTER (WHERE state = 'idle') AS idle,
    count(*) FILTER (WHERE state = 'idle in transaction') AS idle_in_txn,
    count(*) FILTER (WHERE state = 'active') AS active
FROM pg_stat_activity
WHERE backend_type = 'client backend';
```

### Fix

Deploy PgBouncer in transaction pooling mode:

```ini
# pgbouncer.ini
[databases]
myapp = host=127.0.0.1 port=5432 dbname=myapp

[pgbouncer]
listen_port = 6432
pool_mode = transaction          # Return connection to pool after each transaction
max_client_conn = 10000          # Clients can queue up to 10K connections
default_pool_size = 50           # Only 50 actual PostgreSQL backends per database
reserve_pool_size = 10
reserve_pool_timeout = 3
server_idle_timeout = 600
```

---

## Anti-Pattern 4: Over-Indexing

### The Mistake

```sql
-- "More indexes = faster queries, right?"
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date);
CREATE INDEX idx_orders_customer_status ON orders(customer_id, status);
CREATE INDEX idx_orders_date_status ON orders(order_date, status);
-- ... 15 more indexes on a single table
```

### Why It's Wrong

Each index:
- Must be updated on every INSERT (all indexes) and UPDATE (indexes on modified columns)
- Consumes disk space and shared buffer cache
- Increases WAL volume (index page modifications generate WAL records)
- Slows down `VACUUM` (must clean index entries for every dead tuple)

A table with 15 indexes can see INSERT throughput drop 3-5x compared to zero secondary indexes.

### Detection

```sql
-- Indexes that cost more than they're worth: never scanned but always maintained
SELECT
    s.relname AS table_name,
    s.indexrelname AS index_name,
    s.idx_scan AS times_used,
    pg_size_pretty(pg_relation_size(s.indexrelid)) AS index_size,
    s.idx_tup_read,
    t.n_tup_ins + t.n_tup_upd + t.n_tup_del AS write_activity
FROM pg_stat_user_indexes s
JOIN pg_stat_user_tables t ON t.relid = s.relid
WHERE s.idx_scan < 10  -- Almost never used
    AND pg_relation_size(s.indexrelid) > 10485760  -- >10MB
    AND s.indexrelname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(s.indexrelid) DESC;
```

### Fix

Audit indexes quarterly:
1. Drop indexes with zero scans since stats reset (confirm stats_reset is >1 week old)
2. Merge overlapping indexes: `(a)` is redundant if `(a, b)` exists
3. Consider partial indexes: `WHERE status = 'active'` instead of full-table index
4. Use covering indexes (`INCLUDE`) to eliminate heap fetches

---

## Anti-Pattern 5: Long-Running Transactions Blocking VACUUM

### The Mistake

```python
# Opens a transaction and holds it for hours
conn = psycopg2.connect(...)
conn.autocommit = False
cur = conn.cursor()
cur.execute("SELECT * FROM orders WHERE status = 'pending'")
# ... process each row (takes 2 hours)
# Transaction stays open. VACUUM can't remove any dead tuples
# created after this transaction's snapshot.
conn.commit()
```

### Why It's Wrong

PostgreSQL's MVCC visibility uses snapshots. An open transaction's snapshot pins the `xmin` horizon — no dead tuple with `xmax > this_transaction's_xmin` can be removed by VACUUM. A single long-running transaction can cause all tables in the database to bloat.

### Detection

```sql
-- Find long-running transactions blocking vacuum
SELECT
    pid,
    usename,
    state,
    xact_start,
    now() - xact_start AS transaction_age,
    query,
    backend_xmin
FROM pg_stat_activity
WHERE state IN ('idle in transaction', 'active')
    AND xact_start < now() - interval '5 minutes'
ORDER BY xact_start ASC;

-- Check if xmin horizon is pinned
SELECT
    slot_name,
    xmin AS replication_slot_xmin,
    catalog_xmin,
    active
FROM pg_replication_slots
WHERE xmin IS NOT NULL OR catalog_xmin IS NOT NULL;
```

### Fix

```sql
-- Kill idle-in-transaction sessions automatically (postgresql.conf)
-- idle_in_transaction_session_timeout = 300000   -- 5 minutes

-- Set statement-level timeout
-- statement_timeout = 60000   -- 60 seconds for OLTP queries

-- Application level: use cursor-based iteration
-- Instead of fetching all rows into memory:

-- Python psycopg2 server-side cursor
with conn.cursor(name='server_cursor') as cur:
    cur.itersize = 1000
    cur.execute("SELECT * FROM orders WHERE status = 'pending'")
    for row in cur:
        process(row)
    # Each fetch grabs 1000 rows; no long-running transaction needed
```

---

## Anti-Pattern 6: Setting random_page_cost = 4.0 on SSDs

### The Mistake

```
# postgresql.conf (default, optimized for spinning disks circa 2000)
random_page_cost = 4.0
```

### Why It's Wrong

`random_page_cost = 4.0` tells the planner that random I/O is 4x more expensive than sequential I/O. This was true for HDDs (seek time ~10ms). On NVMe SSDs, random and sequential reads are nearly identical (~0.1ms). The incorrect cost makes the planner:
- Prefer sequential scans over index scans (even when an index scan is faster)
- Choose merge joins over hash joins unnecessarily
- Underestimate the value of index-only scans

### Detection

```sql
-- Check current setting
SHOW random_page_cost;
SHOW seq_page_cost;

-- If EXPLAIN shows Seq Scan on a table with a highly selective WHERE clause
-- AND an index exists on the filtered column, the planner is likely wrong
EXPLAIN SELECT * FROM orders WHERE customer_id = 42;
-- If this shows "Seq Scan" with "Filter: customer_id = 42"
-- instead of "Index Scan using idx_orders_customer"
-- then random_page_cost is too high for your storage
```

### Fix

```sql
-- For SSDs (NVMe or SATA SSD):
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
SELECT pg_reload_conf();

-- For cloud ephemeral SSDs (AWS gp3, GCP pd-ssd):
-- random_page_cost = 1.1 to 1.5
-- For mixed SSD/HDD (tablespace-dependent): set per-tablespace
ALTER TABLESPACE ssd_tablespace SET (random_page_cost = 1.1);
ALTER TABLESPACE hdd_tablespace SET (random_page_cost = 4.0);
```

---

## Decision Matrix: When PostgreSQL Is the Wrong Choice

| Scenario | Why PostgreSQL Fails | Better Alternative |
|---|---|---|
| Key-value store, >10M ops/sec, sub-ms latency | Process-per-connection overhead; MVCC overhead per row; no built-in sharding | Redis, DynamoDB, ScyllaDB |
| Append-only event log, 1M+ events/sec ingest | WAL overhead on every insert; no native columnar compression; VACUUM overhead on dead-tuple-free workloads | Kafka + ClickHouse, Apache Druid |
| Full-text search as primary access pattern | `tsvector` is functional but lacks BM25 relevance tuning, faceted search, distributed indexing | Elasticsearch, Typesense, Meilisearch |
| Analytical queries on 100+ TB cold data | Single-node PostgreSQL can't distribute queries; no columnar storage (unless using Citus columnar or Hydra) | Snowflake, BigQuery, ClickHouse, DuckDB |
| Multi-model graph traversals (6+ hops) | Recursive CTEs become O(n^k) for deep traversals; no native graph optimizer | Neo4j, TigerGraph, Amazon Neptune |
| Global 5-nines with automatic failover + sharding | Vanilla PostgreSQL has no built-in consensus-based failover or distributed transactions | CockroachDB, YugabyteDB, Google Spanner |
| Massive BLOB storage (files, images, video) | TOAST handles LO but was never designed for media streaming; pg_largeobject is limited to 4TB | S3, MinIO, CDN |
